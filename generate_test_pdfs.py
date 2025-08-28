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
from flask import render_template

def create_test_data():
    """Erstelle Test-Daten für die PDF-Generierung"""
    
    # Existierende Test-Person finden oder erstellen
    test_person = Person.query.filter_by(email="max.mustermann@example.com").first()
    if not test_person:
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
        db.session.add(test_person)
        db.session.flush()
    
    # Test-Verse erstellen oder finden (Einzelvers + Mehrfachverse)
    test_verses = []
    
    # Vers 1: Jesaja 43,1
    verse1 = Verse.query.filter_by(book="JESAJA", chapter=43, verse=1).first()
    if not verse1:
        verse1 = Verse(
            book="JESAJA",
            chapter=43,
            verse=1,
            text="So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!",
            is_sponsored=False,
            positivity_score=95
        )
        db.session.add(verse1)
    test_verses.append(verse1)
    
    # Vers 2: Jeremia 29,11
    verse2 = Verse.query.filter_by(book="JEREMIA", chapter=29, verse=11).first()
    if not verse2:
        verse2 = Verse(
            book="JEREMIA",
            chapter=29,
            verse=11,
            text="Denn ich weiß wohl, was ich für Gedanken über euch habe, spricht der HERR: Gedanken des Friedens und nicht des Leides, dass ich euch gebe das Ende, des ihr wartet.",
            is_sponsored=False,
            positivity_score=92
        )
        db.session.add(verse2)
    test_verses.append(verse2)
    
    # Vers 3: Zefanja 3,17  
    verse3 = Verse.query.filter_by(book="ZEFANJA", chapter=3, verse=17).first()
    if not verse3:
        verse3 = Verse(
            book="ZEFANJA",
            chapter=3,
            verse=17,
            text="Der HERR, dein Gott, ist bei dir, ein starker Heiland. Er wird sich über dich freuen und dir freundlich sein, er wird dir vergeben in seiner Liebe und wird über dich mit Jauchzen fröhlich sein.",
            is_sponsored=False,
            positivity_score=94
        )
        db.session.add(verse3)
    test_verses.append(verse3)
    
    db.session.flush()  # Für IDs
    
    # Test Donations für verschiedene Typen erstellen
    donations = {}
    
    # === EINZELVERS-ZERTIFIKATE ===
    
    # 1. Personal Certificate (Einzelvers)
    personal_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verses[0].id,
        donation_type='einzelperson',
        amount=Decimal('100.00'),
        payment_status='completed',
        completed_at=datetime.now(),
        person_snapshot=test_person.to_snapshot(),
        privacy_consent=True,
        wants_receipt=True
    )
    donations['einzelperson'] = personal_donation
    
    # 2. Group Certificate (Einzelvers)
    group_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verses[0].id,
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
    donations['gruppe'] = group_donation
    
    # 3. Gift Certificate (Einzelvers) - KORRIGIERT: recipient_name statt separate Namen
    gift_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verses[0].id,
        donation_type='geschenk',
        donation_details={
            'recipient_name': 'Anna Schmidt'
        },
        amount=Decimal('100.00'),
        payment_status='completed',
        completed_at=datetime.now(),
        person_snapshot=test_person.to_snapshot(),
        privacy_consent=True,
        wants_receipt=False
    )
    donations['geschenk'] = gift_donation
    
    # === MEHRVERS-ZERTIFIKATE (3 Verse) ===
    
    # 4. Personal Certificate (3 Verse) 
    personal_multi_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verses[0].id,  # Hauptvers
        donation_type='einzelperson',
        amount=Decimal('300.00'),
        payment_status='completed',
        completed_at=datetime.now(),
        person_snapshot=test_person.to_snapshot(),
        privacy_consent=True,
        wants_receipt=True
    )
    donations['einzelperson_multi'] = personal_multi_donation
    
    # 5. Group Certificate (3 Verse)
    group_multi_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verses[0].id,  # Hauptvers
        donation_type='gruppe',
        donation_details={
            'group_article': 'Die',
            'group_name': 'Evangelische Gemeinde Berlin'
        },
        amount=Decimal('300.00'),
        payment_status='completed',
        completed_at=datetime.now(),
        person_snapshot=test_person.to_snapshot(),
        privacy_consent=True,
        wants_receipt=False
    )
    donations['gruppe_multi'] = group_multi_donation
    
    # 6. Gift Certificate (3 Verse)
    gift_multi_donation = Donation(
        person_id=test_person.id,
        verse_id=test_verses[0].id,  # Hauptvers
        donation_type='geschenk',
        donation_details={
            'recipient_name': 'Anna Schmidt'
        },
        amount=Decimal('300.00'),
        payment_status='completed',
        completed_at=datetime.now(),
        person_snapshot=test_person.to_snapshot(),
        privacy_consent=True,
        wants_receipt=False
    )
    donations['geschenk_multi'] = gift_multi_donation
    
    # Alle Donations zur Datenbank hinzufügen
    for donation in donations.values():
        db.session.add(donation)
    
    db.session.commit()
    
    # Für Multi-Vers-Zertifikate müssen wir die verses-Liste im Context überschreiben
    # Das machen wir später im pdf_service.py Context
    
    return {
        'einzelperson': donations['einzelperson'],
        'gruppe': donations['gruppe'], 
        'geschenk': donations['geschenk'],
        'einzelperson_multi': donations['einzelperson_multi'],
        'gruppe_multi': donations['gruppe_multi'],
        'geschenk_multi': donations['geschenk_multi'],
        'test_verses': test_verses,  # Für Multi-Vers-Templates
        'tax_receipt': donations['einzelperson']  # Verwendet die gleiche Spende
    }

