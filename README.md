# NGÜ Bibelvers-Sponsoring App

Flask-basierte Web-Anwendung für das Sponsoring einzelner Bibelverse zur Finanzierung der NGÜ (Neue Genfer Übersetzung) des Alten Testaments.

## Projektstruktur

```
ngue-bvs-app/
├── demo/                    # 🎨 Demo-Version (läuft auf Homeserver)
│   ├── app.py              # Demo Flask-App
│   ├── templates/          # UI-Templates für Demo
│   ├── static/             # CSS/JS/Images für Demo
│   └── README.md           # Demo-Dokumentation
│
├── src/                     # 🚀 Echte App (in Entwicklung)
│   ├── models.py           # SQLAlchemy Database-Models
│   ├── requirements.txt    # Python Dependencies
│   ├── templates/          # Production Templates
│   ├── static/             # Production Assets
│   └── README.md           # Development-Dokumentation
│
├── data/                    # 📚 Gemeinsame Daten
│   ├── schlachter-1951/    # HTML-Dateien der Schlachter Bibel
│   ├── verses/             # verses.json mit ~11.000 Versen + Scores
│   └── vectors/            # Für semantic search (zukünftig)
│
├── docs/                    # 📖 Projektdokumentation
│   ├── development-todos/   # Detaillierte Implementation-TODOs
│   ├── database-refactoring-payment-transactions.md
│   └── ...
│
├── design/                  # 🎨 Design-System und Assets
│   ├── design-system-preliminary.md
│   ├── Logo NGU *.png
│   └── NGÜ Sponsoring[3720].pdf
│
└── archive/                 # 📦 Historische Dateien
```

## Zwei Versionen

### 🎨 Demo (`/demo/`)
- **Zweck**: User-Feedback sammeln, UI/UX testen
- **Status**: ✅ Läuft produktiv auf Homeserver
- **Features**: Vollständige UI, statische Daten, kein echtes Payment
- **Start**: `cd demo && python app.py`

### 🚀 Production (`/src/`)
- **Zweck**: Echte App mit Database, Payments, PDF-Generation
- **Status**: 🔄 In aktiver Entwicklung
- **Features**: PostgreSQL, Stripe, ~11.000 Verse, echte Spenden
- **Start**: `cd src && python app.py`

## Aktueller Entwicklungsstand

### ✅ Abgeschlossen
- Database-Models (User, Donation, PaymentTransaction, Certificate, DonationCartItem)
- ~11.000 Bibelverse mit Positivity-Scores (0-100)
- UI/UX-Design vollständig (17 Templates, Bootstrap 5.3)
- NGÜ-Branding und Logo-Integration
- Projektstruktur und TODO-System

### 🔄 In Bearbeitung
- Stripe Payment-Integration
- PDF-Zertifikat-Generator
- E-Mail-Automation
- Semantic Verse Search

### ⏳ Geplant
- Admin-Dashboard
- Performance-Optimierung
- Testing-Suite
- Production-Deployment

## Technische Details

### Tech Stack
- **Backend**: Python 3.8+ mit Flask
- **Database**: PostgreSQL mit SQLAlchemy ORM und pgvector
- **Payments**: Stripe (€100 pro Vers)
- **PDF**: WeasyPrint für Zertifikat-Generierung
- **Email**: Flask-Mail für automatischen Versand
- **Frontend**: Bootstrap 5.3, responsive design

### Business Model
- **Sponsoring**: €100 pro Altes Testament Vers
- **Zielgruppe**: Einzelpersonen, Gruppen, Geschenkspenden
- **Zertifikate**: Personalisierte PDF-Zertifikate + Spendenbescheinigungen
- **Automatisierung**: Minimaler manueller Aufwand nach Spende

## Entwicklung

### Demo beibehalten
```bash
cd demo/
python app.py  # Demo läuft weiter für User-Feedback
```

