import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from datetime import datetime
import secrets

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

# Custom filter for currency formatting
@app.template_filter('currency')
def currency_filter(value):
    """Format value as EUR currency."""
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

# Context processor to inject current year
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

# Helper function for demo verse data
def get_demo_verse(verse_id):
    """Get demo verse data for the given ID."""
    verses = {
        'jeremia-29-11': {
            'reference': 'Jeremia 29,11',
            'text': 'Denn ich weiß die Gedanken, die ich über euch denke, spricht der HERR, Gedanken des Friedens und nicht des Unheils, euch eine Zukunft und Hoffnung zu geben.'
        },
        'psalm-23-1': {
            'reference': 'Psalm 23,1',
            'text': 'Der HERR ist mein Hirte; mir wird nichts mangeln.'
        },
        'sprueche-3-5-6': {
            'reference': 'Sprüche 3,5-6',
            'text': 'Vertraue auf den HERRN von ganzem Herzen und verlaß dich nicht auf deinen Verstand; erkenne ihn auf allen deinen Wegen, so wird er deine Pfade ebnen!'
        }
    }
    return verses.get(verse_id, verses['jeremia-29-11'])

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

@app.route("/vers-suche/referenz")
def vers_suche_referenz():
    """Reference search page"""
    return render_template("vers-suche-referenz.html")

@app.route("/vers-suche/keyword")
def vers_suche_keyword():
    """Keyword search page"""
    return render_template("vers-suche-keyword.html")

# ==========================================
# VERSE CONFIRMATION ROUTES
# ==========================================

@app.route("/vers/<verse_id>/bestaetigung")
def vers_bestaetigung(verse_id):
    """Verse confirmation page"""
    verse_data = get_demo_verse(verse_id)
    return render_template("vers-bestaetigung.html", 
                         verse_reference=verse_data['reference'],
                         verse_text=verse_data['text'])

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
        'verse_text': 'Denn ich weiß die Gedanken...',
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
        # Demo login - in production you would check against database
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Demo: any login works for demonstration
        if email and password:
            session["user_id"] = 1  # Demo user ID
            session["user_email"] = email
            flash("Erfolgreich angemeldet!", "success")
            return redirect(url_for("index"))
        else:
            flash("Ungültige Anmeldedaten.", "danger")
    
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
        # Handle registration
        flash("Registrierung erfolgreich! Sie können sich nun anmelden.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/meine-verse")
def meine_verse():
    """My verses page (requires login)"""
    if not session.get("user_id"):
        flash("Bitte melden Sie sich an, um Ihre Verse zu sehen.", "warning")
        return redirect(url_for("login"))
    return render_template("meine-verse.html")

@app.route("/profil")
def profil():
    """Profile page (requires login)"""
    if not session.get("user_id"):
        flash("Bitte melden Sie sich an, um Ihr Profil zu sehen.", "warning")
        return redirect(url_for("login"))
    return render_template("profil.html")

@app.route("/dashboard")
def dashboard():
    """User dashboard"""
    if not session.get("user_id"):
        flash("Bitte melden Sie sich an.", "warning")
        return redirect(url_for("login"))
    return render_template("dashboard.html")

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

@app.route("/widerruf")
def widerruf():
    """Revocation page"""
    flash("Die Widerrufsbelehrung ist noch in Entwicklung.", "info")
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
    """Download demo donation receipt"""
    flash("Demo-Spendenbescheinigung: In der echten Anwendung würde hier ein PDF generiert.", "info")
    return redirect(url_for("checkout_erfolg"))

# ==========================================
# DONATION TYPE SPECIFIC ROUTES
# ==========================================

@app.route("/spende/einzelperson")
def spende_einzelperson():
    """Individual donation page"""
    return render_template("spende-einzelperson.html")

@app.route("/spende/gruppe")
def spende_gruppe():
    """Group donation page"""
    return render_template("spende-gruppe.html")

@app.route("/spende/geschenk")
def spende_geschenk():
    """Gift donation page"""
    return render_template("spende-geschenk.html")

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
    app.run(debug=True, host="0.0.0.0", port=5000)