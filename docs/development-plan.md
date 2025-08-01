# Entwicklungsplan für das Bibelvers-Sponsoring-Projekt

## Phase 0: Vorüberlegungen (Woche 0) ✅

- ✅ User-Feedback zu Preismodell einholen
- ✅ Entscheidung: Kein Premium-Modell - einheitlicher Preis von 100€ mit Vers-Auswahl für alle
- ✅ Bestätigung: 11.000 noch zu übersetzende Verse im AT
- [ ] Klärung mit Peter-Schöffer-Stiftung zu Spendenbescheinigungen und benötigten Daten
- [ ] Hintergrund zur 100€-Kalkulation erfragen

## Phase 1: Konzeption und Design (Woche 1)

### Session 1 - User Journey Mapping
- Flussdiagramm der kompletten User Journey erstellen
- Alle möglichen Pfade definieren (Gastspender, registrierter Nutzer)
- Alle benötigten Seiten/Routes identifizieren
- Entscheidungspunkte dokumentieren (z.B. "Möchten Sie sich registrieren?")

### Session 2 - Wireframes erstellen
- Grobe Wireframes für jede identifizierte Seite skizzieren
- Homepage mit Projektbeschreibung
- Vers-Suche und -Auswahl-Seite
- Checkout-Prozess
- Registrierung/Login
- Benutzerdashboard
- Tools: Figma, draw.io oder Papier

### Session 3 - Texte und Content-Strategie
- Alle Haupttexte für die Webseite schreiben
- Projektbeschreibung und Mission
- FAQ-Bereich
- Datenschutzerklärung (Vorlage anpassen)
- E-Mail-Templates für Zertifikat-Versand
- Fehlermeldungen und Bestätigungstexte

### Session 4 - Grafiken und Visuelles Design
- NGÜ-Logo erstellen/beschaffen
- Farbschema und Schriftarten definieren
- Zertifikat-Vorlage gestalten
- Passende Bilder sammeln (lizenzfrei)
- Moodboard für visuellen Stil erstellen
- Konzept für Vers-Animation entwickeln

### Session 5 - Technische Architektur planen
- Datenbankschema-Diagramm erstellen
- Alle API-Endpoints auflisten
- Ordnerstruktur des Projekts definieren
- Session-Verwaltung planen
- Suchfunktionalität konzipieren
- Alle benötigten Umgebungsvariablen dokumentieren

### Session 6 - Frontend-Mockups finalisieren
- Detaillierte Mockups mit realem Content erstellen
- Alle Interaktionen und Hover-States definieren
- Mobile-Responsiveness planen
- Style-Guide-Seite erstellen

## Phase 2: Backend-Grundstruktur (Woche 2)

### Session 7 - Projekt-Setup
- Flask-Projekt initialisieren
- Virtuelle Umgebung einrichten
- Alle Dependencies installieren (Flask, SQLAlchemy, psycopg2, etc.)
- Git-Repository erstellen
- Grundlegende Ordnerstruktur anlegen
- PostgreSQL mit Docker aufsetzen

### Session 8 - Datenbank-Setup
- PostgreSQL-Datenbank mit pgvector Extension einrichten
- SQLAlchemy-Models erstellen (User, BibelVerse, VerseVector, Purchase)
- Datenbank initialisieren
- Migrations-System einrichten
- Test-Daten einfügen (ein paar Beispiel-Verse)

### Session 9 - Bibelvers-Daten importieren
- Script zum Import der Schlachter-1951 HTML-Dateien schreiben
- Parser für HTML-Struktur entwickeln
- HFA-2015 Textdatei einlesen und Verse zuordnen
- Beide Übersetzungen in Datenbank importieren
- Backup-Strategie implementieren
- Embedding-Modell auswählen (Sentence-BERT oder OpenAI)

### Session 10 - Basis-Routes implementieren
- Homepage-Route
- Basis-Templates mit Jinja2
- Static-Files-Handling (CSS, JS)
- Error-Handler (404, 500)

