# E-Mail Template: Geschenk-Schenker (mit Versand an Empfänger)

## Betreff:
**Ihr Geschenk wurde zugestellt - Vielen Dank für Ihre Spende!**

## E-Mail-Text:

Liebe/r {SCHENKER_NAME},

vielen Dank für Ihre Geschenk-Spende zur Neuen Genfer Übersetzung! Mit Ihren 100€ haben Sie in Namen von **{EMPFAENGER_NAME}** die Übersetzung des Verses **{VERS_REFERENZ}** ermöglicht.

**Ihr Geschenk wurde zugestellt:**
**{EMPFAENGER_NAME}** hat soeben eine E-Mail mit dem personalisierten Geschenk-Zertifikat erhalten. Das Zertifikat erklärt die Bedeutung Ihres Geschenks und enthält den gesponserten Bibelvers.

**Was Sie erhalten:**
Im Anhang finden Sie eine Kopie des Geschenk-Zertifikats sowie Ihre Spendenbescheinigung für die Steuererklärung. Beide Dokumente sind als PDF-Dateien beigefügt.

**Ihr bleibender Beitrag:**
Mit Ihrer Spende haben Sie in Namen von **{EMPFAENGER_NAME}** eine Investition getätigt, die weit über die eigene Lebenszeit hinauswirkt. Der gesponserte Vers wird Teil einer modernen Bibelübersetzung, die über Jahrzehnte hinweg von Menschen gelesen wird und Leben prägen kann.

Der Vers fließt in den laufenden Übersetzungsprozess der NGÜ ein. Das Übersetzungsteam arbeitet kontinuierlich daran, das gesamte Alte Testament fertigzustellen und hofft, dieses Ziel in den kommenden Jahren zu erreichen.

**Haben Sie Fragen?**
Bei Fragen zu Ihrer Spende oder zum NGÜ-Projekt können Sie uns gerne kontaktieren unter: {KONTAKT_EMAIL}

Mit herzlichen Grüßen

{ABSENDER_NAME}  
Peter-Schöffer-Stiftung  
Im Auftrag der Genfer Bibelgesellschaft

---

**Anhänge:**
- Geschenk-Zertifikat_{EMPFAENGER_NACHNAME}_{VERS_REFERENZ}_Kopie.pdf
- Spendenbescheinigung_{JAHR}_{BESCHEINIGUNGS_NR}.pdf

---

## Template-Variablen:

- `{SCHENKER_NAME}` - Vollständiger Name des Schenkers
- `{EMPFAENGER_NAME}` - Vollständiger Name des Empfängers
- `{VERS_REFERENZ}` - Bibelstelle (z.B. "Psalm_23-1")
- `{KONTAKT_EMAIL}` - Support-E-Mail-Adresse
- `{ABSENDER_NAME}` - Name des E-Mail-Absenders
- `{EMPFAENGER_NACHNAME}` - Nachname für Dateinamen
- `{JAHR}` - Aktuelles Jahr
- `{BESCHEINIGUNGS_NR}` - Nummer der Spendenbescheinigung

## Technische Hinweise:

- **E-Mail-Typ:** HTML + Text
- **Anhänge:** 2 PDF-Dateien (Zertifikat-Kopie + Spendenbescheinigung)
- **Versand-Timing:** Sofort nach erfolgreicher Zahlung UND Empfänger-E-Mail
- **Absender:** noreply@ngue-sponsoring.de (oder ähnlich)
- **Trigger:** Nur wenn "Zertifikat an Empfänger senden" aktiviert war