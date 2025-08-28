# PDF Phase 4: Checkout-Integration

**Status:** TODO  
**Priorität:** Hoch  
**Abhängigkeiten:** Phase 2 (Service), Phase 3 (Database)  
**Geschätzte Zeit:** 4-5 Stunden

## Überblick

Diese Phase integriert die PDF-Generierung in den bestehenden Checkout-Flow, implementiert sichere Download-Routes und passt die checkout-erfolg.html Seite für echte PDF-Links an.

## Aufgaben-Checkliste

### 1. Checkout-Erfolg Route erweitern

- [ ] **Route analysieren**: Bestehende `/checkout-erfolg` Route finden
- [ ] **PDF-Generierung**: Nach successful payment PDFs erstellen
- [ ] **Session-Handling**: Session-ID für Pfad-Gruppierung verwenden
- [ ] **Error-Handling**: Graceful degradation bei PDF-Problemen

#### Bestehende Route finden und erweitern:
```python
# In app.py - bestehende checkout-erfolg Route finden und erweitern

from pdf_service import PDFGeneratorService

@app.route('/checkout-erfolg')
def checkout_success():
    """Checkout-Erfolg mit PDF-Generierung"""
    
    # Bestehende Logic beibehalten
    session_id = session.get('session_id')  # oder wie Session-ID aktuell verwaltet wird
    donation_ids = session.get('completed_donations', [])  # oder ähnlich
    
    if not donation_ids:
        flash('Keine abgeschlossenen Spenden gefunden.', 'warning')
        return redirect(url_for('index'))
    
    try:
        # PDFs für alle Donations dieser Session generieren
        pdf_service = PDFGeneratorService(current_app)
        generated_documents = pdf_service.generate_donation_documents_batch(
            donation_ids, 
            session_id or 'no_session'
        )
        
        # Template-Context mit echten Download-Links vorbereiten
        template_context = prepare_success_page_context(
            donation_ids, 
            generated_documents
        )
        
        # Erfolgreiche PDF-Generierung in Session markieren
        session['pdfs_generated'] = True
        
        return render_template('checkout-erfolg.html', **template_context)
        
    except PDFGenerationError as e:
        current_app.logger.error(f"PDF generation failed: {str(e)}")
        
        # Fallback: Seite ohne PDFs anzeigen
        template_context = prepare_success_page_context_fallback(donation_ids)
        template_context['pdf_error'] = True
        
        return render_template('checkout-erfolg.html', **template_context)

def prepare_success_page_context(donation_ids: List[int], 
                                generated_documents: Dict) -> Dict[str, Any]:
    """Bereitet Template-Context mit PDF-Links vor"""
    
    # Letzte Donation für Hauptanzeige
    latest_donation = Donation.query.get(donation_ids[-1]) if donation_ids else None
    
    # Download-Links sammeln
    certificate_links = []
    tax_receipt_links = []
    
    for cert in generated_documents.get('certificates', []):
        certificate_links.append({
            'donation_id': cert.donation_id,
            'download_url': cert.get_download_url(),
            'filename': cert.filename,
            'type': cert.certificate_type
        })
    
    for receipt in generated_documents.get('tax_receipts', []):
        tax_receipt_links.append({
            'donation_id': receipt.donation_id,
            'download_url': receipt.get_download_url(),
            'filename': receipt.filename
        })
    
    # User-Daten für Anzeige
    user_email = latest_donation.person.email if latest_donation else 'unbekannt@example.com'
    verse_reference = latest_donation.verse.reference if latest_donation else 'Jeremia 29,11'
    
    return {
        'user_email': user_email,
        'verse_reference': verse_reference,
        'certificate_links': certificate_links,
        'tax_receipt_links': tax_receipt_links,
        'total_donations': len(donation_ids),
        'pdfs_available': True,
        # Statistiken (bestehende Logic beibehalten)
        'total_sponsored': Verse.query.filter_by(is_sponsored=True).count(),
        'total_amount': db.session.query(func.sum(Donation.amount)).filter_by(payment_status='completed').scalar() or 0,
        'remaining_verses': Verse.query.filter_by(is_sponsored=False).count()
    }

def prepare_success_page_context_fallback(donation_ids: List[int]) -> Dict[str, Any]:
    """Fallback-Context wenn PDF-Generierung fehlschlägt"""
    
    latest_donation = Donation.query.get(donation_ids[-1]) if donation_ids else None
    
    return {
        'user_email': latest_donation.person.email if latest_donation else 'unbekannt@example.com',
        'verse_reference': latest_donation.verse.reference if latest_donation else 'Jeremia 29,11',
        'certificate_links': [],
        'tax_receipt_links': [],
        'total_donations': len(donation_ids),
        'pdfs_available': False,
        'total_sponsored': Verse.query.filter_by(is_sponsored=True).count(),
        'total_amount': db.session.query(func.sum(Donation.amount)).filter_by(payment_status='completed').scalar() or 0,
        'remaining_verses': Verse.query.filter_by(is_sponsored=False).count()
    }
```

