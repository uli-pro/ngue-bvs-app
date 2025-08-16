"""
Tests for verse selection logic and adaptive featured verse algorithm.
"""

import pytest
from .test_helpers import (
    VerseFactory, ResponseParser, AssertionHelper, DatabaseHelper
)

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from models import Verse


class TestAdaptiveVerseSelection:
    """Test the get_adaptive_featured_verses method."""
    
    def test_basic_verse_selection(self, app, sample_verses):
        """Test basic selection returns 3 highest scored verses."""
        verses = Verse.get_adaptive_featured_verses(3)
        
        assert len(verses) == 3
        # Should return highest scored unsponsored verses
        scores = [v.positivity_score for v in verses]
        assert all(score >= 85 for score in scores), f"Expected high scores, got {scores}"
    
    def test_adaptive_fallback_mechanism(self, app):
        """Test fallback to lower scores when high scores unavailable."""
        # Create only low-scored verses
        low_verses = VerseFactory.create_batch(5, base_score=30)
        
        verses = Verse.get_adaptive_featured_verses(3)
        assert len(verses) == 3
        assert all(v.positivity_score >= 30 for v in verses)
    
    def test_keyword_bonus_calculation(self, app):
        """Test that positive keywords increase verse selection priority."""
        # Create verses with different keyword counts
        verse_no_keywords = VerseFactory.create(
            book='TEST', chapter=1, verse=1,
            text='This verse has no positive words.',
            positivity_score=70
        )
        
        verse_with_keywords = VerseFactory.create(
            book='TEST', chapter=1, verse=2,
            text='This verse contains Liebe, Hoffnung, Frieden and Freude.',
            positivity_score=70  # Same base score
        )
        
        verses = Verse.get_adaptive_featured_verses(3)
        
        # Verse with keywords should be selected first due to bonus
        selected_ids = [v.id for v in verses]
        assert verse_with_keywords.id in selected_ids
        
        # If both are selected, keyword verse should come first
        if verse_no_keywords.id in selected_ids:
            keyword_index = selected_ids.index(verse_with_keywords.id)
            no_keyword_index = selected_ids.index(verse_no_keywords.id)
            assert keyword_index < no_keyword_index
    
    def test_exclude_ids_functionality(self, app, sample_verses):
        """Test that excluded IDs are not returned."""
        # Get first selection
        first_verses = Verse.get_adaptive_featured_verses(3)
        first_ids = [v.id for v in first_verses]
        
        # Get second selection excluding first
        second_verses = Verse.get_adaptive_featured_verses(3, exclude_ids=first_ids)
        second_ids = [v.id for v in second_verses]
        
        # No overlap
        assert not set(first_ids).intersection(set(second_ids))
    
    def test_sponsored_verses_excluded(self, app, sample_verses):
        """Test that sponsored verses are never returned."""
        verses = Verse.get_adaptive_featured_verses(10)  # Request more than available
        
        for verse in verses:
            assert not verse.is_sponsored, f"Sponsored verse {verse.reference} was returned"
    
    def test_insufficient_verses_available(self, app):
        """Test when fewer than requested verses are available."""
        # Create only 2 unsponsored verses
        VerseFactory.create_batch(2, base_score=80)
        
        verses = Verse.get_adaptive_featured_verses(3)
        assert len(verses) == 2  # Should return what's available
    
    def test_no_verses_available(self, app):
        """Test when no unsponsored verses are available."""
        # Create only sponsored verses
        VerseFactory.create_batch(3, base_score=80, is_sponsored=True)
        
        verses = Verse.get_adaptive_featured_verses(3)
        assert len(verses) == 0


