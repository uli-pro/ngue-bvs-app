# NGÜ Bibelvers-Sponsoring App

Eine Web-Applikation zur Finanzierung der Bibelübersetzung NGÜ (Neue Genfer Übersetzung) durch individuelles Vers-Sponsoring.

## Projektziel

Dieses Projekt ermöglicht es Unterstützern, einzelne Verse des Alten Testaments der NGÜ-Bibelübersetzung zu sponsern. Für jeden gesponserten Vers (100€) erhalten die Spender ein personalisiertes Zertifikat als ideellen Gegenwert ihrer Spende.

**CS50 Final Project** - Dies ist mein Abschlussprojekt für Harvard's CS50 Kurs.

## Features

### Kernfunktionen
- **Vers-Sponsoring**: Auswahl eines verfügbaren Verses für 100€ Spende
- **Intelligente Semantische Suche**: 
  - Thematische Suche mit modernen NLP-Technologien
  - Automatische Vorschläge ähnlicher Verse bei bereits vergebenen Versen
  - Cosine-Similarity-basierte Ähnlichkeitsberechnung
- **Such- und Auswahlsystem**: Dropdown-Auswahl nach Buch/Kapitel/Vers oder Stichwortsuche
- **Zertifikat-System**: Automatische Generierung und Versand personalisierter Zertifikate
- **Spendenbescheinigung**: Automatische Erstellung und Versand offizieller Spendenbescheinigungen
- **Benutzerkonten**: Optional für Spender, mit Übersicht aller gesponserten Verse
- **Gast-Spenden**: Möglichkeit ohne Registrierung zu spenden
- **Visuelle Fortschrittsanzeige**: Animation beim Sponsoring eines Verses

### Zusatzfunktionen
- Geschenk-Option für Vers-Sponsoring
- Newsletter-Anmeldung
- Spendenhistorie für registrierte Nutzer
- Responsive Design für alle Geräte

### Technische Besonderheiten
- **Hybrid-Suche**: Dynamische Kombination von Keyword- und Vektor-Suche
- **Positivitäts-Ranking**: LLM-basierte Bewertung für positive, ermutigende Verse
- **Schlachter 1951**: Gemeinfrei und überraschend effektiv für Vektorsuche (72,7% Genauigkeit)
- **Optimiertes Modell**: paraphrase-multilingual-mpnet-base-v2 (768 Dimensionen)

## Technologie-Stack

### Backend
- **Python 3.8+** mit **Flask** Web-Framework
- **PostgreSQL** mit **pgvector** Extension für Vektoroperationen
- **SQLAlchemy** als ORM
- **Stripe** für Zahlungsabwicklung

### Frontend
- **HTML5** / **CSS3** / **JavaScript**
- **Bootstrap** oder **Tailwind CSS** (noch zu entscheiden)
- **Jinja2** Template Engine

### Weitere Tools
- **Flask-Mail** für E-Mail-Versand
- **ReportLab** oder **WeasyPrint** für PDF-Generierung
- **Flask-Login** für Authentifizierung
- **pytest** für Testing
- **Embedding-Modell** (Sentence-BERT: paraphrase-multilingual-mpnet-base-v2)

## Projektstruktur

```
ngue-bvs-app/
├── app/                    # Flask-Anwendung (wird erstellt)
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   └── utils.py
├── data/                   # Bibeldaten (nicht im Git)
│   ├── schlachter-1951/    # HTML-Dateien für Import
│   └── vectors/            # Generierte Vektordaten
├── prompts/                # Entwicklungs-Prompts
│   ├── claude-code/        # Für Claude Code
│   ├── development/        # Für allgemeine Entwicklung
│   └── README.md
├── static/                 # Statische Dateien
├── templates/              # Jinja2 Templates
├── tests/                  # Test-Suite
├── docs/                   # Projektdokumentation
│   ├── development-plan.md
│   ├── project-description.md
│   └── untranslated_bible_books.csv
├── dev-diary/              # Entwicklungstagebuch
│   ├── README.md
│   ├── week-00-vorueberlegungen.md
│   └── week-01-konzeption.md
├── CLAUDE.md               # Anleitung für Claude Code
├── requirements.txt        # Python-Dependencies
├── config.py              # App-Konfiguration
├── .env.example           # Umgebungsvariablen-Template
├── .gitignore
└── README.md
```

