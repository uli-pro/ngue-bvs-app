"""
Edge Cases and Boundary Tests for Cart System
Tests for boundary conditions, empty states, and unusual scenarios
"""

import pytest
import json
from app import app
from models import Verse
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
    """Get a valid verse ID for testing"""
    with app.app_context():
        verse = Verse.query.filter_by(is_sponsored=False).first()
        if not verse:
            pytest.skip("No unsponsored verses available for testing")
        return verse.id


class TestEmptyCartHandling:
    """Test behavior with empty cart states"""
    
    def test_empty_cart_display(self, client):
        """Empty cart should redirect to verse selection"""
        response = client.get('/spendenkorb')
        
        # Should redirect to verse selection with message
        assert response.status_code == 302
        assert '/vers-auswaehlen' in response.location
    
    def test_empty_cart_removal_attempt(self, client):
        """Attempting to remove from empty cart should handle gracefully"""
        response = client.post('/spendenkorb/entfernen', 
                             json={'item_index': 0})
        
        # Should handle gracefully
        assert response.status_code in [200, 400]
        
        data = json.loads(response.data)
        assert data.get('success') == False
    
    def test_cart_operations_without_session(self, client):
        """Test cart operations when no session exists"""
        # Clear any existing session
        with client.session_transaction() as sess:
            sess.clear()
        
        response = client.get('/spendenkorb')
        assert response.status_code == 302


class TestSingleItemCart:
    """Test behavior with single item in cart"""
    
    def test_single_item_cart_display(self, client, sample_verse_id):
        """Single item cart should display properly"""
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {
                    'email': 'test@example.com',
                    'privacy_consent': True
                },
                'amount': 100.00,
                'currency': 'EUR'
            }]
        
        response = client.get('/spendenkorb')
        assert response.status_code == 200
        assert b'100' in response.data  # Amount should be displayed
    
    def test_remove_only_item_from_cart(self, client, sample_verse_id):
        """Removing the only item should result in empty cart"""
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        response = client.post('/spendenkorb/entfernen', 
                             json={'item_index': 0})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') == True
        
        # Cart should now be empty
        with client.session_transaction() as sess:
            assert len(sess.get('cart', [])) == 0


class TestMaximumCartSize:
    """Test behavior at maximum cart capacity"""
    
    def test_cart_at_maximum_capacity(self, client, sample_verse_id):
        """Cart with 20 items should function properly"""
        with client.session_transaction() as sess:
            # Create exactly 20 items
            cart_items = []
            for i in range(20):
                cart_items.append({
                    'verse_id': sample_verse_id + i,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': f'test{i}@example.com'},
                    'amount': 100.00,
                    'currency': 'EUR'
                })
            sess['cart'] = cart_items
        
        response = client.get('/spendenkorb')
        assert response.status_code == 200
        
        # Should display all 20 items
        with client.session_transaction() as sess:
            assert len(sess['cart']) == 20
    
    def test_adding_to_full_cart(self, client, sample_verse_id):
        """Adding to full cart should be rejected"""
        # Fill cart to maximum
        with client.session_transaction() as sess:
            cart_items = []
            for i in range(20):
                cart_items.append({
                    'verse_id': sample_verse_id + i,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': f'test{i}@example.com'},
                    'amount': 100.00
                })
            sess['cart'] = cart_items
            sess['selected_verse_id'] = sample_verse_id + 20
            sess['donation_type'] = 'einzelperson'
        
        # Try to add another item
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test21@example.com',
            'privacy': 'on'
        })
        
        # Should redirect to cart with warning
        assert response.status_code == 302
        assert '/spendenkorb' in response.location
        
        # Cart should still have exactly 20 items
        with client.session_transaction() as sess:
            assert len(sess['cart']) == 20
    
    def test_removing_from_full_cart(self, client, sample_verse_id):
        """Removing item from full cart should work"""
        # Fill cart to maximum
        with client.session_transaction() as sess:
            cart_items = []
            for i in range(20):
                cart_items.append({
                    'verse_id': sample_verse_id + i,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': f'test{i}@example.com'},
                    'amount': 100.00
                })
            sess['cart'] = cart_items
        
        # Remove middle item
        response = client.post('/spendenkorb/entfernen', 
                             json={'item_index': 10})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') == True
        
        # Should have 19 items now
        with client.session_transaction() as sess:
            assert len(sess['cart']) == 19