### Echte App entwickeln
```bash
cd src/
pip install -r requirements.txt
python -c "from models import init_db; init_db(app)"
python -c "from models import import_all_verses; import_all_verses()"
python app.py  # Neue App-Entwicklung
```

### TODOs verfolgen
Alle Implementierungs-Pläne in `/docs/development-todos/`:
- `pdf-generator-service-requirements.md`
- `stripe-billing-integration.md`
- `checkout-form-prefilling.md`
- und weitere...

## CS50 Context

Dieses Projekt dient als Final Project für Harvard's CS50 Kurs und löst ein echtes Problem für die Peter-Schöffer-Stiftung zur Finanzierung der NGÜ-Bibelübersetzung.

---

**Demo**: Läuft produktiv für User-Feedback  
**Production**: In aktiver Entwicklung  
**Ziel**: Vollautomatisierte Vers-Sponsoring-Plattform

## Features

- **Individual Verse Sponsoring**: Sponsor any available Old Testament verse for €100
- **Intelligent Verse Search**: Find verses by keyword, reference, or thematic similarity
- **Automated Certificate Generation**: Personalized PDF certificates automatically generated and emailed
- **User Accounts**: Optional registration with donation history tracking
- **Guest Donations**: Contribute without creating an account
- **Semantic Search**: AI-powered verse recommendation using vector embeddings
- **Multi-language Support**: Prepared for future expansion to Switzerland

## Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Database**: PostgreSQL with pgvector extension
- **Payments**: Stripe integration
- **Frontend**: HTML5, CSS3, Bootstrap 5.3
- **AI/ML**: Sentence-BERT embeddings for semantic search
- **PDF Generation**: Automated certificate creation

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 14+ with pgvector extension
- Stripe account (for payments)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ngue-bvs-app.git
   cd ngue-bvs-app
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Stripe credentials
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

Visit `http://localhost:5000` to see the application.

## Project Structure

```
ngue-bvs-app/
├── app.py                  # Main Flask application
├── templates/              # HTML templates (17 pages)
├── static/                 # CSS, JavaScript, images
├── content/                # Page content and forms
├── data/                   # Bible text data (Schlachter 1951)
├── design/                 # Design system and assets
├── docs/                   # Project documentation
├── tests/                  # Test suite
└── requirements.txt        # Python dependencies
```

## Key Components

### Semantic Verse Search
- **Vector Embeddings**: Each verse converted to 768-dimensional vectors
- **Hybrid Search**: Combines keyword and semantic similarity
- **Positivity Ranking**: AI-curated positive verses prioritized in results

### Database Schema
- **BibelVerse**: ~11,000 Old Testament verses with sponsorship status
- **User**: Optional user accounts for sponsors
- **Purchase**: Donation transactions with Stripe integration
- **VerseVector**: AI-generated embeddings for semantic search

### Payment Flow
1. User selects verse (search, browse, or direct reference)
2. Checkout with personal details (required for donation receipt)
3. Stripe payment processing
4. Automated certificate and receipt generation
5. Email delivery of documents

## Development

### Running Tests
```bash
pytest
pytest --cov=app tests/  # With coverage
```

### Database Setup
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Contributing

This is a CS50 final project currently in active development. While I'm working on it individually for academic purposes, feedback and suggestions are welcome!

**Found a bug or have a suggestion?** Please [open an issue](../../issues) on GitHub.

## Roadmap

- **Phase 1**: Germany launch with Peter-Schöffer-Stiftung (Current)
- **Phase 2**: Switzerland expansion with Genfer Bibelgesellschaft (Planned)

## License

[To be determined]

## Acknowledgments

- **Harvard CS50** for excellent computer science education
- **Peter-Schöffer-Stiftung** for partnership and support
- **NGÜ Translation Team** for trusting this project

## Contact

Ulrich Probst - [your-email@example.com]

Project Link: [https://github.com/yourusername/ngue-bvs-app](https://github.com/yourusername/ngue-bvs-app)