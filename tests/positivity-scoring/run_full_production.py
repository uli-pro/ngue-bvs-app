#!/usr/bin/env python3
"""
Vollproduktion: Alle 11.003 Bibelverse mit Positivity-Scores versehen
Finale Version für die NGÜ-App
"""

import os
import time
from datetime import datetime
from production_scorer import ProductionPositivityScorer

def run_full_production():
    """Startet die Vollproduktion für alle 11.003 Verse."""
    print("🚀 " + "="*60)
    print("    VOLLPRODUKTION: 11.003 BIBELVERSE SCORING")
    print("="*62 + "\n")
    
    # API Key aus Environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        api_key = input("Anthropic API Key: ").strip()
        if not api_key:
            print("❌ API Key erforderlich!")
            return False
    
    try:
        # Scorer mit Batch API initialisieren
        scorer = ProductionPositivityScorer(api_key=api_key, use_batch_api=True)
        
        print("📋 KONFIGURATION:")
        print("   • Modell: Claude 3.5 Haiku")
        print("   • Modus: Batch API (50% Rabatt)")
        print("   • Batch-Größe: 1.000 Verse pro Batch")
        print("   • Geschätzte Kosten: ~$0.99")
        print("   • Geschätzte Dauer: 1-2 Stunden")
        print("   • Progress-Tracking: Aktiviert")
        print("   • Automatische Zwischenspeicherung: Ja")
        
        print(f"\n⚠️  WICHTIG:")
        print(f"   • Dies verarbeitet ALLE 11.003 Verse")
        print(f"   • Der Prozess läuft automatisch und kann nicht pausiert werden")
        print(f"   • Bei Unterbrechung wird an der letzten Position fortgesetzt")
        
        print(f"\n💰 KOSTEN-BESTÄTIGUNG:")
        print(f"   • Batch API Preis: ~$0.99 (mit 50% Rabatt)")
        print(f"   • Pro Vers: ~$0.00009")
        
        # Automatischer Start (da bereits bestätigt)
        print(f"\n🔥 VOLLPRODUKTION AUTOMATISCH GESTARTET!")
        
        print(f"\n🎯 VOLLPRODUKTION GESTARTET um {datetime.now().strftime('%H:%M:%S')}")
        print("="*62)
        
        # Starte Vollproduktion
        start_time = time.time()
        scored_verses, analysis = scorer.run_full_production()
        total_duration = time.time() - start_time
        
        if not scored_verses:
            print("❌ Vollproduktion fehlgeschlagen - keine Verse verarbeitet")
            return False
        
        # Finale Analyse
        analysis['total_duration_seconds'] = round(total_duration, 2)
        analysis['total_duration_hours'] = round(total_duration / 3600, 2)
        
        # Speichere finale Ergebnisse
        json_file, md_file = scorer.save_results(scored_verses, analysis, prefix="FINAL_PRODUCTION")
        
        print("\n" + "🎉 " + "="*58)
        print("     VOLLPRODUKTION ERFOLGREICH ABGESCHLOSSEN!")
        print("="*62)
        
        # Finale Statistiken
        print(f"\n📊 FINALE ERGEBNISSE:")
        print(f"   • Verarbeitete Verse: {analysis.get('total_verses', 0):,}")
        print(f"   • Erfolgsrate: {analysis.get('success_rate', 0)}%")
        print(f"   • Durchschnittsscore: {analysis.get('average_score', 0)}")
        print(f"   • Höchster Score: {analysis.get('highest_score', 0)}")
        print(f"   • Niedrigster Score: {analysis.get('lowest_score', 0)}")
        print(f"   • Gesamtdauer: {analysis['total_duration_hours']} Stunden")
        
        # Score-Verteilung
        if 'distribution' in analysis:
            print(f"\n📈 FINALE SCORE-VERTEILUNG:")
            for desc, data in analysis['distribution'].items():
                print(f"   • {desc}: {data['count']:,} Verse ({data['percentage']}%)")
        
        # Top 10 Verse
        successful_verses = [v for v in scored_verses if v.get('success', False)]
        if successful_verses:
            successful_verses.sort(key=lambda x: x['positivity_score'], reverse=True)
            print(f"\n🏆 TOP 10 POSITIVE VERSE:")
            for i, verse in enumerate(successful_verses[:10], 1):
                score = verse['positivity_score']
                ref = verse['reference']
                text = verse['text'][:60] + "..." if len(verse['text']) > 60 else verse['text']
                print(f"   {i:2d}. {ref} (Score: {score})")
                print(f"       \"{text}\"")
        
        print(f"\n📁 FINALE DATEIEN:")
        print(f"   • JSON: {json_file}")
        print(f"   • Report: {md_file}")
        
        print(f"\n🎯 NÄCHSTE SCHRITTE:")
        print(f"   • Datenbank-Integration der Positivity-Scores")
        print(f"   • Top 1000 positive Verse für App-Frontend auswählen")
        print(f"   • Qualitätskontrolle der Extremwerte")
        
        print(f"\n✅ MISSION ACCOMPLISHED! 🎊")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Vollproduktion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_full_production()
    if success:
        print("\n🚀 Alle 11.003 Verse erfolgreich bewertet!")
        print("🏆 Ready für NGÜ-App Integration!")
    else:
        print("\n💥 Vollproduktion fehlgeschlagen!")
        print("🔧 Bitte Fehler beheben und erneut versuchen.")