#!/usr/bin/env python3
"""
Erweiterter Vector Search Test mit 100 AT-Versen

Dieses Script:
1. Extrahiert 100 zufällige Verse aus den Schlachter HTML-Dateien
2. Erstellt realistische Test-Queries
3. Führt Performance-Tests durch
4. Generiert detaillierte Statistiken
"""

import json
import random
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import time
from collections import defaultdict

# AT-Bücher die wir testen wollen (verschiedene Genres)
TEST_BOOKS = {
    'GEN': 'Genesis - Geschichtsbuch',
    'PSA': 'Psalmen - Poesie',
    'PRO': 'Sprüche - Weisheit',
    'ISA': 'Jesaja - Prophet',
    'JER': 'Jeremia - Prophet',
    'DAN': 'Daniel - Apokalyptik',
    'HOS': 'Hosea - Kleiner Prophet',
    'JOB': 'Hiob - Weisheit',
    'ECC': 'Prediger - Philosophie',
    'LAM': 'Klagelieder - Poesie'
}

def extract_verses_from_html(html_path):
    """Extrahiere Verse aus Schlachter HTML-Datei"""
    verses = []
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Finde Buch und Kapitel aus Dateiname
    filename = os.path.basename(html_path)
    match = re.match(r'([A-Z]{3})(\d+)\.htm', filename)
    if not match:
        return verses
    
    book = match.group(1)
    chapter = int(match.group(2))
    
    # Finde alle span elements mit class="verse"
    verse_spans = soup.find_all('span', class_='verse')
    
    if not verse_spans:
        return verses
    
    # Der Text eines Verses ist vom aktuellen span bis zum nächsten span
    for i, span in enumerate(verse_spans):
        # Extrahiere Versnummer aus ID (z.B. "V1", "V2", etc.)
        verse_id = span.get('id', '')
        if verse_id.startswith('V'):
            try:
                verse_num = int(verse_id[1:])
            except ValueError:
                continue
        else:
            continue
        
        # Der Verstext beginnt nach der Versnummer im span
        # und geht bis zum nächsten verse span
        if span.parent:
            parent = span.parent
            
            # Sammle allen Text von diesem span bis zum nächsten
            verse_text_parts = []
            current = span
            
            # Hole den Text aus dem span selbst (enthält die Nummer)
            span_text = span.get_text().strip()
            # Entferne die führende Nummer
            verse_text_match = re.match(r'^\d+\s+(.+)', span_text)
            if verse_text_match:
                verse_text_parts.append(verse_text_match.group(1))
            
            # Hole den Text nach dem span bis zum nächsten verse span
            for sibling in span.next_siblings:
                if isinstance(sibling, str):
                    verse_text_parts.append(sibling.strip())
                elif hasattr(sibling, 'name') and sibling.name == 'span' and 'verse' in sibling.get('class', []):
                    break
                elif hasattr(sibling, 'get_text'):
                    verse_text_parts.append(sibling.get_text().strip())
            
            verse_text = ' '.join(verse_text_parts).strip()
            verse_text = ' '.join(verse_text.split())  # Normalize whitespace
            
            if verse_text:
                verses.append({
                    'reference': f"{book}.{chapter}.{verse_num}",
                    'book': book,
                    'chapter': chapter,
                    'verse': verse_num,
                    'text': verse_text
                })
    
    return verses

def collect_test_verses(data_dir, num_verses=100):
    """Sammle Testverse aus verschiedenen Büchern"""
    all_verses = []
    verses_by_book = defaultdict(list)
    
    # Durchsuche HTML-Dateien
    for book in TEST_BOOKS.keys():
        pattern = f"{book}*.htm"
        book_files = list(Path(data_dir).glob(pattern))
        
        print(f"Gefunden: {len(book_files)} Dateien für {book}")
        
        for html_file in book_files[:5]:  # Max 5 Kapitel pro Buch
            verses = extract_verses_from_html(html_file)
            verses_by_book[book].extend(verses)
            all_verses.extend(verses)
    
    # Statistik
    print("\nVerse pro Buch:")
    for book, verses in verses_by_book.items():
        print(f"  {book}: {len(verses)} Verse")
    
    # Wähle zufällige Verse aus (gewichtet nach Büchern)
    selected_verses = []
    verses_per_book = num_verses // len(TEST_BOOKS)
    
    for book, verses in verses_by_book.items():
        if len(verses) >= verses_per_book:
            selected = random.sample(verses, verses_per_book)
        else:
            selected = verses
        selected_verses.extend(selected)
    
    # Falls nicht genug, fülle auf
    if len(selected_verses) < num_verses and len(all_verses) > num_verses:
        remaining = num_verses - len(selected_verses)
        additional = random.sample(
            [v for v in all_verses if v not in selected_verses], 
            remaining
        )
        selected_verses.extend(additional)
    
    return selected_verses[:num_verses]

