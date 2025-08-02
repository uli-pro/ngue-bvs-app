#!/usr/bin/env python3
"""
Erstellt das finale Dataset mit allen Versen aus den unübersetzten Büchern

Dieses Script:
1. Liest die Liste der unübersetzten Bücher aus untranslated_bible_books.csv
2. Extrahiert ALLE Verse aus diesen Büchern (ca. 11.000 Verse)
3. Speichert sie in final_verses_data.json
4. Erstellt zwei Subsets: 1000 und 100 Verse
"""

import json

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import time
from collections import defaultdict
import random

# Mapping von deutschen Buchnamen zu Bibel-Codes
BOOK_MAPPING = {
    '1.Könige': '1KI',
    '2.Könige': '2KI',
    '1.Chronik': '1CH',
    '2.Chronik': '2CH',
    'Esra': 'EZR',
    'Nehemia': 'NEH',
    'Esther': 'EST',
    'Hiob': 'JOB',
    'Prediger': 'ECC',
    'Hoheslied': 'SNG',
    'Jesaja': 'ISA',
    'Jeremia': 'JER',
    'Klagelieder': 'LAM',
    'Hesekiel': 'EZK',
    'Daniel': 'DAN',
    'Hosea': 'HOS',
    'Joel': 'JOL',
    'Amos': 'AMO',
    'Obadja': 'OBA',
    'Micha': 'MIC',
    'Nahum': 'NAM',
    'Habakuk': 'HAB',
    'Zefanja': 'ZEP',
    'Haggai': 'HAG',
    'Sacharja': 'ZEC',
    'Maleachi': 'MAL'
}

def get_untranslated_books():
    """Gibt die Liste der unübersetzten Bücher zurück"""
    untranslated_books = [
        '1.Könige',
        '2.Könige',
        '1.Chronik',
        '2.Chronik',
        'Esra',
        'Nehemia',
        'Esther',
        'Hiob',
        'Prediger',
        'Hoheslied',
        'Jesaja',
        'Jeremia',
        'Klagelieder',
        'Hesekiel',
        'Daniel',
        'Hosea',
        'Joel',
        'Amos',
        'Obadja',
        'Micha',
        'Nahum',
        'Habakuk',
        'Zefanja',
        'Haggai',
        'Sacharja',
        'Maleachi'
    ]
    
    books = []
    for book_name in untranslated_books:
        if book_name in BOOK_MAPPING:
            books.append({
                'name': book_name,
                'code': BOOK_MAPPING[book_name]
            })
        else:
            print(f"WARNUNG: Kein Mapping gefunden für: {book_name}")
    
    return books

def extract_verses_from_html(html_path):
    """Extrahiere Verse aus Schlachter HTML-Datei"""
    verses = []
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Finde Buch und Kapitel aus Dateiname
    filename = os.path.basename(html_path)
    match = re.match(r'([A-Z0-9]{3})(\d+)\.htm', filename)
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

def collect_all_verses(data_dir, book_codes):
    """Sammle ALLE Verse aus den angegebenen Büchern"""
    all_verses = []
    verses_by_book = defaultdict(list)
    
    # Durchsuche HTML-Dateien für jedes Buch
    for book_info in book_codes:
        book_code = book_info['code']
        book_name = book_info['name']
        
        # Spezialfall für Psalmen (3-stellige Kapitelnummern)
        if book_code == 'PSA':
            pattern = f"{book_code}*.htm"
        else:
            pattern = f"{book_code}*.htm"
        
        book_files = list(Path(data_dir).glob(pattern))
        
        # Filtere nur Kapitel-Dateien (nicht die Übersichtsdatei)
        chapter_files = [f for f in book_files if re.match(rf'{book_code}\d+\.htm', f.name)]
        chapter_files.sort()
        
        print(f"\n{book_name} ({book_code}): {len(chapter_files)} Kapitel gefunden")
        
        for html_file in chapter_files:
            verses = extract_verses_from_html(html_file)
            verses_by_book[book_code].extend(verses)
            all_verses.extend(verses)
            
            if len(verses) > 0:
                print(f"  {html_file.name}: {len(verses)} Verse")
    
    # Statistik
    print("\n" + "="*50)
    print("ZUSAMMENFASSUNG:")
    print("="*50)
    total_verses = 0
    for book_code, verses in verses_by_book.items():
        book_name = next((b['name'] for b in book_codes if b['code'] == book_code), book_code)
        print(f"{book_name:20} ({book_code}): {len(verses):5} Verse")
        total_verses += len(verses)
    
    print("="*50)
    print(f"GESAMT: {total_verses} Verse")
    
    return all_verses, verses_by_book

