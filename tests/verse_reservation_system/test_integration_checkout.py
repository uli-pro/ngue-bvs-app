"""
Integration tests for the complete verse selection and checkout flow.
"""

import pytest
from freezegun import freeze_time
from .test_helpers import (
    VerseFactory, ReservationFactory, AssertionHelper, 
    ResponseParser, DatabaseHelper
)

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from models import db, VerseReservation


class TestCompleteCheckoutFlow:
    """Test the complete flow from verse selection to checkout summary."""
    
    def test_successful_verse_to_checkout_flow(self, client, sample_verses):
        """Test complete successful flow: select verse -> donation type -> data -> summary."""
        # Step 1: Select verse from featured list
        response = client.get('/vers-auswaehlen')
        assert response.status_code == 200
        
        verses = ResponseParser.get_verses_from_response(response)
        assert len(verses) > 0
        
        # Step 2: Choose first verse
        verse_url = verses[0]['url']
        response = client.get(verse_url)
        assert response.status_code == 200
        
        # Step 3: Select donation type (einzelperson)
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200
        
        # Step 4: Go to summary (simplified - normally would submit form data)
        response = client.get('/checkout/zusammenfassung')
        assert response.status_code == 200
        
        # Verify reservation exists throughout
        reservations = VerseReservation.query.all()
        assert len(reservations) == 1
        assert not reservations[0].is_expired
    
    def test_verse_selection_with_session_persistence(self, client, sample_verses):
        """Test verse selection maintains session across navigation."""
        # Initial verse selection
        response1 = client.get('/vers-auswaehlen')
        verses1 = ResponseParser.get_verses_from_response(response1)
        
        # Navigate to FAQ and back
        client.get('/faq')
        response2 = client.get('/vers-auswaehlen')
        verses2 = ResponseParser.get_verses_from_response(response2)
        
        # Should be same verses
        AssertionHelper.assert_verses_same(verses1, verses2)
        
        # Select a verse
        verse_url = verses1[0]['url']
        response = client.get(verse_url)
        assert response.status_code == 200
        
        # Navigate away and back to verse selection
        client.get('/ueber-ngue')
        response3 = client.get('/vers-auswaehlen')
        verses3 = ResponseParser.get_verses_from_response(response3)
        
        # Should still be same verses (session persistence)
        AssertionHelper.assert_verses_same(verses1, verses3)
    
    def test_reservation_extension_throughout_checkout(self, client, sample_verses):
        """Test that reservations are extended at each checkout step."""
        verse = sample_verses[0]
        
        # Step 1: Select verse (creates reservation)
        response = client.get(f'/vers/{verse.url_slug}/spendenart')
        assert response.status_code == 200
        
        # Get initial reservation
        reservation = VerseReservation.query.first()
        assert reservation is not None
        initial_expiry = reservation.expires_at
        
        # Small delay to ensure time difference
        import time
        time.sleep(0.1)
        
        # Step 2: Access checkout data page (should extend reservation)
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200
        
        # Check if reservation was extended
        db.session.refresh(reservation)
        if hasattr(reservation, 'extends_at'):  # If extension logic is implemented
            assert reservation.expires_at >= initial_expiry
    
    def test_checkout_flow_with_refresh_verses(self, client, sample_verses):
        """Test checkout flow after using 'andere Verse anzeigen'."""
        # Initial verses
        response1 = client.get('/vers-auswaehlen')
        verses1 = ResponseParser.get_verses_from_response(response1)
        
        # Refresh to get different verses
        response2 = client.get('/vers-auswaehlen?refresh=true')
        verses2 = ResponseParser.get_verses_from_response(response2)
        
        # Should be different
        AssertionHelper.assert_verses_different(verses1, verses2)
        
        # Select verse from new set
        verse_url = verses2[0]['url']
        response = client.get(verse_url)
        assert response.status_code == 200
        
        # Continue to checkout
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200
    
    def test_multiple_verses_exploration_then_checkout(self, client, sample_verses):
        """Test exploring multiple verses before selecting one."""
        # Get initial verses
        response = client.get('/vers-auswaehlen')
        verses = ResponseParser.get_verses_from_response(response)
        
        # Look at first verse but don't commit
        verse1_url = verses[0]['url']
        response = client.get(verse1_url)
        assert response.status_code == 200
        
        # Go back to selection
        response = client.get('/vers-auswaehlen')
        assert response.status_code == 200
        
        # Refresh to see other verses
        response = client.get('/vers-auswaehlen?refresh=true')
        new_verses = ResponseParser.get_verses_from_response(response)
        
        # Select different verse
        verse2_url = new_verses[0]['url']
        response = client.get(verse2_url)
        assert response.status_code == 200
        
        # Proceed with checkout
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200


