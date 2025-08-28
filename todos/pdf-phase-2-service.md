# PDF Phase 2: PDFGeneratorService implementieren

**Status:** TODO  
**Priorität:** Hoch  
**Abhängigkeiten:** Phase 1 (Templates)  
**Geschätzte Zeit:** 6-8 Stunden

## Überblick

Diese Phase implementiert den PDFGeneratorService, der HTML-Templates in PDF-Dokumente konvertiert, Dateien speichert und Certificate-Records in der Datenbank erstellt.

### ✅ Phase 1 Ergebnisse (Basis für Phase 2):
- **Template-Struktur**: Vollständig implementiert mit Montserrat-Font
- **Verzeichnisse**: `templates/certificates/` und `static/certificates/` erstellt
- **Hintergrundbild**: `certificate-background.png` in `/static/certificates/` verfügbar
- **CSS-Integration**: `certificate_styles.css` mit A4-Positionierung und Print-Optimierung
- **Template-Typen**: 4 funktionsfähige Templates (personal, group, gift, tax_receipt)
- **Datenmodell-Mapping**: Korrekte Zuordnung aus `person_snapshot` (JSONB) und `donation_details`

## Aufgaben-Checkliste

### 1. Service-Datei erstellen

- [ ] **Datei erstellen**: `pdf_service.py` im Projektroot
- [ ] **Imports konfigurieren**: WeasyPrint, Flask, SQLAlchemy
- [ ] **Klassen-Struktur**: PDFGeneratorService mit allen Methoden
- [ ] **Exception-Klassen**: Eigene Exceptions definieren

#### Code-Vorlage pdf_service.py (Grundstruktur):
```python
"""
PDF Generator Service für NGÜ Bibelvers-Sponsoring App
Generiert Zertifikate und Spendenbescheinigungen mit WeasyPrint
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Tuple, Any
import weasyprint
from flask import Flask, render_template, current_app
from models import db, Donation, Certificate, Person, Verse

# Custom Exceptions
class PDFGenerationError(Exception):
    """PDF-Generierung fehlgeschlagen"""
    pass

class FileSystemError(PDFGenerationError):
    """Dateisystem-Operation fehlgeschlagen"""
    pass

class TemplateNotFoundError(PDFGenerationError):
    """PDF-Template nicht gefunden"""
    pass

class ValidationError(PDFGenerationError):
    """Ungültige Parameter"""
    pass

class PDFGeneratorService:
    """Service für PDF-Generierung von Zertifikaten und Spendenbescheinigungen"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Flask-App initialisieren"""
        app.config.setdefault('CERTIFICATE_STORAGE_PATH', '/tmp/certificates')
        app.config.setdefault('PDF_TEMPLATE_PATH', 'templates/certificates')
        
    # Hauptmethoden hier implementieren...
```

### 2. Hauptmethoden implementieren

#### 2.1 Certificate-Generierung

- [ ] **Methode**: `generate_certificate(donation_id: int, certificate_type: str) -> Certificate`
- [ ] **Parameter-Validierung**: donation_id und certificate_type prüfen
- [ ] **Daten laden**: Donation mit Person und Verse laden
- [ ] **Template-Context**: Alle Template-Variablen vorbereiten
- [ ] **PDF generieren**: WeasyPrint aufrufen
- [ ] **Certificate-Record**: In Datenbank speichern

