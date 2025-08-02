#!/usr/bin/env python3
"""
LLM-basiertes Positivitäts-Scoring für Bibelverse
Test mit 100 Versen - verschiedene APIs unterstützt
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import sys

# API-Clients (optional)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests  # Für Ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class LLMScorer:
    """Bewertet Bibelverse mit verschiedenen LLMs."""
    
    def __init__(self, api_type: str = "ollama", api_key: Optional[str] = None):
        self.api_type = api_type.lower()
        self.api_key = api_key
        
        # Prompt für alle Modelle
        self.system_prompt = """Du bist ein Experte für biblische Texte. Bewerte Bibelverse für eine Spenden-App, 
wo Menschen positive, ermutigende Verse sponsern können.

Bewertungskriterien:
- 90-100: Sehr positiv - Verheißungen, Segen, Trost, Ermutigung, Gottes Liebe
- 70-89: Positiv - Hoffnung, Glaube, Weisheit, gute Lehre
- 50-69: Neutral - Historisch, beschreibend, lehrreich ohne starke Emotion
- 30-49: Gemischt - Enthält sowohl positive als auch negative Elemente
- 10-29: Negativ - Warnungen, Tadel, Gericht
- 0-9: Sehr negativ - Tod, Zerstörung, Strafe, Zorn

Antworte NUR mit einer Zahl zwischen 0 und 100."""

        # API-Client initialisieren
        if self.api_type == "anthropic" and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=api_key)
        elif self.api_type == "openai" and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=api_key)
        elif self.api_type == "ollama" and OLLAMA_AVAILABLE:
            self.ollama_url = "http://localhost:11434/api/generate"
        else:
            raise ValueError(f"API-Typ '{api_type}' nicht verfügbar oder nicht unterstützt")
    
    def score_verse_anthropic(self, verse_text: str) -> int:
        """Bewertet einen Vers mit Claude."""
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Günstigstes Modell
                max_tokens=10,
                temperature=0,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Vers: {verse_text}"
                }]
            )
            score = int(response.content[0].text.strip())
            return min(100, max(0, score))
        except Exception as e:
            print(f"Anthropic API Fehler: {e}")
            return -1
    
    def score_verse_openai(self, verse_text: str) -> int:
        """Bewertet einen Vers mit OpenAI GPT."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Vers: {verse_text}"}
                ],
                temperature=0,
                max_tokens=10
            )
            score = int(response.choices[0].message.content.strip())
            return min(100, max(0, score))
        except Exception as e:
            print(f"OpenAI API Fehler: {e}")
            return -1
    
    def score_verse_ollama(self, verse_text: str, model: str = "mixtral") -> int:
        """Bewertet einen Vers mit lokalem Ollama."""
        try:
            prompt = f"{self.system_prompt}\n\nVers: {verse_text}\n\nScore:"
            
            response = requests.post(self.ollama_url, json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'temperature': 0
            })
            
            if response.status_code == 200:
                result = response.json()
                # Extrahiere nur die Zahl aus der Antwort
                score_text = result['response'].strip()
                # Versuche die erste Zahl zu finden
                import re
                numbers = re.findall(r'\d+', score_text)
                if numbers:
                    score = int(numbers[0])
                    return min(100, max(0, score))
            return -1
        except Exception as e:
            print(f"Ollama API Fehler: {e}")
            return -1
    
    def score_verse(self, verse: Dict) -> Dict:
        """Bewertet einen einzelnen Vers."""
        verse_text = verse['text']
        
        # Score basierend auf API-Typ
        if self.api_type == "anthropic":
            score = self.score_verse_anthropic(verse_text)
        elif self.api_type == "openai":
            score = self.score_verse_openai(verse_text)
        elif self.api_type == "ollama":
            score = self.score_verse_ollama(verse_text)
        else:
            score = -1
        
        return {
            'verse_id': verse.get('id', ''),
            'reference': verse.get('reference', ''),
            'book': verse.get('book', ''),
            'chapter': verse.get('chapter', 0),
            'verse': verse.get('verse', 0),
            'text': verse_text,
            'llm_score': score,
            'llm_model': self.api_type
        }
    
    def score_verses_batch(self, verses: List[Dict], delay: float = 0.5) -> List[Dict]:
        """Bewertet mehrere Verse mit Verzögerung zwischen Anfragen."""
        scored_verses = []
        total = len(verses)
        
        print(f"\nBewerte {total} Verse mit {self.api_type.upper()}...\n")
        
        for i, verse in enumerate(verses, 1):
            print(f"Verarbeite Vers {i}/{total}: {verse.get('reference', '')}...", end='', flush=True)
            
            scored = self.score_verse(verse)
            scored_verses.append(scored)
            
            if scored['llm_score'] >= 0:
                print(f" Score: {scored['llm_score']}")
            else:
                print(" FEHLER")
            
            # Verzögerung zwischen Anfragen (API-Limits)
            if i < total:
                time.sleep(delay)
        
        # Nach Score sortieren
        scored_verses.sort(key=lambda x: x['llm_score'], reverse=True)
        
        return scored_verses


