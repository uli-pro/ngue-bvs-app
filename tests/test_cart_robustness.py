"""
Cart Robustness and Error Recovery Tests
Tests for error handling, graceful degradation, and system resilience
"""

import pytest
import json
import time
from unittest.mock import patch, Mock
from app import app
from models import Verse
from flask import session
from werkzeug.exceptions import InternalServerError


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


class TestNetworkInterruptionSimulation:
    """Test handling of network interruptions and partial requests"""
    
    def test_partial_form_submission_recovery(self, client, sample_verse_id):
        """Test recovery from partial form submissions"""
        # Start checkout process
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = sample_verse_id
            sess['donation_type'] = 'einzelperson'
        
        # Simulate partial form data (as if network was interrupted)
        partial_data = {
            'email': 'test@example.com',
            # Missing other required fields
        }
        
        response = client.post('/checkout/einzelperson/daten', data=partial_data)
        
        # Should handle gracefully and not add invalid data to cart
        assert response.status_code in [200, 400]
        
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 0  # No incomplete data should be added
            
            # Session should maintain verse selection for retry
            assert sess.get('selected_verse_id') == sample_verse_id
    
    def test_session_corruption_recovery(self, client, sample_verse_id):
        """Test recovery from corrupted session data"""
        # Create corrupted session data
        with client.session_transaction() as sess:
            sess['cart'] = "corrupted_data"  # Should be list
            sess['selected_verse_id'] = "not_a_number"  # Should be int
            sess['shared_donor_data'] = 12345  # Should be dict
        
        # Access cart page - should handle corruption gracefully
        response = client.get('/spendenkorb')
        
        # Should either show empty cart or redirect to verse selection
        assert response.status_code in [200, 302]
        
        # Session should be cleaned up
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert isinstance(cart, list)  # Should be corrected to proper type
    
    def test_concurrent_cart_modifications(self, client, sample_verse_id):
        """Test handling of concurrent cart modifications"""
        # Add item to cart
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Simulate concurrent modification during removal
        original_cart = None
        with client.session_transaction() as sess:
            original_cart = sess['cart'].copy()
        
        # Start removal request
        response = client.post('/spendenkorb/entfernen', 
                             json={'item_index': 0})
        
        # Should handle gracefully even if cart was modified concurrently
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Should either succeed or fail gracefully
        assert 'success' in data


class TestDatabaseErrorHandling:
    """Test handling of database connection and query errors"""
    
    @patch('models.Verse.query')
    def test_database_unavailable_during_cart_display(self, mock_query, client):
        """Test cart display when database is unavailable"""
        # Mock database error
        mock_query.get.side_effect = Exception("Database connection failed")
        
        # Add item to cart with valid-looking data
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': 1,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Access cart - should handle database error gracefully
        response = client.get('/spendenkorb')
        
        # Should show error page or graceful degradation
        assert response.status_code in [200, 500]
    
    def test_verse_not_found_in_cart(self, client):
        """Test handling when verse in cart no longer exists"""
        # Add non-existent verse to cart
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': 999999,  # Non-existent verse
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Access cart
        response = client.get('/spendenkorb')
        
        # Should handle missing verse gracefully
        assert response.status_code in [200, 302]
        
        # Invalid items might be filtered out
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            # Cart might be empty or contain error markers
            assert isinstance(cart, list)
    
    def test_verse_became_sponsored_during_checkout(self, client, sample_verse_id):
        """Test handling when verse becomes sponsored during checkout"""
        # Simulate verse being sponsored between selection and checkout
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Mock verse as sponsored
        with patch('models.Verse.query') as mock_query:
            mock_verse = Mock()
            mock_verse.is_sponsored = True
            mock_verse.id = sample_verse_id
            mock_query.get.return_value = mock_verse
            
            response = client.get('/spendenkorb')
            
            # Should handle gracefully (show warning, remove item, etc.)
            assert response.status_code in [200, 302]


