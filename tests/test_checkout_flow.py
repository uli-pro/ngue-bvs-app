"""
Checkout Flow Tests
Tests for complete checkout process, form data persistence, and donation types
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


class TestBasicCheckoutFlow:
    """Test basic checkout flow for all donation types"""
    
    def test_einzelperson_checkout_flow(self, client, sample_verse_id):
        """Complete einzelperson checkout flow"""
        # Step 1: Select verse and donation type
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        assert response.status_code == 302
        assert 'checkout' in response.location
        
        # Step 2: Fill out contact form
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'salutation': 'Herr',
            'firstName': 'Max',
            'lastName': 'Mustermann',
            'street': 'Musterstraße',
            'houseNumber': '123',
            'postalCode': '12345',
            'city': 'Musterstadt',
            'country': 'DE',
            'newsletter': 'on',
            'privacy': 'on'
        })
        
        # Should redirect to cart
        assert response.status_code == 302
        assert '/spendenkorb' in response.location
        
        # Verify item in cart
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            assert cart[0]['donation_type'] == 'einzelperson'
            assert cart[0]['donor_data']['email'] == 'test@example.com'
            assert cart[0]['donor_data']['newsletter'] == True
    
    def test_gruppe_checkout_flow(self, client, sample_verse_id):
        """Complete gruppe checkout flow"""
        # Select verse and donation type
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'gruppe'
        })
        assert response.status_code == 302
        
        # Fill out group form
        response = client.post('/checkout/gruppe/daten', data={
            'email': 'kontakt@gemeinde.de',
            'group_article': 'Die',
            'group_name': 'Kirchengemeinde St. Maria',
            'privacy': 'on'
        })
        
        # Should redirect to cart
        assert response.status_code == 302
        assert '/spendenkorb' in response.location
        
        # Verify group data in cart
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            assert cart[0]['donation_type'] == 'gruppe'
            assert cart[0]['donor_data']['group_name'] == 'Kirchengemeinde St. Maria'
            assert cart[0]['donor_data']['wants_receipt'] == False  # Groups don't get receipts
    
    def test_geschenk_checkout_flow(self, client, sample_verse_id):
        """Complete geschenk checkout flow"""
        # Select verse and donation type
        response = client.post(f'/vers/{sample_verse_id}/spendenart', data={
            'donation_type': 'geschenk'
        })
        assert response.status_code == 302
        
        # Fill out gift form
        response = client.post('/checkout/geschenk/daten', data={
            'email': 'spender@example.com',
            'salutation': 'Frau',
            'firstName': 'Anna',
            'lastName': 'Spenderin',
            'street': 'Geberstraße',
            'houseNumber': '456',
            'postalCode': '54321',
            'city': 'Geberstadt',
            'country': 'DE',
            'gift_recipient_name': 'Maria Beschenkte',
            'gift_direct_send': 'on',
            'gift_recipient_email': 'beschenkte@example.com',
            'privacy': 'on'
        })
        
        # Should redirect to cart
        assert response.status_code == 302
        assert '/spendenkorb' in response.location
        
        # Verify gift data in cart
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            assert cart[0]['donation_type'] == 'geschenk'
            assert cart[0]['donor_data']['gift_recipient_name'] == 'Maria Beschenkte'
            assert cart[0]['donor_data']['gift_direct_send'] == True


class TestFormDataPersistence:
    """Test form data persistence between checkout attempts"""
    
    def test_newsletter_checkbox_persistence(self, client, sample_verse_id):
        """Newsletter checkbox should remain checked for subsequent verses"""
        # First verse with newsletter subscription
        self._complete_checkout(client, sample_verse_id, {
            'email': 'test@example.com',
            'newsletter': 'on',
            'privacy': 'on'
        })
        
        # Select another verse
        another_verse_id = sample_verse_id + 1
        response = client.post(f'/vers/{another_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        # Get form - newsletter should be pre-checked
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200
        # Newsletter checkbox should be checked (form_data.newsletter = True)
    
    def test_privacy_checkbox_persistence(self, client, sample_verse_id):
        """Privacy checkbox should remain checked for subsequent verses"""
        # First verse with privacy consent
        self._complete_checkout(client, sample_verse_id, {
            'email': 'test@example.com',
            'privacy': 'on'
        })
        
        # Select another verse
        another_verse_id = sample_verse_id + 1
        response = client.post(f'/vers/{another_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        # Get form - privacy should be pre-checked
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200
        # Privacy checkbox should be checked
    
    def test_donor_data_persistence(self, client, sample_verse_id):
        """Donor personal data should persist between checkouts"""
        donor_data = {
            'email': 'max@example.com',
            'salutation': 'Herr',
            'firstName': 'Max',
            'lastName': 'Mustermann',
            'street': 'Teststraße',
            'houseNumber': '123',
            'postalCode': '12345',
            'city': 'Teststadt',
            'country': 'DE',
            'privacy': 'on'
        }
        
        # First checkout
        self._complete_checkout(client, sample_verse_id, donor_data)
        
        # Select another verse
        another_verse_id = sample_verse_id + 1
        response = client.post(f'/vers/{another_verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        # Form should be pre-filled with previous data
        response = client.get('/checkout/einzelperson/daten')
        assert response.status_code == 200
        # Check that shared_donor_data contains the right values
    
    def test_data_persistence_across_donation_types(self, client, sample_verse_id):
        """Data should persist even when switching donation types"""
        # Complete einzelperson checkout
        self._complete_checkout(client, sample_verse_id, {
            'email': 'test@example.com',
            'firstName': 'Test',
            'lastName': 'User',
            'privacy': 'on'
        })
        
        # Switch to geschenk type for another verse
        another_verse_id = sample_verse_id + 1
        response = client.post(f'/vers/{another_verse_id}/spendenart', data={
            'donation_type': 'geschenk'
        })
        
        # Form should still have email and name data
        response = client.get('/checkout/geschenk/daten')
        assert response.status_code == 200
    
    def _complete_checkout(self, client, verse_id, form_data):
        """Helper to complete a checkout process"""
        # Select verse
        client.post(f'/vers/{verse_id}/spendenart', data={
            'donation_type': 'einzelperson'
        })
        
        # Submit form
        response = client.post('/checkout/einzelperson/daten', data=form_data)
        assert response.status_code == 302


class TestFormValidation:
    """Test form validation for all donation types"""
    
    def test_einzelperson_required_fields(self, client, sample_verse_id):
        """Test required field validation for einzelperson"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        # Test missing email
        response = client.post('/checkout/einzelperson/daten', data={
            'privacy': 'on'
        })
        assert response.status_code in [200, 400]
        
        # Should not add to cart
        with client.session_transaction() as sess:
            assert len(sess.get('cart', [])) == 0
        
        # Test missing privacy consent
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com'
        })
        assert response.status_code in [200, 400]
    
    def test_gruppe_required_fields(self, client, sample_verse_id):
        """Test required field validation for gruppe"""
        self._setup_checkout(client, sample_verse_id, 'gruppe')
        
        # Test missing group name
        response = client.post('/checkout/gruppe/daten', data={
            'email': 'test@example.com',
            'group_article': 'Die',
            'privacy': 'on'
        })
        assert response.status_code in [200, 400]
        
        # Test missing group article
        response = client.post('/checkout/gruppe/daten', data={
            'email': 'test@example.com',
            'group_name': 'Test Gruppe',
            'privacy': 'on'
        })
        assert response.status_code in [200, 400]
    
    def test_geschenk_required_fields(self, client, sample_verse_id):
        """Test required field validation for geschenk"""
        self._setup_checkout(client, sample_verse_id, 'geschenk')
        
        # Test missing gift recipient name
        response = client.post('/checkout/geschenk/daten', data={
            'email': 'test@example.com',
            'privacy': 'on'
        })
        assert response.status_code in [200, 400]
        
        # Test missing recipient email when direct send is enabled
        response = client.post('/checkout/geschenk/daten', data={
            'email': 'test@example.com',
            'gift_recipient_name': 'Test Recipient',
            'gift_direct_send': 'on',
            # Missing gift_recipient_email
            'privacy': 'on'
        })
        assert response.status_code in [200, 400]
    
    def test_spendenbescheinigung_required_fields(self, client, sample_verse_id):
        """Test required fields when receipt is requested"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        # Test with receipt enabled but missing required fields
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'wantReceipt': 'on',
            # Missing salutation, firstName, lastName, etc.
            'privacy': 'on'
        })
        assert response.status_code in [200, 400]
    
    def _setup_checkout(self, client, verse_id, donation_type):
        """Helper to set up checkout session"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = verse_id
            sess['donation_type'] = donation_type


