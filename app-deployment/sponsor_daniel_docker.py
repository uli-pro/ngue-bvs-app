#!/usr/bin/env python3
"""
Docker-optimiertes Skript zum Markieren aller Daniel-Verse als gesponsert
Für NGÜ Bibelvers-Sponsoring App in Docker-Umgebung
"""

import os
import sys
from datetime import datetime
import psycopg2

def load_env_file(env_path='.env'):
    """Lädt .env Datei manuell"""
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value.strip('"\'')
        return env_vars
    except FileNotFoundError:
        print(f"Warnung: {env_path} nicht gefunden")
        return {}

def get_database_config():
    """Extrahiert Datenbank-Konfiguration aus .env"""
    env_vars = load_env_file('.env')
    
    # Docker-Setup: postgres ist der Container-Name (docker-compose.yml:102)
    host = 'postgres'  # Docker-Container-Name aus docker-compose.yml
    
    return {
        'host': host,
        'database': env_vars.get('POSTGRES_DB', 'ngue_db'),
        'user': env_vars.get('POSTGRES_USER', 'postgres'), 
        'password': env_vars.get('POSTGRES_PASSWORD', ''),
        'port': 5432  # Standard PostgreSQL Port
    }

def main():
    """Hauptfunktion zum Markieren aller Daniel-Verse als gesponsert"""
    
    print("=== NGÜ Daniel-Verse Sponsoring Script (Docker Version) ===")
    print("WARNUNG: Bitte stellen Sie sicher, dass Sie eine Datensicherung haben!")
    print()
    
    # Datenbank-Konfiguration aus .env laden
    db_config = get_database_config()
    
    print(f"Datenbankverbindung:")
    print(f"  Host: {db_config['host']}")
    print(f"  Datenbank: {db_config['database']}")
    print(f"  Benutzer: {db_config['user']}")
    print(f"  Port: {db_config['port']}")
    print()
    
    if not db_config['password']:
        print("Fehler: POSTGRES_PASSWORD nicht in .env gefunden!")
        sys.exit(1)
    
    try:
        # Docker-Container-zu-Container Verbindung
        print("Verbinde mit PostgreSQL-Container...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("Suche nach Daniel-Versen...")
        
        # Alle Daniel-Verse finden - verschiedene mögliche Buchbezeichnungen
        cursor.execute("""
            SELECT id, book, chapter, verse, is_sponsored 
            FROM verses 
            WHERE book ILIKE '%daniel%' OR book ILIKE '%dan%'
            ORDER BY book, chapter, verse
        """)
        
        daniel_verses = cursor.fetchall()
        
        if not daniel_verses:
            print("Keine Daniel-Verse in der Datenbank gefunden")
            print("Verfügbare Bücher prüfen...")
            cursor.execute("SELECT DISTINCT book FROM verses WHERE book ILIKE '%dan%' ORDER BY book")
            books = cursor.fetchall()
            if books:
                print("Bücher mit 'DAN' gefunden:")
                for book in books:
                    print(f"  - {book[0]}")
            else:
                print("Keine Bücher mit 'DAN' gefunden. Alle Bücher:")
                cursor.execute("SELECT DISTINCT book FROM verses ORDER BY book LIMIT 10")
                all_books = cursor.fetchall()
                for book in all_books:
                    print(f"  - {book[0]}")
            return
        
        # Zusammenfassung der gefundenen Verse
        book_summary = {}
        for verse in daniel_verses:
            book = verse[1]
            if book not in book_summary:
                book_summary[book] = {'total': 0, 'sponsored': 0}
            book_summary[book]['total'] += 1
            if verse[4]:  # is_sponsored
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
            print(f"  {book}: {stats['total']} Verse ({stats['sponsored']} gesponsert, {to_sponsor} offen)")
        
        print(f"\nGesamtübersicht:")
        print(f"  Gesamtverse: {total_verses}")
        print(f"  Bereits gesponsert: {total_sponsored}")
        print(f"  Zu sponsern: {total_to_sponsor}")
        
        if total_to_sponsor == 0:
            print("\n✅ Alle Daniel-Verse sind bereits gesponsert!")
            return
        
        # Zeige erste paar Verse als Beispiel
        print(f"\nBeispiel-Verse (erste 5):")
        for i, verse in enumerate(daniel_verses[:5]):
            status = "✅ gesponsert" if verse[4] else "⭕ offen"
            print(f"  {verse[1]} {verse[2]},{verse[3]} - {status}")
        if len(daniel_verses) > 5:
            print(f"  ... und {len(daniel_verses) - 5} weitere")
        
        # Bestätigung vom Benutzer einholen
        print(f"\n⚠️  ACHTUNG: Dies wird {total_to_sponsor} Verse als gesponsert markieren!")
        confirm = input(f"Möchten Sie fortfahren? (j/N): ")
        if confirm.lower() not in ['j', 'ja', 'y', 'yes']:
            print("Abgebrochen.")
            return
        
        # Verse als gesponsert markieren
        current_time = datetime.utcnow()
        sponsored_count = 0
        
        print(f"\nMarkiere Verse als gesponsert...")
        for verse in daniel_verses:
            verse_id, book, chapter, verse_num, is_sponsored = verse
            if not is_sponsored:
                cursor.execute("""
                    UPDATE verses 
                    SET is_sponsored = TRUE, sponsored_at = %s 
                    WHERE id = %s
                """, (current_time, verse_id))
                sponsored_count += 1
                print(f"  ✅ {book} {chapter},{verse_num}")
        
        # Änderungen in Datenbank speichern
        conn.commit()
        print(f"\n🎉 Erfolgreich {sponsored_count} Daniel-Verse als gesponsert markiert!")
        
        # Finale Zusammenfassung
        print(f"\nAbschluss-Zusammenfassung:")
        print(f"  📖 Bücher: {', '.join(book_summary.keys())}")
        print(f"  📝 Gesponserte Verse: {sponsored_count}")
        print(f"  🕐 Zeitstempel: {current_time}")
        print(f"  💰 Sponsoring-Betrag: {sponsored_count * 100}€ (à 100€ pro Vers)")
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Datenbankverbindung fehlgeschlagen!")
        print(f"Fehlerdetails: {str(e)}")
        print(f"\nMögliche Lösungen:")
        print(f"1. Stellen Sie sicher, dass PostgreSQL-Container läuft: docker ps")
        print(f"2. Prüfen Sie die .env Datei auf korrekte POSTGRES_* Variablen")
        print(f"3. Führen Sie das Skript INNERHALB des Docker-Netzwerks aus")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"❌ Datenbankfehler: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {str(e)}")
        sys.exit(1)
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Prüfe ob wir im richtigen Verzeichnis sind
    if not os.path.exists('.env'):
        print("❌ Fehler: .env Datei nicht gefunden!")
        print("Bitte führen Sie das Skript im /docker/ngue-app/app-deployment Verzeichnis aus.")
        sys.exit(1)
    
    main()