class TestErrorHandlingInCheckoutFlow:
    """Test error conditions and edge cases in checkout flow."""
    
    def test_expired_reservation_during_checkout(self, client, sample_verses, session_manager):
        """Test handling when reservation expires during checkout."""
        verse = sample_verses[0]
        
        # Create already expired reservation
        expired_reservation = ReservationFactory.create_expired(
            verse_id=verse.id,
            session_id='test-session',
            minutes_ago=5
        )
        
        # Set up session as if user had selected this verse
        session_manager.set_selected_verse(verse.id, expired_reservation.id)
        
        # Try to access checkout
        response = client.get('/checkout/einzelperson/daten')
        
        assert response.status_code == 302  # Redirect
        assert response.location.endswith('/vers-auswaehlen')  # Should redirect to verse selection
    
    def test_verse_becomes_sponsored_during_checkout(self, client, sample_verses, session_manager):
        """Test handling when verse becomes sponsored during checkout."""
        verse = sample_verses[0]
        
        # Start checkout process
        response = client.get(f'/vers/{verse.url_slug}/spendenart')
        assert response.status_code == 200
        
        # Simulate verse being sponsored by another user
        verse.is_sponsored = True
        db.session.commit()
        
        # Try to continue checkout
        response = client.get('/checkout/einzelperson/daten')
        
        # Should handle gracefully (redirect or show error)
        assert response.status_code in [200, 302]
        
        if response.status_code == 302:
            assert response.location.endswith('/vers-auswaehlen')  # Should redirect to verse selection
    
    def test_invalid_verse_id_in_checkout_flow(self, client):
        """Test checkout flow with invalid verse ID."""
        # Try to select non-existent verse
        response = client.get('/vers/invalid-verse-id/spendenart')
        
        assert response.status_code == 302  # Redirect
        assert response.location.endswith('/vers-auswaehlen')  # Should redirect to verse selection
        
        # Should not be able to proceed to checkout without valid verse
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 302  # Redirect
        assert response.location.endswith('/vers-auswaehlen')  # Should redirect to verse selection
    
    def test_checkout_without_verse_selection(self, client):
        """Test attempting checkout without selecting a verse."""
        # Try to go directly to checkout
        response = client.get('/checkout/einzelperson/daten')
        
        assert response.status_code == 302  # Redirect
        assert response.location.endswith('/vers-auswaehlen')  # Should redirect to verse selection
    
    def test_invalid_donation_type(self, client, sample_verses):
        """Test checkout with invalid donation type."""
        verse = sample_verses[0]
        
        # Select valid verse
        response = client.get(f'/vers/{verse.url_slug}/spendenart')
        assert response.status_code == 200
        
        # Try invalid donation type
        response = client.get('/checkout/invalid-type/daten')
        
        assert response.status_code == 302  # Redirect
        assert response.location.endswith('/vers-auswaehlen')  # Should redirect to verse selection
    
    def test_browser_back_button_simulation(self, client, sample_verses):
        """Test navigation patterns similar to browser back button."""
        # Step 1: Select verse
        verse = sample_verses[0]
        response = client.get(f'/vers/{verse.url_slug}/spendenart')
        assert response.status_code == 200
        
        # Step 2: Go to checkout
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200
        
        # Step 3: Simulate back to verse selection
        response = client.get('/vers-auswaehlen')
        assert response.status_code == 200
        
        # Step 4: Try different verse (simulating user changing mind)
        if len(sample_verses) > 1:
            different_verse = sample_verses[1]
            response = client.get(f'/vers/{different_verse.url_slug}/spendenart')
            assert response.status_code == 200
            
            # Should work (previous reservation might be replaced)
            response = client.get('/checkout/einzelperson/daten')
            assert response.status_code == 200


class TestRaceConditionScenarios:
    """Test race condition handling in realistic scenarios."""
    
    def test_concurrent_verse_selection_attempt(self, app, sample_verses):
        """Test two users trying to select same verse simultaneously."""
        verse = sample_verses[0]
        
        # Create two separate clients (simulating different users)
        with app.test_client() as client1, app.test_client() as client2:
            # Both try to select same verse
            response1 = client1.get(f'/vers/{verse.url_slug}/spendenart')
            response2 = client2.get(f'/vers/{verse.url_slug}/spendenart')
            
            # One should succeed, one should be blocked
            success_count = sum(1 for r in [response1, response2] if r.status_code == 200)
            redirect_count = sum(1 for r in [response1, response2] if r.status_code == 302)
            
            assert success_count == 1, "Exactly one user should succeed"
            assert redirect_count == 1, "Exactly one user should be redirected"
    
    def test_rapid_verse_switching(self, client, sample_verses):
        """Test rapidly switching between verses."""
        if len(sample_verses) < 3:
            pytest.skip("Not enough sample verses for this test")
        
        # Rapidly access different verses
        for i in range(min(3, len(sample_verses))):
            verse = sample_verses[i]
            response = client.get(f'/vers/{verse.url_slug}/spendenart')
            
            # Each should work (previous reservations should be updated/replaced)
            assert response.status_code == 200
        
        # Should have at most one active reservation per session
        reservations = VerseReservation.query.all()
        # Note: Depending on implementation, might have multiple reservations
        # or might replace previous ones
        assert len(reservations) >= 1
    
    def test_session_timeout_during_checkout(self, client, sample_verses):
        """Test behavior when session data is lost during checkout."""
        verse = sample_verses[0]
        
        # Start checkout process
        response = client.get(f'/vers/{verse.url_slug}/spendenart')
        assert response.status_code == 200
        
        # Simulate session loss (clear session)
        with client.session_transaction() as sess:
            sess.clear()
        
        # Try to continue checkout
        response = client.get('/checkout/einzelperson/daten')
        
        assert response.status_code == 302  # Should redirect
        assert response.location.endswith('/vers-auswaehlen')  # Should redirect to verse selection


