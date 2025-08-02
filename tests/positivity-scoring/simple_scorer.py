#!/usr/bin/env python3
"""
Einfaches Positivitäts-Scoring für Bibelverse (ohne Datenbank)
Generiert nur Reports im Markdown-Format.
"""

import json
import re
import os
from typing import Dict, List, Tuple
from datetime import datetime

class SimplePositivityScorer:
    """Vereinfachter Scorer ohne Datenbankanbindung."""
    
    def __init__(self):
        # Positive Schlüsselwörter
        self.positive_keywords = {
            'liebe': 3.0, 'lieben': 3.0, 'liebt': 3.0, 'geliebt': 3.0,
            'gnade': 3.0, 'gnädig': 3.0, 'barmherzig': 3.0, 'barmherzigkeit': 3.0,
            'güte': 3.0, 'gütig': 3.0, 'freundlich': 2.5, 'freundlichkeit': 2.5,
            'freude': 3.0, 'freuen': 3.0, 'fröhlich': 2.5, 'glück': 2.5,
            'frieden': 3.0, 'friedlich': 2.5, 'ruhe': 2.0,
            'hoffnung': 3.0, 'hoffen': 2.5, 'zuversicht': 2.5,
            'segen': 3.0, 'segnen': 3.0, 'gesegnet': 3.0,
            'heil': 3.0, 'heilung': 3.0, 'heilen': 3.0,
            'erlösung': 3.0, 'erlösen': 3.0, 'erlöst': 3.0, 'erretten': 3.0,
            'ewigkeit': 2.5, 'ewig': 2.5, 'leben': 2.5, 'lebendig': 2.5,
            'helfen': 2.5, 'hilfe': 2.5, 'hilft': 2.5,
            'schutz': 2.5, 'schützen': 2.5, 'bewahren': 2.5,
            'trost': 2.5, 'trösten': 2.5, 'ermutigen': 2.5,
            'vertrauen': 2.5, 'glauben': 2.5, 'glaube': 2.5, 'treue': 2.5,
            'stark': 2.0, 'stärke': 2.0, 'kraft': 2.0,
            'weisheit': 2.0, 'weise': 2.0, 'verstand': 2.0,
            'gerecht': 2.0, 'gerechtigkeit': 2.0,
            'gut': 2.0, 'gutes': 2.0, 'guten': 2.0,
            'licht': 2.5, 'leuchten': 2.0, 'hell': 2.0,
            'führen': 2.0, 'führung': 2.0, 'leiten': 2.0,
            'danken': 2.5, 'dank': 2.5, 'dankbar': 2.5, 'loben': 2.5, 'preisen': 2.5,
            'vergeben': 3.0, 'vergebung': 3.0,
            'himmel': 2.0, 'himmlisch': 2.0, 'herrlichkeit': 2.5
        }
        
        # Negative Schlüsselwörter
        self.negative_keywords = {
            'tod': -3.0, 'tot': -3.0, 'sterben': -3.0, 'töten': -3.0,
            'vernichten': -3.0, 'zerstören': -3.0,
            'zorn': -3.0, 'zornig': -3.0, 'wut': -3.0, 'hass': -3.0,
            'angst': -2.5, 'fürchten': -2.5, 'furcht': -2.5,
            'trauer': -2.5, 'traurig': -2.5, 'weinen': -2.0, 'klagen': -2.0,
            'schmerz': -2.5, 'leiden': -2.5, 'qual': -2.5,
            'sünde': -2.5, 'sündigen': -2.5, 'sünder': -2.5, 'schuld': -2.5,
            'böse': -2.5, 'übel': -2.5, 'gottlos': -2.5,
            'strafe': -2.5, 'strafen': -2.5, 'gericht': -2.5,
            'verdammen': -3.0, 'fluch': -3.0,
            'krieg': -2.5, 'kampf': -2.0, 'feind': -2.0,
            'nicht': -0.5, 'kein': -0.5, 'niemals': -1.0,
            'mangel': -2.0, 'verloren': -2.0,
            'finsternis': -2.5, 'dunkel': -2.0,
            'krank': -2.0, 'schwach': -1.5,
            'arm': -1.5, 'elend': -2.5, 'not': -2.0,
            'lüge': -2.5, 'betrug': -2.5, 'falsch': -2.0
        }
    
    def score_verse(self, verse: Dict) -> Dict:
        """Bewertet einen einzelnen Vers."""
        text = verse['text'].lower()
        
        # Keywords zählen
        positive_score = 0.0
        negative_score = 0.0
        found_positive = {}
        found_negative = {}
        
        for keyword, weight in self.positive_keywords.items():
            count = len(re.findall(r'\b' + keyword + r'\b', text))
            if count > 0:
                positive_score += weight * count
                found_positive[keyword] = count
                
        for keyword, weight in self.negative_keywords.items():
            count = len(re.findall(r'\b' + keyword + r'\b', text))
            if count > 0:
                negative_score += weight * count
                found_negative[keyword] = count
        
        # Spezielle Phrasen berücksichtigen
        if 'nicht' in text and 'fürchten' in text:
            positive_score += 2.0
        if 'kein' in text and 'tod' in text:
            positive_score += 2.0
            
        # Gesamtscore
        total_score = positive_score + negative_score
        normalized_score = max(0, min(100, (total_score + 20) * 2.5))
        
        return {
            'reference': verse.get('reference', ''),
            'text': verse['text'],
            'score': round(normalized_score, 1),
            'positive_keywords': found_positive,
            'negative_keywords': found_negative
        }


