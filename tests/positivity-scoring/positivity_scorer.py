#!/usr/bin/env python3
"""
Positivitäts-Scoring für Bibelverse
Dieses Skript bewertet Bibelverse nach ihrer emotionalen Valenz
für die NGÜ Bible Vers Donation App.
"""

import json
import re
from typing import Dict, List, Tuple
from datetime import datetime
import os

class BibelversPositivityScorer:
    def __init__(self):
        # Positive Schlüsselwörter mit Gewichtungen
        self.positive_keywords = {
            # Göttliche Eigenschaften
            'liebe': 3.0, 'lieben': 3.0, 'liebt': 3.0, 'geliebt': 3.0,
            'gnade': 3.0, 'gnädig': 3.0, 'barmherzig': 3.0, 'barmherzigkeit': 3.0,
            'güte': 3.0, 'gütig': 3.0, 'freundlich': 2.5, 'freundlichkeit': 2.5,
            
            # Positive Emotionen
            'freude': 3.0, 'freuen': 3.0, 'fröhlich': 2.5, 'glück': 2.5, 'glücklich': 2.5,
            'frieden': 3.0, 'friedlich': 2.5, 'ruhe': 2.0, 'ruhig': 2.0,
            'hoffnung': 3.0, 'hoffen': 2.5, 'zuversicht': 2.5, 'zuversichtlich': 2.5,
            
            # Spirituelle Konzepte
            'segen': 3.0, 'segnen': 3.0, 'gesegnet': 3.0, 'segnung': 3.0,
            'heil': 3.0, 'heilung': 3.0, 'heilen': 3.0, 'geheilt': 3.0,
            'erlösung': 3.0, 'erlösen': 3.0, 'erlöst': 3.0, 'erretten': 3.0, 'gerettet': 3.0,
            'ewigkeit': 2.5, 'ewig': 2.5, 'leben': 2.5, 'lebens': 2.5, 'lebendig': 2.5,
            
            # Positive Handlungen
            'helfen': 2.5, 'hilfe': 2.5, 'hilft': 2.5, 'geholfen': 2.5,
            'schutz': 2.5, 'schützen': 2.5, 'beschützen': 2.5, 'bewahren': 2.5,
            'trost': 2.5, 'trösten': 2.5, 'getröstet': 2.5, 'ermutigen': 2.5,
            'vertrauen': 2.5, 'glauben': 2.5, 'glaube': 2.5, 'treue': 2.5, 'treu': 2.5,
            
            # Positive Eigenschaften
            'stark': 2.0, 'stärke': 2.0, 'kraft': 2.0, 'kräftig': 2.0, 'mächtig': 2.0,
            'weisheit': 2.0, 'weise': 2.0, 'verstand': 2.0, 'erkenntnis': 2.0,
            'gerecht': 2.0, 'gerechtigkeit': 2.0, 'rechtschaffen': 2.0,
            'gut': 2.0, 'gutes': 2.0, 'guten': 2.0, 'beste': 2.0,
            
            # Licht und Führung
            'licht': 2.5, 'leuchten': 2.0, 'hell': 2.0, 'strahlen': 2.0,
            'führen': 2.0, 'führung': 2.0, 'leiten': 2.0, 'weg': 1.5,
            
            # Gemeinschaft
            'gemeinschaft': 2.0, 'zusammen': 1.5, 'einheit': 2.0, 'gemeinsam': 1.5,
            
            # Dankbarkeit
            'danken': 2.5, 'dank': 2.5, 'dankbar': 2.5, 'loben': 2.5, 'preisen': 2.5,
            
            # Vergebung
            'vergeben': 3.0, 'vergebung': 3.0, 'verzeihen': 2.5, 'verzeihung': 2.5,
            
            # Wachstum
            'wachsen': 1.5, 'gedeihen': 2.0, 'blühen': 2.0, 'frucht': 1.5,
            
            # Himmlisches
            'himmel': 2.0, 'himmlisch': 2.0, 'paradies': 2.5, 'herrlichkeit': 2.5
        }
        
        # Negative Schlüsselwörter mit Gewichtungen
        self.negative_keywords = {
            # Tod und Zerstörung
            'tod': -3.0, 'tot': -3.0, 'sterben': -3.0, 'gestorben': -3.0, 'töten': -3.0,
            'vernichten': -3.0, 'vernichtung': -3.0, 'zerstören': -3.0, 'zerstörung': -3.0,
            
            # Negative Emotionen
            'zorn': -3.0, 'zornig': -3.0, 'wut': -3.0, 'wütend': -3.0, 'hass': -3.0, 'hassen': -3.0,
            'angst': -2.5, 'fürchten': -2.5, 'furcht': -2.5, 'erschrecken': -2.5,
            'trauer': -2.5, 'traurig': -2.5, 'weinen': -2.0, 'tränen': -2.0, 'klagen': -2.0,
            'schmerz': -2.5, 'leiden': -2.5, 'qual': -2.5, 'pein': -2.5,
            
            # Sünde und Schuld
            'sünde': -2.5, 'sündigen': -2.5, 'sünder': -2.5, 'schuld': -2.5, 'schuldig': -2.5,
            'böse': -2.5, 'übel': -2.5, 'schlecht': -2.0, 'gottlos': -2.5,
            
            # Strafe und Gericht
            'strafe': -2.5, 'strafen': -2.5, 'gericht': -2.5, 'richten': -2.0,
            'verdammen': -3.0, 'verdammnis': -3.0, 'fluch': -3.0, 'verfluchen': -3.0,
            
            # Konflikt
            'krieg': -2.5, 'kampf': -2.0, 'streit': -2.0, 'feind': -2.0, 'feinde': -2.0,
            'schlagen': -2.0, 'schwert': -2.0, 'waffe': -2.0,
            
            # Negation und Mangel
            'nicht': -0.5, 'kein': -0.5, 'keine': -0.5, 'niemals': -1.0, 'nie': -1.0,
            'mangel': -2.0, 'fehlen': -1.5, 'verloren': -2.0, 'verlieren': -2.0,
            
            # Dunkelheit
            'finsternis': -2.5, 'dunkel': -2.0, 'dunkelheit': -2.0, 'schatten': -1.5,
            
            # Negative Zustände
            'krank': -2.0, 'krankheit': -2.0, 'schwach': -1.5, 'schwäche': -1.5,
            'arm': -1.5, 'armut': -2.0, 'elend': -2.5, 'not': -2.0,
            
            # Täuschung
            'lüge': -2.5, 'lügen': -2.5, 'betrug': -2.5, 'betrügen': -2.5,
            'falsch': -2.0, 'täuschen': -2.0, 'täuschung': -2.0
        }
        
        # Kontextmodifikatoren - Phrasen die die Bedeutung umkehren können
        self.context_modifiers = {
            'kein .* tod': 2.0,  # "kein Tod" ist positiv
            'nicht .* fürchten': 2.0,  # "nicht fürchten" ist positiv
            'vom .* erlösen': 2.0,  # "vom Tod erlösen" ist positiv
            'aus .* erretten': 2.0,  # "aus der Not erretten" ist positiv
            'überwind.* .* böse': 2.0,  # "das Böse überwinden" ist positiv
        }
        
    def calculate_keyword_score(self, text: str) -> Tuple[float, Dict[str, int]]:
        """Berechnet den Keyword-basierten Score."""
        text_lower = text.lower()
        
        positive_score = 0.0
        negative_score = 0.0
        found_keywords = {'positive': {}, 'negative': {}}
        
        # Positive Keywords zählen
        for keyword, weight in self.positive_keywords.items():
            count = len(re.findall(r'\b' + keyword + r'\b', text_lower))
            if count > 0:
                positive_score += weight * count
                found_keywords['positive'][keyword] = count
                
        # Negative Keywords zählen
        for keyword, weight in self.negative_keywords.items():
            count = len(re.findall(r'\b' + keyword + r'\b', text_lower))
            if count > 0:
                negative_score += weight * count  # weight ist bereits negativ
                found_keywords['negative'][keyword] = count
        
        # Kontextmodifikatoren anwenden
        for pattern, modifier in self.context_modifiers.items():
            if re.search(pattern, text_lower):
                positive_score += modifier
                
        total_score = positive_score + negative_score
        
        return total_score, found_keywords
    
    def analyze_structure(self, text: str) -> float:
        """Analysiert die Struktur des Verses (Fragen, Ausrufe, etc.)"""
        structure_score = 0.0
        
        # Ausrufezeichen deuten oft auf Ermutigung oder Lob hin
        exclamation_count = text.count('!')
        structure_score += exclamation_count * 0.5
        
        # Rhetorische Fragen können negativ sein
        if '?' in text and any(word in text.lower() for word in ['warum', 'weshalb', 'wieso']):
            structure_score -= 1.0
            
        # Direkte Anrede ist oft ermutigend
        if any(phrase in text.lower() for phrase in ['du bist', 'ihr seid', 'wir sind']):
            structure_score += 0.5
            
        return structure_score
    
    def calculate_theme_bonus(self, text: str) -> float:
        """Gibt Bonus-Punkte für bestimmte positive Themen."""
        theme_score = 0.0
        text_lower = text.lower()
        
        # Verheißungen und Zusagen
        if any(phrase in text_lower for phrase in ['ich will', 'ich werde', 'er wird']):
            if any(word in text_lower for word in ['segnen', 'helfen', 'erretten', 'bewahren']):
                theme_score += 2.0
                
        # Lobpreis und Anbetung
        if any(phrase in text_lower for phrase in ['lobet den herrn', 'preiset', 'danket']):
            theme_score += 2.5
            
        # Trost und Ermutigung
        if 'fürchte' in text_lower and 'nicht' in text_lower:
            theme_score += 2.0
            
        return theme_score
    
    def calculate_positivity_score(self, verse: Dict) -> Dict:
        """Berechnet den Gesamt-Positivitätsscore für einen Vers."""
        text = verse['text']
        
        # Keyword-Score berechnen
        keyword_score, found_keywords = self.calculate_keyword_score(text)
        
        # Struktur-Score
        structure_score = self.analyze_structure(text)
        
        # Themen-Bonus
        theme_bonus = self.calculate_theme_bonus(text)
        
        # Gesamtscore
        total_score = keyword_score + structure_score + theme_bonus
        
        # Normalisierung auf 0-100 Skala
        # Annahme: Scores zwischen -20 und +20 sind typisch
        normalized_score = max(0, min(100, (total_score + 20) * 2.5))
        
        return {
            'verse_id': verse.get('id', ''),
            'reference': verse.get('reference', ''),
            'book': verse.get('book', ''),
            'chapter': verse.get('chapter', 0),
            'verse': verse.get('verse', 0),
            'text': text,
            'positivity_score': round(normalized_score, 2),
            'raw_score': round(total_score, 2),
            'keyword_score': round(keyword_score, 2),
            'structure_score': round(structure_score, 2),
            'theme_bonus': round(theme_bonus, 2),
            'found_keywords': found_keywords
        }
    
    def score_verses(self, verses: List[Dict]) -> List[Dict]:
        """Bewertet eine Liste von Versen."""
        scored_verses = []
        
        for verse in verses:
            scored_verse = self.calculate_positivity_score(verse)
            scored_verses.append(scored_verse)
            
        # Nach Score sortieren (höchster zuerst)
        scored_verses.sort(key=lambda x: x['positivity_score'], reverse=True)
        
        return scored_verses


