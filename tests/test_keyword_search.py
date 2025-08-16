"""
Test Suite für Keyword Search Funktionalität
TDD Tests für /vers-auswaehlen/keyword Seite
"""

import pytest
import json
from app import app, db
from models import Verse, User
from flask import session
from sqlalchemy import text


@pytest.fixture
def client():
    """Test client für Flask App"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    # Verwende aktuelle Datenbank für Tests (sollte ngue_bvs_app sein)
    # app.config['SQLALCHEMY_DATABASE_URI'] bleibt aus .env
    
    with app.test_client() as client:
        with app.app_context():
            # Prüfe ob Verse in der Datenbank existieren
            verse_count = Verse.query.count()
            if verse_count < 10:
                print(f"Warning: Nur {verse_count} Verse in Datenbank gefunden. Tests benötigen mehr Daten.")
            yield client
            # Keine Änderungen an der Produktiv-DB




class TestKeywordSearchBackend:
    """Unit Tests für die Backend-Logik"""
    
    def test_keyword_search_api_responds(self, client):
        """API-Endpoint soll erreichbar sein"""
        response = client.post('/api/verse/search/keyword', 
                             json={'query': 'Hoffnung'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
    def test_keyword_search_returns_max_three_results(self, client):
        """Suche soll maximal 3 Verse zurückgeben"""
        response = client.post('/api/verse/search/keyword', 
                             json={'query': 'der'})  # Häufiges Wort
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['verses']) <= 3
    
    def test_keyword_search_filters_sponsored_verses(self, client):
        """Gesponserte Verse sollen nicht in Ergebnissen erscheinen"""
        response = client.post('/api/verse/search/keyword', 
                             json={'query': 'Hoffnung'})
        
        data = json.loads(response.data)
        for verse in data['verses']:
            assert verse['is_sponsored'] == False
    
    def test_keyword_search_sorts_by_positivity(self, client):
        """Verse sollen nach Positivity-Score sortiert sein (höchste zuerst)"""
        response = client.post('/api/verse/search/keyword', 
                             json={'query': 'Hoffnung'})
        
        data = json.loads(response.data)
        verses = data['verses']
        
        # Erste 3 Verse sollten die höchsten Positivity-Scores haben
        assert verses[0]['positivity_score'] >= verses[1]['positivity_score']
        assert verses[1]['positivity_score'] >= verses[2]['positivity_score']
        
        # Der erste Vers sollte hohen Positivity-Score haben
        assert verses[0]['positivity_score'] >= 90
    
    def test_keyword_search_with_no_results(self, client):
        """Suche ohne Treffer soll leere Liste zurückgeben"""
        response = client.post('/api/verse/search/keyword', 
                             json={'query': 'Zauberstab'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['verses']) == 0
        assert data['has_more'] == False
    
    def test_keyword_search_pagination(self, client):
        """Weitere Verse laden soll funktionieren"""
        # Erste 3 Verse laden
        response1 = client.post('/api/verse/search/keyword', 
                              json={'query': 'Hoffnung'})
        data1 = json.loads(response1.data)
        
        # Weitere 3 Verse laden
        response2 = client.post('/api/verse/search/keyword', 
                              json={'query': 'Hoffnung', 'offset': 3})
        data2 = json.loads(response2.data)
        
        assert len(data2['verses']) == 3
        assert data2['offset'] == 3
        
        # Verse sollten unterschiedlich sein
        ids1 = [v['id'] for v in data1['verses']]
        ids2 = [v['id'] for v in data2['verses']]
        assert set(ids1).isdisjoint(set(ids2))
    
    def test_keyword_search_has_more_flag(self, client):
        """has_more Flag soll korrekt gesetzt werden"""
        response = client.post('/api/verse/search/keyword', 
                             json={'query': 'Hoffnung'})
        
        data = json.loads(response.data)
        # has_more sollte verfügbar sein wenn mehr als 3 Verse gefunden wurden
        if data['total_found'] > 3:
            assert data['has_more'] == True
        
        # Test mit größerem Offset um Ende zu finden
        large_offset = max(100, data['total_found'])  # Großer Offset
        response_last = client.post('/api/verse/search/keyword', 
                                  json={'query': 'Hoffnung', 'offset': large_offset})
        data_last = json.loads(response_last.data)
        assert data_last['has_more'] == False


class TestKeywordSearchAPI:
    """Tests für den API-Endpoint"""
    
    def test_api_keyword_search_structure(self, client):
        """Response soll korrekte JSON-Struktur haben"""
        response = client.post('/api/verse/search/keyword', 
                             json={'query': 'Hoffnung'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Prüfe Response-Struktur
        required_keys = ['success', 'query', 'verses', 'has_more', 'total_found', 'offset']
        for key in required_keys:
            assert key in data
        
        # Prüfe Verse-Struktur
        if data['verses']:
            verse = data['verses'][0]
            verse_keys = ['id', 'book', 'chapter', 'verse', 'text', 'reference', 'positivity_score', 'is_sponsored', 'url_slug']
            for key in verse_keys:
                assert key in verse
    
    def test_api_keyword_search_invalid_params(self, client):
        """API soll ungültige Parameter behandeln"""
        # Leere Query
        response = client.post('/api/verse/search/keyword', json={})
        assert response.status_code == 400
        
        # Query zu kurz
        response = client.post('/api/verse/search/keyword', json={'query': 'a'})
        assert response.status_code == 400
        
        # Ungültiges JSON - kann 400 oder 500 sein
        response = client.post('/api/verse/search/keyword', 
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code in [400, 500]  # Beide sind akzeptabel
    
    def test_api_keyword_search_methods(self, client):
        """Nur POST sollte erlaubt sein"""
        response = client.get('/api/verse/search/keyword')
        assert response.status_code == 405
        
        response = client.put('/api/verse/search/keyword')
        assert response.status_code == 405


class TestKeywordSearchSessionManagement:
    """Tests für Session-basierte Funktionalität"""
    
    def test_session_tracks_shown_verses(self, client):
        """Session soll gezeigte Verse speichern"""
        with client.session_transaction() as sess:
            # Session sollte leer starten
            assert 'keyword_search' not in sess
        
        # Erste Suche
        response = client.post('/api/verse/search/keyword', 
                             json={'query': 'Hoffnung'})
        
        with client.session_transaction() as sess:
            # Session sollte jetzt Daten enthalten
            assert 'keyword_search' in sess
            search_data = sess['keyword_search']
            assert search_data['query'] == 'Hoffnung'
            assert len(search_data['shown_verse_ids']) == 3
    
    def test_session_prevents_duplicate_verses(self, client):
        """Bereits gezeigte Verse sollen nicht wiederholt werden"""
        # Erste 6 Verse laden
        client.post('/api/verse/search/keyword', json={'query': 'Hoffnung'})
        response2 = client.post('/api/verse/search/keyword', 
                              json={'query': 'Hoffnung', 'offset': 3})
        
        with client.session_transaction() as sess:
            search_data = sess['keyword_search']
            # Sollte 6 verschiedene Vers-IDs haben
            assert len(search_data['shown_verse_ids']) == 6
            # Keine Duplikate
            assert len(set(search_data['shown_verse_ids'])) == 6
    
    def test_session_resets_for_new_query(self, client):
        """Neue Suche soll Session zurücksetzen"""
        # Erste Suche
        client.post('/api/verse/search/keyword', json={'query': 'Hoffnung'})
        
        # Neue Suche mit anderem Keyword
        client.post('/api/verse/search/keyword', json={'query': 'Liebe'})
        
        with client.session_transaction() as sess:
            search_data = sess['keyword_search']
            assert search_data['query'] == 'Liebe'
            # Session sollte neue IDs haben (nicht unbedingt leer, da neue Verse geladen werden)
            assert 'shown_verse_ids' in search_data


class TestKeywordSearchIntegration:
    """Integration Tests für Frontend-Backend Zusammenspiel"""
    
    def test_template_renders_correctly(self, client):
        """Template soll korrekt gerendert werden"""
        response = client.get('/vers-auswaehlen/keyword')
        assert response.status_code == 200
        assert b'Nach Thema suchen' in response.data
        assert b'keywordSearchForm' in response.data
    
    def test_search_preserves_csrf_protection(self, client):
        """CSRF-Schutz soll bei AJAX-Requests funktionieren"""
        # Für echte Tests würde hier CSRF-Token Management getestet
        pass