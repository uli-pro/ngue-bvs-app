# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, abort
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets


# Load environment variables
load_dotenv()

# Configure application
app = Flask(__name__)


# Load configuration from environment
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Admin notification configuration
app.config["ADMIN_EMAIL"] = os.environ.get("ADMIN_EMAIL")

# Certificate storage configuration
app.config['CERTIFICATE_STORAGE_PATH'] = os.path.join(os.getcwd(), 'certificates')
app.config['PDF_TEMPLATE_PATH'] = 'templates/certificates'

# Email configuration now handled directly by email_service.py using IONOS SMTP

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize extensions
from models import db, Person, Verse, Donation, VerseReservation, Certificate, MagicLinkToken
from sqlalchemy import text
from stripe_service import StripeService, StripeError
from pdf_service import PDFGeneratorService, PDFGenerationError
from hubspot_service import HubSpotService
import stripe
db.init_app(app)

# Import admin blueprint
from admin import init_admin

# Initialize PDF Generator Service
pdf_service = PDFGeneratorService()
pdf_service.init_app(app)

# Initialize Email Service
from email_service import email_service
email_service.init_app(app)

# Configure session to use database (production-ready)
app.config["SESSION_PERMANENT"] = True  # Make sessions permanent so they get expiry dates
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY"] = db
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=31)  # Set session lifetime

# CSRF Protection  
csrf = CSRFProtect(app)
# Note: Stripe webhook routes use @csrf.exempt decorator individually

# Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Initialize and register admin blueprint
admin_bp = init_admin(app)
app.register_blueprint(admin_bp)

# Session Security (development-safe)
if app.debug:
    # Development: HTTP-friendly settings
    app.config["SESSION_COOKIE_SECURE"] = False
else:
    # Production: HTTPS-only settings
    app.config["SESSION_COOKIE_SECURE"] = True

# Security settings for all environments
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = 'Lax'


# Initialize Flask-Session
sess = Session(app)

# Create sessions table if it doesn't exist
with app.app_context():
    try:
        # This creates the sessions table if it doesn't exist
        sess.app.session_interface.db.create_all()
    except Exception as e:
        # Table might already exist, that's fine
        print(f"Sessions table initialization: {e}")


# Custom filter for currency formatting
@app.template_filter('currency')
def currency_filter(value):
    """Format value as EUR currency."""
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# Context processor to inject current year
@app.context_processor
def inject_context():
    return {
        'current_year': datetime.now().year
    }


# ==========================================
# CART VALIDATION AND RECOVERY FUNCTIONS
# ==========================================

def validate_cart_item(item):
    """Validate cart item structure and content."""
    
    if not isinstance(item, dict):
        return False
    
    required_fields = ['verse_id', 'donor_data', 'amount']
    
    # Check required fields exist
    for field in required_fields:
        if field not in item:
            return False
    
    # Check field types and values
    try:
        verse_id = int(item['verse_id'])
        if verse_id <= 0:
            return False
    except (ValueError, TypeError):
        return False
    
    
    if not isinstance(item['donor_data'], dict):
        return False
    
    try:
        amount = float(item['amount'])
        if amount <= 0:
            return False
    except (ValueError, TypeError):
        return False
    
    return True


def sanitize_cart(cart):
    """Clean up cart by removing invalid items."""
    original_count = len(cart) if isinstance(cart, list) else 0
    
    if not isinstance(cart, list):
        return []
    
    valid_items = []
    invalid_count = 0
    for i, item in enumerate(cart):
        if validate_cart_item(item):
            # Ensure currency field exists
            if 'currency' not in item:
                item['currency'] = 'EUR'
            valid_items.append(item)
        else:
            invalid_count += 1
    
    
    return valid_items


def handle_corrupted_session():
    """Handle corrupted session data gracefully."""
    
    try:
        # Initialize empty cart if missing or corrupted
        if 'cart' not in session or not isinstance(session['cart'], list):
            session['cart'] = []
        else:
            # Sanitize existing cart
            old_size = len(session['cart'])
            session['cart'] = sanitize_cart(session['cart'])
            new_size = len(session['cart'])
            
            if old_size != new_size:
                pass
        
        session.modified = True
        
    except Exception as e:
        # If all else fails, reset cart completely
        
        session['cart'] = []
        session.modified = True
        app.logger.error(f"Session corruption recovery failed: {e}")


# ==========================================
# INDEX PAGE ROUTES
# ==========================================

@app.route("/")
def index():
    """Show homepage"""
    # Get real statistics from database
    total_verses = Verse.query.count()
    sponsored_verses = Verse.query.filter_by(is_sponsored=True).count()
    available_verses = total_verses - sponsored_verses
    percentage = round((sponsored_verses / total_verses * 100), 1) if total_verses > 0 else 0
    
    # Bible translation progress calculations
    # Constants for complete Bible
    NT_VERSES = 7958  # New Testament - completely translated
    AT_VERSES = 23186  # Old Testament - total verses
    AT_ALREADY_TRANSLATED = 12139  # AT verses already translated (not in our DB)
    TOTAL_BIBLE_VERSES = NT_VERSES + AT_VERSES  # 31,144 verses total
    
    # Current translation status
    # NT is complete (7958), AT has 12139 already translated
    # Our database contains the remaining AT verses that need sponsoring
    at_remaining_to_translate = total_verses  # Verses in DB = verses still to translate
    
    # Overall Bible progress
    total_translated = NT_VERSES + AT_ALREADY_TRANSLATED  # 7958 + 12139 = 20097
    total_remaining = at_remaining_to_translate  # Verses in our database
    bible_percentage = round((total_translated / TOTAL_BIBLE_VERSES * 100), 1)
    
    # AT-specific progress
    at_percentage = round((AT_ALREADY_TRANSLATED / AT_VERSES * 100), 1)
    
    stats = {
        'total_verses': total_verses,
        'sponsored_verses': sponsored_verses,
        'available_verses': available_verses,
        'percentage': percentage
    }
    
    # Bible translation progress stats
    bible_stats = {
        'total_bible_verses': TOTAL_BIBLE_VERSES,
        'total_translated': total_translated,
        'total_remaining': total_remaining,
        'bible_percentage': bible_percentage,
        'nt_verses': NT_VERSES,
        'at_verses': AT_VERSES,
        'at_already_translated': AT_ALREADY_TRANSLATED,
        'at_still_to_translate': at_remaining_to_translate,
        'at_percentage': at_percentage
    }
    
    return render_template("index.html", stats=stats, bible_stats=bible_stats)

# ==========================================
# INFORMATION PAGES ROUTES
# ==========================================

@app.route("/ueber-ngue")
def ueber_ngue():
    """About NGÜ page"""
    return render_template("ueber-ngue.html")

@app.route("/ueber-partner")
def ueber_partner():
    """About our partners page - combined view of Stiftung and Verlage"""
    return render_template("ueber-partner.html")

@app.route("/faq")
def faq():
    """FAQ page"""
    return render_template("faq.html")

# ==========================================
# VERS-AUSWAEHLEN-ROUTES
# ==========================================

