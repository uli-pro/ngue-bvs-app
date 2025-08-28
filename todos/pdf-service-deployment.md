# PDF Service Deployment Guide

## Übersicht

Der PDFGeneratorService wurde erfolgreich implementiert und ist bereit für die Production-Deployment. Dieses Dokument beschreibt die Anforderungen und Deployment-Strategien.

## ✅ Implementation Status

### Implementierte Features:
- ✅ **PDFGeneratorService** - Vollständige Service-Klasse
- ✅ **Alle Zertifikattypen** - personal, group, gift, tax_receipt
- ✅ **Template Integration** - Kompatibel mit Phase 1 Templates  
- ✅ **Flask Integration** - Vollständig in app.py integriert
- ✅ **Error Handling** - Comprehensive exception hierarchy
- ✅ **Testing Framework** - Unit & Integration Tests
- ✅ **HTML Beispiele** - Alle 4 Zertifikattypen in `/docs`

### Test-Dateien erstellt:
```
docs/
├── example_personal_certificate.html    # Persönliches Zertifikat
├── example_group_certificate.html       # Gruppenzertifikat  
├── example_gift_certificate.html        # Geschenkzertifikat
└── example_tax_receipt.html            # Spendenbescheinigung
```

## 🔧 WeasyPrint System-Dependencies

### Lokale Entwicklung (macOS):
```bash
# Mit Homebrew installieren
brew install cairo pango gdk-pixbuf libffi gobject-introspection

# Umgebungsvariablen setzen
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

### Production Server (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libgirepository1.0-dev \
    shared-mime-info
```

### Production Server (CentOS/RHEL):
```bash
sudo yum install -y \
    cairo-devel \
    pango-devel \
    gdk-pixbuf2-devel \
    libffi-devel \
    gobject-introspection-devel
```

## 🐳 Docker Deployment (Empfohlen)

### Dockerfile für NGÜ App:
```dockerfile
FROM python:3.11-slim

# WeasyPrint Dependencies
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libgirepository1.0-dev \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App Code
COPY . .

# Certificate Storage Directory
RUN mkdir -p /app/certificates && \
    chmod 755 /app/certificates

# Expose Port
EXPOSE 5000

CMD ["python", "app.py"]
```

### docker-compose.yml:
```yaml
version: '3.8'

services:
  ngue-app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - CERTIFICATE_STORAGE_PATH=/app/certificates
    volumes:
      - certificate_storage:/app/certificates
      - ./static:/app/static
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    # ... DB configuration

volumes:
  certificate_storage:
```

## 📁 File Storage Configuration

### Verzeichnisstruktur:
```
certificates/
├── YYYY/                    # Jahr
│   └── MM/                  # Monat
│       └── session_ID/      # Session-gruppiert
│           ├── donation_001_personal_certificate_YYYYMMDD_HHMMSS.pdf
│           ├── donation_001_tax_receipt_YYYYMMDD_HHMMSS.pdf
│           └── ...
```

### Flask Konfiguration:
```python
# In app.py bereits konfiguriert:
app.config['CERTIFICATE_STORAGE_PATH'] = os.path.join(os.getcwd(), 'certificates')
app.config['PDF_TEMPLATE_PATH'] = 'templates/certificates'
```

### Für Production:
```python
# Production-optimierte Pfade
app.config['CERTIFICATE_STORAGE_PATH'] = '/var/www/ngue/certificates'
# oder Docker Volume:
app.config['CERTIFICATE_STORAGE_PATH'] = '/app/certificates'
```

## 🚀 Usage Examples

### Einzelnes Zertifikat generieren:
```python
from pdf_service import PDFGeneratorService

# Service ist bereits in app.py initialisiert
pdf_service = PDFGeneratorService(app)

# Personal Certificate
certificate = pdf_service.generate_certificate(
    donation_id=123,
    certificate_type='personal_certificate', 
    session_id='cart_abc123'
)

# Tax Receipt
tax_receipt = pdf_service.generate_tax_receipt(
    donation_id=123,
    session_id='cart_abc123'
)
```

### Batch-Generierung:
```python
# Mehrere Zertifikate einer Session
certificates = pdf_service.generate_certificate_batch(
    donation_ids=[101, 102, 103],
    session_id='cart_abc123'
)
```

