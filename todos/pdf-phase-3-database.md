# PDF Phase 3: Database-Integration

**Status:** TODO  
**Priorität:** Hoch  
**Abhängigkeiten:** Phase 2 (PDFGeneratorService)  
**Geschätzte Zeit:** 3-4 Stunden

## Überblick

Diese Phase verfeinert die Datenbank-Integration, implementiert atomische Transaktionen für PDF-Generierung und Certificate-Verwaltung, und stellt sicher, dass Dateisystem und Datenbank synchron bleiben.

## Aufgaben-Checkliste

### 1. Certificate-Model erweitern

- [ ] **Neue Methoden**: `exists_on_disk`, `delete_file`, `get_download_url`
- [ ] **Model-Validierung**: Erweiterte Validierung für file_path
- [ ] **Indexes hinzufügen**: Performance-Optimierung
- [ ] **Migration**: Wenn neue Felder hinzugefügt werden

#### Erweiterte Certificate-Model Methoden:
```python
# In models.py - Certificate-Klasse erweitern

class Certificate(db.Model):
    # ... bestehende Felder ...
    
    @property
    def exists_on_disk(self):
        """Prüft ob PDF-Datei tatsächlich existiert"""
        return os.path.exists(self.file_path) if self.file_path else False
    
    @property
    def file_size(self):
        """Dateigröße in Bytes"""
        if self.exists_on_disk:
            return os.path.getsize(self.file_path)
        return 0
    
    def delete_file(self):
        """Löscht PDF-Datei vom Dateisystem"""
        if self.exists_on_disk:
            try:
                os.remove(self.file_path)
                return True
            except OSError:
                return False
        return True
    
    def get_download_url(self):
        """Generiert sichere Download-URL"""
        return f"/download/certificate/{self.id}"
    
    def validate_file_path(self):
        """Validiert file_path auf Sicherheit"""
        if not self.file_path:
            return False
        
        # Nur erlaubte Zeichen
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./\\')
        if not all(c in allowed_chars for c in self.file_path):
            return False
            
        # Kein Path Traversal
        normalized = os.path.normpath(self.file_path)
        if '..' in normalized:
            return False
            
        return True
    
    @classmethod
    def find_by_donation_and_type(cls, donation_id: int, certificate_type: str):
        """Findet Certificate nach Donation und Type"""
        return cls.query.filter_by(
            donation_id=donation_id,
            certificate_type=certificate_type
        ).first()
    
    @classmethod
    def cleanup_orphaned_files(cls):
        """Löscht PDF-Dateien ohne entsprechenden DB-Record"""
        base_path = current_app.config.get('CERTIFICATE_STORAGE_PATH', '/tmp/certificates')
        if not os.path.exists(base_path):
            return 0
            
        deleted_count = 0
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    
                    # Prüfen ob Certificate-Record existiert
                    certificate = cls.query.filter_by(file_path=file_path).first()
                    if not certificate:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except OSError:
                            pass
        
        return deleted_count
    
    def __repr__(self):
        return f'<Certificate {self.id}: {self.certificate_type} for Donation {self.donation_id}>'
```

### 2. Atomische Transaktionen implementieren

- [ ] **Service erweitern**: Transaction-Management in PDFGeneratorService
- [ ] **Rollback-Logic**: Bei Fehlern alles rückgängig machen
- [ ] **Savepoints**: Für komplexe Multi-Operation Transaktionen
- [ ] **Error-Recovery**: Konsistenz nach Fehlern wiederherstellen

