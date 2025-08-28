"""
PDF Generator Service für NGÜ Bibelvers-Sponsoring App
Generiert Zertifikate und Spendenbescheinigungen mit WeasyPrint
"""

import os
import platform
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Tuple, Any

# Setup environment for WeasyPrint on macOS
# On Linux (Docker), libraries are in system path
if platform.system() == "Darwin":
    os.environ['PKG_CONFIG_PATH'] = "/opt/homebrew/lib/pkgconfig"
    os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib"
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = "/opt/homebrew/lib"

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
        app.config.setdefault('CERTIFICATE_STORAGE_PATH', os.path.join(os.getcwd(), 'certificates'))
        app.config.setdefault('PDF_TEMPLATE_PATH', 'templates/certificates')
        
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
        
        # Vers laden
        verse = donation.verse
        
        # Basis-Context (basierend auf Phase 1 Template-Struktur)
        context = {
            'donation': donation,
            'person_snapshot': person_data,
            'verse': verse,
            'verses': [verse],  # Als Liste für Template-Kompatibilität
            'background_image_path': '/static/certificates/certificate-background.png',
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
                'tax_number': '07/456/78901',
                'tax_office': 'Finanzamt Worms'
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
                if donation.donation_type == 'einzelperson':
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