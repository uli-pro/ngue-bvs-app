#!/usr/bin/env python3
"""
Einmaliges Test-Skript: Generiert Storno-PDF und sendet an ue.probst@gmail.com
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from flask import render_template
from pdf_service import PDFGeneratorService
from email_service import email_service
import weasyprint

TEST_EMAIL = "ue.probst@gmail.com"

def generate_test_storno_pdf():
    """Generiert Test-Storno-PDF mit Dummy-Daten"""

    with app.app_context():
        # Hintergrundbild-Pfad mit Timestamp um Caching zu verhindern
        bg_path = os.path.join(os.path.dirname(__file__), "static/certificates/storno-background.png")

        # Dummy-Daten für Test
        test_context = {
            'donor_name': 'Max Mustermann',
            'donor_address': {
                'street': 'Musterstraße 123',
                'postal_code': '12345',
                'city': 'Musterstadt',
                'country': 'Deutschland'
            },
            'original_receipt_number': 'SPE-TEST-001',
            'original_date': '01.12.2025',
            'amount': 100.00,
            'cancellation_reason': 'SEPA-Lastschrift fehlgeschlagen (Testfall)',
            'cancellation_date': datetime.now().strftime('%d.%m.%Y'),
            'verse_references': ['1. Mose 1,1', '1. Mose 1,2', '1. Mose 1,3'],
            'background_image_path': f'file://{bg_path}?v={datetime.now().timestamp()}'
        }

        print(f"📄 Hintergrundbild: {bg_path}")
        print(f"   Existiert: {os.path.exists(bg_path)}")
        if os.path.exists(bg_path):
            print(f"   Größe: {os.path.getsize(bg_path):,} Bytes")
            print(f"   Geändert: {datetime.fromtimestamp(os.path.getmtime(bg_path))}")

        # HTML rendern
        html_content = render_template('certificates/storno_bescheinigung.html', **test_context)

        # PDF generieren
        output_dir = os.path.join(os.path.dirname(__file__), 'certificates', 'test')
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f'test_storno_{timestamp}.pdf')

        html_doc = weasyprint.HTML(string=html_content, base_url=app.static_folder)
        html_doc.write_pdf(target=output_path, presentational_hints=True)

        print(f"✅ PDF generiert: {output_path}")
        return output_path, test_context


def send_test_email(pdf_path: str, storno_context: dict):
    """Sendet Test-E-Mail an ue.probst@gmail.com"""

    with app.app_context():
        email_service.init_app(app)

        # Donation-Daten für E-Mail
        donation_data = {
            'id': 'TEST',
            'total_amount': 100.00,
            'created_at': datetime.now(),
            'person': {
                'first_name': 'Max',
                'last_name': 'Mustermann',
                'email': TEST_EMAIL  # Überschreiben für Test
            }
        }

        print(f"📧 Sende Storno-E-Mail an {TEST_EMAIL}...")

        success = email_service.send_storno_email(
            donation_data=donation_data,
            storno_pdf_path=pdf_path,
            storno_context=storno_context
        )

        if success:
            print(f"✅ E-Mail erfolgreich gesendet an {TEST_EMAIL}!")
        else:
            print(f"❌ E-Mail-Versand fehlgeschlagen!")

        return success


def main():
    print("=" * 60)
    print("🧪 STORNO TEST - E-Mail an ue.probst@gmail.com")
    print("=" * 60)

    # 1. PDF generieren
    pdf_path, context = generate_test_storno_pdf()

    # 2. E-Mail senden
    success = send_test_email(pdf_path, context)

    print("\n" + "=" * 60)
    print(f"{'✅ TEST ERFOLGREICH' if success else '❌ TEST FEHLGESCHLAGEN'}")
    print("=" * 60)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)