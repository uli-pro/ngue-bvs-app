#!/usr/bin/env python3
"""
Verbessertes Positivitäts-Scoring mit vortrainiertem BERT-Modell
Kombiniert Machine Learning mit domänenspezifischen Keywords
"""

import json
import os
from typing import Dict, List, Tuple
from datetime import datetime
import numpy as np

# Transformers für Sentiment Analysis
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warnung: transformers nicht installiert. Fallback auf Keyword-Methode.")
    TRANSFORMERS_AVAILABLE = False

class HybridPositivityScorer:
    """Kombiniert BERT-basierte Sentiment-Analyse mit biblischen Keywords."""
    
    def __init__(self, use_bert=True):
        self.use_bert = use_bert and TRANSFORMERS_AVAILABLE
        
        if self.use_bert:
            print("Lade BERT-Modell für Sentiment-Analyse...")
            # Deutsches Sentiment-Modell
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="oliverguhr/german-sentiment-bert",
                device=-1  # CPU verwenden
            )
            print("✓ Modell geladen")
        
        # Biblische Schlüsselwörter für Feinabstimmung
        self.biblical_positive = {
            # Göttliche Verheißungen
            'verheißung': 3.0, 'zusage': 3.0, 'versprechen': 2.5,
            'bund': 2.5, 'erwählt': 2.5, 'auserwählt': 3.0,
            
            # Segen und Gnade
            'segen': 3.0, 'segnen': 3.0, 'gesegnet': 3.0,
            'gnade': 3.0, 'gnädig': 3.0, 'barmherzig': 3.0,
            
            # Erlösung
            'erlösung': 3.0, 'erlöst': 3.0, 'erlöser': 3.0,
            'heil': 3.0, 'heiland': 3.0, 'retter': 3.0,
            'befreit': 2.5, 'befreiung': 2.5,
            
            # Trost und Ermutigung
            'trost': 2.5, 'trösten': 2.5, 'ermutigung': 2.5,
            'mut': 2.0, 'getrost': 2.5, 'zuversicht': 2.5,
            
            # Ewiges Leben
            'ewiges leben': 3.0, 'ewigkeit': 2.5, 'auferstehung': 3.0,
            'himmelreich': 3.0, 'paradies': 3.0,
            
            # Lobpreis
            'halleluja': 3.0, 'lobpreis': 3.0, 'anbetung': 2.5,
            'ehre': 2.0, 'herrlichkeit': 2.5, 'majestät': 2.5
        }
        
        self.biblical_negative = {
            # Gericht und Strafe
            'gericht': -3.0, 'verdammnis': -3.0, 'verdammt': -3.0,
            'strafe': -2.5, 'züchtigung': -2.5, 'fluch': -3.0,
            
            # Sünde
            'sünde': -2.0, 'schuld': -2.0, 'übertreten': -2.0,
            'abfall': -2.5, 'gottlos': -2.5, 'verwerfung': -3.0,
            
            # Negative Endzustände
            'hölle': -3.0, 'feuersee': -3.0, 'abgrund': -3.0,
            'verderben': -3.0, 'untergang': -3.0
        }
        
        # Kontextuelle Verstärker
        self.positive_phrases = [
            'fürchte dich nicht',
            'ich bin bei dir',
            'ich will dich',
            'siehe, ich',
            'freut euch',
            'selig sind',
            'wohl dem'
        ]
        
        self.negative_phrases = [
            'wehe euch',
            'verflucht sei',
            'ihr werdet sterben',
            'es wird keine',
            'verlassen von gott'
        ]
    
    def get_bert_sentiment(self, text: str) -> Tuple[str, float]:
        """Holt BERT-basierte Sentiment-Bewertung."""
        if not self.use_bert:
            return 'NEUTRAL', 0.5
            
        try:
            # BERT-Analyse
            result = self.sentiment_pipeline(text)[0]
            label = result['label']
            score = result['score']
            
            # Mapping auf einheitliche Skala
            if label == 'POSITIVE':
                return 'POSITIVE', score
            elif label == 'NEGATIVE':
                return 'NEGATIVE', 1 - score  # Invertieren für einheitliche Skala
            else:
                return 'NEUTRAL', 0.5
                
        except Exception as e:
            print(f"BERT-Fehler: {e}")
            return 'NEUTRAL', 0.5
    
    def calculate_biblical_score(self, text: str) -> float:
        """Berechnet Score basierend auf biblischen Keywords."""
        text_lower = text.lower()
        score = 0.0
        
        # Positive Keywords
        for keyword, weight in self.biblical_positive.items():
            if keyword in text_lower:
                score += weight
                
        # Negative Keywords
        for keyword, weight in self.biblical_negative.items():
            if keyword in text_lower:
                score += weight  # weight ist bereits negativ
                
        # Phrasen-Bonus
        for phrase in self.positive_phrases:
            if phrase in text_lower:
                score += 2.0
                
        for phrase in self.negative_phrases:
            if phrase in text_lower:
                score -= 2.0
                
        return score
    
    def score_verse(self, verse: Dict) -> Dict:
        """Bewertet einen Vers mit Hybrid-Methode."""
        text = verse['text']
        
        # 1. BERT Sentiment Score (0-1 Skala)
        sentiment_label, bert_score = self.get_bert_sentiment(text)
        
        # 2. Biblischer Keyword Score
        biblical_score = self.calculate_biblical_score(text)
        
        # 3. Strukturelle Analyse
        structure_score = 0.0
        if text.count('!') > 0:
            structure_score += 0.5 * text.count('!')
        if text.count('?') > 1:  # Viele Fragen sind oft negativ
            structure_score -= 0.5
            
        # 4. Kombinierter Score
        # BERT hat 50% Gewicht, Keywords 40%, Struktur 10%
        if self.use_bert:
            # BERT Score auf -1 bis +1 normalisieren
            normalized_bert = (bert_score - 0.5) * 2
            if sentiment_label == 'NEGATIVE':
                normalized_bert = -normalized_bert
                
            combined_raw = (
                normalized_bert * 10 +  # BERT Komponente
                biblical_score * 0.8 +  # Keyword Komponente  
                structure_score         # Struktur Komponente
            )
        else:
            # Nur Keywords wenn BERT nicht verfügbar
            combined_raw = biblical_score + structure_score
        
        # Auf 0-100 Skala normalisieren
        final_score = max(0, min(100, (combined_raw + 15) * 3.33))
        
        return {
            'verse_id': verse.get('id', ''),
            'reference': verse.get('reference', ''),
            'book': verse.get('book', ''),
            'chapter': verse.get('chapter', 0),
            'verse': verse.get('verse', 0),
            'text': text,
            'positivity_score': round(final_score, 1),
            'bert_sentiment': sentiment_label if self.use_bert else 'N/A',
            'bert_confidence': round(bert_score, 3) if self.use_bert else 0,
            'biblical_score': round(biblical_score, 1),
            'structure_score': round(structure_score, 1)
        }
    
    def score_verses_batch(self, verses: List[Dict], batch_size: int = 32) -> List[Dict]:
        """Bewertet Verse in Batches für bessere Performance."""
        scored_verses = []
        total = len(verses)
        
        for i in range(0, total, batch_size):
            batch = verses[i:i + batch_size]
            print(f"Verarbeite Verse {i+1}-{min(i+batch_size, total)} von {total}...")
            
            for verse in batch:
                scored = self.score_verse(verse)
                scored_verses.append(scored)
                
        # Nach Score sortieren
        scored_verses.sort(key=lambda x: x['positivity_score'], reverse=True)
        return scored_verses


