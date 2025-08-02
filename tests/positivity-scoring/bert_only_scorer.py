#!/usr/bin/env python3
"""
BERT-only Sentiment Scoring für Bibelverse
Verwendet ausschließlich das deutsche BERT-Modell ohne zusätzliche Keywords
"""

import json
import os
from datetime import datetime
from typing import Dict, List

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("FEHLER: transformers nicht installiert!")
    print("Bitte installiere mit: pip install transformers torch")
    exit(1)

class BertOnlyScorer:
    """Verwendet nur BERT für Sentiment-Analyse."""
    
    def __init__(self):
        print("Lade deutsches BERT-Modell...")
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="oliverguhr/german-sentiment-bert",
            device=-1  # CPU verwenden
        )
        print("✓ Modell geladen\n")
    
    def score_verse(self, verse: Dict) -> Dict:
        """Bewertet einen Vers nur mit BERT."""
        text = verse['text']
        
        # BERT-Analyse
        result = self.sentiment_pipeline(text)[0]
        label = result['label']
        confidence = result['score']
        
        # Score berechnen:
        # POSITIVE: score = confidence (0.5 bis 1.0 mapped auf 50-100)
        # NEGATIVE: score = 1 - confidence (0.5 bis 1.0 mapped auf 0-50)
        # NEUTRAL: score = 50
        
        if label == 'POSITIVE':
            # Confidence von 0.5-1.0 auf 50-100 mappen
            bert_score = 50 + (confidence - 0.5) * 100
        elif label == 'NEGATIVE':
            # Confidence von 0.5-1.0 auf 50-0 mappen (invertiert)
            bert_score = 50 - (confidence - 0.5) * 100
        else:  # NEUTRAL
            bert_score = 50.0
        
        return {
            'verse_id': verse.get('id', ''),
            'reference': verse.get('reference', ''),
            'book': verse.get('book', ''),
            'chapter': verse.get('chapter', 0),
            'verse': verse.get('verse', 0),
            'text': text,
            'bert_score': round(bert_score, 1),
            'bert_sentiment': label,
            'bert_confidence': round(confidence, 3)
        }
    
    def score_verses_batch(self, verses: List[Dict], batch_size: int = 50) -> List[Dict]:
        """Bewertet alle Verse in Batches."""
        scored_verses = []
        total = len(verses)
        
        print(f"Analysiere {total} Verse mit BERT...\n")
        
        for i in range(0, total, batch_size):
            batch = verses[i:i + batch_size]
            batch_end = min(i + batch_size, total)
            
            print(f"Verarbeite Verse {i+1}-{batch_end} von {total}...", end='', flush=True)
            
            for verse in batch:
                scored = self.score_verse(verse)
                scored_verses.append(scored)
            
            print(" ✓")
        
        # Nach BERT-Score sortieren (höchster zuerst)
        scored_verses.sort(key=lambda x: x['bert_score'], reverse=True)
        
        return scored_verses


