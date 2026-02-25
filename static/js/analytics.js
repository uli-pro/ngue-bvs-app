/**
 * Analytics Helper for Plausible Analytics
 * Provides simple event tracking wrapper for NGÜ BVS App
 */

const Analytics = {
    /**
     * Track a custom event with Plausible
     * @param {string} eventName - Name of the event
     * @param {object} props - Optional properties to send with the event
     */
    track(eventName, props = {}) {
        if (typeof window.plausible !== 'function') {
            console.warn('Plausible Analytics not loaded');
            return;
        }

        try {
            window.plausible(eventName, { props });
            console.log(`Analytics event tracked: ${eventName}`, props);
        } catch (e) {
            console.warn('Analytics tracking failed:', e);
        }
    },

    /**
     * Track when a verse is added to the cart
     * @param {string} verseReference - e.g., "1. Mose 1,1"
     * @param {number} price - Amount in EUR
     */
    trackVerseAdded(verseReference, price) {
        this.track('Verse Added', {
            verse: verseReference,
            price: price
        });
    },

    /**
     * Track when checkout process starts
     * @param {number} items - Number of verses in cart
     * @param {number} amount - Total amount in EUR
     */
    trackCheckoutStarted(items, amount) {
        this.track('Checkout Started', {
            items: items,
            amount: amount
        });
    },

    /**
     * Track completed donation (with revenue tracking)
     * @param {string} type - Donation type (individual/group/gift)
     * @param {number} amount - Total amount in EUR
     * @param {number} verses - Number of verses sponsored
     */
    trackDonation(type, amount, verses) {
        if (typeof window.plausible !== 'function') {
            console.warn('Plausible Analytics not loaded');
            return;
        }

        try {
            window.plausible('Donation', {
                props: {
                    type: type,
                    verses: verses
                },
                revenue: {
                    amount: amount,
                    currency: 'EUR'
                }
            });
            console.log(`Donation tracked: €${amount}, ${verses} verses, type: ${type}`);
        } catch (e) {
            console.warn('Analytics tracking failed:', e);
        }
    }
};

// Make it globally available
window.NGUEAnalytics = Analytics;