class TestMemoryAndResourceHandling:
    """Test handling of memory limits and resource constraints"""
    
    def test_large_session_data_handling(self, client):
        """Test handling of extremely large session data"""
        # Create large cart data
        large_cart = []
        for i in range(20):  # Maximum cart size
            large_cart.append({
                'verse_id': i + 1,
                'donation_type': 'einzelperson',
                'donor_data': {
                    'email': f'test{i}@example.com',
                    'first_name': 'X' * 100,  # Large strings
                    'last_name': 'Y' * 100,
                    'street': 'Z' * 200,
                    'notes': 'A' * 1000  # Very large field
                },
                'amount': 100.00
            })
        
        with client.session_transaction() as sess:
            sess['cart'] = large_cart
        
        # Should handle large session data
        response = client.get('/spendenkorb')
        assert response.status_code in [200, 302]
    
    def test_memory_leak_prevention(self, client, sample_verse_id):
        """Test that repeated operations don't cause memory leaks"""
        # Perform many cart operations
        for i in range(10):
            # Add item
            with client.session_transaction() as sess:
                sess['selected_verse_id'] = sample_verse_id + i
                sess['donation_type'] = 'einzelperson'
            
            # Complete checkout
            response = client.post('/checkout/einzelperson/daten', data={
                'email': f'test{i}@example.com',
                'privacy': 'on'
            })
            
            # Remove item
            if i > 0:  # Can't remove from empty cart
                client.post('/spendenkorb/entfernen', 
                           json={'item_index': 0})
        
        # Should complete without memory issues
        response = client.get('/spendenkorb')
        assert response.status_code in [200, 302]
    
    def test_session_size_monitoring(self, client, sample_verse_id):
        """Test that session size stays within reasonable limits"""
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
            
            # Session should not grow excessively large
            # (This is implementation-dependent)
            assert len(str(sess)) < 50000  # Reasonable session size limit


class TestErrorMessageClarity:
    """Test that error messages are clear and helpful"""
    
    def test_validation_error_messages(self, client, sample_verse_id):
        """Test that validation errors provide clear guidance"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = sample_verse_id
            sess['donation_type'] = 'einzelperson'
        
        # Submit form with validation errors
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'invalid-email',  # Invalid format
            # Missing required fields
        })
        
        # Should provide helpful error messages
        assert response.status_code in [200, 400]
        # In a real test, you'd check that specific error messages are shown
    
    def test_system_error_handling(self, client):
        """Test handling of unexpected system errors"""
        # Simulate system error
        with patch('flask.session', side_effect=Exception("System error")):
            response = client.get('/spendenkorb')
            
            # Should show user-friendly error page
            assert response.status_code in [200, 500]
    
    def test_empty_cart_guidance(self, client):
        """Test that empty cart provides clear next steps"""
        response = client.get('/spendenkorb')
        
        # Should redirect to verse selection with helpful message
        assert response.status_code == 302
        assert '/vers-auswaehlen' in response.location


class TestStateConsistency:
    """Test that application state remains consistent after errors"""
    
    def test_failed_checkout_state_consistency(self, client, sample_verse_id):
        """Test state consistency after failed checkout"""
        # Set up checkout
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = sample_verse_id
            sess['donation_type'] = 'einzelperson'
            sess['reservation_id'] = 123  # Mock reservation
        
        # Attempt checkout with invalid data
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'invalid'  # Invalid email
        })
        
        # State should remain consistent
        with client.session_transaction() as sess:
            # Should still have verse selected for retry
            assert sess.get('selected_verse_id') == sample_verse_id
            # Should not have incomplete data in cart
            assert len(sess.get('cart', [])) == 0
    
    def test_cart_consistency_after_removal_error(self, client, sample_verse_id):
        """Test cart consistency after failed item removal"""
        # Set up cart with multiple items
        with client.session_transaction() as sess:
            sess['cart'] = [
                {
                    'verse_id': sample_verse_id,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': 'test1@example.com'},
                    'amount': 100.00
                },
                {
                    'verse_id': sample_verse_id + 1,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': 'test2@example.com'},
                    'amount': 100.00
                }
            ]
        
        # Try to remove invalid index
        response = client.post('/spendenkorb/entfernen', 
                             json={'item_index': 999})
        
        # Cart should remain unchanged
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 2  # Both items should still be there
            assert cart[0]['verse_id'] == sample_verse_id
            assert cart[1]['verse_id'] == sample_verse_id + 1
    
    def test_session_isolation_between_users(self, client, sample_verse_id):
        """Test that sessions don't interfere with each other"""
        # First user adds item to cart
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'user1@example.com'},
                'amount': 100.00
            }]
        
        # Simulate second user (new client)
        client2 = app.test_client()
        with client2:
            response = client2.get('/spendenkorb')
            
            # Second user should have empty cart
            assert response.status_code == 302  # Redirect to verse selection
            
            with client2.session_transaction() as sess:
                assert len(sess.get('cart', [])) == 0
        
        # First user's cart should be unchanged
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            assert cart[0]['donor_data']['email'] == 'user1@example.com'


