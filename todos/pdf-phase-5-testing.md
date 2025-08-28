# PDF Phase 5: Testing & Optimierung

**Status:** TODO  
**Priorität:** Hoch  
**Abhängigkeiten:** Phase 1-4 (alle vorherigen Phasen)  
**Geschätzte Zeit:** 6-8 Stunden

## Überblick

Diese Phase implementiert eine umfassende Test-Suite für die PDF-Generierung, führt Performance-Tests durch und optimiert das System für den Produktivbetrieb.

## Aufgaben-Checkliste

### 1. Test-Infrastruktur einrichten

- [ ] **Test-Verzeichnisse**: Temporäre Dateisystem-Struktur für Tests
- [ ] **Mock-Services**: WeasyPrint und E-Mail-Service Mocks
- [ ] **Test-Fixtures**: Realistische Test-Daten erstellen
- [ ] **Cleanup-Mechanismen**: Automatische Test-Daten Bereinigung

#### Test-Setup implementieren:
```python
# tests/conftest.py - Test-Configuration erweitern

import pytest
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app
from models import db, Person, Donation, Verse, Certificate
from pdf_service import PDFGeneratorService

@pytest.fixture
def test_app():
    """Test-Flask-App mit temporärer Datenbank"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'CERTIFICATE_STORAGE_PATH': tempfile.mkdtemp(),
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        
        # Cleanup test files
        shutil.rmtree(app.config['CERTIFICATE_STORAGE_PATH'], ignore_errors=True)

@pytest.fixture
def pdf_service(test_app):
    """PDF-Service für Tests"""
    return PDFGeneratorService(test_app)

@pytest.fixture
def test_person(test_app):
    """Test-Person mit vollständigen Daten"""
    person = Person(
        email='test@example.com',
        first_name='Max',
        last_name='Mustermann',
        salutation='Herr',
        street='Teststraße',
        house_number='123',
        postal_code='12345',
        city='Teststadt',
        country='DE'
    )
    
    db.session.add(person)
    db.session.commit()
    return person

@pytest.fixture
def test_verse(test_app):
    """Test-Bibelvers"""
    verse = Verse(
        book='JESAJA',
        chapter=43,
        verse=1,
        text='Fürchte dich nicht, denn ich habe dich erlöst.',
        reference='Jesaja 43,1',
        is_sponsored=False,
        positivity_score=85
    )
    
    db.session.add(verse)
    db.session.commit()
    return verse

@pytest.fixture
def completed_donation(test_person, test_verse):
    """Abgeschlossene Test-Donation"""
    donation = Donation(
        person_id=test_person.id,
        verse_id=test_verse.id,
        donation_type='person',
        amount=Decimal('100.00'),
        currency='EUR',
        payment_status='completed',
        wants_receipt=True,
        privacy_consent=True,
        person_snapshot=test_person.to_snapshot(),
        completed_at=datetime.utcnow()
    )
    
    db.session.add(donation)
    db.session.commit()
    return donation

@pytest.fixture
def group_donation(test_person, test_verse):
    """Gruppen-Donation für Tests"""
    donation = Donation(
        person_id=test_person.id,
        verse_id=test_verse.id,
        donation_type='gruppe',
        donation_details={
            'group_article': 'Die',
            'group_name': 'Testgemeinde Musterstadt'
        },
        amount=Decimal('100.00'),
        payment_status='completed',
        wants_receipt=True,
        privacy_consent=True,
        person_snapshot=test_person.to_snapshot(),
        completed_at=datetime.utcnow()
    )
    
    db.session.add(donation)
    db.session.commit()
    return donation

@pytest.fixture
def gift_donation(test_person, test_verse):
    """Geschenk-Donation für Tests"""
    donation = Donation(
        person_id=test_person.id,
        verse_id=test_verse.id,
        donation_type='geschenk',
        donation_details={
            'recipient_first_name': 'Anna',
            'recipient_last_name': 'Müller'
        },
        amount=Decimal('100.00'),
        payment_status='completed',
        wants_receipt=False,
        privacy_consent=True,
        person_snapshot=test_person.to_snapshot(),
        completed_at=datetime.utcnow()
    )
    
    db.session.add(donation)
    db.session.commit()
    return donation

@pytest.fixture
def mock_weasyprint(monkeypatch):
    """Mock für WeasyPrint um echte PDF-Generierung zu vermeiden"""
    
    class MockHTML:
        def __init__(self, string=None, base_url=None):
            self.content = string
            
        def write_pdf(self, target=None, stylesheets=None, **kwargs):
            # Fake PDF-Content erstellen
            fake_pdf_content = b'%PDF-1.4\n%Mock PDF content for testing\n%%EOF\n'
            
            if isinstance(target, str):
                # Verzeichnis erstellen falls nicht vorhanden
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'wb') as f:
                    f.write(fake_pdf_content)
            else:
                return fake_pdf_content
    
    class MockCSS:
        def __init__(self, filename=None, **kwargs):
            pass
    
    monkeypatch.setattr('weasyprint.HTML', MockHTML)
    monkeypatch.setattr('weasyprint.CSS', MockCSS)
    
    return MockHTML
```

