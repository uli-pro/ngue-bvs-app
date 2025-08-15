#!/usr/bin/env python3
"""
Test-Script für Benchmark mit 500 Versen
Vereinfachte Version für automatisierten Test
"""

import os
import json
from production_scorer import ProductionPositivityScorer

def run_benchmark_test():
    """Führt automatisch einen Benchmark-Test durch."""
    print("=== AUTOMATISCHER BENCHMARK TEST ===\n")
    
    # API Key aus Environment oder Benutzer-Input
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY Environment Variable nicht gesetzt!")
        print("Setze mit: export ANTHROPIC_API_KEY='dein-key-hier'")
        print("Oder füge ihn manuell ein:")
        api_key = input("Anthropic API Key: ").strip()
        if not api_key:
            print("❌ API Key erforderlich!")
            return False
    
    try:
        # Scorer mit Batch API initialisieren
        scorer = ProductionPositivityScorer(api_key=api_key, use_batch_api=True)
        
        print("🚀 Starte Benchmark Test mit 500 Versen...")
        print("📋 Modus: Batch API (falls verfügbar), sonst Sequential")
        print("💰 Geschätzte Kosten: ~$0.10")
        
        # Führe Benchmark durch
        scored_verses, analysis = scorer.run_benchmark_test(num_verses=500)
        
        if not scored_verses:
            print("❌ Benchmark fehlgeschlagen - keine Verse verarbeitet")
            return False
        
        # Speichere Ergebnisse
        json_file, md_file = scorer.save_results(scored_verses, analysis, prefix="benchmark")
        
        print("\n" + "="*60)
        print("✅ BENCHMARK TEST ERFOLGREICH ABGESCHLOSSEN!")
        print("="*60)
        
        # Zeige Zusammenfassung
        print(f"\n📊 ERGEBNISSE:")
        print(f"   • Verarbeitete Verse: {analysis.get('total_verses', 0)}")
        print(f"   • Erfolgsrate: {analysis.get('success_rate', 0)}%")
        print(f"   • Durchschnittsscore: {analysis.get('average_score', 0)}")
        print(f"   • Höchster Score: {analysis.get('highest_score', 0)}")
        print(f"   • Niedrigster Score: {analysis.get('lowest_score', 0)}")
        
        if 'duration_seconds' in analysis:
            print(f"   • Verarbeitungszeit: {analysis['duration_seconds']} Sekunden")
        if 'verses_per_minute' in analysis:
            print(f"   • Geschwindigkeit: {analysis['verses_per_minute']} Verse/Minute")
        
        print(f"\n📁 DATEIEN:")
        print(f"   • JSON: {json_file}")
        print(f"   • Report: {md_file}")
        
        # Score-Verteilung anzeigen
        if 'distribution' in analysis:
            print(f"\n📈 SCORE-VERTEILUNG:")
            for desc, data in analysis['distribution'].items():
                print(f"   • {desc}: {data['count']} Verse ({data['percentage']}%)")
        
        # Top 5 Verse zeigen
        successful_verses = [v for v in scored_verses if v.get('success', False)]
        if successful_verses:
            successful_verses.sort(key=lambda x: x['positivity_score'], reverse=True)
            print(f"\n🏆 TOP 5 POSITIVE VERSE:")
            for i, verse in enumerate(successful_verses[:5], 1):
                score = verse['positivity_score']
                ref = verse['reference']
                text = verse['text'][:60] + "..." if len(verse['text']) > 60 else verse['text']
                print(f"   {i}. {ref} (Score: {score})")
                print(f"      \"{text}\"")
        
        print(f"\n🎯 BEREIT FÜR VOLLPRODUKTION!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Benchmark: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_benchmark_test()
    if success:
        print("\n✅ Test erfolgreich - Vollproduktion kann gestartet werden!")
    else:
        print("\n❌ Test fehlgeschlagen - bitte Probleme beheben vor Vollproduktion!")