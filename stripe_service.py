"""
Stripe Payment Service Module
Handles Stripe payment integration with SEPA Direct Debit and 3D Secure support
"""

import os
import stripe
from flask import current_app, request, session, url_for, has_request_context
from decimal import Decimal
from models import db, Person, Donation, PaymentTransaction, Verse
from datetime import datetime
import logging

# 🔧 DEBUG INFRASTRUCTURE FOR STRIPE - REMOVE AFTER DEBUGGING 🔧
import json

stripe_logger = logging.getLogger('debug_flow')

def stripe_debug_print(location, data, level="DEBUG"):
    """🔧 STRIPE PRINTF DEBUGGING - REMOVE AFTER DEBUGGING 🔧"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    message = f"[{timestamp}] [STRIPE-{level}] {location}: {json.dumps(data, default=str)}"
    print(f"💳 {message}")
    stripe_logger.info(message)

def stripe_strategic_log(operation, component, data, success=True):
    """🔧 STRIPE STRATEGIC LOGGING - CAN STAY LONGER 🔧"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'operation': operation,
        'component': f"stripe_{component}",
        'success': success,
        'data': data
    }
    stripe_logger.info(f"STRATEGIC: {json.dumps(log_entry)}")
    print(f"💳 STRIPE-STRATEGIC [{component}] {operation}: {'✅' if success else '❌'} - {data}")
# 🔧 END STRIPE DEBUG INFRASTRUCTURE 🔧

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

logger = logging.getLogger(__name__)


class StripeError(Exception):
    """Custom exception for Stripe-related errors"""
    pass