### 2. Download-Routes implementieren

- [ ] **Route**: `/download/certificate/<int:certificate_id>`
- [ ] **Route**: `/download/tax-receipt/<int:certificate_id>`
- [ ] **Sicherheitsprüfungen**: Session-basierte Zugriffskontrolle
- [ ] **File-Serving**: Sichere PDF-Auslieferung
- [ ] **Rate-Limiting**: Schutz vor Missbrauch

#### Download-Routes implementieren:
```python
from flask import send_file, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate-Limiter konfigurieren (falls nicht bereits vorhanden)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

@app.route('/download/certificate/<int:certificate_id>')
@limiter.limit("10 per minute")
def download_certificate(certificate_id: int):
    """Sicherer PDF-Download für Zertifikate"""
    
    # Certificate laden
    certificate = Certificate.query.get_or_404(certificate_id)
    
    # Sicherheitsprüfungen
    if not _can_access_certificate(certificate):
        abort(403)
    
    # Datei existiert?
    if not certificate.exists_on_disk:
        current_app.logger.error(f"Certificate file missing: {certificate.file_path}")
        abort(404)
    
    try:
        # PDF-Datei senden
        return send_file(
            certificate.file_path,
            as_attachment=True,
            download_name=certificate.filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        current_app.logger.error(f"File serving failed: {str(e)}")
        abort(500)

def _can_access_certificate(certificate: Certificate) -> bool:
    """Prüft ob aktueller User auf Certificate zugreifen darf"""
    
    # Session-basierte Zugriffskontrolle
    session_donations = session.get('completed_donations', [])
    
    # User darf auf Certificate zugreifen wenn:
    # 1. Certificate gehört zu einer Donation aus aktueller Session
    if certificate.donation_id in session_donations:
        return True
    
    # 2. PDFs wurden in aktueller Session generiert
    if session.get('pdfs_generated') and certificate.donation_id in session_donations:
        return True
    
    # 3. Alternative: Time-based access (PDFs sind 24h nach Generierung verfügbar)
    if certificate.generated_at:
        hours_since_generation = (datetime.utcnow() - certificate.generated_at).total_seconds() / 3600
        if hours_since_generation <= 24:
            return True
    
    return False

@app.route('/download/tax-receipt/<int:certificate_id>')
@limiter.limit("10 per minute")
def download_tax_receipt(certificate_id: int):
    """Download für Spendenbescheinigungen"""
    
    certificate = Certificate.query.get_or_404(certificate_id)
    
    # Nur Tax-Receipts erlauben
    if certificate.certificate_type != 'tax_receipt':
        abort(404)
    
    # Gleiche Sicherheitsprüfungen
    if not _can_access_certificate(certificate):
        abort(403)
    
    if not certificate.exists_on_disk:
        abort(404)
    
    try:
        return send_file(
            certificate.file_path,
            as_attachment=True,
            download_name=certificate.filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        current_app.logger.error(f"Tax receipt serving failed: {str(e)}")
        abort(500)
```

### 3. Template checkout-erfolg.html anpassen

- [ ] **HTML erweitern**: Dynamische PDF-Links statt statische Demo-Links
- [ ] **Conditional Rendering**: Unterschiedliche Anzeige je nach PDF-Status
- [ ] **Error-Messages**: Benutzerfreundliche Fehlermeldungen
- [ ] **Download-Tracking**: Optional für Analytics