def create_test_queries(verses):
    """Erstelle realistische Test-Queries basierend auf den Versen"""
    queries = []
    
    # Häufige biblische Themen und ihre Schlüsselwörter
    themes = {
        'Gott': ['HERR', 'Gott', 'Allmächtig', 'Schöpfer'],
        'Glaube': ['glauben', 'vertrauen', 'Glaube', 'Vertrauen'],
        'Liebe': ['Liebe', 'lieben', 'Barmherzigkeit', 'Güte'],
        'Sünde': ['Sünde', 'Schuld', 'Übertretung', 'böse'],
        'Erlösung': ['retten', 'erlösen', 'Heil', 'Rettung'],
        'Gebet': ['beten', 'Gebet', 'rufen', 'bitten'],
        'Weisheit': ['Weisheit', 'weise', 'Verstand', 'Erkenntnis'],
        'Gerechtigkeit': ['gerecht', 'Gerechtigkeit', 'Recht', 'richten'],
        'Hoffnung': ['Hoffnung', 'hoffen', 'harren', 'warten'],
        'Frieden': ['Frieden', 'Ruhe', 'still', 'Shalom']
    }
    
    # Erstelle Queries basierend auf gefundenen Themen
    theme_verses = defaultdict(list)
    
    for verse in verses:
        text_lower = verse['text'].lower()
        for theme, keywords in themes.items():
            if any(keyword.lower() in text_lower for keyword in keywords):
                theme_verses[theme].append(verse['reference'])
    
    # Generiere Test-Queries
    for theme, verse_refs in theme_verses.items():
        if len(verse_refs) >= 2:  # Nur wenn mindestens 2 Verse das Thema haben
            queries.append({
                'query': theme,
                'expected_matches': verse_refs[:5],  # Max 5 erwartete Treffer
                'theme': theme
            })
    
    # Zusätzliche komplexere Queries
    complex_queries = [
        {
            'query': 'Gottes Liebe und Barmherzigkeit',
            'theme': 'compound',
            'keywords': ['liebe', 'barmherzig', 'gütig']
        },
        {
            'query': 'Vergebung der Sünden',
            'theme': 'compound',
            'keywords': ['vergeben', 'sünde', 'schuld']
        },
        {
            'query': 'Kraft in schweren Zeiten',
            'theme': 'compound',
            'keywords': ['kraft', 'stark', 'schwer', 'not']
        }
    ]
    
    # Finde Verse für komplexe Queries
    for cq in complex_queries:
        matches = []
        for verse in verses:
            text_lower = verse['text'].lower()
            if sum(1 for kw in cq['keywords'] if kw in text_lower) >= 2:
                matches.append(verse['reference'])
        
        if matches:
            queries.append({
                'query': cq['query'],
                'expected_matches': matches[:5],
                'theme': cq['theme']
            })
    
    return queries

def prepare_extended_test_data():
    """Hauptfunktion zur Vorbereitung der erweiterten Testdaten"""
    data_dir = '../../data/schlachter-1951'
    
    if not os.path.exists(data_dir):
        print(f"FEHLER: Verzeichnis {data_dir} nicht gefunden!")
        print("Bitte Schlachter HTML-Dateien in data/schlachter-1951/ ablegen")
        return
    
    print("Sammle Testverse...")
    verses = collect_test_verses(data_dir, 1000)
    
    print(f"\nGesammelt: {len(verses)} Verse")
    
    print("\nErstelle Test-Queries...")
    queries = create_test_queries(verses)
    
    print(f"Erstellt: {len(queries)} Test-Queries")
    
    # Speichere Testdaten
    test_data = {
        'test_verses': verses,
        'test_queries': queries,
        'metadata': {
            'num_verses': len(verses),
            'num_queries': len(queries),
            'books_included': list(TEST_BOOKS.keys()),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    
    output_file = 'extended_test_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nTestdaten gespeichert in: {output_file}")
    print("\nBeispiel-Verse:")
    for verse in verses[:3]:
        print(f"  {verse['reference']}: {verse['text'][:80]}...")
    
    print("\nBeispiel-Queries:")
    for query in queries[:3]:
        print(f"  '{query['query']}' -> {len(query['expected_matches'])} erwartete Treffer")


if __name__ == "__main__":
    prepare_extended_test_data()