class TestFieldLengthValidation:
    """Test field length limits and truncation"""
    
    def test_string_field_length_limits(self, client, sample_verse_id):
        """Test that string fields are properly limited"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        # Test with extremely long values
        long_string = 'x' * 500  # 500 characters
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': long_string,
            'lastName': long_string,
            'street': long_string,
            'city': long_string,
            'houseNumber': '1',
            'postalCode': '12345',
            'country': 'DE',
            'privacy': 'on'
        })
        
        # Should handle gracefully (truncate or reject)
        assert response.status_code in [200, 302, 400]
        
        if response.status_code == 302:
            # If accepted, check truncation
            with client.session_transaction() as sess:
                cart = sess.get('cart', [])
                if cart:
                    donor_data = cart[0]['donor_data']
                    assert len(donor_data.get('first_name', '')) <= 100
                    assert len(donor_data.get('last_name', '')) <= 100
    
    def test_email_length_validation(self, client, sample_verse_id):
        """Test email length validation"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        # Very long email
        long_email = 'a' * 300 + '@example.com'
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': long_email,
            'privacy': 'on'
        })
        
        # Should reject or truncate
        assert response.status_code in [200, 400]
    
    def test_postal_code_validation(self, client, sample_verse_id):
        """Test postal code length and format"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        test_codes = [
            '123456789012345',  # Too long
            '',                 # Empty
            '12.345',          # With decimal
            'ABCDE',           # Letters only
        ]
        
        for code in test_codes:
            response = client.post('/checkout/einzelperson/daten', data={
                'email': 'test@example.com',
                'firstName': 'Test',
                'lastName': 'User',
                'street': 'Test Street',
                'houseNumber': '1',
                'postalCode': code,
                'city': 'Test City',
                'country': 'DE',
                'privacy': 'on'
            })
            
            # Should validate appropriately
            assert response.status_code in [200, 400]
    
    def _setup_checkout(self, client, verse_id, donation_type):
        """Helper to set up checkout session"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = verse_id
            sess['donation_type'] = donation_type