def generate_bert_report(scored_verses: List[Dict], output_path: str):
    """Generiert einen Report nur mit BERT-Scores."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_path, f"bert_only_analysis_{timestamp}.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# BERT-Only Sentiment Analyse für Bibelverse\n\n")
        f.write(f"**Generiert am**: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}\n")
        f.write(f"**Modell**: oliverguhr/german-sentiment-bert\n")
        f.write(f"**Anzahl Verse**: {len(scored_verses)}\n\n")
        
        # Sentiment-Verteilung
        sentiments = [v['bert_sentiment'] for v in scored_verses]
        positive_count = sentiments.count('POSITIVE')
        negative_count = sentiments.count('NEGATIVE') 
        neutral_count = sentiments.count('NEUTRAL')
        
        f.write("## Sentiment-Verteilung\n\n")
        f.write(f"| Sentiment | Anzahl | Prozent |\n")
        f.write(f"|-----------|--------|----------|\n")
        f.write(f"| POSITIVE | {positive_count} | {positive_count/len(sentiments)*100:.1f}% |\n")
        f.write(f"| NEGATIVE | {negative_count} | {negative_count/len(sentiments)*100:.1f}% |\n")
        f.write(f"| NEUTRAL | {neutral_count} | {neutral_count/len(sentiments)*100:.1f}% |\n\n")
        
        # Score-Statistiken
        scores = [v['bert_score'] for v in scored_verses]
        avg_score = sum(scores) / len(scores)
        
        f.write("## Score-Statistiken\n\n")
        f.write(f"- **Durchschnitt**: {avg_score:.1f}/100\n")
        f.write(f"- **Maximum**: {max(scores):.1f}\n")
        f.write(f"- **Minimum**: {min(scores):.1f}\n")
        f.write(f"- **Verse mit Score ≥ 80**: {len([s for s in scores if s >= 80])}\n")
        f.write(f"- **Verse mit Score ≤ 20**: {len([s for s in scores if s <= 20])}\n\n")
        
        # Score-Verteilung in Bereichen
        f.write("## Score-Verteilung nach Bereichen\n\n")
        f.write("| Score-Bereich | Anzahl | Prozent | Interpretation |\n")
        f.write("|---------------|--------|----------|----------------|\n")
        ranges = [
            (90, 100, "Sehr positiv"),
            (70, 90, "Positiv"),
            (50, 70, "Leicht positiv"),
            (30, 50, "Leicht negativ"),
            (10, 30, "Negativ"),
            (0, 10, "Sehr negativ")
        ]
        for low, high, interpretation in ranges:
            count = len([s for s in scores if low <= s < high])
            percentage = count / len(scores) * 100
            f.write(f"| {low}-{high} | {count} | {percentage:.1f}% | {interpretation} |\n")
        
        # Top 50 Positive Verse (die höchsten Scores)
        f.write("\n## Top 50 Positive Verse\n\n")
        f.write("Die 50 Verse mit den höchsten BERT-Scores:\n\n")
        
        for i, verse in enumerate(scored_verses[:50], 1):
            f.write(f"### {i}. {verse['reference']} (BERT Score: {verse['bert_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            f.write(f"**BERT-Analyse**: {verse['bert_sentiment']} ")
            f.write(f"(Konfidenz: {verse['bert_confidence']})\n\n")
            f.write("---\n\n")
        
        # Mittlere 30 Verse (um die Mitte herum)
        f.write("## Mittlere 30 Verse\n\n")
        f.write("30 Verse aus der Mitte der Rangliste:\n\n")
        
        # Finde die Mitte
        middle_index = len(scored_verses) // 2
        start_index = middle_index - 15
        end_index = middle_index + 15
        
        for i, verse in enumerate(scored_verses[start_index:end_index], start_index + 1):
            f.write(f"### {i}. {verse['reference']} (BERT Score: {verse['bert_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            f.write(f"**BERT-Analyse**: {verse['bert_sentiment']} ")
            f.write(f"(Konfidenz: {verse['bert_confidence']})\n\n")
            f.write("---\n\n")
        
        # Bottom 30 Verse (die niedrigsten Scores)
        f.write("## Bottom 30 Verse\n\n")
        f.write("Die 30 Verse mit den niedrigsten BERT-Scores:\n\n")
        
        # Die letzten 30, aber in umgekehrter Reihenfolge nummeriert
        total = len(scored_verses)
        for i, verse in enumerate(scored_verses[-30:], total - 29):
            f.write(f"### {i}. {verse['reference']} (BERT Score: {verse['bert_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            f.write(f"**BERT-Analyse**: {verse['bert_sentiment']} ")
            f.write(f"(Konfidenz: {verse['bert_confidence']})\n\n")
            f.write("---\n\n")
        
        # Interessante Fälle (nur wenn vorhanden)
        f.write("## Interessante Fälle\n\n")
        
        # Höchste Konfidenz POSITIVE
        positive_verses = [v for v in scored_verses if v['bert_sentiment'] == 'POSITIVE']
        if positive_verses:
            most_confident_positive = max(positive_verses, key=lambda x: x['bert_confidence'])
            f.write(f"### Höchste Positive Konfidenz: {most_confident_positive['reference']}\n\n")
            f.write(f"> {most_confident_positive['text']}\n\n")
            f.write(f"**Konfidenz**: {most_confident_positive['bert_confidence']}\n\n")
        
        # Höchste Konfidenz NEGATIVE
        negative_verses = [v for v in scored_verses if v['bert_sentiment'] == 'NEGATIVE']
        if negative_verses:
            most_confident_negative = max(negative_verses, key=lambda x: x['bert_confidence'])
            f.write(f"### Höchste Negative Konfidenz: {most_confident_negative['reference']}\n\n")
            f.write(f"> {most_confident_negative['text']}\n\n")
            f.write(f"**Konfidenz**: {most_confident_negative['bert_confidence']}\n\n")
        
    print(f"\n✓ Report gespeichert: {report_file}")
    return report_file


def main():
    """Hauptfunktion."""
    print("=== BERT-Only Sentiment Scoring ===\n")
    
    # Pfade
    base_path = "/Users/ulrichprobst/Library/Mobile Documents/com~apple~CloudDocs/1 Uli Dokumente/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/ngue-bvs-app"
    
    # Suche nach der top_1000 Datei
    results_dir = os.path.join(base_path, "tests/positivity-scoring/results")
    
    # Finde die neueste top_1000 Datei
    top_1000_files = [f for f in os.listdir(results_dir) if f.startswith("top_1000_verses_")]
    
    if top_1000_files:
        # Nimm die neueste
        top_1000_files.sort()
        input_file = os.path.join(results_dir, top_1000_files[-1])
        print(f"Verwende: {top_1000_files[-1]}")
    else:
        # Fallback auf 100er Subset
        print("Keine top_1000 Datei gefunden. Verwende 100er Subset.")
        input_file = os.path.join(base_path, "tests/vector-poc/verses_subset_100.json")
    
    # Scorer initialisieren
    scorer = BertOnlyScorer()
    
    # Verse laden
    print("\nLade Verse...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Prüfe ob es die top_1000 Struktur ist
    if 'verses' in data:
        verses = data['verses']
    elif 'scored_verses' in data:
        # Bei top_1000 Format
        verses = data['scored_verses']
    else:
        print("Unbekanntes Dateiformat!")
        return
    
    print(f"✓ {len(verses)} Verse geladen\n")
    
    # BERT-Scoring
    scored_verses = scorer.score_verses_batch(verses)
    
    # Ergebnisse speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON speichern
    json_file = os.path.join(results_dir, f"bert_only_scores_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_verses': len(scored_verses),
                'timestamp': timestamp,
                'model': 'oliverguhr/german-sentiment-bert',
                'source_file': os.path.basename(input_file)
            },
            'scored_verses': scored_verses  # Bereits nach BERT-Score sortiert (höchster zuerst)
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✓ JSON gespeichert: {json_file}")
    
    # Report generieren
    report_file = generate_bert_report(scored_verses, results_dir)
    
    # Zusammenfassung
    print("\n=== ZUSAMMENFASSUNG ===\n")
    print(f"Analysierte Verse: {len(scored_verses)}")
    
    # Sentiment-Verteilung
    sentiments = [v['bert_sentiment'] for v in scored_verses]
    print(f"\nSentiment-Verteilung:")
    print(f"- POSITIVE: {sentiments.count('POSITIVE')} ({sentiments.count('POSITIVE')/len(sentiments)*100:.1f}%)")
    print(f"- NEGATIVE: {sentiments.count('NEGATIVE')} ({sentiments.count('NEGATIVE')/len(sentiments)*100:.1f}%)")
    print(f"- NEUTRAL: {sentiments.count('NEUTRAL')} ({sentiments.count('NEUTRAL')/len(sentiments)*100:.1f}%)")
    
    # Top 10 ausgeben
    print("\nTop 10 Positive Verse (nach BERT-Score):\n")
    for i, verse in enumerate(scored_verses[:10], 1):
        print(f"{i}. {verse['reference']} (Score: {verse['bert_score']})")
        print(f"   \"{verse['text'][:80]}...\"")
        print(f"   BERT: {verse['bert_sentiment']} (Konfidenz: {verse['bert_confidence']})\n")
    
    # Bottom 5
    print("\nBottom 5 Verse (niedrigste BERT-Scores):\n")
    total = len(scored_verses)
    for i, verse in enumerate(scored_verses[-5:], total - 4):
        print(f"{i}. {verse['reference']} (Score: {verse['bert_score']})")
        print(f"   \"{verse['text'][:80]}...\"")
        print(f"   BERT: {verse['bert_sentiment']} (Konfidenz: {verse['bert_confidence']})\n")
    
    print("✓ Analyse abgeschlossen!")


if __name__ == "__main__":
    main()
