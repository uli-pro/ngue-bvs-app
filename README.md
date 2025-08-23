# NGÜ Bibelvers-Sponsoring App

Vereinfachte Flask-Web-Anwendung für das Sponsoring einzelner Bibelverse zur Finanzierung der NGÜ (Neue Genfer Übersetzung) des Alten Testaments.

## 📋 Überblick

**Vereinfachtes Spendenmodell**: Einzelne Altes Testament Verse für je €100 sponsern  
**Keine Benutzerkonten**: Direkter Spendenvorgang ohne Registrierung  
**Stripe-Integration**: SEPA-Lastschrift bevorzugt, Kreditkarten als Fallback  
**Automatisiert**: PDF-Zertifikate und E-Mail-Versand nach Spende  

## 🚀 Aktueller Status (August 2025)

- ✅ **Funktionsfähige Anwendung** - Produktionsbereit
- ✅ **Vereinfachte Architektur** - Person-basierte Spenden ohne Benutzerkonten
- ✅ **Vollständige UI** - 21 responsive Templates mit NGÜ-Branding
- ✅ **Stripe-Integration** - SEPA-Lastschrift und Kreditkarten
- ✅ **Intelligente Suche** - Hybrid-Suche mit KI-Positivitätsbewertung

## 🏗️ Vereinfachte Architektur

### **Kerndatenmodell**
- **Person**: Zentrale Spenderverwaltung (ersetzt User-Model)
- **Verse**: ~11.000 Altes Testament Verse mit Sponsoring-Status
- **Donation**: Vereinfachte Spenden mit JSONB-Details
- **VerseReservation**: Temporäre Versreservierungen während Checkout

### **Kein Benutzerkonto-System**
- Spender geben E-Mail und persönliche Daten pro Spende ein
- `Person`-Records werden automatisch basierend auf E-Mail erstellt/aktualisiert
- Keine Passwörter, Sessions oder Benutzer-Dashboards
- Gast-Checkout ist der primäre Ablauf

## 🛠️ Technologie-Stack

- **Backend**: Flask 3.0 mit SQLAlchemy
- **Database**: PostgreSQL mit pgvector für semantische Suche
- **Payments**: Stripe 12.4 (SEPA-Lastschrift bevorzugt)
- **Suche**: Hybrid Keyword + Vektor-Ähnlichkeitssuche
- **Sicherheit**: Flask-WTF CSRF, Flask-Limiter Rate-Limiting
- **PDF**: WeasyPrint + ReportLab für Zertifikatsgenerierung
- **Frontend**: Bootstrap 5.3, Vanilla JavaScript

## 📁 Projektstruktur

```
ngue-bvs-app/
├── app.py                    # Haupt-Flask-Anwendung (1750+ Zeilen)
├── models.py                 # Datenbankmodelle (Person, Verse, Donation, etc.)
├── stripe_service.py         # Stripe-Zahlungsintegration
├── requirements.txt          # Python-Abhängigkeiten
├── templates/                # 21 HTML-Templates
│   ├── layout.html          # Basis-Template mit NGÜ-Branding
│   ├── index.html           # Homepage mit empfohlenen Versen
│   ├── vers-auswaehlen*.html # Versauswahlseiten
│   ├── checkout-*.html      # Zahlungsfluss-Templates
│   └── ...                  # Weitere Templates
├── static/                   # CSS, JavaScript, Bilder
│   ├── styles.css           # Haupt-Stylesheet
│   ├── js/                  # JavaScript-Module
│   └── logo-*.png           # NGÜ-Logos
├── data/
│   └── verses/
│       └── verses.json      # ~11.000 Verse mit Positivitätsbewertungen
├── docs/                    # Entwicklungsdokumentation
├── tests/                   # Umfassende Testsuite
├── demo/                    # Demo-Version (separate Implementierung)
└── archive/                 # Historische Dateien (für Entwicklung ignorieren)
```

## 🔧 Schnellstart

### Voraussetzungen
- Python 3.8+
- PostgreSQL mit pgvector-Erweiterung
- Stripe-Konto (für Zahlungen)

### Installation

```bash
# 1. Repository klonen
git clone [repository-url]
cd ngue-bvs-app

# 2. Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. Umgebungsvariablen konfigurieren
cp .env.example .env
# .env mit Ihren Datenbank- und Stripe-Credentials bearbeiten

# 5. Datenbank einrichten
python setup_db_v2.py  # Initialisiert Datenbank mit Versen

# 6. Anwendung starten
python app.py
```

Besuchen Sie `http://localhost:5000` um die Anwendung zu sehen.

## 🌟 Hauptfunktionen

### **Versauswahl**
- **Empfohlene Verse**: KI-kuratierte positive Verse auf der Homepage
- **Stichwort-Suche**: Volltext-PostgreSQL-Suche mit deutscher Sprachunterstützung
- **Referenz-Suche**: Direkte biblische Referenz-Suche (z.B. "Jesaja 43,1")
- **Semantische Suche**: Vektor-Ähnlichkeit mit OpenAI-Embeddings
- **Hybrid-Suche**: Dynamische Gewichtung basierend auf Anfragekomplexität