#### Code-Vorlage generate_certificate():
```python
def generate_certificate(self, donation_id: int, certificate_type: str, 
                        session_id: Optional[str] = None) -> Certificate:
    """
    Generiert PDF-Zertifikat und erstellt Certificate-Record
    
    Args:
        donation_id: ID der Spende
        certificate_type: personal_certificate, group_certificate, gift_certificate
        session_id: Shopping Cart Session ID für Pfad-Gruppierung
        
    Returns:
        Certificate: Erstellter Certificate-Record mit file_path und filename
        
    Raises:
        PDFGenerationError: Bei Fehlern in der PDF-Erstellung
        FileSystemError: Bei Dateisystem-Problemen
        ValidationError: Bei ungültigen Parametern
    """
    # 1. Parameter validieren
    if not donation_id or certificate_type not in [
        'personal_certificate', 'group_certificate', 'gift_certificate'
    ]:
        raise ValidationError(f"Invalid parameters: {donation_id}, {certificate_type}")
    
    # 2. Donation laden
    donation = Donation.query.get(donation_id)
    if not donation:
        raise ValidationError(f"Donation {donation_id} not found")
    
    if donation.payment_status != 'completed':
        raise ValidationError(f"Donation {donation_id} not completed")
    
    try:
        # 3. Pfad und Dateiname generieren
        filename, file_path = self._generate_certificate_paths(
            donation, certificate_type, session_id
        )
        
        # 4. Template-Context vorbereiten
        context = self._prepare_certificate_context(donation, certificate_type)
        
        # 5. HTML rendern
        template_name = f"certificates/{certificate_type}.html"
        html_content = render_template(template_name, **context)
        
        # 6. PDF generieren
        self._generate_pdf_from_html(html_content, file_path)
        
        # 7. Certificate-Record erstellen
        certificate = Certificate(
            donation_id=donation.id,
            certificate_type=certificate_type,
            filename=filename,
            file_path=file_path
        )
        
        db.session.add(certificate)
        db.session.commit()
        
        return certificate
        
    except Exception as e:
        db.session.rollback()
        # Cleanup: PDF-Datei löschen falls erstellt
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise PDFGenerationError(f"Certificate generation failed: {str(e)}")
```

#### 2.2 Tax-Receipt-Generierung

- [ ] **Methode**: `generate_tax_receipt(donation_id: int, session_id: Optional[str]) -> Certificate`
- [ ] **Betrag in Worten**: Funktion für Textkonvertierung
- [ ] **Separates Template**: tax_receipt.html verwenden
- [ ] **Stiftungsdaten**: Fest eingebaute Werte

#### Code-Vorlage generate_tax_receipt():
```python
def generate_tax_receipt(self, donation_id: int, 
                        session_id: Optional[str] = None) -> Certificate:
    """Generiert Spendenbescheinigung für Steuer"""
    
    donation = Donation.query.get(donation_id)
    if not donation or donation.payment_status != 'completed':
        raise ValidationError(f"Invalid donation {donation_id}")
    
    try:
        # Pfad generieren
        filename, file_path = self._generate_certificate_paths(
            donation, 'tax_receipt', session_id
        )
        
        # Context für Spendenbescheinigung
        context = self._prepare_tax_receipt_context(donation)
        
        # HTML rendern
        html_content = render_template('certificates/tax_receipt.html', **context)
        
        # PDF generieren
        self._generate_pdf_from_html(html_content, file_path)
        
        # Certificate-Record
        certificate = Certificate(
            donation_id=donation.id,
            certificate_type='tax_receipt',
            filename=filename,
            file_path=file_path
        )
        
        db.session.add(certificate)
        db.session.commit()
        
        return certificate
        
    except Exception as e:
        db.session.rollback()
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise PDFGenerationError(f"Tax receipt generation failed: {str(e)}")
```

### 3. Hilfsmethoden implementieren

#### 3.1 Pfad-Generierung

- [ ] **Methode**: `_generate_certificate_paths(donation, certificate_type, session_id) -> tuple`
- [ ] **Session-Struktur**: Nach Schema aus requirements.md
- [ ] **Eindeutige Namen**: Timestamp + ID für Eindeutigkeit
- [ ] **Ordner erstellen**: Automatisch wenn nicht vorhanden

