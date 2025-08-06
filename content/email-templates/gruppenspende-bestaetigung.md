# E-Mail Template: Gruppenspende-Bestätigung

## Betreff-Zeile:
**"Ihr Gruppenzertifikat für {ARTIKEL} {GRUPPENNAME}"**

Beispiele:
- "Ihr Gruppenzertifikat für die Familie Schmidt"
- "Ihr Gruppenzertifikat für den Bibelkreis Musterhausen"
- "Ihr Gruppenzertifikat für das Volleyball-Team Musterdorf"

## E-Mail-Template:

### Anrede:
Liebe {KONTAKTPERSON_ANREDE} {KONTAKTPERSON_NACHNAME},

### Haupttext:
vielen Dank für Ihre Gruppenspende!

**{ARTIKEL} {GRUPPENNAME}** hat durch eine Spende von 100€ erfolgreich die Patenschaft für den Vers **{VERS_REFERENZ}** ({VERS_TEXT_PREVIEW}) übernommen.

Das personalisierte Gruppenzertifikat finden Sie als PDF im Anhang dieser E-Mail.

### Informationen zur Spende:
- **Gesponserte Gruppe:** {ARTIKEL} {GRUPPENNAME}
- **Kontaktperson:** {KONTAKTPERSON_VOLLNAME}
- **Vers-Referenz:** {VERS_REFERENZ}
- **Spendenbetrag:** 100,00 €
- **Datum:** {SPENDE_DATUM}

### Spendenbescheinigung (Wichtiger Hinweis):
Für Gruppenspenden können wir leider keine automatische Spendenbescheinigung erstellen. Falls Sie eine offizielle Spendenbescheinigung für steuerliche Zwecke benötigen, wenden Sie sich bitte an uns:

📧 spenden@peter-schoeffer-stiftung.de  
📞 +49 (0)XXXX XXXXXX

Geben Sie dabei bitte Ihre Transaktions-ID **{STRIPE_PAYMENT_ID}** an.

### Projektinformationen:
Ihre Spende hilft dabei, die verbleibenden 11.000 Verse des Alten Testaments der NGÜ (Neue Genfer Übersetzung) zu finanzieren. Weitere Informationen zum Projekt finden Sie auf unserer Website: https://ngue-bvs.peter-schoeffer-stiftung.de

### Anhang:
- Gruppenzertifikat_{ARTIKEL}_{GRUPPENNAME}_{VERS_REFERENZ}.pdf

---

### Fußzeile:
Mit herzlichen Grüßen  
Das NGÜ-Team

**Peter-Schöffer-Stiftung**  
Musterstraße 123  
12345 Musterstadt

🌐 www.peter-schoeffer-stiftung.de  
📧 info@peter-schoeffer-stiftung.de

Diese E-Mail wurde automatisch generiert. Bei Fragen kontaktieren Sie uns gerne direkt.

## Variablen für Template-System:

### Gruppe:
- `{ARTIKEL}` → Der/Die/Das (mit Großbuchstabe am Satzanfang)
- `{ARTIKEL_KLEIN}` → der/die/das (klein für Sätze)
- `{GRUPPENNAME}` → Name der Gruppe
- `{KONTAKTPERSON_ANREDE}` → Lieber/Liebe
- `{KONTAKTPERSON_VOLLNAME}` → Vor- und Nachname
- `{KONTAKTPERSON_NACHNAME}` → Nur Nachname für Anrede

### Standard-Variablen:
- `{VERS_REFERENZ}` → z.B. "1. Mose 1,1"
- `{VERS_TEXT_PREVIEW}` → Erste 50 Zeichen des Verses
- `{SPENDE_DATUM}` → Datum der Spende
- `{STRIPE_PAYMENT_ID}` → Eindeutige Transaktions-ID

## Technische Hinweise:
- Gruppenspende-E-Mails verwenden eigenes Template (nicht das Standard-Template)
- Keine automatische Spendenbescheinigung im Anhang
- Gruppenzertifikat-PDF hat spezielle Namenskonvention
- Template-Logik muss Artikel-Groß-/Kleinschreibung berücksichtigen