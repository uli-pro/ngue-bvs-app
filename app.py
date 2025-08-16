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

# Helper function for demo verse data - Delete as soon as verses from db are used.
def get_demo_verse(verse_id):
    """Get demo verse data for the given ID."""
    verses = {
        'jesaja-43-1': {
            'reference': 'Jesaja 43,1',
            'text': 'Und nun spricht der HERR, der dich geschaffen hat, Jakob, und der dich gemacht hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst. Ich habe dich bei deinem Namen gerufen; du bist mein!'
        },
        'jeremia-29-11': {
            'reference': 'Jeremia 29,11',
            'text': 'Denn ich weiß, was für Gedanken ich über euch habe, spricht der HERR, Gedanken des Friedens und nicht des Leides, euch eine Zukunft und eine Hoffnung zu geben.'
        },
        'zefanja-3-17': {
            'reference': 'Zefanja 3,17',
            'text': 'Der HERR, dein Gott, ist in deiner Mitte, ein Held, der helfen kann; er wird sich über dich freuen mit Wonne, er wird schweigen in seiner Liebe, er wird über dir jubelnd frohlocken.'
        }
    }
    return verses.get(verse_id, verses['jeremia-29-11'])

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
# MAIN ROUTES
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

@app.route("/vers-auswaehlen")
def vers_auswaehlen():
    """Verse selection page with session-based persistence"""
    # Check ob "andere Verse" explizit angefordert
    refresh_verses = request.args.get('refresh') == 'true'
    
    if 'featured_verse_ids' not in session:
        # Erste Auswahl - keine Excludes
        featured_verses = Verse.get_adaptive_featured_verses(3)
        session['featured_verse_ids'] = [v.id for v in featured_verses]
        session['shown_verse_ids'] = [v.id for v in featured_verses]  # Track all shown verses
    elif refresh_verses:
        # "Andere Verse anzeigen" - exclude ALL previously shown verses
        all_shown_ids = session.get('shown_verse_ids', [])
        featured_verses = Verse.get_adaptive_featured_verses(3, exclude_ids=all_shown_ids)
        
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
        
        # Check ob Verse zwischenzeitlich gesponsert wurden
        available_verses = [v for v in featured_verses if not v.is_sponsored]
        
        if len(available_verses) < len(featured_verses):
            # Ersetze gesponserte Verse
            missing_count = len(featured_verses) - len(available_verses)
            all_shown_ids = session.get('shown_verse_ids', [])
            
            new_verses = Verse.get_adaptive_featured_verses(
                missing_count, exclude_ids=all_shown_ids
            )
            
            featured_verses = available_verses + new_verses
            session['featured_verse_ids'] = [v.id for v in featured_verses]
            # Update shown_verse_ids
            session['shown_verse_ids'] = list(set(all_shown_ids + [v.id for v in new_verses]))
    
    return render_template("vers-auswaehlen.html", 
                         featured_verses=featured_verses)

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

@app.route("/projektpartner")
def projektpartner():
    """Project partners page"""
    flash("Die Projektpartner-Seite ist noch in Entwicklung.", "info")
    return redirect(url_for("ueber_stiftung"))

@app.route("/faq")
def faq():
    """FAQ page"""
    return render_template("faq.html")

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

@app.route("/checkout/<donation_type>/daten")
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
    
    return render_template("checkout-daten.html", donation_type=donation_type, verse=verse)

@app.route("/checkout/zusammenfassung")
def checkout_zusammenfassung():
    """Checkout summary page with reservation validation"""
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
    
    # Load verse and build data from session
    verse = Verse.query.get(session['selected_verse_id'])
    donation_data = {
        'verse_reference': verse.reference,
        'verse_text': verse.text,
        'donor_name': session.get('donor_name', 'Demo User'),
        'donor_email': session.get('donor_email', 'demo@example.com'),
        'amount': 100.00
    }
    return render_template("checkout-zusammenfassung.html", data=donation_data)

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
# DONATION TYPE SPECIFIC ROUTES
# ==========================================

@app.route("/checkout/gruppe/daten", methods=["GET", "POST"])
def checkout_gruppe_daten():
    """Group donation contact data"""
    if request.method == "POST":
        # Store group contact data in session
        session['group_contact'] = {
            'email': request.form.get('email'),
            'newsletter': request.form.get('newsletter') == 'on',
            'privacy': request.form.get('privacy') == 'on'
        }
        return redirect(url_for("checkout_zusammenfassung"))
    
    return render_template("checkout-daten.html", donation_type='gruppe')

@app.route("/checkout/geschenk/daten", methods=["GET", "POST"])
def checkout_geschenk_daten():
    """Gift donation donor data"""
    if request.method == "POST":
        # Store gift donor data in session
        session['gift_donor'] = {
            'email': request.form.get('email'),
            'salutation': request.form.get('salutation'),
            'first_name': request.form.get('firstName'),
            'last_name': request.form.get('lastName'),
            'want_receipt': request.form.get('wantReceipt') == 'on',
            'newsletter': request.form.get('newsletter') == 'on',
            'privacy': request.form.get('privacy') == 'on'
        }
        return redirect(url_for("checkout_zusammenfassung"))
    
    return render_template("checkout-daten.html", donation_type='geschenk')

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

if __name__ == "__main__":
    # Run in debug mode for development
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)