#### Code-Vorlage _generate_certificate_paths():
```python
def _generate_certificate_paths(self, donation: Donation, certificate_type: str, 
                               session_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Generiert filename und file_path für Zertifikat
    
    Schema: certificates/YYYY/MM/session_ID/donation_ID_type_YYYYMMDD_HHMMSS.pdf
    
    Returns:
        tuple: (filename, absolute_file_path)
    """
    # Basis-Verzeichnis
    base_dir = current_app.config['CERTIFICATE_STORAGE_PATH']
    
    # Jahr/Monat-Struktur
    now = datetime.now()
    year_month = f"{now.year}/{now.month:02d}"
    
    # Session-Verzeichnis
    session_dir = f"session_{session_id}" if session_id else "no_session"
    
    # Dateiname generieren
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"donation_{donation.id:03d}_{certificate_type}_{timestamp}.pdf"
    
    # Vollständiger Pfad
    directory = os.path.join(base_dir, year_month, session_dir)
    file_path = os.path.join(directory, filename)
    
    # Ordner erstellen falls nicht vorhanden
    os.makedirs(directory, exist_ok=True)
    
    # Sicherheitsprüfung: Path Traversal verhindern
    if not os.path.abspath(file_path).startswith(os.path.abspath(base_dir)):
        raise FileSystemError("Invalid file path detected")
    
    return filename, file_path
```

#### 3.2 Certificate-Context vorbereiten

- [ ] **Methode**: `_prepare_certificate_context(donation, certificate_type) -> dict`
- [ ] **Person-Daten**: Aus person_snapshot oder person laden
- [ ] **Vers-Daten**: Mit Referenz und Text
- [ ] **Spenden-Details**: Je nach donation_type anpassen

#### Code-Vorlage _prepare_certificate_context():
```python
def _prepare_certificate_context(self, donation: Donation, certificate_type: str) -> Dict[str, Any]:
    """Bereitet Template-Context für Zertifikat vor"""
    
    # Person-Daten (bevorzugt aus Snapshot für historische Korrektheit)
    person_data = donation.person_snapshot or {}
    if not person_data:
        person_data = {
            'first_name': donation.person.first_name,
            'last_name': donation.person.last_name,
            'email': donation.person.email
        }
    
    # Vers laden
    verse = donation.verse
    
    # Basis-Context (basierend auf Phase 1 Template-Struktur)
    context = {
        'donation': donation,
        'person_snapshot': person_data,
        'verse': verse,
        'verses': [verse],  # Als Liste für Template-Kompatibilität
        'background_image_path': '/static/certificates/certificate-background.png',  # Phase 1: Kopiert nach /static/certificates/
        'formatted_amount': f"{donation.amount:.2f}",
        'formatted_date': donation.completed_at.strftime('%d.%m.%Y') if donation.completed_at else 'Unbekannt'
    }
    
    # Typ-spezifische Anpassungen
    if certificate_type == 'group_certificate':
        details = donation.donation_details or {}
        context['group_article'] = details.get('group_article', '')
        context['group_name'] = details.get('group_name', '')
        
    elif certificate_type == 'gift_certificate':
        details = donation.donation_details or {}
        context['recipient_first_name'] = details.get('recipient_first_name', '')
        context['recipient_last_name'] = details.get('recipient_last_name', '')
    
    return context
```

#### 3.3 Tax-Receipt-Context vorbereiten

- [ ] **Methode**: `_prepare_tax_receipt_context(donation) -> dict`
- [ ] **Betrag in Worten**: `_amount_to_words()` aufrufen
- [ ] **Stiftungsdaten**: Peter-Schöffer-Stiftung Konstanten
- [ ] **Formular-Felder**: Alle required fields