#### Template-Anpassungen:
```html
<!-- In templates/checkout-erfolg.html - Documents Section ersetzen -->

<!-- Documents Section -->
<section class="section-padding">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="card border-success">
                    <div class="card-header bg-secondary text-white text-center">
                        <h3 class="mb-0">Ihre Dokumente</h3>
                    </div>
                    <div class="card-body p-4">
                        {% if pdfs_available %}
                            <p class="text-center lead mb-4">Ihre Dokumente stehen zum Download bereit:</p>
                            
                            <div class="row g-3">
                                <!-- Zertifikate -->
                                {% if certificate_links %}
                                    <div class="col-md-6">
                                        <div class="card h-100">
                                            <div class="card-body text-center">
                                                <i class="fas fa-certificate fa-3x text-primary mb-3"></i>
                                                <h5>
                                                    {% if certificate_links|length == 1 %}
                                                        Persönliches Zertifikat
                                                    {% else %}
                                                        Zertifikate ({{ certificate_links|length }})
                                                    {% endif %}
                                                </h5>
                                                <p class="text-muted">Ihre Sponsoring-Zertifikat{{ 'e' if certificate_links|length > 1 else '' }}</p>
                                                
                                                {% for cert_link in certificate_links %}
                                                    <div class="mb-2">
                                                        <a href="{{ cert_link.download_url }}" 
                                                           class="btn btn-primary btn-sm" 
                                                           target="_blank"
                                                           onclick="trackDownload('certificate', {{ cert_link.donation_id }})">
                                                            <i class="fas fa-download me-2"></i>
                                                            {% if certificate_links|length == 1 %}
                                                                Zertifikat herunterladen
                                                            {% else %}
                                                                Zertifikat {{ loop.index }}
                                                            {% endif %}
                                                        </a>
                                                    </div>
                                                {% endfor %}
                                            </div>
                                        </div>
                                    </div>
                                {% endif %}
                                
                                <!-- Spendenbescheinigungen -->
                                {% if tax_receipt_links %}
                                    <div class="col-md-6">
                                        <div class="card h-100">
                                            <div class="card-body text-center">
                                                <i class="fas fa-file-invoice fa-3x text-secondary mb-3"></i>
                                                <h5>
                                                    {% if tax_receipt_links|length == 1 %}
                                                        Spendenbescheinigung
                                                    {% else %}
                                                        Spendenbescheinigungen ({{ tax_receipt_links|length }})
                                                    {% endif %}
                                                </h5>
                                                <p class="text-muted">Für Ihre Steuererklärung</p>
                                                
                                                {% for receipt_link in tax_receipt_links %}
                                                    <div class="mb-2">
                                                        <a href="{{ receipt_link.download_url }}" 
                                                           class="btn btn-secondary btn-sm" 
                                                           target="_blank"
                                                           onclick="trackDownload('tax_receipt', {{ receipt_link.donation_id }})">
                                                            <i class="fas fa-download me-2"></i>
                                                            {% if tax_receipt_links|length == 1 %}
                                                                Bescheinigung herunterladen
                                                            {% else %}
                                                                Bescheinigung {{ loop.index }}
                                                            {% endif %}
                                                        </a>
                                                    </div>
                                                {% endfor %}
                                            </div>
                                        </div>
                                    </div>
                                {% endif %}
                                
                                <!-- Fallback wenn keine PDFs verfügbar -->
                                {% if not certificate_links and not tax_receipt_links %}
                                    <div class="col-12">
                                        <div class="alert alert-warning text-center">
                                            <i class="fas fa-exclamation-triangle me-2"></i>
                                            PDF-Dokumente werden gerade erstellt. Sie erhalten sie per E-Mail.
                                        </div>
                                    </div>
                                {% endif %}
                            </div>
                            
                            <div class="alert alert-info mt-4 text-center">
                                <i class="fas fa-envelope me-2"></i>
                                Alle Dokumente wurden auch an Ihre E-Mail-Adresse 
                                <strong>{{ user_email }}</strong> versendet.
                            </div>
                            
                        {% else %}
                            <!-- Fallback bei PDF-Generierung-Fehlern -->
                            <div class="alert alert-warning text-center">
                                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                                <h5>Dokumente werden vorbereitet</h5>
                                <p>Ihre Zertifikate und Spendenbescheinigungen werden gerade erstellt 
                                   und an <strong>{{ user_email }}</strong> versendet.</p>
                                <p class="mb-0"><small>Falls Sie die Dokumente nicht innerhalb von 
                                   30 Minuten erhalten, wenden Sie sich bitte an unseren Support.</small></p>
                            </div>
                            
                            {% if pdf_error %}
                                <div class="alert alert-danger text-center mt-3">
                                    <i class="fas fa-exclamation-circle me-2"></i>
                                    <small>Technischer Hinweis: Bei der Dokumentenerstellung ist ein Problem aufgetreten. 
                                    Der Support wurde automatisch benachrichtigt.</small>
                                </div>
                            {% endif %}
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- JavaScript für Download-Tracking -->
<script>
function trackDownload(documentType, donationId) {
    // Optional: Analytics-Tracking für Downloads
    if (typeof gtag !== 'undefined') {
        gtag('event', 'download', {
            'event_category': 'PDF',
            'event_label': documentType,
            'value': donationId
        });
    }
    
    // Optional: Server-seitiges Tracking
    fetch('/api/track-download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify({
            document_type: documentType,
            donation_id: donationId
        })
    }).catch(err => console.log('Tracking failed:', err));
}
</script>
```

