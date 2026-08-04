"""
Trägt ein Bulk-Sponsoring ein (extern akquirierte Kapitel-/Buch-Patenschaft).

Für Fälle, in denen jemand mehrere Verse zu einem Sonderpreis sponsert — also
nicht 100 € pro Vers über den normalen Checkout, sondern z.B. 1.500 € für zwei
ganze Kapitel. Solche Spenden bekommen is_bulk_sponsoring=True und werden aus
den Tagesreport-Summen herausgerechnet.

Ablauf:
  1. Das Skript zeigt zuerst alle benötigten Angaben und wartet.
  2. Danach fragt es Feld für Feld ab und validiert jede Eingabe sofort.
  3. Es zeigt eine vollständige Vorschau inklusive Bescheinigungsnummer.
  4. Geschrieben wird erst nach expliziter Bestätigung.

Alles läuft in EINER Transaktion. Bei Abbruch oder Fehler wird komplett
zurückgerollt — auch die Bescheinigungsnummer, denn receipt_counters ist eine
normale Tabelle und keine Sequence. Es kann also keine Nummer verloren gehen.

Ausführung lokal (Projekt-Root, venv aktiv):
    python3 bulk_sponsoring.py

    # Probelauf ohne Schreiben (Vorschau, dann garantierter Rollback)
    python3 bulk_sponsoring.py --dry-run

    # Eingaben eines früheren Laufs wiederverwenden
    python3 bulk_sponsoring.py --load bulk-eingaben/<datei>.json

Produktion (Skript liegt im Image, dortige .env wird automatisch genutzt):
    docker exec -it <app-container> python3 /app/bulk_sponsoring.py --dry-run
    docker exec -it <app-container> python3 /app/bulk_sponsoring.py

WICHTIG: Vor dem Produktionslauf einen Datenbank-Dump ziehen.

Die Eingaben werden unter bulk-eingaben/ protokolliert. Dieses Verzeichnis
enthält personenbezogene Spenderdaten und ist deshalb per .gitignore vom Repo
und per .dockerignore vom Image ausgeschlossen.

Die Spendenbescheinigung wird über die normale Pipeline erzeugt — eine einzige
über den vollen Betrag, mit der Nummer aus der Datenbank. So bleibt die
Nummernfolge lückenlos und PDF und Datenbank können nicht auseinanderlaufen.

Das Zertifikat erzeugt das Skript NICHT: dessen Text weicht bei
Kapitel-Patenschaften ab ("Kapitel" statt "Bibelverse"). E-Mails verschickt
es ebenfalls nicht.
"""

import json
import os
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN

SKRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKRIPT_DIR)

from app import app
from book_names import BOOK_NAMES
from models import db, Person, Verse, Donation, DonationVerse, ReceiptCounter, VerseReservation
from pdf_service import PDFGeneratorService

# Protokoll der Eingaben — enthält personenbezogene Daten, siehe .gitignore
EINGABEN_DIR = os.path.join(SKRIPT_DIR, "bulk-eingaben")

BESTAETIGUNGSWORT = "EINTRAGEN"

# Deutscher Buchname (kleingeschrieben, ohne Leerzeichen) -> Buchcode
DEUTSCH_ZU_CODE = {
    name.lower().replace(" ", "").replace(".", ""): code
    for code, name in BOOK_NAMES.items()
}


class Abbruch(Exception):
    """Benutzer hat abgebrochen."""


# ---------------------------------------------------------------------------
# Eingabe-Helfer
# ---------------------------------------------------------------------------

def frage(text, pflicht=True, default=None):
    """Fragt einen Textwert ab. Leere Eingabe -> Default oder erneute Frage."""
    zusatz = f" [{default}]" if default else ""
    while True:
        try:
            wert = input(f"{text}{zusatz}: ").strip()
        except EOFError:
            raise Abbruch("Eingabe abgebrochen.")
        if not wert and default is not None:
            return default
        if wert:
            return wert
        if not pflicht:
            return None
        print("  -> Pflichtangabe, bitte ausfüllen.")


