#!/usr/bin/env python3
"""Debug HTML parser"""

from bs4 import BeautifulSoup
import re

# Test mit PSA009.htm
html_path = '../../data/schlachter-1951/PSA009.htm'

with open(html_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Debug: Dateiname
filename = 'PSA009.htm'
match = re.match(r'([A-Z]{3})(\d+)\.htm', filename)
print(f"Filename match: {match}")
if match:
    print(f"Book: {match.group(1)}, Chapter: {match.group(2)}")

# Debug: HTML Struktur
main_div = soup.find('div', class_='p')
print(f"\nFound div with class='p': {main_div is not None}")

if main_div:
    # Hole Text
    full_text = main_div.get_text()
    print(f"\nFirst 200 chars of text: {full_text[:200]}")
    
    # Debug: Pattern matching
    verse_pattern = re.compile(r'(\d+)\s+\u00A0')
    matches = list(verse_pattern.finditer(full_text))
    print(f"\nFound {len(matches)} verse numbers")
    
    if matches:
        for i, match in enumerate(matches[:3]):  # Erste 3 Verse
            print(f"\nVerse {match.group(1)}:")
            start = match.end()
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = start + 100  # Nur erste 100 Zeichen
            verse_text = full_text[start:end].strip()
            print(f"Text: {verse_text[:100]}...")

# Alternative: Schaue direkt auf span elements
print("\n\nAlternative approach - looking at span elements:")
verse_spans = soup.find_all('span', class_='verse')
print(f"Found {len(verse_spans)} span elements with class='verse'")

if verse_spans:
    for span in verse_spans[:3]:
        print(f"\nSpan ID: {span.get('id')}")
        print(f"Span text: {span.get_text()[:50]}...")