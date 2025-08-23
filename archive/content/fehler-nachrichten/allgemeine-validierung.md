# Allgemeine Validierungs-Fehlermeldungen

## Formular-Validierung

### Pflichtfelder
- **Feld leer:** "Dieses Feld ist erforderlich."
- **Auswahl fehlt:** "Bitte wählen Sie eine Option."
- **Checkbox nicht aktiviert:** "Diese Zustimmung ist erforderlich."

### E-Mail-Validierung
- **Format ungültig:** "Bitte geben Sie eine gültige E-Mail-Adresse ein."
- **E-Mail bereits registriert:** "Diese E-Mail-Adresse ist bereits registriert. [Zur Anmeldung]"
- **E-Mail nicht gefunden:** "Diese E-Mail-Adresse ist nicht registriert."

### Passwort-Validierung
- **Zu kurz:** "Das Passwort muss mindestens 8 Zeichen lang sein."
- **Zu schwach:** "Das Passwort muss Groß- und Kleinbuchstaben sowie mindestens eine Zahl enthalten."
- **Passwörter unterschiedlich:** "Die Passwörter stimmen nicht überein."

### Text-Validierung
- **Zu kurz:** "Dieser Text muss mindestens {MIN} Zeichen lang sein."
- **Zu lang:** "Dieser Text darf maximal {MAX} Zeichen lang sein."
- **Ungültige Zeichen:** "Bitte verwenden Sie nur Buchstaben, Zahlen und folgende Sonderzeichen: .,!?-"

### Zahlen-Validierung
- **PLZ ungültig:** "Bitte geben Sie eine gültige 5-stellige Postleitzahl ein."
- **Telefonnummer ungültig:** "Bitte geben Sie eine gültige Telefonnummer ein."

### Datums-Validierung
- **Datum in Zukunft:** "Das Datum darf nicht in der Zukunft liegen."
- **Datum zu alt:** "Bitte wählen Sie ein aktuelleres Datum."

## Technische Fehlermeldungen

### Netzwerk-Fehler
- **Keine Verbindung:** "Verbindung fehlgeschlagen. Bitte prüfen Sie Ihre Internetverbindung."
- **Server nicht erreichbar:** "Der Server ist momentan nicht erreichbar. Bitte versuchen Sie es später erneut."
- **Timeout:** "Die Anfrage hat zu lange gedauert. Bitte versuchen Sie es erneut."

### Session-Fehler
- **Session abgelaufen:** "Ihre Sitzung ist abgelaufen. Bitte laden Sie die Seite neu."
- **Nicht angemeldet:** "Bitte melden Sie sich an, um fortzufahren."
- **Keine Berechtigung:** "Sie haben keine Berechtigung für diese Aktion."

### Allgemeine Fehler
- **Unbekannter Fehler:** "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut."
- **Wartungsarbeiten:** "Die Website wird momentan gewartet. Bitte versuchen Sie es in wenigen Minuten erneut."

## Formular-spezifische Validierung

### Bibelstellen-Format
- **Format ungültig:** "Bitte verwenden Sie das Format: Buch Kapitel,Vers"
- **Buch unbekannt:** "Das Buch '{BUCH}' wurde nicht gefunden."
- **Kapitel nicht vorhanden:** "Kapitel {KAPITEL} existiert nicht in {BUCH}."
- **Vers nicht vorhanden:** "Vers {VERS} existiert nicht in {BUCH} {KAPITEL}."

### Such-Validierung
- **Suchbegriff zu kurz:** "Der Suchbegriff muss mindestens 3 Zeichen lang sein."
- **Keine Sonderzeichen:** "Bitte verwenden Sie nur Buchstaben und Zahlen für die Suche."

## Hinweise zur Verwendung
- Verwenden Sie Platzhalter ({VARIABLE}) für dynamische Werte
- Halten Sie Fehlermeldungen kurz und präzise
- Bieten Sie wenn möglich Lösungsvorschläge an
- Verwenden Sie einheitliche Formulierungen