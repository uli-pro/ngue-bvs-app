# Spendenbescheinigung NGÜ - Dokumentation

## Übersicht
Rechtskonforme Zuwendungsbestätigung für die Peter-Schöffer-Stiftung zur Bestätigung von Spenden für das NGÜ Bibelvers-Sponsoring-Projekt.

## Textinhalt der Spendenbescheinigung

### Kopfbereich
```
Peter-Schöffer-Stiftung
„Ingenium vires superat" - Geist übertrifft Stärke
Zuwendungsbestätigung Nr.: [JAHR]-[LAUFENDE_NR]
```

### Haupttitel
**Bestätigung über Geldzuwendungen/Mitgliedsbeitrag**
*im Sinne des § 10b des Einkommensteuergesetzes an eine der in § 5 Abs. 1 Nr. 9 des Körperschaftsteuergesetzes bezeichneten Körperschaften, Personenvereinigungen oder Vermögensmassen*

### Empfängeradresse
```
[ANREDE]
[VORNAME] [NACHNAME]
[STRASSE] [HAUSNUMMER]
[PLZ] [ORT]
```

### Bestätigungstext
**Wir bestätigen, dass die Zuwendung nur zur Förderung der Religion, der Erziehung, Volks- und Berufsbildung einschließlich der Studentenhilfe sowie Kunst und Kultur verwendet wird.**

### Spendendetails
- **Betrag der Zuwendung - in Ziffern -:** 100,00 €
- **- in Buchstaben -:** Einhundert Euro
- **Tag der Zuwendung:** [DATUM]
- **Zweck der Zuwendung:** Finanzierung der Übersetzung eines Bibelverses für die NGÜ - [BIBELSTELLE]
- **Verzicht auf Erstattung von Aufwendungen:** Nein ☑

### Freistellungsbescheid
**Angaben zum Zuwendungsempfänger:**

Die Peter-Schöffer-Stiftung ist wegen Förderung der Religion, von Bildung und Erziehung sowie von Kunst und Kultur nach dem letzten uns zugegangenen Freistellungsbescheid des Finanzamts [FINANZAMT] vom [DATUM_FREISTELLUNG], Steuernummer [STEUERNUMMER], nach § 5 Abs. 1 Nr. 9 des Körperschaftsteuergesetzes von der Körperschaftsteuer und nach § 3 Nr. 6 des Gewerbesteuergesetzes von der Gewerbesteuer befreit.

Die Einhaltung der satzungsmäßigen Voraussetzungen nach den §§ 51, 59, 60 und 61 AO wurde vom Finanzamt [FINANZAMT] mit Bescheid vom [DATUM_BESCHEID] nach § 60a AO gesondert festgestellt. Wir fördern nach unserer Satzung die oben angekreuzten Zwecke.

### Unterschriften
- **Links:** Worms, [DATUM_AUSSTELLUNG]
- **Rechts:** [Digitale Unterschrift] Daniel Weninger, Vorstand

### Rechtliche Hinweise
**Hinweis:**
Wer vorsätzlich oder grob fahrlässig eine unrichtige Zuwendungsbestätigung erstellt oder veranlasst, dass Zuwendungen nicht zu den in der Zuwendungsbestätigung angegebenen steuerbegünstigten Zwecken verwendet werden, haftet für die entgangene Steuer (§ 10b Abs. 4 EStG, § 9 Abs. 3 KStG, § 9 Nr. 5 GewStG).

Diese Zuwendungsbestätigung wird nur für Zwecke der Einkommensteuer-Veranlagung anerkannt, wenn sie in deutscher Sprache ausgestellt ist, das Datum der Zuwendung, die Höhe der Zuwendung in Ziffern und Buchstaben sowie die Angaben zum Zuwendungsempfänger und die Unterschrift enthält.

**Besonderer Hinweis zur NGÜ-Übersetzung:**
Ihre Spende unterstützt die Vollendung der Neuen Genfer Übersetzung (NGÜ) des Alten Testaments. Die Peter-Schöffer-Stiftung fördert dieses Projekt im Rahmen ihrer satzungsmäßigen Zwecke zur Förderung von Religion, Bildung und Kultur in der Tradition humanistischer Bildungsideale der Renaissance.