@app.route("/vers-auswaehlen")
def vers_auswaehlen():
    """Verse selection page with session-based persistence"""
    # Cleanup expired reservations periodically (security/performance)
    try:
        VerseReservation.cleanup_expired()
    except Exception:
        pass  # Silent cleanup failure, don't break user experience
    
    # Check ob "andere Verse" explizit angefordert
    refresh_verses = request.args.get('refresh') == 'true'
    
    # Get verses already in cart to exclude them
    cart_verse_ids = []
    if 'cart' in session:
        cart_verse_ids = [item['verse_id'] for item in session['cart']]
    
    if 'featured_verse_ids' not in session:
        # Erste Auswahl - exclude cart items
        featured_verses = Verse.get_adaptive_featured_verses(3, exclude_ids=cart_verse_ids)
        session['featured_verse_ids'] = [v.id for v in featured_verses]
        session['shown_verse_ids'] = [v.id for v in featured_verses]  # Track all shown verses
    elif refresh_verses:
        # "Andere Verse anzeigen" - exclude ALL previously shown verses AND cart items
        all_shown_ids = session.get('shown_verse_ids', [])
        exclude_ids = list(set(all_shown_ids + cart_verse_ids))
        featured_verses = Verse.get_adaptive_featured_verses(3, exclude_ids=exclude_ids)
        
        if len(featured_verses) == 0:
            # Keine neuen Verse verfügbar - reset und zeige erste wieder
            featured_verses = Verse.get_adaptive_featured_verses(3)
            session['shown_verse_ids'] = [v.id for v in featured_verses]
        else:
            # Füge neue Verse zur "bereits gezeigt" Liste hinzu
            session['shown_verse_ids'] = all_shown_ids + [v.id for v in featured_verses]
        
        session['featured_verse_ids'] = [v.id for v in featured_verses]
    else:
        # Bestehende Session-Verse laden
        verse_ids = session['featured_verse_ids']
        featured_verses = Verse.query.filter(Verse.id.in_(verse_ids)).all()
        
        # Check ob Verse zwischenzeitlich gesponsert wurden oder bereits im Warenkorb sind
        cart_verse_ids = []
        if 'cart' in session:
            cart_verse_ids = [item['verse_id'] for item in session['cart']]
        
        available_verses = [v for v in featured_verses if not v.is_sponsored and v.id not in cart_verse_ids]
        
        if len(available_verses) < len(featured_verses):
            # Ersetze gesponserte/bereits im Korb befindliche Verse
            missing_count = len(featured_verses) - len(available_verses)
            all_shown_ids = session.get('shown_verse_ids', [])
            exclude_ids = list(set(all_shown_ids + cart_verse_ids))
            
            new_verses = Verse.get_adaptive_featured_verses(
                missing_count, exclude_ids=exclude_ids
            )
            
            featured_verses = available_verses + new_verses
            session['featured_verse_ids'] = [v.id for v in featured_verses]
            # Update shown_verse_ids
            session['shown_verse_ids'] = list(set(all_shown_ids + [v.id for v in new_verses]))
    
    return render_template("vers-auswaehlen.html", 
                         featured_verses=featured_verses)

# ==========================================
# VERSE SEARCH ROUTES
# ==========================================

@app.route("/vers-auswaehlen/referenz")
def vers_auswaehlen_referenz():
    """Reference search page"""
    return render_template("vers-auswaehlen-referenz.html")

@app.route("/vers-auswaehlen/keyword")
def vers_auswaehlen_keyword():
    """Keyword search page"""
    return render_template("vers-auswaehlen-keyword.html")

# ==========================================
# REFERENCE SEARCH API ROUTES
# ==========================================

@app.route("/api/verse/reference/<book>/<int:chapter>/<int:verse_num>")
@csrf.exempt  # GET requests don't need CSRF protection
def api_verse_by_reference(book, chapter, verse_num):
    """API endpoint for verse reference search with enhanced error handling."""
    # Input validation
    if not book or not book.strip():
        return {
            'success': False,
            'error': 'Book name is required'
        }, 400
    
    if chapter <= 0 or verse_num <= 0:
        return {
            'success': False,
            'error': 'Chapter and verse numbers must be positive'
        }, 400
    
    if chapter > 200 or verse_num > 200:  # Reasonable limits
        return {
            'success': False,
            'error': 'Chapter or verse number seems too large'
        }, 400
    
    try:
        verse = Verse.get_by_reference(book, chapter, verse_num)
        
        if not verse:
            return {
                'success': False,
                'error': f'Verse {book} {chapter}:{verse_num} not found in database',
                'suggestion': 'Please check the book name, chapter and verse numbers'
            }, 404
        
        # If verse is sponsored, include similar verses
        response_data = {
            'success': True,
            'verse': {
                'id': verse.id,
                'book': verse.book,
                'chapter': verse.chapter,
                'verse': verse.verse,
                'text': verse.text,
                'reference': verse.reference,
                'german_reference': verse.german_reference,
                'positivity_score': verse.positivity_score,
                'is_sponsored': verse.is_sponsored,
                'url_slug': verse.url_slug
            }
        }
        
        # Add similar verses if this one is sponsored
        if verse.is_sponsored:
            similar_verses = verse.find_similar_verses(limit=3, positivity_tolerance=10)
            response_data['similar_verses'] = [
                {
                    'id': alt.id,
                    'reference': alt.reference,
                    'german_reference': alt.german_reference,
                    'text': alt.text,  # Show full text for alternative verses
                    'positivity_score': alt.positivity_score,
                    'url_slug': alt.url_slug
                }
                for alt in similar_verses
            ]
        
        return response_data
        
    except Exception as e:
        app.logger.error(f"Error in verse reference search: {e}")
        return {
            'success': False,
            'error': 'Internal server error occurred while searching for verse'
        }, 500

@app.route("/api/verse/<int:verse_id>/similar")
@csrf.exempt  # GET requests don't need CSRF protection
def api_similar_verses(verse_id):
    """Get similar verses for a sponsored verse"""
    try:
        verse = Verse.query.get(verse_id)
        if not verse:
            return {
                'success': False,
                'error': 'Verse not found'
            }, 404
        
        alternatives = verse.find_similar_verses(limit=3, positivity_tolerance=10)
        
        alternatives_data = []
        for alt in alternatives:
            alternatives_data.append({
                'id': alt.id,
                'book': alt.book,
                'chapter': alt.chapter,
                'verse': alt.verse,
                'text': alt.text,
                'reference': alt.reference,
                'positivity_score': alt.positivity_score,
                'url_slug': alt.url_slug
            })
        
        return {
            'success': True,
            'original_verse': {
                'id': verse.id,
                'reference': verse.reference,
                'german_reference': verse.german_reference,
                'is_sponsored': verse.is_sponsored
            },
            'alternatives': alternatives_data
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'Internal server error'
        }, 500

@app.route("/api/verse/books")
@csrf.exempt  # GET requests don't need CSRF protection
def api_verse_books():
    """Get list of all available books in biblical order"""
    try:
        # Get all available books from database
        available_books_query = db.session.query(Verse.book.distinct()).all()
        available_books = {book[0] for book in available_books_query if book[0]}
        
        # Biblical order for Old Testament books
        biblical_order = [
            # Missing: GEN, EXO, LEV, NUM, DEU, JOS, JDG, RUT, 1SA, 2SA (not in our AT-only dataset)
            '1KI',      # 1.Könige  
            '2KI',      # 2.Könige
            '1CH',      # 1.Chronik
            '2CH',      # 2.Chronik
            'EZR',      # Esra
            'NEH',      # Nehemia  
            'EST',      # Esther
            'JOB',      # Hiob
            # Missing: PSA, PRO (not in available books)
            'ECC',      # Prediger
            'SNG',      # Hoheslied
            'ISA',      # Jesaja
            'JER',      # Jeremia
            'LAM',      # Klagelieder
            'EZK',      # Hesekiel
            'DAN',      # Daniel
            'HOS',      # Hosea
            'JOL',      # Joel
            'AMO',      # Amos
            'OBA',      # Obadja
            # Missing: JON (not in available books)
            'MIC',      # Micha
            'NAM',      # Nahum
            'HAB',      # Habakuk
            'ZEP',      # Zefanja
            'HAG',      # Haggai
            'ZEC',      # Sacharja
            'MAL'       # Maleachi
        ]
        
        # Return only books that exist in database, in biblical order with German names
        from book_names import get_german_book_name
        
        book_list = []
        for book in biblical_order:
            if book in available_books:
                book_list.append({
                    'code': book,
                    'german_name': get_german_book_name(book)
                })
        
        return {
            'success': True,
            'books': book_list
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'Internal server error'
        }, 500

