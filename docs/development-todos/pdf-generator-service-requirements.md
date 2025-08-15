# PDF-Generator-Service Requirements

**Status:** TODO - Noch zu implementieren  
**Priorität:** Hoch  
**Datum:** 15. August 2025

## Überblick

Der PDF-Generator-Service ist verantwortlich für die vollständige Erstellung, Speicherung und Verwaltung aller PDF-Zertifikate und Spendenbescheinigungen. Er koordiniert Pfad-Generierung, PDF-Erstellung und Datenbank-Updates atomisch.

## Hauptverantwortlichkeiten

### 1. Pfad- und Dateinamen-Generierung
- **Session-basierte Ordnerstruktur** erstellen
- **Eindeutige Dateinamen** generieren 
- **Naming-Konflikte** vermeiden
- **Ordner automatisch erstellen** falls nicht vorhanden

### 2. PDF-Template-Management
- **4 verschiedene Zertifikat-Typen** unterstützen:
  - `personal_certificate` - Persönliches Zertifikat
  - `group_certificate` - Gruppen-Zertifikat
  - `gift_certificate` - Geschenk-Zertifikat
  - `tax_receipt` - Spendenbescheinigung
- **Template-Engine** (Jinja2, ReportLab, WeasyPrint?)
- **NGÜ-Branding** konsistent anwenden

### 3. Datenbank-Integration
- **Certificate-Records erstellen** nach erfolgreicher PDF-Generierung
- **Atomische Operationen** (alles oder nichts)
- **Fehlerbehandlung** mit sauberem Rollback

### 4. Dateisystem-Management
- **Sichere Pfad-Erstellung** (keine Directory Traversal)
- **Ordnerstruktur-Konsistenz**
- **Datei-Berechtigungen** korrekt setzen

## Technische Spezifikation

### API-Interface
```python
class PDFGeneratorService:
    def generate_certificate(self, donation_id: int, certificate_type: str, session_id: str = None) -> Certificate:
        """
        Generiert PDF-Zertifikat und erstellt Certificate-Record
        
        Args:
            donation_id: ID der Spende
            certificate_type: personal_certificate, group_certificate, gift_certificate, tax_receipt
            session_id: Shopping Cart Session ID für Pfad-Gruppierung
            
        Returns:
            Certificate: Erstellter Certificate-Record mit file_path und filename
            
        Raises:
            PDFGenerationError: Bei Fehlern in der PDF-Erstellung
            FileSystemError: Bei Dateisystem-Problemen
            ValidationError: Bei ungültigen Parametern
        """
    
    def generate_certificate_batch(self, donation_ids: List[int], session_id: str) -> List[Certificate]:
        """Batch-Generierung für mehrere Zertifikate einer Session"""
    
    def regenerate_certificate(self, certificate_id: int) -> Certificate:
        """Zertifikat neu generieren (bei Template-Änderungen)"""
```

### Pfad-Struktur
```
certificates/
├── 2025/
│   └── 01/                                    # Jahr/Monat
│       ├── session_abc123def456/              # Shopping Cart Session ID
│       │   ├── donation_001_personal_cert_20250115_143022.pdf
│       │   ├── donation_001_tax_receipt_20250115_143022.pdf
│       │   ├── donation_002_group_cert_20250115_143025.pdf
│       │   └── donation_002_tax_receipt_20250115_143025.pdf
│       └── session_xyz789ghi012/
│           ├── donation_003_gift_cert_20250115_150112.pdf
│           └── donation_003_tax_receipt_20250115_150112.pdf
```

### Dateinamen-Konvention
```
{donation_id}_{certificate_type}_{YYYYMMDD}_{HHMMSS}.pdf

Beispiele:
- donation_001_personal_cert_20250115_143022.pdf
- donation_002_group_cert_20250115_143025.pdf
- donation_003_gift_cert_20250115_150112.pdf
- donation_001_tax_receipt_20250115_143022.pdf
```

## Implementierungs-Details

### 1. Pfad-Generator
```python
def generate_certificate_paths(donation, certificate_type, session_id=None):
    """
    Generiert filename und file_path für Zertifikat
    
    Returns:
        tuple: (filename, absolute_file_path)
    """
    # Basis-Verzeichnis
    base_dir = app.config['CERTIFICATE_STORAGE_PATH']
    
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
    
    return filename, file_path
```

