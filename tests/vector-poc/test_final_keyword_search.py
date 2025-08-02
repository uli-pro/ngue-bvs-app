#!/usr/bin/env python3
"""
Keyword-basierter Test für die Bibelvers-Suche - FINALES DATASET

Testet die 50 häufigsten Keywords einzeln sowie sinnvolle Kombinationen
mit dem kompletten Dataset aller unübersetzten Bücher (~11.000 Verse)
"""

import json
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

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

# Die 50 häufigsten Keywords für Bibelvers-Suchen
TOP_50_KEYWORDS = [
    'Liebe', 'Gott', 'Glaube', 'Hoffnung', 'Jesus',  # 1-5
    'Vertrauen', 'Gebet', 'Frieden', 'Kraft', 'Herz',  # 6-10
    'Leben', 'Weg', 'Licht', 'Wahrheit', 'Gnade',  # 11-15
    'Segen', 'Freude', 'Weisheit', 'Mut', 'Trost',
    'Vergebung', 'Erlösung', 'Heilung', 'Schutz', 'Führung',
    'Dankbarkeit', 'Demut', 'Treue', 'Barmherzigkeit', 'Güte',
    'Stärke', 'Hilfe', 'Rettung', 'Ewigkeit', 'Himmel',
    'Seele', 'Geist', 'Wort', 'Lobpreis', 'Anbetung',
    'Sünde', 'Buße', 'Umkehr', 'Neuanfang', 'Zukunft',
    'Angst', 'Sorge', 'Not', 'Prüfung', 'Sieg'
]

# Sinnvolle 2er-Kombinationen aus den Top 15
KEYWORD_PAIRS = [
    ('Gott', 'Liebe'),
    ('Glaube', 'Hoffnung'),
    ('Jesus', 'Weg'),
    ('Gebet', 'Vertrauen'),
    ('Frieden', 'Herz'),
    ('Kraft', 'Mut'),
    ('Licht', 'Wahrheit'),
    ('Leben', 'Gnade'),
    ('Gott', 'Vertrauen'),
    ('Jesus', 'Liebe'),
    ('Hoffnung', 'Leben'),
    ('Glaube', 'Kraft'),
    ('Herz', 'Frieden'),
    ('Weg', 'Wahrheit'),
    ('Gnade', 'Barmherzigkeit')
]

# Sinnvolle 3er-Kombinationen aus den Top 15
KEYWORD_TRIPLES = [
    ('Gott', 'Liebe', 'Gnade'),
    ('Glaube', 'Hoffnung', 'Liebe'),
    ('Jesus', 'Weg', 'Wahrheit'),
    ('Vertrauen', 'Gebet', 'Kraft'),
    ('Frieden', 'Herz', 'Leben'),
    ('Licht', 'Wahrheit', 'Leben'),
    ('Gott', 'Vertrauen', 'Führung'),
    ('Jesus', 'Gnade', 'Erlösung'),
    ('Kraft', 'Mut', 'Hoffnung'),
    ('Herz', 'Liebe', 'Frieden')
]


