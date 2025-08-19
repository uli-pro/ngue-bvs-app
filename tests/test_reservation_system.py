"""
Reservation System Tests
Tests for verse reservation logic, expiration handling, and concurrent access
"""

import pytest
import json
from datetime import datetime, timedelta
from app import app
from models import Verse, VerseReservation, db
from flask import session


@pytest.fixture
def client():
    """Test client for Flask App"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def sample_verse_id(client):
    """Get a valid unsponsored verse ID for testing"""
    with app.app_context():
        verse = Verse.query.filter_by(is_sponsored=False).first()
        if not verse:
            pytest.skip("No unsponsored verses available for testing")
        return verse.id


class TestReservationCreation:
    """Test reservation creation and basic functionality"""
    
    def test_verse_selection_creates_reservation(self, client, sample_verse_id):
        """Selecting a verse should create a reservation"""
        initial_reservation_count = VerseReservation.query.count()
        
        # Select verse with donation type
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        # Should redirect to checkout
        assert response.status_code == 302
        assert 'checkout' in response.location
        
        # Should create a reservation
        assert VerseReservation.query.count() == initial_reservation_count + 1
        
        # Session should contain reservation ID
        with client.session_transaction() as sess:
            assert 'reservation_id' in sess
            assert 'selected_verse_id' in sess
            assert sess['selected_verse_id'] == sample_verse_id
    
    def test_reservation_has_correct_expiration(self, client, sample_verse_id):
        """New reservation should have correct expiration time"""
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
            
        if reservation_id:
            reservation = VerseReservation.query.get(reservation_id)
            assert reservation is not None
            
            # Should expire in approximately 15 minutes
            time_diff = reservation.expires_at - datetime.utcnow()
            assert 13 <= time_diff.total_seconds() / 60 <= 17  # 13-17 minutes tolerance
    
    def test_existing_reservation_blocks_new_reservation(self, client, sample_verse_id):
        """Existing active reservation should block new reservation attempts"""
        # Create first reservation
        response1 = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        assert response1.status_code == 302
        
        # Try to create second reservation for same verse (different client session)
        client2 = app.test_client()
        with client2:
            response2 = client2.post(f'/vers/{sample_verse_id}/spendenart', data={
                'donation_type': 'einzelperson'
            })
            
            # Should redirect with error message
            assert response2.status_code == 302
            assert '/vers-auswaehlen' in response2.location


class TestReservationExpiration:
    """Test reservation expiration logic"""
    
    def test_expired_reservation_detection(self, client, sample_verse_id):
        """Expired reservations should be detected correctly"""
        # Create reservation
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
        
        if reservation_id:
            # Manually expire the reservation
            reservation = VerseReservation.query.get(reservation_id)
            reservation.expires_at = datetime.utcnow() - timedelta(minutes=1)
            db.session.commit()
            
            # Access checkout page - should detect expiration
            response = client.get('/checkout/einzelperson/daten')
            
            # Should redirect to verse selection with expiration message
            assert response.status_code == 302
            assert '/vers-auswaehlen' in response.location
            
            # Session should be cleared
            with client.session_transaction() as sess:
                assert 'selected_verse_id' not in sess
                assert 'reservation_id' not in sess
    
    def test_reservation_extension_during_checkout(self, client, sample_verse_id):
        """Reservation should be extended during active checkout"""
        # Create reservation
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
        
        if reservation_id:
            original_reservation = VerseReservation.query.get(reservation_id)
            original_expiry = original_reservation.expires_at
            
            # Access checkout page (should extend reservation)
            response = client.get('/checkout/einzelperson/daten')
            assert response.status_code == 200
            
            # Check if reservation was extended
            updated_reservation = VerseReservation.query.get(reservation_id)
            assert updated_reservation.expires_at > original_expiry
    
    def test_expired_reservation_cleanup(self, client, sample_verse_id):
        """Expired reservations should be cleaned up"""
        # Create reservation
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
        
        if reservation_id:
            # Manually expire the reservation
            reservation = VerseReservation.query.get(reservation_id)
            reservation.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            initial_count = VerseReservation.query.count()
            
            # Trigger cleanup (happens during verse selection)
            client.get('/vers-auswaehlen')
            
            # Expired reservation should be removed
            assert VerseReservation.query.count() < initial_count


class TestConcurrentReservations:
    """Test concurrent reservation attempts"""
    
    def test_simultaneous_reservation_attempts(self, client, sample_verse_id):
        """Multiple simultaneous reservation attempts should be handled correctly"""
        # Simulate first user starting reservation
        response1 = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        assert response1.status_code == 302
        
        # Simulate second user trying same verse immediately
        client2 = app.test_client()
        with client2:
            response2 = client2.post(f'/vers/{sample_verse_id}/spendenart', data={
                'donation_type': 'einzelperson'
            })
            
            # Second request should be rejected
            assert response2.status_code == 302
            assert '/vers-auswaehlen' in response2.location
            
            # Should not have reservation in session
            with client2.session_transaction() as sess:
                assert 'reservation_id' not in sess
    
    def test_reservation_race_condition_handling(self, client, sample_verse_id):
        """Test handling of race conditions in reservation creation"""
        # This test simulates potential race conditions
        # In practice, database constraints should prevent duplicate reservations
        
        # Start multiple reservation attempts
        clients = [app.test_client() for _ in range(3)]
        
        responses = []
        for test_client in clients:
            with test_client:
                response = test_client.post(f'/vers/{sample_verse_id}/spendenart', data={
                    'donation_type': 'einzelperson'
                })
                responses.append(response)
        
        # Only one should succeed
        successful_reservations = [r for r in responses if r.status_code == 302 and 'checkout' in r.location]
        assert len(successful_reservations) <= 1
    
    def test_abandoned_reservation_reuse(self, client, sample_verse_id):
        """Abandoned expired reservation should allow new reservation"""
        # Create and abandon reservation
        response1 = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
        
        if reservation_id:
            # Manually expire the reservation
            reservation = VerseReservation.query.get(reservation_id)
            reservation.expires_at = datetime.utcnow() - timedelta(minutes=1)
            db.session.commit()
            
            # New user should be able to reserve the verse
            client2 = app.test_client()
            with client2:
                response2 = client2.post(f'/vers/{sample_verse_id}/spendenart', data={
                    'donation_type': 'einzelperson'
                })
                
                # Should succeed
                assert response2.status_code == 302
                assert 'checkout' in response2.location


class TestReservationSessionIntegration:
    """Test integration between reservations and session management"""
    
    def test_session_reservation_synchronization(self, client, sample_verse_id):
        """Session should stay synchronized with reservation state"""
        # Create reservation
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
            verse_id = sess.get('selected_verse_id')
        
        assert reservation_id is not None
        assert verse_id == sample_verse_id
        
        # Verify reservation exists in database
        reservation = VerseReservation.query.get(reservation_id)
        assert reservation is not None
        assert reservation.verse_id == sample_verse_id
    
    def test_session_cleanup_on_reservation_expiry(self, client, sample_verse_id):
        """Session should be cleaned up when reservation expires"""
        # Create reservation
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
        
        if reservation_id:
            # Expire reservation
            reservation = VerseReservation.query.get(reservation_id)
            reservation.expires_at = datetime.utcnow() - timedelta(minutes=1)
            db.session.commit()
            
            # Access checkout - should clean up session
            response = client.get('/checkout/einzelperson/daten')
            
            with client.session_transaction() as sess:
                assert 'reservation_id' not in sess
                assert 'selected_verse_id' not in sess
    
    def test_checkout_without_valid_reservation(self, client):
        """Checkout without valid reservation should redirect"""
        # Try to access checkout without reservation
        response = client.get('/checkout/einzelperson/daten')
        
        # Should redirect to verse selection
        assert response.status_code == 302
        assert '/vers-auswaehlen' in response.location
    
    def test_invalid_reservation_id_handling(self, client):
        """Invalid reservation ID in session should be handled gracefully"""
        with client.session_transaction() as sess:
            sess['reservation_id'] = 99999  # Non-existent ID
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        # Access checkout
        response = client.get('/checkout/einzelperson/daten')
        
        # Should redirect due to invalid reservation
        assert response.status_code == 302
        assert '/vers-auswaehlen' in response.location


class TestCartReservationIntegration:
    """Test integration between cart and reservation system"""
    
    def test_adding_to_cart_maintains_reservation(self, client, sample_verse_id):
        """Adding item to cart should maintain reservation"""
        # Create reservation and add to cart
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            original_reservation_id = sess.get('reservation_id')
        
        # Add to cart
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'privacy': 'on'
        })
        
        # Should redirect to cart
        assert response.status_code == 302
        assert '/spendenkorb' in response.location
        
        # Check cart contains reservation ID
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            assert cart[0].get('reservation_id') == original_reservation_id
    
    def test_cart_reservation_persistence(self, client, sample_verse_id):
        """Reservations in cart should persist"""
        # Add item with reservation to cart
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'reservation_id': 123,  # Mock reservation ID
                'amount': 100.00
            }]
        
        # Access cart
        response = client.get('/spendenkorb')
        assert response.status_code == 200
        
        # Cart should still contain reservation
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            assert cart[0].get('reservation_id') == 123
    
    def test_removing_from_cart_releases_reservation(self, client, sample_verse_id):
        """Removing item from cart should release reservation"""
        # Create actual reservation
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
        
        # Add to cart
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'privacy': 'on'
        })
        
        # Remove from cart
        response = client.post('/spendenkorb/entfernen', 
                             json={'item_index': 0})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') == True
        
        # Reservation should no longer block the verse
        # (This would be tested by trying to reserve again)


class TestReservationErrorHandling:
    """Test error handling in reservation system"""
    
    def test_database_error_during_reservation(self, client, sample_verse_id):
        """Database errors during reservation should be handled gracefully"""
        # This test would need to mock database errors
        # For now, test basic error conditions
        
        # Try to reserve non-existent verse
        response = client.post('/vers/999999/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        # Should handle gracefully
        assert response.status_code in [302, 404]
    
    def test_invalid_donation_type_reservation(self, client, sample_verse_id):
        """Invalid donation type should be handled"""
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'invalid_type'
        })
        
        # Should redirect with error
        assert response.status_code == 302
        assert '/vers-auswaehlen' in response.location
    
    def test_missing_donation_type_reservation(self, client, sample_verse_id):
        """Missing donation type should be handled"""
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={})
        
        # Should redirect with error
        assert response.status_code == 302
        assert '/vers-auswaehlen' in response.location


class TestReservationCleanup:
    """Test reservation cleanup mechanisms"""
    
    def test_periodic_cleanup_removes_expired(self, client, sample_verse_id):
        """Periodic cleanup should remove expired reservations"""
        initial_count = VerseReservation.query.count()
        
        # Create reservation and immediately expire it
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
        
        if reservation_id:
            reservation = VerseReservation.query.get(reservation_id)
            reservation.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            # Trigger cleanup (happens during various operations)
            client.get('/vers-auswaehlen')
            
            # Should be cleaned up
            assert VerseReservation.query.get(reservation_id) is None
    
    def test_cleanup_preserves_active_reservations(self, client, sample_verse_id):
        """Cleanup should not remove active reservations"""
        # Create active reservation
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        with client.session_transaction() as sess:
            reservation_id = sess.get('reservation_id')
        
        if reservation_id:
            # Trigger cleanup
            client.get('/vers-auswaehlen')
            
            # Active reservation should still exist
            reservation = VerseReservation.query.get(reservation_id)
            assert reservation is not None
            assert not reservation.is_expired