class StripeService:
    """Service class for Stripe payment operations"""
    
    @staticmethod
    def create_payment_intent(cart_items, person, preferred_payment_methods=None):
        """
        Create Stripe PaymentIntent with SEPA preference and 3D Secure support
        
        Args:
            cart_items: List of cart items with verse and donation data
            person: Person object with donor information
            preferred_payment_methods: List of preferred payment methods
            
        Returns:
            dict: PaymentIntent data and related information
        """
        try:
            # First, create donation records
            donations = StripeService.create_donations_from_cart(cart_items, person.id)
            
            if not donations:
                raise StripeError("No valid donations could be created")
            
            # Calculate total amount from the consolidated donation
            total_amount = int(donations[0].total_amount * 100)  # Convert to cents for Stripe
            
            if total_amount <= 0:
                raise StripeError("Invalid donation amount")
            
            # Default payment methods with SEPA first
            if not preferred_payment_methods:
                preferred_payment_methods = ['sepa_debit', 'card']
            
            # Prepare billing details using Person object
            billing_details = StripeService._prepare_billing_details_from_person(person)
            
            # Simplified metadata for single donation
            metadata = {
                'donation_id': str(donations[0].id),
                'verse_count': str(donations[0].verse_count)
            }
            
            # Create PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=total_amount,
                currency='eur',
                
                # Payment methods with SEPA preference
                payment_method_types=preferred_payment_methods,
                
                # Enhanced payment method options
                payment_method_options={
                    'card': {
                        'request_three_d_secure': 'any'  # Always require 3DS when possible
                    }
                    # SEPA handled automatically by Stripe (2025 API)
                },
                
                # Customer information
                receipt_email=person.email,
                description=f"NGÜ Bibelvers-Sponsoring: {donations[0].verse_count} Verse",
                
                # Metadata for webhook processing
                metadata=metadata
            )
            
            logger.info(f"PaymentIntent created: {payment_intent.id} for amount: €{total_amount/100:.2f}")
            
            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': total_amount,
                'currency': 'eur',
                'metadata': metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {e}")
            raise StripeError(f"Payment initialization failed: {e.user_message or str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating PaymentIntent: {e}")
            raise StripeError(f"Unexpected error during payment initialization: {str(e)}")
    
    @staticmethod
    def _prepare_billing_details_from_person(person):
        """Prepare billing details from Person object"""
        billing_details = {
            'name': f"{person.first_name or ''} {person.last_name or ''}".strip(),
            'email': person.email,
        }
        
        # Add address if available
        if person.street and person.city:
            billing_details['address'] = {
                'line1': f"{person.street or ''} {person.house_number or ''}".strip(),
                'city': person.city,
                'postal_code': person.postal_code,
                'country': (person.country or 'DE').upper()
            }
        
        return billing_details
    
    @staticmethod
    def create_donations_from_cart(cart_items, person_id):
        """
        Erstellt EINE Donation mit MEHREREN Versen
        
        Args:
            cart_items: List of cart items from session
            person_id: Person ID (required)
            
        Returns:
            list: Created Donation objects (single donation in list for compatibility)
        """
        try:
            person = Person.query.get(person_id)
            if not person:
                raise StripeError("Invalid person ID")
            
            # Gruppiere Cart-Items (alle Verse einer Person = eine Donation)
            verses_to_add = []
            total_amount = Decimal('0')
            
            for item in cart_items:
                verse = Verse.query.get(item['verse_id'])
                if not verse or verse.is_sponsored:
                    continue
                verses_to_add.append((verse, Decimal(str(item['amount']))))
                total_amount += Decimal(str(item['amount']))
            
            if not verses_to_add:
                raise StripeError("No valid verses to process")
            
            # EINE Donation für ALLE Verse
            item_data = cart_items[0].get('donor_data', {})  # Donor data ist für alle gleich
            
            donation = Donation(
                person_id=person.id,
                person_snapshot=person.to_snapshot(),
                verse_count=len(verses_to_add),
                total_amount=total_amount,
                currency='EUR',
                wants_receipt=item_data.get('wants_receipt', True),
                privacy_consent=True,
                payment_status='pending'
            )
            
            db.session.add(donation)
            db.session.flush()  # ID generieren
            
            # Verse zur Donation hinzufügen (ohne sofortige Sponsoring-Markierung)
            for verse, amount in verses_to_add:
                donation.add_verse(verse, amount)
                # Note: Verses will be marked as sponsored in mark_completed() after successful payment
            
            # Payment Transaction
            payment_transaction = PaymentTransaction(
                donation_id=donation.id,
                provider='stripe'
            )
            db.session.add(payment_transaction)
            
            db.session.commit()
            return [donation]  # Liste für Kompatibilität
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating donation from cart: {e}")
            raise StripeError(f"Failed to create donation: {str(e)}")
    
    @staticmethod
    def get_or_create_customer(person):
        """
        Get existing or create new Stripe Customer
        
        Args:
            person: Person object with donor information
            
        Returns:
            str: Stripe Customer ID or None
        """
        try:
            if not person.email:
                return None
            
            # Search for existing customer by email
            customers = stripe.Customer.list(email=person.email, limit=1)
            
            if customers.data:
                logger.info(f"Found existing Stripe customer: {customers.data[0].id}")
                return customers.data[0].id
            
            # Create new customer
            customer_data = {
                'email': person.email,
                'name': f"{person.first_name or ''} {person.last_name or ''}".strip(),
                'metadata': {
                    'source': 'ngue_bible_sponsoring',
                    'created_at': datetime.utcnow().isoformat()
                }
            }
            
            # Add address if available
            if person.street and person.city:
                customer_data['address'] = {
                    'line1': f"{person.street or ''} {person.house_number or ''}".strip(),
                    'city': person.city,
                    'postal_code': person.postal_code,
                    'country': (person.country or 'DE').upper()
                }
            
            customer = stripe.Customer.create(**customer_data)
            logger.info(f"Created new Stripe customer: {customer.id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.warning(f"Failed to create/retrieve Stripe customer: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error managing Stripe customer: {e}")
            return None
    
    @staticmethod
    def handle_successful_payment(payment_intent):
        """
        Handle successful payment from webhook
        
        Args:
            payment_intent: Stripe PaymentIntent object
        """
        # 🔧 DEBUG POINT 8 + STRATEGIC LOGGING 3: Stripe Webhook → Database 🔧
        payment_intent_id = payment_intent.id
        
        stripe_debug_print("WEBHOOK_SUCCESS_START", {
            'payment_intent_id': payment_intent_id,
            'amount': payment_intent.get('amount', 0),
            'currency': payment_intent.get('currency', 'unknown'),
            'metadata': payment_intent.get('metadata', {})
        })
        
        stripe_strategic_log("webhook_payment_success", "webhook", {
            'payment_intent_id': payment_intent_id,
            'amount_cents': payment_intent.get('amount', 0),
            'payment_method': payment_intent.get('payment_method_types', [])
        })
        
        try:
            # Get donation ID from metadata
            donation_id = payment_intent.metadata.get('donation_id')
            if not donation_id or not donation_id.isdigit():
                stripe_debug_print("WEBHOOK_NO_DONATION_ID", {
                    'payment_intent_id': payment_intent_id,
                    'metadata': payment_intent.get('metadata', {}),
                    'error': 'missing_or_invalid_donation_id'
                }, level="ERROR")
                
                stripe_strategic_log("webhook_donation_lookup_failed", "webhook", {
                    'payment_intent_id': payment_intent_id,
                    'error': 'no_donation_id_in_metadata'
                }, success=False)
                
                logger.error(f"No valid donation ID in PaymentIntent {payment_intent.id}")
                return False
            
            donation_id = int(donation_id)
            stripe_debug_print("WEBHOOK_DONATION_LOOKUP", {
                'payment_intent_id': payment_intent_id,
                'donation_id': donation_id
            })
            
            # Find donation by ID
            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status.in_(['pending', 'processing'])
            ).first()
            
            if not donation:
                stripe_debug_print("WEBHOOK_DONATION_NOT_FOUND", {
                    'payment_intent_id': payment_intent_id,
                    'donation_id': donation_id,
                    'error': 'donation_not_found_or_wrong_status'
                }, level="ERROR")
                
                stripe_strategic_log("donation_not_found", "webhook", {
                    'payment_intent_id': payment_intent_id,
                    'donation_id': donation_id
                }, success=False)
                
                logger.error(f"No pending donation found for PaymentIntent {payment_intent.id}")
                return False
            
            # Track verses before completion
            verse_ids_before = [va.verse_id for va in donation.verse_associations]
            stripe_debug_print("WEBHOOK_DONATION_FOUND", {
                'donation_id': donation.id,
                'person_email_domain': donation.person.email.split('@')[1] if donation.person and donation.person.email else 'unknown',
                'verse_count': len(verse_ids_before),
                'verse_ids': verse_ids_before,
                'current_status': donation.payment_status
            })
            
            # Start database transaction
            try:
                # Mark donation as completed
                donation.mark_completed()
                
                stripe_debug_print("DONATION_MARKED_COMPLETE", {
                    'donation_id': donation.id,
                    'new_status': donation.payment_status
                })
                
                # Update payment transaction
                if donation.payment:
                    donation.payment.update_stripe_data(payment_intent)
                    donation.payment.mark_confirmed()
                    
                    stripe_debug_print("PAYMENT_TRANSACTION_UPDATED", {
                        'donation_id': donation.id,
                        'payment_transaction_updated': True
                    })
                
                # Track verse sponsorship changes
                verses_sponsored = []
                for verse_assoc in donation.verse_associations:
                    verse = verse_assoc.verse
                    if verse.is_sponsored:
                        verses_sponsored.append({
                            'verse_id': verse.id,
                            'reference': verse.reference,
                            'sponsored_at': verse.sponsored_at.isoformat() if verse.sponsored_at else None
                        })
                
                db.session.commit()
                
                stripe_debug_print("WEBHOOK_SUCCESS_COMPLETE", {
                    'donation_id': donation.id,
                    'verses_sponsored': verses_sponsored,
                    'database_committed': True
                })
                
                stripe_strategic_log("donation_completed_successfully", "webhook", {
                    'donation_id': donation.id,
                    'payment_intent_id': payment_intent_id,
                    'verses_sponsored': len(verses_sponsored),
                    'person_email_domain': donation.person.email.split('@')[1] if donation.person.email else 'unknown'
                }, success=True)
                
                logger.info(f"Successfully processed payment for donation {donation.id}")
                return True
                
            except Exception as e:
                db.session.rollback()
                
                stripe_debug_print("WEBHOOK_DATABASE_ERROR", {
                    'donation_id': donation.id,
                    'error': str(e),
                    'action': 'rollback_performed'
                }, level="ERROR")
                
                stripe_strategic_log("donation_completion_failed", "webhook", {
                    'donation_id': donation.id,
                    'payment_intent_id': payment_intent_id,
                    'error': str(e)
                }, success=False)
                
                logger.error(f"Database error processing successful payment: {e}")
                raise
                
        except Exception as e:
            stripe_debug_print("WEBHOOK_GENERAL_ERROR", {
                'payment_intent_id': payment_intent_id,
                'error': str(e)
            }, level="ERROR")
            
            stripe_strategic_log("webhook_processing_failed", "webhook", {
                'payment_intent_id': payment_intent_id,
                'error': str(e)
            }, success=False)
            
            logger.error(f"Error handling successful payment: {e}")
            return False
    
    @staticmethod
    def handle_failed_payment(payment_intent):
        """
        Handle failed payment from webhook
        
        Args:
            payment_intent: Stripe PaymentIntent object
        """
        try:
            # Get donation ID from metadata
            donation_id = payment_intent.metadata.get('donation_id')
            if not donation_id or not donation_id.isdigit():
                logger.error(f"No valid donation ID in failed PaymentIntent {payment_intent.id}")
                return False
            donation_id = int(donation_id)
            
            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status.in_(['pending', 'processing'])
            ).first()
            
            if not donation:
                logger.error(f"No pending donation found for failed PaymentIntent {payment_intent.id}")
                return False
            
            error_message = "Payment failed"
            if hasattr(payment_intent, 'last_payment_error') and payment_intent.last_payment_error:
                error_message = payment_intent.last_payment_error.get('message', error_message)
            
            donation.mark_failed(error_message)
            
            if donation.payment:
                donation.payment.update_stripe_data(payment_intent)
                donation.payment.mark_failed(error_message)
            
            db.session.commit()
            logger.info(f"Marked donation {donation.id} as failed")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling failed payment: {e}")
            return False
    
    @staticmethod
    def handle_processing_payment(payment_intent):
        """
        Handle payment in processing state (typically SEPA)
        
        Args:
            payment_intent: Stripe PaymentIntent object
        """
        try:
            # Get donation ID from metadata
            donation_id = payment_intent.metadata.get('donation_id')
            if not donation_id or not donation_id.isdigit():
                logger.error(f"No valid donation ID in processing PaymentIntent {payment_intent.id}")
                return False
            donation_id = int(donation_id)
            
            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status == 'pending'
            ).first()
            
            if not donation:
                logger.error(f"No pending donation found for processing PaymentIntent {payment_intent.id}")
                return False
            
            donation.payment_status = 'processing'
            
            if donation.payment:
                donation.payment.update_stripe_data(payment_intent)
            
            db.session.commit()
            logger.info(f"Marked donation {donation.id} as processing (SEPA)")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling processing payment: {e}")
            return False
    
    @staticmethod
    def verify_webhook_signature(payload, signature, webhook_secret):
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Raw request payload
            signature: Stripe-Signature header
            webhook_secret: Webhook endpoint secret
            
        Returns:
            dict: Verified event object
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event
        except ValueError:
            raise StripeError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise StripeError("Invalid signature")
    
    @staticmethod
    def handle_webhook_event(event):
        """
        Main webhook event handler
        
        Args:
            event: Stripe webhook event
            
        Returns:
            bool: Success status
        """
        event_type = event['type']
        payment_intent = event['data']['object']
        
        logger.info(f"Processing webhook event: {event_type} for PaymentIntent: {payment_intent.get('id')}")
        
        if event_type == 'payment_intent.succeeded':
            return StripeService.handle_successful_payment(payment_intent)
        
        elif event_type == 'payment_intent.payment_failed':
            return StripeService.handle_failed_payment(payment_intent)
        
        elif event_type == 'payment_intent.processing':
            return StripeService.handle_processing_payment(payment_intent)
        
        elif event_type == 'payment_intent.requires_action':
            # 3D Secure or other action required - usually handled on frontend
            # For SEPA, this might indicate additional verification needed
            logger.info(f"PaymentIntent {payment_intent.get('id')} requires action")
            return StripeService.handle_requires_action_payment(payment_intent)
        
        elif event_type == 'payment_intent.canceled':
            # Payment was canceled (could be SEPA cancellation)
            return StripeService.handle_canceled_payment(payment_intent)
        
        elif event_type == 'charge.dispute.created':
            # Handle SEPA chargeback/dispute
            return StripeService.handle_chargeback(event['data']['object'])
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return True
    
    @staticmethod
    def handle_chargeback(charge):
        """
        Handle chargeback/dispute (mainly for SEPA)
        
        Args:
            charge: Stripe Charge object with dispute
        """
        try:
            payment_intent_id = charge.get('payment_intent')
            if not payment_intent_id:
                return False
            
            # Find payment transaction
            payment = PaymentTransaction.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment and payment.donation:
                # Mark all verses as available again
                for verse_assoc in payment.donation.verse_associations:
                    verse_assoc.verse.is_sponsored = False
                payment.donation.payment_status = 'disputed'
                
                # Log the dispute
                logger.warning(f"Chargeback for donation {payment.donation.id}, verses: {', '.join([va.verse.reference for va in payment.donation.verse_associations])}")
                
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling chargeback: {e}")
            return False
    
    @staticmethod
    def handle_requires_action_payment(payment_intent):
        """
        Handle payment that requires additional action (3DS, SEPA verification, etc.)
        
        Args:
            payment_intent: Stripe PaymentIntent object
        """
        try:
            # Get donation ID from metadata
            donation_id = payment_intent.metadata.get('donation_id')
            if not donation_id or not donation_id.isdigit():
                logger.error(f"No valid donation ID in requires_action PaymentIntent {payment_intent.id}")
                return False
            donation_id = int(donation_id)
            
            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status.in_(['pending', 'processing'])
            ).first()
            
            if not donation:
                logger.error(f"No pending donation found for requires_action PaymentIntent {payment_intent.id}")
                return False
            
            # Keep status as processing for now - user needs to complete action
            if donation.payment_status == 'pending':
                donation.payment_status = 'processing'
            
            if donation.payment:
                donation.payment.update_stripe_data(payment_intent)
            
            db.session.commit()
            logger.info(f"Updated donation {donation.id} requiring action")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling requires_action payment: {e}")
            return False
    
    @staticmethod
    def handle_canceled_payment(payment_intent):
        """
        Handle canceled payment (user canceled or SEPA declined)
        
        Args:
            payment_intent: Stripe PaymentIntent object
        """
        try:
            # Get donation ID from metadata
            donation_id = payment_intent.metadata.get('donation_id')
            if not donation_id or not donation_id.isdigit():
                logger.error(f"No valid donation ID in canceled PaymentIntent {payment_intent.id}")
                return False
            donation_id = int(donation_id)
            
            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status.in_(['pending', 'processing'])
            ).first()
            
            if not donation:
                logger.error(f"No pending donation found for canceled PaymentIntent {payment_intent.id}")
                return False
            
            cancellation_reason = payment_intent.cancellation_reason or 'canceled'
            error_message = f"Payment canceled: {cancellation_reason}"
            
            donation.mark_failed(error_message)
            
            if donation.payment:
                donation.payment.update_stripe_data(payment_intent)
                donation.payment.mark_failed(error_message)
            
            db.session.commit()
            logger.info(f"Marked donation {donation.id} as canceled/failed")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling canceled payment: {e}")
            return False