def main():
    """Hauptfunktion zum Testen des Scorers."""
    # Pfade
    base_path = "/Users/ulrichprobst/Library/Mobile Documents/com~apple~CloudDocs/1 Uli Dokumente/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/ngue-bvs-app"
    input_file = os.path.join(base_path, "tests/vector-poc/verses_subset_100.json")
    output_dir = os.path.join(base_path, "tests/positivity-scoring")
    
    # Scorer initialisieren
    scorer = BibelversPositivityScorer()
    
    # Verse laden
    print("Lade Verse...")
    with open(input_file, 'r', encoding='utf-8') as f:
        verses_data = json.load(f)
    
    verses = verses_data['verses']
    print(f"Gefunden: {len(verses)} Verse")
    
    # Scoring durchführen
    print("\nBerechne Positivitäts-Scores...")
    scored_verses = scorer.score_verses(verses)
    
    # Ergebnisse speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Vollständige Ergebnisse
    output_file = os.path.join(output_dir, f"scored_verses_{timestamp}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_verses': len(scored_verses),
                'timestamp': timestamp,
                'input_file': input_file
            },
            'scored_verses': scored_verses
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nErgebnisse gespeichert in: {output_file}")
    
    # Report generieren
    generate_report(scored_verses, output_dir, timestamp)
    
    # Top 10 und Bottom 10 anzeigen
    print("\n=== TOP 10 POSITIVE VERSE ===")
    for i, verse in enumerate(scored_verses[:10], 1):
        print(f"\n{i}. {verse['reference']} (Score: {verse['positivity_score']})")
        print(f"   {verse['text'][:100]}...")
        print(f"   Positive Keywords: {list(verse['found_keywords']['positive'].keys())}")
    
    print("\n=== BOTTOM 10 VERSE ===")
    for i, verse in enumerate(scored_verses[-10:], 1):
        print(f"\n{i}. {verse['reference']} (Score: {verse['positivity_score']})")
        print(f"   {verse['text'][:100]}...")
        print(f"   Negative Keywords: {list(verse['found_keywords']['negative'].keys())}")


