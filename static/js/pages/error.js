/**
 * Error Pages JavaScript
 * Handles error page functionality (500, checkout-fehler, etc.)
 */

const ErrorPage = {
    retryCount: 0,
    maxRetries: 3,

    /**
     * Initialize error page functionality
     */
    init: function() {
        this.loadErrorDetails();
        this.setupAutoRetry();
    },

    /**
     * Load error details (for checkout errors)
     */
    loadErrorDetails: function() {
        // Simulate loading error details from URL params or session
        const urlParams = new URLSearchParams(window.location.search);
        const errorType = urlParams.get('error') || 'unknown';
        
        // Show appropriate error message based on type
        this.showErrorForType(errorType);
    },

    /**
     * Show error message for specific error type
     */
    showErrorForType: function(errorType) {
        const errorMessages = {
            'payment_failed': 'Die Zahlung konnte nicht verarbeitet werden.',
            'timeout': 'Die Verbindung ist abgelaufen.',
            'network': 'Es gab ein Netzwerkproblem.',
            'unknown': 'Ein unerwarteter Fehler ist aufgetreten.'
        };

        const errorElement = document.getElementById('errorMessage');
        if (errorElement && errorMessages[errorType]) {
            errorElement.textContent = errorMessages[errorType];
        }
    },

    /**
     * Setup auto-retry functionality for 500 errors
     */
    setupAutoRetry: function() {
        // Only for 500 error page
        if (window.location.pathname.includes('500') || document.body.classList.contains('error-500')) {
            setTimeout(() => {
                this.showRetryOption();
            }, 5000);
        }
    },

    /**
     * Show retry option
     */
    showRetryOption: function() {
        const retrySection = document.getElementById('retrySection');
        if (retrySection) {
            retrySection.style.display = 'block';
        }
    },

    /**
     * Retry payment
     */
    retryPayment: function() {
        ToastManager.info('Wiederhole Zahlung...');
        
        // Simulate retry
        setTimeout(() => {
            window.location.href = '/checkout/zusammenfassung';
        }, 2000);
    },

    /**
     * Show payment methods
     */
    showPaymentMethods: function() {
        window.location.href = '/checkout/zahlung';
    },

    /**
     * Go back to checkout
     */
    goToCheckout: function() {
        window.location.href = '/checkout/daten';
    },

    /**
     * Auto retry for 500 errors
     */
    autoRetry: function() {
        if (this.retryCount >= this.maxRetries) {
            ToastManager.error('Maximale Anzahl der Wiederholungsversuche erreicht.');
            return;
        }

        this.retryCount++;
        ToastManager.info(`Wiederholungsversuch ${this.retryCount}/${this.maxRetries}...`);
        
        setTimeout(() => {
            window.location.reload();
        }, 3000);
    },

    /**
     * Show timeout message
     */
    showTimeoutMessage: function() {
        const timeoutSection = document.getElementById('timeoutMessage');
        if (timeoutSection) {
            timeoutSection.style.display = 'block';
        }
    }
};

// Make functions globally available for onclick handlers
window.loadErrorDetails = function() {
    ErrorPage.loadErrorDetails();
};

window.retryPayment = function() {
    ErrorPage.retryPayment();
};

window.showPaymentMethods = function() {
    ErrorPage.showPaymentMethods();
};

window.goToCheckout = function() {
    ErrorPage.goToCheckout();
};

window.showRetryOption = function() {
    ErrorPage.showRetryOption();
};

window.autoRetry = function() {
    ErrorPage.autoRetry();
};

window.showTimeoutMessage = function() {
    ErrorPage.showTimeoutMessage();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    ErrorPage.init();
});