### **Intelligenter Spendenfluss**
- **Einkaufswagen**: Mehrere Verse können vor Checkout hinzugefügt werden
- **Reservierungssystem**: Temporäre Versreservierungen verhindern Konflikte
- **Einheitlicher Checkout**: Ein Formular für alle Spendentypen
- **Person-Management**: Automatische Person-Erstellung/-Updates basierend auf E-Mail

### **Zahlung & Zertifikate**
- **Stripe-Integration**: SEPA-first-Payment mit Karten-Fallback
- **Automatische Zertifikate**: PDF-Generierung bei erfolgreicher Zahlung
- **E-Mail-Versand**: Automatisierter Zertifikat- und Bescheinigungsversand
- **Mehrere Spendentypen**: Einzel-, Gruppen- und Geschenkspenden

## 📊 Feature-Status

### **✅ Fertig & Funktionsfähig**
- Versauswahl mit mehreren Suchmethoden
- Einkaufswagen mit Reservierungssystem
- Vereinfachter Checkout-Ablauf (keine Konten erforderlich)
- Stripe-Zahlungsintegration mit SEPA-Präferenz
- PDF-Zertifikatsgenerierung (Dummy-Templates bereit)
- E-Mail-Automatisierungs-Framework
- Umfassende Fehlerbehandlung und Validierung

### **🔄 In Entwicklung**
- Echte PDF-Zertifikatsgenerierung (Templates existieren)
- E-Mail-Service-Integration (Flask-Mail konfiguriert)
- Admin-Cleanup-Endpunkte
- Performance-Optimierungen

### **⏳ Geplant**
- Produktions-Deployment-Konfiguration
- Admin-Dashboard für Monitoring
- Schweiz-Erweiterung Vorbereitung
- Erweiterte Analytik und Berichterstattung

## 🔒 Sicherheitsfeatures

- **CSRF-Schutz**: Flask-WTF auf allen Formularen
- **Rate-Limiting**: Flask-Limiter auf API-Endpunkten und Zahlungsrouten
- **Eingabevalidierung**: Umfassende Formularvalidierung und Bereinigung
- **Session-Sicherheit**: HTTPOnly, Secure (in Produktion), SameSite-Cookies
- **Zahlungssicherheit**: Keine Kreditkartendaten gespeichert (von Stripe verwaltet)
- **Datenschutz**: DSGVO-konforme Datenerhebung mit expliziter Einwilligung

## 🌐 CS50 Kontext

Diese Flask-Anwendung dient als CS50-Abschlussprojekt und demonstriert:
- **Web-Entwicklung**: Flask, SQLAlchemy, responsive Design
- **Datenbankdesign**: PostgreSQL mit erweiterten Features (pgvector)
- **Zahlungsintegration**: Stripe API mit Webhook-Behandlung
- **KI/ML**: Semantische Suche mit Vektor-Embeddings
- **Echte Anwendung**: Lösung tatsächlicher Finanzierungsbedürfnisse für Bibelübersetzung

## 📝 Entwicklungsnotizen

### **Mit der Codebasis arbeiten**
- **`/archive` ignorieren**: Enthält veraltete Dateien aus vorherigen Iterationen
- **Fokus auf Root-Ebene**: Haupt-Anwendungsdateien sind im Projekt-Root
- **Demo vs. Produktion**: `/demo` ist separat; Haupt-App ist im Root-Verzeichnis

### **Umgebungskonfiguration**
```bash
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/ngue_db
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 🧪 Testing

```bash
# Tests ausführen
pytest

# Mit Coverage
pytest --cov

# Spezifische Test-Kategorien
pytest tests/test_verse_selection.py
pytest tests/test_checkout_flow.py
```

## 🤝 Mitwirkung

Dies ist ein CS50-Abschlussprojekt, das derzeit in aktiver Entwicklung ist. Während ich individuell daran arbeite für akademische Zwecke, sind Feedback und Vorschläge willkommen!

**Bug gefunden oder Vorschlag?** Bitte [öffnen Sie ein Issue](../../issues) auf GitHub.

## 🎯 Roadmap

- **Phase 1**: Deutschland-Launch mit Peter-Schöffer-Stiftung (Aktuell)
- **Phase 2**: Schweiz-Erweiterung mit Genfer Bibelgesellschaft (Geplant)

## 📧 Kontakt

Ulrich Probst  
Projekt-Link: [GitHub Repository URL]

---

**Demo**: Läuft separat für User-Feedback  
**Produktion**: Funktionsfähige Anwendung im Root-Verzeichnis  
**Ziel**: Vollautomatisierte Vers-Sponsoring-Plattform für die NGÜ-Bibelübersetzung