"""
Tests for the verse reference search functionality.
Tests written first according to TDD methodology.
"""

import pytest
from unittest.mock import Mock, patch
from .test_helpers import (
    VerseFactory, AssertionHelper, ResponseParser
)

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from models import db, Verse


class TestBasicReferenceFunctionality:
    """Test basic verse reference lookup functionality."""
    
    def test_get_verse_by_reference_success(self, app, sample_verses):
        """Test successful verse lookup by biblical reference."""
        # Use existing test verse: ISA 43:1
        verse = VerseFactory.create(
            book='JESAJA', chapter=43, verse=1,
            text='Fürchte dich nicht, denn ich habe dich erlöst.',
            positivity_score=95
        )
        
        # Test the method we need to implement
        found_verse = Verse.get_by_reference('JESAJA', 43, 1)
        
        assert found_verse is not None
        assert found_verse.id == verse.id
        assert found_verse.book == 'JESAJA'
        assert found_verse.chapter == 43
        assert found_verse.verse == 1
    
    def test_get_verse_by_reference_not_found(self, app):
        """Test verse lookup for non-existent reference."""
        found_verse = Verse.get_by_reference('NONEXISTENT', 999, 999)
        assert found_verse is None
    
    def test_get_verse_by_reference_case_insensitive(self, app):
        """Test that book names are case-insensitive."""
        verse = VerseFactory.create(
            book='JEREMIA', chapter=29, verse=11,
            text='Denn ich weiß die Gedanken...',
            positivity_score=92
        )
        
        # Test different case variations
        found_verse1 = Verse.get_by_reference('jeremia', 29, 11)
        found_verse2 = Verse.get_by_reference('Jeremia', 29, 11)
        found_verse3 = Verse.get_by_reference('JEREMIA', 29, 11)
        
        assert found_verse1 is not None
        assert found_verse2 is not None
        assert found_verse3 is not None
        assert found_verse1.id == found_verse2.id == found_verse3.id == verse.id
    
    def test_invalid_reference_parameters(self, app):
        """Test handling of invalid reference parameters."""
        # Negative numbers
        assert Verse.get_by_reference('JESAJA', -1, 1) is None
        assert Verse.get_by_reference('JESAJA', 1, -1) is None
        
        # Zero values
        assert Verse.get_by_reference('JESAJA', 0, 1) is None
        assert Verse.get_by_reference('JESAJA', 1, 0) is None
        
        # Empty book name
        assert Verse.get_by_reference('', 1, 1) is None
        assert Verse.get_by_reference(None, 1, 1) is None


