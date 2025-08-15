import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_session import Session
from datetime import datetime, timedelta
import secrets
import hashlib
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Generate a secret key if not in production
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

Session(app)

# Demo user storage (in production, use database)
demo_users = {}
verification_tokens = {}
reset_tokens = {}
login_attempts = {}  # Track failed login attempts for rate limiting

# Custom filter for currency formatting
@app.template_filter('currency')
def currency_filter(value):
    """Format value as EUR currency."""
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

# Context processor to inject current year and user info
@app.context_processor
def inject_context():
    user_info = None
    if session.get("user_id"):
        user_info = demo_users.get(session["user_id"])
    return {
        'current_year': datetime.now().year,
        'current_user': user_info
    }

# Helper function for demo verse data
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

def login_required(f):
    """Decorator for routes that require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Bitte melden Sie sich an, um diese Seite zu sehen.", "warning")
            session["next_url"] = request.url
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

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

def create_demo_user(email, password, first_name, last_name, newsletter=False):
    """Create a demo user account."""
    user_id = secrets.token_hex(16)
    verification_token = generate_verification_token()
    
    demo_users[user_id] = {
        "id": user_id,
        "email": email,
        "password_hash": generate_password_hash(password),
        "first_name": first_name,
        "last_name": last_name,
        "newsletter": newsletter,
        "verified": False,
        "created_at": datetime.now(),
        "sponsored_verses": []
    }
    
    verification_tokens[verification_token] = user_id
    return user_id, verification_token

def verify_user_email(token):
    """Verify user email with token."""
    if token in verification_tokens:
        user_id = verification_tokens[token]
        if user_id in demo_users:
            demo_users[user_id]["verified"] = True
            del verification_tokens[token]
            return True, user_id
    return False, None

def find_user_by_email(email):
    """Find user by email address."""
    for user_id, user in demo_users.items():
        if user["email"].lower() == email.lower():
            return user
    return None

# ==========================================
# MAIN ROUTES
# ==========================================

@app.route("/")
def index():
    """Show homepage"""
    stats = {
        'total_verses': 10998,
        'sponsored_verses': 357,
        'available_verses': 10641,
        'percentage': 3
    }
    return render_template("index.html", stats=stats)

@app.route("/vers-auswaehlen")
def vers_auswaehlen():
    """Verse selection page"""
    return render_template("vers-auswaehlen.html")

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
    """Donation type selection page"""
    verse_data = get_demo_verse(verse_id)
    return render_template("vers-spendenart.html", 
                         verse_reference=verse_data['reference'],
                         verse_text=verse_data['text'],
                         verse_id=verse_id)

# ==========================================
# CHECKOUT ROUTES
# ==========================================

@app.route("/checkout/<donation_type>/daten")
def checkout_daten(donation_type):
    """Data collection for different donation types"""
    if donation_type not in ['einzelperson', 'gruppe', 'geschenk']:
        flash("Ungültiger Spendentyp.", "error")
        return redirect(url_for("vers_auswaehlen"))
    
    # Store donation type in session
    session['donation_type'] = donation_type
    return render_template("checkout-daten.html", donation_type=donation_type)

@app.route("/checkout/zusammenfassung")
def checkout_zusammenfassung():
    """Checkout summary page"""
    # Demo data - would normally come from session
    donation_data = {
        'verse_reference': 'Jeremia 29,11',
        'verse_text': 'Denn ich weiß die Gedanken, die ich über euch denke, spricht der HERR, Gedanken des Friedens und nicht des Unheils, euch eine Zukunft und Hoffnung zu geben.',
        'donor_name': 'Max Mustermann',
        'donor_email': 'max.mustermann@example.com',
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
        
        # DEMO MODE: Accept any login credentials
        # Check if user exists
        user = find_user_by_email(email)
        
        if not user:
            # Create a demo user on the fly for testing
            first_name = email.split('@')[0].capitalize()
            demo_user_id = secrets.token_hex(16)
            demo_users[demo_user_id] = {
                "id": demo_user_id,
                "email": email,
                "password_hash": generate_password_hash(password),
                "first_name": first_name,
                "last_name": "Demo",
                "newsletter": True,
                "verified": True,  # Auto-verify for demo
                "created_at": datetime.now(),
                "sponsored_verses": []
            }
            user = demo_users[demo_user_id]
        
        # Login the user (skip password check for demo)
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_name"] = f"{user['first_name']} {user['last_name']}"
        
        if remember:
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=30)
        
        flash(f"Willkommen, {user['first_name']}! (Demo-Modus: Automatische Anmeldung)", "success")
        
        # Redirect to next URL or dashboard
        next_url = session.pop("next_url", None)
        if next_url:
            return redirect(next_url)
        return redirect(url_for("dashboard"))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    flash("Sie wurden erfolgreich abgemeldet.", "info")
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
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
        
        # Create user account
        user_id, verification_token = create_demo_user(
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
            reset_tokens[reset_token] = {
                "user_id": user["id"],
                "expires": datetime.now() + timedelta(hours=1)
            }
            
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
    if token not in reset_tokens:
        flash("Der Passwort-Reset-Link ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("password_reset_request"))
    
    token_data = reset_tokens[token]
    
    # Check if token is expired
    if datetime.now() > token_data["expires"]:
        del reset_tokens[token]
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
        user_id = token_data["user_id"]
        if user_id in demo_users:
            demo_users[user_id]["password_hash"] = generate_password_hash(password)
            del reset_tokens[token]
            flash("Ihr Passwort wurde erfolgreich zurückgesetzt. Sie können sich nun anmelden.", "success")
            return redirect(url_for("login"))
    
    return render_template("password-reset.html", token=token)

@app.route("/meine-verse")
@login_required
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
@login_required
def profil():
    """Profile page (requires login)"""
    return render_template("profil.html")

@app.route("/dashboard")
@login_required
def dashboard():
    """User dashboard"""
    user = demo_users.get(session["user_id"])
    return render_template("dashboard.html", user=user)

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
    return render_template("transparenz.html")

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