---

## Entwicklungshinweise

### Platzhalter-Variablen

| Platzhalter | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `[JAHR]` | Aktuelles Jahr | 2025 |
| `[LAUFENDE_NR]` | Fortlaufende Nummer (5-stellig) | 00001 |
| `[ANREDE]` | Anrede des Spenders | Herr/Frau/Eheleute/Firma |
| `[VORNAME]` | Vorname des Spenders | Max |
| `[NACHNAME]` | Nachname des Spenders | Mustermann |
| `[STRASSE]` | Straßenname | Hauptstraße |
| `[HAUSNUMMER]` | Hausnummer | 42 |
| `[PLZ]` | Postleitzahl | 67547 |
| `[ORT]` | Ort | Worms |
| `[DATUM]` | Datum der Spende | 06.08.2025 |
| `[DATUM_AUSSTELLUNG]` | Datum der Ausstellung | 07.08.2025 |
| `[BIBELSTELLE]` | Gesponserte Bibelstelle | Genesis 1,1 |
| `[FINANZAMT]` | Zuständiges Finanzamt | Worms-Kirchheimbolanden |
| `[DATUM_FREISTELLUNG]` | Datum des Freistellungsbescheids | 15.03.2023 |
| `[STEUERNUMMER]` | Steuernummer der Stiftung | 44/670/12345 |
| `[DATUM_BESCHEID]` | Datum des § 60a AO Bescheids | 15.03.2023 |

### Rechtliche Anforderungen ✅

- **Amtliches Muster**: Streng nach § 50 Abs. 1 EStDV
- **Keine Umformulierungen**: Vorgeschriebene Texte 1:1 übernommen
- **Format**: Maximal eine DIN-A4-Seite
- **Betragsangabe**: Sowohl in Ziffern als auch in Buchstaben
- **Haftungshinweise**: Vollständig nach Vorgabe enthalten
- **Keine Werbung**: Vorderseite frei von Werbung/Danksagungen
- **Freistellungsbescheid**: Maximal 5 Jahre alt
- **Digitale Unterschrift**: Als Faksimile rechtlich zulässig

### Technische Implementierung

#### Python-Beispiel für Platzhalter-Ersetzung
```python
from datetime import datetime

def generate_spendenbescheinigung(donation_data):
    """
    Generiert eine Spendenbescheinigung mit den Spendendaten
    
    Args:
        donation_data (dict): Dictionary mit allen Spendendaten
    
    Returns:
        str: HTML-String der fertigen Spendenbescheinigung
    """
    # Template laden
    with open('templates/spendenbescheinigung.html', 'r') as f:
        template = f.read()
    
    # Automatische Werte
    current_year = datetime.now().year
    ausstellung_datum = datetime.now().strftime('%d.%m.%Y')
    laufende_nr = str(donation_data['id']).zfill(5)
    
    # Platzhalter ersetzen
    replacements = {
        '[JAHR]': str(current_year),
        '[LAUFENDE_NR]': laufende_nr,
        '[ANREDE]': donation_data['anrede'],
        '[VORNAME]': donation_data['vorname'],
        '[NACHNAME]': donation_data['nachname'],
        '[STRASSE]': donation_data['strasse'],
        '[HAUSNUMMER]': donation_data['hausnummer'],
        '[PLZ]': donation_data['plz'],
        '[ORT]': donation_data['ort'],
        '[DATUM]': donation_data['spenden_datum'],
        '[DATUM_AUSSTELLUNG]': ausstellung_datum,
        '[BIBELSTELLE]': donation_data['bibelstelle'],
        '[FINANZAMT]': 'Worms-Kirchheimbolanden',
        '[DATUM_FREISTELLUNG]': '15.03.2023',
        '[STEUERNUMMER]': '44/670/12345',
        '[DATUM_BESCHEID]': '15.03.2023'
    }
    
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    
    return template
```

