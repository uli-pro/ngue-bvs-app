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

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

logger = logging.getLogger(__name__)


class StripeError(Exception):
    """Custom exception for Stripe-related errors"""
    pass


class StripeService:
    """Service class for Stripe payment operations"""
    
    @staticmethod
    def create_payment_intent(cart_items, donor_data, preferred_payment_methods=None):
        """
        Create Stripe PaymentIntent with SEPA preference and 3D Secure support
        
        Args:
            cart_items: List of cart items with verse and donation data
            donor_data: Donor information from session
            preferred_payment_methods: List of preferred payment methods
            
        Returns:
            dict: PaymentIntent data and related information
        """
        try:
            # First, create donation records
            donations = StripeService.create_donations_from_cart(cart_items)
            
            if not donations:
                raise StripeError("No valid donations could be created")
            
            # Calculate total amount (all verses are €100 each)
            total_amount = len(donations) * 100 * 100  # Convert to cents for Stripe
            
            if total_amount <= 0:
                raise StripeError("Invalid donation amount")
            
            # Default payment methods with SEPA first
            if not preferred_payment_methods:
                preferred_payment_methods = ['sepa_debit', 'card']
            
            # Prepare billing details
            billing_details = StripeService._prepare_billing_details(donor_data)
            
            # Prepare metadata for tracking (use donation IDs instead of cart items)
            donation_ids = [str(d.id) for d in donations]
            verse_ids = [str(d.verse_id) for d in donations]
            
            metadata = {
                'donation_ids': ','.join(donation_ids),
                'verse_ids': ','.join(verse_ids),
                'verse_count': str(len(donations)),
                'donor_email': donor_data.get('email', ''),
                'session_id': session.get('session_id', ''),
                'project': 'ngue_bible_sponsoring',
                'version': '1.0'
            }
            
            # Add donation type info
            if donations:
                metadata['donation_type'] = donations[0].donation_type
            
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
                receipt_email=donor_data.get('email'),
                description=f"NGÜ Bibelvers-Sponsoring: {len(donations)} Verse",
                
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
    def _prepare_billing_details(donor_data):
        """Prepare billing details from donor data"""
        billing_details = {
            'name': f"{donor_data.get('first_name', '')} {donor_data.get('last_name', '')}".strip(),
            'email': donor_data.get('email'),
        }
        
        # Add address if available
        if donor_data.get('street') and donor_data.get('city'):
            billing_details['address'] = {
                'line1': f"{donor_data.get('street', '')} {donor_data.get('house_number', '')}".strip(),
                'city': donor_data.get('city'),
                'postal_code': donor_data.get('postal_code'),
                'country': donor_data.get('country', 'DE').upper()
            }
        
        return billing_details
    
    @staticmethod
    def _prepare_metadata(cart_items, donor_data):
        """Prepare metadata for PaymentIntent"""
        verse_ids = [str(item.get('verse_id')) for item in cart_items]
        
        metadata = {
            'verse_ids': ','.join(verse_ids),
            'verse_count': str(len(cart_items)),
            'donor_email': donor_data.get('email', ''),
            'session_id': session.get('session_id', ''),
            'project': 'ngue_bible_sponsoring',
            'version': '1.0'
        }
        
        # Add donation type info
        if cart_items:
            first_item = cart_items[0]
            metadata['donation_type'] = first_item.get('donation_type', 'einzelperson')
        
        return metadata
    
    @staticmethod
    def create_donations_from_cart(cart_items):
        """
        Create Donation records from cart items using new Person/Donation structure
        
        Args:
            cart_items: List of cart items from session
            
        Returns:
            list: Created Donation objects
        """
        donations = []
        
        try:
            for item in cart_items:
                # Get verse
                verse = Verse.query.get(item['verse_id'])
                if not verse or verse.is_sponsored:
                    continue
                
                donor_data = item['donor_data']
                donation_type = item['donation_type']
                
                # Create or find person
                person = Person.find_or_create(
                    email=donor_data.get('email'),
                    first_name=donor_data.get('first_name'),
                    last_name=donor_data.get('last_name'),
                    salutation=donor_data.get('salutation'),
                    title=donor_data.get('title'),
                    street=donor_data.get('street'),
                    house_number=donor_data.get('house_number'),
                    postal_code=donor_data.get('postal_code'),
                    city=donor_data.get('city'),
                    country=donor_data.get('country', 'DE'),
                    newsletter_opt_in=donor_data.get('newsletter', False)
                )
                
                # Commit person to get ID
                db.session.commit()
                
                # Prepare donation_details based on type
                donation_details = {}
                if donation_type == 'gruppe':
                    donation_details = {
                        'group_name': donor_data.get('group_name'),
                        'group_article': donor_data.get('group_article')
                    }
                elif donation_type == 'geschenk':
                    donation_details = {
                        'recipient_name': donor_data.get('gift_recipient_name'),
                        'recipient_email': donor_data.get('gift_recipient_email'),
                        'gift_message': donor_data.get('gift_message'),
                        'direct_send': donor_data.get('gift_direct_send', False)
                    }
                
                # Create donation record with new structure
                donation = Donation(
                    person_id=person.id,
                    verse_id=verse.id,
                    donation_type=donation_type,
                    donation_details=donation_details,
                    person_snapshot=person.to_snapshot(),
                    amount=Decimal(str(item['amount'])),
                    currency=item.get('currency', 'EUR'),
                    wants_receipt=donor_data.get('wants_receipt', True),
                    privacy_consent=donor_data.get('privacy_consent', True),
                    payment_status='pending'
                )
                
                db.session.add(donation)
                donations.append(donation)
            
            # Commit all donations
            db.session.commit()
            
            # Create payment transactions
            for donation in donations:
                payment_transaction = PaymentTransaction(
                    donation_id=donation.id,
                    provider='stripe'
                )
                db.session.add(payment_transaction)
                donation.payment = payment_transaction
            
            db.session.commit()
            return donations
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating donations from cart: {e}")
            raise StripeError(f"Failed to create donation records: {str(e)}")
    
    @staticmethod
    def get_or_create_customer(donor_data):
        """
        Get existing or create new Stripe Customer
        
        Args:
            donor_data: Donor information
            
        Returns:
            str: Stripe Customer ID or None
        """
        try:
            email = donor_data.get('email')
            if not email:
                return None
            
            # Search for existing customer by email
            customers = stripe.Customer.list(email=email, limit=1)
            
            if customers.data:
                logger.info(f"Found existing Stripe customer: {customers.data[0].id}")
                return customers.data[0].id
            
            # Create new customer
            customer_data = {
                'email': email,
                'name': f"{donor_data.get('first_name', '')} {donor_data.get('last_name', '')}".strip(),
                'metadata': {
                    'source': 'ngue_bible_sponsoring',
                    'created_at': datetime.utcnow().isoformat()
                }
            }
            
            # Add address if available
            if donor_data.get('street') and donor_data.get('city'):
                customer_data['address'] = {
                    'line1': f"{donor_data.get('street', '')} {donor_data.get('house_number', '')}".strip(),
                    'city': donor_data.get('city'),
                    'postal_code': donor_data.get('postal_code'),
                    'country': donor_data.get('country', 'DE').upper()
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
        try:
            # Get donation IDs from metadata
            donation_ids = payment_intent.metadata.get('donation_ids', '').split(',')
            donation_ids = [int(did) for did in donation_ids if did.isdigit()]
            
            if not donation_ids:
                logger.error(f"No valid donation IDs in PaymentIntent {payment_intent.id}")
                return False
            
            # Find donations by donation IDs
            donations = Donation.query.filter(
                Donation.id.in_(donation_ids),
                Donation.payment_status.in_(['pending', 'processing'])
            ).all()
            
            if not donations:
                logger.error(f"No pending donations found for PaymentIntent {payment_intent.id}")
                return False
            
            # Start database transaction
            try:
                # Mark all donations as completed
                for donation in donations:
                    donation.mark_completed()
                    
                    # Update payment transaction
                    if donation.payment:
                        donation.payment.update_stripe_data(payment_intent)
                        donation.payment.mark_confirmed()
                
                db.session.commit()
                
                logger.info(f"Successfully processed payment for {len(donations)} donations")
                return True
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error processing successful payment: {e}")
                raise
                
        except Exception as e:
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
            # Get donation IDs from metadata
            donation_ids = payment_intent.metadata.get('donation_ids', '').split(',')
            donation_ids = [int(did) for did in donation_ids if did.isdigit()]
            
            if not donation_ids:
                logger.error(f"No valid donation IDs in failed PaymentIntent {payment_intent.id}")
                return False
            
            donations = Donation.query.filter(
                Donation.id.in_(donation_ids),
                Donation.payment_status.in_(['pending', 'processing'])
            ).all()
            
            error_message = "Payment failed"
            if hasattr(payment_intent, 'last_payment_error') and payment_intent.last_payment_error:
                error_message = payment_intent.last_payment_error.get('message', error_message)
            
            for donation in donations:
                donation.mark_failed(error_message)
                
                if donation.payment:
                    donation.payment.update_stripe_data(payment_intent)
                    donation.payment.mark_failed(error_message)
            
            db.session.commit()
            logger.info(f"Marked {len(donations)} donations as failed")
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
            # Get donation IDs from metadata
            donation_ids = payment_intent.metadata.get('donation_ids', '').split(',')
            donation_ids = [int(did) for did in donation_ids if did.isdigit()]
            
            if not donation_ids:
                logger.error(f"No valid donation IDs in processing PaymentIntent {payment_intent.id}")
                return False
            
            donations = Donation.query.filter(
                Donation.id.in_(donation_ids),
                Donation.payment_status == 'pending'
            ).all()
            
            for donation in donations:
                donation.payment_status = 'processing'
                
                if donation.payment:
                    donation.payment.update_stripe_data(payment_intent)
            
            db.session.commit()
            logger.info(f"Marked {len(donations)} donations as processing (SEPA)")
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
                # Mark verse as available again
                payment.donation.verse.is_sponsored = False
                payment.donation.payment_status = 'disputed'
                
                # Log the dispute
                logger.warning(f"Chargeback for donation {payment.donation.id}, verse {payment.donation.verse.reference}")
                
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
            # Get donation IDs from metadata
            donation_ids = payment_intent.metadata.get('donation_ids', '').split(',')
            donation_ids = [int(did) for did in donation_ids if did.isdigit()]
            
            if not donation_ids:
                logger.error(f"No valid donation IDs in requires_action PaymentIntent {payment_intent.id}")
                return False
            
            donations = Donation.query.filter(
                Donation.id.in_(donation_ids),
                Donation.payment_status.in_(['pending', 'processing'])
            ).all()
            
            for donation in donations:
                # Keep status as processing for now - user needs to complete action
                if donation.payment_status == 'pending':
                    donation.payment_status = 'processing'
                
                if donation.payment:
                    donation.payment.update_stripe_data(payment_intent)
            
            db.session.commit()
            logger.info(f"Updated {len(donations)} donations requiring action")
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
            # Get donation IDs from metadata
            donation_ids = payment_intent.metadata.get('donation_ids', '').split(',')
            donation_ids = [int(did) for did in donation_ids if did.isdigit()]
            
            if not donation_ids:
                logger.error(f"No valid donation IDs in canceled PaymentIntent {payment_intent.id}")
                return False
            
            donations = Donation.query.filter(
                Donation.id.in_(donation_ids),
                Donation.payment_status.in_(['pending', 'processing'])
            ).all()
            
            cancellation_reason = payment_intent.cancellation_reason or 'canceled'
            error_message = f"Payment canceled: {cancellation_reason}"
            
            for donation in donations:
                donation.mark_failed(error_message)
                
                if donation.payment:
                    donation.payment.update_stripe_data(payment_intent)
                    donation.payment.mark_failed(error_message)
            
            db.session.commit()
            logger.info(f"Marked {len(donations)} donations as canceled/failed")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling canceled payment: {e}")
            return False