def generate_llm_report(scored_verses: List[Dict], output_path: str, api_type: str):
    """Generiert einen Report der LLM-Bewertungen."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_path, f"llm_{api_type}_analysis_{timestamp}.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# LLM-basierte Positivitäts-Analyse ({api_type.upper()})\n\n")
        f.write(f"**Generiert am**: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}\n")
        f.write(f"**Modell**: {api_type}\n")
        f.write(f"**Anzahl Verse**: {len(scored_verses)}\n\n")
        
        # Statistiken
        valid_scores = [v['llm_score'] for v in scored_verses if v['llm_score'] >= 0]
        if valid_scores:
            avg_score = sum(valid_scores) / len(valid_scores)
            
            f.write("## Statistiken\n\n")
            f.write(f"- **Erfolgreiche Bewertungen**: {len(valid_scores)}/{len(scored_verses)}\n")
            f.write(f"- **Durchschnittsscore**: {avg_score:.1f}/100\n")
            f.write(f"- **Höchster Score**: {max(valid_scores)}\n")
            f.write(f"- **Niedrigster Score**: {min(valid_scores)}\n\n")
            
            # Score-Verteilung
            f.write("## Score-Verteilung\n\n")
            f.write("| Bereich | Beschreibung | Anzahl | Prozent |\n")
            f.write("|---------|--------------|--------|----------|\n")
            
            ranges = [
                (90, 100, "Sehr positiv"),
                (70, 89, "Positiv"),
                (50, 69, "Neutral"),
                (30, 49, "Gemischt"),
                (10, 29, "Negativ"),
                (0, 9, "Sehr negativ")
            ]
            
            for low, high, desc in ranges:
                if low == 90:  # Letzter Bereich inklusiv
                    count = len([s for s in valid_scores if low <= s <= high])
                else:
                    count = len([s for s in valid_scores if low <= s < high])
                pct = count / len(valid_scores) * 100
                f.write(f"| {low}-{high} | {desc} | {count} | {pct:.1f}% |\n")
        
        # Top 20 Positive
        f.write("\n## Top 20 Positive Verse\n\n")
        top_verses = [v for v in scored_verses if v['llm_score'] >= 0][:20]
        
        for i, verse in enumerate(top_verses, 1):
            f.write(f"### {i}. {verse['reference']} (Score: {verse['llm_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            f.write("---\n\n")
        
        # Mittlere 10
        f.write("## Mittlere 10 Verse\n\n")
        if len(valid_scores) > 30:
            mid_start = len(valid_scores) // 2 - 5
            mid_verses = [v for v in scored_verses if v['llm_score'] >= 0][mid_start:mid_start+10]
            
            for verse in mid_verses:
                f.write(f"### {verse['reference']} (Score: {verse['llm_score']})\n\n")
                f.write(f"> {verse['text']}\n\n")
                f.write("---\n\n")
        
        # Bottom 10
        f.write("## Bottom 10 Verse\n\n")
        bottom_verses = [v for v in scored_verses if v['llm_score'] >= 0][-10:]
        
        for verse in bottom_verses:
            f.write(f"### {verse['reference']} (Score: {verse['llm_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
            f.write("---\n\n")
    
    print(f"\n✓ Report gespeichert: {report_file}")
    return report_file


def main():
    """Hauptfunktion."""
    print("=== LLM-basiertes Bibelvers-Scoring (Test) ===\n")
    
    # API-Auswahl
    print("Verfügbare APIs:")
    if OLLAMA_AVAILABLE:
        print("1. Ollama (lokal, kostenlos)")
    if OPENAI_AVAILABLE:
        print("2. OpenAI GPT-3.5")
    if ANTHROPIC_AVAILABLE:
        print("3. Anthropic Claude")
    
    # Wähle API
    api_choice = input("\nWelche API möchtest du verwenden? (1/2/3): ").strip()
    
    if api_choice == "1" and OLLAMA_AVAILABLE:
        api_type = "ollama"
        api_key = None
        print("\nStelle sicher, dass Ollama läuft: ollama serve")
        model = input("Welches Modell? (mixtral/llama2/mistral) [mixtral]: ").strip() or "mixtral"
    elif api_choice == "2" and OPENAI_AVAILABLE:
        api_type = "openai"
        api_key = input("OpenAI API Key: ").strip()
    elif api_choice == "3" and ANTHROPIC_AVAILABLE:
        api_type = "anthropic"
        api_key = input("Anthropic API Key: ").strip()
    else:
        print("Ungültige Auswahl oder API nicht verfügbar!")
        return
    
    # Pfade
    base_path = "/Users/ulrichprobst/Library/Mobile Documents/com~apple~CloudDocs/1 Uli Dokumente/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/ngue-bvs-app"
    input_file = os.path.join(base_path, "tests/vector-poc/verses_subset_100.json")
    output_dir = os.path.join(base_path, "tests/positivity-scoring/results")
    
    # Scorer initialisieren
    try:
        scorer = LLMScorer(api_type=api_type, api_key=api_key)
    except Exception as e:
        print(f"Fehler beim Initialisieren: {e}")
        return
    
    # Verse laden
    print("\nLade 100 Test-Verse...")
    with open(input_file, 'r', encoding='utf-8') as f:
        verses_data = json.load(f)
    verses = verses_data['verses']
    print(f"✓ {len(verses)} Verse geladen")
    
    # Kosten-Warnung
    if api_type == "openai":
        print(f"\n⚠️  Geschätzte Kosten: ~${len(verses) * 0.0001:.2f}")
    elif api_type == "anthropic":
        print(f"\n⚠️  Geschätzte Kosten: ~${len(verses) * 0.00005:.2f}")
    
    proceed = input("\nFortfahren? (j/n): ").lower()
    if proceed != 'j':
        print("Abgebrochen.")
        return
    
    # Scoring durchführen
    start_time = time.time()
    scored_verses = scorer.score_verses_batch(verses, delay=0.5 if api_type != "ollama" else 0.1)
    duration = time.time() - start_time
    
    print(f"\n✓ Scoring abgeschlossen in {duration:.1f} Sekunden")
    
    # Ergebnisse speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON speichern
    json_file = os.path.join(output_dir, f"llm_{api_type}_scores_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_verses': len(scored_verses),
                'timestamp': timestamp,
                'model': api_type,
                'duration_seconds': round(duration, 2)
            },
            'scored_verses': scored_verses
        }, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON gespeichert: {json_file}")
    
    # Report generieren
    report_file = generate_llm_report(scored_verses, output_dir, api_type)
    
    # Top 5 ausgeben
    print("\n=== TOP 5 VERSE ===")
    for i, verse in enumerate(scored_verses[:5], 1):
        if verse['llm_score'] >= 0:
            print(f"\n{i}. {verse['reference']} (Score: {verse['llm_score']})")
            print(f"   \"{verse['text'][:80]}...\"")
    
    print("\n✓ Test abgeschlossen!")


if __name__ == "__main__":
    main()