## Installation

### Voraussetzungen
- Python 3.8+
- PostgreSQL 14+ 
- Docker (optional, für einfaches PostgreSQL-Setup)
- pip
- virtualenv (empfohlen)

### PostgreSQL mit pgvector einrichten

#### Option 1: Mit Docker (empfohlen für Entwicklung)
```bash
docker run -d \
  --name ngue-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=ngue_bvs_db \
  -p 5432:5432 \
  ankane/pgvector
```

#### Option 2: Manuelle Installation
1. PostgreSQL installieren
2. pgvector Extension installieren:
```bash
# Ubuntu/Debian
sudo apt install postgresql-14-pgvector

# macOS mit Homebrew
brew install pgvector
```
3. In PostgreSQL:
```sql
CREATE DATABASE ngue_bvs_db;
\c ngue_bvs_db
CREATE EXTENSION vector;
```

### App-Setup

1. Repository klonen
```bash
git clone [repository-url]
cd ngue-bvs-app
```

2. Virtuelle Umgebung erstellen und aktivieren
```bash
python -m venv venv
source venv/bin/activate  # Auf Windows: venv\Scripts\activate
```

3. Dependencies installieren
```bash
pip install -r requirements.txt
```

4. Umgebungsvariablen konfigurieren
```bash
cp .env.example .env
# .env Datei mit eigenen Werten füllen
```

5. Bibeldaten platzieren
```bash
# Schlachter 1951 HTML-Dateien nach data/schlachter-1951/
```

6. Datenbank initialisieren
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

7. Bibelverse importieren und vektorisieren
```bash
flask import-verses
flask vectorize-verses
```

8. Entwicklungsserver starten
```bash
flask run
```

Die App ist nun unter `http://localhost:5000` erreichbar.

## Konfiguration

Erstellen Sie eine `.env` Datei mit folgenden Variablen:

```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:password@localhost:5432/ngue_bvs_db
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password

# Optional: Für externe Embedding-APIs
OPENAI_API_KEY=your-openai-key  # Falls OpenAI Embeddings genutzt werden
```

## Datenbank-Schema (Vorläufig)

**Hinweis**: Das folgende Schema ist vorläufig und wird sich während der Entwicklung noch weiterentwickeln.

### User
- id (Primary Key)
- email (Unique)
- password_hash
- salutation (Enum: 'Herr', 'Frau', 'Eheleute', 'Firma')
- first_name
- last_name
- street
- house_number
- postal_code
- city
- newsletter_subscribed (Boolean)
- data_processing_consent (Boolean)
- created_at

### BibelVerse
- id (Primary Key)
- reference (z.B. "GEN.1.1" - eindeutige Referenz)
- book (String)
- chapter (Integer)
- verse (Integer)
- text_schlachter (Text - vollständiger Vers Schlachter 1951)
- is_sponsored (Boolean)
- sponsor_name (String, nullable)
- created_at
- updated_at

### VerseVector
- id (Primary Key)
- verse_id (Foreign Key zu BibelVerse)
- embedding (vector(768) - Vektor-Repräsentation)
- model_version (String - verwendetes Embedding-Modell)
- created_at

### Purchase
- id (Primary Key)
- user_id (Foreign Key, nullable für Gäste)
- verse_id (Foreign Key zu BibelVerse)
- amount (Decimal)
- stripe_payment_id (String)
- certificate_url (String)
- donation_receipt_url (String)
- donation_receipt_number (String, unique)
- created_at
- is_gift (Boolean)
- recipient_salutation (String, nullable)
- recipient_first_name (String, nullable)
- recipient_last_name (String, nullable)
- recipient_email (String, nullable)
- gift_message (Text, nullable)