class TestVerseSelectionRoutes:
    """Test the /vers-auswaehlen route behavior."""
    
    def test_initial_verse_selection(self, client, sample_verses, session_manager):
        """Test first visit to verse selection page."""
        response = client.get('/vers-auswaehlen')
        
        assert response.status_code == 200
        verses = ResponseParser.get_verses_from_response(response)
        assert len(verses) == 3
        
        # Check session was populated
        session_data = session_manager.get_session_data()
        assert 'featured_verse_ids' in session_data
        assert 'shown_verse_ids' in session_data
        assert len(session_data['featured_verse_ids']) == 3
    
    def test_session_persistence(self, client, sample_verses, session_manager):
        """Test that same verses are shown on repeated visits."""
        # First visit
        response1 = client.get('/vers-auswaehlen')
        verses1 = ResponseParser.get_verses_from_response(response1)
        
        # Navigate away and back
        client.get('/faq')
        response2 = client.get('/vers-auswaehlen')
        verses2 = ResponseParser.get_verses_from_response(response2)
        
        # Should be identical
        AssertionHelper.assert_verses_same(verses1, verses2)
    
    def test_refresh_shows_different_verses(self, client, sample_verses, session_manager):
        """Test 'andere Verse anzeigen' functionality."""
        # First visit
        response1 = client.get('/vers-auswaehlen')
        verses1 = ResponseParser.get_verses_from_response(response1)
        
        # Refresh with parameter
        response2 = client.get('/vers-auswaehlen?refresh=true')
        verses2 = ResponseParser.get_verses_from_response(response2)
        
        # Should be different
        AssertionHelper.assert_verses_different(verses1, verses2)
    
    def test_multiple_refreshes_no_repeats(self, client, sample_verses, session_manager):
        """Test that multiple refreshes don't repeat verses until necessary."""
        seen_references = set()
        
        # Initial load
        response = client.get('/vers-auswaehlen')
        verses = ResponseParser.get_verses_from_response(response)
        for verse in verses:
            seen_references.add(verse['reference'])
        
        # Multiple refreshes
        for i in range(3):
            response = client.get('/vers-auswaehlen?refresh=true')
            verses = ResponseParser.get_verses_from_response(response)
            
            # Check for new verses (some might repeat if we've seen most)
            current_refs = {verse['reference'] for verse in verses}
            
            # At least some should be new (unless we've exhausted the pool)
            total_available = len(sample_verses) - len([v for v in sample_verses if v.is_sponsored])
            if len(seen_references) < total_available:
                assert not current_refs.issubset(seen_references), "No new verses found"
            
            seen_references.update(current_refs)
    
    def test_sponsored_verse_replacement(self, client, sample_verses, session_manager):
        """Test automatic replacement when featured verse becomes sponsored."""
        # Set specific verses in session
        verse_ids = [sample_verses[0].id, sample_verses[1].id, sample_verses[2].id]
        session_manager.set_featured_verses(verse_ids)
        
        # Sponsor one of the featured verses
        sample_verses[1].is_sponsored = True
        from models import db
        db.session.commit()
        
        # Visit page - should replace sponsored verse
        response = client.get('/vers-auswaehlen')
        verses = ResponseParser.get_verses_from_response(response)
        
        assert len(verses) == 3
        # Should not contain the sponsored verse
        verse_refs = [verse['reference'] for verse in verses]
        assert sample_verses[1].reference not in verse_refs


class TestURLSlugGeneration:
    """Test URL slug generation for verses."""
    
    def test_url_slug_property(self, app, sample_verses):
        """Test that url_slug property generates correct format."""
        verse = sample_verses[0]  # ISA 43:1
        expected_slug = 'isa-43-1'
        assert verse.url_slug == expected_slug
    
    def test_verse_links_in_template(self, client, sample_verses):
        """Test that verse links use correct URL slugs."""
        response = client.get('/vers-auswaehlen')
        verses = ResponseParser.get_verses_from_response(response)
        
        for verse_data in verses:
            url = verse_data['url']
            assert '/vers/' in url
            assert '/spendenart' in url
            
            # Extract slug
            slug = ResponseParser.extract_verse_id_from_url(url)
            assert slug is not None
            assert '-' in slug  # Should have book-chapter-verse format
    
    def test_slug_to_verse_lookup(self, app, sample_verses):
        """Test looking up verse by URL slug."""
        verse = sample_verses[0]
        slug = verse.url_slug
        
        found_verse = DatabaseHelper.get_verse_by_slug(slug)
        assert found_verse is not None
        assert found_verse.id == verse.id


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""
    
    def test_empty_database(self, client):
        """Test behavior with no verses in database."""
        response = client.get('/vers-auswaehlen')
        
        # Should not crash, might show empty state or redirect
        assert response.status_code in [200, 302]
    
    def test_all_verses_sponsored(self, client, sample_verses):
        """Test when all verses are sponsored."""
        # Sponsor all verses
        from models import db
        for verse in sample_verses:
            verse.is_sponsored = True
        db.session.commit()
        
        response = client.get('/vers-auswaehlen')
        
        # Should handle gracefully
        assert response.status_code in [200, 302]
        
        if response.status_code == 200:
            verses = ResponseParser.get_verses_from_response(response)
            assert len(verses) == 0
    
    def test_invalid_session_data(self, client, sample_verses, session_manager):
        """Test handling of corrupted session data."""
        # Set invalid verse IDs in session
        session_manager.set_featured_verses([99999, 99998, 99997])  # Non-existent IDs
        
        response = client.get('/vers-auswaehlen')
        
        # Should recover gracefully and show new verses
        assert response.status_code == 200
        verses = ResponseParser.get_verses_from_response(response)
        # Might be empty or show available verses depending on implementation
    
    def test_large_exclude_list(self, app, sample_verses):
        """Test performance with large exclude list."""
        # Create many verses
        many_verses = VerseFactory.create_batch(100, base_score=50)
        verse_ids = [v.id for v in many_verses[:90]]  # Exclude most
        
        # Should still work efficiently
        verses = Verse.get_adaptive_featured_verses(3, exclude_ids=verse_ids)
        assert len(verses) <= 3
    
    def test_refresh_with_insufficient_new_verses(self, client, session_manager):
        """Test refresh when there aren't enough new verses."""
        # Create only 4 verses total
        verses = VerseFactory.create_batch(4, base_score=80)
        
        # First visit shows 3
        response1 = client.get('/vers-auswaehlen')
        verses1 = ResponseParser.get_verses_from_response(response1)
        assert len(verses1) == 3
        
        # Refresh - should show different selection but might repeat some
        response2 = client.get('/vers-auswaehlen?refresh=true')
        verses2 = ResponseParser.get_verses_from_response(response2)
        
        # Should handle gracefully
        assert len(verses2) > 0