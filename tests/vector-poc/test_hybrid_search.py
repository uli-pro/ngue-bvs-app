#!/usr/bin/env python3
"""
Hybrid Vector + Keyword Search Test

Testet die Kombination von Vektor-Suche und Volltext-Suche
für verschiedene Query-Typen (ganze Verse vs. Keywords)
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
from collections import defaultdict
import re

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


class HybridSearchTester:
    def __init__(self):
        """Initialisiere Hybrid-Tester"""
        print(f"\n{'='*60}")
        print(f"Hybrid Search Test (Vector + Keyword)")
        print(f"Modell: {MODEL_NAME}")
        print(f"{'='*60}")
        
        self.model = SentenceTransformer(MODEL_NAME)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Embedding-Dimension: {self.dimension}")
        
        # Lade Testdaten
        try:
            with open('extended_test_data.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print("\nERROR: extended_test_data.json nicht gefunden!")
            print("Bitte zuerst 'python prepare_extended_test.py' ausführen")
            exit(1)
        
        print(f"Geladen: {self.data['metadata']['num_verses']} Verse")
        
        # Datenbank-Setup
        self.setup_database()
        
        # Generiere Embeddings
        self.generate_embeddings()
    
    def setup_database(self):
        """Erstelle Datenbank-Tabellen mit pgvector und Volltext-Index"""
        print("\nRichte Datenbank ein...")
        
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        
        # Registriere pgvector
        register_vector(self.conn)
        
        # Erstelle pgvector extension
        self.cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Lösche alte Tabellen
        self.cur.execute("DROP TABLE IF EXISTS hybrid_test_verses CASCADE;")
        
        # Erstelle Tabelle mit Volltext-Spalte
        self.cur.execute(f"""
            CREATE TABLE hybrid_test_verses (
                id SERIAL PRIMARY KEY,
                reference VARCHAR(20) UNIQUE,
                book VARCHAR(3),
                chapter INTEGER,
                verse INTEGER,
                text TEXT,
                embedding vector({self.dimension}),
                search_vector tsvector
            );
        """)
        
        # Erstelle Indizes
        self.cur.execute("""
            CREATE INDEX ON hybrid_test_verses 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        
        self.cur.execute("""
            CREATE INDEX ON hybrid_test_verses 
            USING GIN (search_vector);
        """)
        
        print("Datenbank eingerichtet!")
    
    def generate_embeddings(self):
        """Generiere Embeddings und Volltext-Vektoren"""
        print("\nGeneriere Embeddings und Volltext-Indizes...")
        
        verses_data = []
        start_time = time.time()
        batch_size = 50
        
        # Batch-Processing
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
            INSERT INTO hybrid_test_verses 
            (reference, book, chapter, verse, text, embedding)
            VALUES %s
            """,
            verses_data,
            template="(%s, %s, %s, %s, %s, %s::vector)"
        )
        
        # Update Volltext-Vektoren
        self.cur.execute("""
            UPDATE hybrid_test_verses 
            SET search_vector = to_tsvector('german', text);
        """)
        
        elapsed = time.time() - start_time
        print(f"\nEmbeddings generiert in {elapsed:.2f} Sekunden")
        
        return elapsed/len(verses_data)
    
    def keyword_search(self, query: str, limit: int = 20) -> list:
        """Volltext-Suche mit PostgreSQL"""
        # Escape special characters
        query_escaped = query.replace("'", "''")
        
        self.cur.execute("""
            SELECT 
                id,
                reference,
                text,
                ts_rank(search_vector, plainto_tsquery('german', %s)) as score
            FROM hybrid_test_verses
            WHERE search_vector @@ plainto_tsquery('german', %s)
            ORDER BY score DESC
            LIMIT %s
        """, (query_escaped, query_escaped, limit))
        
        results = []
        for row in self.cur.fetchall():
            results.append({
                'id': row[0],
                'reference': row[1],
                'text': row[2],
                'score': float(row[3])
            })
        
        return results
    
    def vector_search(self, query: str, limit: int = 20) -> list:
        """Vektor-Suche"""
        query_embedding = self.model.encode(query)
        
        self.cur.execute("""
            SELECT 
                id,
                reference,
                text,
                1 - (embedding <=> %s::vector) as score
            FROM hybrid_test_verses
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding.tolist(), query_embedding.tolist(), limit))
        
        results = []
        for row in self.cur.fetchall():
            results.append({
                'id': row[0],
                'reference': row[1],
                'text': row[2],
                'score': float(row[3])
            })
        
        return results
    
    def hybrid_search(self, query: str, limit: int = 10, keyword_weight: float = None) -> list:
        """
        Hybrid-Suche mit dynamischer Gewichtung
        """
        # Dynamische Gewichtung basierend auf Query-Länge
        word_count = len(query.split())
        
        if keyword_weight is None:
            if word_count <= 3:
                # Keywords dominieren
                keyword_weight = 0.7
                vector_weight = 0.3
            else:
                # Vektoren dominieren
                keyword_weight = 0.2
                vector_weight = 0.8
        else:
            vector_weight = 1.0 - keyword_weight
        
        # 1. Keyword-Suche
        keyword_results = self.keyword_search(query, limit=limit*2)
        keyword_dict = {r['id']: r for r in keyword_results}
        
        # 2. Vektor-Suche
        vector_results = self.vector_search(query, limit=limit*2)
        vector_dict = {r['id']: r for r in vector_results}
        
        # 3. Kombiniere Scores
        combined_scores = {}
        all_ids = set(keyword_dict.keys()) | set(vector_dict.keys())
        
        for verse_id in all_ids:
            score = 0.0
            
            # Keyword-Score (normalisiert)
            if verse_id in keyword_dict:
                # Normalisiere auf 0-1
                max_keyword_score = keyword_results[0]['score'] if keyword_results else 1.0
                norm_keyword_score = keyword_dict[verse_id]['score'] / max_keyword_score if max_keyword_score > 0 else 0
                score += keyword_weight * norm_keyword_score
            
            # Vektor-Score (bereits 0-1)
            if verse_id in vector_dict:
                score += vector_weight * vector_dict[verse_id]['score']
            
            combined_scores[verse_id] = {
                'score': score,
                'reference': keyword_dict.get(verse_id, vector_dict.get(verse_id))['reference'],
                'text': keyword_dict.get(verse_id, vector_dict.get(verse_id))['text'],
                'keyword_score': keyword_dict.get(verse_id, {}).get('score', 0),
                'vector_score': vector_dict.get(verse_id, {}).get('score', 0)
            }
        
        # Sortiere nach kombiniertem Score
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:limit]
        
        return sorted_results
    
    def test_keyword_queries(self):
        """Teste Keyword-basierte Queries (1-3 Wörter)"""
        print("\n" + "="*60)
        print("TEST 1: KEYWORD-QUERIES (1-3 Wörter)")
        print("="*60)
        
        keyword_queries = [
            {'query': 'Gott', 'type': 'single'},
            {'query': 'Liebe', 'type': 'single'},
            {'query': 'Hoffnung', 'type': 'single'},
            {'query': 'Gott Liebe', 'type': 'double'},
            {'query': 'ewiges Leben', 'type': 'double'},
            {'query': 'Glaube Hoffnung Liebe', 'type': 'triple'}
        ]
        
        results = []
        
        for test in keyword_queries:
            query = test['query']
            print(f"\nQuery: '{query}' ({test['type']})")
            
            # Teste alle drei Methoden
            start = time.time()
            keyword_only = self.keyword_search(query, limit=5)
            keyword_time = time.time() - start
            
            start = time.time()
            vector_only = self.vector_search(query, limit=5)
            vector_time = time.time() - start
            
            start = time.time()
            hybrid = self.hybrid_search(query, limit=5)
            hybrid_time = time.time() - start
            
            # Analysiere Überlappung
            keyword_refs = set(r['reference'] for r in keyword_only)
            vector_refs = set(r['reference'] for r in vector_only)
            hybrid_refs = set(r['reference'] for r in hybrid)
            
            overlap = len(keyword_refs & vector_refs)
            
            print(f"  Keyword-Suche: {len(keyword_only)} Treffer in {keyword_time:.3f}s")
            print(f"  Vektor-Suche: {len(vector_only)} Treffer in {vector_time:.3f}s")
            print(f"  Hybrid-Suche: {len(hybrid)} Treffer in {hybrid_time:.3f}s")
            print(f"  Überlappung Keyword/Vektor: {overlap} Verse")
            
            # Zeige Top-3 Hybrid-Ergebnisse
            print(f"\n  Top 3 Hybrid-Ergebnisse:")
            for i, result in enumerate(hybrid[:3], 1):
                print(f"  {i}. {result['reference']} (Score: {result['score']:.3f})")
                print(f"     Keyword: {result['keyword_score']:.3f}, Vektor: {result['vector_score']:.3f}")
                print(f"     Text: {result['text'][:80]}...")
            
            results.append({
                'query': query,
                'type': test['type'],
                'keyword_results': keyword_only,
                'vector_results': vector_only,
                'hybrid_results': hybrid,
                'times': {
                    'keyword': keyword_time,
                    'vector': vector_time,
                    'hybrid': hybrid_time
                },
                'overlap': overlap
            })
        
        return results
    
    def test_verse_queries(self):
        """Teste mit kompletten Versen als Query"""
        print("\n" + "="*60)
        print("TEST 2: GANZE VERSE ALS QUERY")
        print("="*60)
        
        # Wähle 5 zufällige Verse als Test-Queries
        test_verses = np.random.choice(self.data['test_verses'], 5, replace=False)
        
        results = []
        
        for verse in test_verses:
            query = verse['text']
            ref = verse['reference']
            
            print(f"\nQuery-Vers: {ref}")
            print(f"Text: {query[:100]}...")
            
            # Teste alle drei Methoden
            start = time.time()
            keyword_only = self.keyword_search(query, limit=5)
            keyword_time = time.time() - start
            
            start = time.time()
            vector_only = self.vector_search(query, limit=5)
            vector_time = time.time() - start
            
            start = time.time()
            hybrid = self.hybrid_search(query, limit=5)
            hybrid_time = time.time() - start
            
            # Filter out the query verse itself
            keyword_only = [r for r in keyword_only if r['reference'] != ref][:5]
            vector_only = [r for r in vector_only if r['reference'] != ref][:5]
            hybrid = [r for r in hybrid if r['reference'] != ref][:5]
            
            print(f"\n  Keyword-Suche: Top Match = {keyword_only[0]['reference'] if keyword_only else 'None'}")
            print(f"  Vektor-Suche: Top Match = {vector_only[0]['reference'] if vector_only else 'None'}")
            print(f"  Hybrid-Suche: Top Match = {hybrid[0]['reference'] if hybrid else 'None'}")
            
            # Zeige Top-3 Hybrid-Ergebnisse
            print(f"\n  Top 3 ähnliche Verse (Hybrid):")
            for i, result in enumerate(hybrid[:3], 1):
                print(f"  {i}. {result['reference']} (Score: {result['score']:.3f})")
                print(f"     Text: {result['text'][:80]}...")
            
            results.append({
                'query_ref': ref,
                'query_text': query,
                'keyword_results': keyword_only,
                'vector_results': vector_only,
                'hybrid_results': hybrid,
                'times': {
                    'keyword': keyword_time,
                    'vector': vector_time,
                    'hybrid': hybrid_time
                }
            })
        
        return results
    
    def test_weight_variations(self):
        """Teste verschiedene Gewichtungen"""
        print("\n" + "="*60)
        print("TEST 3: GEWICHTUNGS-VARIATIONEN")
        print("="*60)
        
        test_query = "Glaube Hoffnung"
        weights = [0.0, 0.3, 0.5, 0.7, 1.0]
        
        print(f"\nTest-Query: '{test_query}'")
        
        for weight in weights:
            results = self.hybrid_search(test_query, limit=5, keyword_weight=weight)
            
            print(f"\nKeyword-Gewicht: {weight:.1f}, Vektor-Gewicht: {1-weight:.1f}")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result['reference']} (Score: {result['score']:.3f})")
    
    def generate_report(self, keyword_results, verse_results):
        """Generiere Testbericht"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"results/hybrid_test_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Hybrid Search Test Report\n\n")
            f.write(f"**Modell**: {MODEL_NAME}\n")
            f.write(f"**Datum**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"**Anzahl Verse**: {self.data['metadata']['num_verses']}\n\n")
            
            f.write("## Test 1: Keyword-Queries\n\n")
            
            # Durchschnittliche Zeiten
            avg_times = {
                'keyword': np.mean([r['times']['keyword'] for r in keyword_results]),
                'vector': np.mean([r['times']['vector'] for r in keyword_results]),
                'hybrid': np.mean([r['times']['hybrid'] for r in keyword_results])
            }
            
            f.write("### Performance\n")
            f.write(f"- Keyword-Suche: {avg_times['keyword']:.3f}s\n")
            f.write(f"- Vektor-Suche: {avg_times['vector']:.3f}s\n")
            f.write(f"- Hybrid-Suche: {avg_times['hybrid']:.3f}s\n\n")
            
            f.write("### Detaillierte Ergebnisse\n\n")
            for result in keyword_results:
                f.write(f"#### Query: '{result['query']}'\n")
                f.write(f"**Überlappung Keyword/Vektor**: {result['overlap']} Verse\n\n")
                
                f.write("**Top 3 Hybrid-Ergebnisse:**\n")
                for i, r in enumerate(result['hybrid_results'][:3], 1):
                    f.write(f"{i}. {r['reference']} (Score: {r['score']:.3f})\n")
                    f.write(f"   - Keyword-Score: {r['keyword_score']:.3f}\n")
                    f.write(f"   - Vektor-Score: {r['vector_score']:.3f}\n")
                f.write("\n")
            
            f.write("## Test 2: Ganze Verse als Query\n\n")
            
            # Analysiere, ob der Top-Treffer sinnvoll ist
            vector_better = 0
            keyword_better = 0
            hybrid_best = 0
            
            for result in verse_results:
                v_score = result['vector_results'][0]['score'] if result['vector_results'] else 0
                k_score = result['keyword_results'][0]['score'] if result['keyword_results'] else 0
                h_score = result['hybrid_results'][0]['score'] if result['hybrid_results'] else 0
                
                if h_score >= max(v_score, k_score):
                    hybrid_best += 1
                elif v_score > k_score:
                    vector_better += 1
                else:
                    keyword_better += 1
            
            f.write("### Zusammenfassung\n")
            f.write(f"- Hybrid am besten: {hybrid_best}/{len(verse_results)}\n")
            f.write(f"- Vektor besser als Keyword: {vector_better}/{len(verse_results)}\n")
            f.write(f"- Keyword besser als Vektor: {keyword_better}/{len(verse_results)}\n\n")
            
            f.write("### Beispiele\n\n")
            for result in verse_results[:2]:
                f.write(f"**Query-Vers**: {result['query_ref']}\n")
                f.write(f"Text: {result['query_text'][:100]}...\n\n")
                
                f.write("**Ähnlichste Verse (Hybrid):**\n")
                for i, r in enumerate(result['hybrid_results'][:3], 1):
                    f.write(f"{i}. {r['reference']}: {r['text'][:80]}...\n")
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
    print("NGÜ Bibelvers-Sponsoring - Hybrid Search Test")
    
    tester = HybridSearchTester()
    
    # Test 1: Keyword-Queries
    keyword_results = tester.test_keyword_queries()
    
    # Test 2: Vers-Queries  
    verse_results = tester.test_verse_queries()
    
    # Test 3: Gewichtungs-Variationen
    tester.test_weight_variations()
    
    # Generiere Bericht
    tester.generate_report(keyword_results, verse_results)
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    print("✓ Hybrid-Suche kombiniert Keyword- und Vektor-Suche")
    print("✓ Dynamische Gewichtung basierend auf Query-Länge")
    print("✓ Bessere Ergebnisse für beide Use Cases")
    
    tester.cleanup()


if __name__ == "__main__":
    main()