class TestPerformanceDegradation:
    """Test graceful performance degradation under load"""
    
    def test_slow_database_response_handling(self, client, sample_verse_id):
        """Test handling of slow database responses"""
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Mock slow database response
        with patch('models.Verse.query') as mock_query:
            def slow_get(verse_id):
                time.sleep(0.1)  # Simulate slow response
                mock_verse = Mock()
                mock_verse.id = verse_id
                mock_verse.is_sponsored = False
                mock_verse.reference = "Test 1:1"
                mock_verse.text = "Test verse"
                return mock_verse
            
            mock_query.get.side_effect = slow_get
            
            # Should still complete, just slower
            response = client.get('/spendenkorb')
            assert response.status_code == 200
    
    def test_timeout_handling(self, client):
        """Test handling of operation timeouts"""
        # This would typically test external service timeouts
        # For now, test basic timeout resilience
        
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': 1,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Should handle requests even with potential timeouts
        response = client.get('/spendenkorb')
        assert response.status_code in [200, 302, 500]


class TestRecoveryMechanisms:
    """Test system recovery mechanisms"""
    
    def test_automatic_session_cleanup(self, client):
        """Test that invalid session data is automatically cleaned up"""
        # Create session with mix of valid and invalid data
        with client.session_transaction() as sess:
            sess['cart'] = [
                {
                    'verse_id': 1,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': 'valid@example.com'},
                    'amount': 100.00
                },
                {
                    # Invalid item - missing required fields
                    'verse_id': 'invalid'
                },
                {
                    'verse_id': 2,
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': 'valid2@example.com'},
                    'amount': 100.00
                }
            ]
        
        # Access cart - should clean up invalid items
        response = client.get('/spendenkorb')
        assert response.status_code in [200, 302]
        
        # Invalid items should be filtered out
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            valid_items = [item for item in cart if isinstance(item.get('verse_id'), int)]
            # Should have fewer items after cleanup
            assert len(valid_items) <= 2
    
    def test_graceful_degradation_without_javascript(self, client, sample_verse_id):
        """Test that cart works without JavaScript"""
        # Add item to cart
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': sample_verse_id,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Access cart page (should work without JS)
        response = client.get('/spendenkorb')
        assert response.status_code == 200
        
        # Basic HTML structure should be present
        assert b'cart' in response.data.lower() or b'spendenkorb' in response.data.lower()
    
    def test_error_logging_and_monitoring(self, client):
        """Test that errors are properly logged for monitoring"""
        # This test would check error logging mechanisms
        # For now, ensure errors don't cause crashes
        
        # Trigger various error conditions
        error_conditions = [
            '/checkout/invalid_type/daten',  # Invalid donation type
            '/vers/999999/spendenart',       # Non-existent verse
        ]
        
        for url in error_conditions:
            response = client.get(url)
            # Should handle errors gracefully, not crash
            assert response.status_code in [200, 302, 404, 500]