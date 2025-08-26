#!/usr/bin/env python3
"""
Vereinfachtes Skript zum Markieren aller Daniel-Verse als gesponsert
Für den NGÜ Bibelvers-Sponsoring App - Homeserver Version
"""

import sys
from datetime import datetime
import psycopg2

# KONFIGURATION - HIER IHRE DATENBANKDATEN EINTRAGEN
DATABASE_CONFIG = {
    'host': 'localhost',      # Ihr PostgreSQL Host
    'database': 'ngue_db',    # Ihr Datenbankname
    'user': 'postgres',       # Ihr PostgreSQL Benutzer
    'password': 'password',   # Ihr PostgreSQL Passwort
    'port': 5432             # Ihr PostgreSQL Port
}

def main():
    """Hauptfunktion zum Markieren aller Daniel-Verse als gesponsert"""
    
    try:
        # Direkte PostgreSQL Verbindung (ohne SQLAlchemy Dependencies)
        print("Verbinde mit Datenbank...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        print("Suche nach Daniel-Versen...")
        
        # Alle Daniel-Verse finden
        cursor.execute("""
            SELECT id, book, chapter, verse, is_sponsored 
            FROM verses 
            WHERE book ILIKE '%daniel%' OR book ILIKE '%dan%'
            ORDER BY chapter, verse
        """)
        
        daniel_verses = cursor.fetchall()
        
        if not daniel_verses:
            print("Keine Daniel-Verse in der Datenbank gefunden")
            print("Verfügbare Bücher prüfen...")
            cursor.execute("SELECT DISTINCT book FROM verses WHERE book ILIKE '%dan%'")
            books = cursor.fetchall()
            if books:
                print("Bücher mit 'DAN' gefunden:")
                for book in books:
                    print(f"  - {book[0]}")
            return
        
        print(f"Gefunden: {len(daniel_verses)} Daniel-Verse")
        
        # Bereits gesponserte Verse zählen
        already_sponsored = sum(1 for verse in daniel_verses if verse[4])  # is_sponsored
        to_sponsor = len(daniel_verses) - already_sponsored
        
        print(f"Bereits gesponsert: {already_sponsored}")
        print(f"Zu sponsern: {to_sponsor}")
        
        if to_sponsor == 0:
            print("Alle Daniel-Verse sind bereits gesponsert!")
            return
        
        # Zeige erste paar Verse als Beispiel
        print(f"\nBeispiel-Verse:")
        for i, verse in enumerate(daniel_verses[:5]):
            status = "✅ gesponsert" if verse[4] else "⭕ offen"
            print(f"  {verse[1]} {verse[2]},{verse[3]} - {status}")
        if len(daniel_verses) > 5:
            print(f"  ... und {len(daniel_verses) - 5} weitere")
        
        # Bestätigung vom Benutzer einholen
        confirm = input(f"\nMöchten Sie {to_sponsor} Daniel-Verse als gesponsert markieren? (j/N): ")
        if confirm.lower() not in ['j', 'ja', 'y', 'yes']:
            print("Abgebrochen.")
            return
        
        # Verse als gesponsert markieren
        current_time = datetime.utcnow()
        sponsored_count = 0
        
        for verse in daniel_verses:
            verse_id, book, chapter, verse_num, is_sponsored = verse
            if not is_sponsored:
                cursor.execute("""
                    UPDATE verses 
                    SET is_sponsored = TRUE, sponsored_at = %s 
                    WHERE id = %s
                """, (current_time, verse_id))
                sponsored_count += 1
                print(f"Gesponsert: {book} {chapter},{verse_num}")
        
        # Änderungen in Datenbank speichern
        conn.commit()
        print(f"\n✅ Erfolgreich {sponsored_count} Daniel-Verse als gesponsert markiert!")
        
        # Zusammenfassung
        print(f"\nZusammenfassung:")
        print(f"- Buch: Daniel")
        print(f"- Gesponserte Verse: {sponsored_count}")
        print(f"- Zeitstempel: {current_time}")
        
    except psycopg2.Error as e:
        print(f"Datenbankfehler: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Fehler beim Verarbeiten: {str(e)}")
        sys.exit(1)
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== NGÜ Daniel-Verse Sponsoring Script ===")
    print("WARNUNG: Bitte stellen Sie sicher, dass Sie eine Datensicherung haben!")
    print()
    main()