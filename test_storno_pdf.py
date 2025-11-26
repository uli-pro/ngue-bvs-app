#!/usr/bin/env python3
"""
Test-Skript für Storno-PDF-Generierung und Storno-E-Mail
Testet die generate_storno_certificate() und send_storno_email() Methoden
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Donation
from pdf_service import PDFGeneratorService
from email_service import email_service


def prepare_donation_data(donation: Donation) -> dict:
    """Bereitet donation_data dict für E-Mail-Service vor (konsistent mit app.py)"""
    return {
        'id': donation.id,
        'total_amount': float(donation.total_amount),
        'created_at': donation.created_at,
        'person': {
            'first_name': donation.person.first_name if donation.person else 'Test',
            'last_name': donation.person.last_name if donation.person else 'User',
            'email': donation.person.email if donation.person else 'test@example.com',
        },
        'verses': [
            {'reference': f"{assoc.verse.book} {assoc.verse.chapter},{assoc.verse.verse}"}
            for assoc in donation.verse_associations if assoc.verse
        ]
    }


def test_storno_generation(donation_id: int = 4, send_email: bool = False):
    """Testet Storno-PDF-Generierung und optional E-Mail-Versand"""

    with app.app_context():
        # 1. Donation laden
        donation = Donation.query.get(donation_id)
        if not donation:
            print(f"❌ Donation #{donation_id} nicht gefunden!")
            return False

        print(f"📋 Donation #{donation_id} geladen:")
        print(f"   Status: {donation.payment_status}")
        print(f"   Betrag: {donation.total_amount} EUR")
        print(f"   Receipt: {donation.receipt_number}")
        print(f"   Storno bereits generiert: {donation.storno_generated}")
        print(f"   Person: {donation.person.first_name} {donation.person.last_name}" if donation.person else "   Person: -")
        print(f"   E-Mail: {donation.person.email}" if donation.person else "   E-Mail: -")

        # 2. Status temporär auf 'failed' setzen (für Test)
        original_status = donation.payment_status
        original_storno_generated = donation.storno_generated

        if donation.payment_status == 'completed':
            print(f"\n⚠️  Status ist 'completed' - setze temporär auf 'failed' für Test...")
            donation.payment_status = 'failed'
            donation.failure_reason = "SEPA-Lastschrift fehlgeschlagen (Test)"
            donation.storno_generated = False  # Reset für Test
            db.session.commit()
            print(f"   Neuer Status: {donation.payment_status}")

        # 3. PDF-Service initialisieren
        pdf_service = PDFGeneratorService(app)

        # 4. Storno-Context vorbereiten (für E-Mail)
        cancellation_reason = "SEPA-Lastschrift fehlgeschlagen (Testfall)"
        storno_context = pdf_service._prepare_storno_context(donation, cancellation_reason)

        print(f"\n📄 Storno-Context vorbereitet:")
        print(f"   original_receipt_number: {storno_context.get('original_receipt_number')}")
        print(f"   original_date: {storno_context.get('original_date')}")
        print(f"   cancellation_reason: {storno_context.get('cancellation_reason')}")
        print(f"   verse_references: {storno_context.get('verse_references')}")

        # 5. Storno-PDF generieren
        print(f"\n🔄 Generiere Storno-PDF...")
        storno_path = pdf_service.generate_storno_certificate(
            donation_id=donation_id,
            cancellation_reason=cancellation_reason
        )

        if storno_path:
            print(f"✅ Storno-PDF erfolgreich generiert!")
            print(f"   Pfad: {storno_path}")
            print(f"   Datei existiert: {os.path.exists(storno_path)}")
            if os.path.exists(storno_path):
                file_size = os.path.getsize(storno_path)
                print(f"   Dateigröße: {file_size:,} Bytes")
        else:
            print(f"❌ Storno-PDF-Generierung fehlgeschlagen!")
            return False

        # 6. Donation-Status prüfen
        db.session.refresh(donation)
        print(f"\n📊 Donation nach PDF-Generierung:")
        print(f"   storno_generated: {donation.storno_generated}")
        print(f"   failure_reason: {donation.failure_reason}")

        # 7. Optional: Storno-E-Mail senden
        if send_email:
            print(f"\n📧 Sende Storno-E-Mail...")

            # E-Mail-Service initialisieren
            email_service.init_app(app)

            # Donation-Daten für E-Mail vorbereiten
            donation_data = prepare_donation_data(donation)

            print(f"   Empfänger: {donation_data['person']['email']}")
            print(f"   Anhang: {os.path.basename(storno_path)}")

            try:
                success = email_service.send_storno_email(
                    donation_data=donation_data,
                    storno_pdf_path=storno_path,
                    storno_context=storno_context
                )

                if success:
                    print(f"✅ Storno-E-Mail erfolgreich gesendet!")
                else:
                    print(f"❌ Storno-E-Mail konnte nicht gesendet werden!")
            except Exception as e:
                print(f"❌ Fehler beim E-Mail-Versand: {e}")

        # 8. Optional: Status zurücksetzen
        reset = input("\n🔄 Status auf 'completed' zurücksetzen? (j/n): ")
        if reset.lower() == 'j':
            donation.payment_status = 'completed'
            donation.storno_generated = False  # Reset für erneuten Test
            donation.failure_reason = None
            db.session.commit()
            print("✅ Status zurückgesetzt auf 'completed'")

        return storno_path is not None


def main():
    """Hauptfunktion mit Argument-Parsing"""
    import argparse

    parser = argparse.ArgumentParser(description='Test Storno-PDF und E-Mail')
    parser.add_argument('donation_id', type=int, nargs='?', default=4,
                        help='Donation ID (default: 4)')
    parser.add_argument('--email', '-e', action='store_true',
                        help='Auch Storno-E-Mail senden')

    args = parser.parse_args()

    print("=" * 60)
    print("🧪 STORNO TEST SKRIPT")
    print("=" * 60)
    print(f"   Donation ID: {args.donation_id}")
    print(f"   E-Mail senden: {'Ja' if args.email else 'Nein'}")
    print("=" * 60)

    success = test_storno_generation(
        donation_id=args.donation_id,
        send_email=args.email
    )

    print("\n" + "=" * 60)
    print(f"{'✅ TEST ERFOLGREICH' if success else '❌ TEST FEHLGESCHLAGEN'}")
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()