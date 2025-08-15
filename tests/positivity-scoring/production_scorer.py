#!/usr/bin/env python3
"""
Production Positivity-Scoring für alle 11.003 Bibelverse
Erweitert den Test-Script für Vollproduktion mit Batch API Support

Dieser Code wurde mit Unterstützung von Claude (Anthropic AI) entwickelt 
- konzipiert und geprompted von Ulrich Probst
"""

import json
import os
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path

# API-Clients
try:
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

class ProductionPositivityScorer:
    """Production-ready Positivity Scorer für alle 11.003 Bibelverse."""
    
    def __init__(self, api_key: str, use_batch_api: bool = True):
        if not ANTHROPIC_AVAILABLE:
            raise ValueError("Anthropic client nicht verfügbar. pip install anthropic")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.use_batch_api = use_batch_api
        self.batch_size = 1000
        self.max_retries = 3
        self.retry_delay = 2
        
        # Pfade
        base_path = Path(__file__).parent.parent.parent
        self.input_file = base_path / "tests/vector-poc/final_verses_data.json"
        self.output_dir = base_path / "tests/positivity-scoring/results"
        self.progress_file = self.output_dir / "scoring_progress.json"
        
        # Optimiertes Prompt (Version 2.0)
        self.system_prompt = """Du bist ein Experte für biblische Texte. Bewerte Bibelverse für eine Spenden-App, 
wo Menschen positive, ermutigende Verse sponsern können.

WICHTIG: Bei der Bewertung konzentriere dich auf die EMOTIONALE WIRKUNG und ERMUTIGUNG für moderne Leser.
Berücksichtige dabei AUCH die kulturelle Bedeutung und Bekanntheit des Verses - 
bekannte Trost- und Hoffnungsverse sind für Spender besonders attraktiv.

Bewertungskriterien (erweitert):
- 95-100: SEHR POSITIV - Starke Verheißungen, Segen, Trost, bedingungslose Liebe Gottes
- 85-94: POSITIV+ - Hoffnung, Ermutigung, Weisheit, inspirierende Lehre
- 70-84: POSITIV - Glaube, gute Lehre, aufbauende Inhalte
- 55-69: NEUTRAL+ - Lehrreich, historisch mit leicht positiven Elementen  
- 40-54: NEUTRAL - Rein beschreibend, historisch, ohne emotionale Färbung
- 25-39: GEMISCHT - Positive und negative Elemente ausgewogen
- 10-24: NEGATIV - Warnungen, Tadel, schwere Themen
- 0-9: SEHR NEGATIV - Tod, Zerstörung, Strafe, Gewalt, Zorn

KONTEXT: Dieser Vers wird einzeln auf einem Zertifikat stehen. Bewerte seine Wirkung als Einzelvers.

WICHTIG: Antworte AUSSCHLIESSLICH mit einer Zahl zwischen 0 und 100. Keine Begründung, keine Erklärung, kein zusätzlicher Text - nur die Zahl."""

    def load_verses(self) -> List[Dict]:
        """Lädt alle Verse aus der JSON-Datei."""
        print(f"Lade Verse aus: {self.input_file}")
        
        if not self.input_file.exists():
            raise FileNotFoundError(f"Verse-Datei nicht gefunden: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        verses = data.get('verses', [])
        print(f"✓ {len(verses)} Verse geladen")
        return verses

    def load_progress(self) -> Dict:
        """Lädt den Fortschritt aus der Progress-Datei."""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'completed_verses': [],
            'failed_verses': [],
            'current_batch': 0,
            'total_batches': 0,
            'start_time': None
        }

    def save_progress(self, progress: Dict):
        """Speichert den aktuellen Fortschritt."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def score_verse_single(self, verse: Dict) -> Dict:
        """Bewertet einen einzelnen Vers mit der regulären API."""
        verse_text = verse['text']
        reference = verse.get('reference', 'Unknown')
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=10,
                    temperature=0,
                    system=self.system_prompt,
                    messages=[{
                        "role": "user",
                        "content": f"Vers: {verse_text}"
                    }]
                )
                
                score_text = response.content[0].text.strip()
                # Extrahiere nur die erste Zahl (vor "Begründung" oder Newlines)
                import re
                numbers = re.findall(r'\d+', score_text)
                if numbers:
                    score = int(numbers[0])
                else:
                    raise ValueError(f"Keine Zahl gefunden in: {score_text}")
                score = min(100, max(0, score))  # Clamp zwischen 0-100
                
                return {
                    'reference': reference,
                    'book': verse.get('book', ''),
                    'chapter': verse.get('chapter', 0),
                    'verse': verse.get('verse', 0),
                    'text': verse_text,
                    'positivity_score': score,
                    'scoring_model': 'claude-3-5-haiku',
                    'scoring_date': datetime.now().isoformat(),
                    'success': True
                }
                
            except Exception as e:
                print(f"  Fehler bei {reference} (Versuch {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                
        # Nach allen Versuchen fehlgeschlagen
        return {
            'reference': reference,
            'text': verse_text,
            'positivity_score': -1,
            'success': False,
            'error': 'Max retries exceeded'
        }

    def create_batch_requests(self, verses: List[Dict], batch_id: str) -> List[Request]:
        """Erstellt Batch-Anfragen für eine Liste von Versen."""
        requests = []
        
        for i, verse in enumerate(verses):
            custom_id = f"{batch_id}_verse_{i}_{verse.get('reference', 'unknown').replace('.', '_')}"
            
            request = Request(
                custom_id=custom_id,
                params=MessageCreateParamsNonStreaming(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=10,
                    temperature=0,
                    system=self.system_prompt,
                    messages=[
                        {"role": "user", "content": f"Vers: {verse['text']}"}
                    ]
                )
            )
            requests.append(request)
        
        return requests

    def process_batch_api(self, verses: List[Dict], batch_id: str = None) -> List[Dict]:
        """Verarbeitet Verse mit der Anthropic Batch API."""
        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"📦 Erstelle Batch-Anfrage '{batch_id}' für {len(verses)} Verse...")
        
        try:
            # Batch-Anfragen erstellen
            requests = self.create_batch_requests(verses, batch_id)
            
            # Batch erstellen
            print("📤 Sende Batch an Anthropic...")
            message_batch = self.client.messages.batches.create(requests=requests)
            
            batch_api_id = message_batch.id
            print(f"✅ Batch erstellt: {batch_api_id}")
            print(f"🔄 Status: {message_batch.processing_status}")
            
            # Warten auf Completion
            print("⏳ Warte auf Batch-Verarbeitung...")
            while True:
                batch_status = self.client.messages.batches.retrieve(batch_api_id)
                status = batch_status.processing_status
                
                print(f"   Status: {status} | Fortschritt: {batch_status.request_counts}")
                
                if status == "ended":
                    print("✅ Batch verarbeitung abgeschlossen!")
                    break
                elif status == "failed":
                    print("❌ Batch-Verarbeitung fehlgeschlagen!")
                    return self.process_sequential(verses)  # Fallback
                elif status in ["canceling", "canceled"]:
                    print("🚫 Batch wurde abgebrochen!")
                    return self.process_sequential(verses)  # Fallback
                
                # Warte 30 Sekunden vor nächster Status-Prüfung
                time.sleep(30)
            
            # Ergebnisse abrufen
            print("📥 Lade Batch-Ergebnisse...")
            scored_verses = []
            
            results_stream = self.client.messages.batches.results(batch_api_id)
            verse_lookup = {f"{batch_id}_verse_{i}_{v.get('reference', 'unknown').replace('.', '_')}": v 
                          for i, v in enumerate(verses)}
            
            for result_entry in results_stream:
                custom_id = result_entry.custom_id
                original_verse = verse_lookup.get(custom_id)
                
                if not original_verse:
                    print(f"⚠️  Vers für custom_id '{custom_id}' nicht gefunden")
                    continue
                
                if result_entry.result.type == "succeeded":
                    # Erfolgreiche Antwort verarbeiten
                    try:
                        score_text = result_entry.result.message.content[0].text.strip()
                        # Extrahiere nur die erste Zahl (vor "Begründung" oder Newlines)
                        import re
                        numbers = re.findall(r'\d+', score_text)
                        if numbers:
                            score = int(numbers[0])
                        else:
                            raise ValueError(f"Keine Zahl gefunden in: {score_text}")
                        score = min(100, max(0, score))
                        
                        scored_verse = {
                            'reference': original_verse.get('reference', 'Unknown'),
                            'book': original_verse.get('book', ''),
                            'chapter': original_verse.get('chapter', 0),
                            'verse': original_verse.get('verse', 0),
                            'text': original_verse['text'],
                            'positivity_score': score,
                            'scoring_model': 'claude-3-5-haiku-batch',
                            'scoring_date': datetime.now().isoformat(),
                            'success': True,
                            'batch_id': batch_api_id
                        }
                        scored_verses.append(scored_verse)
                        
                    except (ValueError, IndexError) as e:
                        print(f"⚠️  Fehler beim Parsen der Antwort für {custom_id}: {e}")
                        scored_verses.append({
                            'reference': original_verse.get('reference', 'Unknown'),
                            'text': original_verse['text'],
                            'positivity_score': -1,
                            'success': False,
                            'error': f'Parse error: {e}',
                            'batch_id': batch_api_id
                        })
                
                elif result_entry.result.type == "errored":
                    # Fehlerhafte Antwort
                    error_msg = result_entry.result.error.message if hasattr(result_entry.result, 'error') else 'Unknown error'
                    scored_verses.append({
                        'reference': original_verse.get('reference', 'Unknown'),
                        'text': original_verse['text'],
                        'positivity_score': -1,
                        'success': False,
                        'error': f'Batch API error: {error_msg}',
                        'batch_id': batch_api_id
                    })
            
            print(f"✅ {len(scored_verses)} Verse aus Batch verarbeitet")
            return scored_verses
            
        except Exception as e:
            print(f"❌ Batch API Fehler: {e}")
            print("🔄 Fallback auf Sequential Processing...")
            return self.process_sequential(verses)

    def process_sequential(self, verses: List[Dict]) -> List[Dict]:
        """Verarbeitet Verse sequenziell mit Rate Limiting."""
        scored_verses = []
        total = len(verses)
        
        print(f"\nVerarbeite {total} Verse sequenziell...")
        
        for i, verse in enumerate(verses, 1):
            reference = verse.get('reference', f'Vers_{i}')
            print(f"  {i}/{total}: {reference}...", end='', flush=True)
            
            scored = self.score_verse_single(verse)
            scored_verses.append(scored)
            
            if scored['success']:
                print(f" Score: {scored['positivity_score']}")
            else:
                print(" FEHLER")
            
            # Rate Limiting: 200 requests/minute = 300ms Delay
            if i < total:
                time.sleep(0.35)
        
        return scored_verses

    def run_benchmark_test(self, num_verses: int = 500) -> Tuple[List[Dict], Dict]:
        """Führt einen Benchmark-Test mit einer Stichprobe von Versen durch."""
        print(f"\n=== BENCHMARK TEST ({num_verses} Verse) ===")
        
        # Lade alle Verse
        all_verses = self.load_verses()
        
        # Zufällige Stichprobe
        benchmark_verses = random.sample(all_verses, min(num_verses, len(all_verses)))
        print(f"Zufällige Stichprobe von {len(benchmark_verses)} Versen ausgewählt")
        
        # Verarbeitung
        start_time = time.time()
        if self.use_batch_api:
            scored_verses = self.process_batch_api(benchmark_verses)
        else:
            scored_verses = self.process_sequential(benchmark_verses)
        
        duration = time.time() - start_time
        
        # Analyse
        analysis = self.analyze_results(scored_verses)
        analysis['duration_seconds'] = round(duration, 2)
        analysis['verses_per_minute'] = round(len(scored_verses) / (duration / 60), 1)
        
        print(f"\n✓ Benchmark abgeschlossen in {duration:.1f} Sekunden")
        print(f"  Geschwindigkeit: {analysis['verses_per_minute']} Verse/Minute")
        
        return scored_verses, analysis

    def analyze_results(self, scored_verses: List[Dict]) -> Dict:
        """Analysiert die Scoring-Ergebnisse."""
        successful = [v for v in scored_verses if v.get('success', False)]
        scores = [v['positivity_score'] for v in successful]
        
        if not scores:
            return {'error': 'Keine erfolgreichen Bewertungen'}
        
        # Score-Verteilung
        ranges = [
            (95, 100, "Sehr positiv"),
            (85, 94, "Positiv+"),
            (70, 84, "Positiv"),
            (55, 69, "Neutral+"),
            (40, 54, "Neutral"),
            (25, 39, "Gemischt"),
            (10, 24, "Negativ"),
            (0, 9, "Sehr negativ")
        ]
        
        distribution = {}
        for low, high, desc in ranges:
            if low == 95:  # Oberster Bereich inklusiv
                count = len([s for s in scores if low <= s <= high])
            else:
                count = len([s for s in scores if low <= s < high])
            pct = count / len(scores) * 100
            distribution[desc] = {'count': count, 'percentage': round(pct, 1)}
        
        return {
            'total_verses': len(scored_verses),
            'successful_scores': len(successful),
            'failed_scores': len(scored_verses) - len(successful),
            'success_rate': round(len(successful) / len(scored_verses) * 100, 1),
            'average_score': round(sum(scores) / len(scores), 1),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'distribution': distribution
        }

    def run_full_production(self) -> Tuple[List[Dict], Dict]:
        """Führt das komplette Scoring aller 11.003 Verse durch."""
        print("\n=== VOLLPRODUKTION (11.003 Verse) ===")
        
        # Lade Verse und Progress
        all_verses = self.load_verses()
        progress = self.load_progress()
        
        # Bereits verarbeitete Verse ausschließen
        completed_refs = {v['reference'] for v in progress.get('completed_verses', [])}
        remaining_verses = [v for v in all_verses if v.get('reference') not in completed_refs]
        
        print(f"Bereits verarbeitet: {len(completed_refs)}")
        print(f"Verbleibend: {len(remaining_verses)}")
        
        if not remaining_verses:
            print("✓ Alle Verse bereits verarbeitet!")
            return progress.get('completed_verses', []), {}
        
        # Zeige Kosten (automatisch bestätigt)
        estimated_cost = len(remaining_verses) * 0.0002  # Konservative Schätzung
        print(f"\n💰 Geschätzte Kosten: ~${estimated_cost:.2f}")
        print("🔥 Automatisch bestätigt - Vollproduktion startet!")
        
        # Progress initialisieren
        if not progress.get('start_time'):
            progress['start_time'] = datetime.now().isoformat()
            progress['total_verses'] = len(all_verses)
        
        # Verarbeitung
        start_time = time.time()
        
        if self.use_batch_api:
            # Batch-Verarbeitung in 1000er-Gruppen
            scored_verses = []
            batches = [remaining_verses[i:i+self.batch_size] for i in range(0, len(remaining_verses), self.batch_size)]
            
            for batch_num, batch_verses in enumerate(batches, 1):
                print(f"\nBatch {batch_num}/{len(batches)} ({len(batch_verses)} Verse)")
                batch_id = f"production_batch_{batch_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                batch_results = self.process_batch_api(batch_verses, batch_id)
                scored_verses.extend(batch_results)
                
                # Progress speichern
                progress['completed_verses'].extend([v for v in batch_results if v.get('success')])
                progress['failed_verses'].extend([v for v in batch_results if not v.get('success')])
                progress['current_batch'] = batch_num
                progress['total_batches'] = len(batches)
                self.save_progress(progress)
        else:
            # Sequential Processing
            scored_verses = self.process_sequential(remaining_verses)
            progress['completed_verses'].extend([v for v in scored_verses if v.get('success')])
            progress['failed_verses'].extend([v for v in scored_verses if not v.get('success')])
            self.save_progress(progress)
        
        duration = time.time() - start_time
        
        # Kombiniere mit bereits verarbeiteten Versen
        all_scored = progress.get('completed_verses', []) + scored_verses
        analysis = self.analyze_results(all_scored)
        analysis['duration_seconds'] = round(duration, 2)
        
        print(f"\n✓ Vollproduktion abgeschlossen in {duration/3600:.1f} Stunden")
        
        return all_scored, analysis

    def save_results(self, scored_verses: List[Dict], analysis: Dict, prefix: str = "production"):
        """Speichert die Ergebnisse in JSON und Markdown."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON speichern
        json_file = self.output_dir / f"{prefix}_scores_{timestamp}.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': timestamp,
                    'model': 'claude-3-5-haiku',
                    'total_verses': len(scored_verses),
                    'use_batch_api': self.use_batch_api,
                    **analysis
                },
                'scored_verses': scored_verses
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✓ JSON gespeichert: {json_file}")
        
        # Markdown Report
        md_file = self.output_dir / f"{prefix}_analysis_{timestamp}.md"
        self.generate_markdown_report(scored_verses, analysis, md_file)
        print(f"✓ Report gespeichert: {md_file}")
        
        return json_file, md_file

    def generate_markdown_report(self, scored_verses: List[Dict], analysis: Dict, output_file: Path):
        """Generiert einen detaillierten Markdown-Report."""
        successful_verses = [v for v in scored_verses if v.get('success', False)]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Production Positivity-Scoring Report\n\n")
            f.write(f"**Generiert am**: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}\n")
            f.write(f"**Modell**: Claude 3.5 Haiku\n")
            f.write(f"**Batch API**: {'Ja' if self.use_batch_api else 'Nein'}\n\n")
            
            # Statistiken
            f.write("## Statistiken\n\n")
            f.write(f"- **Verarbeitete Verse**: {analysis.get('total_verses', 0)}\n")
            f.write(f"- **Erfolgreiche Bewertungen**: {analysis.get('successful_scores', 0)}\n")
            f.write(f"- **Fehlgeschlagene Bewertungen**: {analysis.get('failed_scores', 0)}\n")
            f.write(f"- **Erfolgsrate**: {analysis.get('success_rate', 0)}%\n")
            f.write(f"- **Durchschnittsscore**: {analysis.get('average_score', 0)}\n")
            f.write(f"- **Höchster Score**: {analysis.get('highest_score', 0)}\n")
            f.write(f"- **Niedrigster Score**: {analysis.get('lowest_score', 0)}\n")
            
            if 'duration_seconds' in analysis:
                f.write(f"- **Verarbeitungszeit**: {analysis['duration_seconds']} Sekunden\n")
            if 'verses_per_minute' in analysis:
                f.write(f"- **Geschwindigkeit**: {analysis['verses_per_minute']} Verse/Minute\n")
            
            # Score-Verteilung
            f.write("\n## Score-Verteilung\n\n")
            f.write("| Bereich | Beschreibung | Anzahl | Prozent |\n")
            f.write("|---------|--------------|--------|---------|\n")
            
            distribution = analysis.get('distribution', {})
            for desc, data in distribution.items():
                f.write(f"| - | {desc} | {data['count']} | {data['percentage']}% |\n")
            
            # Top Verse
            if successful_verses:
                successful_verses.sort(key=lambda x: x['positivity_score'], reverse=True)
                
                f.write("\n## Top 20 Positive Verse\n\n")
                for i, verse in enumerate(successful_verses[:20], 1):
                    f.write(f"### {i}. {verse['reference']} (Score: {verse['positivity_score']})\n\n")
                    f.write(f"> {verse['text']}\n\n")
                    f.write("---\n\n")