class TestDuplicateVerseHandling:
    """Test handling of duplicate verses"""
    
    def test_adding_duplicate_verse_to_cart(self, client, sample_verse_id):
        """Adding same verse twice should be prevented"""
        # Add first verse
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test1@example.com'},
                'amount': 100.00
            }]
            sess['selected_verse_id'] = sample_verse_id  # Same verse
            sess['donation_type'] = 'einzelperson'
        
        # Try to add same verse again
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test2@example.com',
            'privacy': 'on'
        })
        
        # Should redirect to verse selection with warning
        assert response.status_code == 302
        assert '/vers-auswaehlen' in response.location
        
        # Cart should still have only one item
        with client.session_transaction() as sess:
            assert len(sess['cart']) == 1
    
    def test_cart_consistency_after_duplicate_attempt(self, client, sample_verse_id):
        """Cart should remain consistent after duplicate attempt"""
        original_cart = [{
            'verse_id': sample_verse_id,
            'donation_type': 'gruppe',
            'donor_data': {'email': 'original@example.com'},
            'amount': 100.00
        }]
        
        with client.session_transaction() as sess:
            sess['cart'] = original_cart.copy()
            sess['selected_verse_id'] = sample_verse_id
            sess['donation_type'] = 'einzelperson'  # Different type
        
        # Try to add duplicate with different donation type
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'duplicate@example.com',
            'privacy': 'on'
        })
        
        # Original cart should be unchanged
        with client.session_transaction() as sess:
            assert len(sess['cart']) == 1
            assert sess['cart'][0]['donation_type'] == 'gruppe'
            assert sess['cart'][0]['donor_data']['email'] == 'original@example.com'


class TestCartPersistence:
    """Test cart persistence across navigation"""
    
    def test_cart_persists_across_requests(self, client, sample_verse_id):
        """Cart should persist across multiple requests"""
        # Add item to cart
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Navigate to different pages
        pages = ['/vers-auswaehlen', '/faq', '/ueber-ngue']
        
        for page in pages:
            response = client.get(page)
            assert response.status_code == 200
            
            # Cart should still exist
            with client.session_transaction() as sess:
                assert len(sess.get('cart', [])) == 1
    
    def test_cart_survives_form_validation_errors(self, client, sample_verse_id):
        """Cart should survive form validation failures"""
        # Add item to cart
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
            sess['selected_verse_id'] = sample_verse_id + 1
            sess['donation_type'] = 'einzelperson'
        
        # Submit invalid form (missing email)
        response = client.post('/checkout/einzelperson/daten', data={
            'privacy': 'on'
            # Missing required email field
        })
        
        # Should show form with errors
        assert response.status_code in [200, 400]
        
        # Cart should remain intact
        with client.session_transaction() as sess:
            assert len(sess.get('cart', [])) == 1


class TestBoundaryValues:
    """Test with boundary values and edge cases"""
    
    def test_zero_amount_handling(self, client, sample_verse_id):
        """Test handling of zero amounts"""
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 0.00,  # Zero amount
                'currency': 'EUR'
            }]
        
        response = client.get('/spendenkorb')
        
        # Should handle gracefully (either show error or normalize)
        assert response.status_code == 200
    
    def test_negative_verse_id_handling(self, client):
        """Test handling of negative verse IDs"""
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': -1,  # Negative ID
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        response = client.get('/spendenkorb')
        
        # Should handle gracefully
        assert response.status_code in [200, 302]
    
    def test_very_large_verse_id(self, client):
        """Test handling of extremely large verse IDs"""
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': 999999999,  # Very large ID
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        response = client.get('/spendenkorb')
        
        # Should handle gracefully
        assert response.status_code in [200, 302]