### Session 11 - User-Authentifizierung Teil 1
- Registrierungs-Formular und -Logik
- Login-System mit Flask-Login
- Password-Hashing implementieren
- Session-Management

### Session 12 - User-Authentifizierung Teil 2
- Logout-Funktionalität
- "Passwort vergessen"-Feature
- E-Mail-Verifikation
- User-Dashboard Grundstruktur

## Phase 3: Frontend-Entwicklung (Woche 3)

### Session 13 - CSS-Framework und Basis-Styling
- Bootstrap oder Tailwind einbinden
- Basis-Layout erstellen
- Navigation implementieren
- Responsive Grid-System

### Session 14 - Homepage gestalten
- Hero-Section mit Projekt-Erklärung
- Call-to-Action Buttons
- Statistiken (bereits finanzierte Verse)
- Visuelle Fortschrittsanzeige

### Session 15 - Vers-Suche implementieren
- Semantische Suche mit Vektoren implementieren
- Stichwort-zu-Vektor Konvertierung
- Cosine-Similarity-Suche in pgvector
- Filter nach Büchern
- Such-Ergebnisse mit Ähnlichkeits-Score anzeigen

### Session 16 - Vers-Auswahl-Interface
- Interaktive Vers-Auswahl
- Vorschau des ausgewählten Verses (Schlachter-Text)
- Semantische Alternativen bei vergebenen Versen
- Kontext-basierte Alternativen (vorheriger/nächster Vers)
- Mobile-optimierte Auswahl
- Vektorisierung neuer Suchanfragen

### Session 17 - Forms und Validierung
- Client-seitige Validierung mit JavaScript
- Server-seitige Validierung
- Nutzerfreundliche Fehlermeldungen
- CSRF-Protection

### Session 18 - User-Dashboard entwickeln
- Übersicht gesponserter Verse
- Download-Bereich für Zertifikate
- Profil-Einstellungen
- Newsletter-Verwaltung

## Phase 4: Zahlungsintegration (Woche 4)

### Session 19 - Stripe-Grundlagen lernen
- Stripe-Dokumentation studieren
- Test-Account erstellen
- Sandbox-Umgebung einrichten
- Erste Test-Zahlung durchführen

### Session 20 - Stripe-Integration Backend
- Stripe Python SDK einbinden
- Checkout-Session für 100€ erstellen
- Webhook-Endpoint implementieren
- Fehlerbehandlung

### Session 21 - Stripe-Integration Frontend
- Stripe.js einbinden
- Checkout-Formular gestalten
- Lade-Animationen
- Erfolgs-/Fehler-Seiten

### Session 22 - Zahlungs-Workflow testen
- Verschiedene Zahlungsszenarien testen
- Webhook-Verarbeitung verifizieren
- Datenbank-Updates prüfen
- Edge-Cases behandeln

### Session 23 - Gast-Checkout implementieren
- Checkout ohne Registrierung
- E-Mail-Erfassung für Zertifikat
- Spätere Konto-Zuordnung ermöglichen
- Datenschutz beachten

