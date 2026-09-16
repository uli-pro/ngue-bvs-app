"""
Fachlogik für Bulk-Sponsoring: extern akquirierte Kapitel-/Buch-Patenschaften
zum Sonderpreis (z.B. 1.750 € für das ganze Buch Obadja statt 100 € pro Vers).

Wird vom Admin-Panel (admin/views.py, Seite "Bulk-Sponsoring") und vom
Kommandozeilen-Skript bulk_sponsoring.py gemeinsam genutzt. Dieses Modul
enthält keine Ein-/Ausgabe und committet nie selbst — der Aufrufer entscheidet.

Ablauf einer Eintragung:
  1. parse_versangaben_text()   Eingabezeilen -> (Buch, Kapitel, von, bis)
  2. loese_verse_auf()          gegen die Datenbank auflösen; bereits gesponserte
                                Verse werden stillschweigend übersprungen
  3. erstelle_bulk_sponsoring() Person, Donation, DonationVerses, Reservierungen,
                                Bescheinigungsnummer — alles in der offenen
                                Transaktion, nur geflusht
  4. (Aufrufer committet)
  5. erzeuge_dokumente()        Spendenbescheinigung und Zertifikat über die
                                normale PDF-Pipeline

Die Beschriftung des Zertifikats ("OBADJA", "HIOB 2", "MALEACHI 4,1-3") wird
aus den Versen der Spende abgeleitet, nicht gespeichert — so funktioniert auch
"Zertifikat neu generieren" im Admin. Regel: ein Kapitel gilt als ganz, wenn
außerhalb der Spende kein sponsorbarer Vers mehr darin übrig ist; ein Buch gilt
als ganz, wenn alle seine Kapitel ganz sind. Wer also "Obadja" einträgt und
zwei Verse davon waren schon vergeben, bekommt trotzdem "OBADJA".
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN

from markupsafe import Markup, escape

from book_names import BOOK_NAMES
from models import db, Person, Verse, Donation, DonationVerse, ReceiptCounter, VerseReservation

# Deutscher Buchname (kleingeschrieben, ohne Leerzeichen/Punkte) -> Buchcode
DEUTSCH_ZU_CODE = {
    name.lower().replace(" ", "").replace(".", ""): code
    for code, name in BOOK_NAMES.items()
}
# Gängige Schreibvarianten, die nicht in BOOK_NAMES stehen (Eingabe wird
# kleingeschrieben und ohne Leerzeichen/Punkte verglichen)
BUCH_ALIASSE = {
    "genesis": "GEN", "exodus": "EXO", "levitikus": "LEV", "leviticus": "LEV",
    "numeri": "NUM", "deuteronomium": "DEU",
    "ruth": "RUT", "esther": "EST", "psalmen": "PSA", "psalms": "PSA",
    "sprichwörter": "PRO", "sprichwoerter": "PRO", "sprueche": "PRO",
    "kohelet": "ECC", "hoheslied": "SNG", "hohelied": "SNG", "hoheslied salomos": "SNG",
    "ezechiel": "EZK", "ezechiël": "EZK", "hesekiel": "EZK",
    "zephanja": "ZEP", "zefanja": "ZEP", "zephania": "ZEP",
    "sacharja": "ZEC", "zacharias": "ZEC", "sacharia": "ZEC",
    "koenige": "1KI",  # bewusst nicht: braucht die Zahl; s.u.
    "1koenige": "1KI", "2koenige": "2KI", "1könige": "1KI", "2könige": "2KI",
    "1kön": "1KI", "2kön": "2KI", "1sam": "1SA", "2sam": "2SA", "1chr": "1CH", "2chr": "2CH",
    "1mo": "GEN", "2mo": "EXO", "3mo": "LEV", "4mo": "NUM", "5mo": "DEU",
    "hi": "JOB", "ps": "PSA", "spr": "PRO", "pred": "ECC", "hld": "SNG", "jes": "ISA",
    "jer": "JER", "klgl": "LAM", "hes": "EZK", "hos": "HOS", "am": "AMO", "ob": "OBA",
    "mi": "MIC", "nah": "NAM", "hab": "HAB", "zef": "ZEP", "hag": "HAG", "sach": "ZEC",
}
del BUCH_ALIASSE["koenige"]
DEUTSCH_ZU_CODE.update({k.replace(" ", "").replace(".", ""): v for k, v in BUCH_ALIASSE.items()})

# Kanonische Reihenfolge der Bücher für die Sortierung der Beschriftung
BUCH_REIHENFOLGE = {code: i for i, code in enumerate(BOOK_NAMES)}

ANREDEN = ("Herr", "Frau", "Eheleute", "Familie")
LAENDER = ("DE", "CH", "AT")
PERSONENFELDER = (
    "first_name", "last_name", "salutation", "street", "house_number",
    "postal_code", "city", "country", "newsletter_consent",
)
REGULAERER_VERSPREIS = Decimal("100")
MAX_ETIKETTEN_ZERTIFIKAT = 10


class BulkSponsoringFehler(ValueError):
    """Fachlicher Fehler mit einer Meldung, die dem Nutzer gezeigt werden kann."""


# ---------------------------------------------------------------------------
# Eingabe-Parser
# ---------------------------------------------------------------------------

def buchcode(eingabe):
    """Wandelt 'JOB', 'Hiob', '1. Mose' usw. in den Buchcode um. None wenn unbekannt."""
    roh = eingabe.strip()
    if roh.upper() in BOOK_NAMES:
        return roh.upper()
    return DEUTSCH_ZU_CODE.get(roh.lower().replace(" ", "").replace(".", ""))


def parse_versangabe(zeile):
    """Zerlegt eine Zeile in (buchcode, kapitel, von, bis).

    kapitel ist None für ein ganzes Buch, von/bis sind None für ein ganzes Kapitel.

    Erlaubt:  Obadja       OBA          (ganzes Buch)
              Hiob 2       JOB 2        (ganzes Kapitel)
              Hiob 2,1-13  JOB 2,1-13   (Versbereich)
              Hiob 2,5     JOB 2,5      (einzelner Vers)
    """
    zeile = zeile.strip()
    muster = re.fullmatch(
        r"(?P<buch>[^\d,]+(?:\d\.?\s*\w+)?)\s+(?P<kap>\d+)"
        r"(?:\s*,\s*(?P<von>\d+)(?:\s*-\s*(?P<bis>\d+))?)?",
        zeile,
    )
    if not muster:
        # Bücher wie "1. Mose" / "1SA" beginnen mit einer Ziffer
        muster = re.fullmatch(
            r"(?P<buch>\d\.?\s*\S+|\dCH|\dKI|\dSA)\s+(?P<kap>\d+)"
            r"(?:\s*,\s*(?P<von>\d+)(?:\s*-\s*(?P<bis>\d+))?)?",
            zeile,
        )
    if not muster:
        code = buchcode(zeile)
        if code:
            return code, None, None, None
        raise BulkSponsoringFehler(
            f"Format nicht erkannt: {zeile!r}. Beispiele: 'Obadja', 'Hiob 2', 'JOB 2,1-13', 'MAL 4,3'"
        )

    code = buchcode(muster.group("buch"))
    if not code:
        raise BulkSponsoringFehler(f"Unbekanntes Buch: {muster.group('buch').strip()!r}")

    kapitel = int(muster.group("kap"))
    von = int(muster.group("von")) if muster.group("von") else None
    bis = int(muster.group("bis")) if muster.group("bis") else von

    if von is not None and bis < von:
        raise BulkSponsoringFehler(f"Versbereich verkehrt herum: {von}-{bis}")

    return code, kapitel, von, bis


def parse_versangaben_text(text):
    """Mehrere Angaben, eine pro Zeile (oder durch ; getrennt). Leere Zeilen werden ignoriert."""
    angaben = []
    for roh in re.split(r"[\n;]", text or ""):
        zeile = roh.strip()
        if zeile:
            angaben.append(parse_versangabe(zeile))
    if not angaben:
        raise BulkSponsoringFehler("Mindestens eine Vers-, Kapitel- oder Buchangabe wird benötigt.")
    return angaben


def bezeichnung(angabe):
    """Lesbare Form einer Angabe: 'Obadja', 'Hiob 2', 'Hiob 2,1-13', 'Maleachi 4,3'."""
    code, kapitel, von, bis = angabe
    name = BOOK_NAMES.get(code, code)
    if kapitel is None:
        return name
    if von is None:
        return f"{name} {kapitel}"
    return f"{name} {kapitel},{von}" if von == bis else f"{name} {kapitel},{von}-{bis}"


def parse_betrag(wert):
    """'1.750,00', '1750', '1750.00' oder Decimal -> Decimal mit 2 Nachkommastellen."""
    if isinstance(wert, Decimal):
        betrag = wert
    else:
        text = str(wert).replace("€", "").replace(" ", "").strip()
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        try:
            betrag = Decimal(text)
        except InvalidOperation:
            raise BulkSponsoringFehler(f"Kein gültiger Betrag: {wert!r}. Beispiel: 1750 oder 1.750,00")
    betrag = betrag.quantize(Decimal("0.01"))
    if betrag <= 0:
        raise BulkSponsoringFehler("Der Betrag muss größer als 0 sein.")
    if betrag > Decimal("999999.99"):
        raise BulkSponsoringFehler("Betrag zu groß (Feld erlaubt max. 999.999,99).")
    return betrag


def parse_datum(wert):
    """'15.09.2026' oder '2026-09-15' oder datetime -> datetime (00:00 Uhr)."""
    if isinstance(wert, datetime):
        return wert
    text = str(wert).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise BulkSponsoringFehler(f"Ungültiges Datum: {wert!r}. Format: 15.09.2026")


# ---------------------------------------------------------------------------
# Verse gegen die Datenbank auflösen
# ---------------------------------------------------------------------------

class Aufloesung:
    """Ergebnis von loese_verse_auf()."""

    def __init__(self):
        self.verse = []          # Verse, die eingetragen werden (sortiert, ohne Doppelte)
        self.uebersprungen = []  # bereits gesponserte Verse (werden stillschweigend übergangen)
        self.erschienen = []     # Verse aus erschienenen Bänden, die trotzdem eingetragen werden
        self.bereiche = []       # (bezeichnung, anzahl_gesamt, anzahl_eingetragen)

    @property
    def angefragt(self):
        return len(self.verse) + len(self.uebersprungen)


def loese_verse_auf(angaben):
    """Löst die Angaben gegen die Datenbank auf.

    Bereits gesponserte Verse werden übersprungen (nicht als Fehler behandelt),
    weil bei Buch-/Kapitelspenden einzelne Verse oft schon über den Shop
    vergeben sind. Wirft BulkSponsoringFehler, wenn eine Angabe keine Verse
    liefert, ein Versbereich unvollständig ist oder am Ende nichts übrig bleibt.
    """
    ergebnis = Aufloesung()
    gesehen = set()

    for angabe in angaben:
        code, kapitel, von, bis = angabe
        abfrage = Verse.query.filter_by(book=code)
        if kapitel is not None:
            abfrage = abfrage.filter_by(chapter=kapitel)
        if von is not None:
            abfrage = abfrage.filter(Verse.verse >= von, Verse.verse <= bis)
        treffer = abfrage.order_by(Verse.chapter, Verse.verse).all()
        name = bezeichnung(angabe)

        if not treffer:
            raise BulkSponsoringFehler(f"Keine Verse gefunden für {name}.")

        if von is not None and len(treffer) != bis - von + 1:
            gefunden = ", ".join(str(v.verse) for v in treffer)
            raise BulkSponsoringFehler(
                f"{name}: {bis - von + 1} Verse erwartet, {len(treffer)} gefunden "
                f"(vorhanden: {gefunden}). Das Kapitel hat vermutlich weniger Verse."
            )

        eingetragen = 0
        for vers in treffer:
            if vers.id in gesehen:
                continue  # Überschneidung zweier Angaben, z.B. "Hiob" und "Hiob 2"
            gesehen.add(vers.id)
            if vers.is_sponsored:
                ergebnis.uebersprungen.append(vers)
                continue
            if vers.is_translated:
                ergebnis.erschienen.append(vers)
            ergebnis.verse.append(vers)
            eingetragen += 1
        ergebnis.bereiche.append((name, len(treffer), eingetragen))

    if not ergebnis.verse:
        raise BulkSponsoringFehler(
            "Alle angegebenen Verse sind bereits gesponsert — es bleibt nichts zum Eintragen."
        )

    ergebnis.verse.sort(key=lambda v: (BUCH_REIHENFOLGE.get(v.book, 999), v.chapter, v.verse))
    return ergebnis


# ---------------------------------------------------------------------------
# Beschriftung (Zertifikat und Mail)
# ---------------------------------------------------------------------------

class Etikett:
    """Ein Eintrag auf dem Zertifikat: art in ('buch', 'kapitel', 'verse')."""

    __slots__ = ("art", "text", "book", "chapter")

    def __init__(self, art, text, book, chapter=None):
        self.art = art
        self.text = text
        self.book = book
        self.chapter = chapter

    def __repr__(self):
        return f"Etikett({self.art!r}, {self.text!r})"

    def __eq__(self, other):
        return isinstance(other, Etikett) and (self.art, self.text) == (other.art, other.text)


def _versbereiche(nummern):
    """[1,2,3,7,9,10] -> '1-3.7.9-10' (Punkt trennt Versgruppen, wie in Bibelstellenangaben üblich)."""
    nummern = sorted(nummern)
    laeufe = []
    start = vorher = nummern[0]
    for n in nummern[1:]:
        if n == vorher + 1:
            vorher = n
            continue
        laeufe.append((start, vorher))
        start = vorher = n
    laeufe.append((start, vorher))
    return ".".join(f"{a}-{b}" if a != b else str(a) for a, b in laeufe)


def beschrifte(verse_keys, kapitel_im_buch, frei_ausserhalb):
    """Reine Funktion: leitet die Zertifikat-Einträge ab.

    verse_keys       Menge von (book, chapter, verse) — die Verse der Spende
    kapitel_im_buch  {book: {chapter, ...}} — alle Kapitel, die es in der DB gibt
    frei_ausserhalb  Menge von (book, chapter, verse) — Verse, die NICHT zur Spende
                     gehören und noch sponsorbar sind

    Ein Kapitel ist ganz, wenn außerhalb der Spende nichts Sponsorbares übrig ist.
    Ein Buch ist ganz, wenn alle seine Kapitel in der Spende vorkommen und ganz sind.
    """
    nach_buch = {}
    for book, chapter, verse in verse_keys:
        nach_buch.setdefault(book, {}).setdefault(chapter, set()).add(verse)

    frei_im_kapitel = set((book, chapter) for book, chapter, _ in frei_ausserhalb)

    etiketten = []
    for book in sorted(nach_buch, key=lambda b: BUCH_REIHENFOLGE.get(b, 999)):
        kapitel = nach_buch[book]
        name = BOOK_NAMES.get(book, book)
        ganz = {c: (book, c) not in frei_im_kapitel for c in kapitel}
        alle_kapitel = kapitel_im_buch.get(book) or set()

        if alle_kapitel and set(kapitel) == set(alle_kapitel) and all(ganz.values()):
            etiketten.append(Etikett("buch", name, book))
            continue

        for c in sorted(kapitel):
            if ganz[c]:
                etiketten.append(Etikett("kapitel", f"{name} {c}", book, c))
            else:
                etiketten.append(Etikett("verse", f"{name} {c},{_versbereiche(kapitel[c])}", book, c))
    return etiketten


def etiketten_fuer_verse(verse):
    """Lädt die nötigen Vergleichsdaten aus der DB und ruft beschrifte() auf.

    Funktioniert vor dem Eintragen (Vorschau) und danach (Zertifikat neu erzeugen):
    die eigenen Verse werden über ihre IDs ausgeschlossen, egal ob sie schon
    als gesponsert markiert sind.
    """
    if not verse:
        return []
    ids = {v.id for v in verse}
    keys = {(v.book, v.chapter, v.verse) for v in verse}
    buecher = {v.book for v in verse}
    kapitel_keys = {(v.book, v.chapter) for v in verse}

    kapitel_im_buch = {}
    for book, chapter in (
        db.session.query(Verse.book, Verse.chapter)
        .filter(Verse.book.in_(buecher)).distinct()
    ):
        kapitel_im_buch.setdefault(book, set()).add(chapter)

    frei = set()
    for vid, book, chapter, versnr in (
        Verse.sponsorable().filter(Verse.book.in_(buecher))
        .with_entities(Verse.id, Verse.book, Verse.chapter, Verse.verse)
    ):
        if vid not in ids and (book, chapter) in kapitel_keys:
            frei.add((book, chapter, versnr))

    return beschrifte(keys, kapitel_im_buch, frei)


def aktive_reservierungen(verse):
    """Anzahl der Verse, die gerade in einem Warenkorb reserviert sind."""
    if not verse:
        return 0
    return VerseReservation.query.filter(
        VerseReservation.verse_id.in_([v.id for v in verse]),
        VerseReservation.expires_at > datetime.utcnow(),
    ).count()


def etiketten_fuer_donation(donation):
    return etiketten_fuer_verse(donation.get_verses_sorted())


def vortext(etiketten):
    """Zeile über der Referenz auf dem Zertifikat: 'des folgenden Buches ermöglicht:' usw."""
    arten = {e.art for e in etiketten}
    einzahl = len(etiketten) == 1
    if arten == {"buch"}:
        return "des folgenden Buches" if einzahl else "der folgenden Bücher"
    if arten == {"kapitel"}:
        return "des folgenden Kapitels" if einzahl else "der folgenden Kapitel"
    if arten == {"verse"}:
        return "des folgenden Bibelabschnitts" if einzahl else "der folgenden Bibelabschnitte"
    if arten == {"buch", "kapitel"}:
        return "der folgenden Bücher und Kapitel"
    return "der folgenden Bibelabschnitte"


def _aufzaehlung(teile):
    if len(teile) == 1:
        return teile[0]
    return ", ".join(teile[:-1]) + " und " + teile[-1]


def beschreibung_fliesstext(etiketten, anzahl_verse):
    """Für die Mail: 'das gesamte Buch Obadja (21 Verse)' /
    'die Kapitel Hiob 2 und Maleachi 4 (zusammen 19 Verse)'."""
    arten = {e.art for e in etiketten}
    texte = [e.text for e in etiketten]
    if arten == {"buch"}:
        kern = ("das gesamte Buch " if len(texte) == 1 else "die Bücher ") + _aufzaehlung(texte)
    elif arten == {"kapitel"}:
        kern = ("das Kapitel " if len(texte) == 1 else "die Kapitel ") + _aufzaehlung(texte)
    elif arten == {"verse"}:
        kern = ("den Abschnitt " if len(texte) == 1 else "die Abschnitte ") + _aufzaehlung(texte)
    else:
        teile = []
        for e in etiketten:
            praefix = {"buch": "das gesamte Buch ", "kapitel": "das Kapitel ", "verse": "den Abschnitt "}[e.art]
            teile.append(praefix + e.text)
        kern = _aufzaehlung(teile)
    verse_text = f"{anzahl_verse} Verse" if anzahl_verse != 1 else "1 Vers"
    if len(etiketten) > 1:
        verse_text = "zusammen " + verse_text
    return f"{kern} ({verse_text})"


# ---------------------------------------------------------------------------
# Betrag, Kommentar, Anrede
# ---------------------------------------------------------------------------

def euro(betrag):
    return f"{betrag:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


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


def baue_kommentar(daten, verse, receipt_number, etiketten, uebersprungen=(), admin_email=None):
    """Interner Kommentar an der Spende (donations.admin_comment)."""
    gesamt = daten["gesamtbetrag"]
    regulaer = REGULAERER_VERSPREIS * len(verse)
    referenzen = ", ".join(v.german_reference for v in verse)
    zeilen = [
        "BULK-SPONSORING — extern akquirierte Kapitel-/Buch-Patenschaft.",
        f"Gesamtbetrag: {euro(gesamt)} für {len(verse)} Verse "
        f"(regulär wären {euro(regulaer)}). Deshalb is_bulk_sponsoring=True "
        "und aus den Tagesreport-Summen herausgerechnet.",
        f"Zertifikat-Beschriftung: {', '.join(e.text for e in etiketten)}",
        f"Verse: {referenzen}",
    ]
    if uebersprungen:
        zeilen.append(
            f"Übersprungen (bereits gesponsert): "
            f"{', '.join(v.german_reference for v in uebersprungen)}"
        )
    zeilen += [
        f"Spendenbescheinigung: EINE über den vollen Betrag von {euro(gesamt)}, "
        f"Nr. {receipt_number}. Keine Einzelbescheinigungen je Vers — die Beträge "
        "auf den donation_verses sind nur die rechnerische Aufteilung innerhalb "
        "dieser einen Spende.",
        f"Zahlungsweg: {daten['zahlungsweg']} (kein Stripe-Vorgang, "
        "daher keine PaymentTransaction).",
        f"Tag der Zuwendung: {daten['zuwendungsdatum'].strftime('%d.%m.%Y')}, "
        f"Bescheinigung ausgestellt am {daten['ausstellungsdatum'].strftime('%d.%m.%Y')}.",
        "Zertifikat und Spendenbescheinigung über die normale Pipeline erzeugt "
        "(Certificate-Records vorhanden). Kein automatischer E-Mail-Versand — "
        "Versand über den Admin mit persönlichem Text.",
    ]
    if admin_email:
        zeilen.append(f"Eingetragen von: {admin_email} am {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    if daten.get("notiz"):
        zeilen.append(f"Notiz: {daten['notiz']}")
    return "\n".join(zeilen)


def anrede(person):
    s = person.salutation
    nachname = person.last_name or ""
    if s == "Herr":
        return f"Sehr geehrter Herr {nachname},"
    if s == "Frau":
        return f"Sehr geehrte Frau {nachname},"
    if s in ("Eheleute", "Familie"):
        return f"Sehr geehrte {s} {nachname},"
    return f"Guten Tag {person.first_name or ''} {nachname},".replace("  ", " ")


# ---------------------------------------------------------------------------
# Person: Vorschau der Änderungen
# ---------------------------------------------------------------------------

def personenfelder(daten):
    return {feld: daten.get(feld) for feld in PERSONENFELDER}


def person_vorschau(daten):
    """Gibt (bestehende Person oder None, Liste der Änderungen) zurück, ohne zu schreiben."""
    bestand = Person.query.filter_by(email=daten["email"].lower()).first()
    if not bestand:
        return None, []
    aenderungen = []
    for feld, neu in personenfelder(daten).items():
        if neu is None:
            continue
        alt = getattr(bestand, feld)
        if alt != neu:
            aenderungen.append((feld, alt, neu))
    return bestand, aenderungen


# ---------------------------------------------------------------------------
# Eintragen
# ---------------------------------------------------------------------------

def erstelle_bulk_sponsoring(daten, aufloesung, admin_email=None):
    """Legt Person (oder aktualisiert sie), Donation und DonationVerses an.

    Läuft in der offenen Session, wird nur geflusht. Der Aufrufer committet
    (oder rollt zurück — dann bleibt auch die Bescheinigungsnummer frei).

    daten: dict mit email, PERSONENFELDER, gesamtbetrag (Decimal),
           zuwendungsdatum/ausstellungsdatum (datetime), zahlungsweg, notiz
    Rückgabe: (donation, receipt_number, etiketten)
    """
    verse = aufloesung.verse
    betraege = verteile_betrag(daten["gesamtbetrag"], len(verse))
    zuwendung = daten["zuwendungsdatum"]

    person = Person.find_or_create(daten["email"].lower(), **personenfelder(daten))
    db.session.flush()

    receipt_number = ReceiptCounter.get_next_receipt_number(auto_commit=False)
    etiketten = etiketten_fuer_verse(verse)
    kommentar = baue_kommentar(
        daten, verse, receipt_number, etiketten, aufloesung.uebersprungen, admin_email
    )

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
        certificate_generated=False,
        receipt_generated=False,
        receipt_number=receipt_number,
        receipt_issued_at=daten["ausstellungsdatum"],
        email_sent=False,
        is_bulk_sponsoring=True,
        admin_comment=kommentar,
        created_at=zuwendung,
        completed_at=zuwendung,
    )
    db.session.add(donation)
    db.session.flush()

    for vers, betrag in zip(verse, betraege):
        db.session.add(DonationVerse(
            donation_id=donation.id,
            verse_id=vers.id,
            amount=betrag,
            created_at=zuwendung,
        ))
        vers.is_sponsored = True
        vers.sponsored_at = zuwendung

    VerseReservation.query.filter(
        VerseReservation.verse_id.in_([v.id for v in verse])
    ).delete(synchronize_session=False)

    person.last_donation_at = zuwendung
    db.session.flush()

    return donation, receipt_number, etiketten


def erzeuge_dokumente(app, donation_id):
    """Spendenbescheinigung und Zertifikat über die normale Pipeline erzeugen.

    Läuft NACH dem Commit der Spende: scheitert eine PDF, bleibt die Spende
    korrekt eingetragen und das PDF kann im Admin nachgezogen werden.
    Rückgabe: dict mit 'bescheinigung', 'zertifikat' (Certificate oder None)
    und 'fehler' (Liste von Meldungen).
    """
    from pdf_service import PDFGeneratorService

    ergebnis = {"bescheinigung": None, "zertifikat": None, "fehler": []}
    dienst = PDFGeneratorService(app)

    try:
        ergebnis["bescheinigung"] = dienst.generate_tax_receipt_atomic(donation_id)
        donation = db.session.get(Donation, donation_id)
        donation.receipt_generated = True
        db.session.commit()
    except Exception as fehler:  # noqa: BLE001 — Meldung wird dem Admin gezeigt
        db.session.rollback()
        ergebnis["fehler"].append(f"Spendenbescheinigung: {type(fehler).__name__}: {fehler}")

    try:
        ergebnis["zertifikat"] = dienst.generate_certificate_atomic(donation_id, "personal_certificate")
        donation = db.session.get(Donation, donation_id)
        donation.certificate_generated = True
        db.session.commit()
    except Exception as fehler:  # noqa: BLE001
        db.session.rollback()
        ergebnis["fehler"].append(f"Zertifikat: {type(fehler).__name__}: {fehler}")

    return ergebnis


# ---------------------------------------------------------------------------
# Persönliche Mail
# ---------------------------------------------------------------------------

MAIL_BETREFF = "Ihre Patenschaft für die Neue Genfer Übersetzung"

MAIL_VORLAGE = """{anrede}