class TestNavigationEdgeCases:
    """Test edge cases in navigation flows"""
    
    def test_direct_access_to_checkout_without_verse(self, client):
        """Direct access to checkout without verse selection"""
        response = client.get('/checkout/einzelperson/daten')
        
        # Should redirect to verse selection
        assert response.status_code == 302
        assert '/vers-auswaehlen' in response.location
    
    def test_invalid_donation_type_url(self, client):
        """Access checkout with invalid donation type"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
        
        response = client.get('/checkout/invalid_type/daten')
        
        # Should redirect or show error
        assert response.status_code in [302, 400, 404]
    
    def test_browser_back_button_simulation(self, client, sample_verse_id):
        """Simulate browser back button behavior"""
        # Start checkout process
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = sample_verse_id
            sess['donation_type'] = 'einzelperson'
        
        # Go to data entry
        response1 = client.get('/checkout/einzelperson/daten')
        assert response1.status_code == 200
        
        # Submit form (add to cart)
        response2 = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'privacy': 'on'
        })
        assert response2.status_code == 302
        
        # Simulate going back to data entry (like browser back)
        response3 = client.get('/checkout/einzelperson/daten')
        
        # Should handle gracefully (redirect or show appropriate message)
        assert response3.status_code in [200, 302]


class TestSessionCorruption:
    """Test handling of corrupted or incomplete session data"""
    
    def test_missing_cart_structure(self, client):
        """Test when cart exists but has wrong structure"""
        with client.session_transaction() as sess:
            sess['cart'] = "not_a_list"  # Wrong type
        
        response = client.get('/spendenkorb')
        
        # Should handle gracefully
        assert response.status_code in [200, 302]
    
    def test_incomplete_cart_items(self, client):
        """Test cart items missing required fields"""
        with client.session_transaction() as sess:
            sess['cart'] = [
                {
                    # Missing verse_id
                    'donation_type': 'einzelperson',
                    'amount': 100.00
                },
                {
                    'verse_id': 1,
                    # Missing amount
                    'donation_type': 'einzelperson'
                }
            ]
        
        response = client.get('/spendenkorb')
        
        # Should handle gracefully (filter out invalid items)
        assert response.status_code in [200, 302]
    
    def test_mixed_valid_invalid_cart_items(self, client, sample_verse_id):
        """Test cart with mix of valid and invalid items"""
        with client.session_transaction() as sess:
            sess['cart'] = [
                {
                    'verse_id': sample_verse_id,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': 'valid@example.com'},
                    'amount': 100.00
                },
                {
                    'verse_id': 'invalid_id',  # Invalid type
                    'donation_type': 'einzelperson',
                    'amount': 100.00
                },
                {
                    'verse_id': sample_verse_id + 1,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': 'valid2@example.com'},
                    'amount': 100.00
                }
            ]
        
        response = client.get('/spendenkorb')
        
        # Should display valid items and handle invalid ones gracefully
        assert response.status_code == 200


class TestSessionTimeout:
    """Test behavior around session timeouts"""
    
    def test_expired_session_handling(self, client):
        """Test handling when session appears expired"""
        # Create a cart but clear session data that would normally exist
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': 1,
                'donation_type': 'einzelperson',
                'amount': 100.00
            }]
            # Don't set selected_verse_id or other session data
        
        # Try to access pages that expect session data
        response = client.get('/spendenkorb')
        
        # Should handle gracefully
        assert response.status_code == 200
    
    def test_partial_session_data(self, client):
        """Test when only some session data exists"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            # Missing donation_type
        
        response = client.get('/checkout/einzelperson/daten')
        
        # Should handle gracefully
        assert response.status_code in [200, 302]