### Session 24 - Zahlungs-Sicherheit
- HTTPS einrichten (Let's Encrypt)
- Content Security Policy
- Rate-Limiting implementieren
- Logging für Zahlungen

## Phase 5: Automatisierung und E-Mail (Woche 5)

### Session 25 - E-Mail-System einrichten
- Flask-Mail konfigurieren
- SMTP-Server einrichten
- E-Mail-Templates mit Jinja2
- Test-Mails versenden

### Session 26 - Zertifikat-Generierung
- PDF-Generierung mit ReportLab oder WeasyPrint
- Zertifikat-Template umsetzen
- Personalisierung implementieren
- Test-Zertifikate erstellen

### Session 27 - Automatischer Versand
- Nach Zahlungsbestätigung Zertifikat generieren
- E-Mail mit Anhang versenden
- Fehlerbehandlung
- Backup-Kopien speichern

### Session 28 - Newsletter-System
- Newsletter-Anmeldung
- Abmelde-Funktionalität
- DSGVO-konforme Verwaltung
- Einfache Sende-Funktion

### Session 29 - Benachrichtigungen und Animation
- Transaktions-E-Mails
- Admin-Benachrichtigungen
- Vers-Sponsoring-Animation implementieren
- Error-Reporting

### Session 30 - Geschenk-Funktionalität
- Geschenk-Option im Checkout
- Empfänger-Daten erfassen
- Personalisierte Geschenk-E-Mail
- Geschenk-Zertifikat

## Phase 6: Testing und Optimierung (Woche 6)

### Session 31 - Unit-Tests schreiben
- Test-Framework einrichten (pytest)
- Model-Tests
- Route-Tests
- Such-Funktionen testen

### Session 32 - Integrations-Tests
- Komplette User-Flows testen
- Zahlungs-Workflows
- E-Mail-Versand
- Datenbank-Integrität

### Session 33 - Performance-Optimierung
- Datenbank-Queries optimieren
- Vektor-Indizes in pgvector einrichten
- Such-Performance mit Caching verbessern
- Batch-Vektorisierung für neue Anfragen
- Asset-Optimierung
- Ladezeiten messen

### Session 34 - Sicherheits-Audit
- SQL-Injection Tests
- XSS-Prävention prüfen
- Authentifizierung testen
- Dependency-Check

### Session 35 - User-Testing vorbereiten
- Test-Szenarien erstellen
- Feedback-Formular
- Test-Accounts anlegen
- Bug-Tracking einrichten

### Session 36 - UI/UX-Verbesserungen
- Feedback einarbeiten
- Micro-Interactions
- Ladeanimationen
- Accessibility-Checks

## Phase 7: Deployment und Launch (Woche 7)

### Session 37 - Production-Setup
- Server einrichten (DigitalOcean/Heroku)
- PostgreSQL installieren
- Environment-Variablen
- Domain konfigurieren

### Session 38 - Deployment-Pipeline
- Git-Workflow finalisieren
- Automatisches Deployment
- Rollback-Strategie
- Monitoring einrichten

### Session 39 - Finale Tests
- Produktiv-System testen
- Zahlungen mit echtem Stripe
- E-Mail-Versand prüfen
- Performance messen

### Session 40 - Dokumentation
- README.md schreiben
- API-Dokumentation
- Deployment-Anleitung
- CS50-Projektbeschreibung

### Session 41 - Backup und Monitoring
- Automatische Backups
- Uptime-Monitoring
- Error-Tracking (Sentry)
- Analytics einrichten

### Session 42 - Launch-Vorbereitung
- Finale Checkliste
- Soft-Launch planen
- Support-Prozesse
- Wartungsplan erstellen

## Wichtige Meilensteine

- **Ende Woche 0**: Konzept basierend auf User-Feedback finalisiert
- **Ende Woche 2**: Funktionierendes Backend mit User-System
- **Ende Woche 3**: Vollständige Such- und Auswahlfunktion
- **Ende Woche 4**: Vollständige Zahlungsintegration
- **Ende Woche 6**: Feature-complete und getestet
- **Ende Woche 7**: Live und einsatzbereit

## Tipps für die Umsetzung

1. **Dokumentieren Sie alles**: Führen Sie ein Entwicklungstagebuch
2. **Commiten Sie oft**: Kleine, häufige Git-Commits
3. **Testen Sie früh**: Nicht bis zum Ende warten
4. **Holen Sie Feedback**: Zeigen Sie Zwischenstände
5. **Bleiben Sie flexibel**: Der Plan kann angepasst werden

Dieser Plan gibt eine strukturierte Herangehensweise vor, lässt aber Raum für Anpassungen basierend auf dem Lernfortschritt und unerwarteten Herausforderungen.