#### Transaction-Management im PDFGeneratorService:
```python
# In pdf_service.py erweitern

from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

class PDFGeneratorService:
    
    @contextmanager
    def _atomic_operation(self):
        """Context Manager für atomische PDF-Generierung"""
        created_files = []
        savepoint = None
        
        try:
            # Savepoint für Rollback
            savepoint = db.session.begin_nested()
            
            yield created_files
            
            # Alles erfolgreich - committen
            savepoint.commit()
            db.session.commit()
            
        except Exception as e:
            # Rollback Datenbank
            if savepoint:
                savepoint.rollback()
            db.session.rollback()
            
            # Cleanup: Erstellte Dateien löschen
            for file_path in created_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass  # File cleanup failure - nicht kritisch
            
            raise PDFGenerationError(f"Atomic operation failed: {str(e)}")
    
    def generate_certificate_atomic(self, donation_id: int, certificate_type: str, 
                                   session_id: Optional[str] = None) -> Certificate:
        """Atomische Certificate-Generierung"""
        
        with self._atomic_operation() as created_files:
            # 1. Parameter validieren
            donation = self._validate_donation(donation_id)
            
            # 2. Prüfen ob Certificate bereits existiert
            existing = Certificate.find_by_donation_and_type(donation_id, certificate_type)
            if existing and existing.exists_on_disk:
                return existing
            
            # 3. Pfade generieren
            filename, file_path = self._generate_certificate_paths(
                donation, certificate_type, session_id
            )
            created_files.append(file_path)  # Für Cleanup registrieren
            
            # 4. PDF generieren
            context = self._prepare_certificate_context(donation, certificate_type)
            template_name = f"certificates/{certificate_type}.html"
            html_content = render_template(template_name, **context)
            self._generate_pdf_from_html(html_content, file_path)
            
            # 5. Certificate-Record erstellen
            certificate = Certificate(
                donation_id=donation.id,
                certificate_type=certificate_type,
                filename=filename,
                file_path=file_path
            )
            
            # Validierung vor DB-Insert
            if not certificate.validate_file_path():
                raise ValidationError(f"Invalid file path: {file_path}")
            
            db.session.add(certificate)
            db.session.flush()  # ID generieren aber noch nicht committen
            
            return certificate
    
    def _validate_donation(self, donation_id: int) -> Donation:
        """Validiert Donation für PDF-Generierung"""
        donation = Donation.query.get(donation_id)
        if not donation:
            raise ValidationError(f"Donation {donation_id} not found")
        
        if donation.payment_status != 'completed':
            raise ValidationError(f"Donation {donation_id} not completed")
        
        # Prüfen ob Donation alle required fields hat
        if not donation.person_snapshot and not donation.person:
            raise ValidationError(f"No person data for donation {donation_id}")
        
        if not donation.verse:
            raise ValidationError(f"No verse data for donation {donation_id}")
        
        return donation
```

### 3. Batch-Operations mit Transaktionen

- [ ] **Batch-Generierung**: Mehrere PDFs in einer Transaction
- [ ] **Partial-Success-Handling**: Was tun bei teilweise erfolgreichen Batches?
- [ ] **Progress-Tracking**: Status-Updates während langer Operationen
- [ ] **Memory-Management**: Große Batches in Chunks verarbeiten