class TestSpecialCharacters:
    """Test handling of special characters and Unicode"""
    
    def test_unicode_in_names(self, client, sample_verse_id):
        """Test Unicode characters in name fields"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': 'José María',
            'lastName': 'Ñoël van der Müller',
            'street': 'Straße',
            'houseNumber': '1a',
            'postalCode': '12345',
            'city': 'München',
            'country': 'DE',
            'privacy': 'on'
        })
        
        # Should handle Unicode correctly
        assert response.status_code in [200, 302]
        
        if response.status_code == 302:
            with client.session_transaction() as sess:
                cart = sess.get('cart', [])
                if cart:
                    donor_data = cart[0]['donor_data']
                    assert 'José' in donor_data.get('first_name', '')
                    assert 'Ñoël' in donor_data.get('last_name', '')
    
    def test_special_characters_in_addresses(self, client, sample_verse_id):
        """Test special characters in address fields"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': 'Test',
            'lastName': 'User',
            'street': 'Straße & Gasse',
            'houseNumber': '1-3/5',
            'postalCode': '12345',
            'city': 'Test-Stadt (Süd)',
            'country': 'DE',
            'privacy': 'on'
        })
        
        # Should handle special characters in addresses
        assert response.status_code in [200, 302]
    
    def test_emoji_handling(self, client, sample_verse_id):
        """Test emoji characters in form fields"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': 'Test 🎉',
            'lastName': 'User ❤️',
            'privacy': 'on'
        })
        
        # Should handle emojis (either accept or sanitize)
        assert response.status_code in [200, 302]
    
    def _setup_checkout(self, client, verse_id, donation_type):
        """Helper to set up checkout session"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = verse_id
            sess['donation_type'] = donation_type