def create_subsets(all_verses, sizes=[1000, 100]):
    """Erstelle Subsets verschiedener Größen"""
    subsets = {}
    
    for size in sizes:
        if size >= len(all_verses):
            print(f"\nWARNUNG: Nur {len(all_verses)} Verse vorhanden, kann kein {size}-Verse Subset erstellen!")
            subsets[size] = all_verses
        else:
            # Stratified sampling: Versuche, aus jedem Buch proportional zu samplen
            subset = []
            verses_by_book = defaultdict(list)
            
            # Gruppiere Verse nach Buch
            for verse in all_verses:
                verses_by_book[verse['book']].append(verse)
            
            # Berechne, wie viele Verse pro Buch
            total_verses = len(all_verses)
            for book, book_verses in verses_by_book.items():
                proportion = len(book_verses) / total_verses
                verses_from_book = max(1, int(size * proportion))
                
                # Sample aus diesem Buch
                if verses_from_book >= len(book_verses):
                    subset.extend(book_verses)
                else:
                    subset.extend(random.sample(book_verses, verses_from_book))
            
            # Falls nicht genug, fülle auf
            if len(subset) < size:
                remaining_verses = [v for v in all_verses if v not in subset]
                additional = random.sample(remaining_verses, size - len(subset))
                subset.extend(additional)
            
            # Falls zu viele, reduziere
            if len(subset) > size:
                subset = random.sample(subset, size)
            
            subsets[size] = subset
            print(f"\nSubset mit {size} Versen erstellt")
    
    return subsets

def save_datasets(all_verses, subsets):
    """Speichere alle Datasets"""
    # 1. Vollständiges Dataset
    full_data = {
        'verses': all_verses,
        'metadata': {
            'num_verses': len(all_verses),
            'books_included': list(set(v['book'] for v in all_verses)),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Vollständiges Dataset aller unübersetzten Bücher'
        }
    }
    
    with open('final_verses_data.json', 'w', encoding='utf-8') as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    print(f"\nVollständiges Dataset gespeichert: final_verses_data.json")
    
    # 2. Subsets
    for size, verses in subsets.items():
        subset_data = {
            'verses': verses,
            'metadata': {
                'num_verses': len(verses),
                'books_included': list(set(v['book'] for v in verses)),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'description': f'Subset mit {size} Versen für Tests',
                'parent_dataset': 'final_verses_data.json'
            }
        }
        
        filename = f'verses_subset_{size}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(subset_data, f, ensure_ascii=False, indent=2)
        print(f"Subset gespeichert: {filename}")

def main():
    """Hauptfunktion"""
    print("NGÜ Bibelvers-Sponsoring - Finale Datenextraktion")
    print("="*60)
    
    # 1. Hole Liste der unübersetzten Bücher
    print("\nLade Liste der unübersetzten Bücher...")
    books = get_untranslated_books()
    print(f"Gefunden: {len(books)} Bücher")
    
    # 2. Extrahiere alle Verse
    data_dir = '../../data/schlachter-1951'
    
    if not os.path.exists(data_dir):
        print(f"\nFEHLER: Verzeichnis {data_dir} nicht gefunden!")
        print("Bitte Schlachter HTML-Dateien in data/schlachter-1951/ ablegen")
        return
    
    print(f"\nExtrahiere Verse aus {data_dir}...")
    all_verses, verses_by_book = collect_all_verses(data_dir, books)
    
    if len(all_verses) == 0:
        print("\nFEHLER: Keine Verse gefunden!")
        return
    
    # 3. Erstelle Subsets
    print(f"\nErstelle Subsets...")
    subsets = create_subsets(all_verses, sizes=[1000, 100])
    
    # 4. Speichere alle Datasets
    save_datasets(all_verses, subsets)
    
    # 5. Zeige Beispiele
    print("\n" + "="*60)
    print("BEISPIELVERSE:")
    print("="*60)
    for i, verse in enumerate(random.sample(all_verses, min(5, len(all_verses)))):
        print(f"\n{i+1}. {verse['reference']}")
        print(f"   {verse['text'][:100]}...")
    
    print("\n✓ Datenextraktion abgeschlossen!")


if __name__ == "__main__":
    # Setze Random Seed für Reproduzierbarkeit
    random.seed(42)
    main()
