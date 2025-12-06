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
from typing import Optional, Dict, Any


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
                'verse_count': str(donations[0].verse_count),
                'source': 'ngue-bvs-app'  # Identifiziert Zahlungen von dieser App
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
        Handle successful payment from webhook.

        Two scenarios:
        1. Card payment (immediate): certificate_sent_at is NULL
           → Mark completed, generate PDFs, send email

        2. SEPA payment (delayed, after processing): certificate_sent_at is set
           → Just update status to 'completed', no email (already sent at processing)

        Args:
            payment_intent: Stripe PaymentIntent object (dict from webhook)

        Returns:
            bool: True if processing successful
        """
        payment_intent_id = payment_intent.get('id')

        try:
            # Get donation ID from metadata
            donation_id = payment_intent.get('metadata', {}).get('donation_id')
            if not donation_id or not str(donation_id).isdigit():
                # No donation_id means this PaymentIntent is not from our app (e.g., RaiseNow)
                logger.info(f"PaymentIntent {payment_intent_id} has no donation_id - not from this app, ignoring")
                return True

            donation_id = int(donation_id)

            # Find donation by ID (allow pending, processing, or already completed for idempotency)
            donation = Donation.query.filter(
                Donation.id == donation_id
            ).first()

            if not donation:
                logger.error(f"Donation {donation_id} not found for PaymentIntent {payment_intent_id}")
                return False

            # Idempotency: Already completed? Just return success
            if donation.payment_status == 'completed':
                logger.info(f"Donation {donation.id} already completed, skipping")
                return True

            # Check if this was already fulfilled during 'processing' (SEPA Optimistic Completion)
            already_fulfilled = donation.certificate_sent_at is not None

            try:
                if already_fulfilled:
                    # SEPA: Certificate was already sent at 'processing'
                    # Just finalize the status
                    donation.payment_status = 'completed'
                    donation.completed_at = datetime.utcnow()

                    if donation.payment:
                        donation.payment.update_stripe_data(payment_intent)
                        donation.payment.mark_confirmed()

                    db.session.commit()
                    logger.info(
                        f"Donation {donation.id} finalized (SEPA): status → completed "
                        f"(certificate was sent at {donation.certificate_sent_at})"
                    )
                else:
                    # Card payment (or SEPA that somehow missed processing event)
                    # Full flow: mark completed, generate PDFs, send email
                    donation.mark_completed()

                    if donation.payment:
                        donation.payment.update_stripe_data(payment_intent)
                        # mark_confirmed() already called by mark_completed()

                    db.session.commit()
                    logger.info(f"Donation {donation.id} marked as completed (card payment)")

                    # Generate PDFs and send email
                    try:
                        StripeService._fulfill_donation(donation)
                    except Exception as e:
                        logger.error(f"Error fulfilling donation {donation.id}: {e}")
                        StripeService._send_admin_alert_for_fulfillment_error(donation, str(e))

                # Sync to HubSpot CRM (runs for both SEPA and card, after payment_status='completed')
                # Non-blocking: don't fail the webhook if HubSpot fails
                try:
                    from hubspot_service import HubSpotService
                    hubspot_result = HubSpotService.sync_donation(donation)
                    if hubspot_result['success']:
                        logger.info(f"HubSpot sync successful for donation {donation.id}")
                    else:
                        error_msg = hubspot_result.get('error', 'Unknown error')
                        logger.warning(f"HubSpot sync failed for donation {donation.id}: {error_msg}")
                        StripeService._send_admin_alert_for_hubspot_error(donation, error_msg)
                except Exception as e:
                    logger.error(f"HubSpot sync error for donation {donation.id}: {e}")
                    StripeService._send_admin_alert_for_hubspot_error(donation, str(e))

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
        Handle failed payment from webhook.

        Two scenarios:
        1. Immediate failure (card): certificate_sent_at is NULL
           → Release verses, NO email (user sees error in UI and can retry)

        2. Delayed failure (SEPA, after processing): certificate_sent_at is set
           → Release verses, generate Storno-PDF, send Storno-Email, notify admin

        Args:
            payment_intent: Stripe PaymentIntent object (dict from webhook)

        Returns:
            bool: True if processing successful
        """
        payment_intent_id = payment_intent.get('id')

        try:
            # Get donation ID from metadata
            donation_id = payment_intent.get('metadata', {}).get('donation_id')
            if not donation_id or not str(donation_id).isdigit():
                # No donation_id means this PaymentIntent is not from our app (e.g., RaiseNow)
                logger.info(f"Failed PaymentIntent {payment_intent_id} has no donation_id - not from this app, ignoring")
                return True

            donation_id = int(donation_id)

            # Find donation (allow pending, processing, or already failed for idempotency)
            donation = Donation.query.filter(
                Donation.id == donation_id
            ).first()

            if not donation:
                logger.error(f"Donation {donation_id} not found for failed PaymentIntent {payment_intent_id}")
                return False

            # Idempotency: Already failed? Just return success
            if donation.payment_status == 'failed':
                logger.info(f"Donation {donation.id} already failed, skipping")
                return True

            # Only process if pending or processing
            if donation.payment_status not in ('pending', 'processing'):
                logger.warning(
                    f"Donation {donation.id} has unexpected status {donation.payment_status} "
                    f"for failed PaymentIntent {payment_intent_id}"
                )
                return False

            # Extract error message from Stripe
            error_message = "Payment failed"
            last_payment_error = payment_intent.get('last_payment_error')
            if last_payment_error:
                error_message = last_payment_error.get('message', error_message)

            # Check if this is a delayed failure (SEPA) or immediate failure (card)
            # Delayed failure = certificate was already sent during 'processing'
            is_delayed_failure = donation.certificate_sent_at is not None

            try:
                # 1. Mark donation as failed (releases verses via mark_failed)
                donation.mark_failed(error_message)

                if donation.payment:
                    donation.payment.update_stripe_data(payment_intent)
                    donation.payment.mark_failed(error_message)

                db.session.commit()
                logger.info(
                    f"Marked donation {donation.id} as failed "
                    f"({'delayed SEPA' if is_delayed_failure else 'immediate card'})"
                )

                # 2. Send appropriate notification (outside main transaction)
                try:
                    if is_delayed_failure:
                        # SEPA: Certificate was already sent → Storno flow
                        StripeService._handle_storno_notification(donation, error_message)
                    else:
                        # Card/immediate failure: User sees error in UI, can retry
                        # KEINE Email an User - nur Logging
                        logger.info(
                            f"Immediate payment failure for donation {donation.id}, "
                            f"no email sent (user can retry on payment page)"
                        )
                except Exception as e:
                    logger.error(f"Error sending failure notification for donation {donation.id}: {e}")
                    # Continue - donation is already marked as failed

                # 3. Send admin alert only for delayed failures (certificates already sent)
                if is_delayed_failure:
                    try:
                        StripeService._send_admin_alert_for_payment_failure(
                            donation, error_message, is_delayed_failure
                        )
                    except Exception as e:
                        logger.error(f"Error sending admin alert for donation {donation.id}: {e}")

                return True

            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error processing failed payment: {e}")
                raise

        except Exception as e:
            logger.error(f"Error handling failed payment: {e}")
            return False

    @staticmethod
    def _handle_failure_notification(donation: Donation, error_message: str):
        """
        Send simple failure email for immediate failures (card).

        No certificate was ever sent, so no Storno needed.

        Args:
            donation: Donation object (already marked as failed)
            error_message: Human-readable error from Stripe
        """
        from email_service import email_service

        try:
            donation_data = StripeService._prepare_donation_data(donation)

            # Map Stripe error to German user-friendly message
            failure_reason = StripeService._translate_stripe_error(error_message)

            email_sent = email_service.send_payment_failed_email(
                donation_data,
                failure_reason
            )

            if email_sent:
                logger.info(f"Payment failed email sent for donation {donation.id}")
            else:
                logger.error(f"Failed to send payment failed email for donation {donation.id}")

        except Exception as e:
            logger.error(f"Error in _handle_failure_notification for donation {donation.id}: {e}")
            raise

    @staticmethod
    def _handle_storno_notification(donation: Donation, error_message: str):
        """
        Generate Storno-PDF and send Storno-Email for delayed failures (SEPA).

        Certificate was already sent, so we need to formally cancel it.

        Args:
            donation: Donation object (already marked as failed)
            error_message: Human-readable error from Stripe
        """
        from pdf_service import PDFGeneratorService
        from email_service import email_service

        try:
            # Translate error to German
            cancellation_reason = StripeService._translate_stripe_error(error_message)

            # 1. Generate Storno-PDF
            pdf_service = PDFGeneratorService(current_app._get_current_object())
            storno_pdf_path = pdf_service.generate_storno_certificate(
                donation.id,
                cancellation_reason=cancellation_reason
            )

            if not storno_pdf_path:
                logger.error(f"Failed to generate storno PDF for donation {donation.id}")
                # Continue without PDF - at least try to send email
                return

            # 2. Get storno context for email (reuse pdf_service method)
            storno_context = pdf_service._prepare_storno_context(donation, cancellation_reason)

            # 3. Send Storno-Email with PDF attachment
            donation_data = StripeService._prepare_donation_data(donation)

            email_sent = email_service.send_storno_email(
                donation_data,
                storno_pdf_path,
                storno_context
            )

            if email_sent:
                # Mark storno as sent
                donation.storno_sent_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Storno email sent for donation {donation.id}")
            else:
                logger.error(f"Failed to send storno email for donation {donation.id}")

        except Exception as e:
            logger.error(f"Error in _handle_storno_notification for donation {donation.id}: {e}")
            raise

    @staticmethod
    def _send_admin_alert_for_payment_failure(donation: Donation, error_message: str,
                                               is_delayed: bool):
        """Send admin alert for payment failure."""
        from email_service import email_service

        failure_type = "SEPA-Lastschrift (verzögert)" if is_delayed else "Kartenzahlung (sofort)"

        try:
            email_service.send_admin_alert(
                subject=f"Zahlung fehlgeschlagen: Donation #{donation.id} ({failure_type})",
                message=f"Eine Zahlung ist fehlgeschlagen für Donation #{donation.id}.",
                error_details=error_message,
                context={
                    'donation_id': donation.id,
                    'payment_status': donation.payment_status,
                    'failure_type': failure_type,
                    'user_email': donation.person.email if donation.person else 'unbekannt',
                    'total_amount': str(donation.total_amount),
                    'certificate_was_sent': 'Ja' if is_delayed else 'Nein',
                    'storno_required': 'Ja' if is_delayed else 'Nein'
                }
            )
        except Exception as e:
            logger.error(f"Failed to send admin alert for failed donation {donation.id}: {e}")

    @staticmethod
    def _translate_stripe_error(error_message: str) -> str:
        """
        Translate Stripe error messages to German user-friendly messages.

        Args:
            error_message: Original Stripe error message (English)

        Returns:
            str: German user-friendly message
        """
        # Common Stripe error translations
        translations = {
            'insufficient_funds': 'Ihr Konto weist nicht genügend Deckung auf.',
            'card_declined': 'Die Karte wurde abgelehnt.',
            'expired_card': 'Die Karte ist abgelaufen.',
            'incorrect_cvc': 'Die Prüfziffer (CVC) ist ungültig.',
            'processing_error': 'Es ist ein Verarbeitungsfehler aufgetreten.',
            'incorrect_number': 'Die Kartennummer ist ungültig.',
            'debit_not_authorized': 'Die Lastschrift wurde nicht autorisiert.',
            'account_closed': 'Das Bankkonto ist geschlossen.',
            'no_account': 'Das Bankkonto existiert nicht.',
            'refer_to_customer': 'Bitte kontaktieren Sie Ihre Bank.',
            'generic_decline': 'Die Zahlung wurde von Ihrer Bank abgelehnt.'
        }

        # Check for known error codes in message
        error_lower = error_message.lower()
        for key, translation in translations.items():
            if key in error_lower:
                return translation

        # Check for common phrases
        if 'insufficient' in error_lower:
            return 'Ihr Konto weist nicht genügend Deckung auf.'
        if 'declined' in error_lower:
            return 'Die Zahlung wurde von Ihrer Bank abgelehnt.'
        if 'expired' in error_lower:
            return 'Die Zahlungsmethode ist abgelaufen.'

        # Default: Return original with German prefix
        return f"Die Zahlung konnte nicht abgeschlossen werden: {error_message}"
    
    @staticmethod
    def handle_processing_payment(payment_intent):
        """
        Handle payment in processing state (typically SEPA) - Optimistic Completion

        For SEPA payments, we implement "Optimistic Completion" as recommended by Stripe:
        - Mark verses as sponsored immediately
        - Generate PDF certificates
        - Send confirmation email
        - Set certificate_sent_at for idempotency

        If payment fails later (5-6 days), handle_failed_payment() will:
        - Release the verses
        - Send storno email with cancellation PDF

        Args:
            payment_intent: Stripe PaymentIntent object (dict from webhook)

        Returns:
            bool: True if processing successful
        """
        try:
            # Get donation ID from metadata
            donation_id = payment_intent.get('metadata', {}).get('donation_id')
            if not donation_id or not str(donation_id).isdigit():
                # No donation_id means this PaymentIntent is not from our app (e.g., RaiseNow)
                # Return True to acknowledge the webhook without processing
                logger.info(f"PaymentIntent {payment_intent.get('id')} has no donation_id - not from this app, ignoring")
                return True
            donation_id = int(donation_id)

            # Find donation - accept 'pending' or 'processing' for idempotency (Stripe retries)
            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status.in_(['pending', 'processing'])
            ).first()

            if not donation:
                # Check if donation exists but is already completed/failed
                existing = Donation.query.get(donation_id)
                if existing:
                    logger.info(f"Donation {donation_id} already in status '{existing.payment_status}', returning OK for idempotency")
                    return True
                logger.error(f"No donation found for processing PaymentIntent {payment_intent.get('id')}")
                return False

            # Idempotency check: If already processed (certificate sent), just return OK
            if donation.certificate_sent_at:
                logger.info(f"Donation {donation.id} already processed (certificate_sent_at set), skipping")
                return True

            # 1. Update payment status to 'processing'
            donation.payment_status = 'processing'

            if donation.payment:
                donation.payment.update_stripe_data(payment_intent)

            # 2. Mark verses as sponsored (Optimistic Completion)
            donation.mark_verses_sponsored()

            db.session.commit()
            logger.info(f"Marked donation {donation.id} as processing (SEPA) with verses sponsored")

            # 3. Generate PDFs and send email (outside main transaction for resilience)
            try:
                StripeService._fulfill_donation(donation)
            except Exception as e:
                # Log error but don't fail the webhook - donation is already marked
                logger.error(f"Error fulfilling donation {donation.id} during processing: {e}")
                # Send admin alert about fulfillment failure
                StripeService._send_admin_alert_for_fulfillment_error(donation, str(e))

            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling processing payment: {e}")
            return False

    @staticmethod
    def _fulfill_donation(donation: Donation) -> bool:
        """
        Generate PDFs and send certificate email for a donation.

        This is called from:
        - handle_processing_payment() for SEPA (Optimistic Completion)
        - handle_successful_payment() for card payments (if not already fulfilled)

        Args:
            donation: Donation object with verses already sponsored

        Returns:
            bool: True if fulfillment successful
        """
        from pdf_service import PDFGeneratorService
        from email_service import email_service

        try:
            # Generate PDFs
            pdf_service = PDFGeneratorService(current_app._get_current_object())
            pdf_attachments = []

            # Personal certificate
            try:
                cert = pdf_service.generate_certificate_atomic(
                    donation.id,
                    'personal_certificate',
                    session_id=None  # No session in webhook context
                )
                if cert and cert.file_path:
                    pdf_attachments.append({
                        'path': cert.file_path,
                        'filename': f"NGÜ_Zertifikat_{donation.id}.pdf",
                        'mimetype': 'application/pdf'
                    })
                    logger.info(f"Generated certificate for donation {donation.id}")
            except Exception as e:
                logger.error(f"Failed to generate certificate for donation {donation.id}: {e}")

            # Tax receipt if wanted
            if donation.wants_receipt:
                try:
                    receipt = pdf_service.generate_tax_receipt_atomic(
                        donation.id,
                        session_id=None
                    )
                    if receipt and receipt.file_path:
                        pdf_attachments.append({
                            'path': receipt.file_path,
                            'filename': f"NGÜ_Spendenbescheinigung_{donation.id}.pdf",
                            'mimetype': 'application/pdf'
                        })
                        logger.info(f"Generated tax receipt for donation {donation.id}")
                except Exception as e:
                    logger.error(f"Failed to generate tax receipt for donation {donation.id}: {e}")

            # Send email with PDFs
            if pdf_attachments:
                donation_data = StripeService._prepare_donation_data(donation)

                email_sent = email_service.send_certificate_email_with_attachments(
                    donation_data,
                    pdf_attachments
                )

                if email_sent:
                    # Mark as fulfilled (idempotency marker)
                    donation.certificate_sent_at = datetime.utcnow()
                    donation.email_sent = True
                    donation.email_sent_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Certificate email sent for donation {donation.id}")
                    # Note: HubSpot sync is NOT done here - it happens in handle_successful_payment()
                    # when payment_status becomes 'completed' (for both card and SEPA)
                    return True
                else:
                    logger.error(f"Failed to send certificate email for donation {donation.id}")
                    return False
            else:
                logger.warning(f"No PDFs generated for donation {donation.id}")
                return False

        except Exception as e:
            logger.error(f"Error in _fulfill_donation for donation {donation.id}: {e}")
            raise

    @staticmethod
    def _prepare_donation_data(donation: Donation) -> Dict[str, Any]:
        """
        Prepare donation data dict for email templates.

        Consistent with app.py pattern for donation_data structure.

        Args:
            donation: Donation ORM object

        Returns:
            dict: Donation data for email templates
        """
        return {
            'id': donation.id,
            'total_amount': float(donation.total_amount),
            'created_at': donation.created_at,
            'person': {
                'email': donation.person.email if donation.person else '',
                'first_name': donation.person.first_name if donation.person else '',
                'last_name': donation.person.last_name if donation.person else ''
            },
            'verses': [{
                'reference': va.verse.german_reference if va.verse else '',
                'text': va.verse.text if va.verse else ''
            } for va in donation.verse_associations]
        }

    @staticmethod
    def _send_admin_alert_for_fulfillment_error(donation: Donation, error: str):
        """Send admin alert when PDF/email fulfillment fails."""
        from email_service import email_service

        try:
            email_service.send_admin_alert(
                subject=f"Fulfillment-Fehler bei Donation #{donation.id}",
                message=f"Die PDF-Generierung oder der E-Mail-Versand ist fehlgeschlagen für Donation #{donation.id}.",
                error_details=error,
                context={
                    'donation_id': donation.id,
                    'payment_status': donation.payment_status,
                    'user_email': donation.person.email if donation.person else 'unbekannt',
                    'total_amount': str(donation.total_amount)
                }
            )
        except Exception as e:
            logger.error(f"Failed to send admin alert for donation {donation.id}: {e}")

    @staticmethod
    def _send_admin_alert_for_hubspot_error(donation: Donation, error: str):
        """Send admin alert when HubSpot sync fails."""
        from email_service import email_service

        # Get verse references for the alert
        verse_refs = [
            va.verse.german_reference if va.verse else 'unbekannt'
            for va in donation.verse_associations
        ]

        try:
            email_service.send_admin_alert(
                subject=f"HubSpot-Sync fehlgeschlagen: Donation #{donation.id}",
                message=(
                    f"Die HubSpot-Synchronisation ist fehlgeschlagen für Donation #{donation.id}. "
                    f"Die Spende wurde erfolgreich verarbeitet, aber der CRM-Eintrag muss manuell erstellt werden."
                ),
                error_details=error,
                context={
                    'donation_id': donation.id,
                    'spender_name': (
                        f"{donation.person.first_name} {donation.person.last_name}"
                        if donation.person else 'unbekannt'
                    ),
                    'spender_email': donation.person.email if donation.person else 'unbekannt',
                    'betrag': f"€{float(donation.total_amount):.2f}",
                    'verse': ', '.join(verse_refs),
                    'anzahl_verse': len(verse_refs),
                    'zahlungsdatum': (
                        donation.completed_at.strftime('%d.%m.%Y %H:%M')
                        if donation.completed_at else 'unbekannt'
                    ),
                    'aktion_erforderlich': 'Bitte manuell in HubSpot anlegen'
                }
            )
            logger.info(f"Sent admin alert for HubSpot sync failure on donation {donation.id}")
        except Exception as e:
            logger.error(f"Failed to send admin alert for HubSpot error on donation {donation.id}: {e}")

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
        Handle chargeback/dispute (mainly for SEPA).

        Chargebacks occur when a donor disputes a completed payment with their bank.
        Since the payment was previously successful, a certificate was already sent,
        so we ALWAYS need to:
        1. Release verses (mark as available)
        2. Mark donation as 'disputed'
        3. Generate Storno-PDF
        4. Send Storno-Email
        5. Notify admin

        Args:
            charge: Stripe Charge object with dispute (dict from webhook)

        Returns:
            bool: True if processing successful
        """
        try:
            payment_intent_id = charge.get('payment_intent')
            if not payment_intent_id:
                logger.error("No payment_intent in charge object for chargeback")
                return False

            # Extract dispute details for logging and notification
            dispute = charge.get('dispute', {})
            dispute_reason = dispute.get('reason', 'unknown') if dispute else 'unknown'
            dispute_amount = charge.get('amount_refunded', charge.get('amount', 0))

            # Find payment transaction via PaymentIntent ID
            payment = PaymentTransaction.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if not payment or not payment.donation:
                logger.error(f"No donation found for chargeback PaymentIntent {payment_intent_id}")
                return False

            donation = payment.donation

            # Idempotency: Already disputed? Just return success
            if donation.payment_status == 'disputed':
                logger.info(f"Donation {donation.id} already disputed, skipping")
                return True

            # Log verse references before releasing
            verse_refs = [
                va.verse.german_reference if va.verse else 'unknown'
                for va in donation.verse_associations
            ]

            try:
                # 1. Release all verses (mark as available again)
                for verse_assoc in donation.verse_associations:
                    if verse_assoc.verse:
                        verse_assoc.verse.is_sponsored = False
                        verse_assoc.verse.sponsored_at = None

                # 2. Mark donation as disputed
                donation.payment_status = 'disputed'
                donation.failure_reason = f"Chargeback: {dispute_reason}"

                db.session.commit()
                logger.warning(
                    f"Chargeback processed for donation {donation.id}: "
                    f"verses {', '.join(verse_refs)} released, reason: {dispute_reason}"
                )

                # 3. Generate Storno-PDF and send Storno-Email (outside main transaction)
                try:
                    StripeService._handle_chargeback_notification(donation, dispute_reason)
                except Exception as e:
                    logger.error(f"Error sending chargeback notification for donation {donation.id}: {e}")
                    # Continue - donation is already marked as disputed

                # 4. Send admin alert with dispute details
                try:
                    StripeService._send_admin_alert_for_chargeback(
                        donation, dispute_reason, dispute_amount, verse_refs
                    )
                except Exception as e:
                    logger.error(f"Error sending admin alert for chargeback {donation.id}: {e}")

                return True

            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error processing chargeback: {e}")
                raise

        except Exception as e:
            logger.error(f"Error handling chargeback: {e}")
            return False

    @staticmethod
    def _handle_chargeback_notification(donation: Donation, dispute_reason: str):
        """
        Generate Storno-PDF and send Storno-Email for chargebacks.

        Chargebacks always occur after successful payment, so a certificate
        was definitely sent. Storno is mandatory.

        Args:
            donation: Donation object (already marked as disputed)
            dispute_reason: Reason for dispute from Stripe
        """
        from pdf_service import PDFGeneratorService
        from email_service import email_service

        try:
            # Translate dispute reason to German
            cancellation_reason = StripeService._translate_chargeback_reason(dispute_reason)

            # 1. Generate Storno-PDF
            pdf_service = PDFGeneratorService(current_app._get_current_object())
            storno_pdf_path = pdf_service.generate_storno_certificate(
                donation.id,
                cancellation_reason=cancellation_reason
            )

            if not storno_pdf_path:
                logger.error(f"Failed to generate storno PDF for chargeback donation {donation.id}")
                return

            # 2. Get storno context for email
            storno_context = pdf_service._prepare_storno_context(donation, cancellation_reason)

            # 3. Send Storno-Email with PDF attachment
            donation_data = StripeService._prepare_donation_data(donation)

            email_sent = email_service.send_storno_email(
                donation_data,
                storno_pdf_path,
                storno_context
            )

            if email_sent:
                donation.storno_sent_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Storno email sent for chargeback donation {donation.id}")
            else:
                logger.error(f"Failed to send storno email for chargeback donation {donation.id}")

        except Exception as e:
            logger.error(f"Error in _handle_chargeback_notification for donation {donation.id}: {e}")
            raise

    @staticmethod
    def _send_admin_alert_for_chargeback(donation: Donation, dispute_reason: str,
                                          dispute_amount: int, verse_refs: list):
        """Send admin alert for chargeback/dispute."""
        from email_service import email_service

        # Convert amount from cents to EUR
        amount_eur = dispute_amount / 100 if dispute_amount else float(donation.total_amount)

        try:
            email_service.send_admin_alert(
                subject=f"⚠️ CHARGEBACK: Donation #{donation.id} - €{amount_eur:.2f}",
                message=(
                    f"Ein Kunde hat eine Rückbuchung (Chargeback) für Donation #{donation.id} "
                    f"veranlasst. Die betroffenen Verse wurden freigegeben."
                ),
                error_details=f"Dispute Reason: {dispute_reason}",
                context={
                    'donation_id': donation.id,
                    'payment_status': donation.payment_status,
                    'dispute_reason': dispute_reason,
                    'dispute_amount_eur': f"€{amount_eur:.2f}",
                    'user_email': donation.person.email if donation.person else 'unbekannt',
                    'user_name': (
                        f"{donation.person.first_name} {donation.person.last_name}"
                        if donation.person else 'unbekannt'
                    ),
                    'affected_verses': ', '.join(verse_refs),
                    'verse_count': len(verse_refs),
                    'original_certificate_date': (
                        donation.certificate_sent_at.strftime('%d.%m.%Y %H:%M')
                        if donation.certificate_sent_at else 'unbekannt'
                    ),
                    'action_required': 'Storno-PDF wurde generiert und an Spender gesendet.'
                }
            )
        except Exception as e:
            logger.error(f"Failed to send admin alert for chargeback {donation.id}: {e}")

    @staticmethod
    def _translate_chargeback_reason(reason: str) -> str:
        """
        Translate Stripe chargeback/dispute reasons to German.

        Args:
            reason: Stripe dispute reason code

        Returns:
            str: German user-friendly message
        """
        # Stripe dispute reason codes
        # https://stripe.com/docs/api/disputes/object#dispute_object-reason
        translations = {
            'bank_cannot_process': 'Die Bank konnte die Zahlung nicht verarbeiten.',
            'check_returned': 'Der Scheck wurde zurückgegeben.',
            'credit_not_processed': 'Eine erwartete Gutschrift wurde nicht verarbeitet.',
            'customer_initiated': 'Die Rückbuchung wurde vom Kontoinhaber veranlasst.',
            'debit_not_authorized': 'Die Lastschrift wurde nicht autorisiert.',
            'duplicate': 'Es wurde eine doppelte Zahlung gemeldet.',
            'fraudulent': 'Die Zahlung wurde als betrügerisch gemeldet.',
            'general': 'Allgemeine Rückbuchung ohne spezifischen Grund.',
            'incorrect_account_details': 'Falsche Kontodaten wurden verwendet.',
            'insufficient_funds': 'Nicht ausreichende Deckung auf dem Konto.',
            'product_not_received': 'Das Produkt/die Leistung wurde nicht erhalten.',
            'product_unacceptable': 'Das Produkt/die Leistung war nicht akzeptabel.',
            'subscription_canceled': 'Ein Abonnement wurde gekündigt.',
            'unrecognized': 'Die Zahlung wurde nicht erkannt.'
        }

        if reason in translations:
            return translations[reason]

        # Default: Return with German prefix
        return f"Rückbuchung durch Bank oder Kontoinhaber: {reason}"
    
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
                # No donation_id means this PaymentIntent is not from our app (e.g., RaiseNow)
                logger.info(f"Requires_action PaymentIntent {payment_intent.id} has no donation_id - not from this app, ignoring")
                return True
            donation_id = int(donation_id)

            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status.in_(['pending', 'processing'])
            ).first()

            if not donation:
                logger.info(f"No pending donation found for requires_action PaymentIntent {payment_intent.id} - may be already processed")
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
                # No donation_id means this PaymentIntent is not from our app (e.g., RaiseNow)
                logger.info(f"Canceled PaymentIntent {payment_intent.id} has no donation_id - not from this app, ignoring")
                return True
            donation_id = int(donation_id)

            donation = Donation.query.filter(
                Donation.id == donation_id,
                Donation.payment_status.in_(['pending', 'processing'])
            ).first()

            if not donation:
                logger.info(f"No pending donation found for canceled PaymentIntent {payment_intent.id} - may be already processed")
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