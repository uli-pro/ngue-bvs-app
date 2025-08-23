#!/usr/bin/env python3
"""
Test script for Stripe integration
Tests SEPA and 3D Secure functionality
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import our modules
from app import app
from models import db, Verse, Donation
from stripe_service import StripeService

def test_stripe_config():
    """Test Stripe configuration"""
    print("🔧 Testing Stripe Configuration...")
    
    public_key = os.environ.get('STRIPE_PUBLIC_KEY')
    secret_key = os.environ.get('STRIPE_SECRET_KEY')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    print(f"✅ Public Key: {'✓' if public_key and public_key.startswith('pk_') else '✗'}")
    print(f"✅ Secret Key: {'✓' if secret_key and secret_key.startswith('sk_') else '✗'}")
    print(f"✅ Webhook Secret: {'✓' if webhook_secret and webhook_secret.startswith('whsec_') else '✗'}")
    
    if not all([public_key, secret_key, webhook_secret]):
        print("❌ Stripe configuration incomplete!")
        return False
    
    print("✅ Stripe configuration complete!")
    return True

def create_test_cart():
    """Create a test cart with sample verses"""
    print("\n📝 Creating test cart...")
    
    with app.app_context():
        # Get 2 unsponsored verses for testing
        verses = Verse.query.filter_by(is_sponsored=False).limit(2).all()
        
        if len(verses) < 2:
            print("❌ Not enough unsponsored verses for testing!")
            return None
        
        # Create test cart items
        cart_items = []
        for i, verse in enumerate(verses):
            cart_item = {
                'verse_id': verse.id,
                'donation_type': 'einzelperson',
                'amount': 100.00,
                'currency': 'EUR',
                'donor_data': {
                    'email': f'test{i+1}@example.com',
                    'first_name': f'Test{i+1}',
                    'last_name': 'User',
                    'street': 'Teststraße',
                    'house_number': '123',
                    'postal_code': '12345',
                    'city': 'Berlin',
                    'country': 'DE',
                    'wants_receipt': True,
                    'privacy_consent': True,
                    'newsletter': False
                }
            }
            cart_items.append(cart_item)
        
        print(f"✅ Created test cart with {len(cart_items)} verses:")
        for i, item in enumerate(cart_items):
            verse = verses[i]
            print(f"   - {verse.reference}: {verse.text[:50]}...")
        
        return cart_items

def test_payment_intent_creation():
    """Test PaymentIntent creation"""
    print("\n💳 Testing PaymentIntent Creation...")
    
    cart_items = create_test_cart()
    if not cart_items:
        return False
    
    donor_data = cart_items[0]['donor_data']
    
    try:
        with app.app_context():
            with app.test_request_context('/', 
                                        environ_base={'REMOTE_ADDR': '127.0.0.1'},
                                        headers={'User-Agent': 'NGU-Test-Suite/1.0'}):
                # Test PaymentIntent creation
                payment_data = StripeService.create_payment_intent(cart_items, donor_data)
                
                print("✅ PaymentIntent created successfully!")
                print(f"   - Client Secret: {payment_data['client_secret'][:20]}...")
                print(f"   - Amount: €{payment_data['amount']/100:.2f}")
                print(f"   - Currency: {payment_data['currency']}")
                
                # Check if donations were created
                donation_ids = payment_data['metadata']['donation_ids'].split(',')
                donations = Donation.query.filter(Donation.id.in_(donation_ids)).all()
                
                print(f"✅ {len(donations)} donation records created:")
                for donation in donations:
                    print(f"   - Donation {donation.id}: {donation.verse.reference} ({donation.payment_status})")
                
                return True
            
    except Exception as e:
        print(f"❌ PaymentIntent creation failed: {e}")
        return False

def test_sepa_test_iban():
    """Test SEPA test IBAN validation"""
    print("\n🏦 SEPA Test IBANs for manual testing:")
    
    test_ibans = {
        'DE89370400440532013000': 'Success (Germany)',
        'AT483200000012345864': 'Success (Austria)', 
        'NL02ABNA0123456789': 'Success (Netherlands)',
        'DE62370400440532013001': 'Decline (Germany)',
        'FR1420041010050500013M02606': 'Success (France)'
    }
    
    for iban, description in test_ibans.items():
        print(f"   📋 {iban} - {description}")
    
    print("\n💡 Use these IBANs in the payment form for testing!")

def test_3ds_test_cards():
    """Test 3D Secure test cards"""
    print("\n🛡️  3D Secure Test Cards for manual testing:")
    
    test_cards = {
        '4000 0027 6000 3184': '3DS2 Authentication Required',
        '4000 0025 0000 3155': '3DS2 Authentication (Frictionless)',
        '4242 4242 4242 4242': 'Success (3DS Optional)',
        '4000 0000 0000 0002': 'Generic Decline',
        '4000 0000 0000 9995': 'Insufficient Funds',
        '4000 0000 0000 0069': 'Expired Card'
    }
    
    for card, description in test_cards.items():
        print(f"   💳 {card} - {description}")
    
    print("\n💡 Use these cards in the payment form for testing!")

def test_webhook_signature_verification():
    """Test webhook signature verification"""
    print("\n🔐 Testing Webhook Signature Verification...")
    
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        print("❌ Webhook secret not configured!")
        return False
    
    # Test payload (mock)
    test_payload = b'{"test": "payload"}'
    test_signature = "t=1234567890,v1=test_signature"
    
    try:
        # This will fail with test data, but we can check if the function exists
        StripeService.verify_webhook_signature(test_payload, test_signature, webhook_secret)
    except Exception as e:
        if "Invalid signature" in str(e):
            print("✅ Webhook signature verification function working!")
            return True
        else:
            print(f"❌ Webhook verification error: {e}")
            return False

def print_testing_urls():
    """Print URLs for manual testing"""
    print("\n🌐 URLs for Manual Testing:")
    print("   📱 Local Development:")
    print("      - App: http://localhost:5000")
    print("      - Verse Selection: http://localhost:5000/vers-auswaehlen")
    print("      - Cart: http://localhost:5000/spendenkorb")
    print("      - Payment: http://localhost:5000/checkout/zahlung")
    print("      - Webhook: http://localhost:5000/stripe/webhook")
    
    print("\n   🔧 Stripe CLI Commands:")
    print("      - Listen: stripe listen --forward-to localhost:5000/stripe/webhook")
    print("      - Test Webhook: stripe trigger payment_intent.succeeded")
    print("      - Logs: stripe logs tail")

def print_manual_test_flow():
    """Print manual testing workflow"""
    print("\n📋 Manual Testing Workflow:")
    print("   1️⃣  Start Flask app: python app.py")
    print("   2️⃣  Start Stripe CLI: stripe listen --forward-to localhost:5000/stripe/webhook")
    print("   3️⃣  Navigate to: http://localhost:5000/vers-auswaehlen")
    print("   4️⃣  Add verse to cart")
    print("   5️⃣  Fill out donor data form")
    print("   6️⃣  Go to payment page")
    print("   7️⃣  Test SEPA payment with test IBAN")
    print("   8️⃣  Test card payment with 3DS test card")
    print("   9️⃣  Check webhook events in Stripe CLI")
    print("   🔟 Verify donation status in database")

def main():
    """Run all tests"""
    print("🧪 NGÜ Stripe Integration Test Suite")
    print("=" * 50)
    
    # Test configuration
    if not test_stripe_config():
        return
    
    # Test PaymentIntent creation
    if not test_payment_intent_creation():
        return
    
    # Test webhook verification
    test_webhook_signature_verification()
    
    # Print test data
    test_sepa_test_iban()
    test_3ds_test_cards()
    
    # Print testing instructions
    print_testing_urls()
    print_manual_test_flow()
    
    print("\n✅ All automated tests completed!")
    print("💡 Now proceed with manual testing using the payment forms.")

if __name__ == "__main__":
    main()