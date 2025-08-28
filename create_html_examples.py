#!/usr/bin/env python3
"""
HTML Example Generator für NGÜ Zertifikate
Erstellt HTML-Beispiele statt PDF-Dateien für Design-Review
"""

import os
from datetime import datetime
from decimal import Decimal
from app import app

def create_html_examples():
    """Erstelle HTML-Beispiele für alle Zertifikattypen"""
    
    # Flask-Konfiguration
    app.config['SERVER_NAME'] = 'localhost:5000'
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    with app.test_request_context():
        from flask import render_template
        
        docs_dir = os.path.join(os.getcwd(), 'docs')
        
        # Basis-Context-Daten für alle Templates
        base_context = {
            'background_image_path': '/static/certificates/certificate-background.png'
        }
        
        print("📋 Erstelle HTML-Beispiele für alle Zertifikattypen...")
        
        # 1. Personal Certificate
        print("📄 Generiere Personal Certificate HTML...")
        personal_context = {
            **base_context,
            'donation': type('Donation', (), {
                'amount': Decimal('100.00'),
                'completed_at': datetime.now()
            })(),
            'person_snapshot': {
                'first_name': 'Max',
                'last_name': 'Mustermann'
            },
            'verse': type('Verse', (), {
                'reference': 'Jesaja 43,1',
                'text': 'So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!'
            })(),
            'verses': [type('Verse', (), {
                'reference': 'Jesaja 43,1',
                'text': 'So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!'
            })()] 
        }
        
        html_content = render_template('certificates/personal_certificate.html', **personal_context)
        with open(os.path.join(docs_dir, 'example_personal_certificate.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("  ✅ Gespeichert: example_personal_certificate.html")
        
        # 2. Group Certificate
        print("📄 Generiere Group Certificate HTML...")
        group_context = {
            **base_context,
            'donation': type('Donation', (), {
                'amount': Decimal('100.00'),
                'completed_at': datetime.now(),
                'donation_details': {
                    'group_article': 'Die',
                    'group_name': 'Evangelische Gemeinde Berlin'
                }
            })(),
            'person_snapshot': {
                'first_name': 'Max',
                'last_name': 'Mustermann'
            },
            'verse': type('Verse', (), {
                'reference': 'Jesaja 43,1', 
                'text': 'So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!'
            })(),
            'verses': [type('Verse', (), {
                'reference': 'Jesaja 43,1',
                'text': 'So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!'
            })()],
            'group_article': 'Die',
            'group_name': 'Evangelische Gemeinde Berlin'
        }
        
        html_content = render_template('certificates/group_certificate.html', **group_context)
        with open(os.path.join(docs_dir, 'example_group_certificate.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("  ✅ Gespeichert: example_group_certificate.html")
        
        # 3. Gift Certificate
        print("📄 Generiere Gift Certificate HTML...")
        gift_context = {
            **base_context,
            'donation': type('Donation', (), {
                'amount': Decimal('100.00'),
                'completed_at': datetime.now(),
                'donation_details': {
                    'recipient_first_name': 'Anna',
                    'recipient_last_name': 'Schmidt'
                }
            })(),
            'person_snapshot': {
                'first_name': 'Max',
                'last_name': 'Mustermann'
            },
            'verse': type('Verse', (), {
                'reference': 'Jesaja 43,1',
                'text': 'So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!'
            })(),
            'verses': [type('Verse', (), {
                'reference': 'Jesaja 43,1',
                'text': 'So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!'
            })()],
            'recipient_first_name': 'Anna',
            'recipient_last_name': 'Schmidt'
        }
        
        html_content = render_template('certificates/gift_certificate.html', **gift_context)
        with open(os.path.join(docs_dir, 'example_gift_certificate.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("  ✅ Gespeichert: example_gift_certificate.html")
        
        # 4. Tax Receipt 
        print("📄 Generiere Tax Receipt HTML...")
        tax_context = {
            **base_context,
            'donation': type('Donation', (), {
                'amount': Decimal('100.00'),
                'completed_at': datetime.now()
            })(),
            'person_snapshot': {
                'first_name': 'Max',
                'last_name': 'Mustermann',
                'street': 'Musterstraße',
                'house_number': '123',
                'postal_code': '12345',
                'city': 'Berlin'
            },
            'formatted_amount': '100.00',
            'amount_in_words': 'Einhundert',
            'formatted_date': datetime.now().strftime('%d. %B %Y'),
            'issue_date': datetime.now().strftime('%d. %B %Y'),
            'foundation': {
                'name': 'Peter-Schöffer-Stiftung',
                'street': 'Wormser Weg 17',
                'postal_code': '67574',
                'city': 'Osthofen',
                'tax_number': '07/456/78901',
                'tax_office': 'Finanzamt Worms'
            }
        }
        
        html_content = render_template('certificates/tax_receipt.html', **tax_context)
        with open(os.path.join(docs_dir, 'example_tax_receipt.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("  ✅ Gespeichert: example_tax_receipt.html")
        
        print(f"\n🎉 HTML-Beispiele erstellt!")
        print(f"📁 4 Dateien erstellt in: {docs_dir}")
        print("   • example_personal_certificate.html")
        print("   • example_group_certificate.html") 
        print("   • example_gift_certificate.html")
        print("   • example_tax_receipt.html")
        print("\n💡 Diese HTML-Dateien zeigen das Design und Layout der Zertifikate.")
        print("   Öffne sie in einem Browser um das Aussehen zu prüfen.")

if __name__ == '__main__':
    print("🚀 Starte HTML-Beispiel-Generierung für NGÜ Zertifikate")
    print("=" * 55)
    create_html_examples()