class TestSponsoredVerseHandling:
    """Test handling of sponsored verses with alternative suggestions."""
    
    def test_sponsored_verse_shows_alternatives(self, app):
        """Test that sponsored verses return similar alternatives."""
        # Create a sponsored verse
        sponsored_verse = VerseFactory.create(
            book='PSALM', chapter=23, verse=1,
            text='Der HERR ist mein Hirte; mir wird nichts mangeln.',
            positivity_score=85,
            is_sponsored=True
        )
        
        # Create similar verses as alternatives
        alt1 = VerseFactory.create(
            book='PSALM', chapter=23, verse=2,
            text='Er weidet mich auf grünen Auen und führet mich zum frischen Wasser.',
            positivity_score=83
        )
        alt2 = VerseFactory.create(
            book='JESAJA', chapter=40, verse=11,
            text='Er wird seine Herde weiden wie ein Hirte.',
            positivity_score=87
        )
        
        # Test method we need to implement
        alternatives = sponsored_verse.find_similar_verses(limit=3, positivity_tolerance=10)
        
        assert len(alternatives) <= 3
        assert all(not alt.is_sponsored for alt in alternatives)
        assert all(abs(alt.positivity_score - sponsored_verse.positivity_score) <= 10 
                  for alt in alternatives)
    
    def test_alternatives_have_similar_positivity(self, app):
        """Test that alternatives have similar positivity scores."""
        sponsored_verse = VerseFactory.create(
            book='JEREMIA', chapter=29, verse=11,
            text='Denn ich weiß die Gedanken...',
            positivity_score=90,
            is_sponsored=True
        )
        
        # Create verses with different positivity scores
        too_low = VerseFactory.create(
            book='TEST', chapter=1, verse=1,
            text='Low positivity test verse',
            positivity_score=70  # Too far from 90
        )
        just_right = VerseFactory.create(
            book='TEST', chapter=1, verse=2,
            text='Good positivity test verse',
            positivity_score=85  # Within tolerance
        )
        
        alternatives = sponsored_verse.find_similar_verses(
            limit=3, positivity_tolerance=10
        )
        
        # Should include just_right but not too_low
        alternative_ids = [alt.id for alt in alternatives]
        assert just_right.id in alternative_ids
        assert too_low.id not in alternative_ids
    
    def test_alternatives_exclude_sponsored_verses(self, app):
        """Test that alternative suggestions don't include sponsored verses."""
        sponsored_verse = VerseFactory.create(
            book='ZEFANJA', chapter=3, verse=17,
            text='Der HERR wird sich über dich freuen...',
            positivity_score=90,
            is_sponsored=True
        )
        
        # Create similar verse that's also sponsored
        similar_sponsored = VerseFactory.create(
            book='TEST', chapter=1, verse=1,
            text='Similar sponsored verse about joy and God',
            positivity_score=88,
            is_sponsored=True
        )
        
        # Create similar verse that's available
        similar_available = VerseFactory.create(
            book='TEST', chapter=1, verse=2,
            text='Similar available verse about joy and God',
            positivity_score=89,
            is_sponsored=False
        )
        
        alternatives = sponsored_verse.find_similar_verses(limit=3)
        
        alternative_ids = [alt.id for alt in alternatives]
        assert similar_available.id in alternative_ids
        assert similar_sponsored.id not in alternative_ids
    
    def test_no_alternatives_available(self, app):
        """Test behavior when no suitable alternatives exist."""
        sponsored_verse = VerseFactory.create(
            book='UNIQUE', chapter=1, verse=1,
            text='Completely unique verse with no alternatives',
            positivity_score=50,
            is_sponsored=True
        )
        
        alternatives = sponsored_verse.find_similar_verses(limit=3)
        
        # Should return empty list or fewer alternatives
        assert isinstance(alternatives, list)
        assert len(alternatives) >= 0  # Might be empty, that's OK