## 🧪 Testing

### Tests ausführen:
```bash
# Unit Tests
pytest tests/test_pdf_service.py

# Mit Coverage
pytest --cov=pdf_service tests/test_pdf_service.py

# Integration Tests (erfordern WeasyPrint Dependencies)
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
pytest tests/test_pdf_service.py::TestPDFServiceIntegration
```

## 🔄 Alternative: ReportLab

Falls WeasyPrint-Dependencies problematisch sind:

### ReportLab als Fallback:
```python
# Bereits in requirements.txt: reportlab==4.0.7

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

def generate_pdf_with_reportlab(template_data, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Hintergrundbild
    c.drawImage('static/certificates/certificate-background.png', 
                0, 0, width=595, height=842)
    
    # Text hinzufügen
    c.setFont("Helvetica", 14)
    c.drawString(100, 700, f"Name: {template_data['name']}")
    
    c.save()
```

## 📊 Performance Considerations

### Optimierungen:
- **Template Caching**: Jinja2 Templates werden automatisch gecacht
- **CSS Compilation**: WeasyPrint kompiliert CSS einmal pro Instanz
- **Memory Management**: PDFs werden direkt in Dateien geschrieben
- **Batch Processing**: Effizienter für mehrere PDFs

### Monitoring:
```python
import time
import logging

# Performance Logging
start_time = time.time()
certificate = pdf_service.generate_certificate(donation_id, cert_type, session_id)
generation_time = time.time() - start_time

logging.info(f"PDF generated in {generation_time:.2f}s: {certificate.filename}")
```

## 🔒 Security

### Implementierte Sicherheitsmaßnahmen:
- ✅ **Path Traversal Protection** - Verhindert "../" Angriffe
- ✅ **Input Validation** - Parameter werden validiert
- ✅ **Database Integrity** - Nur completed donations werden verarbeitet
- ✅ **File Permissions** - PDFs werden mit 644 Permissions erstellt
- ✅ **Cleanup on Error** - Fehlgeschlagene PDFs werden gelöscht

## 🎯 Integration mit Checkout-Flow

### Checkout-Integration (Phase 4):
```python
# Nach erfolgreichem Stripe Payment:
@csrf.exempt
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    # ... Payment verification
    
    if payment_success:
        # Donation als completed markieren
        donation.mark_completed()
        
        # PDF generieren
        try:
            certificate = pdf_service.generate_certificate(
                donation.id,
                get_certificate_type(donation.donation_type),
                session.get('session_id')
            )
            
            if donation.wants_receipt:
                tax_receipt = pdf_service.generate_tax_receipt(
                    donation.id,
                    session.get('session_id')
                )
            
            # Email mit PDFs versenden (Phase 5)
            send_certificate_email(donation, certificate, tax_receipt)
            
        except PDFGenerationError as e:
            app.logger.error(f"PDF generation failed for donation {donation.id}: {e}")
            # Fallback: Email ohne PDF oder später retry
```

## 📋 Deployment Checklist

### Pre-Deployment:
- [ ] WeasyPrint Dependencies installiert
- [ ] Certificate Storage Directory erstellt mit korrekten Permissions
- [ ] Environment Variables konfiguriert
- [ ] Database Migration durchgeführt (Certificate Modell)

### Deployment:
- [ ] Docker Image mit Dependencies gebaut
- [ ] Volume Mounts für Certificate Storage konfiguriert  
- [ ] Reverse Proxy (nginx/traefik) für static files
- [ ] SSL Zertifikate für HTTPS

### Post-Deployment Testing:
- [ ] PDF Generation Test erfolgreich
- [ ] Template Rendering funktioniert
- [ ] File Storage Permissions korrekt
- [ ] Error Handling funktioniert

### Monitoring:
- [ ] Log-Level für PDF Service konfiguriert
- [ ] Disk Space Monitoring für Certificate Storage
- [ ] Performance Metrics für PDF Generation Time

---

**Status**: ✅ **Implementation Complete - Ready for Production**

Der PDF Service ist vollständig implementiert und produktionsbereit. Die HTML-Beispiele in `/docs` zeigen das finale Design aller vier Zertifikattypen.