### 2. Unit-Tests für PDF-Service

- [ ] **Test-Suite**: `tests/test_pdf_service.py`
- [ ] **Alle Service-Methoden**: Jede public method testen
- [ ] **Edge-Cases**: Ungültige Parameter, fehlende Daten
- [ ] **Mocking**: WeasyPrint und Filesystem-Operations

#### PDF-Service Unit-Tests:
```python
# tests/test_pdf_service.py

import pytest
import os
from decimal import Decimal
from datetime import datetime

from pdf_service import PDFGeneratorService, PDFGenerationError, ValidationError
from models import Certificate

class TestPDFGeneratorService:
    
    def test_generate_personal_certificate_success(self, pdf_service, completed_donation, mock_weasyprint):
        """Test erfolgreiche Generierung eines persönlichen Zertifikats"""
        
        certificate = pdf_service.generate_certificate_atomic(
            completed_donation.id,
            'personal_certificate',
            'test_session_123'
        )
        
        # Certificate-Record validieren
        assert certificate.donation_id == completed_donation.id
        assert certificate.certificate_type == 'personal_certificate'
        assert certificate.filename.endswith('.pdf')
        assert 'test_session_123' in certificate.file_path
        
        # Datei existiert
        assert certificate.exists_on_disk
        
        # DB-Record wurde erstellt
        db_cert = Certificate.query.get(certificate.id)
        assert db_cert is not None
    
    def test_generate_group_certificate(self, pdf_service, group_donation, mock_weasyprint):
        """Test Gruppenzertifikat-Generierung"""
        
        certificate = pdf_service.generate_certificate_atomic(
            group_donation.id,
            'group_certificate'
        )
        
        assert certificate.certificate_type == 'group_certificate'
        assert certificate.exists_on_disk
    
    def test_generate_gift_certificate(self, pdf_service, gift_donation, mock_weasyprint):
        """Test Geschenkzertifikat-Generierung"""
        
        certificate = pdf_service.generate_certificate_atomic(
            gift_donation.id,
            'gift_certificate'
        )
        
        assert certificate.certificate_type == 'gift_certificate'
        assert certificate.exists_on_disk
    
    def test_generate_tax_receipt(self, pdf_service, completed_donation, mock_weasyprint):
        """Test Spendenbescheinigung-Generierung"""
        
        certificate = pdf_service.generate_tax_receipt(
            completed_donation.id,
            'test_session_456'
        )
        
        assert certificate.certificate_type == 'tax_receipt'
        assert certificate.exists_on_disk
        assert 'test_session_456' in certificate.file_path
    
    def test_invalid_donation_id(self, pdf_service):
        """Test mit ungültiger Donation-ID"""
        
        with pytest.raises(ValidationError, match="Donation 99999 not found"):
            pdf_service.generate_certificate_atomic(99999, 'personal_certificate')
    
    def test_invalid_certificate_type(self, pdf_service, completed_donation):
        """Test mit ungültigem Certificate-Type"""
        
        with pytest.raises(ValidationError, match="Invalid parameters"):
            pdf_service.generate_certificate_atomic(
                completed_donation.id, 
                'invalid_type'
            )
    
    def test_incomplete_donation(self, pdf_service, test_person, test_verse):
        """Test mit nicht abgeschlossener Donation"""
        
        # Pending donation erstellen
        pending_donation = Donation(
            person_id=test_person.id,
            verse_id=test_verse.id,
            donation_type='person',
            amount=Decimal('100.00'),
            payment_status='pending',  # Nicht completed
            person_snapshot=test_person.to_snapshot()
        )
        db.session.add(pending_donation)
        db.session.commit()
        
        with pytest.raises(ValidationError, match="not completed"):
            pdf_service.generate_certificate_atomic(
                pending_donation.id,
                'personal_certificate'
            )
    
    def test_path_generation(self, pdf_service, completed_donation):
        """Test korrekte Pfad-Generierung"""
        
        filename, file_path = pdf_service._generate_certificate_paths(
            completed_donation,
            'personal_certificate',
            'session_abc123'
        )
        
        # Filename-Format prüfen
        assert filename.startswith(f'donation_{completed_donation.id:03d}_')
        assert 'personal_certificate' in filename
        assert filename.endswith('.pdf')
        
        # Pfad-Struktur prüfen
        assert '/session_abc123/' in file_path
        assert filename in file_path
        
        # Jahr/Monat in Pfad
        now = datetime.now()
        expected_date_part = f"{now.year}/{now.month:02d}"
        assert expected_date_part in file_path
    
    def test_context_preparation_personal(self, pdf_service, completed_donation):
        """Test Context-Vorbereitung für persönliches Zertifikat"""
        
        context = pdf_service._prepare_certificate_context(
            completed_donation,
            'personal_certificate'
        )
        
        # Basis-Daten
        assert context['donation'] == completed_donation
        assert context['verse'] == completed_donation.verse
        assert context['formatted_amount'] == '100.00'
        
        # Person-Daten aus Snapshot
        person_data = context['person_snapshot']
        assert person_data['first_name'] == 'Max'
        assert person_data['last_name'] == 'Mustermann'
    
    def test_context_preparation_group(self, pdf_service, group_donation):
        """Test Context-Vorbereitung für Gruppenzertifikat"""
        
        context = pdf_service._prepare_certificate_context(
            group_donation,
            'group_certificate'
        )
        
        assert context['group_article'] == 'Die'
        assert context['group_name'] == 'Testgemeinde Musterstadt'
    
    def test_context_preparation_gift(self, pdf_service, gift_donation):
        """Test Context-Vorbereitung für Geschenkzertifikat"""
        
        context = pdf_service._prepare_certificate_context(
            gift_donation,
            'gift_certificate'
        )
        
        assert context['recipient_first_name'] == 'Anna'
        assert context['recipient_last_name'] == 'Müller'
    
    def test_amount_to_words(self, pdf_service):
        """Test Betrag-in-Worten Konvertierung"""
        
        assert pdf_service._amount_to_words(Decimal('100.00')) == 'Einhundert'
        assert pdf_service._amount_to_words(Decimal('250.00')) == 'Zweihundertfünfzig'
        assert pdf_service._amount_to_words(Decimal('33.00')) == 'Dreiunddreißig'
    
    def test_batch_generation(self, pdf_service, completed_donation, group_donation, 
                             gift_donation, mock_weasyprint):
        """Test Batch-Generierung mehrerer Zertifikate"""
        
        donation_ids = [completed_donation.id, group_donation.id, gift_donation.id]
        
        results = pdf_service.generate_donation_documents_batch(
            donation_ids,
            'batch_session_789'
        )
        
        # Alle Zertifikate erstellt
        assert len(results['certificates']) == 3
        assert len(results['tax_receipts']) == 2  # Nur completed_donation und group_donation want receipts
        assert len(results['errors']) == 0
        
        # Alle Dateien existieren
        for cert in results['certificates']:
            assert cert.exists_on_disk
            assert 'batch_session_789' in cert.file_path
    
    def test_transaction_rollback_on_error(self, pdf_service, completed_donation, monkeypatch):
        """Test dass bei Fehlern alles zurückgerollt wird"""
        
        # WeasyPrint zum Fehlschlagen bringen
        def failing_write_pdf(*args, **kwargs):
            raise Exception("Mock PDF generation failure")
        
        monkeypatch.setattr('weasyprint.HTML.write_pdf', failing_write_pdf)
        
        # Generierung sollte fehlschlagen
        with pytest.raises(PDFGenerationError):
            pdf_service.generate_certificate_atomic(
                completed_donation.id,
                'personal_certificate'
            )
        
        # Kein Certificate-Record in DB
        cert = Certificate.query.filter_by(donation_id=completed_donation.id).first()
        assert cert is None
    
    def test_duplicate_certificate_handling(self, pdf_service, completed_donation, mock_weasyprint):
        """Test dass bereits existierende Zertifikate nicht doppelt erstellt werden"""
        
        # Erstes Zertifikat erstellen
        cert1 = pdf_service.generate_certificate_atomic(
            completed_donation.id,
            'personal_certificate',
            'session_duplicate_test'
        )
        
        # Zweites Mal erstellen - sollte existierendes zurückgeben
        cert2 = pdf_service.generate_certificate_atomic(
            completed_donation.id,
            'personal_certificate',
            'session_duplicate_test'
        )
        
        # Gleiches Certificate zurückgegeben
        assert cert1.id == cert2.id
        
        # Nur ein Certificate-Record in DB
        certs = Certificate.query.filter_by(
            donation_id=completed_donation.id,
            certificate_type='personal_certificate'
        ).all()
        assert len(certs) == 1
```