#### Code-Vorlage _prepare_tax_receipt_context():
```python
def _prepare_tax_receipt_context(self, donation: Donation) -> Dict[str, Any]:
    """Bereitet Context für Spendenbescheinigung vor"""
    
    person_data = donation.person_snapshot or {
        'first_name': donation.person.first_name,
        'last_name': donation.person.last_name,
        'street': donation.person.street,
        'house_number': donation.person.house_number,
        'postal_code': donation.person.postal_code,
        'city': donation.person.city
    }
    
    context = {
        'donation': donation,
        'person_snapshot': person_data,
        'formatted_amount': f"{donation.amount:.2f}",
        'amount_in_words': self._amount_to_words(donation.amount),
        'formatted_date': donation.completed_at.strftime('%d. %B %Y') if donation.completed_at else '',
        'issue_date': datetime.now().strftime('%d. %B %Y'),
        
        # Stiftungsdaten (konstant - basierend auf Phase 1 tax_receipt.html)
        'foundation': {
            'name': 'Peter-Schöffer-Stiftung',
            'street': 'Wormser Weg 17',
            'postal_code': '67574',
            'city': 'Osthofen',
            'tax_number': '07/456/78901',  # Korrekte StNr aus Phase 1
            'tax_office': 'Finanzamt Worms'
        }
    }
    
    return context
```

#### 3.4 Betrag in Worten konvertieren

- [ ] **Methode**: `_amount_to_words(amount: Decimal) -> str`
- [ ] **Deutsche Zahlwörter**: Ein, zwei, drei... bis Tausende
- [ ] **Euro-Format**: "Einhundert Euro" etc.

#### Code-Vorlage _amount_to_words():
```python
def _amount_to_words(self, amount: Decimal) -> str:
    """Konvertiert Dezimalbetrag in deutsche Zahlwörter"""
    
    # Vereinfachte Implementierung für gängige Beträge (0-9999 Euro)
    ones = ['null', 'ein', 'zwei', 'drei', 'vier', 'fünf', 'sechs', 'sieben', 'acht', 'neun']
    teens = ['zehn', 'elf', 'zwölf', 'dreizehn', 'vierzehn', 'fünfzehn', 
             'sechzehn', 'siebzehn', 'achtzehn', 'neunzehn']
    tens = ['', '', 'zwanzig', 'dreißig', 'vierzig', 'fünfzig', 'sechzig', 
            'siebzig', 'achtzig', 'neunzig']
    hundreds = ['', 'einhundert', 'zweihundert', 'dreihundert', 'vierhundert',
                'fünfhundert', 'sechshundert', 'siebenhundert', 'achthundert', 'neunhundert']
    
    amount_int = int(amount)
    
    if amount_int == 100:
        return "Einhundert"
    elif amount_int < 1000:
        # Für Beträge 100-999
        h = amount_int // 100
        remainder = amount_int % 100
        
        result = hundreds[h] if h > 0 else ''
        
        if remainder >= 10 and remainder < 20:
            result += teens[remainder - 10]
        elif remainder >= 20:
            t = remainder // 10
            o = remainder % 10
            if o > 0:
                result += ones[o] + 'und' + tens[t]
            else:
                result += tens[t]
        elif remainder > 0:
            result += ones[remainder]
        
        return result.capitalize()
    
    # Fallback für komplexere Beträge
    return f"{amount_int}"
```

#### 3.5 PDF-Generierung aus HTML

- [ ] **Methode**: `_generate_pdf_from_html(html_content: str, output_path: str)`
- [ ] **WeasyPrint-Konfiguration**: CSS und Schriften
- [ ] **Error-Handling**: WeasyPrint-spezifische Errors
- [ ] **File-Permissions**: Korrekte Berechtigungen setzen

#### Code-Vorlage _generate_pdf_from_html():
```python
def _generate_pdf_from_html(self, html_content: str, output_path: str):
    """Generiert PDF aus HTML-Content mit WeasyPrint"""
    
    try:
        # WeasyPrint-Konfiguration (Phase 1: CSS-Pfad korrekt)
        css = weasyprint.CSS(filename='static/certificates/css/certificate_styles.css')
        
        # HTML-Document erstellen
        html_doc = weasyprint.HTML(string=html_content, base_url=current_app.static_folder)
        
        # PDF generieren (Phase 1: Montserrat wird über Google Fonts geladen)
        html_doc.write_pdf(
            target=output_path,
            stylesheets=[css],
            font_config=None,  # System-Schriften + Google Fonts
            presentational_hints=True
        )
        
        # Datei-Berechtigungen setzen (lesbar für Web-Server)
        os.chmod(output_path, 0o644)
        
    except Exception as e:
        raise PDFGenerationError(f"WeasyPrint failed: {str(e)}")
```

