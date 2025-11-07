# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

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
    def create_payment_intent(cart_items, person, preferred_payment_methods=None, existing_donation_id=None, existing_payment_intent_id=None):
        """
        Create or update Stripe PaymentIntent with SEPA preference and 3D Secure support

        Args:
            cart_items: List of cart items with verse and donation data
            person: Person object with donor information
            preferred_payment_methods: List of preferred payment methods
            existing_donation_id: Optional existing donation ID to reuse
            existing_payment_intent_id: Optional existing payment intent ID to update

        Returns:
            dict: PaymentIntent data and related information
        """
        try:
            # Default payment methods with SEPA first
            if not preferred_payment_methods:
                preferred_payment_methods = ['sepa_debit', 'card']

            # Check if we should reuse existing donation and payment intent
            if existing_donation_id and existing_payment_intent_id:
                donation = Donation.query.get(existing_donation_id)

                # Only reuse if donation is still pending (not completed/failed)
                if donation and donation.payment_status == 'pending':
                    try:
                        # Try to retrieve existing PaymentIntent
                        payment_intent = stripe.PaymentIntent.retrieve(existing_payment_intent_id)

                        # Only update if PaymentIntent is not already succeeded/processing
                        if payment_intent.status in ['requires_payment_method', 'requires_confirmation', 'requires_action']:
                            logger.info(f"Reusing existing PaymentIntent {existing_payment_intent_id} and donation {existing_donation_id}")

                            # Update payment methods if changed
                            if set(payment_intent.payment_method_types) != set(preferred_payment_methods):
                                payment_intent = stripe.PaymentIntent.modify(
                                    existing_payment_intent_id,
                                    payment_method_types=preferred_payment_methods
                                )
                                logger.info(f"Updated PaymentIntent {existing_payment_intent_id} payment methods to {preferred_payment_methods}")

                            return {
                                'client_secret': payment_intent.client_secret,
                                'payment_intent_id': payment_intent.id,
                                'amount': payment_intent.amount,
                                'currency': 'eur',
                                'metadata': payment_intent.metadata,
                                'donation_id': donation.id,
                                'reused': True
                            }
                    except stripe.error.InvalidRequestError:
                        # PaymentIntent no longer valid, create new one
                        logger.warning(f"Could not retrieve PaymentIntent {existing_payment_intent_id}, creating new one")
                        pass

            # If we had an existing payment intent but couldn't reuse it, cancel the old one
            if existing_payment_intent_id:
                try:
                    old_payment_intent = stripe.PaymentIntent.retrieve(existing_payment_intent_id)
                    # Cancel if it's still cancelable (not already succeeded/canceled)
                    if old_payment_intent.status in ['requires_payment_method', 'requires_confirmation', 'requires_action']:
                        stripe.PaymentIntent.cancel(existing_payment_intent_id)
                        logger.info(f"Canceled superseded PaymentIntent {existing_payment_intent_id}")

                        # Also mark the old donation as canceled if it exists
                        if existing_donation_id:
                            old_donation = Donation.query.get(existing_donation_id)
                            if old_donation and old_donation.payment_status == 'pending':
                                old_donation.mark_failed("Superseded by new payment attempt")
                                db.session.commit()
                                logger.info(f"Marked superseded donation {existing_donation_id} as failed")
                except stripe.error.InvalidRequestError:
                    # PaymentIntent already gone, that's fine
                    pass
                except Exception as e:
                    logger.warning(f"Could not cancel old PaymentIntent {existing_payment_intent_id}: {e}")

            # Create new donation if needed
            donations = StripeService.create_donations_from_cart(cart_items, person.id)

            if not donations:
                raise StripeError("No valid donations could be created")

            # Calculate total amount from the consolidated donation
            total_amount = int(donations[0].total_amount * 100)  # Convert to cents for Stripe

            if total_amount <= 0:
                raise StripeError("Invalid donation amount")

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

            # Store Payment Intent ID immediately in database
            if donations[0].payment:
                donations[0].payment.stripe_payment_intent_id = payment_intent.id
                donations[0].payment.provider_transaction_id = payment_intent.id
                db.session.commit()
                logger.info(f"Stored Payment Intent ID for donation {donations[0].id}")

            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': total_amount,
                'currency': 'eur',
                'metadata': metadata,
                'donation_id': donations[0].id,
                'reused': False
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
        payment_intent_id = payment_intent.id
        
        try:
            # Get donation ID from metadata
            donation_id = payment_intent.metadata.get('donation_id')
            if not donation_id or not donation_id.isdigit():
                logger.error(f"No valid donation ID in PaymentIntent {payment_intent.id}")
                return False
            
            donation_id = int(donation_id)
            
            # Find donation by ID
            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status.in_(['pending', 'processing'])
            ).first()
            
            if not donation:
                logger.error(f"No pending donation found for PaymentIntent {payment_intent.id}")
                return False
            
            # Track verses before completion
            verse_ids_before = [va.verse_id for va in donation.verse_associations]
            
            # Start database transaction
            try:
                # Mark donation as completed
                donation.mark_completed()
                
                # Update payment transaction
                if donation.payment:
                    donation.payment.update_stripe_data(payment_intent)
                    donation.payment.mark_confirmed()
                
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
                
                logger.info(f"Successfully processed payment for donation {donation.id}")
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