def main():
    """Hauptfunktion mit Menü."""
    print("=== Production Positivity Scorer ===\n")
    
    if not ANTHROPIC_AVAILABLE:
        print("❌ Anthropic Client nicht verfügbar. Installiere mit: pip install anthropic")
        return
    
    # API Key
    api_key = input("Anthropic API Key: ").strip()
    if not api_key:
        print("❌ API Key erforderlich!")
        return
    
    # Modus auswählen
    print("\nVerfügbare Modi:")
    print("1. Benchmark Test (500 Verse)")
    print("2. Vollproduktion (11.003 Verse)")
    print("3. Beide (Benchmark dann Vollproduktion)")
    
    mode = input("\nModus wählen (1/2/3): ").strip()
    
    # Batch API Option
    use_batch = input("Batch API verwenden? (j/n) [empfohlen: j]: ").lower() == 'j'
    
    try:
        scorer = ProductionPositivityScorer(api_key=api_key, use_batch_api=use_batch)
        
        if mode == "1" or mode == "3":
            # Benchmark Test
            scored_verses, analysis = scorer.run_benchmark_test(500)
            scorer.save_results(scored_verses, analysis, prefix="benchmark")
            
            if mode == "3":
                proceed = input("\nBenchmark erfolgreich. Vollproduktion starten? (j/n): ").lower()
                if proceed != 'j':
                    print("Vollproduktion abgebrochen.")
                    return
        
        if mode == "2" or mode == "3":
            # Vollproduktion
            scored_verses, analysis = scorer.run_full_production()
            if scored_verses:
                scorer.save_results(scored_verses, analysis, prefix="production")
        
        print("\n✅ Alle Aufgaben abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return


if __name__ == "__main__":
    main()