### 4. Batch-Operationen

- [ ] **Methode**: `generate_certificate_batch(donation_ids: List[int], session_id: str) -> List[Certificate]`
- [ ] **Mehrere PDFs**: Loop durch donation_ids
- [ ] **Transaction-Handling**: Alles oder nichts
- [ ] **Progress-Tracking**: Optional für große Batches

#### Code-Vorlage generate_certificate_batch():
```python
def generate_certificate_batch(self, donation_ids: List[int], 
                              session_id: str) -> List[Certificate]:
    """Batch-Generierung für mehrere Zertifikate einer Session"""
    
    certificates = []
    
    try:
        for donation_id in donation_ids:
            donation = Donation.query.get(donation_id)
            if not donation:
                continue
                
            # Certificate-Type bestimmen
            if donation.donation_type == 'person':
                cert_type = 'personal_certificate'
            elif donation.donation_type == 'gruppe':
                cert_type = 'group_certificate'
            elif donation.donation_type == 'geschenk':
                cert_type = 'gift_certificate'
            else:
                cert_type = 'personal_certificate'  # Default
            
            # Zertifikat generieren
            cert = self.generate_certificate(donation_id, cert_type, session_id)
            certificates.append(cert)
            
            # Tax Receipt wenn gewünscht
            if donation.wants_receipt:
                tax_cert = self.generate_tax_receipt(donation_id, session_id)
                certificates.append(tax_cert)
        
        return certificates
        
    except Exception as e:
        # Bei Fehler alle erstellten Dateien löschen
        for cert in certificates:
            if cert.file_path and os.path.exists(cert.file_path):
                os.remove(cert.file_path)
        raise PDFGenerationError(f"Batch generation failed: {str(e)}")
```

### 5. Service in Flask-App registrieren

- [ ] **app.py erweitern**: Service-Instanz erstellen
- [ ] **Config-Werte**: CERTIFICATE_STORAGE_PATH setzen
- [ ] **Import hinzufügen**: pdf_service importieren

#### Code-Vorlage für app.py Integration:
```python
# In app.py
from pdf_service import PDFGeneratorService

# Nach App-Erstellung
pdf_service = PDFGeneratorService()
pdf_service.init_app(app)

# Config-Werte
app.config['CERTIFICATE_STORAGE_PATH'] = os.path.join(os.getcwd(), 'certificates')
app.config['PDF_TEMPLATE_PATH'] = 'templates/certificates'
```

## Testing-Strategien

### Unit-Tests

- [ ] **Test-Datei**: `tests/test_pdf_service.py`
- [ ] **Mock-Daten**: Test-Donations und Persons
- [ ] **Template-Tests**: HTML-Rendering testen
- [ ] **PDF-Tests**: WeasyPrint-Output validieren

#### Test-Vorlage:
```python
import pytest
from pdf_service import PDFGeneratorService, PDFGenerationError

def test_generate_personal_certificate(app, test_donation):
    """Test PDF-Generierung für persönliches Zertifikat"""
    with app.app_context():
        service = PDFGeneratorService(app)
        
        # PDF generieren
        certificate = service.generate_certificate(
            test_donation.id, 
            'personal_certificate', 
            'test_session_123'
        )
        
        # Assertions
        assert certificate.certificate_type == 'personal_certificate'
        assert certificate.filename.endswith('.pdf')
        assert os.path.exists(certificate.file_path)
        
        # Cleanup
        os.remove(certificate.file_path)
```

### Integration-Tests