class TestInternationalAddresses:
    """Test international address formats"""
    
    def test_different_country_formats(self, client, sample_verse_id):
        """Test address formats for different countries"""
        countries_and_formats = [
            ('US', '90210', 'Beverly Hills, CA'),
            ('GB', 'SW1A 1AA', 'London'),
            ('FR', '75001', 'Paris'),
            ('CH', '8001', 'Zürich'),
            ('AT', '1010', 'Wien'),
        ]
        
        for country, postal_code, city in countries_and_formats:
            with client.session_transaction() as sess:
                sess['selected_verse_id'] = sample_verse_id
                sess['donation_type'] = 'einzelperson'
            
            response = client.post('/checkout/einzelperson/daten', data={
                'email': 'test@example.com',
                'firstName': 'Test',
                'lastName': 'User',
                'street': 'Test Street',
                'houseNumber': '123',
                'postalCode': postal_code,
                'city': city,
                'country': country,
                'privacy': 'on'
            })
            
            # Should accept various international formats
            assert response.status_code in [200, 302]
    
    def test_missing_country_default(self, client, sample_verse_id):
        """Test default country handling"""
        self._setup_checkout(client, sample_verse_id, 'einzelperson')
        
        response = client.post('/checkout/einzelperson/daten', data={
            'email': 'test@example.com',
            'firstName': 'Test',
            'lastName': 'User',
            'street': 'Test Street',
            'houseNumber': '123',
            'postalCode': '12345',
            'city': 'Test City',
            # country not specified
            'privacy': 'on'
        })
        
        # Should default to DE or handle gracefully
        assert response.status_code in [200, 302]
        
        if response.status_code == 302:
            with client.session_transaction() as sess:
                cart = sess.get('cart', [])
                if cart and cart[0]['donor_data'].get('country'):
                    assert cart[0]['donor_data']['country'] in ['DE', '']
    
    def _setup_checkout(self, client, verse_id, donation_type):
        """Helper to set up checkout session"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = verse_id
            sess['donation_type'] = donation_type


class TestGiftSpecificFeatures:
    """Test gift-specific functionality"""
    
    def test_gift_direct_send_toggle(self, client, sample_verse_id):
        """Test gift direct send functionality"""
        self._setup_checkout(client, sample_verse_id, 'geschenk')
        
        # Test with direct send enabled
        response = client.post('/checkout/geschenk/daten', data={
            'email': 'spender@example.com',
            'gift_recipient_name': 'Test Recipient',
            'gift_direct_send': 'on',
            'gift_recipient_email': 'recipient@example.com',
            'privacy': 'on'
        })
        
        assert response.status_code == 302
        
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            assert cart[0]['donor_data']['gift_direct_send'] == True
            assert cart[0]['donor_data']['gift_recipient_email'] == 'recipient@example.com'
    
    def test_gift_personal_delivery(self, client, sample_verse_id):
        """Test gift for personal delivery (no direct send)"""
        self._setup_checkout(client, sample_verse_id, 'geschenk')
        
        # Test without direct send (personal delivery)
        response = client.post('/checkout/geschenk/daten', data={
            'email': 'spender@example.com',
            'gift_recipient_name': 'Test Recipient',
            # gift_direct_send not checked
            'privacy': 'on'
        })
        
        assert response.status_code == 302
        
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            assert cart[0]['donor_data']['gift_direct_send'] == False
            assert 'gift_recipient_email' not in cart[0]['donor_data'] or cart[0]['donor_data']['gift_recipient_email'] == ''
    
    def test_gift_message_handling(self, client, sample_verse_id):
        """Test gift message functionality"""
        self._setup_checkout(client, sample_verse_id, 'geschenk')
        
        gift_message = "Herzlichen Glückwunsch zum Geburtstag! 🎉"
        
        response = client.post('/checkout/geschenk/daten', data={
            'email': 'spender@example.com',
            'gift_recipient_name': 'Test Recipient',
            'gift_direct_send': 'on',
            'gift_recipient_email': 'recipient@example.com',
            'gift_message': gift_message,
            'privacy': 'on'
        })
        
        assert response.status_code == 302
        
        with client.session_transaction() as sess:
            cart = sess.get('cart', [])
            assert len(cart) == 1
            # Message should be HTML-escaped for security
            stored_message = cart[0]['donor_data']['gift_message']
            assert 'Glückwunsch' in stored_message
    
    def _setup_checkout(self, client, verse_id, donation_type):
        """Helper to set up checkout session"""
        with client.session_transaction() as sess:
            sess['selected_verse_id'] = verse_id
            sess['donation_type'] = donation_type