@app.route("/api/verse/chapters/<book>")
@csrf.exempt  # GET requests don't need CSRF protection
def api_verse_chapters(book):
    """Get list of chapters for a specific book"""
    try:
        book_upper = book.upper()
        chapters = db.session.query(Verse.chapter.distinct()).filter(
            Verse.book == book_upper
        ).order_by(Verse.chapter).all()
        
        chapter_list = [chapter[0] for chapter in chapters if chapter[0]]
        
        return {
            'success': True,
            'chapters': chapter_list
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'Internal server error'
        }, 500

@app.route("/api/verse/verses/<book>/<int:chapter>")
@csrf.exempt  # GET requests don't need CSRF protection
def api_verse_verses(book, chapter):
    """Get list of verses for a specific book and chapter"""
    try:
        book_upper = book.upper()
        verses = db.session.query(Verse.verse.distinct()).filter(
            Verse.book == book_upper,
            Verse.chapter == chapter
        ).order_by(Verse.verse).all()
        
        verse_list = [verse[0] for verse in verses if verse[0]]
        
        return {
            'success': True,
            'verses': verse_list
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'Internal server error'
        }, 500

# ==========================================
# KEYWORD SEARCH API ROUTE
# ==========================================

@app.route("/api/verse/search/keyword", methods=["POST"])
def api_keyword_search():
    """Keyword search API with positivity-based ranking and pagination"""
    try:
        # Validate request
        if not request.is_json:
            return {
                'success': False,
                'error': 'Request must be JSON'
            }, 400
        
        data = request.get_json()
        query = data.get('query', '').strip()
        offset = data.get('offset', 0)
        
        # Validate parameters
        if not query:
            return {
                'success': False,
                'error': 'Query parameter is required'
            }, 400
        
        if len(query) < 2:
            return {
                'success': False,
                'error': 'Query must be at least 2 characters long'
            }, 400
        
        if offset < 0:
            offset = 0
        
        # Session management für Pagination
        if 'keyword_search' not in session or session['keyword_search'].get('query') != query:
            # Neue Suche oder geänderte Query - Session zurücksetzen
            session['keyword_search'] = {
                'query': query,
                'shown_verse_ids': [],
                'all_result_ids': None
            }
        
        search_session = session['keyword_search']
        
        # Wenn noch keine Gesamtergebnisse geladen wurden
        if search_session['all_result_ids'] is None:
            # Führe Hybrid-Suche durch
            all_results = Verse.search_hybrid(query, limit=100)
            
            # Nach kombiniertem Score sortieren (Positivity + Search Score)
            scored_results = []
            for verse in all_results:
                if not verse.is_sponsored:  # Nur ungesponserte Verse
                    # Kombinierter Score: 40% Search relevance + 60% Positivity
                    search_relevance = 1.0  # Placeholder - alle Hybrid-Ergebnisse sind relevant
                    positivity_normalized = (verse.positivity_score or 0) / 100.0
                    combined_score = 0.4 * search_relevance + 0.6 * positivity_normalized
                    scored_results.append((verse, combined_score))
            
            # Nach kombiniertem Score sortieren (höchste zuerst)
            scored_results.sort(key=lambda x: x[1], reverse=True)
            
            # Nur die Verse-IDs speichern für Pagination
            search_session['all_result_ids'] = [verse.id for verse, score in scored_results]
            session.modified = True
        
        # Paginierung: 3 Verse ab Offset
        all_ids = search_session['all_result_ids']
        page_ids = all_ids[offset:offset + 3]
        
        # Verse laden
        if page_ids:
            # Lade Verse in der korrekten Reihenfolge
            verses_dict = {v.id: v for v in Verse.query.filter(Verse.id.in_(page_ids)).all()}
            verses = [verses_dict[vid] for vid in page_ids if vid in verses_dict]
        else:
            verses = []
        
        # Update shown_verse_ids
        search_session['shown_verse_ids'].extend([v.id for v in verses])
        session.modified = True
        
        # Response zusammenbauen
        verses_data = []
        for verse in verses:
            verses_data.append({
                'id': verse.id,
                'book': verse.book,
                'chapter': verse.chapter,
                'verse': verse.verse,
                'text': verse.text,
                'reference': verse.reference,
                'german_reference': verse.german_reference,
                'positivity_score': verse.positivity_score,
                'is_sponsored': verse.is_sponsored,
                'url_slug': verse.url_slug
            })
        
        # Prüfe ob weitere Verse verfügbar sind
        has_more = (offset + 3) < len(all_ids)
        
        return {
            'success': True,
            'query': query,
            'verses': verses_data,
            'has_more': has_more,
            'total_found': len(all_ids),
            'offset': offset
        }
        
    except Exception as e:
        app.logger.error(f"Error in keyword search: {e}")
        return {
            'success': False,
            'error': 'Internal server error occurred'
        }, 500



# ==========================================
# VERSE CONFIRMATION ROUTES
# ==========================================

