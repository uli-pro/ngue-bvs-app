#!/usr/bin/env python3
"""
Test PDF Generator für NGÜ Zertifikate
Erstellt Beispiel-PDFs für alle vier Zertifikattypen
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
import shutil

# Flask app setup
from app import app, db
from models import Person, Verse, Donation, Certificate
from pdf_service import PDFGeneratorService

def create_test_data():
    """Erstelle Test-Daten für die PDF-Generierung"""
    
    # Test Person erstellen
    test_person = Person(
        email="max.mustermann@example.com",
        first_name="Max",
        last_name="Mustermann",
        salutation="Herr",
        street="Musterstraße",
        house_number="123",
        postal_code="12345",
        city="Berlin",
        country="DE"
    )
    
    # Test Vers erstellen
    test_verse = Verse(
        book="Jesaja",
        chapter=43,
        verse=1,
        text="So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!",
        is_sponsored=False,
        positivity_score=95
    )
    
    db.session.add(test_person)
    db.session.add(test_verse)
    db.session.flush()  # Für IDs
    
    # Test Donations für verschiedene Typen erstellen
    donations = []
    
    # 1. Personal Certificate
    personal_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verse.id,
        donation_type='einzelperson',
        amount=Decimal('100.00'),
        payment_status='completed',
        completed_at=datetime.now(),
        person_snapshot=test_person.to_snapshot(),
        privacy_consent=True,
        wants_receipt=True
    )
    
    # 2. Group Certificate  
    group_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verse.id,
        donation_type='gruppe',
        donation_details={
            'group_article': 'Die',
            'group_name': 'Evangelische Gemeinde Berlin'
        },
        amount=Decimal('100.00'),
        payment_status='completed',
        completed_at=datetime.now(),
        person_snapshot=test_person.to_snapshot(),
        privacy_consent=True,
        wants_receipt=False
    )
    
    # 3. Gift Certificate
    gift_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verse.id,
        donation_type='geschenk',
        donation_details={
            'recipient_first_name': 'Anna',
            'recipient_last_name': 'Schmidt'
        },
        amount=Decimal('100.00'),
        payment_status='completed',
        completed_at=datetime.now(),
        person_snapshot=test_person.to_snapshot(),
        privacy_consent=True,
        wants_receipt=False
    )
    
    # 4. Tax Receipt (verwendet personal_donation)
    
    donations.extend([personal_donation, group_donation, gift_donation])
    
    for donation in donations:
        db.session.add(donation)
    
    db.session.commit()
    
    return {
        'einzelperson': personal_donation,
        'gruppe': group_donation, 
        'geschenk': gift_donation,
        'tax_receipt': personal_donation  # Verwendet die gleiche Spende
    }

def generate_test_pdfs():
    """Generiere Test-PDFs für alle Zertifikattypen"""
    
    # Flask-Konfiguration für URL-Generierung
    app.config['SERVER_NAME'] = 'localhost:5000'
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    with app.test_request_context():
        try:
            # Temporäres Verzeichnis für PDFs konfigurieren
            docs_dir = os.path.join(os.getcwd(), 'docs')
            temp_cert_dir = os.path.join(docs_dir, 'temp_certificates')
            
            # Sicherstellen, dass Verzeichnis existiert
            os.makedirs(temp_cert_dir, exist_ok=True)
            
            # Konfiguration überschreiben für Test
            app.config['CERTIFICATE_STORAGE_PATH'] = temp_cert_dir
            
            print("📋 Erstelle Test-Daten...")
            test_donations = create_test_data()
            
            print("🔧 Initialisiere PDF Service...")
            pdf_service = PDFGeneratorService(app)
            
            generated_files = []
            
            # 1. Personal Certificate
            print("📄 Generiere Personal Certificate...")
            try:
                cert = pdf_service.generate_certificate(
                    test_donations['einzelperson'].id,
                    'personal_certificate',
                    'test_session'
                )
                
                # Datei nach docs kopieren
                target_file = os.path.join(docs_dir, 'test_personal_certificate.pdf')
                shutil.copy2(cert.file_path, target_file)
                generated_files.append('test_personal_certificate.pdf')
                print(f"  ✅ Gespeichert: {target_file}")
                
            except Exception as e:
                print(f"  ❌ Fehler: {str(e)}")
            
            # 2. Group Certificate  
            print("📄 Generiere Group Certificate...")
            try:
                cert = pdf_service.generate_certificate(
                    test_donations['gruppe'].id,
                    'group_certificate', 
                    'test_session'
                )
                
                target_file = os.path.join(docs_dir, 'test_group_certificate.pdf')
                shutil.copy2(cert.file_path, target_file)
                generated_files.append('test_group_certificate.pdf')
                print(f"  ✅ Gespeichert: {target_file}")
                
            except Exception as e:
                print(f"  ❌ Fehler: {str(e)}")
            
            # 3. Gift Certificate
            print("📄 Generiere Gift Certificate...")
            try:
                cert = pdf_service.generate_certificate(
                    test_donations['geschenk'].id,
                    'gift_certificate',
                    'test_session'
                )
                
                target_file = os.path.join(docs_dir, 'test_gift_certificate.pdf')  
                shutil.copy2(cert.file_path, target_file)
                generated_files.append('test_gift_certificate.pdf')
                print(f"  ✅ Gespeichert: {target_file}")
                
            except Exception as e:
                print(f"  ❌ Fehler: {str(e)}")
            
            # 4. Tax Receipt
            print("📄 Generiere Tax Receipt...")
            try:
                cert = pdf_service.generate_tax_receipt(
                    test_donations['tax_receipt'].id,
                    'test_session'
                )
                
                target_file = os.path.join(docs_dir, 'test_tax_receipt.pdf')
                shutil.copy2(cert.file_path, target_file)  
                generated_files.append('test_tax_receipt.pdf')
                print(f"  ✅ Gespeichert: {target_file}")
                
            except Exception as e:
                print(f"  ❌ Fehler: {str(e)}")
            
            print(f"\n🎉 Test-PDF-Generierung abgeschlossen!")
            print(f"📁 {len(generated_files)} Dateien erstellt in: {docs_dir}")
            for file in generated_files:
                print(f"   • {file}")
            
            # Cleanup: Temporäres Verzeichnis löschen
            if os.path.exists(temp_cert_dir):
                shutil.rmtree(temp_cert_dir)
                print(f"🧹 Temporäres Verzeichnis bereinigt")
                
        except Exception as e:
            print(f"❌ Kritischer Fehler: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Database cleanup
            try:
                db.session.rollback()
                # Test-Daten löschen falls vorhanden
                db.session.query(Certificate).delete()
                db.session.query(Donation).delete() 
                db.session.query(Verse).delete()
                db.session.query(Person).delete()
                db.session.commit()
                print("🗑️  Test-Daten aus Datenbank entfernt")
            except:
                pass

if __name__ == '__main__':
    print("🚀 Starte Test-PDF-Generierung für NGÜ Zertifikate")
    print("=" * 50)
    
    # Prüfe WeasyPrint Installation
    try:
        import weasyprint
        print("✅ WeasyPrint verfügbar")
    except ImportError as e:
        print("❌ WeasyPrint nicht verfügbar:")
        print(f"   {str(e)}")
        print("   Bitte installiere WeasyPrint System-Dependencies")
        print("   Siehe: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation")
        sys.exit(1)
    
    generate_test_pdfs()