### 4. Session-Management erweitern

- [ ] **Session-Variablen**: Für PDF-Zugriffskontrolle
- [ ] **Cleanup-Logic**: Sessions nach erfolgreicher PDF-Generierung bereinigen
- [ ] **Timeout-Handling**: Session-Expiry für Downloads
- [ ] **Multiple-Sessions**: Handling wenn User mehrere Sessions hat

#### Session-Management erweitern:
```python
# In app.py oder session_utils.py

def setup_pdf_session(donation_ids: List[int], session_id: str):
    """Bereitet Session für PDF-Downloads vor"""
    session['completed_donations'] = donation_ids
    session['session_id'] = session_id
    session['pdf_access_granted_at'] = datetime.utcnow().isoformat()
    session['pdf_access_expires_at'] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    session.permanent = True  # Session überdauert Browser-Schließung

def cleanup_pdf_session():
    """Bereinigt PDF-spezifische Session-Daten"""
    keys_to_remove = [
        'completed_donations',
        'pdfs_generated', 
        'pdf_access_granted_at',
        'pdf_access_expires_at'
    ]
    
    for key in keys_to_remove:
        session.pop(key, None)

def is_pdf_access_valid() -> bool:
    """Prüft ob PDF-Zugriff noch gültig ist"""
    if 'pdf_access_expires_at' not in session:
        return False
    
    try:
        expires_at = datetime.fromisoformat(session['pdf_access_expires_at'])
        return datetime.utcnow() < expires_at
    except (ValueError, TypeError):
        return False

@app.before_request
def check_pdf_session_expiry():
    """Bereinigt abgelaufene PDF-Sessions automatisch"""
    if 'pdf_access_expires_at' in session and not is_pdf_access_valid():
        cleanup_pdf_session()
```

### 5. E-Mail-Integration vorbereiten

- [ ] **E-Mail-Service**: PDF-Anhänge für automatischen Versand vorbereiten
- [ ] **Template-Erweiterung**: E-Mail-Templates für PDF-Versand
- [ ] **Async-Queue**: Für verzögerten E-Mail-Versand nach PDF-Generierung
- [ ] **Fallback-Logic**: Was passiert wenn E-Mail-Versand fehlschlägt