#### Erweiterte Batch-Operations:
```python
def generate_donation_documents_batch(self, donation_ids: List[int], 
                                     session_id: str,
                                     chunk_size: int = 10) -> Dict[str, List[Certificate]]:
    """
    Generiert alle Dokumente für eine Liste von Donations
    Verarbeitet in Chunks für besseres Memory-Management
    """
    results = {
        'certificates': [],
        'tax_receipts': [],
        'errors': []
    }
    
    # In Chunks verarbeiten
    for i in range(0, len(donation_ids), chunk_size):
        chunk = donation_ids[i:i + chunk_size]
        
        try:
            chunk_results = self._process_donation_chunk(chunk, session_id)
            
            # Ergebnisse sammeln
            results['certificates'].extend(chunk_results['certificates'])
            results['tax_receipts'].extend(chunk_results['tax_receipts'])
            
        except Exception as e:
            # Chunk-Fehler protokollieren aber weitermachen
            error_info = {
                'chunk': chunk,
                'error': str(e),
                'timestamp': datetime.utcnow()
            }
            results['errors'].append(error_info)
    
    return results

def _process_donation_chunk(self, donation_ids: List[int], 
                           session_id: str) -> Dict[str, List[Certificate]]:
    """Verarbeitet einen Chunk von Donations atomisch"""
    
    with self._atomic_operation() as created_files:
        certificates = []
        tax_receipts = []
        
        for donation_id in donation_ids:
            try:
                donation = self._validate_donation(donation_id)
                
                # Certificate-Type bestimmen
                cert_type = self._determine_certificate_type(donation)
                
                # Zertifikat generieren
                certificate = self.generate_certificate_atomic(
                    donation_id, cert_type, session_id
                )
                certificates.append(certificate)
                
                # Spendenbescheinigung wenn gewünscht
                if donation.wants_receipt:
                    tax_receipt = self.generate_tax_receipt_atomic(
                        donation_id, session_id
                    )
                    tax_receipts.append(tax_receipt)
                    
                # Status in Donation aktualisieren
                donation.certificate_generated = True
                if donation.wants_receipt:
                    donation.receipt_generated = True
                    
            except Exception as e:
                # Einzelnen Donation-Fehler protokollieren aber Chunk fortsetzen
                current_app.logger.warning(
                    f"Failed to process donation {donation_id}: {str(e)}"
                )
        
        return {
            'certificates': certificates,
            'tax_receipts': tax_receipts
        }

def _determine_certificate_type(self, donation: Donation) -> str:
    """Bestimmt Certificate-Type basierend auf Donation-Type"""
    type_mapping = {
        'person': 'personal_certificate',
        'gruppe': 'group_certificate', 
        'geschenk': 'gift_certificate'
    }
    return type_mapping.get(donation.donation_type, 'personal_certificate')
```

### 4. Konsistenz-Checks implementieren

- [ ] **Methode**: `verify_consistency()` - Prüft DB vs Filesystem
- [ ] **Orphaned Files**: Dateien ohne DB-Record finden
- [ ] **Missing Files**: DB-Records ohne Datei finden
- [ ] **Repair-Funktionen**: Automatische Reparatur wenn möglich

