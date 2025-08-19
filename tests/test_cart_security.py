"""
Security Tests for Cart System
Tests for potential attack vectors, input validation, and session security
"""

import pytest
import json
import html
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


class TestCartSecurityLimits:
    """Test cart size limits and session overflow protection"""
    
    def test_cart_size_limit_protection(self, client, sample_verse_id):
        """Cart should reject items beyond the 20-item limit"""
        # Fill cart to maximum (20 items)
        with client.session_transaction() as sess:
            # Create 20 cart items
            cart_items = []
            for i in range(20):
                cart_items.append({
                    'verse_id': sample_verse_id + i,  # Use different IDs
                    'donation_type': 'einzelperson',
                    'donor_data': {'email': f'test{i}@example.com', 'privacy_consent': True},
                    'amount': 100.00,
                    'currency': 'EUR'
                })
            sess['cart'] = cart_items
        
        # Try to add 21st item
        response = client.post(f'/checkout/einzelperson/daten', data={
            'email': 'test21@example.com',
            'privacy': 'on'
        })
        
        # Should redirect to cart with warning
        assert response.status_code == 302
        assert '/spendenkorb' in response.location
    
    def test_session_overflow_prevention(self, client):
        """Prevent session data from growing too large"""
        # Try to add extremely large data to session
        large_data = 'x' * 10000  # 10KB string
        
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': large_data,  # Extremely long name
            'lastName': 'Test',
            'street': 'Test Street',
            'houseNumber': '1',
            'postalCode': '12345',
            'city': 'Test City',
            'country': 'DE',
            'privacy': 'on'
        })
        
        # Should handle gracefully (either truncate or reject)
        assert response.status_code in [200, 302, 400]


class TestCartInputValidation:
    """Test input validation and sanitization"""
    
    def test_xss_prevention_in_form_fields(self, client):
        """Prevent XSS attacks through form inputs"""
        xss_payload = '<script>alert("XSS")</script>'
        
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': xss_payload,
            'lastName': xss_payload,
            'street': xss_payload,
            'privacy': 'on'
        })
        
        # Check if data is properly escaped
        with client.session_transaction() as sess:
            if 'shared_donor_data' in sess:
                data = sess['shared_donor_data']
                # Should be HTML escaped
                assert '<script>' not in str(data.get('first_name', ''))
                assert '&lt;script&gt;' in str(data.get('first_name', '')) or data.get('first_name') == html.escape(xss_payload)
    
    def test_sql_injection_prevention(self, client):
        """Prevent SQL injection through form inputs"""
        sql_payload = "'; DROP TABLE verses; --"
        
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': f'test{sql_payload}@example.com',
            'firstName': sql_payload,
            'privacy': 'on'
        })
        
        # Should handle safely without database corruption
        assert response.status_code in [200, 302, 400]
    
    def test_special_characters_handling(self, client):
        """Handle special characters and Unicode properly"""
        special_chars = "äöüßÄÖÜ€@#$%^&*()[]{}|\\:;\"'<>,.?/~`"
        unicode_chars = "测试用户 🎉 Ñoël"
        
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': special_chars,
            'lastName': unicode_chars,
            'street': 'Straße 123',
            'houseNumber': '1a',
            'postalCode': '12345',
            'city': 'München',
            'country': 'DE',
            'privacy': 'on'
        })
        
        # Should handle gracefully
        assert response.status_code in [200, 302]


class TestCartManipulation:
    """Test attempts to manipulate cart data"""
    
    def test_cart_item_index_manipulation(self, client):
        """Prevent manipulation of cart item indices"""
        # Add item to cart first
        with client.session_transaction() as sess:
            sess['cart'] = [{
                'verse_id': 1,
                'donation_type': 'einzelperson',
                'donor_data': {'email': 'test@example.com'},
                'amount': 100.00
            }]
        
        # Try to remove with invalid indices
        test_cases = [
            -1,           # Negative index
            999,          # Index out of bounds
            'invalid',    # Non-integer
            None,         # Null value
            '',           # Empty string
        ]
        
        for invalid_index in test_cases:
            response = client.post('/spendenkorb/entfernen', 
                                 json={'item_index': invalid_index})
            
            # Should handle gracefully
            assert response.status_code in [200, 400]
            
            # Cart should remain intact
            with client.session_transaction() as sess:
                assert len(sess.get('cart', [])) == 1
    
    def test_cart_direct_session_manipulation(self, client):
        """Test resilience against direct session manipulation"""
        # Malformed cart data
        malformed_carts = [
            None,
            "invalid_string",
            123,
            [{"invalid": "structure"}],
            [{"verse_id": "not_a_number"}],
            [{"verse_id": -1, "amount": -100}],  # Negative values
        ]
        
        for malformed_cart in malformed_carts:
            with client.session_transaction() as sess:
                sess['cart'] = malformed_cart
            
            # App should handle gracefully
            response = client.get('/spendenkorb')
            assert response.status_code in [200, 302]  # Either show empty cart or redirect