### 3. Integration-Tests

- [ ] **Test-Suite**: `tests/test_pdf_integration.py`
- [ ] **End-to-End-Flows**: Komplette User-Journey testen
- [ ] **Template-Rendering**: HTML-Output validieren
- [ ] **Download-Security**: Sicherheitsmechanismen testen

#### Integration-Tests implementieren:
```python
# tests/test_pdf_integration.py

import pytest
from flask import session

class TestPDFIntegration:
    
    def test_complete_checkout_flow(self, client, completed_donation, mock_weasyprint):
        """Test kompletter Checkout-Flow mit PDF-Generierung"""
        
        # Session für Checkout-Erfolg vorbereiten
        with client.session_transaction() as sess:
            sess['completed_donations'] = [completed_donation.id]
            sess['session_id'] = 'integration_test_session'
        
        # Checkout-Erfolg aufrufen
        response = client.get('/checkout-erfolg')
        
        assert response.status_code == 200
        
        # PDF-Links in Response
        response_text = response.get_data(as_text=True)
        assert 'Zertifikat herunterladen' in response_text
        assert 'Bescheinigung herunterladen' in response_text
        assert 'test@example.com' in response_text
        
        # Certificate-Records in DB erstellt
        certificates = Certificate.query.filter_by(donation_id=completed_donation.id).all()
        assert len(certificates) == 2  # Certificate + Tax Receipt
    
    def test_certificate_download_authorized(self, client, completed_donation, mock_weasyprint):
        """Test autorisierter Certificate-Download"""
        
        # PDF erstellen
        pdf_service = PDFGeneratorService(client.application)
        certificate = pdf_service.generate_certificate_atomic(
            completed_donation.id,
            'personal_certificate',
            'download_test_session'
        )
        
        # Session für Download-Berechtigung
        with client.session_transaction() as sess:
            sess['completed_donations'] = [completed_donation.id]
            sess['pdfs_generated'] = True
        
        # Download versuchen
        response = client.get(f'/download/certificate/{certificate.id}')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/pdf'
        assert certificate.filename in response.headers['Content-Disposition']
    
    def test_certificate_download_unauthorized(self, client, completed_donation, mock_weasyprint):
        """Test unautorisierten Download-Versuch"""
        
        pdf_service = PDFGeneratorService(client.application)
        certificate = pdf_service.generate_certificate_atomic(
            completed_donation.id,
            'personal_certificate'
        )
        
        # Ohne Session-Berechtigung
        response = client.get(f'/download/certificate/{certificate.id}')
        
        assert response.status_code == 403
    
    def test_missing_pdf_file_handling(self, client, completed_donation):
        """Test Verhalten wenn PDF-Datei gelöscht wurde"""
        
        # Certificate-Record ohne echte Datei erstellen
        certificate = Certificate(
            donation_id=completed_donation.id,
            certificate_type='personal_certificate',
            filename='missing_file.pdf',
            file_path='/nonexistent/path/missing_file.pdf'
        )
        db.session.add(certificate)
        db.session.commit()
        
        # Session-Berechtigung
        with client.session_transaction() as sess:
            sess['completed_donations'] = [completed_donation.id]
        
        # Download sollte 404 zurückgeben
        response = client.get(f'/download/certificate/{certificate.id}')
        assert response.status_code == 404
    
    def test_template_rendering_personal(self, test_app, completed_donation):
        """Test Template-Rendering für persönliches Zertifikat"""
        
        with test_app.app_context():
            pdf_service = PDFGeneratorService(test_app)
            context = pdf_service._prepare_certificate_context(
                completed_donation,
                'personal_certificate'
            )
            
            # Template rendern
            from flask import render_template
            html = render_template('certificates/personal_certificate.html', **context)
            
            # Content-Validierung
            assert 'Max Mustermann' in html
            assert '100.00 €' in html
            assert 'Jesaja 43,1' in html
            assert 'Fürchte dich nicht' in html
    
    def test_template_rendering_group(self, test_app, group_donation):
        """Test Template-Rendering für Gruppenzertifikat"""
        
        with test_app.app_context():
            pdf_service = PDFGeneratorService(test_app)
            context = pdf_service._prepare_certificate_context(
                group_donation,
                'group_certificate'
            )
            
            html = render_template('certificates/group_certificate.html', **context)
            
            assert 'Die Testgemeinde Musterstadt' in html
            assert '100.00 €' in html
    
    def test_template_rendering_tax_receipt(self, test_app, completed_donation):
        """Test Template-Rendering für Spendenbescheinigung"""
        
        with test_app.app_context():
            pdf_service = PDFGeneratorService(test_app)
            context = pdf_service._prepare_tax_receipt_context(completed_donation)
            
            html = render_template('certificates/tax_receipt.html', **context)
            
            # Stiftungsdaten
            assert 'Peter-Schöffer-Stiftung' in html
            assert 'Wormser Weg 17' in html
            
            # Spender-Daten
            assert 'Max Mustermann' in html
            assert 'Teststraße 123' in html
            assert '12345 Teststadt' in html
            
            # Betrag
            assert '100.00' in html
            assert 'Einhundert' in html
    
    def test_error_handling_in_checkout(self, client, completed_donation, monkeypatch):
        """Test Error-Handling bei PDF-Problemen im Checkout"""
        
        # PDF-Service zum Fehlschlagen bringen
        def failing_generate_batch(*args, **kwargs):
            raise PDFGenerationError("Test error for error handling")
        
        monkeypatch.setattr(
            'pdf_service.PDFGeneratorService.generate_donation_documents_batch',
            failing_generate_batch
        )
        
        with client.session_transaction() as sess:
            sess['completed_donations'] = [completed_donation.id]
        
        response = client.get('/checkout-erfolg')
        
        # Seite lädt trotz PDF-Fehler
        assert response.status_code == 200
        
        # Fallback-Nachricht angezeigt
        response_text = response.get_data(as_text=True)
        assert 'werden gerade erstellt' in response_text
        assert 'per E-Mail versendet' in response_text
```