@app.route("/vers/<verse_id>/spendenart", methods=["GET", "POST"])
def vers_spendenart(verse_id):
    """Direct redirect to donation data collection - no type selection needed"""
    # Parse verse_id (z.B. "jesaja-43-1" → book="JESAJA", chapter=43, verse=1)
    parts = verse_id.rsplit('-', 2)
    if len(parts) != 3:
        flash("Ungültige Vers-Referenz.", "error")
        return redirect(url_for("vers_auswaehlen"))
    
    try:
        book = parts[0].upper()
        chapter = int(parts[1])
        verse_num = int(parts[2])
    except ValueError:
        flash("Ungültige Vers-Referenz.", "error")
        return redirect(url_for("vers_auswaehlen"))
    
    # Finde Vers in DB
    verse = Verse.query.filter_by(
        book=book, 
        chapter=chapter, 
        verse=verse_num
    ).first()
    
    if not verse:
        flash("Dieser Vers wurde nicht gefunden.", "error")
        return redirect(url_for("vers_auswaehlen"))
    
    # Check if already sponsored
    if verse.is_sponsored:
        flash(f"Dieser Vers wurde inzwischen gesponsert. Bitte wählen Sie einen anderen.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Create or extend reservation
    try:
        reservation = VerseReservation.create_or_update(
            verse.id, session.sid, minutes=15
        )
        session['selected_verse_id'] = verse.id
        session['reservation_id'] = reservation.id
        session.modified = True
    except Exception as e:
        flash("Dieser Vers ist bereits reserviert.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Direct redirect to checkout_spendendaten
    return redirect(url_for("checkout_spendendaten"))

@app.route("/vers/<int:verse_id>/spendenart", methods=["GET", "POST"])
def vers_spendenart_by_id(verse_id):
    """Direct redirect to donation data collection (by numeric ID)"""
    # Find verse by numeric ID
    verse = Verse.query.get(verse_id)
    
    if not verse:
        flash("Dieser Vers wurde nicht gefunden.", "error")
        return redirect(url_for("vers_auswaehlen"))
    
    # Check if already sponsored
    if verse.is_sponsored:
        flash(f"Dieser Vers wurde inzwischen gesponsert. Bitte wählen Sie einen anderen.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Create or extend reservation
    try:
        reservation = VerseReservation.create_or_update(
            verse.id, session.sid, minutes=15
        )
        session['selected_verse_id'] = verse.id
        session['reservation_id'] = reservation.id
        session.modified = True
    except Exception as e:
        flash("Dieser Vers ist bereits reserviert.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Direct redirect to checkout_spendendaten
    return redirect(url_for("checkout_spendendaten"))

# ==========================================
# CHECKOUT ROUTES
# ==========================================

@app.route("/spendenkorb")
def spendenkorb():
    """Donation cart page showing all selected verses"""
    
    # Handle corrupted session data gracefully
    handle_corrupted_session()
    
    # Initialize cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []
    
    # Load verse data for all items in cart
    cart_items = []
    total_amount = 0
    expired_count = 0
    
    
    # Check and update reservations for cart items
    for i, item in enumerate(session['cart']):
        # Load verse data
        verse = Verse.query.get(item['verse_id'])
        if not verse:
            continue
            
        # Verse im Cart sind dauerhaft reserviert - extend existing reservations
        reservation_valid = True
        if item.get('reservation_id'):
            try:
                reservation = VerseReservation.query.get(item['reservation_id'])
                if reservation:
                    # Extend reservation for cart items (they stay reserved)
                    reservation.extend_reservation(60)  # 1 hour extension for cart items
                else:
                    # Reservation was deleted - recreate it for cart item
                    try:
                        new_reservation = VerseReservation.create_or_update(
                            verse.id, session.sid, minutes=60
                        )
                        item['reservation_id'] = new_reservation.id
                        session.modified = True
                    except Exception:
                        # If we can't recreate reservation, verse might be taken
                        reservation_valid = False
                        expired_count += 1
            except Exception:
                # Try to recreate reservation
                try:
                    new_reservation = VerseReservation.create_or_update(
                        verse.id, session.sid, minutes=60
                    )
                    item['reservation_id'] = new_reservation.id
                    session.modified = True
                except Exception:
                    reservation_valid = False
                    expired_count += 1
        
        cart_item_display = {
            'index': i,
            'verse': verse,
            'donor_data': item.get('donor_data', {}),
            'amount': item['amount'],
            'currency': item.get('currency', 'EUR'),
            'reservation_valid': reservation_valid
        }
        cart_items.append(cart_item_display)
        total_amount += item['amount']
    
    # Show helpful message if there are problematic items
    if expired_count > 0:
        flash(f"Achtung: {expired_count} Vers(e) in Ihrem Korb sind zwischenzeitlich nicht mehr verfügbar und müssen entfernt werden.", "danger")
    
    return render_template("spendenkorb.html", 
                         cart_items=cart_items, 
                         total_amount=total_amount,
                         cart_count=len(cart_items))


@app.route("/spendenkorb/entfernen", methods=["POST"])
def cart_remove_item():
    """Remove item from cart via form submission"""
    try:
        # Handle corrupted session data gracefully
        handle_corrupted_session()
        
        item_index = request.form.get('item_index')
        
        if 'cart' not in session or item_index is None:
            flash('Ungültige Anfrage.', 'error')
            return redirect(url_for('spendenkorb'))
        
        # Security: Validate item_index is integer and in valid range
        try:
            item_index = int(item_index)
        except (ValueError, TypeError):
            flash('Ungültiger Versindex.', 'error')
            return redirect(url_for('spendenkorb'))
        
        cart = session['cart']
        if 0 <= item_index < len(cart):
            # Clean up reservation if exists (safely handle already deleted reservations)
            removed_item = cart[item_index]
            if removed_item.get('reservation_id'):
                try:
                    reservation = VerseReservation.query.get(removed_item['reservation_id'])
                    if reservation:
                        db.session.delete(reservation)
                        db.session.commit()
                except Exception:
                    # Reservation might already be deleted by cleanup - that's okay
                    # Continue with cart removal anyway
                    pass
            
            # Remove item from cart
            cart.pop(item_index)
            session['cart'] = cart
            session.modified = True
            
            # Set flash message for success feedback
            flash('Der Vers wurde aus Ihrem Spendenkorb entfernt.', 'success')
        else:
            flash('Vers nicht gefunden.', 'error')
            
        return redirect(url_for('spendenkorb'))
            
    except Exception as e:
        flash('Ein Fehler ist aufgetreten.', 'error')
        return redirect(url_for('spendenkorb'))


@app.route("/admin/cleanup-reservations", methods=["POST"])
@limiter.limit("1 per minute")
def cleanup_reservations():
    """Admin endpoint to cleanup expired reservations"""
    try:
        count = VerseReservation.cleanup_expired()
        return jsonify({
            'success': True, 
            'message': f'Cleaned up {count} expired reservations'
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Cleanup failed: {str(e)}'
        }), 500



# ==========================================
# CONTACT ROUTES
# ==========================================

@app.route("/kontakt", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def kontakt():
    """Contact page with spam protection (rate limit, honeypot, email notification)"""
    if request.method == "POST":
        try:
            # Honeypot check - if filled, it's a bot
            if request.form.get("website"):
                app.logger.warning(f"Honeypot triggered from IP {request.remote_addr}")
                # Show success to bot (don't reveal we detected them)
                flash("Vielen Dank für Ihre Nachricht! Wir werden uns in Kürze bei Ihnen melden.", "success")
                return redirect(url_for("index"))

            # Validate required fields
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            subject = request.form.get("subject", "Allgemeine Anfrage").strip()
            message = request.form.get("message", "").strip()

            if not name or not email or not message:
                flash("Bitte füllen Sie alle Pflichtfelder aus.", "error")
                return render_template("kontakt.html")

            # Basic email validation
            if "@" not in email or "." not in email.split("@")[1]:
                flash("Bitte geben Sie eine gültige E-Mail-Adresse ein.", "error")
                return render_template("kontakt.html")

            # Send email via email service
            email_service.send_contact_form_email(
                name=name,
                email=email,
                subject=subject,
                message=message,
                send_confirmation=True
            )

            app.logger.info(f"Contact form submitted by {name} ({email})")
            flash(f"Vielen Dank für Ihre Nachricht, {name}! Wir haben Ihnen eine Bestätigung per E-Mail gesendet und werden uns in Kürze bei Ihnen melden.", "success")
            return redirect(url_for("index"))

        except Exception as e:
            app.logger.error(f"Contact form error: {e}")
            flash("Es gab ein Problem beim Versenden Ihrer Nachricht. Bitte versuchen Sie es später erneut oder kontaktieren Sie uns direkt per E-Mail.", "error")
            return render_template("kontakt.html")

    return render_template("kontakt.html")

# ==========================================
# LEGAL ROUTES
# ==========================================

@app.route("/impressum")
def impressum():
    """Imprint page"""
    return render_template("impressum.html")

@app.route("/datenschutz")
def datenschutz():
    """Privacy policy page"""
    return render_template("datenschutz.html")

@app.route("/transparenz")
def transparenz():
    """Transparency page"""
    # Get statistics for transparency display
    total_verses = Verse.query.count()
    sponsored_verses = Verse.query.filter_by(is_sponsored=True).count()
    available_verses = total_verses - sponsored_verses
    percentage = round((sponsored_verses / total_verses * 100), 1) if total_verses > 0 else 0
    
    stats = {
        'total_verses': total_verses,
        'sponsored_verses': sponsored_verses,
        'available_verses': available_verses,
        'percentage': percentage,
        'total_amount': sponsored_verses * 100,  # Total amount raised
        'total_goal': total_verses * 100  # Total funding goal
    }
    
    return render_template("transparenz.html", stats=stats)

# ==========================================
# SECURE PDF DOWNLOAD ROUTES
# ==========================================

@app.route('/download/certificate/<int:certificate_id>')
@limiter.limit("10 per minute")
def download_certificate(certificate_id):
    """Sicherer PDF-Download für Zertifikate"""
    
    # Certificate laden
    certificate = Certificate.query.get_or_404(certificate_id)
    
    # Sicherheitsprüfungen
    if not can_access_certificate(certificate):
        abort(403)
    
    # Datei existiert?
    if not certificate.exists_on_disk:
        app.logger.error(f"Certificate file missing: {certificate.file_path}")
        abort(404)
    
    try:
        # PDF-Datei senden
        return send_file(
            certificate.file_path,
            as_attachment=True,
            download_name=certificate.filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f"File serving failed: {str(e)}")
        abort(500)

@app.route('/download/tax-receipt/<int:certificate_id>')
@limiter.limit("10 per minute")
def download_tax_receipt(certificate_id):
    """Download für Spendenbescheinigungen"""
    
    certificate = Certificate.query.get_or_404(certificate_id)
    
    # Nur Tax-Receipts erlauben
    if certificate.certificate_type != 'tax_receipt':
        abort(404)
    
    # Gleiche Sicherheitsprüfungen
    if not can_access_certificate(certificate):
        abort(403)
    
    if not certificate.exists_on_disk:
        abort(404)
    
    try:
        return send_file(
            certificate.file_path,
            as_attachment=True,
            download_name=certificate.filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f"Tax receipt serving failed: {str(e)}")
        abort(500)

def can_access_certificate(certificate):
    """Prüft ob aktueller User auf Certificate zugreifen darf"""
    
    # Session-basierte Zugriffskontrolle
    session_donations = session.get('completed_donations', [])
    
    # User darf auf Certificate zugreifen wenn:
    # 1. Certificate gehört zu einer Donation aus aktueller Session
    if certificate.donation_id in session_donations:
        return True
    
    # 2. PDFs wurden in aktueller Session generiert
    if session.get('pdfs_generated') and certificate.donation_id in session_donations:
        return True
    
    # 3. Time-based access (PDFs sind 24h nach Generierung verfügbar)
    if certificate.generated_at:
        hours_since_generation = (datetime.utcnow() - certificate.generated_at).total_seconds() / 3600
        if hours_since_generation <= 24:
            return True
    
    return False

def is_pdf_access_valid():
    """Prüft ob PDF-Zugriff noch gültig ist"""
    if 'pdf_access_expires_at' not in session:
        return False
    
    try:
        expires_at = datetime.fromisoformat(session['pdf_access_expires_at'])
        return datetime.utcnow() < expires_at
    except (ValueError, TypeError):
        return False

@app.before_request
def check_pdf_session_expiry():
    """Bereinigt abgelaufene PDF-Sessions automatisch"""
    if 'pdf_access_expires_at' in session and not is_pdf_access_valid():
        cleanup_pdf_session()

def cleanup_pdf_session():
    """Bereinigt PDF-spezifische Session-Daten"""
    keys_to_remove = [
        'completed_donations',
        'pdfs_generated', 
        'pdf_access_granted_at',
        'pdf_access_expires_at'
    ]
    
    for key in keys_to_remove:
        session.pop(key, None)

@app.route('/api/track-download', methods=['POST'])
@limiter.limit("30 per minute")
def api_track_download():
    """Optional tracking endpoint for PDF downloads"""
    try:
        data = request.get_json()
        document_type = data.get('document_type')
        donation_id = data.get('donation_id')
        
        app.logger.info(f"Download tracked: {document_type} for donation {donation_id}")
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.warning(f"Download tracking failed: {e}")
        return jsonify({'status': 'ignored'}), 200

# ==========================================
# STRIPE PAYMENT ROUTES
# ==========================================

@app.route("/checkout/zahlung")
def checkout_zahlung():
    """Payment page with Stripe Elements (SEPA preference)"""
    # Validate cart exists and has items
    handle_corrupted_session()
    
    if 'cart' not in session or not session['cart']:
        flash("Ihr Spendenkorb ist leer. Bitte wählen Sie zuerst einen Vers aus.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Validate all cart items are still available
    cart_items = session['cart']
    unavailable_count = 0
    
    for item in cart_items:
        verse = Verse.query.get(item['verse_id'])
        if not verse or verse.is_sponsored:
            unavailable_count += 1
    
    if unavailable_count > 0:
        flash(f"Achtung: {unavailable_count} Vers(e) in Ihrem Korb sind zwischenzeitlich gesponsert worden. Bitte aktualisieren Sie Ihren Warenkorb.", "danger")
        return redirect(url_for("spendenkorb"))
    
    # Calculate totals
    total_amount = len(cart_items) * 100  # €100 per verse
    
    # Get person from database (required for new checkout flow)
    if 'checkout_person_id' not in session:
        flash("Bitte füllen Sie zuerst Ihre Daten aus.", "warning")
        return redirect(url_for("checkout_spendendaten"))
    
    person = Person.query.get(session['checkout_person_id'])
    if not person:
        flash("Ihre Daten konnten nicht gefunden werden.", "danger")
        return redirect(url_for("checkout_spendendaten"))
    
    # Load verses for display
    verse_ids = [item['verse_id'] for item in cart_items]
    verses = Verse.query.filter(Verse.id.in_(verse_ids)).all()
    verses_dict = {v.id: v for v in verses}
    
    # Prepare cart display data
    cart_display = []
    for item in cart_items:
        verse = verses_dict.get(item['verse_id'])
        if verse:
            cart_display.append({
                'verse': verse,
                'amount': item['amount']
            })
    
    return render_template("checkout-zahlung.html", 
                         cart_items=cart_display,
                         total_amount=total_amount,
                         person=person,
                         stripe_public_key=os.environ.get('STRIPE_PUBLIC_KEY'))

@app.route("/checkout/create-payment-intent", methods=["POST"])
@limiter.limit("10 per minute")  # Prevent DoS attacks on payment API
def create_payment_intent():
    """Create Stripe PaymentIntent for cart"""
    try:
        # Validate cart
        handle_corrupted_session()
        
        if 'cart' not in session or not session['cart']:
            return jsonify({'error': 'Empty cart'}), 400
        
        cart_items = session['cart']
        
        # Validate all verses are still available
        for item in cart_items:
            verse = Verse.query.get(item['verse_id'])
            if not verse or verse.is_sponsored:
                return jsonify({'error': f'Verse {item["verse_id"]} is no longer available'}), 400
        
        # Get person data and create PaymentIntent
        if 'checkout_person_id' not in session:
            return jsonify({'error': 'Invalid person data'}), 400

        person = Person.query.get(session['checkout_person_id'])
        if not person:
            return jsonify({'error': 'Invalid person data'}), 400

        # Get payment type from request (if provided)
        data = request.get_json() or {}
        payment_type = data.get('payment_type')

        # Map frontend type to Stripe payment method types
        preferred_payment_methods = None
        if payment_type == 'sepa':
            preferred_payment_methods = ['sepa_debit']
        elif payment_type == 'card':
            preferred_payment_methods = ['card']
        # If no payment_type specified, StripeService will use default ['sepa_debit', 'card']

        # Get existing payment intent and donation from session (if any)
        existing_payment_intent_id = session.get('payment_intent_id')
        existing_donation_id = session.get('current_donation_id')

        # Create or update PaymentIntent with person object directly
        payment_data = StripeService.create_payment_intent(
            cart_items,
            person=person,
            preferred_payment_methods=preferred_payment_methods,
            existing_donation_id=existing_donation_id,
            existing_payment_intent_id=existing_payment_intent_id
        )

        # Store PaymentIntent ID and Donation ID in session for later verification
        session['payment_intent_id'] = payment_data['payment_intent_id']
        session['current_donation_id'] = payment_data['donation_id']
        session.modified = True

        # Log whether we reused or created new
        if payment_data.get('reused'):
            app.logger.info(f"Reused existing PaymentIntent {payment_data['payment_intent_id']} and donation {payment_data['donation_id']}")
        else:
            app.logger.info(f"Created new PaymentIntent {payment_data['payment_intent_id']} and donation {payment_data['donation_id']}")

        return jsonify({
            'success': True,
            'client_secret': payment_data['client_secret'],
            'amount': payment_data['amount'],
            'reused': payment_data.get('reused', False)
        })
        
    except StripeError as e:
        app.logger.error(f"Stripe error creating PaymentIntent: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error creating PaymentIntent: {e}")
        return jsonify({'error': 'Payment initialization failed'}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    app.logger.warning(f"Rate limit exceeded from IP: {request.remote_addr}")
    return jsonify({
        'error': 'Zu viele Anfragen. Bitte warten Sie einen Moment und versuchen Sie es erneut.',
        'retry_after': getattr(e, 'retry_after', 60)
    }), 429

@app.route("/stripe/webhook", methods=["POST"])
@csrf.exempt
@limiter.limit("100 per minute") # Allow high webhook volume but prevent abuse
def stripe_webhook():
    """Handle Stripe webhook events with improved error handling"""
    
    event_type = None
    event_id = None
    
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        # Validate configuration
        if not webhook_secret:
            app.logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return 'Webhook configuration error', 400
        
        if not signature:
            app.logger.warning("Webhook request missing Stripe-Signature header")
            return 'Missing signature', 400
        
        # Verify webhook signature
        try:
            event = StripeService.verify_webhook_signature(payload, signature, webhook_secret)
            event_type = event.get('type')
            event_id = event.get('id')
        except StripeError as e:
            app.logger.error(f"Webhook signature verification failed for event: {str(e)}")
            return 'Invalid signature', 400
        except ValueError as e:
            app.logger.error(f"Invalid webhook payload format: {str(e)}")
            return 'Invalid payload', 400
        
        # Log received event (safe data only)
        app.logger.info(f"Processing webhook: {event_type} (ID: {event_id})")
        
        # Handle the event with detailed error tracking
        try:
            success = StripeService.handle_webhook_event(event)
            
            if success:
                app.logger.info(f"Successfully processed webhook: {event_type} (ID: {event_id})")
                return 'OK', 200
            else:
                app.logger.error(f"Failed to process webhook: {event_type} (ID: {event_id}) - Business logic error")
                # Return 500 to trigger Stripe retry
                return 'Event processing failed', 500
                
        except Exception as processing_error:
            app.logger.error(f"Exception processing webhook {event_type} (ID: {event_id}): {str(processing_error)}")
            app.logger.error(f"Processing error details: {processing_error.__class__.__name__}")
            # Return 500 to trigger Stripe retry
            return 'Processing exception', 500
            
    except ImportError as e:
        app.logger.critical(f"Failed to import StripeService: {e}")
        return 'Service unavailable', 503
        
    except Exception as e:
        app.logger.error(f"Unexpected webhook handler error: {str(e)} (Type: {event_type}, ID: {event_id})")
        app.logger.error(f"Error class: {e.__class__.__name__}")
        # Return 500 to ensure Stripe retries the webhook
        return 'Internal server error', 500

@app.route("/checkout/erfolg")
def checkout_erfolg():
    """Success page after payment - displays existing PDFs generated by webhook.

    This page no longer generates PDFs or sends emails. All fulfillment is handled
    by the Stripe webhook. This page only loads and displays existing certificates.

    Access methods:
    1. donation_id URL parameter (from /api/donation/status redirect)
    2. session['current_donation_id'] (fallback)

    Note: No Stripe API calls here - all data comes from database (set by webhook).
    """
    donation_id = None

    # Method 1: Direct donation_id parameter (from payment-status.js redirect)
    donation_id_param = request.args.get('donation_id')
    if donation_id_param and donation_id_param.isdigit():
        donation_id = int(donation_id_param)

    # Method 2: Fallback to session
    if not donation_id:
        donation_id = session.get('current_donation_id')

    # Validate donation_id exists
    if not donation_id:
        app.logger.warning("No donation_id found for success page")
        flash("Keine Spende gefunden. Bitte kontaktieren Sie uns bei Fragen.", "warning")
        return redirect(url_for("index"))

    # Security check: Donation must belong to current session
    current_donation_id = session.get('current_donation_id')
    completed_donations = session.get('completed_donations', [])

    if donation_id != current_donation_id and donation_id not in completed_donations:
        app.logger.warning(
            f"Unauthorized success page access: requested={donation_id}, "
            f"current={current_donation_id}, completed={completed_donations}"
        )
        flash("Zugriff nicht autorisiert.", "error")
        return redirect(url_for("index"))

    # Load donation from database
    donation = Donation.query.get(donation_id)
    if not donation:
        app.logger.error(f"Donation {donation_id} not found in database")
        flash("Spende nicht gefunden.", "error")
        return redirect(url_for("index"))

    # Check if webhook has completed fulfillment (PDFs generated, email sent)
    if not donation.certificate_sent_at:
        # Webhook hasn't finished yet - redirect back to processing page
        app.logger.info(
            f"Donation {donation_id} certificate_sent_at is NULL, "
            f"redirecting back to processing page"
        )
        flash("Ihre Zahlung wird noch verarbeitet. Bitte warten Sie einen Moment.", "info")
        return redirect(url_for("checkout_verarbeitung"))

    # Clear cart and checkout data (donation is complete)
    session.pop('cart', None)
    session.pop('shared_donor_data', None)
    session.pop('payment_intent_id', None)
    session.pop('current_donation_id', None)
    session.pop('checkout_person_id', None)
    session.modified = True

    # Load existing PDFs (generated by webhook) and prepare template context
    template_context = _prepare_existing_pdfs_context(donation, session.sid)

    app.logger.info(f"Rendering success page for donation {donation_id} with existing PDFs")
    return render_template("checkout-erfolg.html", **template_context)

def _prepare_existing_pdfs_context(donation, session_id):
    """Lädt existierende PDFs für eine Donation (Webhook hat bereits generiert).

    Diese Funktion wird aufgerufen wenn certificate_sent_at bereits gesetzt ist,
    d.h. der Webhook hat bereits PDFs generiert und E-Mail gesendet.
    Wir laden nur die existierenden Certificate-Records aus der DB.

    Args:
        donation: Donation-Objekt
        session_id: Session ID für PDF-Access-Kontrolle

    Returns:
        dict: Template-Context mit existierenden PDF-Links
    """
    from sqlalchemy import func

    # Lade existierende Certificates aus der DB
    existing_certs = Certificate.query.filter_by(donation_id=donation.id).all()

    certificate_links = []
    tax_receipt_links = []

    for cert in existing_certs:
        if cert.certificate_type in ('personal_certificate', 'sponsorship'):
            certificate_links.append({
                'donation_id': cert.donation_id,
                'download_url': cert.get_download_url(),
                'filename': cert.filename,
                'type': cert.certificate_type
            })
        elif cert.certificate_type == 'tax_receipt':
            tax_receipt_links.append({
                'donation_id': cert.donation_id,
                'download_url': cert.get_download_url(),
                'filename': cert.filename
            })

    # Verse-Referenzen sammeln
    verse_references = []
    for verse_assoc in donation.verse_associations:
        verse_references.append(verse_assoc.verse.german_reference)
    verse_reference = verse_references[0] if len(verse_references) == 1 else None

    # Setup PDF session for access control
    setup_pdf_session([donation.id], session_id)

    user_email = donation.person.email if donation and donation.person else 'support@peter-schoeffer-stiftung.de'

    app.logger.info(
        f"Loaded {len(certificate_links)} certificates and {len(tax_receipt_links)} tax receipts "
        f"for donation {donation.id} (existing PDFs from webhook)"
    )

    return {
        'user_email': user_email,
        'verse_reference': verse_reference,
        'verse_references': verse_references,
        'certificate_links': certificate_links,
        'tax_receipt_links': tax_receipt_links,
        'total_donations': 1,
        'pdfs_available': len(certificate_links) > 0 or len(tax_receipt_links) > 0,
        'pdfs_from_webhook': True,  # Flag für Template (optional)
        'total_sponsored': Verse.query.filter_by(is_sponsored=True).count(),
        'total_amount': db.session.query(func.sum(Donation.amount)).filter_by(payment_status='completed').scalar() or 0,
        'remaining_verses': Verse.query.filter_by(is_sponsored=False).count()
    }


def setup_pdf_session(donation_ids, session_id):
    """Bereitet Session für PDF-Downloads vor"""
    session['completed_donations'] = donation_ids
    session['session_id'] = session_id
    session['pdf_access_granted_at'] = datetime.utcnow().isoformat()
    session['pdf_access_expires_at'] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    session['pdfs_generated'] = True
    session.permanent = True

@app.route("/checkout/verarbeitung")
def checkout_verarbeitung():
    """Processing page for pending payments (especially SEPA)

    Frontend polls /api/donation/status/<donation_id> to check database status
    set by webhook. No direct Stripe polling from frontend anymore.
    """
    # Get donation_id from session (set during PaymentIntent creation)
    donation_id = session.get('current_donation_id')

    if not donation_id:
        flash("Kein gültiger Zahlungsvorgang gefunden.", "error")
        return redirect(url_for("checkout_zahlung"))

    # Get donation details from database for display
    donation = Donation.query.get(donation_id)
    if not donation:
        flash("Spende nicht gefunden.", "error")
        return redirect(url_for("index"))

    # Use actual donation data for display (more robust than session cart)
    verse_count = donation.verse_count or 1
    total_amount = float(donation.amount)

    return render_template("checkout-verarbeitung.html",
                         donation_id=donation_id,
                         verse_count=verse_count,
                         total_amount=total_amount)

@app.route("/api/donation/status/<int:donation_id>")
@csrf.exempt  # GET requests for status checking don't need CSRF protection
@limiter.limit("30 per minute")  # Allow frequent status checks but prevent abuse
def api_donation_status(donation_id):
    """
    API endpoint to check donation status from database.

    This endpoint is polled by the frontend during payment processing.
    It checks the database status (set by webhooks) rather than Stripe directly.

    Security: Only returns status for donations belonging to current session.

    Returns:
        - status: Current payment_status (pending, processing, completed, failed, disputed)
        - pdfs_ready: Boolean - True when certificate_sent_at is set
        - redirect_url: URL to redirect to when pdfs_ready=True
        - error_redirect_url: URL to redirect to on failure
    """
    try:
        # Security check: Donation must belong to current session
        current_donation_id = session.get('current_donation_id')
        completed_donations = session.get('completed_donations', [])

        if donation_id != current_donation_id and donation_id not in completed_donations:
            app.logger.warning(
                f"Unauthorized donation status check: requested={donation_id}, "
                f"current={current_donation_id}, completed={completed_donations}"
            )
            return jsonify({'error': 'Unauthorized'}), 403

        # Load donation from database
        donation = Donation.query.get(donation_id)
        if not donation:
            app.logger.error(f"Donation {donation_id} not found in database")
            return jsonify({'error': 'Donation not found'}), 404

        # Determine if PDFs are ready (webhook has completed fulfillment)
        pdfs_ready = donation.certificate_sent_at is not None

        # Build response based on status
        response_data = {
            'success': True,
            'donation_id': donation_id,
            'status': donation.payment_status,
            'pdfs_ready': pdfs_ready
        }

        # Add redirect URLs based on status
        if donation.payment_status in ('failed', 'disputed'):
            # Payment failed - redirect to error page
            response_data['error_redirect_url'] = url_for(
                'checkout_fehler',
                reason='payment_failed',
                _external=False
            )
        elif pdfs_ready:
            # PDFs ready - redirect to success page
            response_data['redirect_url'] = url_for(
                'checkout_erfolg',
                donation_id=donation_id,
                _external=False
            )
        # else: still processing - frontend continues polling

        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error checking donation status for {donation_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==========================================

# ==========================================
# NEW CHECKOUT FLOW API ROUTES
# ==========================================

@app.route("/api/cart/count", methods=["GET"])
@csrf.exempt  # GET requests don't need CSRF protection
@limiter.limit("120 per minute")
def api_cart_count():
    """Get cart item count for badge display"""
    try:
        # Handle corrupted session data gracefully
        handle_corrupted_session()
        
        cart_count = len(session.get('cart', []))
        
        return jsonify({
            'success': True,
            'count': cart_count
        })
        
    except Exception as e:
        app.logger.error(f"Error getting cart count: {e}")
        return jsonify({
            'success': False,
            'count': 0
        })

@app.route("/api/cart/add", methods=["POST"])
@limiter.limit("60 per minute")
def api_cart_add():
    """Add item to cart with donation details"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Keine Daten erhalten'}), 400
        
        # Validate input
        verse_id = data.get('verse_id')
        donation_details = data.get('donation_details', {})
        
        if not verse_id:
            return jsonify({'success': False, 'error': 'Ungültige Anfrage'}), 400
        
        # Check verse availability
        verse = Verse.query.get(verse_id)
        if not verse:
            return jsonify({'success': False, 'error': 'Vers nicht gefunden'}), 404
        
        if verse.is_sponsored:
            return jsonify({'success': False, 'error': 'Vers bereits gesponsert'}), 400
        
        # Check if verse is reserved by someone else
        existing_reservation = VerseReservation.get_active_for_verse(
            verse.id, 
            exclude_session_id=session.sid
        )
        
        if existing_reservation:
            return jsonify({'success': False, 'error': 'Vers wird bereits reserviert'}), 400
        
        # Initialize cart if needed and handle corruption
        handle_corrupted_session()
        
        # Check cart size limit
        if len(session['cart']) >= 20:
            return jsonify({
                'success': False, 
                'error': 'Maximale Anzahl Verse (20) erreicht'
            }), 400
        
        # Check for duplicate verses in cart
        if any(item['verse_id'] == verse_id for item in session['cart']):
            return jsonify({'success': False, 'error': 'Vers bereits im Korb'}), 400
        
        # Create/Update reservation for this verse
        try:
            reservation = VerseReservation.create_or_update(
                verse_id=verse.id,
                session_id=session.sid,
                minutes=60  # Extended reservation for cart items
            )
        except Exception as e:
            app.logger.error(f"Failed to create reservation: {e}")
            return jsonify({'success': False, 'error': 'Reservierung fehlgeschlagen'}), 500
        
        # Add to cart with simplified structure for individual donations
        cart_item = {
            'verse_id': verse_id,
            'donor_data': donation_details,  # Use donor_data for compatibility with validate_cart_item
            'reservation_id': reservation.id,
            'amount': 100.00,
            'currency': 'EUR',
            'added_at': datetime.utcnow().isoformat()
        }
        
        session['cart'].append(cart_item)
        session.modified = True
        
        return jsonify({
            'success': True, 
            'cart_count': len(session['cart']),
            'item': {
                'verse_reference': verse.reference,
                'amount': 100.00
            }
        })
        
    except Exception as e:
        app.logger.error(f"API cart add error: {e}")
        return jsonify({'success': False, 'error': 'Interner Serverfehler'}), 500

@app.route("/checkout/spendendaten", methods=["GET", "POST"])
@limiter.limit("30 per minute")
def checkout_spendendaten():
    """Unified data collection after cart"""
    
    # Check cart exists
    if 'cart' not in session or not session['cart']:
        flash("Ihr Spendenkorb ist leer.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    cart_items = []
    
    # Load cart data - simplified structure
    for item in session['cart']:
        verse = Verse.query.get(item['verse_id'])
        if verse:
            cart_items.append({
                'verse': verse,
                'donor_data': item.get('donor_data', {})
            })
    
    total_amount = len(cart_items) * 100
    
    
    if request.method == "POST":
        email = request.form.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            flash("Bitte geben Sie eine gültige E-Mail-Adresse ein.", "danger")
            return render_template("checkout-spendendaten.html",
                                 cart_items=cart_items,
                                 total_amount=total_amount,
                                 form_data=request.form)
        
        wants_receipt = request.form.get('wantsReceipt') == 'on'
        newsletter_consent = request.form.get('newsletter') == 'on'
        
        # Validate receipt data if requested
        person_data = {'email': email, 'newsletter_consent': newsletter_consent}
        if wants_receipt:
            required_fields = ['salutation', 'firstName', 'lastName', 'street', 'houseNumber', 'postalCode', 'city']
            missing_fields = []
            
            for field in required_fields:
                value = request.form.get(field, '').strip()
                if not value:
                    missing_fields.append(field)
                else:
                    # Map form fields to person model fields
                    field_mapping = {
                        'firstName': 'first_name',
                        'lastName': 'last_name',
                        'houseNumber': 'house_number',
                        'postalCode': 'postal_code'
                    }
                    person_field = field_mapping.get(field, field)
                    person_data[person_field] = value
            
            if missing_fields:
                flash("Bitte füllen Sie alle Pflichtfelder für die Spendenbescheinigung aus.", "danger")
                return render_template("checkout-spendendaten.html",
                                     cart_items=cart_items,
                                     total_amount=total_amount,
                                     form_data=request.form)
        
        # Privacy consent validation
        privacy_consent = request.form.get('privacy') == 'on'
        if not privacy_consent:
            flash("Bitte akzeptieren Sie die Datenschutzerklärung.", "danger")
            return render_template("checkout-spendendaten.html",
                                 cart_items=cart_items,
                                 total_amount=total_amount,
                                 form_data=request.form)
        
        # Note: privacy_consent and wants_receipt are donation-specific, not person-specific
        
        # Handle salutation: "Ohne" becomes None/NULL in database
        salutation_value = request.form.get('salutation')
        if salutation_value == 'Ohne':
            salutation_value = None
        person_data['salutation'] = salutation_value
        
        
        # Create or find person
        person = Person.find_or_create(**person_data)
        
        
        db.session.commit()
        
        
        # Store person in session for payment
        session['checkout_person_id'] = person.id
        session['wants_receipt'] = wants_receipt
        session.modified = True
        
        return redirect(url_for('checkout_zahlung'))
    
    return render_template("checkout-spendendaten.html",
                         cart_items=cart_items,
                         total_amount=total_amount,
                         form_data={})



# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return render_template("500.html"), 500

# ==========================================
# PLACEHOLDER ROUTES (for completeness)
# ==========================================

@app.route("/cookies")
def cookies():
    """Cookie policy page"""
    flash("Die Cookie-Richtlinie finden Sie in der Datenschutzerklärung.", "info")
    return redirect(url_for("datenschutz"))

# ==========================================
# HEALTH CHECK ENDPOINTS
# ==========================================

@app.route("/health")
def health_check():
    """Health check endpoint for Docker and load balancers"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'environment': app.config.get('ENV', 'development')
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy', 
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 503

@app.route("/ping")
def ping():
    """Simple ping endpoint"""
    return {'status': 'pong'}, 200

# E-Mail Test Endpoints (Development only)
@app.route("/api/email/test")
@csrf.exempt  # GET requests don't need CSRF protection
@limiter.limit("3 per minute")
def test_email():
    """Test email functionality"""
    try:
        test_email_address = request.args.get('email', 'ue.probst@gmail.com')
        
        if email_service.send_test_email(test_email_address):
            return jsonify({
                'status': 'success',
                'message': f'Test email sent to {test_email_address}',
                'provider': email_service.provider.__class__.__name__
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send test email'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Email test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/email/connection-test")
@csrf.exempt  # GET requests don't need CSRF protection
@limiter.limit("5 per minute") 
def test_email_connection():
    """Test email provider connection"""
    try:
        connection_ok = email_service.test_connection()
        provider_name = email_service.provider.__class__.__name__
        
        return jsonify({
            'status': 'success' if connection_ok else 'error',
            'provider': provider_name,
            'connection': 'OK' if connection_ok else 'FAILED',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Connection test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/email/provider-switch", methods=['POST'])
@limiter.limit("2 per minute")
def switch_email_provider():
    """Switch email provider (for testing)"""
    try:
        new_provider = request.json.get('provider', '').lower()
        
        if new_provider not in ['gmail', 'mailgun']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid provider. Use gmail or mailgun.'
            }), 400
        
        # Update environment and reinitialize
        os.environ['EMAIL_PROVIDER'] = new_provider
        email_service.init_app(current_app)
        
        return jsonify({
            'status': 'success',
            'message': f'Switched to {new_provider} provider',
            'provider': email_service.provider.__class__.__name__
        })
        
    except Exception as e:
        app.logger.error(f"Provider switch failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    # Run in debug mode for development
    port = int(os.environ.get("FLASK_RUN_PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)