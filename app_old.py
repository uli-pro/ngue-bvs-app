import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_from_directory, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required as flask_login_required, current_user
from flask_wtf import FlaskForm, CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
from functools import wraps
# Password hashing handled by models.py with Argon2
import re

# Load environment variables
load_dotenv()

# Configure application
app = Flask(__name__)

# Load configuration from environment
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize extensions
from models import db, User, Verse, Donation, VerificationToken, ResetToken, VerseReservation
db.init_app(app)

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

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

# Login attempts tracking (TODO: Move to database table later)
login_attempts = {}

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
        # current_user is automatically available via Flask-Login
    }


# ==========================================
# HELPER FUNCTIONS FOR USER MANAGEMENT
# ==========================================

def generate_verification_token():
    """Generate a secure verification token."""
    return secrets.token_urlsafe(32)


# ==========================================
# CART VALIDATION AND RECOVERY FUNCTIONS
# ==========================================

def validate_cart_item(item):
    """Validate cart item structure and content."""
    if not isinstance(item, dict):
        return False
    
    required_fields = ['verse_id', 'donation_type', 'donor_data', 'amount']
    
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
    
    if item['donation_type'] not in ['einzelperson', 'gruppe', 'geschenk']:
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
    if not isinstance(cart, list):
        return []
    
    valid_items = []
    for item in cart:
        if validate_cart_item(item):
            # Ensure currency field exists
            if 'currency' not in item:
                item['currency'] = 'EUR'
            valid_items.append(item)
    
    return valid_items


def handle_corrupted_session():
    """Handle corrupted session data gracefully."""
    try:
        # Initialize empty cart if missing or corrupted
        if 'cart' not in session or not isinstance(session['cart'], list):
            session['cart'] = []
        else:
            # Sanitize existing cart
            session['cart'] = sanitize_cart(session['cart'])
        
        session.modified = True
        
    except Exception as e:
        # If all else fails, reset cart completely
        session['cart'] = []
        session.modified = True
        app.logger.error(f"Session corruption recovery failed: {e}")

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Das Passwort muss mindestens 8 Zeichen lang sein."
    if not re.search(r"[A-Z]", password):
        return False, "Das Passwort muss mindestens einen Großbuchstaben enthalten."
    if not re.search(r"[a-z]", password):
        return False, "Das Passwort muss mindestens einen Kleinbuchstaben enthalten."
    if not re.search(r"\d", password):
        return False, "Das Passwort muss mindestens eine Zahl enthalten."
    return True, ""

def check_rate_limit(email):
    """Check if user has exceeded login attempts."""
    if email not in login_attempts:
        login_attempts[email] = {"count": 0, "last_attempt": datetime.now()}
        return True
    
    attempts = login_attempts[email]
    time_diff = datetime.now() - attempts["last_attempt"]
    
    # Reset counter after 15 minutes
    if time_diff > timedelta(minutes=15):
        attempts["count"] = 0
        attempts["last_attempt"] = datetime.now()
        return True
    
    # Allow max 5 attempts
    if attempts["count"] >= 5:
        return False
    
    return True

def create_user(email, password, first_name, last_name, newsletter=False):
    """Create a real user account in database."""
    verification_token = generate_verification_token()
    
    # Create new user with Argon2 password hashing
    user = User(
        email=email.lower(),
        first_name=first_name,
        last_name=last_name,
        newsletter_opt_in=newsletter,
        is_verified=False  # Needs email verification
    )
    
    # Set password using Argon2 (from models.py)
    user.set_password(password)
    
    # Save to database
    db.session.add(user)
    db.session.commit()
    
    # Create verification token in database
    token_obj = VerificationToken(
        user_id=user.id,
        token=verification_token
    )
    db.session.add(token_obj)
    db.session.commit()
    
    return user.id, verification_token

def verify_user_email(token):
    """Verify user email with token."""
    token_obj = VerificationToken.query.filter_by(token=token, used=False).first()
    
    if not token_obj:
        return False, None
    
    if token_obj.is_expired:
        return False, None
    
    # Mark user as verified
    user = token_obj.user
    user.is_verified = True
    
    # Mark token as used
    token_obj.used = True
    
    db.session.commit()
    return True, user.id

def find_user_by_email(email):
    """Find user by email address from database."""
    return User.query.filter_by(email=email.lower()).first()

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

