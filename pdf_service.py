# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

"""
PDF Generator Service für NGÜ Bibelvers-Sponsoring App
Generiert Zertifikate und Spendenbescheinigungen mit WeasyPrint
"""

import os
import platform
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Tuple, Any
from contextlib import contextmanager
from functools import wraps

# Setup environment for WeasyPrint on macOS
# On Linux (Docker), libraries are in system path
if platform.system() == "Darwin":
    os.environ['PKG_CONFIG_PATH'] = "/opt/homebrew/lib/pkgconfig"
    os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib"
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = "/opt/homebrew/lib"

import weasyprint
from flask import Flask, render_template, current_app
from sqlalchemy.exc import SQLAlchemyError
from models import db, Donation, Certificate, Person, Verse

# Deutsche Monatsnamen für Datumsformatierung
GERMAN_MONTHS = {
    1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
    5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
}

def format_date_german(dt: datetime) -> str:
    """Formatiert ein Datum im deutschen Format: '03. Dezember 2025'"""
    if dt is None:
        return ''
    return f"{dt.day:02d}. {GERMAN_MONTHS[dt.month]} {dt.year}"

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
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'total_generated': 0,
            'total_errors': 0,
            'avg_generation_time': 0,
            'operations_by_type': {}
        }
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Flask-App initialisieren"""
        app.config.setdefault('CERTIFICATE_STORAGE_PATH', os.path.join(os.getcwd(), 'certificates'))
        app.config.setdefault('PDF_TEMPLATE_PATH', 'templates/certificates')
    
    def _track_performance(self, operation_name: str):
        """Decorator für Performance-Tracking"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                operation_type = kwargs.get('certificate_type', 'unknown')
                
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
                    
                    # Per-Type-Statistiken
                    if operation_type not in self.stats['operations_by_type']:
                        self.stats['operations_by_type'][operation_type] = {
                            'count': 0, 'avg_time': 0, 'errors': 0
                        }
                    
                    type_stats = self.stats['operations_by_type'][operation_type]
                    type_stats['count'] += 1
                    if type_stats['avg_time'] == 0:
                        type_stats['avg_time'] = duration
                    else:
                        type_stats['avg_time'] = type_stats['avg_time'] * 0.9 + duration * 0.1
                    
                    self.logger.info(
                        f"{operation_name} completed in {duration:.2f}s for type {operation_type}"
                    )
                    return result
                    
                except Exception as e:
                    # Error-Metrics
                    duration = time.time() - start_time
                    self.stats['total_errors'] += 1
                    
                    if operation_type not in self.stats['operations_by_type']:
                        self.stats['operations_by_type'][operation_type] = {
                            'count': 0, 'avg_time': 0, 'errors': 0
                        }
                    self.stats['operations_by_type'][operation_type]['errors'] += 1
                    
                    self.logger.error(
                        f"{operation_name} failed after {duration:.2f}s for type {operation_type}: {str(e)}"
                    )
                    raise
                    
            return wrapper
        return decorator
    
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
        
    def generate_certificate(self, donation_id: int, certificate_type: str, 
                            session_id: Optional[str] = None) -> Certificate:
        """
        Generiert PDF-Zertifikat und erstellt Certificate-Record
        
        Args:
            donation_id: ID der Spende
            certificate_type: personal_certificate (unterstützt Donations mit einem oder mehreren Versen)
            session_id: Shopping Cart Session ID für Pfad-Gruppierung
            
        Returns:
            Certificate: Erstellter Certificate-Record mit file_path und filename
            
        Raises:
            PDFGenerationError: Bei Fehlern in der PDF-Erstellung
            FileSystemError: Bei Dateisystem-Problemen
            ValidationError: Bei ungültigen Parametern
        """
        # 1. Parameter validieren
        if not donation_id or certificate_type != 'personal_certificate':
            raise ValidationError(f"Invalid parameters: {donation_id}, {certificate_type}")
        
        # 2. Donation laden
        donation = Donation.query.get(donation_id)
        if not donation:
            raise ValidationError(f"Donation {donation_id} not found")
        
        # Allow 'completed' (card) and 'processing' (SEPA Optimistic Completion)
        if donation.payment_status not in ('completed', 'processing'):
            raise ValidationError(f"Donation {donation_id} not ready for PDF generation (status: {donation.payment_status})")
        
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
    
    def generate_storno_certificate(self, donation_id: int,
                                    cancellation_reason: Optional[str] = None) -> Optional[str]:
        """
        Generiert Storno-PDF für fehlgeschlagene/stornierte Spenden.

        Diese Methode generiert KEIN Certificate-Record, da Stornos keine
        gültigen Zertifikate sind. Sie markiert jedoch donation.storno_generated = True.

        Args:
            donation_id: ID der Spende
            cancellation_reason: Grund für die Stornierung (z.B. "SEPA-Lastschrift fehlgeschlagen")

        Returns:
            str: Pfad zur generierten PDF-Datei oder None bei Fehler

        Note:
            Wird nur für Donations generiert, die:
            - Bereits ein Zertifikat erhalten haben (certificate_sent_at IS NOT NULL)
            - Status 'failed' oder 'disputed' haben
        """
        try:
            donation = Donation.query.get(donation_id)
            if not donation:
                self.logger.error(f"Storno: Donation {donation_id} not found")
                return None

            # Nur für fehlgeschlagene/stornierte Spenden
            if donation.payment_status not in ('failed', 'disputed'):
                self.logger.warning(
                    f"Storno: Donation {donation_id} has status {donation.payment_status}, "
                    f"expected 'failed' or 'disputed'"
                )
                return None

            # Idempotenz: Nur einmal generieren
            if donation.storno_generated:
                self.logger.info(f"Storno already generated for donation {donation_id}")
                # Versuche existierende Datei zu finden
                existing_path = self._find_existing_storno(donation_id)
                return existing_path

            # Pfad generieren
            filename, file_path = self._generate_storno_paths(donation)

            # Context für Template vorbereiten
            context = self._prepare_storno_context(donation, cancellation_reason)

            # HTML rendern
            html_content = render_template('certificates/storno_bescheinigung.html', **context)

            # PDF generieren (nutzt eingebettetes CSS aus Template)
            self._generate_storno_pdf_from_html(html_content, file_path)

            # Donation als storno_generated markieren
            donation.storno_generated = True
            db.session.commit()

            self.logger.info(f"Storno PDF generated for donation {donation_id}: {file_path}")
            return file_path

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to generate storno PDF for donation {donation_id}: {e}")
            return None

    def _generate_storno_paths(self, donation: Donation) -> Tuple[str, str]:
        """Generiert Pfade für Storno-PDF"""
        base_dir = current_app.config['CERTIFICATE_STORAGE_PATH']

        now = datetime.now()
        year_month = f"{now.year}/{now.month:02d}"

        # Storno-Dateien in separatem Unterordner
        directory = os.path.join(base_dir, year_month, "storno")

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"storno_donation_{donation.id:03d}_{timestamp}.pdf"

        file_path = os.path.join(directory, filename)

        os.makedirs(directory, exist_ok=True)

        # Sicherheitsprüfung
        if not os.path.abspath(file_path).startswith(os.path.abspath(base_dir)):
            raise FileSystemError("Invalid file path detected")

        return filename, file_path

    def _find_existing_storno(self, donation_id: int) -> Optional[str]:
        """Sucht nach bereits generierter Storno-PDF"""
        base_dir = current_app.config.get('CERTIFICATE_STORAGE_PATH', '/tmp/certificates')

        # Durchsuche alle storno-Verzeichnisse
        for root, dirs, files in os.walk(base_dir):
            if 'storno' in root:
                for file in files:
                    if file.startswith(f"storno_donation_{donation_id:03d}_"):
                        return os.path.join(root, file)
        return None

    def _prepare_storno_context(self, donation: Donation,
                                cancellation_reason: Optional[str] = None) -> Dict[str, Any]:
        """Bereitet Context für Storno-Template vor"""

        # Person-Daten aus Snapshot (konsistent mit anderen Methoden)
        person_data = donation.person_snapshot or {}
        if not person_data and donation.person:
            person_data = {
                'first_name': donation.person.first_name,
                'last_name': donation.person.last_name,
                'street': donation.person.street,
                'house_number': donation.person.house_number,
                'postal_code': donation.person.postal_code,
                'city': donation.person.city,
                'country': donation.person.country or 'Deutschland'
            }

        # Donor name zusammensetzen (Template erwartet donor_name als String)
        donor_name = f"{person_data.get('first_name', '')} {person_data.get('last_name', '')}".strip()
        if not donor_name:
            donor_name = "Spender/in"

        # Adresse aufbereiten (Template erwartet donor_address dict)
        street = person_data.get('street', '')
        house_number = person_data.get('house_number', '')
        full_street = f"{street} {house_number}".strip() if street else ''

        donor_address = {
            'street': full_street,
            'postal_code': person_data.get('postal_code', ''),
            'city': person_data.get('city', ''),
            'country': person_data.get('country', 'Deutschland')
        }

        # Verse-Referenzen für die Storno-Bescheinigung
        verse_references = []
        for assoc in donation.verse_associations:
            if assoc.verse:
                verse_ref = f"{assoc.verse.book} {assoc.verse.chapter},{assoc.verse.verse}"
                verse_references.append(verse_ref)

        # Stornierungsgrund bestimmen
        if not cancellation_reason:
            if donation.payment_status == 'disputed':
                cancellation_reason = "Lastschrift wurde vom Kontoinhaber widerrufen (Chargeback)"
            else:
                cancellation_reason = donation.failure_reason or "Zahlung fehlgeschlagen"

        # Original-Quittungsnummer (falls vorhanden)
        original_receipt_number = donation.receipt_number or f"SPE-{donation.id:06d}"

        # Original-Datum (Priorität: certificate_sent_at > completed_at > created_at)
        if donation.certificate_sent_at:
            original_date = donation.certificate_sent_at.strftime('%d.%m.%Y')
        elif donation.completed_at:
            original_date = donation.completed_at.strftime('%d.%m.%Y')
        else:
            original_date = donation.created_at.strftime('%d.%m.%Y') if donation.created_at else "unbekannt"

        # Absoluter Pfad für Hintergrundbild (konsistent mit anderen Methoden)
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        background_image_path = os.path.join(static_dir, 'certificates', 'storno-background.png')

        context = {
            # Template-Variablen (passend zu storno_bescheinigung.html)
            'donor_name': donor_name,
            'donor_address': donor_address,
            'original_receipt_number': original_receipt_number,
            'original_date': original_date,
            'amount': donation.total_amount,  # Template nutzt |currency Filter
            'cancellation_reason': cancellation_reason,
            'cancellation_date': datetime.now().strftime('%d.%m.%Y'),
            'verse_references': verse_references,
            'background_image_path': f'file://{background_image_path}',
            # Zusätzlich donation für eventuelle Template-Erweiterungen
            'donation': donation
        }

        return context

    def _generate_storno_pdf_from_html(self, html_content: str, output_path: str):
        """Generiert Storno-PDF aus HTML-Content"""
        try:
            # Storno verwendet das eingebettete CSS aus dem Template
            # (anders als Zertifikate, die externe CSS nutzen)
            html_doc = weasyprint.HTML(string=html_content, base_url=current_app.static_folder)

            html_doc.write_pdf(
                target=output_path,
                font_config=None,
                presentational_hints=True
            )

            os.chmod(output_path, 0o644)

        except Exception as e:
            raise PDFGenerationError(f"Storno PDF generation failed: {str(e)}")

    def generate_tax_receipt_atomic(self, donation_id: int,
                                   session_id: Optional[str] = None) -> Certificate:
        """Atomische Spendenbescheinigung-Generierung"""

        with self._atomic_operation() as created_files:
            # Parameter validieren
            donation = self._validate_donation(donation_id)

            # Prüfen ob Receipt bereits existiert
            existing = Certificate.find_by_donation_and_type(donation_id, 'tax_receipt')
            if existing and existing.exists_on_disk:
                return existing

            # Generate receipt number if not already assigned
            if not donation.receipt_number:
                try:
                    from models import ReceiptCounter
                    receipt_number = ReceiptCounter.get_next_receipt_number(auto_commit=False)
                    donation.receipt_number = receipt_number
                    donation.receipt_issued_at = datetime.utcnow()
                    db.session.flush()  # Flush but don't commit yet (atomic operation handles commit)
                    logging.info(f"Assigned receipt number {receipt_number} to donation {donation_id}")
                except Exception as e:
                    logging.error(f"Failed to generate receipt number: {e}")
                    raise  # Re-raise to trigger rollback

            # Pfade generieren
            filename, file_path = self._generate_certificate_paths(
                donation, 'tax_receipt', session_id
            )
            created_files.append(file_path)

            # PDF generieren
            context = self._prepare_tax_receipt_context(donation)
            html_content = render_template('certificates/tax_receipt.html', **context)
            self._generate_pdf_from_html(html_content, file_path)
            
            # Certificate-Record erstellen
            certificate = Certificate(
                donation_id=donation.id,
                certificate_type='tax_receipt',
                filename=filename,
                file_path=file_path
            )
            
            if not certificate.validate_file_path():
                raise ValidationError(f"Invalid file path: {file_path}")
            
            db.session.add(certificate)
            db.session.flush()
            
            return certificate
    
    def _validate_donation(self, donation_id: int) -> Donation:
        """Validiert Donation für PDF-Generierung"""
        donation = Donation.query.get(donation_id)
        if not donation:
            raise ValidationError(f"Donation {donation_id} not found")
        
        # Allow 'completed' (card) and 'processing' (SEPA Optimistic Completion)
        if donation.payment_status not in ('completed', 'processing'):
            raise ValidationError(f"Donation {donation_id} not ready for PDF generation (status: {donation.payment_status})")
        
        # Prüfen ob Donation alle required fields hat
        if not donation.person_snapshot and not donation.person:
            raise ValidationError(f"No person data for donation {donation_id}")
        
        if not donation.verse_associations:
            raise ValidationError(f"No verses associated with donation {donation_id}")
        
        return donation

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
                    if tax_receipts and donation_id == tax_receipts[-1].donation_id:
                        donation.receipt_generated = True
                        
                except Exception as e:
                    # Einzelnen Donation-Fehler protokollieren aber Chunk fortsetzen
                    current_app.logger.warning(
                        f"Failed to process donation {donation_id}: {str(e)}"
                    )
                    # Bei chunk-internen Fehlern den ganzen Chunk abbrechen
                    raise e
            
            return {
                'certificates': certificates,
                'tax_receipts': tax_receipts
            }

    def _determine_certificate_type(self, donation: Donation) -> str:
        """Alle Donations verwenden personal_certificate Template"""
        return 'personal_certificate'

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
        
        # ALLE Verse der Donation laden und sortieren
        verses = donation.get_verses_sorted()
        
        # Validierung: Prüfen ob Verse gefunden wurden
        if not verses:
            self.logger.error(f"No verses found for donation {donation.id}. "
                            f"verse_associations count: {len(donation.verse_associations)}")
            # Debug-Info über verse_associations
            for i, assoc in enumerate(donation.verse_associations):
                self.logger.error(f"Association {i}: donation_id={assoc.donation_id}, "
                                f"verse_id={assoc.verse_id}, verse={assoc.verse}")
            raise PDFGenerationError(f"No verses found for donation {donation.id}")
        
        self.logger.info(f"PDF generation for donation {donation.id}: {len(verses)} verses found")
        
        # Absoluter Pfad für Hintergrundbild (WeasyPrint benötigt absolute Pfade)
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        background_image_path = os.path.join(static_dir, 'certificates', 'certificate-background.png')
        
        # Determine certificate date:
        # - For completed donations: use completed_at
        # - For SEPA (processing): use current date (Optimistic Completion)
        if donation.completed_at:
            cert_date = donation.completed_at
        else:
            cert_date = datetime.now()  # SEPA: use current date

        # Context für Sammelzertifikat mit mehreren Versen
        context = {
            'donation': donation,
            'person_snapshot': person_data,
            'verses': verses,  # Liste mit ALLEN Versen
            'verse_count': len(verses),
            'is_multiple': len(verses) > 1,
            'background_image_path': f'file://{background_image_path}',
            'formatted_amount': f"{donation.total_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            'formatted_date': format_date_german(cert_date),
            'certificate_title': f"Patenschafts-Zertifikat für {len(verses)} {'Vers' if len(verses) == 1 else 'Verse'}"
        }
        
        return context

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
        
        # Absoluter Pfad für Hintergrundbild (WeasyPrint benötigt absolute Pfade)
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        background_image_path = os.path.join(static_dir, 'certificates', 'spendenbescheinigung-schoeffer.png')
        
        # Verse für Konsistenz hinzufügen
        verses = donation.get_verses_sorted()
        
        context = {
            'donation': donation,
            'person_snapshot': person_data,
            'verses': verses,  # Für Konsistenz mit Certificate-Context
            'verse_count': len(verses),
            'formatted_amount': f"{donation.total_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            'amount_in_words': self._amount_to_words(donation.total_amount),
            'formatted_date': format_date_german(donation.completed_at or donation.created_at),
            'issue_date': format_date_german(datetime.now()),
            'background_image_path': f'file://{background_image_path}',

            # Receipt numbering (legally required per §50 Abs. 1 EStDV)
            'receipt_number': donation.receipt_number or 'AUSSTEHEND',
            'receipt_issued_date': donation.receipt_issued_at.strftime('%d.%m.%Y') if donation.receipt_issued_at else (donation.completed_at.strftime('%d.%m.%Y') if donation.completed_at else ''),

            # Stiftungsdaten (konstant - basierend auf offiziellem Text)
            'foundation': {
                'name': 'Peter-Schoeffer-Stiftung',
                'street': 'Wormser Weg 17',
                'postal_code': '67574',
                'city': 'Osthofen',
                'tax_number': '44/673/08355',
                'tax_office': 'Finanzamt Worms-Kirchheimbolanden'
            }
        }
        
        return context

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
        base_path = current_app.config.get('CERTIFICATE_STORAGE_PATH', '/tmp/certificates')
        total_size = 0
        file_count = 0
        
        if os.path.exists(base_path):
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                        except OSError:
                            pass
        
        return {
            'total_bytes': total_size,
            'total_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count
        }
    
    def _quick_consistency_check(self) -> Dict[str, Any]:
        """Schneller Konsistenz-Check für Monitoring"""
        try:
            total_certs = Certificate.query.count()
            missing_files = 0
            
            # Stichproben-Check (nur die letzten 50 Certificates)
            recent_certs = Certificate.query.order_by(Certificate.generated_at.desc()).limit(50).all()
            for cert in recent_certs:
                if not cert.exists_on_disk:
                    missing_files += 1
            
            return {
                'status': 'ok' if missing_files == 0 else 'degraded' if missing_files < 5 else 'error',
                'total_certificates': total_certs,
                'sample_size': len(recent_certs),
                'missing_files_in_sample': missing_files
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }