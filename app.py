import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_from_directory
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

@app.route("/vers/<verse_id>/spendenart")
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
            # Group-specific fields
            group_article = request.form.get('group_article', '').strip()
            group_name = request.form.get('group_name', '').strip()
            
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
                # Collect receipt data
                salutation = request.form.get('salutation', '').strip()
                first_name = request.form.get('firstName', '').strip()
                last_name = request.form.get('lastName', '').strip()
                street = request.form.get('street', '').strip()
                house_number = request.form.get('houseNumber', '').strip()
                postal_code = request.form.get('postalCode', '').strip()
                city = request.form.get('city', '').strip()
                country = request.form.get('country', 'DE').strip()
                
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
            gift_recipient_name = request.form.get('gift_recipient_name', '').strip()
            gift_direct_send = request.form.get('gift_direct_send') == 'on'
            
            if not gift_recipient_name:
                errors.append("Bitte geben Sie den Namen des Empfängers ein.")
                
            form_data['gift_recipient_name'] = gift_recipient_name
            form_data['gift_direct_send'] = gift_direct_send
            form_data['gift_message'] = request.form.get('gift_message', '').strip()
            
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
        
        # Initialize cart if not exists
        if 'cart' not in session:
            session['cart'] = []
        
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
    # Check if cart exists and has items
    if 'cart' not in session or not session['cart']:
        flash("Ihr Spendenkorb ist leer. Bitte wählen Sie zuerst einen Vers aus.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    # Load verse data for all items in cart
    cart_items = []
    total_amount = 0
    
    # Check and update reservations for cart items
    for i, item in enumerate(session['cart']):
        # Load verse data
        verse = Verse.query.get(item['verse_id'])
        if not verse:
            continue
            
        # Check reservation status
        reservation_valid = True
        if item.get('reservation_id'):
            reservation = VerseReservation.query.get(item['reservation_id'])
            if not reservation or reservation.is_expired:
                reservation_valid = False
                flash(f"Die Reservierung für {verse.reference} ist abgelaufen.", "warning")
            else:
                # Extend reservation
                reservation.extend_reservation(15)
        
        cart_item_display = {
            'index': i,
            'verse': verse,
            'donation_type': item['donation_type'],
            'donor_data': item['donor_data'],
            'amount': item['amount'],
            'currency': item['currency'],
            'reservation_valid': reservation_valid
        }
        cart_items.append(cart_item_display)
        total_amount += item['amount']
    
    return render_template("spendenkorb.html", 
                         cart_items=cart_items, 
                         total_amount=total_amount,
                         cart_count=len(cart_items))


@app.route("/spendenkorb/entfernen", methods=["POST"])
def cart_remove_item():
    """Remove item from cart via AJAX"""
    try:
        data = request.get_json()
        item_index = data.get('item_index')
        
        if 'cart' not in session or item_index is None:
            return jsonify({'success': False, 'message': 'Invalid request'})
        
        cart = session['cart']
        if 0 <= item_index < len(cart):
            # Clean up reservation if exists
            removed_item = cart[item_index]
            if removed_item.get('reservation_id'):
                reservation = VerseReservation.query.get(removed_item['reservation_id'])
                if reservation:
                    db.session.delete(reservation)
                    db.session.commit()
            
            # Remove item from cart
            cart.pop(item_index)
            session['cart'] = cart
            session.modified = True
            
            return jsonify({'success': True, 'message': 'Item removed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Item not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route("/checkout/erfolg")
def checkout_erfolg():
    """Success page after payment"""
    return render_template("checkout-erfolg.html")

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

@app.route("/spendenbedingungen")
def spendenbedingungen():
    """Donation terms page"""
    flash("Die Spendenbedingungen sind noch in Entwicklung.", "info")
    return redirect(url_for("datenschutz"))

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