#!/usr/bin/env python3
"""
Semantische Suche Test für die Bibelvers-Suche - FINALES DATASET

Testet die semantische Ähnlichkeitssuche mit beliebten Bibelversen
aus dem kompletten Dataset aller unübersetzten Bücher (~11.000 Verse)
"""

import json
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import numpy as np

# Lade Umgebungsvariablen
load_dotenv()

# Konfiguration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ulrichprobst'),
    'user': os.getenv('DB_USER', 'ulrichprobst'),
    'password': os.getenv('DB_PASSWORD', '')
}

MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'

# Beliebte Bibelverse für den Test
POPULAR_VERSES = [
    {'ref': '1KI.8.57', 'name': '1. Könige 8,57'},
    {'ref': '1KI.17.14', 'name': '1. Könige 17,14'},
    {'ref': '2KI.19.19', 'name': '2. Könige 19,19'},
    {'ref': '1CH.16.11', 'name': '1. Chronik 16,11'},
    {'ref': '1CH.29.11', 'name': '1. Chronik 29,11'},
    {'ref': '1CH.4.10', 'name': '1. Chronik 4,10'},
    {'ref': '2CH.7.14', 'name': '2. Chronik 7,14'},
    {'ref': 'EZR.10.1', 'name': 'Esra 10,1'},
    {'ref': 'NEH.1.4', 'name': 'Nehemia 1,4'},
    {'ref': 'EST.4.14', 'name': 'Esther 4,14'},
    {'ref': 'JOB.1.21', 'name': 'Hiob 1,21'},
    {'ref': 'ECC.3.1', 'name': 'Prediger 3,1'},
    {'ref': 'SNG.7.10', 'name': 'Hoheslied 7,10'},
    {'ref': 'ISA.40.31', 'name': 'Jesaja 40,31'},
    {'ref': 'JER.29.11', 'name': 'Jeremia 29,11'}
]


