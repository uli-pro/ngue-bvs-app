"""
HubSpot Integration Service
Handles automatic synchronization of donations to HubSpot CRM
"""

import os
import logging
from datetime import datetime
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate as ContactCreate
from hubspot.crm.deals import SimplePublicObjectInputForCreate as DealCreate
from hubspot.crm.deals import ApiException

logger = logging.getLogger(__name__)


class HubSpotSyncError(Exception):
    """Custom exception for HubSpot sync errors"""
    pass


class HubSpotService:
    """Service class for HubSpot CRM synchronization"""

    @staticmethod
    def _get_client():
        """Initialize HubSpot client with API key from environment"""
        api_key = os.getenv('HUBSPOT_API_KEY')
        if not api_key:
            raise HubSpotSyncError("HUBSPOT_API_KEY not configured in environment")
        return HubSpot(access_token=api_key)

    @staticmethod
    def _map_person_to_contact_properties(person):
        """
        Map Person model to HubSpot Contact properties
        Only overwrites fields that have values (non-empty)
        """
        properties = {
            "email": person.email,
            "firstname": person.first_name or "",
            "lastname": person.last_name or "",
            "ngue_newsletter_einwilligung": person.newsletter_consent
        }

        # Only add optional fields if they have values
        if person.salutation:
            properties["salutation"] = person.salutation

        if person.street:
            # Combine street and house number
            properties["address"] = f"{person.street} {person.house_number}".strip()

        if person.postal_code:
            properties["zip"] = person.postal_code

        if person.city:
            properties["city"] = person.city

        return properties

    @staticmethod
    def _sync_contact(client, person):
        """
        Create or update HubSpot contact
        Returns contact ID on success, None on failure
        """
        try:
            properties = HubSpotService._map_person_to_contact_properties(person)

            # Search for existing contact by email
            search_result = client.crm.contacts.search_api.do_search(
                public_object_search_request={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": person.email
                        }]
                    }]
                }
            )

            if search_result.results:
                # Update existing contact
                contact_id = search_result.results[0].id
                client.crm.contacts.basic_api.update(
                    contact_id=contact_id,
                    simple_public_object_input={"properties": properties}
                )
                logger.info(f"HubSpot: Updated contact {contact_id} for {person.email}")
                return contact_id
            else:
                # Create new contact
                contact = client.crm.contacts.basic_api.create(
                    simple_public_object_input_for_create=ContactCreate(
                        properties=properties
                    )
                )
                logger.info(f"HubSpot: Created contact {contact.id} for {person.email}")
                return contact.id

        except Exception as e:
            logger.error(f"HubSpot: Failed to sync contact for {person.email}: {str(e)}")
            return None

    @staticmethod
    def _map_donation_to_deal_properties(donation, person):
        """Map Donation model to HubSpot Deal properties"""
        # Get all verses for this donation
        verses = donation.get_verses_sorted()
        verse_references = "; ".join([v.german_reference for v in verses])

        # Create descriptive deal name
        deal_name = f"NGÜ Spende - {donation.verse_count} Vers(e) - {person.email}"

        properties = {
            "dealname": deal_name,
            "amount": str(float(donation.total_amount)),
            "closedate": donation.completed_at.strftime("%Y-%m-%d") if donation.completed_at else datetime.utcnow().strftime("%Y-%m-%d"),
            "dealstage": "closedwon",
            "pipeline": "default",

            # Custom properties (must be created in HubSpot first)
            "stripe_payment_intent_id": donation.payment.stripe_payment_intent_id if donation.payment else "",
            "ngue_verse_count": str(donation.verse_count),
            "ngue_verse_references": verse_references,
            "ngue_pipeline_source": "ngue-bvs-app"
        }

        return properties

    @staticmethod
    def _sync_deal(client, donation, person, contact_id):
        """
        Create or update HubSpot deal for donation
        Returns deal ID on success, None on failure
        """
        try:
            properties = HubSpotService._map_donation_to_deal_properties(donation, person)

            # Check if deal already exists (via Stripe Payment Intent ID)
            if donation.payment and donation.payment.stripe_payment_intent_id:
                search_result = client.crm.deals.search_api.do_search(
                    public_object_search_request={
                        "filterGroups": [{
                            "filters": [{
                                "propertyName": "stripe_payment_intent_id",
                                "operator": "EQ",
                                "value": donation.payment.stripe_payment_intent_id
                            }]
                        }]
                    }
                )

                if search_result.results:
                    # Update existing deal
                    deal_id = search_result.results[0].id
                    client.crm.deals.basic_api.update(
                        deal_id=deal_id,
                        simple_public_object_input={"properties": properties}
                    )
                    logger.info(f"HubSpot: Updated deal {deal_id} for donation {donation.id}")
                    return deal_id

            # Create new deal with association to contact
            deal = client.crm.deals.basic_api.create(
                simple_public_object_input_for_create=DealCreate(
                    properties=properties,
                    associations=[
                        {
                            "to": {"id": contact_id},
                            "types": [
                                {
                                    "associationCategory": "HUBSPOT_DEFINED",
                                    "associationTypeId": 3  # Deal to Contact
                                }
                            ]
                        }
                    ]
                )
            )
            logger.info(f"HubSpot: Created deal {deal.id} for donation {donation.id}")
            return deal.id

        except ApiException as e:
            logger.error(f"HubSpot: Failed to sync deal for donation {donation.id}: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"HubSpot: Unexpected error syncing deal for donation {donation.id}: {str(e)}")
            return None

    @staticmethod
    def sync_donation(donation):
        """
        Main sync function: Synchronize completed donation to HubSpot

        Args:
            donation: Donation model instance (must be completed)

        Returns:
            dict: {'success': bool, 'contact_id': str, 'deal_id': str, 'error': str}
        """
        # Validate donation state
        if donation.payment_status != 'completed':
            logger.warning(f"HubSpot: Skipping sync for incomplete donation {donation.id}")
            return {'success': False, 'error': 'Donation not completed'}

        if not donation.person:
            logger.error(f"HubSpot: No person associated with donation {donation.id}")
            return {'success': False, 'error': 'No person associated'}

        try:
            # Initialize HubSpot client
            client = HubSpotService._get_client()

            # Step 1: Sync contact (person)
            contact_id = HubSpotService._sync_contact(client, donation.person)
            if not contact_id:
                return {'success': False, 'error': 'Failed to sync contact'}

            # Step 2: Sync deal (donation)
            deal_id = HubSpotService._sync_deal(client, donation, donation.person, contact_id)
            if not deal_id:
                return {'success': False, 'contact_id': contact_id, 'error': 'Failed to sync deal'}

            logger.info(f"HubSpot: Successfully synced donation {donation.id} (Contact: {contact_id}, Deal: {deal_id})")
            return {
                'success': True,
                'contact_id': contact_id,
                'deal_id': deal_id
            }

        except HubSpotSyncError as e:
            logger.error(f"HubSpot: Configuration error: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"HubSpot: Unexpected error syncing donation {donation.id}: {str(e)}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}