def generate_multi_verse_certificate(pdf_service, donation_id, certificate_type, verses):
    """Hilfsfunktion für Multi-Vers-Zertifikate"""
    
    # Standard-Zertifikat generieren
    cert = pdf_service.generate_certificate(donation_id, certificate_type, 'test_session')
    
    # Context für Multi-Vers überschreiben 
    donation = Donation.query.get(donation_id)
    context = pdf_service._prepare_certificate_context(donation, certificate_type)
    context['verses'] = verses  # Alle 3 Verse überschreiben
    
    # Template rendern mit erweiterten Versen
    template_name = f"certificates/{certificate_type}.html"
    html_content = render_template(template_name, **context)
    
    # PDF neu generieren mit Multi-Vers-Context
    pdf_service._generate_pdf_from_html(html_content, cert.file_path)
    
    return cert

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
            
            # 4. Multi-Vers Personal Certificate
            print("📄 Generiere Multi-Vers Personal Certificate...")
            try:
                cert = generate_multi_verse_certificate(
                    pdf_service, test_donations['einzelperson_multi'].id, 
                    'personal_certificate', test_donations['test_verses']
                )
                
                target_file = os.path.join(docs_dir, 'test_personal_multi_certificate.pdf')
                shutil.copy2(cert.file_path, target_file)
                generated_files.append('test_personal_multi_certificate.pdf')
                print(f"  ✅ Gespeichert: {target_file}")
                
            except Exception as e:
                print(f"  ❌ Fehler: {str(e)}")
            
            # 5. Multi-Vers Group Certificate  
            print("📄 Generiere Multi-Vers Group Certificate...")
            try:
                cert = generate_multi_verse_certificate(
                    pdf_service, test_donations['gruppe_multi'].id,
                    'group_certificate', test_donations['test_verses']
                )
                
                target_file = os.path.join(docs_dir, 'test_group_multi_certificate.pdf')
                shutil.copy2(cert.file_path, target_file)
                generated_files.append('test_group_multi_certificate.pdf')
                print(f"  ✅ Gespeichert: {target_file}")
                
            except Exception as e:
                print(f"  ❌ Fehler: {str(e)}")
            
            # 6. Multi-Vers Gift Certificate
            print("📄 Generiere Multi-Vers Gift Certificate...")
            try:
                cert = generate_multi_verse_certificate(
                    pdf_service, test_donations['geschenk_multi'].id,
                    'gift_certificate', test_donations['test_verses'] 
                )
                
                target_file = os.path.join(docs_dir, 'test_gift_multi_certificate.pdf')  
                shutil.copy2(cert.file_path, target_file)
                generated_files.append('test_gift_multi_certificate.pdf')
                print(f"  ✅ Gespeichert: {target_file}")
                
            except Exception as e:
                print(f"  ❌ Fehler: {str(e)}")
            
            # 7. Tax Receipt
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