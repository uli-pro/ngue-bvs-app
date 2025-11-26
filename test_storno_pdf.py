#!/usr/bin/env python3
"""
Test-Skript für Storno-PDF-Generierung
Testet die generate_storno_certificate() Methode für Donation #4
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Donation
from pdf_service import PDFGeneratorService

def test_storno_generation(donation_id: int = 4):
    """Testet Storno-PDF-Generierung für eine Donation"""

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

        # 2. Status temporär auf 'failed' setzen (für Test)
        original_status = donation.payment_status
        if donation.payment_status == 'completed':
            print(f"\n⚠️  Status ist 'completed' - setze temporär auf 'failed' für Test...")
            donation.payment_status = 'failed'
            donation.failure_reason = "SEPA-Lastschrift fehlgeschlagen (Test)"
            db.session.commit()
            print(f"   Neuer Status: {donation.payment_status}")

        # 3. PDF-Service initialisieren
        pdf_service = PDFGeneratorService(app)

        # 4. Storno-PDF generieren
        print(f"\n🔄 Generiere Storno-PDF...")
        storno_path = pdf_service.generate_storno_certificate(
            donation_id=donation_id,
            cancellation_reason="SEPA-Lastschrift fehlgeschlagen (Testfall)"
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

        # 5. Donation-Status prüfen
        db.session.refresh(donation)
        print(f"\n📊 Donation nach Generierung:")
        print(f"   storno_generated: {donation.storno_generated}")
        print(f"   failure_reason: {donation.failure_reason}")

        # 6. Optional: Status zurücksetzen
        reset = input("\n🔄 Status auf 'completed' zurücksetzen? (j/n): ")
        if reset.lower() == 'j':
            donation.payment_status = 'completed'
            donation.storno_generated = False  # Reset für erneuten Test
            donation.failure_reason = None
            db.session.commit()
            print("✅ Status zurückgesetzt auf 'completed'")

        return storno_path is not None

if __name__ == "__main__":
    donation_id = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    success = test_storno_generation(donation_id)
    sys.exit(0 if success else 1)