def main():
    """Hauptfunktion."""
    print("Positivitäts-Scoring für Bibelverse\n")
    
    # Pfade
    base_path = "/Users/ulrichprobst/Library/Mobile Documents/com~apple~CloudDocs/1 Uli Dokumente/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/ngue-bvs-app"
    input_file = os.path.join(base_path, "tests/vector-poc/verses_subset_100.json")
    output_dir = os.path.join(base_path, "tests/positivity-scoring/results")
    
    # Scorer initialisieren
    scorer = SimplePositivityScorer()
    
    # Verse laden
    print("Lade Verse...")
    with open(input_file, 'r', encoding='utf-8') as f:
        verses_data = json.load(f)
    verses = verses_data['verses']
    print(f"✓ {len(verses)} Verse geladen\n")
    
    # Scoring
    print("Berechne Scores...")
    scored_verses = []
    for verse in verses:
        scored = scorer.score_verse(verse)
        scored_verses.append(scored)
    
    # Sortieren
    scored_verses.sort(key=lambda x: x['score'], reverse=True)
    print("✓ Scoring abgeschlossen\n")
    
    # Report generieren
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"simple_positivity_report_{timestamp}.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Bibelvers Positivitäts-Analyse\n\n")
        f.write(f"**Datum**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write(f"**Anzahl Verse**: {len(verses)}\n\n")
        
        # Statistiken
        scores = [v['score'] for v in scored_verses]
        avg_score = sum(scores) / len(scores)
        
        f.write("## Zusammenfassung\n\n")
        f.write(f"- Durchschnittsscore: {avg_score:.1f}\n")
        f.write(f"- Höchster Score: {max(scores)}\n")
        f.write(f"- Niedrigster Score: {min(scores)}\n")
        f.write(f"- Verse mit Score ≥ 70: {len([s for s in scores if s >= 70])}\n\n")
        
        # Top 30
        f.write("## Top 30 Positive Verse\n\n")
        for i, verse in enumerate(scored_verses[:30], 1):
            f.write(f"### {i}. {verse['reference']} (Score: {verse['score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            if verse['positive_keywords']:
                f.write(f"**Positive**: {', '.join(verse['positive_keywords'].keys())}\n\n")
            f.write("---\n\n")
        
        # Bottom 10
        f.write("## Bottom 10 Verse\n\n")
        for verse in scored_verses[-10:]:
            f.write(f"### {verse['reference']} (Score: {verse['score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            if verse['negative_keywords']:
                f.write(f"**Negative**: {', '.join(verse['negative_keywords'].keys())}\n\n")
            f.write("---\n\n")
    
    print(f"✓ Report gespeichert: {report_file}")
    
    # Top 5 ausgeben
    print("\nTop 5 positive Verse:")
    for i, verse in enumerate(scored_verses[:5], 1):
        print(f"\n{i}. {verse['reference']} (Score: {verse['score']})")
        print(f"   \"{verse['text'][:80]}...\"")


if __name__ == "__main__":
    main()
