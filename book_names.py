# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

"""
Deutsche Buchnamen-Mapping für NGÜ Bibelvers-Sponsoring App
Zentrale Tabelle zur Übersetzung englischer Buchcodes in deutsche Buchnamen
"""

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