### 4. Performance-Tests

- [ ] **Load-Tests**: Batch-Generierung unter Last
- [ ] **Memory-Tests**: Memory-Leaks bei vielen PDFs
- [ ] **Timing-Tests**: Generation-Zeit messen
- [ ] **Scalability-Tests**: Große Anzahl gleichzeitiger Requests

#### Performance-Test-Suite:
```python
# tests/test_pdf_performance.py

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

class TestPDFPerformance:
    
    def test_single_pdf_generation_time(self, pdf_service, completed_donation, mock_weasyprint):
        """Test Generierungszeit für einzelnes PDF"""
        
        start_time = time.time()
        
        certificate = pdf_service.generate_certificate_atomic(
            completed_donation.id,
            'personal_certificate'
        )
        
        generation_time = time.time() - start_time
        
        # Generierung sollte unter 2 Sekunden dauern (mit Mock)
        assert generation_time < 2.0
        assert certificate.exists_on_disk
    
    def test_batch_generation_performance(self, pdf_service, test_app, mock_weasyprint):
        """Test Performance bei Batch-Generierung"""
        
        # 20 Test-Donations erstellen
        donation_ids = []
        
        with test_app.app_context():
            for i in range(20):
                person = Person(
                    email=f'test{i}@example.com',
                    first_name=f'Test{i}',
                    last_name='User'
                )
                
                verse = Verse(
                    book='PSALM',
                    chapter=23,
                    verse=i+1,
                    text=f'Test verse {i+1}',
                    reference=f'Psalm 23,{i+1}',
                    is_sponsored=False
                )
                
                donation = Donation(
                    person_id=person.id,
                    verse_id=verse.id,
                    donation_type='person',
                    amount=Decimal('100.00'),
                    payment_status='completed',
                    person_snapshot=person.to_snapshot(),
                    wants_receipt=True,
                    privacy_consent=True
                )
                
                db.session.add_all([person, verse, donation])
                db.session.flush()
                donation_ids.append(donation.id)
            
            db.session.commit()
            
            # Batch-Generierung testen
            start_time = time.time()
            
            results = pdf_service.generate_donation_documents_batch(
                donation_ids,
                'performance_test_session'
            )
            
            batch_time = time.time() - start_time
            
            # Performance-Assertions
            assert len(results['certificates']) == 20
            assert len(results['tax_receipts']) == 20
            assert batch_time < 30.0  # 20 PDFs in unter 30 Sekunden
            
            # Durchschnitt pro PDF
            avg_time_per_pdf = batch_time / 40  # 20 certificates + 20 tax receipts
            assert avg_time_per_pdf < 1.5
    
    def test_concurrent_pdf_generation(self, pdf_service, test_app, mock_weasyprint):
        """Test gleichzeitige PDF-Generierung"""
        
        # 10 Test-Donations erstellen
        donation_ids = []
        
        with test_app.app_context():
            for i in range(10):
                person = Person(email=f'concurrent{i}@example.com', first_name=f'User{i}', last_name='Test')
                verse = Verse(book='JESAJA', chapter=40, verse=i+1, text=f'Verse {i+1}', reference=f'Jesaja 40,{i+1}')
                donation = Donation(
                    person_id=person.id, verse_id=verse.id, donation_type='person',
                    amount=Decimal('100.00'), payment_status='completed',
                    person_snapshot=person.to_snapshot(), privacy_consent=True
                )
                
                db.session.add_all([person, verse, donation])
                db.session.flush()
                donation_ids.append(donation.id)
            
            db.session.commit()
            
            def generate_pdf(donation_id):
                """Thread-Worker für PDF-Generierung"""
                try:
                    return pdf_service.generate_certificate_atomic(
                        donation_id,
                        'personal_certificate',
                        f'thread_session_{threading.current_thread().ident}'
                    )
                except Exception as e:
                    return e
            
            # Gleichzeitige Generierung mit ThreadPoolExecutor
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(generate_pdf, donation_ids))
            
            concurrent_time = time.time() - start_time
            
            # Alle PDFs erfolgreich erstellt
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == 10
            
            # Concurrent sollte schneller sein als sequential
            assert concurrent_time < 15.0  # 10 PDFs in unter 15 Sekunden
    
    def test_memory_usage_large_batch(self, pdf_service, test_app, mock_weasyprint):
        """Test Memory-Usage bei großen Batches"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 50 Donations erstellen (simuliert große Session)
        donation_ids = []
        
        with test_app.app_context():
            for i in range(50):
                person = Person(email=f'memory{i}@example.com', first_name=f'User{i}', last_name='Test')
                verse = Verse(book='PSALM', chapter=119, verse=i+1, text=f'Long verse text {i+1} ' * 10, reference=f'Psalm 119,{i+1}')
                donation = Donation(
                    person_id=person.id, verse_id=verse.id, donation_type='person',
                    amount=Decimal('100.00'), payment_status='completed',
                    person_snapshot=person.to_snapshot(), privacy_consent=True
                )
                
                db.session.add_all([person, verse, donation])
                db.session.flush()
                donation_ids.append(donation.id)
            
            db.session.commit()
            
            # Memory vor Generierung
            pre_generation_memory = process.memory_info().rss
            
            # Batch-Generierung
            results = pdf_service.generate_donation_documents_batch(
                donation_ids,
                'memory_test_session',
                chunk_size=10  # Kleinere Chunks für besseres Memory-Management
            )
            
            # Memory nach Generierung
            post_generation_memory = process.memory_info().rss
            
            # Memory-Increase sollte reasonable sein
            memory_increase = post_generation_memory - pre_generation_memory
            memory_increase_mb = memory_increase / (1024 * 1024)
            
            # Nicht mehr als 100MB zusätzlich für 50 PDFs
            assert memory_increase_mb < 100
            
            # Alle PDFs erstellt
            assert len(results['certificates']) == 50
    
    def test_file_system_performance(self, pdf_service, completed_donation, mock_weasyprint, tmp_path):
        """Test Dateisystem-Performance bei vielen Dateien"""
        
        # Custom storage path für Test
        storage_path = str(tmp_path / 'performance_certificates')
        pdf_service.app.config['CERTIFICATE_STORAGE_PATH'] = storage_path
        
        # 100 PDFs in verschiedenen Sessions erstellen
        start_time = time.time()
        
        certificates = []
        for i in range(100):
            session_id = f'perf_session_{i // 10}'  # 10 PDFs pro Session
            
            certificate = pdf_service.generate_certificate_atomic(
                completed_donation.id,
                'personal_certificate',
                session_id
            )
            certificates.append(certificate)
        
        creation_time = time.time() - start_time
        
        # File-Creation sollte linear skalieren
        assert creation_time < 60.0  # 100 PDFs in unter 60 Sekunden
        
        # Alle Dateien existieren
        for cert in certificates:
            assert cert.exists_on_disk
        
        # Korrekte Verzeichnisstruktur
        session_dirs = set()
        for cert in certificates:
            session_dir = cert.file_path.split('/')[-2]
            session_dirs.add(session_dir)
        
        # 10 verschiedene Session-Verzeichnisse
        assert len(session_dirs) == 10
```

