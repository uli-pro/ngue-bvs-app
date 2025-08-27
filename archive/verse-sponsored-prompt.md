# Implementation Prompt: Fix Verse Sponsorship Completion Bug

## Problem Summary
Verses are not being marked as sponsored after successful payment. The homepage and transparency page statistics don't update because donations remain in "pending" status instead of being marked as "completed".

## Root Cause Analysis
1. **Webhook is unreliable** - Stripe webhooks are not consistently marking donations as completed
2. **checkout_erfolg route lacks completion logic** - Currently only stores payment_intent_id and clears cart
3. **Missing fallback mechanism** - No alternative to webhook for completing donations

## Required Implementation

### 1. Add Global Stripe Imports
In `app.py`, after line 29 (`db.init_app(app)`), add these imports:
```python
# Initialize extensions
from models import db, Person, Verse, Donation, VerseReservation
from sqlalchemy import text
from stripe_service import StripeService, StripeError  # ADD THIS LINE
import stripe  # ADD THIS LINE
db.init_app(app)
```

### 2. Improve mark_completed() Method in models.py
Update the `mark_completed()` method in the `Donation` class (around line 319) to be idempotent:

```python
def mark_completed(self):
    """Mark donation as completed"""
    # Check if already completed to avoid duplicate processing
    if self.payment_status == 'completed':
        return
        
    self.payment_status = 'completed'
    self.completed_at = datetime.utcnow()
    # Mark verse as sponsored
    self.verse.is_sponsored = True
    self.verse.sponsored_at = datetime.utcnow()
    if self.payment:
        self.payment.mark_confirmed()
    db.session.commit()
```

### 3. Extend checkout_erfolg Route in app.py
Replace the current `checkout_erfolg` function (around line 1378) with this enhanced version:

```python
@app.route("/checkout/erfolg")
def checkout_erfolg():
    """Success page after payment with payment verification"""
    # Get payment intent from URL parameters (Stripe redirects)
    payment_intent_id = request.args.get('payment_intent')
    
    if payment_intent_id:
        # Store payment intent ID for success page display
        session['completed_payment_intent'] = payment_intent_id
        session.modified = True
        
        # Process donation completion immediately upon success page load
        try:
            # Retrieve PaymentIntent from Stripe to verify success
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            app.logger.info(f"Retrieved PaymentIntent {payment_intent_id} with status: {payment_intent.status}")
            
            # Only process if payment actually succeeded
            if payment_intent.status == 'succeeded':
                # Get donation IDs from metadata
                donation_ids_str = payment_intent.metadata.get('donation_ids', '')
                donation_ids = [int(did) for did in donation_ids_str.split(',') if did.isdigit()]
                
                if donation_ids:
                    # Find and complete donations
                    donations = Donation.query.filter(Donation.id.in_(donation_ids)).all()
                    completed_count = 0
                    
                    for donation in donations:
                        donation.mark_completed()
                        completed_count += 1
                    
                    app.logger.info(f"Successfully marked {completed_count} donations as completed from success page")
                else:
                    app.logger.warning(f"No valid donation IDs found in PaymentIntent {payment_intent_id} metadata")
            else:
                app.logger.warning(f"PaymentIntent {payment_intent_id} has status {payment_intent.status}, not succeeded")
                
        except stripe.error.StripeError as e:
            app.logger.error(f"Stripe error retrieving PaymentIntent {payment_intent_id}: {e}")
        except Exception as e:
            app.logger.error(f"Error processing donation completion on success page: {e}")
    
    # Clear cart after successful payment (will be cleared by webhook anyway)
    session.pop('cart', None)
    session.pop('shared_donor_data', None)
    session.pop('payment_intent_id', None)
    session.modified = True
    
    return render_template("checkout-erfolg.html")
```

### 4. Remove Redundant Local Imports
Remove these local import blocks from other functions in app.py:

From `create_payment_intent()` function:
```python
# Remove these lines:
from stripe_service import StripeService, StripeError
```

From `stripe_webhook()` function:
```python
# Remove these lines:
from stripe_service import StripeService, StripeError
```

From `api_payment_status()` function:
```python
# Remove these lines:
from stripe_service import StripeService, StripeError
import stripe
```

### 5. SQL Fix for Existing Pending Donations
Run these SQL commands to fix existing pending donations:

```sql
-- Fix verse 622 (1KI 17,22) that was sponsored twice
UPDATE donations 
SET payment_status = 'completed', completed_at = NOW()
WHERE id = 3;  -- First donation for verse 622

UPDATE verses 
SET is_sponsored = true, sponsored_at = NOW()
WHERE id = 622;

UPDATE donations 
SET payment_status = 'cancelled'
WHERE id = 4;  -- Second duplicate donation

-- Clean up expired reservations
DELETE FROM verse_reservations WHERE expires_at < NOW();
```

## Expected Results
After implementation:
1. **Immediate donation completion** - Donations marked as completed on success page load
2. **Updated statistics** - Homepage and transparency page show correct counts
3. **Prevent double sponsoring** - Verses can't be sponsored multiple times
4. **Better logging** - Terminal shows completion process
5. **Webhook as backup** - Webhook still works as fallback mechanism

## Files to Modify
1. `app.py` - Add imports and extend checkout_erfolg route
2. `models.py` - Make mark_completed() method idempotent
3. Database - Fix existing pending donations with SQL

## Testing
1. Sponsor a verse with test card `4242 4242 4242 4242`
2. Check terminal logs for completion messages
3. Verify donation status in database: `SELECT payment_status FROM donations ORDER BY created_at DESC LIMIT 1;`
4. Check verse count: `SELECT COUNT(*) FROM verses WHERE is_sponsored = true;`
5. Reload homepage to verify statistics update

## Deployment
1. Copy `app.py` and `models.py` to server
2. Run `docker-compose up -d --build`
3. Execute SQL fix commands on server database