class SemanticSearchTester:
    def __init__(self, dataset_file='final_verses_data.json'):
        """Initialisiere Tester mit finalem Dataset"""
        self.table_name = 'semantic_test_verses'
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = True
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Initialisiere Modell
        print(f"\nLade Embedding-Modell: {MODEL_NAME}...")
        self.model = SentenceTransformer(MODEL_NAME)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Embedding-Dimension: {self.dimension}")
        
        # Registriere pgvector
        register_vector(self.conn)
        
        # Lade Dataset
        print(f"\nLade finales Dataset aus {dataset_file}...")
        try:
            with open(dataset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.verses = data['verses']
                self.verse_count = len(self.verses)
                self.books_included = data['metadata']['books_included']
                print(f"Geladen: {self.verse_count:,} Verse aus {len(self.books_included)} Büchern")
        except FileNotFoundError:
            print(f"FEHLER: {dataset_file} nicht gefunden!")
            print("Bitte zuerst 'python prepare_final_data.py' ausführen")
            exit(1)
        
        # Setup Datenbank
        self.setup_database()
    
    def setup_database(self):
        """Erstelle Tabelle und fülle sie mit Versen + Embeddings"""
        print("\nRichte Datenbank ein...")
        
        # Erstelle pgvector extension
        self.cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Lösche alte Tabelle
        self.cur.execute(f"DROP TABLE IF EXISTS {self.table_name} CASCADE;")
        
        # Erstelle neue Tabelle
        self.cur.execute(f"""
            CREATE TABLE {self.table_name} (
                id SERIAL PRIMARY KEY,
                reference VARCHAR(20) UNIQUE,
                book VARCHAR(3),
                chapter INTEGER,
                verse INTEGER,
                text TEXT,
                embedding vector({self.dimension})
            );
        """)
        
        # Erstelle Index für Vektor-Suche
        self.cur.execute(f"""
            CREATE INDEX ON {self.table_name} 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        
        # Generiere Embeddings und füge Verse ein
        print(f"\nGeneriere Embeddings für {self.verse_count:,} Verse...")
        print("(Dies kann einige Minuten dauern...)")
        
        start_time = time.time()
        batch_size = 100
        
        for i in range(0, len(self.verses), batch_size):
            batch = self.verses[i:i+batch_size]
            texts = [v['text'] for v in batch]
            
            # Generiere Embeddings für Batch
            embeddings = self.model.encode(texts, show_progress_bar=False)
            
            # Bereite Daten für Insert vor
            verses_data = []
            for verse, embedding in zip(batch, embeddings):
                verses_data.append((
                    verse['reference'],
                    verse['book'],
                    verse['chapter'],
                    verse['verse'],
                    verse['text'],
                    embedding.tolist()
                ))
            
            # Füge Batch ein
            execute_values(
                self.cur,
                f"""
                INSERT INTO {self.table_name} 
                (reference, book, chapter, verse, text, embedding)
                VALUES %s
                """,
                verses_data,
                template="(%s, %s, %s, %s, %s, %s::vector)"
            )
            
            # Progress
            processed = min(i+batch_size, len(self.verses))
            if processed % 1000 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed
                remaining = (len(self.verses) - processed) / rate
                print(f"  Verarbeitet: {processed:,}/{len(self.verses):,} Verse "
                      f"({processed/len(self.verses)*100:.1f}%) - "
                      f"Geschätzte Restzeit: {remaining/60:.1f} Min")
        
        elapsed = time.time() - start_time
        print(f"\n✓ Embeddings generiert in {elapsed/60:.1f} Minuten")
        print(f"  Durchschnitt: {elapsed/len(self.verses):.3f}s pro Vers")
        
        # Analysiere Tabelle
        self.cur.execute(f"ANALYZE {self.table_name};")
        print(f"✓ Tabelle '{self.table_name}' erstellt und optimiert")
    
    def get_verse_text(self, reference):
        """Hole den Text eines bestimmten Verses"""
        self.cur.execute(f"""
            SELECT text 
            FROM {self.table_name}
            WHERE reference = %s
        """, (reference,))
        
        result = self.cur.fetchone()
        return result['text'] if result else None
    
    def find_similar_verses(self, reference, limit=5):
        """Finde semantisch ähnliche Verse zu einem gegebenen Vers"""
        # Hole den Originalvers
        verse_text = self.get_verse_text(reference)
        if not verse_text:
            return None, []
        
        # Zeit messen
        start_time = time.time()
        
        # Generiere Embedding für Query-Vers
        query_embedding = self.model.encode(verse_text)
        
        # Suche ähnliche Verse (schließe den Originalvers aus)
        self.cur.execute(f"""
            SELECT 
                reference,
                text,
                1 - (embedding <=> %s::vector) as similarity
            FROM {self.table_name}
            WHERE reference != %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding.tolist(), reference, query_embedding.tolist(), limit))
        
        results = self.cur.fetchall()
        search_time = time.time() - start_time
        
        return verse_text, results, search_time
    
    def run_all_tests(self):
        """Führe semantische Suche für alle beliebten Verse durch"""
        print("\n" + "="*80)
        print("SEMANTISCHE SUCHE TEST - FINALES DATASET")
        print("="*80)
        
        all_results = []
        total_search_time = 0
        
        for i, verse_info in enumerate(POPULAR_VERSES, 1):
            reference = verse_info['ref']
            name = verse_info['name']
            
            print(f"\n{i}. Suche ähnliche Verse zu: {name}")
            
            verse_text, similar_verses, search_time = self.find_similar_verses(reference, limit=5)
            total_search_time += search_time
            
            if verse_text:
                print(f"   Original: {verse_text[:100]}...")
                print(f"   Suchzeit: {search_time:.3f}s")
                print(f"\n   Ähnlichste Verse:")
                
                result_data = {
                    'reference': reference,
                    'name': name,
                    'original_text': verse_text,
                    'similar_verses': [],
                    'search_time': search_time
                }
                
                for j, verse in enumerate(similar_verses, 1):
                    print(f"\n   {j}. {verse['reference']} (Ähnlichkeit: {verse['similarity']:.4f})")
                    print(f"      {verse['text']}")
                    
                    result_data['similar_verses'].append({
                        'reference': verse['reference'],
                        'text': verse['text'],
                        'similarity': float(verse['similarity'])
                    })
                
                all_results.append(result_data)
            else:
                print(f"   FEHLER: Vers {reference} nicht gefunden!")
        
        print(f"\n\nGesamte Suchzeit: {total_search_time:.2f}s")
        print(f"Durchschnitt: {total_search_time/len(POPULAR_VERSES):.3f}s pro Suche")
        
        return all_results
    
    def save_results(self, results):
        """Speichere Ergebnisse"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON-Datei
        json_filename = f"results/semantic_search_results_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'test_date': timestamp,
                'model': MODEL_NAME,
                'verse_count': self.verse_count,
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\nErgebnisse gespeichert in: {json_filename}")
        
        # Markdown-Report
        self.create_markdown_report(results, timestamp)
    
    def create_markdown_report(self, results, timestamp):
        """Erstelle detaillierten Markdown-Report"""
        filename = f"results/semantic_search_report_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Semantische Suche Test Report - FINALES DATASET\n\n")
            f.write(f"**Datum**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"**Modell**: {MODEL_NAME}\n")
            f.write(f"**Verse in Datenbank**: {self.verse_count:,}\n")
            f.write(f"**Getestete Verse**: {len(results)}\n\n")
            
            # Performance
            total_time = sum(r['search_time'] for r in results)
            avg_time = total_time / len(results)
            
            f.write("## Performance\n\n")
            f.write(f"- **Gesamte Suchzeit**: {total_time:.2f}s\n")
            f.write(f"- **Durchschnittliche Suchzeit**: {avg_time:.3f}s\n")
            f.write(f"- **Schnellste Suche**: {min(r['search_time'] for r in results):.3f}s\n")
            f.write(f"- **Langsamste Suche**: {max(r['search_time'] for r in results):.3f}s\n\n")
            
            # Durchschnittliche Ähnlichkeit
            all_similarities = []
            for r in results:
                all_similarities.extend([v['similarity'] for v in r['similar_verses']])
            
            f.write("## Ähnlichkeits-Statistiken\n\n")
            f.write(f"- **Durchschnittliche Ähnlichkeit (Top 5)**: {np.mean(all_similarities):.4f}\n")
            f.write(f"- **Höchste Ähnlichkeit**: {max(all_similarities):.4f}\n")
            f.write(f"- **Niedrigste Ähnlichkeit**: {min(all_similarities):.4f}\n\n")
            
            # Detaillierte Ergebnisse
            f.write("## Detaillierte Ergebnisse\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"### {i}. {result['name']}\n\n")
                f.write(f"**Referenz**: {result['reference']}\n")
                f.write(f"**Suchzeit**: {result['search_time']:.3f}s\n\n")
                f.write(f"**Originalvers**:\n")
                f.write(f"> {result['original_text']}\n\n")
                
                f.write("**Die 5 ähnlichsten Verse**:\n\n")
                
                for j, verse in enumerate(result['similar_verses'], 1):
                    f.write(f"{j}. **{verse['reference']}** (Ähnlichkeit: {verse['similarity']:.4f})\n")
                    f.write(f"   > {verse['text']}\n\n")
                
                f.write("\n---\n\n")
            
            # Kreuzreferenzen
            f.write("## Interessante Beobachtungen\n\n")
            
            # Finde Verse, die mehrfach als ähnlich auftauchen
            similar_refs = {}
            for result in results:
                for verse in result['similar_verses']:
                    ref = verse['reference']
                    if ref not in similar_refs:
                        similar_refs[ref] = []
                    similar_refs[ref].append(result['reference'])
            
            multiple_matches = {k: v for k, v in similar_refs.items() if len(v) > 1}
            
            if multiple_matches:
                f.write("### Verse, die mehrfach als ähnlich gefunden wurden:\n\n")
                for ref, sources in sorted(multiple_matches.items(), key=lambda x: len(x[1]), reverse=True):
                    f.write(f"- **{ref}** ist ähnlich zu: {', '.join(sources)}\n")
        
        print(f"Markdown-Report gespeichert in: {filename}")
    
    def cleanup(self):
        """Schließe Datenbankverbindung"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


def main():
    """Hauptfunktion"""
    print("NGÜ Bibelvers-Sponsoring - Semantische Suche Test")
    print("FINALES DATASET mit allen unübersetzten Büchern")
    
    # Warnung vor langer Laufzeit
    print("\n" + "!"*60)
    print("WARNUNG: Das Generieren der Embeddings für ~11.000 Verse")
    print("kann 5-10 Minuten dauern. Bitte Geduld!")
    print("!"*60)
    
    tester = SemanticSearchTester()
    
    # Führe Tests durch
    results = tester.run_all_tests()
    
    # Speichere Ergebnisse
    tester.save_results(results)
    
    # Zusammenfassung
    print("\n" + "="*80)
    print("TEST ABGESCHLOSSEN")
    print("="*80)
    print(f"\n✓ {len(POPULAR_VERSES)} beliebte Verse getestet")
    print(f"✓ Je 5 ähnlichste Verse gefunden")
    print(f"✓ Reports gespeichert")
    
    tester.cleanup()


if __name__ == "__main__":
    main()