### GuestDonor (Für Spenden ohne Registrierung)
- id (Primary Key)
- purchase_id (Foreign Key zu Purchase)
- salutation
- first_name
- last_name
- street
- house_number
- postal_code
- city
- email
- data_processing_consent (Boolean)
- created_at

### SearchLog (Optional, für Analyse)
- id (Primary Key)
- search_query (String)
- search_type (Enum: 'keyword', 'reference', 'similarity')
- results_count (Integer)
- selected_verse_id (Foreign Key, nullable)
- created_at

## Testing

Tests ausführen:
```bash
pytest
```

Mit Coverage-Report:
```bash
pytest --cov=app tests/
```

## API Endpoints (Geplant)

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/` | Homepage |
| GET | `/api/verses/available` | Verfügbare Verse (JSON) |
| GET | `/api/verses/search` | Verse suchen (Keyword oder Referenz) |
| POST | `/api/verses/similar` | Ähnliche Verse finden (Vektor-Suche) |
| GET | `/checkout/<verse_id>` | Checkout-Seite für spezifischen Vers |
| POST | `/process-payment` | Zahlung verarbeiten |
| GET | `/register` | Registrierungsseite |
| POST | `/register` | Benutzer registrieren |
| GET | `/login` | Login-Seite |
| POST | `/login` | Benutzer einloggen |
| GET | `/dashboard` | Benutzer-Dashboard |
| GET | `/certificate/<id>` | Zertifikat herunterladen |

## Cosine Similarity für Vers-Ähnlichkeit

**Cosine Similarity** misst die Ähnlichkeit zwischen zwei Vektoren anhand des Winkels zwischen ihnen:
- Wert zwischen -1 und 1 (meist 0 bis 1 bei Textvektoren)
- 1 = identisch, 0 = keine Ähnlichkeit
- Ideal für hochdimensionale Vektorräume
- In PostgreSQL mit pgvector: `<=>` Operator für Cosine Distance

Beispiel-Query:
```sql
SELECT verse_id, 1 - (embedding <=> query_embedding) as similarity
FROM verse_vectors
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

## Mitwirken

Dieses Projekt ist Teil meines CS50-Kurses. Während der Entwicklungsphase arbeite ich alleine daran, aber Feedback und Vorschläge sind willkommen!

## Lizenz

[Noch zu bestimmen]

## Danksagung

- **Harvard CS50** für die exzellente Ausbildung
- **Peter-Schöffer-Stiftung** für die Zusammenarbeit
- **NGÜ-Team** für das Vertrauen in dieses Projekt

## Kontakt

Ulrich Probst - [Ihre E-Mail]

Projekt Link: [https://github.com/[ihr-username]/ngue-bvs-app](https://github.com/[ihr-username]/ngue-bvs-app)

---

## Entwicklungsstatus

- [x] Projektplanung
- [x] User-Feedback und Konzeptanpassung
- [x] Proof of Concept für Vektor-Suche
- [x] Umfangreiche Tests mit 100/1.000/11.000 Versen
- [x] Hybrid-Suche Implementierung
- [ ] LLM-basiertes Positivitäts-Ranking (nächster Schritt)
- [ ] Woche 1: Konzeption und Design
- [ ] Woche 2: Backend-Grundstruktur
- [ ] Woche 3: Frontend-Entwicklung
- [ ] Woche 4: Zahlungsintegration
- [ ] Woche 5: Automatisierung
- [ ] Woche 6: Testing
- [ ] Woche 7: Deployment

### Aktuelle Erkenntnisse (02.08.2025)
- **Kritisch**: Nutzer suchen positive Verse, aber Standard-Suche liefert oft negative
- **Lösung**: Top-1000 positive Verse mit LLM vorranken
- **Nächste Schritte**: Prompt-Optimierung für Positivitäts-Ranking

Detaillierte Entwicklungsdokumentation finden Sie im [Entwicklungstagebuch](./dev-diary/README.md).
