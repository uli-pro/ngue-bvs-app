#!/usr/bin/env python3
"""
Einmaliges Backfill-Script für payment_method_type.

Liest CSV mit PaymentIntent-IDs, fragt Stripe API ab, gibt SQL UPDATE-Statements aus.

Verwendung:
    1. CSV aus DB exportieren:
       psql -d ngue_db -c "COPY (SELECT id, stripe_payment_intent_id FROM payment_transactions
           WHERE payment_method_type IS NULL AND stripe_payment_intent_id IS NOT NULL)
           TO STDOUT WITH CSV HEADER" > payment_intents.csv

    2. Script ausführen:
       export STRIPE_SECRET_KEY="sk_live_xxx"
       python backfill_payment_methods.py payment_intents.csv > update_statements.sql

    3. SQL prüfen und ausführen:
       psql -d ngue_db -f update_statements.sql
"""
import csv
import os
import sys
import time
import stripe


def main():
    # 1. Stripe API Key prüfen
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("ERROR: STRIPE_SECRET_KEY nicht gesetzt", file=sys.stderr)
        print("Bitte setzen mit: export STRIPE_SECRET_KEY='sk_live_xxx'", file=sys.stderr)
        sys.exit(1)

    # 2. CSV-Datei als Argument
    if len(sys.argv) < 2:
        print("Usage: python backfill_payment_methods.py <csv_file>", file=sys.stderr)
        print("\nBeispiel:", file=sys.stderr)
        print("  python backfill_payment_methods.py payment_intents.csv", file=sys.stderr)
        sys.exit(1)

    csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"ERROR: Datei nicht gefunden: {csv_file}", file=sys.stderr)
        sys.exit(1)

    # 3. Header für SQL-Output
    print("-- Backfill payment_method_type")
    print("-- Generated from Stripe API")
    print(f"-- Source: {csv_file}")
    print("-- " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("")
    print("BEGIN;")
    print("")

    # Zähler
    total = 0
    updated = 0
    errors = 0
    skipped = 0

    # 4. CSV verarbeiten
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total += 1
            pt_id = row['id']
            pi_id = row['stripe_payment_intent_id']

            # Leere IDs überspringen
            if not pi_id or pi_id.strip() == '':
                print(f"-- SKIP id={pt_id}: Keine PaymentIntent-ID")
                skipped += 1
                continue

            try:
                # Stripe API abfragen (mit latest_charge expandiert - neue API)
                pi = stripe.PaymentIntent.retrieve(pi_id, expand=['latest_charge'])

                # Zahlungsart extrahieren
                payment_type = None

                # Methode 1: latest_charge (neue Stripe API)
                if hasattr(pi, 'latest_charge') and pi.latest_charge:
                    charge = pi.latest_charge
                    if hasattr(charge, 'payment_method_details') and charge.payment_method_details:
                        payment_type = charge.payment_method_details.type

                # Methode 2: Fallback auf payment_method_types
                if not payment_type and hasattr(pi, 'payment_method_types') and pi.payment_method_types:
                    payment_type = pi.payment_method_types[0]

                if payment_type:
                    print(f"UPDATE payment_transactions SET payment_method_type = '{payment_type}' WHERE id = {pt_id};")
                    updated += 1
                else:
                    print(f"-- WARNING: Keine Zahlungsart für id={pt_id} ({pi_id})")
                    skipped += 1

                # Rate Limiting: 0.5s zwischen API-Calls
                time.sleep(0.5)

            except stripe.error.InvalidRequestError as e:
                # PaymentIntent existiert nicht (z.B. Test vs. Live Key)
                print(f"-- SKIP id={pt_id} ({pi_id}): Nicht gefunden (falscher API-Key?)")
                skipped += 1
            except stripe.error.StripeError as e:
                print(f"-- ERROR id={pt_id} ({pi_id}): {e}", file=sys.stderr)
                errors += 1

    # 5. Footer
    print("")
    print("COMMIT;")
    print("")
    print(f"-- Zusammenfassung: {total} verarbeitet, {updated} Updates, {skipped} übersprungen, {errors} Fehler")

    # Status auf stderr
    print(f"\n=== Fertig ===", file=sys.stderr)
    print(f"Verarbeitet: {total}", file=sys.stderr)
    print(f"Updates:     {updated}", file=sys.stderr)
    print(f"Übersprungen: {skipped}", file=sys.stderr)
    print(f"Fehler:      {errors}", file=sys.stderr)


if __name__ == '__main__':
    main()
