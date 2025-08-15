# NGÜ Bibelvers-Sponsoring App (Production)

Dies ist die **echte Implementierung** der NGÜ Bibelvers-Sponsoring App mit Database, Payments und allen Features.

## Status
- 🔄 **In Entwicklung**
- ✅ Database-Models implementiert (PostgreSQL + SQLAlchemy)
- ✅ ~11.000 Verse mit Positivity-Scores ready
- ⏳ Payment-Integration (Stripe)
- ⏳ PDF-Generator-Service
- ⏳ E-Mail-Automation

## Tech Stack
- **Backend**: Python 3.8+ mit Flask
- **Database**: PostgreSQL mit SQLAlchemy ORM
- **Payments**: Stripe
- **PDF**: WeasyPrint oder ReportLab
- **Email**: Flask-Mail
- **Templates**: Jinja2 (übernommen aus Demo)

## Database Setup
```bash
cd src/

# 1. Virtual Environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate     # Windows

# 2. Dependencies
pip install -r requirements.txt

# 3. Database
python -c "from models import init_db; from app import app; init_db(app)"
python -c "from models import import_all_verses; import_all_verses()"
```

## Development
```bash
cd src/
python app.py
```

## Features (geplant)
- **Real Database**: PostgreSQL mit 11.000+ Versen
- **Stripe Payments**: Echte €100 Transaktionen
- **PDF-Zertifikate**: Automatische Generierung
- **E-Mail-Versand**: Automatisch nach Zahlung
- **User-Accounts**: Mit echten Daten
- **Admin-Dashboard**: Spenden-Verwaltung
- **Semantic Search**: pgvector für Vers-Suche

## TODOs
Siehe `/docs/development-todos/` für detaillierte Implementierungs-Pläne.

**Demo läuft weiter in `/demo/` Verzeichnis!**