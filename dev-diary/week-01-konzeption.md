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

## Session 3: Haupttexte für Webseiten (Session 2 in neuer Zählung)
**Datum:** 05.08.2025  
**Dauer:** 2 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [x] Homepage-Texte entwickeln (Hero-Bereich, Projektinfo, CTA)
- [x] Vers-Auswahl-Seite texten (Erklärungen, Philosophie-Text)
- [x] "Über die NGÜ"-Seite schreiben 
- [x] "Über die Peter-Schöffer-Stiftung"-Seite erstellen
- [x] Wireframe-Ergänzungen für größere Sponsorings
- [x] Content-Struktur und Verzeichnisse anlegen

### Was ich gemacht habe
Die heutige Session war sehr produktiv und fokussierte sich auf die Entwicklung der Kerntexte für die Webseite. Wir begannen mit einer strategischen Diskussion über den emotionalen Benefit des Bibelvers-Sponsorings: Der zentrale Gedanke ist, dass Spender mit ihrer Unterstützung etwas Zeitloses schaffen - sie ermöglichen eine neue Übersetzung des Wortes Gottes, die über Jahrzehnte hinweg Menschen erreichen wird. Dieser "bleibende Beitrag" wurde zum Leitmotiv für alle Texte. 

Bei der Homepage-Entwicklung erarbeiteten wir eine ausgewogene Balance zwischen emotionaler Ansprache und realistischen Erwartungen. Statt übertriebener "Generationen"-Rhetorik fokussierten wir auf "Jahrzehnte" und "über die eigene Lebenszeit hinaus". Die Projektinfo-Sektion wurde strukturiert um drei Kernpunkte: die Übersetzungsqualität, die zeitliche Dimension und das persönliche Zertifikat als Dankeschön.

Für die Vers-Auswahl-Seite entwickelten wir einen wichtigen Philosophie-Text, der betont, dass jeder Vers zur Gesamtbotschaft der Bibel beiträgt. Dies war notwendig, um zu vermeiden, dass nur "positive" Verse gesponsert werden - ein strategisch wichtiger Punkt für die Nachhaltigkeit des Projekts. Besonders wichtig war auch die korrekte Terminologie bezüglich der NGÜ: Wir sprechen von "zuverlässiger Übersetzung in zeitgemäße Sprache", nicht von "Übertragung" oder "moderner Sprache", da letztere Begriffe in konservativen christlichen Kreisen negativ konnotiert sind.

Die "Über die NGÜ"-Seite wurde basierend auf umfangreichen Recherchen zur Übersetzungsmethode entwickelt. Der Fokus lag auf den drei Säulen der NGÜ: genaue Übersetzung, natürliche Sprache und überprüfbare Entscheidungen durch das Anmerkungssystem. Wichtig war, die NGÜ als "Die Exakte" zu positionieren (Deutsche Bibelgesellschaft), ohne dabei marktschreierisch zu werden.

Für die Stiftungsseite recherchierten wir die Peter-Schöffer-Stiftung ausführlich und entwickelten Texte, die die NGÜ als "eines der Hauptprojekte" positionieren, mit klarem Bezug zur historischen Tradition der Bibelübersetzung durch Peter Schöffer den Jüngeren.

### Probleme & Lösungen
**Problem:** Homepage-Texte waren zu emotional/übertrieben ("Generationen")  
**Lösung:** Realistischere Zeitangaben ("Jahrzehnte", "über die eigene Lebenszeit hinaus") mit subtiler Andeutung der tieferen geistlichen Wirkung

**Problem:** Gefahr der Fokussierung nur auf "positive" Verse durch Positivity-Ranking  
**Lösung:** Philosophie-Text entwickelt, der betont, dass alle Verse wichtig sind für die vollständige biblische Botschaft

**Problem:** Falsche Terminologie für NGÜ ("Übertragung", "modern")  
**Lösung:** Korrekte Begriffe verwendet: "zuverlässige Übersetzung", "zeitgemäße Sprache", "Die Exakte"

**Problem:** Wireframes enthielten noch keine Option für größere Sponsorings  
**Lösung:** Ergänzung in Homepage und Vers-Bestätigung-Seite für Kapitel-/Buch-Sponsorings mit E-Mail-Link-Lösung

### Gelernt
- **Content-Strategie für Spendenprojekte**: Der emotionale Benefit muss authentisch und realistisch sein - zu große Versprechen schaden der Glaubwürdigkeit
- **Zielgruppen-spezifische Terminologie**: In religiösen Bereichen haben scheinbar neutrale Begriffe oft starke Konnotationen, die man kennen muss
- **Philosophische Positionierung**: Bei kontroversen Aspekten (hier: nicht nur positive Verse) braucht es einen durchdachten philosophischen Rahmen
- **Strukturierte Content-Entwicklung**: Ein klares Verzeichnissystem und YAML-Frontmatter erleichtern die spätere Implementierung erheblich

### TODOs für nächste Session
- [ ] FAQ-Bereich entwickeln (besonders Schlachter 1951-Erklärung)
- [ ] E-Mail-Templates für Zertifikat und Spendenbescheinigung
- [ ] Fehlermeldungen und Bestätigungstexte

### Hilfreiche Ressourcen
- neuegenferuebersetzung.de/die-uebersetzungsmethode/
- schoeffer.org (Peter-Schöffer-Stiftung)
- NGÜ Marketing-PDF mit Übersetzungsbeispielen