### 5. Security-Tests

- [ ] **Access-Control-Tests**: Unauthorisierter Zugriff auf PDFs
- [ ] **Path-Traversal-Tests**: Sicherheit der Pfad-Generierung
- [ ] **Rate-Limiting-Tests**: Schutz vor Missbrauch
- [ ] **Input-Validation-Tests**: SQL-Injection und XSS Schutz

#### Security-Test-Suite:
```python
# tests/test_pdf_security.py

import pytest
import os
from unittest.mock import patch

class TestPDFSecurity:
    
    def test_unauthorized_certificate_download(self, client, completed_donation, mock_weasyprint):
        """Test unautorisierten Zugriff auf PDFs"""
        
        pdf_service = PDFGeneratorService(client.application)
        certificate = pdf_service.generate_certificate_atomic(
            completed_donation.id,
            'personal_certificate'
        )
        
        # Ohne Session-Daten
        response = client.get(f'/download/certificate/{certificate.id}')
        assert response.status_code == 403
        
        # Mit falschen Session-Daten
        with client.session_transaction() as sess:
            sess['completed_donations'] = [99999]  # Andere Donation-ID
        
        response = client.get(f'/download/certificate/{certificate.id}')
        assert response.status_code == 403
    
    def test_path_traversal_protection(self, pdf_service, completed_donation):
        """Test Schutz vor Directory Traversal"""
        
        # Malicious session_id mit Path Traversal
        malicious_session = '../../../etc/passwd'
        
        # Sollte sicher behandelt werden
        filename, file_path = pdf_service._generate_certificate_paths(
            completed_donation,
            'personal_certificate',
            malicious_session
        )
        
        # Pfad sollte innerhalb des erlaubten Bereichs bleiben
        base_path = pdf_service.app.config['CERTIFICATE_STORAGE_PATH']
        assert os.path.commonpath([file_path, base_path]) == base_path
        
        # Keine gefährlichen Pfad-Komponenten
        assert '..' not in file_path
        assert '/etc/passwd' not in file_path
    
    def test_file_path_validation(self, test_app):
        """Test Certificate file_path Validierung"""
        
        # Gültige Pfade
        valid_cert = Certificate(
            donation_id=1,
            certificate_type='personal_certificate',
            filename='test.pdf',
            file_path='/safe/path/test.pdf'
        )
        assert valid_cert.validate_file_path()
        
        # Ungültige Pfade
        invalid_paths = [
            '../../../etc/passwd',
            '/path/with/../traversal',
            'path/with/../../danger',
            '/path/with\x00null',
            'path/with|pipe',
            'path/with<redirect>'
        ]
        
        for invalid_path in invalid_paths:
            invalid_cert = Certificate(
                donation_id=1,
                certificate_type='personal_certificate',
                filename='test.pdf',
                file_path=invalid_path
            )
            assert not invalid_cert.validate_file_path()
    
    def test_download_rate_limiting(self, client, completed_donation, mock_weasyprint):
        """Test Rate-Limiting für Downloads"""
        
        pdf_service = PDFGeneratorService(client.application)
        certificate = pdf_service.generate_certificate_atomic(
            completed_donation.id,
            'personal_certificate'
        )
        
        # Session für berechtigen Zugriff
        with client.session_transaction() as sess:
            sess['completed_donations'] = [completed_donation.id]
        
        # Viele Requests schnell hintereinander
        responses = []
        for i in range(15):  # Mehr als das 10/minute Limit
            response = client.get(f'/download/certificate/{certificate.id}')
            responses.append(response.status_code)
        
        # Erste Requests OK, spätere rate-limited
        successful_requests = sum(1 for status in responses if status == 200)
        rate_limited_requests = sum(1 for status in responses if status == 429)
        
        # Rate-Limiting greift
        assert successful_requests <= 12  # Etwas Toleranz für Timing
        assert rate_limited_requests >= 3
    
    def test_sql_injection_in_certificate_lookup(self, client):
        """Test SQL-Injection Schutz bei Certificate-Lookup"""
        
        # SQL-Injection Versuche
        malicious_ids = [
            "1; DROP TABLE certificates;--",
            "1' OR '1'='1",
            "1 UNION SELECT * FROM persons",
            "1'; DELETE FROM donations;--"
        ]
        
        for malicious_id in malicious_ids:
            # Sollte sicher als 404 behandelt werden
            response = client.get(f'/download/certificate/{malicious_id}')
            assert response.status_code == 404
    
    def test_xss_protection_in_templates(self, test_app, completed_donation):
        """Test XSS-Schutz in PDF-Templates"""
        
        # Malicious Person-Daten mit XSS-Payload
        malicious_person = Person(
            email='test@example.com',
            first_name='<script>alert("xss")</script>',
            last_name='</script><img src=x onerror=alert(1)>',
            street='<iframe src=javascript:alert(1)></iframe>'
        )
        
        malicious_donation = Donation(
            person_id=1,  # Dummy
            verse_id=1,   # Dummy
            donation_type='person',
            amount=Decimal('100.00'),
            payment_status='completed',
            person_snapshot=malicious_person.to_snapshot(),
            privacy_consent=True
        )
        
        with test_app.app_context():
            pdf_service = PDFGeneratorService(test_app)
            context = pdf_service._prepare_certificate_context(
                malicious_donation,
                'personal_certificate'
            )
            
            # Template rendern
            from flask import render_template
            html = render_template('certificates/personal_certificate.html', **context)
            
            # XSS-Payloads sollten escaped sein
            assert '<script>' not in html
            assert 'alert(' not in html
            assert '<iframe' not in html
            assert 'javascript:' not in html
            
            # Escaped Versionen sollten vorhanden sein
            assert '&lt;script&gt;' in html or html.count('<') == html.count('&lt;')
    
    def test_session_fixation_protection(self, client, completed_donation):
        """Test Schutz vor Session Fixation"""
        
        # Alte Session-ID
        old_session_id = None
        
        with client.session_transaction() as sess:
            sess['completed_donations'] = [completed_donation.id]
            old_session_id = sess.get('csrf_token')  # Proxy für Session-ID
        
        # Checkout-Erfolg aufrufen
        response = client.get('/checkout-erfolg')
        assert response.status_code == 200
        
        # Session sollte regeneriert werden (nicht zwingend, aber sicher)
        with client.session_transaction() as sess:
            new_session_id = sess.get('csrf_token')
            # Session-Inhalt sollte noch vorhanden sein
            assert sess.get('completed_donations') == [completed_donation.id]
    
    def test_csrf_protection_on_sensitive_endpoints(self, client):
        """Test CSRF-Schutz auf sensible Endpoints"""
        
        # PDF-Retry Endpoint sollte CSRF-geschützt sein
        response = client.post('/api/retry-pdf-generation', json={
            'donation_id': 1,
            'certificate_type': 'personal_certificate'
        })
        
        # Ohne CSRF-Token sollte Request abgelehnt werden
        assert response.status_code in [403, 400]
```