### 2. Template-System
```python
def render_certificate_template(donation, certificate_type):
    """
    Rendert PDF-Template basierend auf Donation und Type
    
    Template-Auswahl:
    - personal_certificate → templates/certificates/personal.html
    - group_certificate → templates/certificates/group.html  
    - gift_certificate → templates/certificates/gift.html
    - tax_receipt → templates/certificates/tax_receipt.html
    """
```

### 3. Fehlerbehandlung
```python
class PDFGenerationError(Exception):
    """PDF-Generierung fehlgeschlagen"""
    
class FileSystemError(Exception):
    """Dateisystem-Operation fehlgeschlagen"""
    
class TemplateNotFoundError(PDFGenerationError):
    """PDF-Template nicht gefunden"""
```

## Konfiguration

### Flask App Config
```python
# app.py oder config.py
CERTIFICATE_STORAGE_PATH = '/path/to/certificates'
PDF_TEMPLATE_PATH = 'templates/certificates'
PDF_ENGINE = 'weasyprint'  # oder 'reportlab'
```

### Template-Verzeichnis-Struktur
```
templates/certificates/
├── base_certificate.html          # Basis-Template mit NGÜ-Branding
├── personal.html                  # Erbt von base_certificate.html
├── group.html
├── gift.html
├── tax_receipt.html
└── assets/
    ├── ngu_logo.png
    ├── certificate_bg.png
    └── certificate.css
```

## Integration mit Certificate-Model

### Vereinfachtes Certificate-Model
```python
class Certificate(db.Model):
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    certificate_type = db.Column(db.String(30), nullable=False)  # Erweitert für 4 Typen
    filename = db.Column(db.String(255), nullable=False)         # Nur Dateiname
    file_path = db.Column(db.String(500), nullable=False)        # Vollständiger Pfad
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    
    @property
    def exists_on_disk(self):
        """Prüft ob PDF-Datei tatsächlich existiert"""
        return os.path.exists(self.file_path)
    
    def delete_file(self):
        """Löscht PDF-Datei vom Dateisystem"""
        if self.exists_on_disk:
            os.remove(self.file_path)
```

## Testing-Anforderungen

### Unit Tests
- Pfad-Generierung für verschiedene Szenarien
- Template-Rendering für alle 4 Typen
- Fehlerbehandlung (fehlende Templates, Dateisystem-Probleme)
- Batch-Generierung

### Integration Tests
- End-to-End PDF-Generierung mit echten Donations
- Dateisystem-Operationen
- Datenbank-Transaktionen

### Test-Daten
- Mock-Donations für alle donation_types
- Test-Templates
- Temporäres Dateisystem für Tests

## Dependencies

### Python-Packages
```
# requirements.txt additions
WeasyPrint>=60.0  # oder ReportLab>=4.0
Pillow>=10.0      # für Bildverarbeitung
Jinja2>=3.1       # Template-Engine (schon durch Flask)
```

### System-Dependencies (für WeasyPrint)
```bash
# Ubuntu/Debian
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

# macOS
brew install weasyprint
```

## Sicherheitsüberlegungen

### Dateisystem-Sicherheit
- **Path Traversal Prevention**: Sichere Pfad-Validierung
- **Datei-Berechtigungen**: Nur App-User kann lesen/schreiben
- **Disk Space Monitoring**: Überwachung des verfügbaren Speicherplatzes

### Template-Sicherheit
- **Input Sanitization**: Alle Donation-Daten vor Template-Rendering escapen
- **Template Sandboxing**: Keine gefährlichen Template-Funktionen erlauben

## Performance-Überlegungen

### Optimierungen
- **Async PDF-Generierung**: Bei Batch-Operationen
- **Template-Caching**: Kompilierte Templates cachen
- **Image-Optimierung**: NGÜ-Logo/Assets optimiert einbinden

### Monitoring
- **Generierungs-Zeit**: Tracking der PDF-Erstellungszeit
- **Error-Rate**: Monitoring fehlgeschlagener Generierungen
- **Disk Usage**: Überwachung des Certificate-Speicherverbrauchs

## Nächste Schritte

1. **Library-Evaluation**: WeasyPrint vs. ReportLab entscheiden
2. **Template-Design**: Erste PDF-Templates erstellen
3. **Service-Implementation**: PDFGeneratorService programmieren
4. **Certificate-Model**: Vereinfachung implementieren
5. **Testing**: Umfassende Test-Suite schreiben

---

**Priorität für MVP:** Hoch - Benötigt für vollständigen Donation-Flow
**Abhängigkeiten:** Certificate-Model, Donation-Model, Flask-App-Struktur
**Geschätzte Implementierungszeit:** 2-3 Tage