Sie hatten sich vor einiger Zeit bei mir gemeldet, weil Sie einen Teil der Neuen Genfer Übersetzung sponsern wollten. Ich hatte Sie daraufhin an Daniel Weninger weitergeleitet, der das Weitere mit Ihnen abgestimmt hat.

Nun hat er mir mitgeteilt, dass alles abgeschlossen ist. Ihre Patenschaft umfasst {beschreibung}. Darüber freue ich mich sehr, und ich danke Ihnen herzlich für Ihre Unterstützung.

Im Anhang finden Sie:

  - Ihr persönliches Patenschafts-Zertifikat
  - die Spendenbescheinigung für Ihr Finanzamt

Sollte an den Unterlagen etwas nicht stimmen oder Sie Fragen haben, melden Sie sich gerne jederzeit bei mir.

Mit freundlichen Grüßen
Uli Probst"""


def mailvorschlag(donation):
    """(Betreff, Text) als editierbarer Vorschlag für den Versand aus dem Admin."""
    etiketten = etiketten_fuer_donation(donation)
    beschreibung = beschreibung_fliesstext(etiketten, donation.verse_count)
    text = MAIL_VORLAGE.format(anrede=anrede(donation.person), beschreibung=beschreibung)
    return MAIL_BETREFF, text


def text_zu_absaetzen(text):
    """Klartext -> Liste von Markup-Absätzen (escaped, Zeilenumbrüche als <br>)."""
    absaetze = []
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        block = block.strip("\n")
        if block.strip():
            absaetze.append(Markup("<br>").join(escape(zeile) for zeile in block.split("\n")))
    return absaetze
