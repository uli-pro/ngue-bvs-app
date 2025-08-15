#!/usr/bin/env python3
"""
Sauberer Test mit 100 echten Bibelversen
Mit verbessertem Prompt und Parsing + Markdown Report
"""

import os
import json
import time
import random
from datetime import datetime
from production_scorer import ProductionPositivityScorer

def run_clean_test():
    """Führt einen sauberen Test mit 100 echten Versen durch."""
    print("=== SAUBERER 100-VERSE TEST ===\n")
    
    # API Key aus Environment 
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        api_key = input("Anthropic API Key: ").strip()
        if not api_key:
            print("❌ API Key erforderlich!")
            return False
    
    try:
        # Scorer initialisieren (Sequential für kleineren Test)
        scorer = ProductionPositivityScorer(api_key=api_key, use_batch_api=False)
        
        print("🚀 Starte sauberen Test mit 100 echten Bibelversen...")
        print("📋 Modus: Sequential Processing (für bessere Kontrolle)")
        print("💰 Geschätzte Kosten: ~$0.02")
        
        # Lade alle Verse und wähle 100 zufällige aus
        all_verses = scorer.load_verses()
        test_verses = random.sample(all_verses, 100)
        
        print(f"✅ {len(test_verses)} zufällige Verse ausgewählt\n")
        
        # Zeige erste paar Verse als Beispiel
        print("📖 BEISPIEL-VERSE:")
        for i, verse in enumerate(test_verses[:3], 1):
            print(f"   {i}. {verse['reference']}: \"{verse['text'][:60]}...\"")
        print()
        
        # Starte Verarbeitung
        start_time = time.time()
        scored_verses = scorer.process_sequential(test_verses)
        duration = time.time() - start_time
        
        print(f"\n✅ Test abgeschlossen in {duration:.1f} Sekunden")
        
        # Analysiere Ergebnisse
        analysis = scorer.analyze_results(scored_verses)
        analysis['duration_seconds'] = round(duration, 2)
        analysis['verses_per_minute'] = round(len(scored_verses) / (duration / 60), 1)
        
        # Speichere Ergebnisse
        json_file, md_file = scorer.save_results(scored_verses, analysis, prefix="clean_test_100")
        
        print(f"\n📁 DATEIEN ERSTELLT:")
        print(f"   • JSON: {json_file}")
        print(f"   • Report: {md_file}")
        
        # Zeige Summary
        print(f"\n📊 QUICK SUMMARY:")
        print(f"   • Erfolgsrate: {analysis.get('success_rate', 0)}%")
        print(f"   • Durchschnittsscore: {analysis.get('average_score', 0)}")
        print(f"   • Höchster Score: {analysis.get('highest_score', 0)}")
        print(f"   • Niedrigster Score: {analysis.get('lowest_score', 0)}")
        
        # Top 5 Verse
        successful_verses = [v for v in scored_verses if v.get('success', False)]
        if successful_verses:
            successful_verses.sort(key=lambda x: x['positivity_score'], reverse=True)
            print(f"\n🏆 TOP 5 VERSE:")
            for i, verse in enumerate(successful_verses[:5], 1):
                score = verse['positivity_score']
                ref = verse['reference']
                text = verse['text'][:50] + "..." if len(verse['text']) > 50 else verse['text']
                print(f"   {i}. {ref} (Score: {score})")
                print(f"      \"{text}\"")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_clean_test()
    if success:
        print("\n✅ Sauberer Test erfolgreich!")
    else:
        print("\n❌ Test fehlgeschlagen!")