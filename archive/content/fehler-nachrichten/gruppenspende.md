# Fehlermeldungen: Gruppenspende

## Validierungsfehler - Artikel

### Artikel nicht ausgewählt:
**Fehlertyp:** Required Field
**Nachricht:** "Bitte wählen Sie einen Artikel für Ihren Gruppennamen aus"
**Kontext:** Erscheint wenn Artikel-Dropdown leer gelassen wird

### Artikel-Dropdown Fehler (technisch):
**Fehlertyp:** Invalid Selection
**Nachricht:** "Ungültige Auswahl. Bitte wählen Sie 'Der', 'Die' oder 'Das'"
**Kontext:** Falls ungültige Werte übermittelt werden

## Validierungsfehler - Gruppenname

### Gruppenname leer:
**Fehlertyp:** Required Field  
**Nachricht:** "Bitte geben Sie einen Gruppennamen ein"
**Kontext:** Feld ist leer oder nur Leerzeichen

### Gruppenname zu kurz:
**Fehlertyp:** Min Length
**Nachricht:** "Der Gruppenname muss mindestens 2 Zeichen haben"
**Kontext:** Weniger als 2 Zeichen eingegeben

### Gruppenname zu lang:
**Fehlertyp:** Max Length
**Nachricht:** "Der Gruppenname darf maximal 80 Zeichen haben"
**Kontext:** Mehr als 80 Zeichen eingegeben

### Gruppenname nur Sonderzeichen:
**Fehlertyp:** Pattern Validation
**Nachricht:** "Der Gruppenname muss mindestens einen Buchstaben enthalten"
**Kontext:** Nur Zahlen/Sonderzeichen, keine Buchstaben

## Kombinierte Validierungsfehler

### Beide Felder leer:
**Fehlertyp:** Multiple Required
**Nachricht:** "Artikel und Gruppenname sind Pflichtfelder"
**Kontext:** Beide Felder sind leer

### Allgemeiner Gruppendaten-Fehler:
**Fehlertyp:** Form Validation
**Nachricht:** "Bitte vervollständigen Sie Ihre Gruppendaten"
**Kontext:** Wenn mehrere Felder fehlerhaft sind

## Backend-Validierung

### Datenbank-Fehler:
**Fehlertyp:** Save Error
**Nachricht:** "Die Gruppendaten konnten nicht gespeichert werden. Bitte versuchen Sie es erneut."
**Kontext:** Technischer Fehler beim Speichern

### Artikel-Gruppenname Kombination:
**Fehlertyp:** Business Logic
**Nachricht:** "Artikel und Gruppenname müssen zusammen passen (z.B. 'Die Familie Schmidt')"
**Kontext:** Falls Backend-Logik Kombination prüft

## Benutzerführung-Hinweise

### Beim Verlassen des Formulars:
**Fehlertyp:** Navigation Warning
**Nachricht:** "Ihre Gruppendaten sind noch nicht gespeichert. Möchten Sie wirklich fortfahren?"
**Kontext:** Ungespeicherte Änderungen beim Seitenwechsel

### Beispiele-Hilfe:
**Fehlertyp:** Helper Message
**Nachricht:** "Beispiele: 'Die Familie Schmidt', 'Der Hauskreis Müller', 'Das Team Musterstadt'"
**Kontext:** Zusätzliche Hilfe bei wiederholten Fehlern

## Erfolgs-Nachrichten

### Gruppendaten gespeichert:
**Typ:** Success Message
**Nachricht:** "Ihre Gruppendaten wurden erfolgreich gespeichert"
**Kontext:** Nach erfolgreichem Speichern vor Weiterleitung

### Formular vollständig:
**Typ:** Validation Success
**Nachricht:** "✓ Gruppendaten vollständig"
**Kontext:** Grüner Haken bei komplettem Formular

## JavaScript Live-Validierung

### Während der Eingabe:
- **Zeichen-Counter:** "78/80 Zeichen" (wird rot bei >80)
- **Live-Vorschau:** "{Artikel} {Gruppenname} hat..." 

### Artikel-Hilfe:
**Bei Auswahl eines Artikels:** 
"Vorschau: {Artikel} [Ihr Gruppenname] hat durch eine Spende..."

## Accessibility-Hinweise

### Screen Reader:
- **Artikel:** "Artikel für Gruppennamen, Pflichtfeld, Dropdown-Menü"
- **Gruppenname:** "Gruppenname, Pflichtfeld, 2 bis 80 Zeichen"

### Fehlermeldungen für Screen Reader:
- Alle Fehlermeldungen mit `aria-describedby` verknüpft
- Fokus wird auf fehlerhaftes Feld gesetzt
- Fehlerzählung: "2 Fehler im Formular gefunden"

## CSS-Klassen für Styling

### Fehler-States:
- `.error-field` → Feld mit rotem Rahmen
- `.error-message` → Rote Fehlermeldung unter Feld
- `.form-invalid` → Komplettes Formular bei Fehlern

### Success-States:
- `.valid-field` → Feld mit grünem Rahmen
- `.success-message` → Grüne Bestätigungsmeldung