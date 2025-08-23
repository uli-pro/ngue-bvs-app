# Gruppenspende-Daten - Formular-Texte

## Überschrift:
**"Ihre Gruppendaten"**

## Formular-Felder:

### Artikel (Pflichtfeld)
**Label:** Artikel für das Zertifikat *
**Input:** Dropdown-Auswahl
**Optionen:**
- Der
- Die  
- Das

**Hilfetext:** 
"Wählen Sie den passenden Artikel für Ihren Gruppennamen. Dieser wird für die grammatikalisch korrekte Formulierung auf dem Zertifikat benötigt."

### Gruppenname (Pflichtfeld)
**Label:** Gruppenname *
**Input:** Textfeld (2-80 Zeichen)
**Placeholder:** "z.B. Bibelkreis Musterhausen"

**Hilfetext:** 
"Geben Sie den Namen Ihrer Gruppe ein, wie er auf dem Zertifikat erscheinen soll."

## Beispiele-Box:
**Überschrift:** "Beispiele für Artikel + Gruppennamen:"
- **Die** Jungschar Mustertadt
- **Der** Bibelclub Musterhausen  
- **Das** Volleyball-Team Musterdorf
- **Die** Familie Schmidt
- **Der** Hauskreis Musterweg

## Info-Boxen:

### Info-Box Kontaktperson:
**Symbol:** ℹ️
**Text:** 
"Sie sind die Kontaktperson für diese Gruppenspende. Das Zertifikat wird an Ihre E-Mail-Adresse gesendet."

### Hinweis-Box Spendenbestätigung:
**Symbol:** ⚠️  
**Überschrift:** "Spendenbestätigung für Gruppen"
**Text:** 
"Für Gruppenspenden können wir keine automatische Spendenbestätigung erstellen. Kontaktieren Sie uns bei Bedarf unter: spenden@peter-schoeffer-stiftung.de"

## Validierung:

### Artikel:
- **Required:** Ja
- **Fehlermeldung:** "Bitte wählen Sie einen Artikel aus"

### Gruppenname:
- **Required:** Ja
- **Min Length:** 2 Zeichen
- **Max Length:** 80 Zeichen
- **Fehlermeldungen:**
  - Leer: "Bitte geben Sie einen Gruppennamen ein"
  - Zu kurz: "Der Gruppenname muss mindestens 2 Zeichen haben"
  - Zu lang: "Der Gruppenname darf maximal 80 Zeichen haben"

## Technische Hinweise:
- Erscheint nur bei Auswahl "Als Gruppe" 
- Beide Felder sind Pflichtfelder
- Artikel und Gruppenname werden zusammen für Zertifikat-Generierung verwendet
- Sonderzeichen in Gruppenname sind erlaubt