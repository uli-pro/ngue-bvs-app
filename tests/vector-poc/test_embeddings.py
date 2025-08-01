#!/usr/bin/env python3
"""
Vector Search Proof of Concept für NGÜ Bibelvers-Sponsoring App

Dieses Script testet:
1. Embedding-Qualität für deutsche Bibeltexte
2. Vergleich zwischen Schlachter 1951 und HFA 2015
3. Semantische Suche mit Cosine Similarity
4. Performance-Benchmarks

Autor: Ulrich Probst
Datum: August 2025
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
import pandas as pd

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

# Embedding-Modelle zum Testen
MODELS_TO_TEST = [
    'paraphrase-multilingual-MiniLM-L12-v2',  # Schnell, mehrsprachig
    'paraphrase-multilingual-mpnet-base-v2',   # Größer, genauer
    # OpenAI würde API-Key benötigen
]


class VectorSearchTester:
    def __init__(self, model_name: str):
        """Initialisiere Tester mit spezifischem Embedding-Modell"""
        print(f"\n{'='*60}")
        print(f"Initialisiere Modell: {model_name}")
        print(f"{'='*60}")
        
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Embedding-Dimension: {self.dimension}")
        
        # Lade Testdaten
        with open('sample_verses.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
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
        self.cur.execute("DROP TABLE IF EXISTS test_verses CASCADE;")
        
        # Erstelle Tabelle
        self.cur.execute(f"""
            CREATE TABLE test_verses (
                id SERIAL PRIMARY KEY,
                reference VARCHAR(20) UNIQUE,
                text_schlachter TEXT,
                text_hfa TEXT,
                embedding_schlachter vector({self.dimension}),
                embedding_hfa vector({self.dimension}),
                themes TEXT[]
            );
        """)
        
        # Erstelle Index für Vektor-Suche
        self.cur.execute("""
            CREATE INDEX ON test_verses 
            USING ivfflat (embedding_hfa vector_cosine_ops)
            WITH (lists = 10);
        """)
        
        print("Datenbank eingerichtet!")
    
    def generate_embeddings(self):
        """Generiere Embeddings für alle Testverse"""
        print("\nGeneriere Embeddings...")
        
        verses_data = []
        start_time = time.time()
        
        for verse in self.data['test_verses']:
            # Embeddings für beide Übersetzungen
            emb_schlachter = self.model.encode(verse['schlachter'])
            emb_hfa = self.model.encode(verse['hfa'])
            
            verses_data.append((
                verse['reference'],
                verse['schlachter'],
                verse['hfa'],
                emb_schlachter.tolist(),
                emb_hfa.tolist(),
                verse['theme']
            ))
            
            print(f"  ✓ {verse['reference']}")
        
        # Batch-Insert
        execute_values(
            self.cur,
            """
            INSERT INTO test_verses 
            (reference, text_schlachter, text_hfa, embedding_schlachter, embedding_hfa, themes)
            VALUES %s
            """,
            verses_data,
            template="(%s, %s, %s, %s::vector, %s::vector, %s)"
        )
        
        elapsed = time.time() - start_time
        print(f"\nEmbeddings generiert in {elapsed:.2f} Sekunden")
        print(f"Durchschnitt: {elapsed/len(verses_data):.3f} Sekunden pro Vers")
    
    def search_similar_verses(self, query: str, use_hfa: bool = True) -> List[Dict]:
        """Suche ähnliche Verse basierend auf Query"""
        # Generiere Embedding für Query
        query_embedding = self.model.encode(query)
        
        # Wähle Spalte
        embedding_col = 'embedding_hfa' if use_hfa else 'embedding_schlachter'
        text_col = 'text_hfa' if use_hfa else 'text_schlachter'
        
        # Cosine Similarity Suche
        self.cur.execute(f"""
            SELECT 
                reference,
                {text_col} as text,
                1 - ({embedding_col} <=> %s::vector) as similarity,
                themes
            FROM test_verses
            ORDER BY {embedding_col} <=> %s::vector
            LIMIT 5
        """, (query_embedding.tolist(), query_embedding.tolist()))
        
        results = []
        for row in self.cur.fetchall():
            results.append({
                'reference': row[0],
                'text': row[1],
                'similarity': float(row[2]),
                'themes': row[3]
            })
        
        return results
    
    def run_search_tests(self):
        """Führe alle Suchtests durch"""
        print("\n" + "="*60)
        print("SUCHTESTS")
        print("="*60)
        
        results = {'hfa': [], 'schlachter': []}
        
        for test_case in self.data['test_queries']:
            query = test_case['query']
            expected = test_case['expected_matches']
            
            print(f"\nSuche: '{query}'")
            print(f"Erwartete Treffer: {', '.join(expected)}")
            
            # Test mit HFA
            print("\n--- Mit HFA 2015 ---")
            hfa_results = self.search_similar_verses(query, use_hfa=True)
            self._print_results(hfa_results, expected)
            results['hfa'].append({
                'query': query,
                'results': hfa_results,
                'expected': expected
            })
            
            # Test mit Schlachter
            print("\n--- Mit Schlachter 1951 ---")
            schlachter_results = self.search_similar_verses(query, use_hfa=False)
            self._print_results(schlachter_results, expected)
            results['schlachter'].append({
                'query': query,
                'results': schlachter_results,
                'expected': expected
            })
        
        return results
    
    def _print_results(self, results: List[Dict], expected: List[str]):
        """Hilfsfunktion zum Formatieren der Ergebnisse"""
        for i, result in enumerate(results, 1):
            is_expected = "✓" if result['reference'] in expected else "✗"
            print(f"{i}. [{is_expected}] {result['reference']} (Ähnlichkeit: {result['similarity']:.3f})")
            print(f"   Text: {result['text'][:80]}...")
            print(f"   Themen: {', '.join(result['themes'])}")
    
    def find_verse_neighbors(self, reference: str):
        """Finde die ähnlichsten Verse zu einem gegebenen Vers"""
        print(f"\n{'='*60}")
        print(f"ÄHNLICHE VERSE ZU {reference}")
        print(f"{'='*60}")
        
        # Hole Embedding des Referenzverses
        self.cur.execute("""
            SELECT embedding_hfa, text_hfa, embedding_schlachter, text_schlachter
            FROM test_verses
            WHERE reference = %s
        """, (reference,))
        
        result = self.cur.fetchone()
        if not result:
            print(f"Vers {reference} nicht gefunden!")
            return
        
        # Suche mit beiden Übersetzungen
        for idx, (embedding, text, translation) in enumerate([
            (result[0], result[1], "HFA 2015"),
            (result[2], result[3], "Schlachter 1951")
        ]):
            print(f"\n--- Basierend auf {translation} ---")
            print(f"Original: {text}")
            
            embedding_col = 'embedding_hfa' if idx == 0 else 'embedding_schlachter'
            
            self.cur.execute(f"""
                SELECT 
                    reference,
                    text_hfa,
                    1 - ({embedding_col} <=> %s::vector) as similarity
                FROM test_verses
                WHERE reference != %s
                ORDER BY {embedding_col} <=> %s::vector
                LIMIT 3
            """, (embedding, reference, embedding))
            
            print("\nÄhnlichste Verse:")
            for i, (ref, text, sim) in enumerate(self.cur.fetchall(), 1):
                print(f"{i}. {ref} (Ähnlichkeit: {sim:.3f})")
                print(f"   {text[:100]}...")
    
    def generate_report(self, all_results: Dict):
        """Generiere Zusammenfassungsbericht"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"results/report_{self.model_name}_{timestamp}.md"
        
        # Erstelle results Verzeichnis
        os.makedirs("results", exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Vector Search Test Report\n\n")
            f.write(f"**Modell**: {self.model_name}\n")
            f.write(f"**Datum**: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"**Embedding-Dimension**: {self.dimension}\n\n")
            
            f.write("## Zusammenfassung\n\n")
            
            # Berechne Erfolgsquote
            for translation in ['hfa', 'schlachter']:
                total_expected = sum(len(test['expected']) for test in all_results[translation])
                total_found = 0
                
                for test in all_results[translation]:
                    found_refs = [r['reference'] for r in test['results'][:3]]  # Top 3
                    total_found += sum(1 for exp in test['expected'] if exp in found_refs)
                
                success_rate = (total_found / total_expected) * 100 if total_expected > 0 else 0
                f.write(f"- **{translation.upper()} Erfolgsquote**: {success_rate:.1f}% ")
                f.write(f"({total_found}/{total_expected} erwartete Treffer in Top 3)\n")
            
            f.write("\n## Detaillierte Ergebnisse\n\n")
            
            for test in all_results['hfa']:
                f.write(f"### Query: '{test['query']}'\n\n")
                f.write(f"**Erwartete Treffer**: {', '.join(test['expected'])}\n\n")
                
                f.write("#### HFA 2015 Ergebnisse:\n")
                for i, result in enumerate(test['results'][:5], 1):
                    is_expected = "✓" if result['reference'] in test['expected'] else "✗"
                    f.write(f"{i}. [{is_expected}] **{result['reference']}** ")
                    f.write(f"(Ähnlichkeit: {result['similarity']:.3f})\n")
                    f.write(f"   > {result['text']}\n\n")
        
        print(f"\n✓ Bericht gespeichert: {report_file}")
    
    def cleanup(self):
        """Schließe Datenbankverbindung"""
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    """Hauptfunktion"""
    print("NGÜ Bibelvers-Sponsoring - Vector Search POC")
    print("=" * 60)
    
    all_model_results = {}
    
    for model_name in MODELS_TO_TEST:
        try:
            tester = VectorSearchTester(model_name)
            
            # Generiere Embeddings
            tester.generate_embeddings()
            
            # Führe Suchtests durch
            results = tester.run_search_tests()
            
            # Teste Vers-Ähnlichkeit
            tester.find_verse_neighbors("PSA.23.1")
            
            # Speichere Ergebnisse
            all_model_results[model_name] = results
            
            # Generiere Bericht
            tester.generate_report(results)
            
            # Aufräumen
            tester.cleanup()
            
        except Exception as e:
            print(f"\n❌ Fehler bei Modell {model_name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Abschlusszusammenfassung
    print("\n" + "="*60)
    print("TESTLAUF ABGESCHLOSSEN")
    print("="*60)
    print("\nGetestete Modelle:")
    for model in all_model_results.keys():
        print(f"  ✓ {model}")
    print(f"\nBerichte gespeichert im 'results' Verzeichnis")
    print("\nNächste Schritte:")
    print("1. Berichte analysieren")
    print("2. Bestes Modell auswählen")
    print("3. Mit größerer Datenmenge testen")
    print("4. Performance-Optimierungen identifizieren")


if __name__ == "__main__":
    main()