#### E-Mail-Integration Grundlagen:
```python
# In pdf_service.py erweitern

from flask_mail import Mail, Message

class PDFGeneratorService:
    
    def __init__(self, app: Optional[Flask] = None, mail: Optional[Mail] = None):
        self.app = app
        self.mail = mail
        if app:
            self.init_app(app)
    
    def generate_certificate_with_email(self, donation_id: int, certificate_type: str,
                                       session_id: Optional[str] = None,
                                       send_email: bool = True) -> Certificate:
        """Generiert Certificate und sendet optional E-Mail"""
        
        certificate = self.generate_certificate_atomic(donation_id, certificate_type, session_id)
        
        if send_email and self.mail:
            try:
                self._send_certificate_email(certificate)
            except Exception as e:
                # E-Mail-Fehler nicht kritisch - PDF ist bereits erstellt
                current_app.logger.warning(f"Email sending failed: {str(e)}")
        
        return certificate
    
    def _send_certificate_email(self, certificate: Certificate):
        """Sendet Certificate per E-Mail"""
        donation = certificate.donation
        person_email = donation.person.email
        
        # E-Mail-Template rendern
        email_html = render_template(
            'emails/certificate_ready.html',
            donation=donation,
            certificate=certificate
        )
        
        # E-Mail erstellen
        msg = Message(
            subject="Ihr NGÜ-Sponsoring Zertifikat ist bereit",
            recipients=[person_email],
            html=email_html
        )
        
        # PDF als Anhang
        if certificate.exists_on_disk:
            with open(certificate.file_path, 'rb') as pdf_file:
                msg.attach(
                    certificate.filename,
                    'application/pdf',
                    pdf_file.read()
                )
        
        # E-Mail senden (async für bessere Performance)
        self.mail.send(msg)
```

### 6. Error-Handling und Logging

- [ ] **User-friendly Errors**: Verständliche Fehlermeldungen
- [ ] **Admin-Notifications**: Bei kritischen PDF-Fehlern
- [ ] **Retry-Logic**: Automatische Wiederholung bei temporären Fehlern
- [ ] **Graceful Degradation**: Fallback-Verhalten definieren

#### Erweiterte Error-Handling:
```python
class PDFIntegrationError(Exception):
    """PDF-Integration spezifische Fehler"""
    pass

@app.errorhandler(PDFGenerationError)
def handle_pdf_error(error):
    """Global PDF-Error Handler"""
    current_app.logger.error(f"PDF generation error: {str(error)}")
    
    # Admin-Benachrichtigung bei kritischen Fehlern
    if isinstance(error, FileSystemError):
        send_admin_notification("PDF FileSystem Error", str(error))
    
    # User-freundliche Fehlerseite
    return render_template('errors/pdf_error.html', error=error), 500

def send_admin_notification(subject: str, message: str):
    """Sendet Admin-Benachrichtigung bei kritischen Fehlern"""
    if current_app.config.get('ADMIN_EMAIL'):
        try:
            msg = Message(
                subject=f"NGÜ-App Alert: {subject}",
                recipients=[current_app.config['ADMIN_EMAIL']],
                body=message
            )
            mail.send(msg)
        except:
            pass  # Nicht kritisch wenn Admin-Mail fehlschlägt

@app.route('/api/retry-pdf-generation', methods=['POST'])
@limiter.limit("5 per minute")
def retry_pdf_generation():
    """API-Endpoint für manuellen PDF-Retry"""
    
    donation_id = request.json.get('donation_id')
    certificate_type = request.json.get('certificate_type')
    
    if not donation_id or not certificate_type:
        return jsonify({'error': 'Missing parameters'}), 400
    
    # Berechtigung prüfen
    if donation_id not in session.get('completed_donations', []):
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        pdf_service = PDFGeneratorService(current_app)
        certificate = pdf_service.generate_certificate_atomic(
            donation_id, certificate_type
        )
        
        return jsonify({
            'success': True,
            'download_url': certificate.get_download_url()
        })
        
    except PDFGenerationError as e:
        return jsonify({
            'error': 'PDF generation failed',
            'details': str(e)
        }), 500
```

## Testing

### Integration-Tests

- [ ] **End-to-End**: Kompletter Checkout-Flow mit PDFs
- [ ] **Download-Tests**: Sicherheit und Functionality der Download-Routes
- [ ] **Session-Tests**: Session-basierte Zugriffskontrolle
- [ ] **Error-Scenarios**: Verschiedene Fehlerszenarien testen