#### Konsistenz-Management:
```python
class CertificateConsistencyManager:
    """Verwaltet Konsistenz zwischen Datenbank und Dateisystem"""
    
    def __init__(self, pdf_service: PDFGeneratorService):
        self.pdf_service = pdf_service
        self.base_path = current_app.config.get('CERTIFICATE_STORAGE_PATH')
    
    def verify_consistency(self) -> Dict[str, Any]:
        """Vollständige Konsistenz-Prüfung"""
        results = {
            'total_certificates': 0,
            'consistent': 0,
            'missing_files': [],
            'orphaned_files': [],
            'invalid_paths': [],
            'errors': []
        }
        
        # Alle Certificates prüfen
        certificates = Certificate.query.all()
        results['total_certificates'] = len(certificates)
        
        for cert in certificates:
            try:
                if not cert.validate_file_path():
                    results['invalid_paths'].append({
                        'id': cert.id,
                        'path': cert.file_path,
                        'reason': 'Invalid path format'
                    })
                elif not cert.exists_on_disk:
                    results['missing_files'].append({
                        'id': cert.id,
                        'path': cert.file_path,
                        'donation_id': cert.donation_id
                    })
                else:
                    results['consistent'] += 1
                    
            except Exception as e:
                results['errors'].append({
                    'certificate_id': cert.id,
                    'error': str(e)
                })
        
        # Orphaned Files finden
        results['orphaned_files'] = self._find_orphaned_files()
        
        return results
    
    def _find_orphaned_files(self) -> List[Dict[str, Any]]:
        """Findet PDF-Dateien ohne entsprechenden Certificate-Record"""
        if not os.path.exists(self.base_path):
            return []
        
        orphaned = []
        all_db_paths = set(cert.file_path for cert in Certificate.query.all() if cert.file_path)
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    
                    if file_path not in all_db_paths:
                        orphaned.append({
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                        })
        
        return orphaned
    
    def repair_missing_files(self, missing_files: List[Dict]) -> Dict[str, Any]:
        """Regeneriert fehlende PDF-Dateien"""
        results = {
            'repaired': 0,
            'failed': [],
            'errors': []
        }
        
        for missing in missing_files:
            try:
                cert_id = missing['id']
                certificate = Certificate.query.get(cert_id)
                
                if not certificate:
                    continue
                
                # PDF neu generieren
                donation = certificate.donation
                session_id = self._extract_session_from_path(certificate.file_path)
                
                # Neues Certificate generieren (das alte wird überschrieben)
                new_cert = self.pdf_service.generate_certificate_atomic(
                    donation.id,
                    certificate.certificate_type,
                    session_id
                )
                
                results['repaired'] += 1
                
            except Exception as e:
                results['failed'].append(missing['id'])
                results['errors'].append({
                    'certificate_id': missing.get('id'),
                    'error': str(e)
                })
        
        return results
    
    def _extract_session_from_path(self, file_path: str) -> Optional[str]:
        """Extrahiert Session-ID aus Dateipfad"""
        # Pattern: .../session_xyz123/...
        import re
        match = re.search(r'/session_([^/]+)/', file_path)
        return match.group(1) if match else None
    
    def cleanup_orphaned_files(self, max_age_days: int = 7) -> int:
        """Löscht verwaiste Dateien älter als max_age_days"""
        orphaned = self._find_orphaned_files()
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for orphan in orphaned:
            if orphan['modified'] < cutoff_date:
                try:
                    os.remove(orphan['path'])
                    deleted_count += 1
                except OSError:
                    pass
        
        return deleted_count
```

### 5. Database-Migrations

- [ ] **Migration erstellen**: Falls neue Certificate-Felder hinzugefügt
- [ ] **Index erstellen**: Performance-Optimierung
- [ ] **Constraints**: Datenbank-Level Validierung

#### Migration-Beispiel:
```python
"""Add certificate indexes for performance

Revision ID: add_certificate_indexes
Revises: previous_migration
Create Date: 2025-08-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Performance-Indexes
    op.create_index('idx_certificates_donation_type', 'certificates', 
                    ['donation_id', 'certificate_type'], unique=True)
    op.create_index('idx_certificates_generated_at', 'certificates', ['generated_at'])
    op.create_index('idx_certificates_file_path', 'certificates', ['file_path'], unique=True)

def downgrade():
    op.drop_index('idx_certificates_file_path', 'certificates')
    op.drop_index('idx_certificates_generated_at', 'certificates')
    op.drop_index('idx_certificates_donation_type', 'certificates')
```

### 6. Monitoring und Logging

- [ ] **Performance-Metrics**: PDF-Generierung Zeit messen
- [ ] **Error-Tracking**: Strukturiertes Logging für Fehler
- [ ] **Statistics**: Anzahl generierte PDFs, Dateisystem-Usage
- [ ] **Health-Checks**: Regelmäßige Konsistenz-Prüfungen