@app.route("/ueber-stiftung")
def ueber_stiftung():
    """About Peter-Schöffer-Stiftung page"""
    return render_template("ueber-stiftung.html")

@app.route("/ueber-verlage")
def ueber_verlage():
    """About the publishing houses page"""
    return render_template("ueber-verlage.html")

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
        
        # Return only books that exist in database, in biblical order
        book_list = [book for book in biblical_order if book in available_books]
        
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
@csrf.exempt
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
    """Donation type selection page with reservation system"""
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
    
    # Check ob bereits gesponsert
    if verse.is_sponsored:
        flash(f"Dieser Vers wurde inzwischen gesponsert. Bitte wählen Sie einen anderen.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Check ob bereits reserviert (von anderem User)
    existing_reservation = VerseReservation.get_active_for_verse(
        verse.id, 
        exclude_session_id=session.sid
    )
    
    if existing_reservation:
        flash(f"Der Vers {verse.reference} wird gerade von einem anderen Nutzer reserviert. Bitte wählen Sie einen anderen.", "info")
        return redirect(url_for("vers_auswaehlen"))
    
    # Erstelle/Update eigene Reservierung
    reservation = VerseReservation.create_or_update(
        verse_id=verse.id,
        session_id=session.sid,
        minutes=15
    )
    
    # Speichere in Session
    session['selected_verse_id'] = verse.id
    session['reservation_id'] = reservation.id
    
    # Handle POST request (donation type selection)
    if request.method == "POST":
        donation_type = request.form.get('donation_type')
        if donation_type in ['einzelperson', 'gruppe', 'geschenk']:
            session['donation_type'] = donation_type
            return redirect(url_for("checkout_daten", donation_type=donation_type))
        else:
            flash("Bitte wählen Sie eine gültige Spendenart.", "error")
            return redirect(url_for("vers_auswaehlen"))
    
    return render_template("vers-spendenart.html", verse=verse)

@app.route("/vers/<int:verse_id>/spendenart", methods=["GET", "POST"])
def vers_spendenart_by_id(verse_id):
    """Donation type selection page with reservation system (by numeric ID)"""
    # Find verse by numeric ID
    verse = Verse.query.get(verse_id)
    
    if not verse:
        flash("Dieser Vers wurde nicht gefunden.", "error")
        return redirect(url_for("vers_auswaehlen"))
    
    # Check if already sponsored
    if verse.is_sponsored:
        flash(f"Dieser Vers wurde inzwischen gesponsert. Bitte wählen Sie einen anderen.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Check if already reserved (by another user)
    existing_reservation = VerseReservation.get_active_for_verse(
        verse.id, 
        exclude_session_id=session.sid
    )
    
    if existing_reservation:
        flash(f"Der Vers {verse.reference} wird gerade von einem anderen Nutzer reserviert. Bitte wählen Sie einen anderen.", "info")
        return redirect(url_for("vers_auswaehlen"))
    
    # Create/Update own reservation
    reservation = VerseReservation.create_or_update(
        verse_id=verse.id,
        session_id=session.sid,
        minutes=15
    )
    
    # Store in session
    session['selected_verse_id'] = verse.id
    session['reservation_id'] = reservation.id
    
    # Handle POST request (donation type selection)
    if request.method == "POST":
        donation_type = request.form.get('donation_type')
        if donation_type in ['einzelperson', 'gruppe', 'geschenk']:
            session['donation_type'] = donation_type
            return redirect(url_for("checkout_daten", donation_type=donation_type))
        else:
            flash("Bitte wählen Sie eine gültige Spendenart.", "error")
            return redirect(url_for("vers_auswaehlen"))
    
    return render_template("vers-spendenart.html", verse=verse)

# ==========================================
# CHECKOUT ROUTES
# ==========================================

@app.route("/checkout/<donation_type>/daten", methods=["GET", "POST"])
def checkout_daten(donation_type):
    """Data collection for different donation types with reservation validation"""
    if donation_type not in ['einzelperson', 'gruppe', 'geschenk']:
        flash("Ungültiger Spendentyp.", "error")
        return redirect(url_for("vers_auswaehlen"))
    
    # Check ob Vers ausgewählt
    if 'selected_verse_id' not in session:
        flash("Bitte wählen Sie zuerst einen Vers aus.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Check ob Reservierung noch gültig
    if 'reservation_id' in session:
        reservation = VerseReservation.query.get(session['reservation_id'])
        if not reservation or reservation.is_expired:
            flash("Ihre Reservierung ist abgelaufen. Bitte wählen Sie erneut.", "warning")
            session.pop('selected_verse_id', None)
            session.pop('reservation_id', None)
            return redirect(url_for("vers_auswaehlen"))
        
        # Verlängere Reservierung bei Aktivität
        reservation.extend_reservation(15)
    
    # Store donation type in session
    session['donation_type'] = donation_type
    
    # Load verse for display
    verse = Verse.query.get(session['selected_verse_id'])
    
    if request.method == "POST":
        # Collect and validate form data
        form_data = {}
        errors = []
        
        # Basic email (required for all types)
        email = request.form.get('email', '').strip()
        if not email or '@' not in email:
            errors.append("Bitte geben Sie eine gültige E-Mail-Adresse ein.")
        if len(email) > 255:
            errors.append("E-Mail-Adresse ist zu lang (max. 255 Zeichen).")
        form_data['email'] = email
        
        # Privacy consent (required)
        privacy_consent = request.form.get('privacy') == 'on'
        if not privacy_consent:
            errors.append("Bitte akzeptieren Sie die Datenschutzerklärung.")
        form_data['privacy_consent'] = privacy_consent
        
        # Newsletter (optional)
        form_data['newsletter'] = request.form.get('newsletter') == 'on'
        
        # Type-specific validation and data collection
        if donation_type == 'gruppe':
            # Group-specific fields with length validation
            group_article = request.form.get('group_article', '').strip()[:20]
            group_name = request.form.get('group_name', '').strip()[:200]
            
            if not group_article:
                errors.append("Bitte wählen Sie einen Artikel für den Gruppennamen.")
            if not group_name:
                errors.append("Bitte geben Sie den Namen der Gruppe ein.")
                
            form_data['group_article'] = group_article
            form_data['group_name'] = group_name
            form_data['wants_receipt'] = False  # Groups can't get automatic receipts
            
        else:
            # Individual and gift donations need receipt data
            wants_receipt = request.form.get('wantReceipt') == 'on'
            form_data['wants_receipt'] = wants_receipt
            
            if wants_receipt:
                # Collect receipt data with length validation
                salutation = request.form.get('salutation', '').strip()
                first_name = request.form.get('firstName', '').strip()[:100]  # Limit length
                last_name = request.form.get('lastName', '').strip()[:100]
                street = request.form.get('street', '').strip()[:200]
                house_number = request.form.get('houseNumber', '').strip()[:10]
                postal_code = request.form.get('postalCode', '').strip()[:10]
                city = request.form.get('city', '').strip()[:100]
                country = request.form.get('country', 'DE').strip()[:2]
                
                # Validate required receipt fields
                if not salutation:
                    errors.append("Bitte wählen Sie eine Anrede.")
                if not first_name:
                    errors.append("Bitte geben Sie Ihren Vornamen ein.")
                if not last_name:
                    errors.append("Bitte geben Sie Ihren Nachnamen ein.")
                if not street:
                    errors.append("Bitte geben Sie Ihre Straße ein.")
                if not house_number:
                    errors.append("Bitte geben Sie Ihre Hausnummer ein.")
                if not postal_code:
                    errors.append("Bitte geben Sie Ihre Postleitzahl ein.")
                if not city:
                    errors.append("Bitte geben Sie Ihren Ort ein.")
                    
                form_data.update({
                    'salutation': salutation,
                    'title': request.form.get('title', '').strip(),
                    'first_name': first_name,
                    'last_name': last_name,
                    'street': street,
                    'house_number': house_number,
                    'postal_code': postal_code,
                    'city': city,
                    'country': country
                })
        
        # Gift-specific fields
        if donation_type == 'geschenk':
            gift_recipient_name = request.form.get('gift_recipient_name', '').strip()[:200]  # Limit length
            gift_direct_send = request.form.get('gift_direct_send') == 'on'
            # HTML-strip and limit gift message for security
            import html
            gift_message = html.escape(request.form.get('gift_message', '').strip())[:1000]
            
            if not gift_recipient_name:
                errors.append("Bitte geben Sie den Namen des Empfängers ein.")
                
            form_data['gift_recipient_name'] = gift_recipient_name
            form_data['gift_direct_send'] = gift_direct_send
            form_data['gift_message'] = gift_message
            
            if gift_direct_send:
                gift_recipient_email = request.form.get('gift_recipient_email', '').strip()
                if not gift_recipient_email or '@' not in gift_recipient_email:
                    errors.append("Bitte geben Sie eine gültige E-Mail-Adresse des Empfängers ein.")
                form_data['gift_recipient_email'] = gift_recipient_email
        
        # If validation failed, show errors and return form
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("checkout-daten.html", donation_type=donation_type, verse=verse, form_data=form_data)
        
        # Initialize cart if not exists and handle corruption
        handle_corrupted_session()
        
        # Check cart size limit (security: prevent session overflow)
        if len(session['cart']) >= 20:
            flash("Sie können maximal 20 Verse gleichzeitig sponsern. Bitte vervollständigen Sie zuerst Ihre aktuelle Spende.", "warning")
            return redirect(url_for("spendenkorb"))
        
        # Check for duplicate verses in cart (fallback security check)
        selected_verse_id = session['selected_verse_id']
        if any(item['verse_id'] == selected_verse_id for item in session['cart']):
            flash("Dieser Vers befindet sich bereits in Ihrem Spendenkorb.", "warning")
            return redirect(url_for("vers_auswaehlen"))
        
        # Add verse to cart with all data
        cart_item = {
            'verse_id': session['selected_verse_id'],
            'donation_type': donation_type,
            'donor_data': form_data,
            'reservation_id': session.get('reservation_id'),
            'amount': 100.00,
            'currency': 'EUR'
        }
        
        # Add to cart
        session['cart'].append(cart_item)
        session.modified = True
        
        # Clear current verse selection (will be handled by cart now)
        session.pop('selected_verse_id', None)
        session.pop('reservation_id', None)
        session.pop('checkout_data', None)
        
        # Store/Update shared donor data for future verse additions
        session['shared_donor_data'] = form_data
        
        # Redirect to cart page
        return redirect(url_for("spendenkorb"))
    
    # Pre-fill form with shared donor data if available
    form_data = session.get('shared_donor_data', {})
    
    return render_template("checkout-daten.html", 
                         donation_type=donation_type, 
                         verse=verse, 
                         form_data=form_data)

@app.route("/spendenkorb")
def spendenkorb():
    """Donation cart page showing all selected verses"""
    # Handle corrupted session data gracefully
    handle_corrupted_session()
    
    # Check if cart exists and has items
    if 'cart' not in session or not session['cart']:
        flash("Ihr Spendenkorb ist leer. Bitte wählen Sie zuerst einen Vers aus.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
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
            'donation_type': item['donation_type'],
            'donor_data': item['donor_data'],
            'amount': item['amount'],
            'currency': item.get('currency', 'EUR'),  # Safe fallback for missing currency
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
    """Remove item from cart via AJAX"""
    try:
        # Handle corrupted session data gracefully
        handle_corrupted_session()
        
        data = request.get_json()
        item_index = data.get('item_index') if data else None
        
        if 'cart' not in session or item_index is None:
            return jsonify({'success': False, 'message': 'Invalid request'})
        
        # Security: Validate item_index is integer and in valid range
        try:
            item_index = int(item_index)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid item index'})
        
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
            
            return jsonify({'success': True, 'message': 'Item removed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Item not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


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

@app.route("/checkout/fehler")
def checkout_fehler():
    """Error page for failed payments"""
    return render_template("checkout-fehler.html")

# ==========================================
# USER ROUTES
# ==========================================

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def login():
    """Login page"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        
        # Validate input
        if not email or not password:
            flash("Bitte geben Sie E-Mail und Passwort ein.", "danger")
            return render_template("login.html")
        
        # Check if user exists in database
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user:
            flash("Unbekannte E-Mail-Adresse oder falsches Passwort.", "danger")
            return render_template("login.html")
        
        # Check if user is verified
        if not user.is_verified:
            flash("Bitte bestätigen Sie erst Ihre E-Mail-Adresse.", "warning")
            return render_template("login.html")
        
        # Verify password
        if not user.check_password(password):
            flash("Unbekannte E-Mail-Adresse oder falsches Passwort.", "danger")
            return render_template("login.html")
        
        # Login user with Flask-Login
        login_user(user, remember=remember)
        
        flash(f"Willkommen, {user.first_name}!", "success")
        
        # Redirect to next URL or dashboard
        next_url = session.pop("next_url", None)
        if next_url:
            return redirect(next_url)
        return redirect(url_for("dashboard"))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    logout_user()
    # Keep some session data that's not user-specific (like CSRF token)
    # Only clear user-specific data
    session.pop("next_url", None)
    flash("Sie wurden erfolgreich abgemeldet.", "info")
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per 10 minutes")
def register():
    """Registration page"""
    if request.method == "POST":
        # Get form data
        first_name = request.form.get("vorname", "").strip()
        last_name = request.form.get("nachname", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        newsletter = request.form.get("newsletter") == "on"
        datenschutz = request.form.get("datenschutz") == "on"
        
        # Validation
        errors = []
        
        if not first_name or not last_name:
            errors.append("Bitte geben Sie Ihren vollständigen Namen ein.")
        
        if not email or "@" not in email:
            errors.append("Bitte geben Sie eine gültige E-Mail-Adresse ein.")
        
        # Check if email already exists
        if find_user_by_email(email):
            errors.append("Diese E-Mail-Adresse ist bereits registriert.")
        
        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            errors.append(error_msg)
        
        if password != password_confirm:
            errors.append("Die Passwörter stimmen nicht überein.")
        
        if not datenschutz:
            errors.append("Bitte stimmen Sie der Datenschutzerklärung zu.")
        
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html")
        
        # Create user account in database
        user_id, verification_token = create_user(
            email, password, first_name, last_name, newsletter
        )
        
        # Store some data in session for the success page
        session["registration_email"] = email
        session["registration_token"] = verification_token
        
        # Redirect to success page
        return redirect(url_for("registration_success"))
    
    return render_template("register.html")

# ==========================================
# NEW ACCOUNT ROUTES
# ==========================================

@app.route("/registration/success")
def registration_success():
    """Registration success page"""
    email = session.get("registration_email")
    token = session.get("registration_token")
    
    if not email:
        return redirect(url_for("register"))
    
    # Clear session data
    session.pop("registration_email", None)
    session.pop("registration_token", None)
    
    return render_template("registration-success.html", email=email, token=token)

@app.route("/verify/<token>")
def verify_email(token):
    """Verify email address with token"""
    success, user_id = verify_user_email(token)
    
    if success:
        flash("Ihre E-Mail-Adresse wurde erfolgreich bestätigt! Sie können sich nun anmelden.", "success")
        return redirect(url_for("login"))
    else:
        flash("Der Bestätigungslink ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("index"))

@app.route("/password/reset", methods=["GET", "POST"])
@limiter.limit("3 per 30 minutes")
def password_reset_request():
    """Request password reset"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        
        if not email:
            flash("Bitte geben Sie Ihre E-Mail-Adresse ein.", "danger")
            return render_template("password-reset-request.html")
        
        user = find_user_by_email(email)
        
        if user:
            # Generate reset token
            reset_token = generate_verification_token()
            
            # Create reset token in database
            token_obj = ResetToken(
                user_id=user.id,
                token=reset_token
            )
            db.session.add(token_obj)
            db.session.commit()
            
            # In production, send email here
            # For demo, show the token
            flash(f"Demo: Passwort-Reset-Link: /password/reset/{reset_token}", "info")
        
        # Always show success message (security: don't reveal if email exists)
        flash("Wenn die E-Mail-Adresse in unserem System existiert, haben wir Ihnen einen Link zum Zurücksetzen des Passworts gesendet.", "success")
        return redirect(url_for("login"))
    
    return render_template("password-reset-request.html")

@app.route("/password/reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    """Reset password with token"""
    # Check if token is valid
    token_obj = ResetToken.query.filter_by(token=token, used=False).first()
    
    if not token_obj:
        flash("Der Passwort-Reset-Link ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("password_reset_request"))
    
    # Check if token is expired
    if token_obj.is_expired:
        flash("Der Passwort-Reset-Link ist abgelaufen.", "danger")
        return redirect(url_for("password_reset_request"))
    
    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        
        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("password-reset.html", token=token)
        
        if password != password_confirm:
            flash("Die Passwörter stimmen nicht überein.", "danger")
            return render_template("password-reset.html", token=token)
        
        # Update password
        user = token_obj.user
        user.set_password(password)
        
        # Mark token as used
        token_obj.used = True
        
        db.session.commit()
        flash("Ihr Passwort wurde erfolgreich zurückgesetzt. Sie können sich nun anmelden.", "success")
        return redirect(url_for("login"))
    
    return render_template("password-reset.html", token=token)

@app.route("/meine-verse")
@flask_login_required
def meine_verse():
    """My verses page (requires login)"""
    
    # Demo verse data
    verses = [
        {
            'id': 'jeremia-29-11',
            'reference': 'Jeremia 29,11',
            'text': 'Denn ich weiß die Gedanken, die ich über euch denke, spricht der HERR, Gedanken des Friedens und nicht des Unheils, euch eine Zukunft und Hoffnung zu geben.',
            'type': 'einzelperson',
            'date': '2025-08-08',
            'book': 'jeremia'
        },
        {
            'id': 'psalm-23-1',
            'reference': 'Psalm 23,1',
            'text': 'Der HERR ist mein Hirte; mir wird nichts mangeln.',
            'type': 'geschenk',
            'date': '2025-08-05',
            'book': 'psalm',
            'gift_recipient': 'Anna Mustermann'
        },
        {
            'id': 'sprueche-3-5-6',
            'reference': 'Sprüche 3,5-6',
            'text': 'Vertraue auf den HERRN von ganzem Herzen und verlaß dich nicht auf deinen Verstand; erkenne ihn auf allen deinen Wegen, so wird er deine Pfade ebnen!',
            'type': 'gruppe',
            'date': '2025-08-01',
            'book': 'sprueche',
            'group_name': 'Die Familie Schmidt'
        }
    ]
    
    return render_template("meine-verse.html", verses=verses)

@app.route("/profil")
@flask_login_required
def profil():
    """Profile page (requires login)"""
    return render_template("profil.html")

@app.route("/dashboard")
@flask_login_required
def dashboard():
    """User dashboard"""
    # Get same statistics as homepage for consistency
    total_verses = Verse.query.count()
    sponsored_verses = Verse.query.filter_by(is_sponsored=True).count()
    available_verses = total_verses - sponsored_verses
    percentage = round((sponsored_verses / total_verses * 100), 1) if total_verses > 0 else 0
    
    stats = {
        'total_verses': total_verses,
        'sponsored_verses': sponsored_verses,
        'available_verses': available_verses,
        'percentage': percentage,
        'total_amount': sponsored_verses * 100  # Calculate total amount raised
    }
    
    return render_template("dashboard.html", user=current_user, stats=stats)


# ==========================================
# CONTACT ROUTES
# ==========================================

@app.route("/kontakt", methods=["GET", "POST"])
def kontakt():
    """Contact page"""
    if request.method == "POST":
        # Handle contact form submission
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        
        # Here you would normally send an email or save to database
        flash(f"Vielen Dank für Ihre Nachricht, {name}! Wir werden uns in Kürze bei Ihnen melden.", "success")
        return redirect(url_for("index"))
    
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
# DOWNLOAD ROUTES
# ==========================================

@app.route("/downloads/zertifikat-demo.pdf")
def download_zertifikat():
    """Download demo certificate"""
    return render_template("dummy-zertifikat.html")

@app.route("/downloads/spendenbescheinigung-demo.pdf")
def download_spendenbescheinigung():
    """View demo donation receipt"""
    return render_template("dummy-spendenbescheinigung.html")

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
    
    # Get donor data from first cart item (they should all be the same)
    donor_data = cart_items[0]['donor_data'] if cart_items else {}
    
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
                'donation_type': item['donation_type'],
                'donor_data': item['donor_data'],
                'amount': item['amount']
            })
    
    return render_template("checkout-zahlung.html", 
                         cart_items=cart_display,
                         total_amount=total_amount,
                         donor_data=donor_data,
                         stripe_public_key=os.environ.get('STRIPE_PUBLIC_KEY'))

@app.route("/checkout/create-payment-intent", methods=["POST"])
@csrf.exempt
@limiter.limit("10 per minute")  # Prevent DoS attacks on payment API
def create_payment_intent():
    """Create Stripe PaymentIntent for cart"""
    try:
        # Import stripe service
        from stripe_service import StripeService, StripeError
        
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
        
        # Get donor data from first item
        donor_data = cart_items[0]['donor_data'] if cart_items else {}
        
        # Create PaymentIntent via service
        payment_data = StripeService.create_payment_intent(cart_items, donor_data)
        
        # Store PaymentIntent ID in session for later verification
        session['payment_intent_id'] = payment_data['payment_intent_id']
        session.modified = True
        
        return jsonify({
            'success': True,
            'client_secret': payment_data['client_secret'],
            'amount': payment_data['amount']
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
        # Import stripe service
        from stripe_service import StripeService, StripeError
        
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
    """Success page after payment with payment verification"""
    # Get payment intent from URL parameters (Stripe redirects)
    payment_intent_id = request.args.get('payment_intent')
    
    if payment_intent_id:
        # Store payment intent ID for success page display
        session['completed_payment_intent'] = payment_intent_id
        session.modified = True
    
    # Clear cart after successful payment (will be cleared by webhook anyway)
    session.pop('cart', None)
    session.pop('shared_donor_data', None)
    session.pop('payment_intent_id', None)
    session.modified = True
    
    return render_template("checkout-erfolg.html")

@app.route("/checkout/verarbeitung")
def checkout_verarbeitung():
    """Processing page for pending payments (especially SEPA)"""
    # Get payment intent ID from URL parameters or session
    payment_intent_id = request.args.get('payment_intent') or session.get('payment_intent_id')
    
    if not payment_intent_id:
        flash("Kein gültiger Zahlungsvorgang gefunden.", "error")
        return redirect(url_for("checkout_zahlung"))
    
    # Get cart information from session for display
    cart_items = session.get('cart', [])
    verse_count = len(cart_items)
    total_amount = verse_count * 100.00
    
    return render_template("checkout-verarbeitung.html",
                         payment_intent_id=payment_intent_id,
                         verse_count=verse_count,
                         total_amount=f"{total_amount:.2f}")

@app.route("/api/payment/status/<payment_intent_id>")
@csrf.exempt
@limiter.limit("30 per minute")  # Allow frequent status checks but prevent abuse
def api_payment_status(payment_intent_id):
    """API endpoint to check payment status"""
    try:
        # Import stripe service
        from stripe_service import StripeService, StripeError
        import stripe
        
        # Validate payment intent ID format
        if not payment_intent_id or not payment_intent_id.startswith('pi_'):
            return jsonify({'error': 'Invalid payment intent ID'}), 400
        
        # Retrieve PaymentIntent from Stripe
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.InvalidRequestError:
            return jsonify({'error': 'Payment intent not found'}), 404
        except stripe.error.StripeError as e:
            app.logger.error(f"Stripe error retrieving PaymentIntent {payment_intent_id}: {e}")
            return jsonify({'error': 'Unable to retrieve payment status'}), 500
        
        # Determine payment method type
        payment_method_type = None
        if payment_intent.payment_method:
            try:
                payment_method = stripe.PaymentMethod.retrieve(payment_intent.payment_method)
                payment_method_type = payment_method.type
            except stripe.error.StripeError:
                payment_method_type = 'unknown'
        
        # Get last payment error if any
        error_message = None
        if payment_intent.last_payment_error:
            error_message = payment_intent.last_payment_error.get('message', 'Payment failed')
        
        # Build response
        response_data = {
            'success': True,
            'payment_intent_id': payment_intent.id,
            'status': payment_intent.status,
            'payment_method_type': payment_method_type,
            'amount': payment_intent.amount,
            'currency': payment_intent.currency,
            'error_message': error_message,
            'created': payment_intent.created,
            'metadata': payment_intent.metadata
        }
        
        # Add status-specific information
        if payment_intent.status == 'succeeded':
            response_data['redirect_url'] = f"/checkout/erfolg?payment_intent={payment_intent.id}"
        elif payment_intent.status in ['canceled', 'requires_payment_method']:
            response_data['redirect_url'] = "/checkout/fehler"
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Unexpected error checking payment status for {payment_intent_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ==========================================

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

@app.route("/agb")
def agb():
    """Terms and conditions"""
    flash("Die AGB sind noch in Entwicklung.", "info")
    return redirect(url_for("datenschutz"))

# ==========================================
# DEBUG ROUTES (TEMPORARY)
# ==========================================

@app.route("/debug/session")
def debug_session():
    """Debug route to view session data"""
    return {
        'session_data': dict(session),
        'session_keys': list(session.keys())
    }

if __name__ == "__main__":
    # Run in debug mode for development
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)