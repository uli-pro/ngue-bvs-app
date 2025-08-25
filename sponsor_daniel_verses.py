#!/usr/bin/env python3
"""
Skript zum Markieren aller Daniel-Verse als gesponsert
Für den NGÜ Bibelvers-Sponsoring App
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Versuche .env zu laden (falls dotenv verfügbar)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Info: python-dotenv nicht installiert, verwende Umgebungsvariablen direkt")

# Import models
from models import db, Verse

def main():
    """Hauptfunktion zum Markieren aller Daniel-Verse als gesponsert"""
    
    # Datenbankverbindung aufbauen - mehrere Quellen prüfen
    database_uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    
    # Fallback: lokale .env Datei manuell lesen
    if not database_uri:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip().startswith('SQLALCHEMY_DATABASE_URI='):
                        database_uri = line.split('=', 1)[1].strip().strip('"\'')
                        break
        except FileNotFoundError:
            pass
    
    # Fallback: Standard-Verbindung für lokale Entwicklung
    if not database_uri:
        database_uri = "postgresql://postgres:password@localhost:5432/ngue_db"
        print(f"Info: Verwende Standard-Datenbankverbindung: {database_uri}")
    
    if not database_uri:
        print("Fehler: Keine Datenbankverbindung konfiguriert")
        print("Optionen:")
        print("1. Umgebungsvariable SQLALCHEMY_DATABASE_URI setzen")
        print("2. .env Datei mit SQLALCHEMY_DATABASE_URI erstellen")
        print("3. Skript anpassen mit direkter Verbindungsstring")
        sys.exit(1)
    
    # Engine und Session erstellen
    engine = create_engine(database_uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("Suche nach Daniel-Versen...")
        
        # Alle Daniel-Verse finden (sowohl "DANIEL" als auch "DAN" berücksichtigen)
        daniel_verses = session.query(Verse).filter(
            Verse.book.in_(['DANIEL', 'DAN'])
        ).all()
        
        if not daniel_verses:
            print("Keine Daniel-Verse in der Datenbank gefunden")
            print("Verfügbare Bücher prüfen...")
            # Zeige verfügbare Bücher mit "DAN" im Namen
            books_with_dan = session.query(Verse.book).filter(
                Verse.book.like('%DAN%')
            ).distinct().all()
            if books_with_dan:
                print("Bücher mit 'DAN' gefunden:")
                for book in books_with_dan:
                    print(f"  - {book[0]}")
            return
        
        print(f"Gefunden: {len(daniel_verses)} Daniel-Verse")
        
        # Bereits gesponserte Verse zählen
        already_sponsored = sum(1 for verse in daniel_verses if verse.is_sponsored)
        to_sponsor = len(daniel_verses) - already_sponsored
        
        print(f"Bereits gesponsert: {already_sponsored}")
        print(f"Zu sponsern: {to_sponsor}")
        
        if to_sponsor == 0:
            print("Alle Daniel-Verse sind bereits gesponsert!")
            return
        
        # Bestätigung vom Benutzer einholen
        confirm = input(f"\nMöchten Sie {to_sponsor} Daniel-Verse als gesponsert markieren? (j/N): ")
        if confirm.lower() not in ['j', 'ja', 'y', 'yes']:
            print("Abgebrochen.")
            return
        
        # Verse als gesponsert markieren
        current_time = datetime.utcnow()
        sponsored_count = 0
        
        for verse in daniel_verses:
            if not verse.is_sponsored:
                verse.is_sponsored = True
                verse.sponsored_at = current_time
                sponsored_count += 1
                print(f"Gesponsert: {verse.reference}")
        
        # Änderungen in Datenbank speichern
        session.commit()
        print(f"\n✅ Erfolgreich {sponsored_count} Daniel-Verse als gesponsert markiert!")
        
        # Zusammenfassung
        print(f"\nZusammenfassung:")
        print(f"- Buch: Daniel")
        print(f"- Gesponserte Verse: {sponsored_count}")
        print(f"- Zeitstempel: {current_time}")
        
    except Exception as e:
        session.rollback()
        print(f"Fehler beim Verarbeiten: {str(e)}")
        sys.exit(1)
        
    finally:
        session.close()

if __name__ == "__main__":
    main()