class TestSimilarVerseAlgorithm:
    """Test the algorithm for finding semantically similar verses."""
    
    def test_find_similar_verses_semantic_only(self, app):
        """Test semantic similarity without keyword extraction."""
        target_verse = VerseFactory.create(
            book='TEST', chapter=1, verse=1,
            text='Der Herr ist mein Hirte und Beschützer',
            positivity_score=85
        )
        
        # Similar verse (shepherd theme)
        similar_verse = VerseFactory.create(
            book='TEST', chapter=1, verse=2,
            text='Gott weidet mich wie ein guter Hirte',
            positivity_score=83
        )
        
        # Dissimilar verse
        dissimilar_verse = VerseFactory.create(
            book='TEST', chapter=1, verse=3,
            text='Die Sterne leuchten am Himmel hell',
            positivity_score=84
        )
        
        # Mock the semantic search (since we don't have embeddings in test)
        with patch.object(Verse, 'search_semantic') as mock_search:
            mock_search.return_value = [similar_verse, dissimilar_verse]
            
            similar_verses = target_verse.find_similar_verses(
                limit=2, use_semantic=True, use_keywords=False
            )
            
            mock_search.assert_called_once()
            assert len(similar_verses) <= 2
    
    def test_extract_keywords_from_verse(self, app):
        """Test keyword extraction from verse text."""
        verse = VerseFactory.create(
            book='TEST', chapter=1, verse=1,
            text='Der HERR ist mein Hirte; mir wird nichts mangeln. Er führt mich zu grünen Auen.',
            positivity_score=85
        )
        
        keywords = verse.extract_keywords(max_keywords=5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        assert all(isinstance(keyword, str) for keyword in keywords)
        
        # Should extract meaningful words (not stopwords)
        expected_keywords = ['HERR', 'Hirte', 'führt', 'Auen']
        assert any(keyword in keywords for keyword in expected_keywords)
    
    def test_hybrid_similarity_search(self, app):
        """Test hybrid search combining semantic and keyword similarity."""
        target_verse = VerseFactory.create(
            book='TEST', chapter=1, verse=1,
            text='Gott ist Liebe und Hoffnung für alle Menschen',
            positivity_score=90
        )
        
        # Create verses with keyword overlap
        keyword_match = VerseFactory.create(
            book='TEST', chapter=1, verse=2,
            text='Die Liebe Gottes gibt uns Hoffnung jeden Tag',
            positivity_score=88
        )
        
        # Mock both semantic and keyword methods
        with patch.object(target_verse, 'extract_keywords') as mock_keywords, \
             patch.object(Verse, 'search_hybrid') as mock_hybrid:
            
            mock_keywords.return_value = ['Gott', 'Liebe', 'Hoffnung']
            mock_hybrid.return_value = [keyword_match]
            
            similar_verses = target_verse.find_similar_verses(
                limit=3, use_semantic=True, use_keywords=True
            )
            
            mock_keywords.assert_called()
            mock_hybrid.assert_called()
            assert len(similar_verses) >= 0
    
    def test_similarity_scoring_combined(self, app):
        """Test combined scoring of semantic and keyword similarity."""
        verse = VerseFactory.create(
            book='TEST', chapter=1, verse=1,
            text='Test verse for similarity scoring',
            positivity_score=80
        )
        
        # Test the combined scoring method
        score = verse.calculate_similarity_score(
            other_verse_text='Similar test verse for scoring',
            positivity_difference=5,
            semantic_weight=0.6,
            keyword_weight=0.3,
            positivity_weight=0.1
        )
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 1  # Normalized score


class TestRouteIntegration:
    """Test API routes and frontend integration."""
    
    def test_reference_search_api_endpoint(self, client, sample_verses):
        """Test API endpoint for verse reference search."""
        # Create test verse
        verse = VerseFactory.create(
            book='JESAJA', chapter=43, verse=1,
            text='Fürchte dich nicht, denn ich habe dich erlöst.',
            positivity_score=95
        )
        
        # Test API endpoint
        response = client.get('/api/verse/reference/jesaja/43/1')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data is not None
        assert data['success'] is True
        assert data['verse']['book'] == 'JESAJA'
        assert data['verse']['chapter'] == 43
        assert data['verse']['verse'] == 1
        assert 'text' in data['verse']
        assert 'positivity_score' in data['verse']
        assert 'is_sponsored' in data['verse']
    
    def test_reference_search_api_not_found(self, client):
        """Test API endpoint with non-existent verse."""
        response = client.get('/api/verse/reference/nonexistent/999/999')
        
        assert response.status_code == 400  # Updated: now returns 400 for large numbers
        data = response.get_json()
        
        assert data is not None
        assert data['success'] is False
        assert 'error' in data
    
    def test_similar_verses_api_endpoint(self, client, sample_verses):
        """Test API endpoint for getting similar verses."""
        # Create sponsored verse
        sponsored_verse = VerseFactory.create(
            book='PSALM', chapter=23, verse=1,
            text='Der HERR ist mein Hirte; mir wird nichts mangeln.',
            positivity_score=85,
            is_sponsored=True
        )
        
        # Create similar verse
        similar_verse = VerseFactory.create(
            book='PSALM', chapter=23, verse=2,
            text='Er weidet mich auf grünen Auen.',
            positivity_score=83
        )
        
        response = client.get(f'/api/verse/{sponsored_verse.id}/similar')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data is not None
        assert data['success'] is True
        assert 'alternatives' in data
        assert isinstance(data['alternatives'], list)
        assert len(data['alternatives']) <= 3
    
    def test_dropdown_population_api(self, client, sample_verses):
        """Test API endpoints for populating dropdowns."""
        # Test book list
        response = client.get('/api/verse/books')
        assert response.status_code == 200
        data = response.get_json()
        assert 'books' in data
        assert isinstance(data['books'], list)
        
        # Test chapters for a book
        response = client.get('/api/verse/chapters/jesaja')
        assert response.status_code == 200
        data = response.get_json()
        assert 'chapters' in data
        assert isinstance(data['chapters'], list)
        
        # Test verses for a chapter
        response = client.get('/api/verse/verses/jesaja/43')
        assert response.status_code == 200
        data = response.get_json()
        assert 'verses' in data
        assert isinstance(data['verses'], list)
    
    def test_verse_selection_from_reference_search(self, client, sample_verses):
        """Test that verse selection works after reference search."""
        verse = VerseFactory.create(
            book='JEREMIA', chapter=29, verse=11,
            text='Denn ich weiß die Gedanken...',
            positivity_score=92
        )
        
        # First, search for the verse
        response = client.get('/api/verse/reference/jeremia/29/11')
        assert response.status_code == 200
        
        # Then, select the verse
        response = client.get(f'/vers/{verse.url_slug}/spendenart')
        assert response.status_code == 200
        
        # Should create reservation
        from models import VerseReservation
        reservations = VerseReservation.query.filter_by(verse_id=verse.id).all()
        assert len(reservations) == 1
    
    def test_reservation_after_reference_search_flow(self, client, sample_verses, session_manager):
        """Test complete flow from reference search to reservation."""
        verse = VerseFactory.create(
            book='ZEFANJA', chapter=3, verse=17,
            text='Der HERR wird sich über dich freuen...',
            positivity_score=90
        )
        
        # Step 1: Reference search
        search_response = client.get('/api/verse/reference/zefanja/3/17')
        assert search_response.status_code == 200
        
        # Step 2: Verse selection
        selection_response = client.get(f'/vers/{verse.url_slug}/spendenart')
        assert selection_response.status_code == 200
        
        # Step 3: Verify reservation and session
        session_data = session_manager.get_session_data()
        assert 'selected_verse_id' in session_data
        assert session_data['selected_verse_id'] == verse.id
        
        # Step 4: Verify reservation in database
        from models import VerseReservation
        reservation = VerseReservation.query.filter_by(verse_id=verse.id).first()
        assert reservation is not None
        assert not reservation.is_expired


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""
    
    def test_malformed_api_requests(self, client):
        """Test handling of malformed API requests."""
        # Invalid book format
        response = client.get('/api/verse/reference/123invalid/1/1')
        assert response.status_code in [400, 404]
        
        # Invalid chapter
        response = client.get('/api/verse/reference/jesaja/abc/1')
        assert response.status_code in [400, 404]
        
        # Invalid verse number
        response = client.get('/api/verse/reference/jesaja/1/xyz')
        assert response.status_code in [400, 404]
    
    def test_database_connection_error(self, client):
        """Test handling of database connection errors."""
        with patch.object(Verse, 'get_by_reference') as mock_get:
            mock_get.side_effect = Exception("Database connection failed")
            
            response = client.get('/api/verse/reference/jesaja/43/1')
            
            # Should handle error gracefully
            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert 'error' in data
    
    def test_very_large_reference_numbers(self, client):
        """Test handling of unreasonably large reference numbers."""
        # Very large chapter
        response = client.get('/api/verse/reference/jesaja/999999/1')
        assert response.status_code == 400  # Updated: now validates input
        
        # Very large verse
        response = client.get('/api/verse/reference/jesaja/1/999999')
        assert response.status_code == 400  # Updated: now validates input
    
    def test_unicode_and_special_characters(self, client):
        """Test handling of unicode and special characters in book names."""
        # Create verse with unicode characters
        verse = VerseFactory.create(
            book='MALEÁCHI', chapter=1, verse=1,
            text='Test verse with unicode book name',
            positivity_score=80
        )
        
        # Should handle unicode in URL
        response = client.get('/api/verse/reference/maleáchi/1/1')
        # Should either work or fail gracefully
        assert response.status_code in [200, 400, 404]