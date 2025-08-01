#!/usr/bin/env python3
"""
Erweiterter Vector Search Test - Nur Schlachter 1951

Testet die Suchqualität mit 100 echten AT-Versen
"""

import json
import time
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
from datetime import datetime

# Lade Umgebungsvariablen
load_dotenv()

# Konfiguration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ulrichprobst'),  # Default database in Postgres.app
    'user': os.getenv('DB_USER', 'ulrichprobst'),      # Your system username
    'password': os.getenv('DB_PASSWORD', '')           # No password by default
}

# Verwende das beste Modell aus dem ersten Test
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'


class ExtendedVectorTester:
    def __init__(self):
        """Initialisiere Tester"""
        print(f"\n{'='*60}")
        print(f"Erweiterter Vector Search Test")
        print(f"Modell: {MODEL_NAME}")
        print(f"{'='*60}")
        
        self.model = SentenceTransformer(MODEL_NAME)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Embedding-Dimension: {self.dimension}")
        
        # Lade erweiterte Testdaten
        try:
            with open('extended_test_data.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print("\nERROR: extended_test_data.json nicht gefunden!")
            print("Bitte zuerst 'python prepare_extended_test.py' ausführen")
            exit(1)
        
        print(f"Geladen: {self.data['metadata']['num_verses']} Verse")
        print(f"Queries: {self.data['metadata']['num_queries']}")
        
        # Datenbank-Setup
        self.setup_database()
    
    def setup_database(self):
        """Erstelle Datenbank-Tabellen mit pgvector"""
        print("\nRichte Datenbank ein...")
        
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        
        # Registriere pgvector
        register_vector(self.conn)
        
        # Erstelle pgvector extension
        self.cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Lösche alte Tabellen
        self.cur.execute("DROP TABLE IF EXISTS extended_test_verses CASCADE;")
        
        # Erstelle Tabelle
        self.cur.execute(f"""
            CREATE TABLE extended_test_verses (
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
        self.cur.execute("""
            CREATE INDEX ON extended_test_verses 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 10);
        """)
        
        print("Datenbank eingerichtet!")
    
    def generate_embeddings(self):
        """Generiere Embeddings für alle Testverse"""
        print("\nGeneriere Embeddings...")
        
        verses_data = []
        start_time = time.time()
        batch_size = 10
        
        # Batch-Processing für bessere Performance
        for i in range(0, len(self.data['test_verses']), batch_size):
            batch = self.data['test_verses'][i:i+batch_size]
            texts = [v['text'] for v in batch]
            
            # Batch-Encoding
            embeddings = self.model.encode(texts)
            
            for verse, embedding in zip(batch, embeddings):
                verses_data.append((
                    verse['reference'],
                    verse['book'],
                    verse['chapter'],
                    verse['verse'],
                    verse['text'],
                    embedding.tolist()
                ))
            
            print(f"  Verarbeitet: {min(i+batch_size, len(self.data['test_verses']))}/{len(self.data['test_verses'])}")
        
        # Batch-Insert
        execute_values(
            self.cur,
            """
            INSERT INTO extended_test_verses 
            (reference, book, chapter, verse, text, embedding)
            VALUES %s
            """,
            verses_data,
            template="(%s, %s, %s, %s, %s, %s::vector)"
        )
        
        elapsed = time.time() - start_time
        print(f"\nEmbeddings generiert in {elapsed:.2f} Sekunden")
        print(f"Durchschnitt: {elapsed/len(verses_data):.3f} Sekunden pro Vers")
        
        return elapsed/len(verses_data)  # Durchschnittszeit pro Vers
    
    def search_verses(self, query: str, limit: int = 10) -> list:
        """Suche ähnliche Verse"""
        query_embedding = self.model.encode(query)
        
        self.cur.execute("""
            SELECT 
                reference,
                text,
                1 - (embedding <=> %s::vector) as similarity
            FROM extended_test_verses
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding.tolist(), query_embedding.tolist(), limit))
        
        return [
            {
                'reference': row[0],
                'text': row[1],
                'similarity': float(row[2])
            }
            for row in self.cur.fetchall()
        ]
    
    def evaluate_search_quality(self):
        """Evaluiere Suchqualität mit verschiedenen Metriken"""
        print("\n" + "="*60)
        print("EVALUIERUNG DER SUCHQUALITÄT")
        print("="*60)
        
        results = {
            'precision_at_1': [],
            'precision_at_3': [],
            'precision_at_5': [],
            'precision_at_10': [],
            'mean_reciprocal_rank': [],
            'queries': []
        }
        
        total_search_time = 0
        
        for test_query in self.data['test_queries']:
            query = test_query['query']
            expected = test_query['expected_matches']
            
            # Zeit messen
            start_time = time.time()
            search_results = self.search_verses(query, limit=10)
            search_time = time.time() - start_time
            total_search_time += search_time
            
            # Ergebnisse analysieren
            found_refs = [r['reference'] for r in search_results]
            
            # Precision at K
            for k in [1, 3, 5, 10]:
                hits = sum(1 for ref in found_refs[:k] if ref in expected)
                precision = hits / min(k, len(expected)) if expected else 0
                results[f'precision_at_{k}'].append(precision)
            
            # Mean Reciprocal Rank
            mrr = 0
            for rank, ref in enumerate(found_refs, 1):
                if ref in expected:
                    mrr = 1.0 / rank
                    break
            results['mean_reciprocal_rank'].append(mrr)
            
            # Speichere Query-Details
            results['queries'].append({
                'query': query,
                'expected': expected,
                'found': found_refs[:5],
                'search_time': search_time
            })
            
            print(f"\nQuery: '{query}'")
            print(f"Erwartete Treffer: {len(expected)}")
            print(f"Gefunden in Top 5: {sum(1 for r in found_refs[:5] if r in expected)}")
            print(f"Suchzeit: {search_time:.3f}s")
        
        # Berechne Durchschnitte
        avg_results = {
            'avg_precision_at_1': np.mean(results['precision_at_1']),
            'avg_precision_at_3': np.mean(results['precision_at_3']),
            'avg_precision_at_5': np.mean(results['precision_at_5']),
            'avg_precision_at_10': np.mean(results['precision_at_10']),
            'avg_mrr': np.mean(results['mean_reciprocal_rank']),
            'avg_search_time': total_search_time / len(self.data['test_queries'])
        }
        
        return results, avg_results
    
    def analyze_by_book_type(self):
        """Analysiere Performance nach Buchtyp"""
        print("\n" + "="*60)
        print("ANALYSE NACH BUCHTYP")
        print("="*60)
        
        # Gruppiere Verse nach Buchtyp
        book_types = {
            'Geschichte': ['GEN'],
            'Poesie': ['PSA', 'LAM'],
            'Weisheit': ['PRO', 'JOB', 'ECC'],
            'Propheten': ['ISA', 'JER', 'DAN', 'HOS']
        }
        
        for book_type, books in book_types.items():
            # Zähle Verse pro Typ
            verses_count = sum(
                1 for v in self.data['test_verses'] 
                if v['book'] in books
            )
            
            if verses_count > 0:
                print(f"\n{book_type}: {verses_count} Verse")
                
                # Teste mit einer typischen Query
                test_query = "Gott"
                results = self.search_verses(test_query, limit=20)
                
                # Zähle Treffer aus diesem Buchtyp
                hits_from_type = sum(
                    1 for r in results[:10] 
                    if any(r['reference'].startswith(b) for b in books)
                )
                
                print(f"  Treffer bei Suche nach '{test_query}': {hits_from_type}/10")
    
    def generate_report(self, results, avg_results, embedding_time):
        """Generiere detaillierten Bericht"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"results/extended_test_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Erweiterter Vector Search Test Report\n\n")
            f.write(f"**Modell**: {MODEL_NAME}\n")
            f.write(f"**Datum**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"**Anzahl Verse**: {self.data['metadata']['num_verses']}\n")
            f.write(f"**Anzahl Queries**: {self.data['metadata']['num_queries']}\n")
            f.write(f"**Getestete Bücher**: {', '.join(self.data['metadata']['books_included'])}\n\n")
            
            f.write("## Performance-Metriken\n\n")
            f.write(f"- **Embedding-Zeit pro Vers**: {embedding_time:.3f}s\n")
            f.write(f"- **Durchschnittliche Suchzeit**: {avg_results['avg_search_time']:.3f}s\n")
            f.write(f"- **Geschätzte Zeit für 11.000 Verse**: {embedding_time * 11000 / 60:.1f} Minuten\n\n")
            
            f.write("## Suchqualität\n\n")
            f.write(f"- **Precision@1**: {avg_results['avg_precision_at_1']:.1%}\n")
            f.write(f"- **Precision@3**: {avg_results['avg_precision_at_3']:.1%}\n")
            f.write(f"- **Precision@5**: {avg_results['avg_precision_at_5']:.1%}\n")
            f.write(f"- **Precision@10**: {avg_results['avg_precision_at_10']:.1%}\n")
            f.write(f"- **Mean Reciprocal Rank**: {avg_results['avg_mrr']:.3f}\n\n")
            
            f.write("## Detaillierte Query-Ergebnisse\n\n")
            for query_result in results['queries']:
                f.write(f"### Query: '{query_result['query']}'\n")
                f.write(f"**Suchzeit**: {query_result['search_time']:.3f}s\n\n")
                f.write(f"**Erwartete Treffer** ({len(query_result['expected'])}):\n")
                for ref in query_result['expected'][:5]:
                    f.write(f"- {ref}\n")
                f.write(f"\n**Gefundene Treffer** (Top 5):\n")
                for i, ref in enumerate(query_result['found'], 1):
                    is_hit = "✓" if ref in query_result['expected'] else "✗"
                    f.write(f"{i}. [{is_hit}] {ref}\n")
                f.write("\n")
        
        print(f"\n✓ Bericht gespeichert: {report_file}")
    
    def cleanup(self):
        """Schließe Datenbankverbindung"""
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    """Hauptfunktion"""
    print("NGÜ Bibelvers-Sponsoring - Erweiterter Vector Search Test")
    print("Nur Schlachter 1951")
    
    tester = ExtendedVectorTester()
    
    # Generiere Embeddings und messe Zeit
    embedding_time = tester.generate_embeddings()
    
    # Evaluiere Suchqualität
    results, avg_results = tester.evaluate_search_quality()
    
    # Analysiere nach Buchtyp
    tester.analyze_by_book_type()
    
    # Generiere Bericht
    tester.generate_report(results, avg_results, embedding_time)
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    print(f"✓ Precision@5: {avg_results['avg_precision_at_5']:.1%}")
    print(f"✓ Durchschnittliche Suchzeit: {avg_results['avg_search_time']:.3f}s")
    print(f"✓ Embedding-Zeit für 11.000 Verse: ~{embedding_time * 11000 / 60:.0f} Minuten")
    
    tester.cleanup()


if __name__ == "__main__":
    main()
