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
**Datum:** 04.08.2025  
**Dauer:** 2 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [x] Flussdiagramm der kompletten User Journey erstellen
- [x] Alle möglichen Pfade definieren (Gastspender, registrierter Nutzer)
- [x] Alle benötigten Seiten/Routes identifizieren
- [x] Entscheidungspunkte dokumentieren

### Was ich gemacht habe
- Umfassende User Journey in Textform dokumentiert
- Kritische Analyse der Journey mit Verbesserungsvorschlägen
- Mermaid-Flussdiagramm erstellt, das alle User-Pfade visualisiert
- 30 benötigte Routes/Seiten identifiziert (inkl. API-Endpoints)
- 12 kritische Entscheidungspunkte in Tabellenform dokumentiert
- Integration von Peter-Schöffer-Stiftung und Transparenz-Seiten eingeplant
- DSGVO-konforme Datenerfassung mit E-Mail als Pflichtfeld konzipiert
- Temporäre Vers-Reservierung (15 Min) während Checkout geplant

### Code-Highlights
```markdown
# Haupt-Routes identifiziert:
/ (Homepage)
/verse-auswahl (Top 3 positive Verse)
/verse-suche/referenz (Bibelstellen-Suche)
/verse-suche/keyword (Thematische Suche)
/verse/{verse_id}/bestaetigung
/checkout/daten
/checkout/zusammenfassung
/checkout/erfolg (Danke-Seite)
/dashboard (User-Bereich)
/ueber-stiftung (NEU: Peter-Schöffer-Stiftung)
/transparenz (NEU: Mittelverwendung)
```

### Probleme & Lösungen
**Problem:** E-Mail-Erfassung fehlte bei Gast-Spendern ohne Spendenbescheinigung  
**Lösung:** E-Mail wird IMMER erfasst (für Zertifikat-Versand), unabhängig von Spendenbescheinigung

**Problem:** Geschenk-Option war nicht in der Journey  
**Lösung:** Geschenk-Option auf Vers-Bestätigungsseite mit Empfängerdaten integriert

**Problem:** Zusammenhang NGÜ/Peter-Schöffer-Stiftung unklar  
**Lösung:** Eigene Stiftungs-Seite und Transparenz-Seite eingeplant

### Gelernt
- **User Journey Mapping**: Eine User Journey ist die vollständige Reise eines Nutzers durch eine Anwendung - von der ersten Interaktion bis zum Ziel. Sie hilft dabei, alle Touchpoints, Entscheidungen und möglichen Probleme zu identifizieren. Durch die Visualisierung als Flussdiagramm werden Lücken und Optimierungspotenziale sichtbar.
- **Mermaid-Diagramme**: Ein textbasiertes Tool zur Erstellung von Flussdiagrammen, das sich perfekt für technische Dokumentation eignet
- **Wichtigkeit von Edge-Cases**: Zahlungsabbrüche, Timeouts und Fehlerzustände müssen von Anfang an mitgedacht werden
- **DSGVO-Compliance**: Datenschutz muss in jeden Schritt der Journey integriert werden

### TODOs für nächste Session
- [x] Wireframes basierend auf der User Journey erstellen

### Hilfreiche Ressourcen
- 

### Notizen
[Persönliche Notizen]

---

## Session 2: Wireframes erstellen
**Datum:** 04.08.2025  
**Dauer:** 2,5 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [x] Grobe Wireframes für jede identifizierte Seite skizzieren
- [x] Homepage mit Projektbeschreibung
- [x] Vers-Auswahl-Seite
- [x] Checkout-Prozess
- [x] Registrierung/Login
- [x] Benutzerdashboard

### Was ich gemacht habe
- Wireframes für alle 20+ identifizierten Seiten erstellt
- Mobile-first Ansatz bei der Gestaltung berücksichtigt
- Konsistente Navigation und User-Flow sichergestellt
- Call-to-Action Platzierungen optimiert
- Formulare für Datenerfassung strukturiert
- Dashboard-Layout für registrierte Nutzer entworfen

### Code-Highlights
```text
# Wireframe-Struktur Beispiel:
Homepage:
+---------------------------+
|     Navigation Bar        |
+---------------------------+
|     Hero Section          |
|   "Jeder Vers zählt"      |
|   [Jetzt spenden]         |
+---------------------------+
|   Tortendiagramm 100€     |
|   Kostenaufschlüsselung   |
+---------------------------+
|   Projekt-Erklärung       |
|   NGÜ & Stiftung Info    |
+---------------------------+
|        Footer             |
+---------------------------+
```

### Probleme & Lösungen
**Problem:** Wie zeigt man 11.000 verfügbare Verse übersichtlich?  
**Lösung:** Drei-Wege-Ansatz: Top 3 / Bibelstellen-Dropdown / Keyword-Suche

**Problem:** Mobile Darstellung von Dropdown-Menüs  
**Lösung:** Native Mobile-Selects verwenden, touch-optimierte Größe

### Gelernt
- **Wireframes**: Wireframes sind schematische Darstellungen einer Webseite oder App, die die Struktur und Funktionalität zeigen, ohne sich auf visuelles Design zu konzentrieren. Sie sind wie der Bauplan eines Hauses - sie zeigen, wo welche Elemente platziert werden, bevor man sich um Farben und Dekoration kümmert. Dies hilft, sich auf die Benutzererfahrung und Funktionalität zu konzentrieren, ohne von ästhetischen Entscheidungen abgelenkt zu werden.
- **Mobile-First Design**: Bei der Erstellung von Wireframes zuerst an mobile Geräte denken, da diese oft mehr Einschränkungen haben
- **Konsistenz**: Wiederkehrende Elemente (Navigation, Footer, CTAs) sollten auf allen Seiten gleich positioniert sein
- **Whitespace**: Großzügiger Abstand zwischen Elementen verbessert die Lesbarkeit und Benutzerfreundlichkeit

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
- Sessions 1 und 2 erfolgreich abgeschlossen
- Klare User Journey mit allen Pfaden dokumentiert
- Alle 20+ Seiten als Wireframes skizziert
- Wichtige Ergänzungen identifiziert (Stiftungs-Info, Transparenz)
- DSGVO-konforme Lösungen von Anfang an eingeplant

**Was war herausfordernd:**
- Balance zwischen Einfachheit und Funktionsumfang
- Mobile-Optimierung bei komplexen Formularen
- Alle Edge-Cases bedenken (Zahlungsabbrüche, Timeouts)

**Wichtigste Erkenntnisse:**
- User Journey Mapping deckt Lücken auf, die man sonst erst später entdeckt
- Wireframes helfen, sich auf Funktion statt Form zu konzentrieren
- Frühzeitige Planung von Fehlerbehandlung spart später viel Arbeit
- Transparenz und Vertrauensbildung sind essentiell bei Spenden-Projekten

**Bereit für Woche 2?** [ ] Ja / [x] Noch offene Punkte:
- Session 3-6 noch abzuschließen (Texte, Design, Architektur)
- Finale Klärung mit Stiftung zu Spendenbescheinigungen ausstehend
