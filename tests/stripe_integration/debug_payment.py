#!/usr/bin/env python3
"""
Debug script for payment errors
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
import logging

def setup_debug_logging():
    """Enable detailed logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable Flask debug logging
    app.logger.setLevel(logging.DEBUG)
    
    # Enable Stripe logging
    stripe_logger = logging.getLogger('stripe')
    stripe_logger.setLevel(logging.DEBUG)
    
    print("🔍 Debug logging enabled!")
    print("🔍 Check console output for detailed errors")

def print_debug_info():
    """Print debug information"""
    print("\n🔧 Debug Information:")
    print(f"   - Flask Debug Mode: {app.debug}")
    print(f"   - Stripe Public Key: {os.environ.get('STRIPE_PUBLIC_KEY', 'NOT SET')[:20]}...")
    print(f"   - Stripe Secret Key: {os.environ.get('STRIPE_SECRET_KEY', 'NOT SET')[:20]}...")
    print(f"   - Webhook Secret: {os.environ.get('STRIPE_WEBHOOK_SECRET', 'NOT SET')[:20]}...")
    
    print("\n🌐 URLs to test:")
    print("   - Cart: http://localhost:5000/spendenkorb")
    print("   - Payment: http://localhost:5000/checkout/zahlung")
    print("   - PaymentIntent API: http://localhost:5000/checkout/create-payment-intent")

if __name__ == "__main__":
    setup_debug_logging()
    print_debug_info()
    
    print("\n🚀 Starting Flask in DEBUG mode...")
    print("   Press Ctrl+C to stop")
    print("   Watch this console for error messages!")
    
    # Start Flask with debug enabled
    app.run(debug=True, port=5000, host='0.0.0.0')