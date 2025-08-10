
from flask import Flask, render_template

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def index():
    """Show homepage"""
    return render_template("index.html")

@app.route("/ueber-ngue")
def ueber_ngue():
    return render_template("ueber_ngue.html")

@app.route("/ueber-stiftung")
def ueber_stiftung():
    return render_template("ueber_stiftung.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/impressum")
def impressum():
    return render_template("impressum.html")

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

@app.route("/verse-auswahl")
def verse_auswahl():
    return render_template("verse_auswahl.html")

@app.route("/verse-suche/referenz")
def verse_suche_referenz():
    return render_template("verse_suche_referenz.html")

@app.route("/verse-suche/keyword")
def verse_suche_keyword():
    return render_template("verse_suche_keyword.html")

@app.route("/bestaetigung")
def bestaetigung():
    return render_template("bestaetigung.html")

@app.route("/datenerfassung")
def datenerfassung():
    return render_template("datenerfassung.html")

@app.route("/zusammenfassung")
def zusammenfassung():
    return render_template("zusammenfassung.html")

@app.route("/erfolg")
def erfolg():
    return render_template("erfolg.html")

@app.route("/fehler")
def fehler():
    return render_template("fehler.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/registrieren")
def registrieren():
    return render_template("registrieren.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/transparenz")
def transparenz():
    return render_template("transparenz.html")

@app.route("/geschenk-datenerfassung")
def geschenk_datenerfassung():
    return render_template("geschenk_datenerfassung.html")

@app.route("/gruppe-datenerfassung")
def gruppe_datenerfassung():
    return render_template("gruppe_datenerfassung.html")

@app.route("/zertifikat-einzel")
def zertifikat_einzel():
    return render_template("zertifikat_einzel.html")

@app.route("/zertifikat-geschenk")
def zertifikat_geschenk():
    return render_template("zertifikat_geschenk.html")

@app.route("/zertifikat-gruppe")
def zertifikat_gruppe():
    return render_template("zertifikat_gruppe.html")

@app.route("/spendenbescheinigung")
def spendenbescheinigung():
    return render_template("spendenbescheinigung.html")

@app.route("/geschenk-zusammenfassung")
def geschenk_zusammenfassung():
    return render_template("geschenk_zusammenfassung.html")

@app.route("/gruppe-zusammenfassung")
def gruppe_zusammenfassung():
    return render_template("gruppe_zusammenfassung.html")

@app.route("/erfolg-geschenk")
def erfolg_geschenk():
    return render_template("erfolg_geschenk.html")

@app.route("/erfolg-gruppe")
def erfolg_gruppe():
    return render_template("erfolg_gruppe.html")

if __name__ == '__main__':
    app.run(debug=True)