def generate_analysis_report(scored_verses: List[Dict], output_path: str):
    """Generiert detaillierten Analyse-Report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_path, f"hybrid_analysis_{timestamp}.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Hybrid Positivitäts-Analyse (BERT + Keywords)\n\n")
        f.write(f"**Generiert**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write(f"**Anzahl Verse**: {len(scored_verses)}\n\n")
        
        # Statistiken
        scores = [v['positivity_score'] for v in scored_verses]
        avg_score = sum(scores) / len(scores)
        
        # Sentiment-Verteilung (nur wenn BERT verwendet)
        if scored_verses[0]['bert_sentiment'] != 'N/A':
            sentiments = [v['bert_sentiment'] for v in scored_verses]
            f.write("## BERT Sentiment-Verteilung\n\n")
            f.write(f"- POSITIVE: {sentiments.count('POSITIVE')} ")
            f.write(f"({sentiments.count('POSITIVE')/len(sentiments)*100:.1f}%)\n")
            f.write(f"- NEGATIVE: {sentiments.count('NEGATIVE')} ")
            f.write(f"({sentiments.count('NEGATIVE')/len(sentiments)*100:.1f}%)\n")
            f.write(f"- NEUTRAL: {sentiments.count('NEUTRAL')} ")
            f.write(f"({sentiments.count('NEUTRAL')/len(sentiments)*100:.1f}%)\n\n")
        
        f.write("## Score-Statistiken\n\n")
        f.write(f"- Durchschnitt: {avg_score:.1f}\n")
        f.write(f"- Maximum: {max(scores):.1f}\n")
        f.write(f"- Minimum: {min(scores):.1f}\n")
        f.write(f"- Verse ≥ 70: {len([s for s in scores if s >= 70])}\n\n")
        
        # Top 30
        f.write("## Top 30 Positive Verse\n\n")
        for i, verse in enumerate(scored_verses[:30], 1):
            f.write(f"### {i}. {verse['reference']} (Score: {verse['positivity_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            
            if verse['bert_sentiment'] != 'N/A':
                f.write(f"**BERT**: {verse['bert_sentiment']} ")
                f.write(f"(Konfidenz: {verse['bert_confidence']})\n")
            f.write(f"**Biblisch**: {verse['biblical_score']}, ")
            f.write(f"**Struktur**: {verse['structure_score']}\n\n")
            f.write("---\n\n")
        
        # Bottom 10
        f.write("## Bottom 10 Verse\n\n")
        for verse in scored_verses[-10:]:
            f.write(f"### {verse['reference']} (Score: {verse['positivity_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            if verse['bert_sentiment'] != 'N/A':
                f.write(f"**BERT**: {verse['bert_sentiment']}\n")
            f.write("\n---\n\n")
            
    print(f"✓ Report gespeichert: {report_file}")
    return report_file


def main():
    """Hauptfunktion zum Testen."""
    print("=== Hybrid Positivitäts-Scoring ===\n")
    
    # Pfade
    base_path = "/Users/ulrichprobst/Library/Mobile Documents/com~apple~CloudDocs/1 Uli Dokumente/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/ngue-bvs-app"
    
    # Wähle Dataset
    use_full = input("Vollständiges Dataset (11k) verwenden? (j/n): ").lower() == 'j'
    if use_full:
        input_file = os.path.join(base_path, "tests/vector-poc/final_verses_data.json")
    else:
        input_file = os.path.join(base_path, "tests/vector-poc/verses_subset_100.json")
    
    output_dir = os.path.join(base_path, "tests/positivity-scoring/results")
    
    # BERT verwenden?
    use_bert = True
    if not TRANSFORMERS_AVAILABLE:
        print("\n⚠️  transformers nicht installiert!")
        print("Installiere mit: pip install transformers torch")
        use_bert = False
    
    # Scorer initialisieren
    print("\nInitialisiere Scorer...")
    scorer = HybridPositivityScorer(use_bert=use_bert)
    
    # Verse laden
    print("\nLade Verse...")
    with open(input_file, 'r', encoding='utf-8') as f:
        verses_data = json.load(f)
    verses = verses_data['verses']
    print(f"✓ {len(verses)} Verse geladen")
    
    # Scoring
    print("\nStarte Scoring...")
    if len(verses) > 1000:
        print("(Dies kann bei 11k Versen einige Minuten dauern...)")
    
    scored_verses = scorer.score_verses_batch(verses)
    
    # Ergebnisse speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON
    json_file = os.path.join(output_dir, f"hybrid_scored_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_verses': len(scored_verses),
                'timestamp': timestamp,
                'bert_used': use_bert,
                'model': 'oliverguhr/german-sentiment-bert' if use_bert else 'keywords_only'
            },
            'scored_verses': scored_verses
        }, f, ensure_ascii=False, indent=2)
    
    # Report
    report_file = generate_analysis_report(scored_verses, output_dir)
    
    # Top 5 ausgeben
    print("\n=== TOP 5 VERSE ===")
    for i, verse in enumerate(scored_verses[:5], 1):
        print(f"\n{i}. {verse['reference']} (Score: {verse['positivity_score']})")
        print(f"   \"{verse['text'][:80]}...\"")
        if verse['bert_sentiment'] != 'N/A':
            print(f"   BERT: {verse['bert_sentiment']}")
    
    print(f"\n✓ Fertig! Ergebnisse in: {output_dir}")


if __name__ == "__main__":
    main()