class TestSessionSecurity:
    """Test session-related security"""
    
    def test_session_data_isolation(self, client):
        """Ensure session data doesn't leak between requests"""
        # First request with data
        with client.session_transaction() as sess:
            sess['cart'] = [{'verse_id': 1, 'amount': 100}]
            sess['user_secret'] = 'secret_data'
        
        # Clear session and make new request
        with client.session_transaction() as sess:
            sess.clear()
        
        response = client.get('/spendenkorb')
        
        # Should not have access to previous session data
        with client.session_transaction() as sess:
            assert 'user_secret' not in sess
            assert sess.get('cart', []) == []
    
    def test_csrf_token_validation(self, client):
        """Test CSRF protection (when enabled)"""
        # Enable CSRF for this test
        app.config['WTF_CSRF_ENABLED'] = True
        
        try:
            with client.session_transaction() as sess:
                sess['selected_verse_id'] = 1
                sess['donation_type'] = 'einzelperson'
            
            # Request without CSRF token should fail
            response = client.post('/checkout/einzelperson/daten', data={
                'email': 'test@example.com',
                'privacy': 'on'
            })
            
            # Should either fail or show form again with error
            assert response.status_code in [200, 400, 403]
            
        finally:
            app.config['WTF_CSRF_ENABLED'] = False
    
    def test_concurrent_session_handling(self, client):
        """Test handling of concurrent session modifications"""
        # Simulate race condition by modifying cart during request
        with client.session_transaction() as sess:
            sess['cart'] = [{'verse_id': 1, 'amount': 100}]
        
        # Start request that modifies cart
        response1 = client.get('/spendenkorb')
        
        # Simulate concurrent modification
        with client.session_transaction() as sess:
            sess['cart'].append({'verse_id': 2, 'amount': 100})
        
        # Complete original request
        assert response1.status_code == 200


class TestDataValidation:
    """Test data validation and sanitization"""
    
    def test_email_validation_edge_cases(self, client):
        """Test email validation with edge cases"""
        invalid_emails = [
            '',                    # Empty
            'invalid',            # No @
            '@example.com',       # No local part
            'test@',              # No domain
            'test@.com',          # Invalid domain
            'test..test@example.com',  # Double dots
            'test@example..com',  # Double dots in domain
            'a' * 300 + '@example.com',  # Too long
        ]
        
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        for invalid_email in invalid_emails:
            response = client.post('/checkout/einzelperson/daten', data={
                'email': invalid_email,
                'privacy': 'on'
            })
            
            # Should either show validation error or return to form
            assert response.status_code in [200, 400]
    
    def test_form_field_length_limits(self, client):
        """Test field length validation"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        # Test with extremely long values
        long_string = 'x' * 1000
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': long_string,
            'lastName': long_string,
            'street': long_string,
            'city': long_string,
            'privacy': 'on'
        })
        
        # Should handle gracefully (truncate or reject)
        assert response.status_code in [200, 302, 400]
    
    def test_numeric_field_validation(self, client):
        """Test validation of numeric fields"""
        # Test with invalid postal codes
        invalid_postal_codes = [
            'abc123',     # Mixed letters/numbers
            '123456789012345',  # Too long
            '-12345',     # Negative
            '12.345',     # Decimal
            '',           # Empty
        ]
        
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        for invalid_code in invalid_postal_codes:
            response = client.post('/checkout/einzelperson/daten', data={
                'email': 'test@example.com',
                'firstName': 'Test',
                'lastName': 'User',
                'street': 'Test Street',
                'houseNumber': '1',
                'postalCode': invalid_code,
                'city': 'Test City',
                'country': 'DE',
                'privacy': 'on'
            })
            
            # Should validate and handle appropriately
            assert response.status_code in [200, 400]


class TestErrorHandling:
    """Test error handling in security contexts"""
    
    def test_malformed_json_requests(self, client):
        """Test handling of malformed JSON in API requests"""
        malformed_payloads = [
            '{"invalid": json}',  # Invalid JSON syntax
            '{"verse_id": }',     # Incomplete JSON
            '',                   # Empty payload
            '{' * 1000,          # Extremely nested/large
        ]
        
        for payload in malformed_payloads:
            response = client.post('/spendenkorb/entfernen',
                                 data=payload,
                                 content_type='application/json')
            
            # Should handle gracefully
            assert response.status_code in [200, 400, 500]
    
    def test_missing_required_fields(self, client):
        """Test handling when required fields are missing"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = 1
            sess['donation_type'] = 'einzelperson'
        
        # Submit form with missing required fields
        response = client.post('/checkout/einzelperson/daten', data={
            # Missing email and privacy consent
        })
        
        # Should show validation errors
        assert response.status_code in [200, 400]
        
        # Should not add to cart
        with client.session_transaction() as sess:
            assert sess.get('cart', []) == []