def frage_email(text):
    while True:
        wert = frage(text)
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", wert):
            return wert.lower()
        print("  -> Das sieht nicht nach einer E-Mail-Adresse aus.")


def frage_ja_nein(text, default=None):
    hinweis = {True: " [j]", False: " [n]", None: " (j/n)"}[default]
    while True:
        try:
            wert = input(f"{text}{hinweis}: ").strip().lower()
        except EOFError:
            raise Abbruch("Eingabe abgebrochen.")
        if not wert and default is not None:
            return default
        if wert in ("j", "ja", "y", "yes"):
            return True
        if wert in ("n", "nein", "no"):
            return False
        print("  -> Bitte j oder n eingeben.")


def frage_datum(text):
    while True:
        wert = frage(f"{text} (TT.MM.JJJJ)")
        try:
            return datetime.strptime(wert, "%d.%m.%Y")
        except ValueError:
            print("  -> Ungültiges Datum. Format: 24.07.2026")


def frage_betrag(text):
    while True:
        wert = frage(text).replace("€", "").replace(" ", "")
        # Deutsche Schreibweise 1.500,00 -> 1500.00
        if "," in wert:
            wert = wert.replace(".", "").replace(",", ".")
        try:
            betrag = Decimal(wert).quantize(Decimal("0.01"))
        except InvalidOperation:
            print("  -> Kein gültiger Betrag. Beispiel: 1500 oder 1.500,00")
            continue
        if betrag <= 0:
            print("  -> Der Betrag muss größer als 0 sein.")
            continue
        if betrag > Decimal("999999.99"):
            print("  -> Betrag zu groß (Feld erlaubt max. 999.999,99).")
            continue
        return betrag


def frage_plz(text):
    while True:
        wert = frage(text)
        if re.fullmatch(r"\d{4,5}", wert):
            return wert
        print("  -> PLZ muss aus 4 oder 5 Ziffern bestehen.")


def frage_anrede():
    erlaubt = ["Herr", "Frau", "Eheleute", "Familie", "Ohne"]
    print(f"  Mögliche Anreden: {', '.join(erlaubt)}")
    while True:
        wert = frage("Anrede", default="Herr")
        treffer = [a for a in erlaubt if a.lower() == wert.lower()]
        if treffer:
            return None if treffer[0] == "Ohne" else treffer[0]
        print(f"  -> Bitte eine aus: {', '.join(erlaubt)}")


# ---------------------------------------------------------------------------
# Vers-Eingabe
# ---------------------------------------------------------------------------

def buchcode(eingabe):
    """Wandelt 'JOB', 'Hiob', '1. Mose' usw. in den Buchcode um. None wenn unbekannt."""
    roh = eingabe.strip()
    if roh.upper() in BOOK_NAMES:
        return roh.upper()
    return DEUTSCH_ZU_CODE.get(roh.lower().replace(" ", "").replace(".", ""))


def parse_versangabe(zeile):
    """Zerlegt eine Zeile in (buchcode, kapitel, von, bis).

    von/bis sind None, wenn das ganze Kapitel gemeint ist.

    Erlaubt:  JOB 2        Hiob 2        (ganzes Kapitel)
              JOB 2,1-13   Hiob 2,1-13   (Versbereich)
              JOB 2,5      Hiob 2,5      (einzelner Vers)
    """
    muster = re.fullmatch(
        r"(?P<buch>[^\d,]+(?:\d\.?\s*\w+)?)\s+(?P<kap>\d+)"
        r"(?:\s*,\s*(?P<von>\d+)(?:\s*-\s*(?P<bis>\d+))?)?",
        zeile.strip(),
    )
    if not muster:
        # Bücher wie "1. Mose" / "1SA" beginnen mit einer Ziffer
        muster = re.fullmatch(
            r"(?P<buch>\d\.?\s*\S+|\dCH|\dKI|\dSA)\s+(?P<kap>\d+)"
            r"(?:\s*,\s*(?P<von>\d+)(?:\s*-\s*(?P<bis>\d+))?)?",
            zeile.strip(),
        )
    if not muster:
        raise ValueError("Format nicht erkannt. Beispiele: 'Hiob 2', 'JOB 2,1-13', 'MAL 4,3'")

    code = buchcode(muster.group("buch"))
    if not code:
        raise ValueError(f"Unbekanntes Buch: {muster.group('buch').strip()!r}")

    kapitel = int(muster.group("kap"))
    von = int(muster.group("von")) if muster.group("von") else None
    bis = int(muster.group("bis")) if muster.group("bis") else von

    if von is not None and bis < von:
        raise ValueError(f"Versbereich verkehrt herum: {von}-{bis}")

    return code, kapitel, von, bis


def frage_verse():
    """Fragt Vers-/Kapitelangaben ab, bis eine Leerzeile kommt."""
    print()
    print("  Verse oder ganze Kapitel eingeben, eine Angabe pro Zeile.")
    print("  Beispiele:  Hiob 2        (ganzes Kapitel)")
    print("              JOB 2,1-13    (Versbereich)")
    print("              Maleachi 4,3  (einzelner Vers)")
    print("  Leere Zeile beendet die Eingabe, '?' zeigt alle Buchcodes.")
    print()

    angaben = []
    while True:
        try:
            zeile = input("  > ").strip()
        except EOFError:
            raise Abbruch("Eingabe abgebrochen.")

        if not zeile:
            if angaben:
                return angaben
            print("  -> Mindestens eine Angabe wird benötigt.")
            continue

        if zeile == "?":
            zeige_buchcodes()
            continue

        try:
            angaben.append(parse_versangabe(zeile))
        except ValueError as fehler:
            print(f"  -> {fehler}")
            continue

        code, kap, von, bis = angaben[-1]
        bereich = "ganzes Kapitel" if von is None else (
            f"Vers {von}" if von == bis else f"Verse {von}-{bis}"
        )
        print(f"     ✓ {BOOK_NAMES[code]} {kap} ({bereich})")


def zeige_buchcodes():
    eintraege = [f"{code}={name}" for code, name in BOOK_NAMES.items()]
    print()
    for i in range(0, len(eintraege), 4):
        print("     " + "   ".join(f"{e:<18}" for e in eintraege[i:i + 4]))
    print()


# ---------------------------------------------------------------------------
# Fachlogik
# ---------------------------------------------------------------------------

def lade_verse(angaben):
    """Löst die Versangaben gegen die Datenbank auf. Wirft bei Problemen."""
    verse = []
    gesehen = set()

    for code, kapitel, von, bis in angaben:
        abfrage = Verse.query.filter_by(book=code, chapter=kapitel)
        if von is not None:
            abfrage = abfrage.filter(Verse.verse >= von, Verse.verse <= bis)
        treffer = abfrage.order_by(Verse.verse).all()

        bezeichnung = f"{BOOK_NAMES[code]} {kapitel}" + (
            "" if von is None else (f",{von}" if von == bis else f",{von}-{bis}")
        )

        if not treffer:
            raise ValueError(f"Keine Verse gefunden für {bezeichnung}.")

        if von is not None:
            erwartet = bis - von + 1
            if len(treffer) != erwartet:
                gefunden = ", ".join(str(v.verse) for v in treffer)
                raise ValueError(
                    f"{bezeichnung}: {erwartet} Verse erwartet, {len(treffer)} gefunden "
                    f"(vorhanden: {gefunden}). Kapitel hat vermutlich weniger Verse."
                )

        for vers in treffer:
            if vers.id in gesehen:
                raise ValueError(f"{vers.german_reference} ist doppelt angegeben.")
            gesehen.add(vers.id)
            verse.append(vers)

    return verse


def verteile_betrag(gesamt, anzahl):
    """Verteilt den Gesamtbetrag centgenau auf n Verse.

    Basisbetrag abgerundet, Restcents auf die ersten Verse verteilt.
    Beispiel 1500,00 € / 19 Verse -> 14x 78,95 € + 5x 78,94 € = 1500,00 €
    """
    cent = Decimal("0.01")
    basis = (gesamt / anzahl).quantize(cent, rounding=ROUND_DOWN)
    rest_cents = int(((gesamt - basis * anzahl) / cent).to_integral_value())

    betraege = [basis + cent if i < rest_cents else basis for i in range(anzahl)]
    assert sum(betraege) == gesamt, f"Verteilung ergibt {sum(betraege)}, erwartet {gesamt}"
    return betraege


def baue_kommentar(daten, verse, receipt_number, gesamt):
    """Interner Kommentar an der Spende (donations.admin_comment)."""
    regulaer = Decimal(100) * len(verse)
    referenzen = ", ".join(v.german_reference for v in verse)
    zeilen = [
        "BULK-SPONSORING — extern akquirierte Kapitel-/Buch-Patenschaft.",
        f"Gesamtbetrag: {euro(gesamt)} für {len(verse)} Verse "
        f"(regulär wären {euro(regulaer)}). Deshalb is_bulk_sponsoring=True "
        "und aus den Tagesreport-Summen herausgerechnet.",
        f"Verse: {referenzen}",
        f"Spendenbescheinigung: EINE über den vollen Betrag von {euro(gesamt)}, "
        f"Nr. {receipt_number}. Keine Einzelbescheinigungen je Vers — die Beträge "
        "auf den donation_verses sind nur die rechnerische Aufteilung innerhalb "
        "dieser einen Spende.",
        f"Zahlungsweg: {daten['zahlungsweg']} (kein Stripe-Vorgang, "
        "daher keine PaymentTransaction).",
        f"Tag der Zuwendung: {daten['zuwendungsdatum'].strftime('%d.%m.%Y')}, "
        f"Bescheinigung ausgestellt am {daten['ausstellungsdatum'].strftime('%d.%m.%Y')}.",
        "Spendenbescheinigung über die normale Pipeline erzeugt (Certificate-Record "
        "vorhanden). Zertifikat wird manuell erstellt, da der Text bei "
        "Kapitel-Patenschaften abweicht.",
        "Kein automatischer E-Mail-Versand.",
    ]
    if daten.get("notiz"):
        zeilen.append(f"Notiz: {daten['notiz']}")
    return "\n".join(zeilen)


def euro(betrag):
    """1500.00 -> '1.500,00 €'"""
    return f"{betrag:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


# ---------------------------------------------------------------------------
# Ein-/Ausgabe der Eingabedaten
# ---------------------------------------------------------------------------

FELDER_UEBERSICHT = """
================================================================================
BULK-SPONSORING EINTRAGEN
================================================================================

Diese Angaben werden benötigt — bitte vorher bereitlegen:

  SPENDER
    - E-Mail-Adresse            (Pflicht, dient als eindeutiger Schlüssel)
    - Anrede                    (Herr / Frau / Eheleute / Familie / Ohne)
    - Vorname, Nachname
    - Straße, Hausnummer
    - PLZ, Ort, Land            (Land als 2 Buchstaben, z.B. DE)
    - Newsletter-Einwilligung   (j/n)

  SPENDE
    - Gesponserte Verse         (ganze Kapitel oder Versbereiche,
                                 z.B. "Hiob 2" oder "JOB 2,1-13")
    - Gesamtbetrag in Euro      (der tatsächlich gezahlte Sonderpreis)
    - Tag der Zuwendung         (Geldeingang — steht auf der Bescheinigung)
    - Ausstellungsdatum         (Datum auf der Bescheinigung, meist heute)
    - Zahlungsweg               (z.B. Überweisung)
    - Notiz                     (optional, kommt in den Admin-Kommentar)

Die Spendenbescheinigungsnummer wird automatisch gezogen — nicht selbst wählen.

WICHTIG: Vor einem Produktionslauf einen Datenbank-Dump ziehen.

================================================================================
"""


def erfasse_daten():
    print(FELDER_UEBERSICHT)
    try:
        input("ENTER drücken, sobald alle Angaben bereitliegen (Strg+C bricht ab) ... ")
    except EOFError:
        raise Abbruch("Eingabe abgebrochen.")

    print("\n--- Spender ---")
    daten = {
        "email": frage_email("E-Mail"),
        "salutation": frage_anrede(),
        "first_name": frage("Vorname"),
        "last_name": frage("Nachname"),
        "street": frage("Straße"),
        "house_number": frage("Hausnummer"),
        "postal_code": frage_plz("PLZ"),
        "city": frage("Ort"),
        "country": frage("Land (2 Buchstaben)", default="DE").upper(),
        "newsletter_consent": frage_ja_nein("Newsletter-Einwilligung", default=False),
    }

    print("\n--- Spende ---")
    daten["versangaben"] = frage_verse()
    daten["gesamtbetrag"] = frage_betrag("Gesamtbetrag in Euro")
    daten["zuwendungsdatum"] = frage_datum("Tag der Zuwendung (Geldeingang)")
    daten["ausstellungsdatum"] = frage_datum("Ausstellungsdatum der Bescheinigung")
    daten["zahlungsweg"] = frage("Zahlungsweg", default="Überweisung")
    daten["notiz"] = frage("Notiz (optional, leer lassen möglich)", pflicht=False)

    return daten


def speichere_eingaben(daten):
    """Legt die Eingaben als JSON ab — als Protokoll und zum Wiederholen."""
    os.makedirs(EINGABEN_DIR, exist_ok=True)
    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = re.sub(r"[^a-z0-9]+", "-", daten["last_name"].lower()).strip("-")
    pfad = os.path.join(EINGABEN_DIR, f"{stempel}-{name}.json")

    serialisierbar = dict(daten)
    serialisierbar["gesamtbetrag"] = str(daten["gesamtbetrag"])
    serialisierbar["zuwendungsdatum"] = daten["zuwendungsdatum"].strftime("%d.%m.%Y")
    serialisierbar["ausstellungsdatum"] = daten["ausstellungsdatum"].strftime("%d.%m.%Y")
    serialisierbar["versangaben"] = [list(a) for a in daten["versangaben"]]

    with open(pfad, "w", encoding="utf-8") as datei:
        json.dump(serialisierbar, datei, ensure_ascii=False, indent=2)
    return pfad


def lade_eingaben(pfad):
    with open(pfad, encoding="utf-8") as datei:
        roh = json.load(datei)
    roh["gesamtbetrag"] = Decimal(roh["gesamtbetrag"])
    roh["zuwendungsdatum"] = datetime.strptime(roh["zuwendungsdatum"], "%d.%m.%Y")
    roh["ausstellungsdatum"] = datetime.strptime(roh["ausstellungsdatum"], "%d.%m.%Y")
    roh["versangaben"] = [tuple(a) for a in roh["versangaben"]]
    return roh


# ---------------------------------------------------------------------------
# Vorschau und Ausführung
# ---------------------------------------------------------------------------

def zeige_vorschau(daten, person, ist_neu, verse, betraege, receipt_number, kommentar):
    gesamt = daten["gesamtbetrag"]
    print()
    print("=" * 80)
    print("VORSCHAU — es wurde noch nichts geschrieben")
    print("=" * 80)
    print()
    print(f"  Person ({'NEU angelegt' if ist_neu else f'BESTEHEND, ID {person.id} — Daten werden aktualisiert'}):")
    anrede = f"{person.salutation} " if person.salutation else ""
    print(f"    {anrede}{person.first_name} {person.last_name} <{person.email}>")
    print(f"    {person.street} {person.house_number}, {person.postal_code} {person.city} ({person.country})")
    print(f"    Newsletter: {'ja' if person.newsletter_consent else 'nein'}")
    print()
    print("  Spende:")
    print(f"    Gesamtbetrag       {euro(gesamt)}")
    print(f"    Verse              {len(verse)} (regulär wären {euro(Decimal(100) * len(verse))})")
    print(f"    Tag der Zuwendung  {daten['zuwendungsdatum'].strftime('%d.%m.%Y')}")
    print(f"    Ausstellungsdatum  {daten['ausstellungsdatum'].strftime('%d.%m.%Y')}")
    print(f"    Zahlungsweg        {daten['zahlungsweg']}")
    print(f"    Status             completed, is_bulk_sponsoring=True")
    print(f"    Bescheinigung      {receipt_number}   <-- wird verbraucht")
    print()
    print("  Verse (werden auf 'gesponsert' gesetzt):")
    for vers, betrag in zip(verse, betraege):
        print(f"    {vers.german_reference:<20} {euro(betrag):>12}")
    print(f"    {'SUMME':<20} {euro(sum(betraege)):>12}")
    print()
    print("  Admin-Kommentar:")
    for zeile in kommentar.splitlines():
        print(f"    {zeile}")
    print()
    print("  Danach wird die Spendenbescheinigung als PDF erzeugt (eine, über den")
    print("  vollen Betrag) und ein Certificate-Record dafür angelegt.")
    print("  Nicht angelegt: Zertifikat-PDF, PaymentTransaction, E-Mails.")
    print("=" * 80)


def main(dry_run, ladepfad):
    # pdf_service lädt das Stylesheet über einen relativen Pfad — deshalb muss
    # das Arbeitsverzeichnis das Projektverzeichnis sein.
    os.chdir(SKRIPT_DIR)

    with app.app_context():
        ziel = app.config["SQLALCHEMY_DATABASE_URI"].split("@")[-1]
        print(f"\nDatenbank: {ziel}")
        if dry_run:
            print("Modus:     DRY-RUN — es wird garantiert nichts geschrieben.")
        print()

        daten = lade_eingaben(ladepfad) if ladepfad else erfasse_daten()
        if ladepfad:
            print(f"Eingaben geladen aus: {ladepfad}")

        # --- Verse auflösen und prüfen -----------------------------------
        verse = lade_verse(daten["versangaben"])

        gesponsert = [v for v in verse if v.is_sponsored]
        if gesponsert:
            referenzen = ", ".join(v.german_reference for v in gesponsert[:8])
            weitere = " ..." if len(gesponsert) > 8 else ""
            raise SystemExit(
                f"\nABBRUCH: {len(gesponsert)} der {len(verse)} Verse sind bereits "
                f"gesponsert:\n  {referenzen}{weitere}\n"
                "Bitte klären, bevor die Spende eingetragen wird."
            )

        # Verse aus erschienenen Bänden werden im Shop nicht mehr angeboten.
        # Eine Patenschaft darauf ist nicht grundsätzlich falsch — sie kann
        # vor dem Erscheinen zugesagt worden sein —, muss aber eine bewusste
        # Entscheidung bleiben, deshalb hier nur eine Warnung.
        erschienen = [v for v in verse if v.is_translated]
        if erschienen:
            referenzen = ", ".join(v.german_reference for v in erschienen[:8])
            weitere = " ..." if len(erschienen) > 8 else ""
            print(
                f"\nWARNUNG: {len(erschienen)} der {len(verse)} Verse gehören zu einem "
                f"bereits erschienenen Band und werden nicht mehr angeboten:\n"
                f"  {referenzen}{weitere}\n"
                "Nur fortfahren, wenn die Patenschaft trotzdem so gewollt ist."
            )

        betraege = verteile_betrag(daten["gesamtbetrag"], len(verse))

        # --- Person -------------------------------------------------------
        bestand = Person.query.filter_by(email=daten["email"]).first()
        ist_neu = bestand is None

        person = Person.find_or_create(daten["email"], **{
            schluessel: daten[schluessel] for schluessel in (
                "first_name", "last_name", "salutation", "street", "house_number",
                "postal_code", "city", "country", "newsletter_consent",
            )
        })
        db.session.flush()

        receipt_number = ReceiptCounter.get_next_receipt_number(auto_commit=False)
        kommentar = baue_kommentar(daten, verse, receipt_number, daten["gesamtbetrag"])

        # --- Spende -------------------------------------------------------
        donation = Donation(
            person_id=person.id,
            person_snapshot=person.to_snapshot(),
            amount=betraege[0],          # Legacy-Feld, wird nirgends ausgewertet
            verse_count=len(verse),
            total_amount=daten["gesamtbetrag"],
            currency="EUR",
            wants_receipt=True,
            privacy_consent=True,
            payment_status="completed",
            certificate_generated=False,  # PDFs werden manuell erzeugt
            receipt_generated=False,
            receipt_number=receipt_number,
            receipt_issued_at=daten["ausstellungsdatum"],
            email_sent=False,             # kein automatischer Versand
            is_bulk_sponsoring=True,
            admin_comment=kommentar,
            created_at=daten["zuwendungsdatum"],
            completed_at=daten["zuwendungsdatum"],
        )
        db.session.add(donation)
        db.session.flush()

        for vers, betrag in zip(verse, betraege):
            db.session.add(DonationVerse(
                donation_id=donation.id,
                verse_id=vers.id,
                amount=betrag,
                created_at=daten["zuwendungsdatum"],
            ))
            vers.is_sponsored = True
            vers.sponsored_at = daten["zuwendungsdatum"]

        VerseReservation.query.filter(
            VerseReservation.verse_id.in_([v.id for v in verse])
        ).delete(synchronize_session=False)

        person.last_donation_at = daten["zuwendungsdatum"]

        # --- Vorschau und Bestätigung -------------------------------------
        zeige_vorschau(daten, person, ist_neu, verse, betraege, receipt_number, kommentar)

        if not ladepfad:
            pfad = speichere_eingaben(daten)
            print(f"\nEingaben protokolliert: {pfad}")

        if dry_run:
            db.session.rollback()
            print("\nDRY-RUN beendet — nichts geschrieben.")
            return

        print()
        try:
            antwort = input(
                f"Zum Schreiben '{BESTAETIGUNGSWORT}' eintippen (alles andere bricht ab): "
            ).strip()
        except EOFError:
            antwort = ""

        if antwort != BESTAETIGUNGSWORT:
            db.session.rollback()
            print("\nAbgebrochen — nichts geschrieben. Die Bescheinigungsnummer bleibt frei.")
            return

        db.session.commit()
        donation_id = donation.id
        print()
        print("=" * 80)
        print(f"EINGETRAGEN. Donation-ID {donation_id}, Bescheinigung {receipt_number}")
        print("=" * 80)

        # --- Spendenbescheinigung erzeugen --------------------------------
        # Über die normale Pipeline, damit die Nummer aus der Datenbank auf dem
        # PDF landet und ein Certificate-Record entsteht. Läuft NACH dem Commit:
        # scheitert die PDF-Erzeugung, bleibt die Spende korrekt eingetragen und
        # das PDF kann nachgezogen werden.
        print("\nErzeuge Spendenbescheinigung ...")
        try:
            dienst = PDFGeneratorService(app)
            beleg = dienst.generate_tax_receipt_atomic(donation_id)
            donation = db.session.get(Donation, donation_id)
            donation.receipt_generated = True
            db.session.commit()
            print(f"  {beleg.file_path}")
        except Exception as fehler:
            print(f"  FEHLGESCHLAGEN: {type(fehler).__name__}: {fehler}")
            print(f"  Die Spende ist eingetragen (ID {donation_id}, {receipt_number}).")
            print("  Die Bescheinigung muss nachträglich erzeugt werden.")

        print()
        print("Nächste Schritte (nicht automatisch erledigt):")
        print("  - Zertifikat-PDF erzeugen (Text weicht bei Kapitel-Patenschaften ab)")
        print("  - Zertifikat und Bescheinigung an den Spender senden")


if __name__ == "__main__":
    argumente = sys.argv[1:]
    pfad = None
    if "--load" in argumente:
        stelle = argumente.index("--load")
        if stelle + 1 >= len(argumente):
            raise SystemExit("FEHLER: --load benötigt einen Dateipfad.")
        pfad = argumente[stelle + 1]
        if not os.path.exists(pfad):
            raise SystemExit(f"FEHLER: Datei nicht gefunden: {pfad}")

    try:
        main(dry_run="--dry-run" in argumente, ladepfad=pfad)
    except Abbruch as fehler:
        print(f"\n{fehler}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nAbgebrochen — nichts geschrieben.")
        sys.exit(1)
    except ValueError as fehler:
        print(f"\nFEHLER: {fehler}")
        sys.exit(1)
