# NGÜ Bibelvers-Sponsoring - Flask Design Demo

Diese Flask-Anwendung zeigt das Design für die NGÜ Bibelvers-Sponsoring Webseite.

## 🚀 Schnellstart

### 1. Virtuelle Umgebung erstellen und aktivieren

```bash
# Python 3 virtuelle Umgebung erstellen
python3 -m venv venv

# Aktivieren (macOS/Linux)
source venv/bin/activate

# Aktivieren (Windows)
venv\Scripts\activate
```

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 3. Flask-App starten

```bash
python app.py
```

Die Anwendung läuft dann unter: **http://localhost:5000**

## 📁 Struktur

```
claude-entwurf/
├── app.py              # Flask-Anwendung
├── requirements.txt    # Python-Dependencies
├── templates/          # HTML-Templates
│   ├── layout.html    # Basis-Layout
│   └── index.html     # Homepage
└── static/            # Statische Dateien
    └── styles.css     # CSS-Styles
```

## 🎨 Features

- **Bootstrap 5.3** für responsives Design
- **NGÜ-Farbpalette** (#dd3333, #323334)
- **Google Fonts** (Poppins, Montserrat)
- **Font Awesome Icons**
- **Mobile-first Design**
- **Flask-Session** für Benutzerverwaltung

## 🔧 Entwicklung

Zum Entwickeln im Debug-Modus:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

## 📝 Hinweise

- Dies ist eine Demo-Version ohne Datenbank
- Login funktioniert mit beliebigen Daten (Demo-Modus)
- Einige Links führen zu Placeholder-Seiten
- Die Vers-Auswahl ist noch nicht implementiert

## 🔗 Wichtige Routen

- `/` - Homepage
- `/faq` - Häufig gestellte Fragen
- `/kontakt` - Kontaktformular
- `/login` - Anmeldung (Demo)
- `/vers-auswaehlen` - Vers-Auswahl (in Entwicklung)