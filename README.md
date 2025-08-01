# NGÜ Bibelvers-Sponsoring App

Eine Web-Applikation zur Finanzierung der Bibelübersetzung NGÜ (Neue Genfer Übersetzung) durch individuelles Vers-Sponsoring.

## Projektziel

Dieses Projekt ermöglicht es Unterstützern, einzelne Verse des Alten Testaments der NGÜ-Bibelübersetzung zu sponsern. Für jeden gesponserten Vers (100€) erhalten die Spender ein personalisiertes Zertifikat als ideellen Gegenwert ihrer Spende.

**CS50 Final Project** - Dies ist mein Abschlussprojekt für Harvard's CS50 Kurs.

## Features

### Kernfunktionen
- **Vers-Sponsoring**: Automatische Zuweisung eines verfügbaren Verses bei 100€ Spende
- **Premium-Sponsoring**: Selbstauswahl eines Verses bei höheren Spenden (z.B. 150€)
- **Zertifikat-System**: Automatische Generierung und Versand personalisierter Zertifikate
- **Benutzerkonten**: Optional für Spender, mit Übersicht aller gesponserten Verse
- **Gast-Spenden**: Möglichkeit ohne Registrierung zu spenden

### Zusatzfunktionen
- Geschenk-Option für Vers-Sponsoring
- Newsletter-Anmeldung
- Spendenhistorie für registrierte Nutzer
- Responsive Design für alle Geräte

## Technologie-Stack

### Backend
- **Python 3.x** mit **Flask** Web-Framework
- **SQLAlchemy** als ORM
- **SQLite3** (Development) / **PostgreSQL** (Production)
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

## Projektstruktur

```
ngue-bvs-app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   └── utils.py
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── checkout.html
│   └── ...
├── tests/
├── migrations/
├── docs/
│   ├── development-plan.md
│   └── ...
├── dev-diary/
│   ├── README.md
│   └── week-01-konzeption.md
├── requirements.txt
├── config.py
├── .env.example
├── .gitignore
└── README.md
```

## Installation

### Voraussetzungen
- Python 3.8+
- pip
- virtualenv (empfohlen)

### Setup

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

5. Datenbank initialisieren
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Entwicklungsserver starten
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
DATABASE_URL=sqlite:///app.db
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
```

## Datenbank-Schema

### User
- id (Primary Key)
- email (Unique)
- password_hash
- name
- created_at
- newsletter_subscribed

### BibelVerse
- id (Primary Key)
- book
- chapter
- verse
- is_sponsored (Boolean)
- purchase_id (Foreign Key)

### Purchase
- id (Primary Key)
- user_id (Foreign Key, nullable für Gäste)
- verse_id (Foreign Key)
- amount
- stripe_payment_id
- created_at
- is_gift (Boolean)
- recipient_email

## Testing

Tests ausführen:
```bash
pytest
```

Mit Coverage-Report:
```bash
pytest --cov=app tests/
```

## API Endpoints

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/` | Homepage |
| GET | `/verses` | Verfügbare Verse anzeigen |
| GET | `/checkout` | Checkout-Seite |
| POST | `/process-payment` | Zahlung verarbeiten |
| GET | `/register` | Registrierungsseite |
| POST | `/register` | Benutzer registrieren |
| GET | `/login` | Login-Seite |
| POST | `/login` | Benutzer einloggen |
| GET | `/dashboard` | Benutzer-Dashboard |
| GET | `/certificate/<id>` | Zertifikat herunterladen |

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
- [ ] Woche 1: Konzeption und Design
- [ ] Woche 2: Backend-Grundstruktur
- [ ] Woche 3: Frontend-Entwicklung
- [ ] Woche 4: Zahlungsintegration
- [ ] Woche 5: Automatisierung
- [ ] Woche 6: Testing
- [ ] Woche 7: Deployment

Detaillierte Entwicklungsdokumentation finden Sie im [Entwicklungstagebuch](./dev-diary/README.md).