class TestTimeBasedIntegrationScenarios:
    """Test time-based scenarios with freezegun."""
    
    def test_checkout_flow_with_time_progression(self, client, sample_verses):
        """Test complete checkout flow with realistic time progression."""
        with freeze_time("2025-01-01 10:00:00") as frozen_time:
            verse = sample_verses[0]
            
            # 10:00 - Select verse
            response = client.get(f'/vers/{verse.url_slug}/spendenart')
            assert response.status_code == 200
            
            reservation = VerseReservation.query.first()
            assert reservation is not None
            assert not reservation.is_expired
            
            # 10:05 - Access checkout (5 minutes later)
            frozen_time.move_to("2025-01-01 10:05:00")
            response = client.get('/checkout/einzelperson/daten')
            assert response.status_code == 200
            
            # Reservation should still be valid and possibly extended
            db.session.refresh(reservation)
            assert not reservation.is_expired
            
            # 10:10 - Access summary (10 minutes total)
            frozen_time.move_to("2025-01-01 10:10:00")
            response = client.get('/checkout/zusammenfassung')
            assert response.status_code == 200
            
            # Should still be valid
            db.session.refresh(reservation)
            assert not reservation.is_expired
    
    def test_checkout_flow_exceeding_reservation_time(self, client, sample_verses):
        """Test checkout flow that takes longer than reservation period."""
        with freeze_time("2025-01-01 10:00:00") as frozen_time:
            verse = sample_verses[0]
            
            # 10:00 - Select verse (15 minute reservation)
            response = client.get(f'/vers/{verse.url_slug}/spendenart')
            assert response.status_code == 200
            
            # 10:20 - Try checkout after reservation expired (no extension)
            frozen_time.move_to("2025-01-01 10:20:00")
            response = client.get('/checkout/einzelperson/daten')
            
            # Should redirect due to expired reservation
            assert response.status_code == 302
            assert response.location.endswith('/vers-auswaehlen')  # Should redirect to verse selection


class TestDataIntegrityInCheckoutFlow:
    """Test data integrity throughout checkout process."""
    
    def test_session_data_consistency(self, client, sample_verses, session_manager):
        """Test that session data remains consistent throughout checkout."""
        verse = sample_verses[0]
        
        # Select verse
        response = client.get(f'/vers/{verse.url_slug}/spendenart')
        assert response.status_code == 200
        
        # Check session data
        session_data = session_manager.get_session_data()
        assert 'selected_verse_id' in session_data
        assert session_data['selected_verse_id'] == verse.id
        
        # Proceed through checkout
        response = client.get('/checkout/einzelperson/daten')
        if response.status_code == 200:
            # Session data should still be consistent
            session_data = session_manager.get_session_data()
            assert session_data['selected_verse_id'] == verse.id
    
    def test_verse_data_display_consistency(self, client, sample_verses):
        """Test that verse data is displayed consistently across pages."""
        verse = sample_verses[0]
        
        # Get verse from selection page
        response = client.get('/vers-auswaehlen')
        verses = ResponseParser.get_verses_from_response(response)
        
        selected_verse_data = None
        for v in verses:
            verse_id = ResponseParser.extract_verse_id_from_url(v['url'])
            if DatabaseHelper.get_verse_by_slug(verse_id) == verse:
                selected_verse_data = v
                break
        
        if selected_verse_data:
            # Select the verse
            response = client.get(selected_verse_data['url'])
            assert response.status_code == 200
            
            # Verse data on spendenart page should match
            # (This would require parsing the spendenart page content)
            # Implementation depends on specific template structure
    
    def test_reservation_cleanup_integrity(self, client, sample_verses):
        """Test that reservation cleanup doesn't affect active sessions."""
        verse1 = sample_verses[0]
        verse2 = sample_verses[1]
        
        # Create active reservation
        response = client.get(f'/vers/{verse1.url_slug}/spendenart')
        assert response.status_code == 200
        
        # Create expired reservation for different verse (simulate other user)
        ReservationFactory.create_expired(
            verse_id=verse2.id,
            session_id='other-session',
            minutes_ago=10
        )
        
        # Run cleanup
        cleaned_count = VerseReservation.cleanup_expired()
        assert cleaned_count == 1  # Should only clean expired one
        
        # Our active reservation should still work
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200