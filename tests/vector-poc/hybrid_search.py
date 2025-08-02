#!/usr/bin/env python3
"""
Hybrid Search Implementation für die NGÜ Bibelvers-Sponsoring App

Kombiniert Vektor-basierte semantische Suche mit Keyword-Suche
für optimale Ergebnisse bei verschiedenen Query-Typen.
"""

from typing import List, Dict, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Einzelnes Suchergebnis"""
    id: int
    reference: str
    book: str
    chapter: int
    verse: int
    text: str
    score: float
    keyword_score: float = 0.0
    vector_score: float = 0.0


class HybridBibleSearch:
    """
    Hybrid-Suche für Bibelverse
    
    Kombiniert PostgreSQL Volltext-Suche mit pgvector Ähnlichkeitssuche
    """
    
    def __init__(self, 
                 db_config: Dict[str, str],
                 model_name: str = 'paraphrase-multilingual-mpnet-base-v2',
                 table_name: str = 'bible_verses'):
        """
        Initialisiere Hybrid-Suche
        
        Args:
            db_config: PostgreSQL Verbindungsparameter
            model_name: Name des Sentence Transformer Modells
            table_name: Name der Datenbanktabelle
        """
        self.db_config = db_config
        self.table_name = table_name
        self.model = SentenceTransformer(model_name)
        
        # Verbindung testen
        self._test_connection()
    
    def _test_connection(self):
        """Teste Datenbankverbindung"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            logger.info("Datenbankverbindung erfolgreich")
        except Exception as e:
            logger.error(f"Datenbankverbindung fehlgeschlagen: {e}")
            raise
    
    def _get_connection(self):
        """Erstelle neue Datenbankverbindung"""
        return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
    
    def search(self, 
               query: str, 
               limit: int = 10,
               keyword_weight: Optional[float] = None,
               excluded_ids: Optional[List[int]] = None) -> List[SearchResult]:
        """
        Führe Hybrid-Suche durch
        
        Args:
            query: Suchanfrage (Keywords oder ganzer Vers)
            limit: Maximale Anzahl Ergebnisse
            keyword_weight: Gewichtung für Keyword-Suche (0-1)
                           None = automatisch basierend auf Query-Länge
            excluded_ids: Liste von IDs, die ausgeschlossen werden sollen
        
        Returns:
            Liste von SearchResult Objekten
        """
        # Bestimme Gewichtung
        if keyword_weight is None:
            keyword_weight, vector_weight = self._determine_weights(query)
        else:
            vector_weight = 1.0 - keyword_weight
        
        logger.info(f"Suche nach: '{query}' (Keyword: {keyword_weight:.1f}, Vektor: {vector_weight:.1f})")
        
        # Führe beide Suchen parallel durch
        keyword_results = self._keyword_search(query, limit * 2, excluded_ids)
        vector_results = self._vector_search(query, limit * 2, excluded_ids)
        
        # Kombiniere Ergebnisse
        combined_results = self._combine_results(
            keyword_results, 
            vector_results,
            keyword_weight,
            vector_weight
        )
        
        # Sortiere und limitiere
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        return combined_results[:limit]
    
    def _determine_weights(self, query: str) -> Tuple[float, float]:
        """
        Bestimme optimale Gewichtung basierend auf Query
        
        Returns:
            (keyword_weight, vector_weight)
        """
        word_count = len(query.split())
        
        if word_count <= 2:
            # Ein oder zwei Wörter: Keyword-Suche dominiert
            return 0.8, 0.2
        elif word_count <= 5:
            # Kurze Phrase: Ausgewogen
            return 0.5, 0.5
        else:
            # Langer Text/Vers: Vektor-Suche dominiert
            return 0.2, 0.8
    
    def _keyword_search(self, 
                       query: str, 
                       limit: int,
                       excluded_ids: Optional[List[int]] = None) -> List[Dict]:
        """Führe Volltext-Suche durch"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Basis-Query
                sql = f"""
                    SELECT 
                        id,
                        reference,
                        book,
                        chapter,
                        verse,
                        text,
                        ts_rank(search_vector, plainto_tsquery('german', %s)) as score
                    FROM {self.table_name}
                    WHERE search_vector @@ plainto_tsquery('german', %s)
                """
                
                params = [query, query]
                
                # Füge Ausschluss-Filter hinzu
                if excluded_ids:
                    sql += " AND id NOT IN %s"
                    params.append(tuple(excluded_ids))
                
                sql += " ORDER BY score DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(sql, params)
                return cur.fetchall()
    
    def _vector_search(self, 
                      query: str, 
                      limit: int,
                      excluded_ids: Optional[List[int]] = None) -> List[Dict]:
        """Führe Vektor-Ähnlichkeitssuche durch"""
        # Generiere Query-Embedding
        query_embedding = self.model.encode(query)
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Basis-Query
                sql = f"""
                    SELECT 
                        id,
                        reference,
                        book,
                        chapter,
                        verse,
                        text,
                        1 - (embedding <=> %s::vector) as score
                    FROM {self.table_name}
                """
                
                params = [query_embedding.tolist()]
                
                # Füge Ausschluss-Filter hinzu
                if excluded_ids:
                    sql += " WHERE id NOT IN %s"
                    params.append(tuple(excluded_ids))
                
                sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
                params.extend([query_embedding.tolist(), limit])
                
                cur.execute(sql, params)
                return cur.fetchall()
    
    def _combine_results(self,
                        keyword_results: List[Dict],
                        vector_results: List[Dict],
                        keyword_weight: float,
                        vector_weight: float) -> List[SearchResult]:
        """Kombiniere und normalisiere Suchergebnisse"""
        results_dict = {}
        
        # Normalisiere Keyword-Scores
        if keyword_results:
            max_keyword_score = keyword_results[0]['score']
            for result in keyword_results:
                norm_score = result['score'] / max_keyword_score if max_keyword_score > 0 else 0
                
                results_dict[result['id']] = SearchResult(
                    id=result['id'],
                    reference=result['reference'],
                    book=result['book'],
                    chapter=result['chapter'],
                    verse=result['verse'],
                    text=result['text'],
                    score=keyword_weight * norm_score,
                    keyword_score=result['score'],
                    vector_score=0.0
                )
        
        # Füge Vektor-Scores hinzu
        for result in vector_results:
            if result['id'] in results_dict:
                # Update existierendes Ergebnis
                results_dict[result['id']].score += vector_weight * result['score']
                results_dict[result['id']].vector_score = result['score']
            else:
                # Neues Ergebnis
                results_dict[result['id']] = SearchResult(
                    id=result['id'],
                    reference=result['reference'],
                    book=result['book'],
                    chapter=result['chapter'],
                    verse=result['verse'],
                    text=result['text'],
                    score=vector_weight * result['score'],
                    keyword_score=0.0,
                    vector_score=result['score']
                )
        
        return list(results_dict.values())
    
    def find_similar_verses(self, 
                           verse_text: str,
                           verse_id: int,
                           limit: int = 5) -> List[SearchResult]:
        """
        Finde ähnliche Verse zu einem gegebenen Vers
        
        Optimiert für den Use Case "Dieser Vers ist bereits gesponsert"
        
        Args:
            verse_text: Text des ursprünglichen Verses
            verse_id: ID des ursprünglichen Verses (wird ausgeschlossen)
            limit: Anzahl ähnlicher Verse
        
        Returns:
            Liste ähnlicher Verse
        """
        # Verwende hauptsächlich Vektor-Suche für Ähnlichkeit
        return self.search(
            query=verse_text,
            limit=limit,
            keyword_weight=0.1,  # Nur 10% Keyword-Gewicht
            excluded_ids=[verse_id]
        )
    
    def search_by_keywords(self,
                          keywords: str,
                          limit: int = 20) -> List[SearchResult]:
        """
        Suche Verse nach Keywords
        
        Optimiert für den Use Case "Zeige mir Verse über [Thema]"
        
        Args:
            keywords: Ein oder mehrere Suchbegriffe
            limit: Anzahl Ergebnisse
        
        Returns:
            Liste relevanter Verse
        """
        # Automatische Gewichtung basierend auf Anzahl Keywords
        return self.search(
            query=keywords,
            limit=limit,
            keyword_weight=None  # Automatisch bestimmen
        )


# Beispiel-Verwendung
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'ulrichprobst'),
        'user': os.getenv('DB_USER', 'ulrichprobst'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    # Initialisiere Suche
    search = HybridBibleSearch(db_config)
    
    # Beispiel 1: Keyword-Suche
    print("=== Keyword-Suche: 'Liebe Gott' ===")
    results = search.search_by_keywords("Liebe Gott", limit=5)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.reference}: {result.text[:80]}...")
        print(f"   Score: {result.score:.3f} (K: {result.keyword_score:.3f}, V: {result.vector_score:.3f})")
    
    # Beispiel 2: Ähnliche Verse finden
    print("\n=== Ähnliche Verse zu Joh 3,16 ===")
    john316 = "Denn Gott hat die Welt so geliebt, dass er seinen eingeborenen Sohn gab..."
    similar = search.find_similar_verses(john316, verse_id=1234, limit=5)
    for i, result in enumerate(similar, 1):
        print(f"{i}. {result.reference}: {result.text[:80]}...")