#### PDF-Generierung mit WeasyPrint
```python
from weasyprint import HTML
import os

def create_pdf(html_content, output_path):
    """
    Erstellt ein PDF aus HTML-Content
    
    Args:
        html_content (str): HTML-String
        output_path (str): Pfad für die PDF-Datei
    """
    # PDF generieren
    HTML(string=html_content).write_pdf(output_path)
    
    return output_path

# Verwendung
donation_data = {
    'id': 42,
    'anrede': 'Herr',
    'vorname': 'Max',
    'nachname': 'Mustermann',
    'strasse': 'Hauptstraße',
    'hausnummer': '42',
    'plz': '67547',
    'ort': 'Worms',
    'spenden_datum': '06.08.2025',
    'bibelstelle': 'Genesis 1,1'
}

html = generate_spendenbescheinigung(donation_data)
pdf_path = create_pdf(html, f'spendenbescheinigungen/2025-00042.pdf')
```

### Datenbankstruktur

```sql
-- Tabelle für Spendenbescheinigungen
CREATE TABLE spendenbescheinigungen (
    id SERIAL PRIMARY KEY,
    jahr INTEGER NOT NULL,
    laufende_nummer INTEGER NOT NULL,
    purchase_id INTEGER REFERENCES purchases(id),
    ausstellungsdatum DATE NOT NULL,
    pdf_path VARCHAR(255),
    email_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(jahr, laufende_nummer)
);

-- Index für effiziente Suche
CREATE INDEX idx_spendenbescheinigung_purchase 
ON spendenbescheinigungen(purchase_id);
```

### Archivierung

- **Elektronisch**: Mindestens 7 Jahre
- **Papier**: Mindestens 10 Jahre (falls ausgedruckt)
- **Format**: PDF/A für Langzeitarchivierung
- **Backup**: Regelmäßige Sicherungen auf separatem Server

### Digitale Unterschrift

#### Option 1: Bilddatei (empfohlen)
```python
# Unterschrift als PNG mit Transparenz
SIGNATURE_PATH = 'static/signatures/d_weninger.png'

# In HTML-Template einbinden
<img src="{{ url_for('static', filename='signatures/d_weninger.png') }}" 
     style="height: 60px;" 
     alt="Unterschrift Daniel Weninger">
```

#### Option 2: SVG (wie im Template)
- Vorteil: Skalierbar, kleine Dateigröße
- Nachteil: Muss manuell erstellt werden

### E-Mail-Versand

```python
from flask_mail import Message, Mail

def send_spendenbescheinigung(email, pdf_path, bibelstelle):
    """
    Versendet die Spendenbescheinigung per E-Mail
    """
    msg = Message(
        'Ihre Spendenbescheinigung - NGÜ Bibelvers-Sponsoring',
        sender='noreply@peter-schoeffer-stiftung.de',
        recipients=[email]
    )
    
    msg.body = f"""
    Sehr geehrte/r Spender/in,

    vielen Dank für Ihre Spende zur Unterstützung der NGÜ-Übersetzung!
    Sie haben den Vers {bibelstelle} gesponsert.

    Im Anhang finden Sie Ihre offizielle Spendenbescheinigung für 
    Ihre Steuerunterlagen.

    Mit freundlichen Grüßen
    Peter-Schöffer-Stiftung
    """
    
    with open(pdf_path, 'rb') as f:
        msg.attach(
            f'Spendenbescheinigung_{bibelstelle.replace(" ", "_")}.pdf',
            'application/pdf',
            f.read()
        )
    
    mail.send(msg)
```

### Wichtige Hinweise

⚠️ **Haftung**: Bei fehlerhafter Ausstellung haftet die Stiftung mit 30% der Spendenbeträge plus Verzugszinsen

⚠️ **Freistellungsbescheid**: Muss aktuell sein (max. 5 Jahre alt) und regelmäßig erneuert werden

⚠️ **Nummerierung**: Fortlaufende Nummern pro Jahr, keine Lücken oder Doppelungen

✅ **Testing**: Vor Produktivstart unbedingt mit echtem Finanzamt/Steuerberater prüfen lassen