#### Monitoring-Integration:
```python
import logging
import time
from functools import wraps

class PDFGeneratorService:
    
    def __init__(self, app: Optional[Flask] = None):
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'total_generated': 0,
            'total_errors': 0,
            'avg_generation_time': 0
        }
    
    def _track_performance(self, operation_name: str):
        """Decorator für Performance-Tracking"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    
                    # Success-Metrics
                    duration = time.time() - start_time
                    self.stats['total_generated'] += 1
                    
                    # Moving average für Generation-Zeit
                    if self.stats['avg_generation_time'] == 0:
                        self.stats['avg_generation_time'] = duration
                    else:
                        self.stats['avg_generation_time'] = (
                            self.stats['avg_generation_time'] * 0.9 + duration * 0.1
                        )
                    
                    self.logger.info(f"{operation_name} completed in {duration:.2f}s")
                    return result
                    
                except Exception as e:
                    # Error-Metrics
                    duration = time.time() - start_time
                    self.stats['total_errors'] += 1
                    
                    self.logger.error(
                        f"{operation_name} failed after {duration:.2f}s: {str(e)}"
                    )
                    raise
                    
            return wrapper
        return decorator
    
    @_track_performance("Certificate Generation")
    def generate_certificate_atomic(self, donation_id: int, certificate_type: str, 
                                   session_id: Optional[str] = None) -> Certificate:
        # Bestehende Implementierung...
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Performance-Statistiken zurück"""
        return {
            **self.stats,
            'disk_usage': self._get_disk_usage(),
            'certificate_count': Certificate.query.count(),
            'consistency_status': self._quick_consistency_check()
        }
    
    def _get_disk_usage(self) -> Dict[str, int]:
        """Berechnet Speicherverbrauch der PDFs"""
        total_size = 0
        file_count = 0
        
        if os.path.exists(self.base_path):
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
        
        return {
            'total_bytes': total_size,
            'total_mb': total_size / (1024 * 1024),
            'file_count': file_count
        }
```

## Testing

### Database-Integration Tests

- [ ] **Transaction-Tests**: Rollback-Verhalten testen
- [ ] **Consistency-Tests**: Repair-Funktionen validieren
- [ ] **Performance-Tests**: Batch-Operations unter Last
- [ ] **Edge-Cases**: Fehlerszenarien und Recovery

#### Test-Beispiele:
```python
# tests/test_pdf_database_integration.py

def test_atomic_certificate_generation_rollback(app, test_donation):
    """Test dass bei Fehlern alles zurückgerollt wird"""
    service = PDFGeneratorService(app)
    
    # Ungültigen Template-Namen verwenden um Fehler zu provozieren
    with pytest.raises(PDFGenerationError):
        service.generate_certificate_atomic(
            test_donation.id, 
            'invalid_certificate_type'
        )
    
    # Prüfen dass kein Certificate-Record erstellt wurde
    certificate = Certificate.query.filter_by(donation_id=test_donation.id).first()
    assert certificate is None
    
    # Prüfen dass keine PDF-Datei existiert
    # (schwierig zu testen ohne den genauen Pfad zu kennen)

def test_consistency_repair(app, orphaned_certificate):
    """Test dass fehlende PDFs regeneriert werden können"""
    manager = CertificateConsistencyManager(PDFGeneratorService(app))
    
    # PDF-Datei löschen aber Certificate-Record behalten
    orphaned_certificate.delete_file()
    
    # Konsistenz prüfen
    results = manager.verify_consistency()
    assert len(results['missing_files']) == 1
    
    # Reparieren
    repair_results = manager.repair_missing_files(results['missing_files'])
    assert repair_results['repaired'] == 1
    
    # Nach Reparatur sollte Datei wieder existieren
    assert orphaned_certificate.exists_on_disk
```

## Performance-Überlegungen

### Optimierungen:
- [ ] **Database-Indexes**: Für häufige Queries
- [ ] **Batch-Size-Tuning**: Optimale Chunk-Größe finden
- [ ] **Connection-Pooling**: Für High-Load Szenarien
- [ ] **Async-Processing**: Für sehr große Batches

### Monitoring:
- [ ] **Query-Performance**: Slow-Query-Logging
- [ ] **Transaction-Length**: Lange Transaktionen identifizieren
- [ ] **Disk-I/O**: Dateisystem-Performance überwachen

## Nächste Schritte

Nach Abschluss dieser Phase:
1. **Phase 4**: Integration in checkout-erfolg
2. **Monitoring-Setup**: Produktive Überwachung einrichten
3. **Load-Testing**: Performance unter Last testen
4. **Documentation**: API-Dokumentation für Service