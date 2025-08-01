# Woche 1: Konzeption und Design

**Zeitraum:** [Startdatum] - [Enddatum]  
**Fokus:** User Journey, Design, Content-Strategie und technische Planung

## Wochenziele
- [ ] Komplette User Journey dokumentieren
- [ ] Wireframes für alle Hauptseiten erstellen
- [ ] Alle Texte und Content vorbereiten
- [ ] Visuelles Design definieren
- [ ] Technische Architektur planen
- [ ] Detaillierte Mockups finalisieren

---

## Session 1: User Journey Mapping
**Datum:** [Datum]  
**Dauer:** 1,5 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [ ] Flussdiagramm der kompletten User Journey erstellen
- [ ] Alle möglichen Pfade definieren (Gastspender, registrierter Nutzer, Premium-Spender)
- [ ] Alle benötigten Seiten/Routes identifizieren
- [ ] Entscheidungspunkte dokumentieren

### Was ich gemacht habe
[Hier Ihre Notizen einfügen]

### Code-Highlights
```markdown
# Beispiel: Route-Planung
/ (Homepage)
/verse-auswahl (Premium-Spender)
/checkout
/register
/login
/dashboard
/zertifikat/<id>
```

### Probleme & Lösungen
**Problem:** [Beschreibung]  
**Lösung:** [Lösung]

### Gelernt
- 

### TODOs für nächste Session
- [ ] Wireframes basierend auf der User Journey erstellen

### Hilfreiche Ressourcen
- 

### Notizen
[Persönliche Notizen]

---

## Session 2: Wireframes erstellen
**Datum:** [Datum]  
**Dauer:** 1,5 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [ ] Grobe Wireframes für jede identifizierte Seite skizzieren
- [ ] Homepage mit Projektbeschreibung
- [ ] Vers-Auswahl-Seite (für Premium-Spender)
- [ ] Checkout-Prozess
- [ ] Registrierung/Login
- [ ] Benutzerdashboard

### Was ich gemacht habe
[Hier Ihre Notizen einfügen]

### Code-Highlights
```text
# Platz für ASCII-Wireframes oder Links zu Figma/Sketches
```

### Probleme & Lösungen
**Problem:** [Beschreibung]  
**Lösung:** [Lösung]

### Gelernt
- 

### TODOs für nächste Session
- [ ] Texte für alle Seiten schreiben

### Hilfreiche Ressourcen
- 

### Notizen
[Persönliche Notizen]

---

## Session 3: Texte und Content-Strategie
**Datum:** [Datum]  
**Dauer:** 1,5 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [ ] Alle Haupttexte für die Webseite schreiben
- [ ] Projektbeschreibung und Mission
- [ ] FAQ-Bereich
- [ ] Datenschutzerklärung (Vorlage anpassen)
- [ ] E-Mail-Templates für Zertifikat-Versand
- [ ] Fehlermeldungen und Bestätigungstexte

### Was ich gemacht habe
[Hier Ihre Notizen einfügen]

### Code-Highlights
```text
# Beispiel für E-Mail-Template
Betreff: Ihr Bibelvers-Zertifikat - Danke für Ihre Unterstützung!

Liebe/r {name},

vielen Dank für Ihre großzügige Spende...
```

### Probleme & Lösungen
**Problem:** [Beschreibung]  
**Lösung:** [Lösung]

### Gelernt
- 

### TODOs für nächste Session
- [ ] Grafiken und visuelles Design planen

### Hilfreiche Ressourcen
- 

### Notizen
[Persönliche Notizen]

---

## Session 4: Grafiken und Visuelles Design
**Datum:** [Datum]  
**Dauer:** 1,5 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [ ] NGÜ-Logo erstellen/beschaffen
- [ ] Farbschema und Schriftarten definieren
- [ ] Zertifikat-Vorlage gestalten
- [ ] Passende Bilder sammeln (lizenzfrei)
- [ ] Moodboard für visuellen Stil erstellen

### Was ich gemacht habe
[Hier Ihre Notizen einfügen]

### Code-Highlights
```css
/* Beispiel: Farbschema */
:root {
  --primary-color: #...;
  --secondary-color: #...;
  --text-color: #...;
  --background-color: #...;
}
```

### Probleme & Lösungen
**Problem:** [Beschreibung]  
**Lösung:** [Lösung]

### Gelernt
- 

### TODOs für nächste Session
- [ ] Technische Architektur detailliert planen

### Hilfreiche Ressourcen
- 

### Notizen
[Persönliche Notizen]

---

## Session 5: Technische Architektur planen
**Datum:** [Datum]  
**Dauer:** 1,5 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [ ] Datenbankschema-Diagramm erstellen
- [ ] Alle API-Endpoints auflisten
- [ ] Ordnerstruktur des Projekts definieren
- [ ] Session-Verwaltung planen
- [ ] Alle benötigten Umgebungsvariablen dokumentieren

### Was ich gemacht habe
[Hier Ihre Notizen einfügen]

### Code-Highlights
```python
# Beispiel: Geplante Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # ...

class BibelVerse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book = db.Column(db.String(50), nullable=False)
    # ...
```

### Probleme & Lösungen
**Problem:** [Beschreibung]  
**Lösung:** [Lösung]

### Gelernt
- 

### TODOs für nächste Session
- [ ] Frontend-Mockups mit realem Content erstellen

### Hilfreiche Ressourcen
- 

### Notizen
[Persönliche Notizen]

---

## Session 6: Frontend-Mockups finalisieren
**Datum:** [Datum]  
**Dauer:** 1,5 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [ ] Detaillierte Mockups mit realem Content erstellen
- [ ] Alle Interaktionen und Hover-States definieren
- [ ] Mobile-Responsiveness planen
- [ ] Style-Guide-Seite erstellen

### Was ich gemacht habe
[Hier Ihre Notizen einfügen]

### Code-Highlights
```css
/* Beispiel: Responsive Breakpoints */
/* Mobile first approach */
/* Small devices (phones, 640px and down) */
@media only screen and (min-width: 640px) { }
/* Medium devices (tablets, 768px and up) */
@media only screen and (min-width: 768px) { }
/* Large devices (desktops, 1024px and up) */
@media only screen and (min-width: 1024px) { }
```

### Probleme & Lösungen
**Problem:** [Beschreibung]  
**Lösung:** [Lösung]

### Gelernt
- 

### TODOs für nächste Session
- [ ] Flask-Projekt initialisieren (Start Woche 2)

### Hilfreiche Ressourcen
- 

### Notizen
[Persönliche Notizen]

---

## Wochenreflexion
**Was lief gut:**
- 

**Was war herausfordernd:**
- 

**Wichtigste Erkenntnisse:**
- 

**Bereit für Woche 2?** [ ] Ja / [ ] Noch offene Punkte:
