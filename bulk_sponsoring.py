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

Zertifikat und Spendenbescheinigung werden über die normale Pipeline erzeugt
(Bulk-Layout: "OBADJA" / "HIOB 2" statt Einzelverse). E-Mails verschickt das
Skript nicht — dafür gibt es den Sende-Knopf im Admin auf der Spendendetailseite.

Seit 09/2026 gibt es dieselbe Funktion im Admin-Panel (/admin/bulk-sponsoring/neu).
Die Fachlogik liegt in bulk_sponsoring_service.py und wird von beiden genutzt;
dieses Skript ist nur noch die Kommandozeilen-Oberfläche dazu.
"""

import json
import os
import re
import sys
from datetime import datetime
from decimal import Decimal

SKRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKRIPT_DIR)

from app import app
from book_names import BOOK_NAMES
from models import db
import bulk_sponsoring_service as bulk
from bulk_sponsoring_service import (  # noqa: F401 — Namen bleiben für Aufrufer erhalten
    BulkSponsoringFehler, buchcode, parse_versangabe, bezeichnung, verteile_betrag, euro,
)

# Protokoll der Eingaben — enthält personenbezogene Daten, siehe .gitignore
EINGABEN_DIR = os.path.join(SKRIPT_DIR, "bulk-eingaben")

BESTAETIGUNGSWORT = "EINTRAGEN"


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
        try:
            return bulk.parse_betrag(frage(text))
        except BulkSponsoringFehler as fehler:
            print(f"  -> {fehler}")


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

# buchcode() und parse_versangabe() kommen aus bulk_sponsoring_service.


def frage_verse():
    """Fragt Vers-/Kapitelangaben ab, bis eine Leerzeile kommt."""
    print()
    print("  Bücher, Kapitel oder Verse eingeben, eine Angabe pro Zeile.")
    print("  Beispiele:  Obadja        (ganzes Buch)")
    print("              Hiob 2        (ganzes Kapitel)")
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
        except BulkSponsoringFehler as fehler:
            print(f"  -> {fehler}")
            continue

        code, kap, von, bis = angaben[-1]
        art = "ganzes Buch" if kap is None else (
            "ganzes Kapitel" if von is None else (f"Vers {von}" if von == bis else f"Verse {von}-{bis}")
        )
        print(f"     ✓ {bezeichnung(angaben[-1])} ({art})")


def zeige_buchcodes():
    eintraege = [f"{code}={name}" for code, name in BOOK_NAMES.items()]
    print()
    for i in range(0, len(eintraege), 4):
        print("     " + "   ".join(f"{e:<18}" for e in eintraege[i:i + 4]))
    print()


# ---------------------------------------------------------------------------
# Fachlogik
# ---------------------------------------------------------------------------

# lade_verse(), verteile_betrag(), baue_kommentar(), euro() liegen im Service.


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

def zeige_vorschau(daten, person_bestand, aenderungen, aufloesung, etiketten, betraege):
    verse = aufloesung.verse
    gesamt = daten["gesamtbetrag"]
    print()
    print("=" * 80)
    print("VORSCHAU — es wurde noch nichts geschrieben")
    print("=" * 80)
    print()
    if person_bestand:
        print(f"  Person: BESTEHEND, ID {person_bestand.id} — die Spende wird ihr zugeordnet.")
        if aenderungen:
            print("    Folgende Felder werden aktualisiert:")
            for feld, alt, neu in aenderungen:
                print(f"      {feld}: {alt!r} -> {neu!r}")
    else:
        print("  Person: NEU angelegt")
    anrede = f"{daten['salutation']} " if daten.get("salutation") else ""
    print(f"    {anrede}{daten['first_name']} {daten['last_name']} <{daten['email']}>")
    print(f"    {daten['street']} {daten['house_number']}, {daten['postal_code']} {daten['city']} ({daten['country']})")
    print(f"    Newsletter: {'ja' if daten['newsletter_consent'] else 'nein'}")
    print()
    print("  Angaben:")
    for name, anzahl, eingetragen in aufloesung.bereiche:
        hinweis = "" if eingetragen == anzahl else f"   ({anzahl - eingetragen} übersprungen, bereits gesponsert)"
        print(f"    {name:<24} {eingetragen:>4} Verse{hinweis}")
    if aufloesung.erschienen:
        print()
        print(f"  WARNUNG: {len(aufloesung.erschienen)} Verse gehören zu einem bereits erschienenen Band")
        print("  und werden im Shop nicht mehr angeboten. Nur fortfahren, wenn das so gewollt ist:")
        print("    " + ", ".join(v.german_reference for v in aufloesung.erschienen))
    print()
    print("  Spende:")
    print(f"    Gesamtbetrag       {euro(gesamt)}")
    print(f"    Verse              {len(verse)} (regulär wären {euro(bulk.REGULAERER_VERSPREIS * len(verse))})")
    print(f"    Tag der Zuwendung  {daten['zuwendungsdatum'].strftime('%d.%m.%Y')}")
    print(f"    Ausstellungsdatum  {daten['ausstellungsdatum'].strftime('%d.%m.%Y')}")
    print(f"    Zahlungsweg        {daten['zahlungsweg']}")
    print(f"    Status             completed, is_bulk_sponsoring=True")
    print(f"    Bescheinigung      wird beim Eintragen vergeben")
    print()
    print("  Zertifikat:")
    print(f"    ... die Übersetzung {bulk.vortext(etiketten)} ermöglicht:")
    for e in etiketten[:bulk.MAX_ETIKETTEN_ZERTIFIKAT]:
        print(f"      {e.text.upper()}")
    if len(etiketten) > bulk.MAX_ETIKETTEN_ZERTIFIKAT:
        print(f"    WARNUNG: {len(etiketten)} Einträge, das Zertifikat zeigt nur {bulk.MAX_ETIKETTEN_ZERTIFIKAT}.")
    print()
    print("  Verse (werden auf 'gesponsert' gesetzt):")
    for vers, betrag in zip(verse, betraege):
        print(f"    {vers.german_reference:<20} {euro(betrag):>12}")
    print(f"    {'SUMME':<20} {euro(sum(betraege)):>12}")
    print()
    print("  Danach werden Spendenbescheinigung und Zertifikat als PDF erzeugt.")
    print("  Nicht angelegt: PaymentTransaction, E-Mails (Versand über den Admin).")
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

        # --- Verse auflösen (bereits gesponserte werden übersprungen) --------
        try:
            aufloesung = bulk.loese_verse_auf(daten["versangaben"])
        except BulkSponsoringFehler as fehler:
            raise SystemExit(f"\nABBRUCH: {fehler}")

        betraege = verteile_betrag(daten["gesamtbetrag"], len(aufloesung.verse))
        person_bestand, aenderungen = bulk.person_vorschau(daten)
        etiketten = bulk.etiketten_fuer_verse(aufloesung.verse)

        # --- Vorschau und Bestätigung -------------------------------------
        zeige_vorschau(daten, person_bestand, aenderungen, aufloesung, etiketten, betraege)

        if not ladepfad:
            pfad = speichere_eingaben(daten)
            print(f"\nEingaben protokolliert: {pfad}")

        if dry_run:
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
            print("\nAbgebrochen — nichts geschrieben.")
            return

        # --- Schreiben: eine Transaktion, Bescheinigungsnummer inklusive ------
        try:
            donation, receipt_number, _ = bulk.erstelle_bulk_sponsoring(
                daten, aufloesung, admin_email="bulk_sponsoring.py (CLI)"
            )
            db.session.commit()
        except Exception as fehler:  # noqa: BLE001
            db.session.rollback()
            raise SystemExit(f"\nFEHLER beim Eintragen, nichts geschrieben: {type(fehler).__name__}: {fehler}")

        donation_id = donation.id
        print()
        print("=" * 80)
        print(f"EINGETRAGEN. Donation-ID {donation_id}, Bescheinigung {receipt_number}")
        print("=" * 80)

        # --- PDFs über die normale Pipeline (nach dem Commit) -----------------
        print("\nErzeuge Spendenbescheinigung und Zertifikat ...")
        dokumente = bulk.erzeuge_dokumente(app, donation_id)
        if dokumente["bescheinigung"]:
            print(f"  Bescheinigung: {dokumente['bescheinigung'].file_path}")
        if dokumente["zertifikat"]:
            print(f"  Zertifikat:    {dokumente['zertifikat'].file_path}")
        for fehler in dokumente["fehler"]:
            print(f"  FEHLGESCHLAGEN: {fehler}")
            print("  -> im Admin auf der Spendendetailseite neu generieren.")

        print()
        print("Nächste Schritte (nicht automatisch erledigt):")
        print(f"  - Im Admin Spende #{donation_id} öffnen, beide PDFs prüfen")
        print("  - Dort die persönliche Mail mit beiden Anhängen senden")


if __name__ == "__main__":
    argumente = sys.argv[1:]
    pfad = None
    if "--load" in argumente:
        stelle = argumente.index("--load")
        if stelle + 1 >= len(argumente):
            raise SystemExit("--load braucht einen Dateipfad.")
        pfad = argumente[stelle + 1]
    try:
        main(dry_run="--dry-run" in argumente, ladepfad=pfad)
    except Abbruch as fehler:
        print(f"\n{fehler}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
        sys.exit(1)