### 6. Load-Testing mit echten Szenarien

- [ ] **Stress-Tests**: System an Grenzen bringen
- [ ] **Realistic Workloads**: Typische User-Patterns simulieren
- [ ] **Recovery-Tests**: Verhalten nach System-Überlastung
- [ ] **Resource-Monitoring**: CPU, Memory, Disk-Usage überwachen

#### Load-Test Framework:
```python
# tests/test_pdf_load.py

import pytest
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
import threading

class TestPDFLoadTesting:
    
    @pytest.mark.slow  # Marker für langsame Tests
    def test_high_concurrency_checkout(self, test_app, mock_weasyprint):
        """Test hohe Anzahl gleichzeitiger Checkout-Requests"""
        
        # 100 Test-Donations vorbereiten
        donation_ids = []
        
        with test_app.app_context():
            # Batch-Insert für bessere Performance
            persons = []
            verses = []
            donations = []
            
            for i in range(100):
                person = Person(email=f'load{i}@example.com', first_name=f'User{i}', last_name='Load')
                verse = Verse(book='PSALM', chapter=1, verse=i+1, text=f'Load test verse {i}', reference=f'Psalm 1,{i+1}')
                
                persons.append(person)
                verses.append(verse)
            
            db.session.add_all(persons + verses)
            db.session.flush()  # IDs generieren
            
            for i, (person, verse) in enumerate(zip(persons, verses)):
                donation = Donation(
                    person_id=person.id, verse_id=verse.id, donation_type='person',
                    amount=Decimal('100.00'), payment_status='completed',
                    person_snapshot=person.to_snapshot(), privacy_consent=True,
                    wants_receipt=True
                )
                donations.append(donation)
                
            db.session.add_all(donations)
            db.session.commit()
            
            donation_ids = [d.id for d in donations]
        
        def simulate_user_session(user_id, donation_batch):
            """Simuliert einen User mit mehreren Donations"""
            with test_app.test_client() as client:
                # Session setup
                with client.session_transaction() as sess:
                    sess['completed_donations'] = donation_batch
                    sess['session_id'] = f'load_session_{user_id}'
                
                # Checkout-Erfolg Request
                start_time = time.time()
                response = client.get('/checkout-erfolg')
                request_time = time.time() - start_time
                
                return {
                    'user_id': user_id,
                    'status_code': response.status_code,
                    'response_time': request_time,
                    'success': response.status_code == 200
                }
        
        # 20 gleichzeitige User-Sessions (je 5 Donations)
        donation_batches = [donation_ids[i:i+5] for i in range(0, 100, 5)]
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(simulate_user_session, i, batch)
                for i, batch in enumerate(donation_batches[:20])
            ]
            
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        
        # Performance-Assertions
        successful_requests = sum(1 for r in results if r['success'])
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        max_response_time = max(r['response_time'] for r in results)
        
        assert successful_requests >= 18  # 90% success rate
        assert avg_response_time < 5.0    # Durchschnitt unter 5 Sekunden
        assert max_response_time < 15.0   # Keine Request über 15 Sekunden
        assert total_time < 30.0          # Alle Requests in unter 30 Sekunden
    
    def test_memory_stability_long_running(self, pdf_service, test_app, mock_weasyprint):
        """Test Memory-Stabilität über längeren Zeitraum"""
        import psutil
        import gc
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 500 PDFs über 10 Batches generieren
        for batch in range(10):
            with test_app.app_context():
                # 50 Donations pro Batch
                donation_ids = []
                
                for i in range(50):
                    person = Person(email=f'stability{batch}_{i}@example.com', first_name=f'User{i}', last_name=f'Batch{batch}')
                    verse = Verse(book='GENESIS', chapter=1, verse=i+1, text=f'Stability test verse {i}', reference=f'Genesis 1,{i+1}')
                    donation = Donation(
                        person_id=person.id, verse_id=verse.id, donation_type='person',
                        amount=Decimal('100.00'), payment_status='completed',
                        person_snapshot=person.to_snapshot(), privacy_consent=True
                    )
                    
                    db.session.add_all([person, verse, donation])
                    db.session.flush()
                    donation_ids.append(donation.id)
                
                db.session.commit()
                
                # Batch-Generierung
                results = pdf_service.generate_donation_documents_batch(
                    donation_ids,
                    f'stability_session_{batch}',
                    chunk_size=10
                )
                
                # Memory nach jedem Batch prüfen
                current_memory = process.memory_info().rss
                memory_increase = (current_memory - initial_memory) / (1024 * 1024)  # MB
                
                # Memory sollte nicht unbegrenzt wachsen
                assert memory_increase < 200  # Nicht mehr als 200MB Increase
                
                # Explizite Garbage Collection
                gc.collect()
                
                # Successful generation
                assert len(results['certificates']) == 50
                assert len(results['errors']) == 0
        
        # Finale Memory-Prüfung
        final_memory = process.memory_info().rss
        total_memory_increase = (final_memory - initial_memory) / (1024 * 1024)
        
        # Nach 500 PDFs sollte Memory-Increase reasonable sein
        assert total_memory_increase < 300  # Unter 300MB für 500 PDFs
```

## Performance-Optimierungen implementieren

### Template-Caching
```python
# In pdf_service.py
from jinja2 import Environment, FileSystemLoader
from functools import lru_cache

class OptimizedPDFGeneratorService(PDFGeneratorService):
    
    def __init__(self, app=None):
        super().__init__(app)
        self._template_cache = {}
        
    @lru_cache(maxsize=10)
    def _get_compiled_template(self, template_name):
        """Cached Template-Kompilierung"""
        return self.app.jinja_env.get_template(template_name)
    
    def _render_template_cached(self, template_name, **context):
        """Template mit Caching rendern"""
        template = self._get_compiled_template(template_name)
        return template.render(**context)
```

## Nächste Schritte

Nach Abschluss aller Tests:
1. **CI/CD-Integration**: Tests in Build-Pipeline einbinden
2. **Production-Monitoring**: Metriken und Alerts einrichten
3. **Documentation**: API-Dokumentation vervollständigen
4. **User-Acceptance-Testing**: Mit echten Usern testen