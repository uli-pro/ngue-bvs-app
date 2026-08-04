# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

"""
Deutsche Buchnamen-Mapping für NGÜ Bibelvers-Sponsoring App
Zentrale Tabelle zur Übersetzung englischer Buchcodes in deutsche Buchnamen
"""

from datetime import date

# Mapping von englischen 3-Buchstaben-Codes zu deutschen Buchnamen
BOOK_NAMES = {
    # Altes Testament - Geschichtsbücher
    'GEN': '1. Mose',
    'EXO': '2. Mose', 
    'LEV': '3. Mose',
    'NUM': '4. Mose',
    'DEU': '5. Mose',
    'JOS': 'Josua',
    'JDG': 'Richter',
    'RUT': 'Rut',
    '1SA': '1. Samuel',
    '2SA': '2. Samuel',
    '1KI': '1. Könige',
    '2KI': '2. Könige',
    '1CH': '1. Chronik',
    '2CH': '2. Chronik',
    'EZR': 'Esra',
    'NEH': 'Nehemia',
    'EST': 'Ester',
    
    # Altes Testament - Poetische Bücher
    'JOB': 'Hiob',
    'PSA': 'Psalm',
    'PRO': 'Sprüche',
    'ECC': 'Prediger',
    'SNG': 'Hohelied',
    
    # Altes Testament - Große Propheten
    'ISA': 'Jesaja',
    'JER': 'Jeremia',
    'LAM': 'Klagelieder',
    'EZK': 'Hesekiel',
    'DAN': 'Daniel',
    
    # Altes Testament - Kleine Propheten
    'HOS': 'Hosea',
    'JOL': 'Joel',
    'AMO': 'Amos',
    'OBA': 'Obadja',
    'JON': 'Jona',
    'MIC': 'Micha',
    'NAM': 'Nahum',
    'HAB': 'Habakuk',
    'ZEP': 'Zefanja',
    'HAG': 'Haggai',
    'ZEC': 'Sacharja',
    'MAL': 'Maleachi'
}

def get_german_book_name(english_code):
    """
    Gibt den deutschen Buchnamen für einen englischen Code zurück
    
    Args:
        english_code (str): 3-Buchstaben englischer Code (z.B. 'ISA', '1KI')
    
    Returns:
        str: Deutscher Buchname (z.B. 'Jesaja', '1. Könige')
             Falls Code nicht gefunden wird, wird der ursprüngliche Code zurückgegeben
    """
    if not english_code:
        return english_code
        
    return BOOK_NAMES.get(english_code.upper(), english_code)

def get_german_reference(book, chapter, verse):
    """
    Erstellt eine vollständige deutsche Bibelreferenz

    Args:
        book (str): Englischer Buchcode
        chapter (int): Kapitel
        verse (int): Vers

    Returns:
        str: Deutsche Referenz (z.B. 'Jesaja 43,1')
    """
    german_book = get_german_book_name(book)
    return f"{german_book} {chapter},{verse}"


# ---------------------------------------------------------------------------
# Bereits erschienene NGÜ-Bände
# ---------------------------------------------------------------------------
# Bücher, die in einem erschienenen Band enthalten sind, können nicht mehr
# gesponsert werden. Ihre Verse bleiben in der Tabelle `verses` stehen, weil
# `donation_verses` auf sie verweist — sie werden über `verses.is_translated`
# aus dem Angebot genommen.
#
# Maßgeblich für alle Abfragen ist die Datenbank. Diese Liste sorgt dafür,
# dass ein Neuaufbau der Datenbank über setup_db.py denselben Zustand
# herstellt, statt die Bücher stillschweigend wieder verkäuflich zu machen.
#
# Beim nächsten erschienenen Band hier einen Eintrag ergänzen und eine
# Migration nach dem Muster von migrations/007_mark_translated_books.sql
# schreiben.
#
# Nur Bände aufführen, deren Bücher in `verses` stehen. Die früheren Bände
# (Neues Testament und Psalmen 2011, Sprüche 2015, 1./2. Mose 2019,
# 3.–5. Mose 2021, Josua/Richter/Rut 2022, 1./2. Samuel 2022) fehlen hier
# bewusst — ihre Bücher waren nie Teil des Datenbestands.

PUBLISHED_VOLUMES = [
    {
        'name': 'Die Geschichtsbücher Josua bis Ester',
        'release': date(2026, 6, 1),   # genauer Tag unbekannt, erschienen 06/2026
        'display': 'Juni 2026',
        'books': ['1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST'],
    },
]

# Buchcode -> Band, für den schnellen Zugriff
TRANSLATED_BOOKS = {
    book: volume
    for volume in PUBLISHED_VOLUMES
    for book in volume['books']
}


def is_book_published(book_code):
    """
    Prüft, ob ein Buch bereits in einem erschienenen Band enthalten ist

    Args:
        book_code (str): Englischer Buchcode (z.B. '1KI')

    Returns:
        bool: True, wenn das Buch nicht mehr gesponsert werden kann
    """
    if not book_code:
        return False

    return book_code.upper() in TRANSLATED_BOOKS


def get_publication_notice(book_code):
    """
    Formuliert den Hinweis für ein bereits erschienenes Buch

    Args:
        book_code (str): Englischer Buchcode (z.B. 'NEH')

    Returns:
        str: Hinweistext für den Besucher, oder None wenn das Buch noch
             gesponsert werden kann
    """
    volume = TRANSLATED_BOOKS.get((book_code or '').upper())
    if not volume:
        return None

    return (
        f"Das Buch {get_german_book_name(book_code)} ist inzwischen erschienen "
        f"– im {volume['display']} als Teil des Bandes „{volume['name']}“. "
        f"Es kann deshalb nicht mehr gesponsert werden."
    )