- [ ] **End-to-End**: Kompletter Flow von Donation zu PDF
- [ ] **Database-Tests**: Certificate-Records validieren
- [ ] **File-System-Tests**: Ordnerstruktur prüfen

## Fehlerbehandlung

### Häufige Probleme:
1. **WeasyPrint Fonts**: System-Schriften nicht gefunden
2. **CSS-Pfade**: Relative Pfade funktionieren nicht
3. **Speicherplatz**: Zu wenig Disk Space
4. **Permissions**: Schreibrechte auf Zielordner
5. **Phase 1 spezifisch**: Montserrat-Font über Google Fonts vs. lokale Installation

### Lösungsansätze:
```python
# Font-Fallbacks (Phase 1: Montserrat mit Fallback-Kette)
CSS_FONT_CONFIG = """
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');

body {
    font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif;
}

/* Für tax_receipt.html */
.tax-receipt {
    font-family: 'Times New Roman', serif;
}
"""

# Error-Recovery für WeasyPrint + Google Fonts
try:
    html_doc.write_pdf(output_path, stylesheets=[css])
except Exception as e:
    # Fallback: Template ohne Google Fonts rendern
    html_content_fallback = html_content.replace('@import url(', '/* @import url(')
    html_doc = weasyprint.HTML(string=html_content_fallback, base_url=current_app.static_folder)
    html_doc.write_pdf(output_path, stylesheets=[css])
```

## Performance-Überlegungen

### Optimierungen:
- [ ] **Template-Caching**: Jinja2-Templates cachen
- [ ] **CSS-Kompilierung**: Einmal kompilierte CSS wiederverwenden
- [ ] **Async-Processing**: Für große Batches
- [ ] **Memory-Management**: Große PDF-Objekte früh freigeben

## Phase 1 Implementierungsdetails (Referenz)

### Template-Pfade (Erstellt):
```
templates/certificates/
├── base_certificate.html           # Basis-Template mit Montserrat
├── personal_certificate.html       # Persönliches Zertifikat
├── group_certificate.html          # Gruppenzertifikat  
├── gift_certificate.html           # Geschenkzertifikat
└── tax_receipt.html                 # Spendenbescheinigung (Times New Roman)

static/certificates/
├── certificate-background.png       # Hintergrundbild (kopiert)
├── css/
│   └── certificate_styles.css      # A4-Styles mit Montserrat
└── fonts/                          # Vorbereitet für lokale Fonts
```

### Template-Variablen (Verwendet):
```python
# Alle Zertifikat-Templates erwarten:
context = {
    'donation': donation,                    # SQLAlchemy Donation object
    'person_snapshot': person_snapshot,      # JSONB dict mit Personendaten
    'verses': [verse],                       # Liste von Verse objects
    'background_image_path': '/static/certificates/certificate-background.png'
}

# Typ-spezifische Variablen:
# group_certificate.html:
donation.donation_details['group_article']   # Der/Die/Das
donation.donation_details['group_name']      # Gruppenname

# gift_certificate.html:
donation.donation_details['recipient_first_name']  # Beschenkter Vorname
donation.donation_details['recipient_last_name']   # Beschenkter Nachname

# tax_receipt.html:
'amount_in_words'                    # Betrag in Worten (Service-Methode)
```

### WeasyPrint-Kompatibilität (Validiert):
- ✅ Montserrat über Google Fonts funktioniert
- ✅ A4-Dimensionen (210mm x 297mm) korrekt
- ✅ Absolute Positionierung für Textfelder  
- ✅ Print-CSS mit color-adjust funktioniert
- ✅ Template-Vererbung mit {% extends %} funktioniert

## Nächste Schritte

Nach Abschluss dieser Phase:
1. **Phase 3**: Database-Integration verfeinern
2. **Testing**: Umfassende Tests implementieren
3. **Performance**: Optimierungen einbauen
4. **Phase 4**: Checkout-Integration