def generate_report(scored_verses: List[Dict], output_dir: str, timestamp: str):
    """Generiert einen detaillierten Markdown-Report."""
    report_file = os.path.join(output_dir, f"positivity_report_{timestamp}.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Bibelvers Positivitäts-Analyse Report\n\n")
        f.write(f"**Datum**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write(f"**Anzahl Verse**: {len(scored_verses)}\n\n")
        
        # Statistiken
        scores = [v['positivity_score'] for v in scored_verses]
        avg_score = sum(scores) / len(scores)
        
        f.write("## Statistiken\n\n")
        f.write(f"- **Durchschnittlicher Score**: {avg_score:.2f}\n")
        f.write(f"- **Höchster Score**: {max(scores):.2f}\n")
        f.write(f"- **Niedrigster Score**: {min(scores):.2f}\n")
        f.write(f"- **Verse mit Score > 70**: {len([s for s in scores if s > 70])}\n")
        f.write(f"- **Verse mit Score < 30**: {len([s for s in scores if s < 30])}\n\n")
        
        # Score-Verteilung
        f.write("## Score-Verteilung\n\n")
        ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
        for low, high in ranges:
            count = len([s for s in scores if low <= s < high])
            percentage = (count / len(scores)) * 100
            f.write(f"- **{low}-{high}**: {count} Verse ({percentage:.1f}%)\n")
        
        # Top 20 Positive
        f.write("\n## Top 20 Positive Verse\n\n")
        for i, verse in enumerate(scored_verses[:20], 1):
            f.write(f"### {i}. {verse['reference']} (Score: {verse['positivity_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            f.write(f"**Positive Keywords**: {', '.join(verse['found_keywords']['positive'].keys())}\n")
            if verse['found_keywords']['negative']:
                f.write(f"**Negative Keywords**: {', '.join(verse['found_keywords']['negative'].keys())}\n")
            f.write(f"**Komponenten**: Keyword-Score: {verse['keyword_score']}, ")
            f.write(f"Struktur: {verse['structure_score']}, Thema: {verse['theme_bonus']}\n\n")
        
        # Bottom 10
        f.write("\n## Bottom 10 Verse (niedrigste Scores)\n\n")
        for i, verse in enumerate(scored_verses[-10:], 1):
            f.write(f"### {i}. {verse['reference']} (Score: {verse['positivity_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            f.write(f"**Negative Keywords**: {', '.join(verse['found_keywords']['negative'].keys())}\n")
            if verse['found_keywords']['positive']:
                f.write(f"**Positive Keywords**: {', '.join(verse['found_keywords']['positive'].keys())}\n")
            f.write("\n")
    
    print(f"Report gespeichert in: {report_file}")


if __name__ == "__main__":
    main()