#### Test-Beispiele:
```python
# tests/test_checkout_integration.py

def test_checkout_success_with_pdf_generation(client, completed_donation):
    """Test kompletter Checkout-Flow mit PDF-Generierung"""
    
    with client.session_transaction() as sess:
        sess['completed_donations'] = [completed_donation.id]
        sess['session_id'] = 'test_session_123'
    
    response = client.get('/checkout-erfolg')
    
    assert response.status_code == 200
    assert b'Zertifikat herunterladen' in response.data
    assert b'Bescheinigung herunterladen' in response.data

def test_certificate_download_access_control(client, test_certificate):
    """Test dass nur berechtigte Users PDFs downloaden können"""
    
    # Ohne Session-Berechtigung
    response = client.get(f'/download/certificate/{test_certificate.id}')
    assert response.status_code == 403
    
    # Mit Session-Berechtigung
    with client.session_transaction() as sess:
        sess['completed_donations'] = [test_certificate.donation_id]
    
    response = client.get(f'/download/certificate/{test_certificate.id}')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'

def test_pdf_error_fallback(client, monkeypatch):
    """Test Fallback-Verhalten bei PDF-Generierung-Fehlern"""
    
    # PDF-Service mocken um Fehler zu simulieren
    def mock_generate_batch(*args, **kwargs):
        raise PDFGenerationError("Test error")
    
    monkeypatch.setattr(
        'pdf_service.PDFGeneratorService.generate_donation_documents_batch',
        mock_generate_batch
    )
    
    with client.session_transaction() as sess:
        sess['completed_donations'] = [1]
    
    response = client.get('/checkout-erfolg')
    
    assert response.status_code == 200
    assert b'werden gerade erstellt' in response.data
    assert b'pdf_error' not in response.data  # Keine technischen Details für User
```

## Performance-Überlegungen

### Optimierungen:
- [ ] **Lazy-Loading**: PDFs nur bei Bedarf generieren
- [ ] **Caching**: Template-Caching für bessere Performance
- [ ] **Batch-Optimierung**: Intelligente Gruppierung von PDF-Generierungen
- [ ] **CDN-Integration**: Für große PDF-Downloads

### Monitoring:
- [ ] **Download-Analytics**: Tracking von PDF-Downloads
- [ ] **Error-Rates**: Monitoring von PDF-Fehlern
- [ ] **Performance-Metrics**: Generation-Zeit und Download-Zeit

## Sicherheitsüberlegungen

### Wichtige Aspekte:
- [ ] **Access-Control**: Nur berechtigte Downloads
- [ ] **Rate-Limiting**: Schutz vor Missbrauch
- [ ] **File-Path-Security**: Keine Directory-Traversal Angriffe
- [ ] **Session-Security**: Sichere Session-Verwaltung für PDF-Zugriff

### Security-Tests:
```python
def test_directory_traversal_protection(client):
    """Test Schutz vor Directory-Traversal Angriffen"""
    
    # Malicious certificate mit gefährlichem Pfad
    malicious_cert = Certificate(
        donation_id=1,
        certificate_type='personal_certificate',
        filename='test.pdf',
        file_path='../../../etc/passwd'
    )
    
    assert not malicious_cert.validate_file_path()

def test_download_rate_limiting(client, test_certificate):
    """Test Rate-Limiting für Downloads"""
    
    with client.session_transaction() as sess:
        sess['completed_donations'] = [test_certificate.donation_id]
    
    # Erste 10 Requests sollten OK sein
    for _ in range(10):
        response = client.get(f'/download/certificate/{test_certificate.id}')
        assert response.status_code in [200, 404]  # 404 wenn Datei nicht existiert
    
    # 11. Request sollte Rate-Limited sein
    response = client.get(f'/download/certificate/{test_certificate.id}')
    assert response.status_code == 429
```

## Nächste Schritte

Nach Abschluss dieser Phase:
1. **Phase 5**: Testing und Optimierung
2. **E-Mail-Integration**: Vollständige E-Mail-Automatisierung
3. **Admin-Dashboard**: Für PDF-Monitoring und -Management
4. **Production-Deployment**: Live-Gang vorbereiten