#!/usr/bin/env python3
"""
Container-Version: Skript zum Markieren aller Daniel-Verse als gesponsert
Läuft INNERHALB des NGU Flask-Containers mit verfügbaren Dependencies
"""

import os
import sys
from datetime import datetime

# Flask-App imports (im Container verfügbar)
sys.path.append('/app')
from models import db, Verse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_database_uri_from_env():
    """Holt Database URI aus Container-Umgebungsvariablen"""
    # Im Container sind die Env-Vars bereits gesetzt (docker-compose.yml:102)
    return os.environ.get('SQLALCHEMY_DATABASE_URI')

def main():
    """Hauptfunktion zum Markieren aller Daniel-Verse als gesponsert"""
    
    print("=== NGÜ Daniel-Verse Sponsoring Script (Container Version) ===")
    print("Läuft INNERHALB des NGU Flask-Containers")
    print("WARNUNG: Bitte stellen Sie sicher, dass Sie eine Datensicherung haben!")
    print()
    
    # Database URI aus Container-Environment
    database_uri = get_database_uri_from_env()
    
    if not database_uri:
        print("❌ Fehler: SQLALCHEMY_DATABASE_URI nicht in Container-Umgebung gefunden!")
        print("Verfügbare Umgebungsvariablen:")
        for key in sorted(os.environ.keys()):
            if any(term in key.upper() for term in ['POSTGRES', 'DATABASE', 'DB']):
                value = os.environ[key]
                # Passwort maskieren
                if 'PASSWORD' in key.upper():
                    value = '*' * len(value)
                print(f"  {key}={value}")
        sys.exit(1)
    
    print(f"Datenbankverbindung: {database_uri.replace(':' + os.environ.get('POSTGRES_PASSWORD', ''), ':***')}")
    print()
    
    try:
        # SQLAlchemy Engine erstellen (nutzt bestehende Flask-Models)
        print("Verbinde mit Datenbank über Flask-Models...")
        engine = create_engine(database_uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Suche nach Daniel-Versen...")
        
        # Alle Daniel-Verse finden - verschiedene mögliche Buchbezeichnungen
        daniel_verses = session.query(Verse).filter(
            Verse.book.ilike('%daniel%') | Verse.book.ilike('%dan%')
        ).order_by(Verse.book, Verse.chapter, Verse.verse).all()
        
        if not daniel_verses:
            print("Keine Daniel-Verse in der Datenbank gefunden")
            print("Verfügbare Bücher prüfen...")
            books_with_dan = session.query(Verse.book).filter(
                Verse.book.ilike('%dan%')
            ).distinct().all()
            if books_with_dan:
                print("Bücher mit 'DAN' gefunden:")
                for book in books_with_dan:
                    print(f"  - {book[0]}")
            else:
                print("Keine Bücher mit 'DAN' gefunden. Erste 10 Bücher:")
                all_books = session.query(Verse.book).distinct().limit(10).all()
                for book in all_books:
                    print(f"  - {book[0]}")
            return
        
        # Zusammenfassung der gefundenen Verse
        book_summary = {}
        for verse in daniel_verses:
            book = verse.book
            if book not in book_summary:
                book_summary[book] = {'total': 0, 'sponsored': 0, 'verses': []}
            book_summary[book]['total'] += 1
            book_summary[book]['verses'].append(verse)
            if verse.is_sponsored:
                book_summary[book]['sponsored'] += 1
        
        print(f"Gefundene Daniel-Verse:")
        total_verses = 0
        total_sponsored = 0
        total_to_sponsor = 0
        
        for book, stats in book_summary.items():
            to_sponsor = stats['total'] - stats['sponsored']
            total_verses += stats['total']
            total_sponsored += stats['sponsored']
            total_to_sponsor += to_sponsor
            print(f"  📖 {book}: {stats['total']} Verse ({stats['sponsored']} gesponsert, {to_sponsor} offen)")
        
        print(f"\n📊 Gesamtübersicht:")
        print(f"  📝 Gesamtverse: {total_verses}")
        print(f"  ✅ Bereits gesponsert: {total_sponsored}")
        print(f"  ⭕ Zu sponsern: {total_to_sponsor}")
        
        if total_to_sponsor == 0:
            print("\n🎉 Alle Daniel-Verse sind bereits gesponsert!")
            return
        
        # Zeige erste paar Verse als Beispiel
        print(f"\n📋 Beispiel-Verse (erste 5):")
        for i, verse in enumerate(daniel_verses[:5]):
            status = "✅ gesponsert" if verse.is_sponsored else "⭕ offen"
            print(f"  {verse.reference} - {status}")
            if i == 0:  # Zeige ersten Verstext als Beispiel
                preview = verse.text[:80] + "..." if len(verse.text) > 80 else verse.text
                print(f"    \"{preview}\"")
        
        if len(daniel_verses) > 5:
            print(f"  ... und {len(daniel_verses) - 5} weitere Verse")
        
        # Bestätigung vom Benutzer einholen
        print(f"\n⚠️  ACHTUNG: Dies wird {total_to_sponsor} Verse als gesponsert markieren!")
        print(f"💰 Entspricht einem Sponsoring-Wert von {total_to_sponsor * 100}€ (à 100€ pro Vers)")
        confirm = input(f"\nMöchten Sie fortfahren? (j/N): ")
        if confirm.lower() not in ['j', 'ja', 'y', 'yes']:
            print("❌ Abgebrochen.")
            return
        
        # Verse als gesponsert markieren
        current_time = datetime.utcnow()
        sponsored_count = 0
        
        print(f"\n🔄 Markiere Verse als gesponsert...")
        
        for verse in daniel_verses:
            if not verse.is_sponsored:
                verse.is_sponsored = True
                verse.sponsored_at = current_time
                sponsored_count += 1
                print(f"  ✅ {verse.reference}")
        
        # Änderungen in Datenbank speichern
        session.commit()
        print(f"\n🎉 Erfolgreich {sponsored_count} Daniel-Verse als gesponsert markiert!")
        
        # Finale Zusammenfassung
        print(f"\n📈 Abschluss-Zusammenfassung:")
        for book, stats in book_summary.items():
            sponsored_in_book = sum(1 for v in stats['verses'] if v.is_sponsored)
            print(f"  📖 {book}: {sponsored_in_book}/{stats['total']} gesponsert")
        
        print(f"\n🎯 Gesamt-Statistik:")
        print(f"  📝 Neu gesponserte Verse: {sponsored_count}")
        print(f"  🕐 Zeitstempel: {current_time}")
        print(f"  💰 Sponsoring-Betrag: {sponsored_count * 100}€")
        print(f"  📊 Daniel-Fortschritt: {total_sponsored + sponsored_count}/{total_verses} (100%)")
        
    except Exception as e:
        if 'session' in locals():
            session.rollback()
        print(f"❌ Fehler beim Verarbeiten: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    # Prüfe ob wir im Container sind
    if not os.path.exists('/app/models.py'):
        print("❌ Fehler: models.py nicht gefunden!")
        print("Dieses Skript muss INNERHALB des NGU Flask-Containers ausgeführt werden.")
        print("\nVerwendung:")
        print("  docker exec -it ngue-flask-app python /app/app-deployment/sponsor_daniel_container.py")
        sys.exit(1)
    
    main()