### Notizen
Sehr wichtige Erkenntnis: Die Balance zwischen emotionaler Ansprache und Sachlichkeit ist entscheidend für die Glaubwürdigkeit. Der "bleibende Beitrag"-Ansatz funktioniert gut, ohne übertrieben zu wirken.

---

## Session 3 (Alt 4): Content-Vervollständigung
**Datum:** 06.08.2025  
**Dauer:** 4 Stunden  
**Woche:** 1 - Konzeption und Design

### Ziele dieser Session
- [x] FAQ-Bereich entwickeln (Schlachter 1951, Steuern, NGÜ, Sponsoring)
- [x] E-Mail-Templates für Zertifikat-Versand erstellen
- [x] E-Mail-Templates für Spendenbescheinigung erstellen
- [x] Fehlermeldungen und Bestätigungstexte schreiben
- [x] Datenschutzerklärung anpassen

### Was ich gemacht habe
Diese Session war eine intensive Content-Entwicklung, bei der wir systematisch alle Texte und Inhalte für die Web-Applikation erstellt haben. Wir begannen mit einem umfassenden FAQ-Bereich mit 18 Einträgen in 5 Kategorien, der alle wichtigen Fragen zum Projekt, zur Vers-Suche, zu Schlachter 1951, zur Steuerlichen Absetzbarkeit und zu technischen Aspekten abdeckt.

Nach den FAQs entwickelten wir die Zertifikat-Vorlagen. Hier war wichtig, die richtige Balance zwischen emotionaler Ansprache und Sachlichkeit zu finden. Der Nutzer half, übertrieben schwülstige Formulierungen zu vermeiden und stattdessen den Fokus auf den "bleibenden Beitrag" zu legen. Wir erstellten separate Templates für Standard-Zertifikate und Geschenk-Zertifikate.

Die E-Mail-Templates wurden in vier Varianten erstellt: Standard-Spender, Geschenk-Empfänger, Geschenk-Schenker mit Versand und Geschenk-Schenker ohne Versand (für persönliche Übergabe). Diese Differenzierung war eine wichtige Erkenntnis aus der Geschenk-Option-Diskussion.

Anschließend dokumentierten wir alle 13 benötigten Formulare der Applikation, von Such-Formularen über Checkout bis zu Benutzerkonten. Dabei wurde klar, dass eine strukturierte Herangehensweise wichtig ist, um nichts zu vergessen.

Ein kritischer Moment war die Entdeckung, dass auch Schweizer Spender berücksichtigt werden müssen. Die Genfer Bibelgesellschaft ist sogar der Senior-Partner, während die Peter-Schöffer-Stiftung der Junior-Partner für Deutschland ist. Wir entschieden uns für "Option B": Einfacher Start mit Deutschland, strukturierte Erweiterung für die Schweiz später. Dies führte zu umfangreichen Vorbereitungen für Phase 2.

### Probleme & Lösungen
**Problem:** Zertifikat-Texte waren zu emotional und redundant  
**Lösung:** Überarbeitung mit Fokus auf "bleibenden Beitrag" und Vermeidung von Wiederholungen

**Problem:** Geschenk-Option hatte Logikfehler  
**Lösung:** Separate Zertifikat-Templates und differenzierte E-Mail-Workflows für verschiedene Geschenk-Szenarien

**Problem:** Schweizer Spender müssen berücksichtigt werden  
**Lösung:** Phase-2-Vorbereitung mit Template-Variablen statt Hardcoding, strukturierte Dokumentation für spätere Erweiterung

**Problem:** Datenschutzerklärung muss DSGVO-konform sein  
**Lösung:** Umfassende 15-Punkte-Datenschutzerklärung nach deutschem Recht mit Stripe-spezifischen Anforderungen

### Gelernt
- **Content-First-Entwicklung**: Es ist sehr wichtig, den ganzen Inhalt der Webseiten einer Web-Applikation fertigzustellen, bevor man sich an die eigentliche Applikation macht. Beim Ausarbeiten aller Details stößt man auf Entscheidungspunkte und neue Routes, die später etabliert werden müssen und oft sogar auf strategische Entscheidungen (wie die mit den Schweizer Spendern), die man vorher nicht bedacht hat, die aber die gesamte Entwicklung der App beeinflussen können.
- **Template-Variablen**: Hardcoding von organisationsspezifischen Daten vermeiden, um spätere Erweiterungen zu erleichtern
- **Geschenk-Workflows**: Komplexe User-Flows wie Geschenk-Optionen brauchen durchdachte Varianten für alle Szenarien
- **Internationale Perspektive**: Auch bei scheinbar nationalen Projekten frühzeitig an internationale Erweiterungen denken

### TODOs für nächste Session
- [ ] Grafiken und Visuelles Design
- [ ] NGÜ-Logo beschaffen
- [ ] Farbschema definieren

### Hilfreiche Ressourcen
- DSGVO-Gesetzestext
- Stripe-Dokumentation zu Datenschutz
- Beispiel-Datenschutzerklärungen anderer Spendenplattformen

### Notizen
Die Schweiz-Integration war eine überraschende Wendung, aber die strukturierte Vorbereitung für Phase 2 wird sich auszahlen. Die Content-First-Methode hat sich als sehr wertvoll erwiesen.

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