class FinalKeywordSearchTester:
    def __init__(self, dataset_file='final_verses_data.json'):
        """Initialisiere Tester mit finalem Dataset"""
        self.table_name = 'final_keyword_test_verses'
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = True
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Registriere pgvector (falls benötigt)
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
        """Erstelle Tabelle und fülle sie mit Versen"""
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
                search_vector tsvector
            );
        """)
        
        # Erstelle Volltext-Index
        self.cur.execute(f"""
            CREATE INDEX ON {self.table_name} 
            USING GIN (search_vector);
        """)
        
        # Füge Verse ein (in Batches für bessere Performance)
        print(f"Füge {self.verse_count:,} Verse in Datenbank ein...")
        batch_size = 1000
        
        for i in range(0, len(self.verses), batch_size):
            batch = self.verses[i:i+batch_size]
            verses_data = [
                (
                    verse['reference'],
                    verse['book'],
                    verse['chapter'],
                    verse['verse'],
                    verse['text']
                )
                for verse in batch
            ]
            
            execute_values(
                self.cur,
                f"""
                INSERT INTO {self.table_name} 
                (reference, book, chapter, verse, text)
                VALUES %s
                """,
                verses_data
            )
            
            print(f"  Eingefügt: {min(i+batch_size, len(self.verses)):,}/{len(self.verses):,} Verse")
        
        # Update Volltext-Vektoren
        print("Erstelle Volltext-Index...")
        self.cur.execute(f"""
            UPDATE {self.table_name} 
            SET search_vector = to_tsvector('german', text);
        """)
        
        # Analysiere Tabelle für bessere Performance
        self.cur.execute(f"ANALYZE {self.table_name};")
        
        print(f"✓ Tabelle '{self.table_name}' erstellt und optimiert")
    
    def search_keyword(self, keyword):
        """Suche nach einem einzelnen Keyword"""
        start_time = time.time()
        
        self.cur.execute(f"""
            SELECT 
                reference,
                text,
                ts_rank(search_vector, plainto_tsquery('german', %s)) as score
            FROM {self.table_name}
            WHERE search_vector @@ plainto_tsquery('german', %s)
            ORDER BY score DESC
            LIMIT 10
        """, (keyword, keyword))
        
        results = self.cur.fetchall()
        search_time = time.time() - start_time
        
        return {
            'keyword': keyword,
            'results': results,
            'count': len(results),
            'search_time': search_time
        }
    
    def search_multiple_keywords(self, keywords):
        """Suche nach mehreren Keywords (nur AND-Verknüpfung)"""
        start_time = time.time()
        
        # Erstelle Query mit AND-Verknüpfung
        query_parts = ' & '.join(keywords)
        
        self.cur.execute(f"""
            SELECT 
                reference,
                text,
                ts_rank(search_vector, to_tsquery('german', %s)) as score
            FROM {self.table_name}
            WHERE search_vector @@ to_tsquery('german', %s)
            ORDER BY score DESC
            LIMIT 10
        """, (query_parts, query_parts))
        
        results = self.cur.fetchall()
        search_time = time.time() - start_time
        
        return {
            'keywords': keywords,
            'search_type': 'AND',
            'results': results,
            'count': len(results),
            'search_time': search_time
        }
    
    def get_total_matches(self, keyword):
        """Hole Gesamtanzahl der Treffer für ein Keyword"""
        self.cur.execute(f"""
            SELECT COUNT(*) as total
            FROM {self.table_name}
            WHERE search_vector @@ plainto_tsquery('german', %s)
        """, (keyword,))
        
        return self.cur.fetchone()['total']
    
    def run_all_tests(self):
        """Führe alle Tests durch"""
        print("\n" + "="*80)
        print("KEYWORD SEARCH TEST - FINALES DATASET")
        print("="*80)
        
        all_results = {
            'single_keywords': [],
            'keyword_pairs': [],
            'keyword_triples': [],
            'metadata': {
                'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'verse_count': self.verse_count,
                'books_included': self.books_included,
                'table_name': self.table_name
            }
        }
        
        # 1. Teste einzelne Keywords
        print("\n1. EINZELNE KEYWORDS (50)")
        print("-" * 40)
        
        for i, keyword in enumerate(TOP_50_KEYWORDS, 1):
            result = self.search_keyword(keyword)
            # Hole auch Gesamtanzahl
            total_matches = self.get_total_matches(keyword)
            result['total_matches'] = total_matches
            
            all_results['single_keywords'].append(result)
            
            print(f"\n{i}. '{keyword}' - {result['count']} von {total_matches} Treffern angezeigt ({result['search_time']:.3f}s)")
            for j, verse in enumerate(result['results'], 1):
                print(f"\n   {j}. {verse['reference']} (Score: {verse['score']:.4f})")
                print(f"      {verse['text']}")
        
        # 2. Teste Keyword-Paare
        print("\n\n2. KEYWORD-PAARE (15)")
        print("-" * 40)
        
        for i, pair in enumerate(KEYWORD_PAIRS, 1):
            result = self.search_multiple_keywords(pair)
            all_results['keyword_pairs'].append(result)
            
            print(f"\n{i}. {' + '.join(pair)} - {result['count']} Treffer (AND) ({result['search_time']:.3f}s)")
            for j, verse in enumerate(result['results'], 1):
                print(f"\n   {j}. {verse['reference']} (Score: {verse['score']:.4f})")
                print(f"      {verse['text']}")
        
        # 3. Teste Keyword-Tripel
        print("\n\n3. KEYWORD-TRIPEL (10)")
        print("-" * 40)
        
        for i, triple in enumerate(KEYWORD_TRIPLES, 1):
            result = self.search_multiple_keywords(triple)
            all_results['keyword_triples'].append(result)
            
            print(f"\n{i}. {' + '.join(triple)} - {result['count']} Treffer (AND) ({result['search_time']:.3f}s)")
            for j, verse in enumerate(result['results'], 1):
                print(f"\n   {j}. {verse['reference']} (Score: {verse['score']:.4f})")
                print(f"      {verse['text']}")
        
        return all_results
    
    def save_results(self, results):
        """Speichere Ergebnisse in JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/final_keyword_test_results_{timestamp}.json"
        
        # Konvertiere Results für JSON
        def convert_results(result_list):
            converted = []
            for item in result_list:
                converted_item = item.copy()
                if 'results' in converted_item:
                    converted_item['results'] = [
                        {
                            'reference': r['reference'],
                            'text': r['text'],
                            'score': float(r['score'])
                        }
                        for r in converted_item['results']
                    ]
                converted.append(converted_item)
            return converted
        
        json_results = {
            'single_keywords': convert_results(results['single_keywords']),
            'keyword_pairs': convert_results(results['keyword_pairs']),
            'keyword_triples': convert_results(results['keyword_triples']),
            'metadata': results['metadata']
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n\nErgebnisse gespeichert in: {filename}")
        
        # Erstelle auch einen Markdown-Report
        self.create_markdown_report(results, timestamp)
    
    def create_markdown_report(self, results, timestamp):
        """Erstelle einen lesbaren Markdown-Report"""
        filename = f"results/final_keyword_test_report_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Keyword Search Test Report - FINALES DATASET\n\n")
            f.write(f"**Datum**: {results['metadata']['test_date']}\n")
            f.write(f"**Verse in Datenbank**: {results['metadata']['verse_count']:,}\n")
            f.write(f"**Bücher**: {', '.join(sorted(results['metadata']['books_included']))}\n\n")
            
            # Statistiken
            total_single = sum(r['total_matches'] for r in results['single_keywords'])
            total_pairs = sum(r['count'] for r in results['keyword_pairs'])
            total_triples = sum(r['count'] for r in results['keyword_triples'])
            
            f.write("## Zusammenfassung\n\n")
            f.write(f"- **Einzelne Keywords**: {len(results['single_keywords'])} getestet, {total_single:,} Treffer insgesamt\n")
            f.write(f"- **Keyword-Paare**: {len(results['keyword_pairs'])} getestet, {total_pairs} Treffer (Top 10 angezeigt)\n")
            f.write(f"- **Keyword-Tripel**: {len(results['keyword_triples'])} getestet, {total_triples} Treffer (Top 10 angezeigt)\n\n")
            
            # Top Keywords nach Treffern
            f.write("## Top 10 Keywords nach Anzahl Treffer\n\n")
            sorted_keywords = sorted(results['single_keywords'], 
                                   key=lambda x: x['total_matches'], 
                                   reverse=True)[:10]
            for i, kw in enumerate(sorted_keywords, 1):
                f.write(f"{i}. **{kw['keyword']}**: {kw['total_matches']:,} Treffer gesamt\n")
            
            # Keywords ohne Treffer
            no_results = [kw['keyword'] for kw in results['single_keywords'] if kw['total_matches'] == 0]
            if no_results:
                f.write(f"\n## Keywords ohne Treffer ({len(no_results)})\n\n")
                f.write(", ".join(no_results) + "\n")
            
            # Performance-Statistiken
            f.write("\n## Performance\n\n")
            avg_time_single = sum(r['search_time'] for r in results['single_keywords']) / len(results['single_keywords'])
            avg_time_pairs = sum(r['search_time'] for r in results['keyword_pairs']) / len(results['keyword_pairs'])
            avg_time_triples = sum(r['search_time'] for r in results['keyword_triples']) / len(results['keyword_triples'])
            
            f.write(f"- Durchschnittliche Suchzeit (einzelne Keywords): {avg_time_single:.3f}s\n")
            f.write(f"- Durchschnittliche Suchzeit (Keyword-Paare): {avg_time_pairs:.3f}s\n")
            f.write(f"- Durchschnittliche Suchzeit (Keyword-Tripel): {avg_time_triples:.3f}s\n")
            
            # Detaillierte Ergebnisse
            f.write("\n## Detaillierte Ergebnisse\n\n")
            
            # Alle 50 Keywords mit je 10 Versen
            f.write("### Einzelne Keywords (50)\n\n")
            for kw in results['single_keywords']:
                f.write(f"#### {kw['keyword']} ({kw['total_matches']:,} Treffer gesamt, Top 10 angezeigt, {kw['search_time']:.3f}s)\n\n")
                if kw['count'] > 0:
                    for i, verse in enumerate(kw['results'], 1):
                        f.write(f"{i}. **{verse['reference']}** (Score: {verse['score']:.4f})\n")
                        f.write(f"   > {verse['text']}\n\n")
                else:
                    f.write("*Keine Treffer*\n\n")
                f.write("\n")
            
            # Alle Keyword-Paare
            f.write("### Keyword-Paare (15)\n\n")
            for pair in results['keyword_pairs']:
                f.write(f"#### {' + '.join(pair['keywords'])} ({pair['count']} Treffer, AND, {pair['search_time']:.3f}s)\n\n")
                if pair['count'] > 0:
                    for i, verse in enumerate(pair['results'], 1):
                        f.write(f"{i}. **{verse['reference']}** (Score: {verse['score']:.4f})\n")
                        f.write(f"   > {verse['text']}\n\n")
                else:
                    f.write("*Keine Treffer*\n\n")
                f.write("\n")
            
            # Alle Keyword-Tripel
            f.write("### Keyword-Tripel (10)\n\n")
            for triple in results['keyword_triples']:
                f.write(f"#### {' + '.join(triple['keywords'])} ({triple['count']} Treffer, AND, {triple['search_time']:.3f}s)\n\n")
                if triple['count'] > 0:
                    for i, verse in enumerate(triple['results'], 1):
                        f.write(f"{i}. **{verse['reference']}** (Score: {verse['score']:.4f})\n")
                        f.write(f"   > {verse['text']}\n\n")
                else:
                    f.write("*Keine Treffer*\n\n")
                f.write("\n")
        
        print(f"Markdown-Report gespeichert in: {filename}")
    
    def cleanup(self):
        """Schließe Datenbankverbindung"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


def main():
    """Hauptfunktion"""
    print("NGÜ Bibelvers-Sponsoring - Keyword Search Test")
    print("FINALES DATASET mit allen unübersetzten Büchern")
    
    tester = FinalKeywordSearchTester()
    
    # Führe Tests durch
    results = tester.run_all_tests()
    
    # Speichere Ergebnisse
    tester.save_results(results)
    
    # Zusammenfassung
    print("\n" + "="*80)
    print("TEST ABGESCHLOSSEN")
    print("="*80)
    
    # Berechne Statistiken
    total_searches = len(TOP_50_KEYWORDS) + len(KEYWORD_PAIRS) + len(KEYWORD_TRIPLES)
    total_time = (
        sum(r['search_time'] for r in results['single_keywords']) +
        sum(r['search_time'] for r in results['keyword_pairs']) +
        sum(r['search_time'] for r in results['keyword_triples'])
    )
    
    print(f"\n✓ {total_searches} Suchanfragen durchgeführt")
    print(f"✓ {tester.verse_count:,} Verse durchsucht")
    print(f"✓ Gesamtzeit: {total_time:.2f}s")
    print(f"✓ Durchschnitt: {total_time/total_searches:.3f}s pro Suche")
    
    tester.cleanup()


if __name__ == "__main__":
    main()
