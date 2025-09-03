/**
 * NGÜ Bibelvers-Sponsoring App
 * Main application JavaScript file
 */

const NGUEApp = {
    /**
     * Initialize the application
     */
    init: function() {
        console.log('NGÜ App initializing...');
        
        // Initialize components
        this.initNavigation();
        this.initForms();
        this.initCommonEvents();
        
        console.log('NGÜ App initialized successfully');
    },

    /**
     * Initialize navigation
     */
    initNavigation: function() {
        if (typeof NavigationManager !== 'undefined') {
            NavigationManager.init();
        }
    },

    /**
     * Initialize forms
     */
    initForms: function() {
        if (typeof FormManager !== 'undefined') {
            FormManager.initValidation();
            FormManager.setupPasswordValidation();
        }
    },

    /**
     * Initialize common events and functionality
     */
    initCommonEvents: function() {
        // Track navigation states
        let intentionalNavigation = false;
        let isAjaxNavigation = false;
        
        // Mark when forms are being submitted normally
        document.addEventListener('submit', function(e) {
            intentionalNavigation = true;
        });
        
        // Mark when links are clicked normally
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a[href]');
            if (link && link.href) {
                // Check if it's an internal link (same domain)
                const url = new URL(link.href, window.location.origin);
                if (url.origin === window.location.origin) {
                    intentionalNavigation = true;
                } else {
                    intentionalNavigation = false; // External links should warn
                }
            }
        });
        
        // Intercept fetch requests to mark AJAX navigation
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            isAjaxNavigation = true;
            // Reset the flag after a delay to allow the response handling
            setTimeout(() => { isAjaxNavigation = false; }, 100);
            return originalFetch.apply(this, args);
        };
        
        // Prevent data loss warning for forms with content (but not during intentional navigation)
        window.addEventListener('beforeunload', function(e) {
            // Don't warn if navigation is intentional or it's an AJAX request
            if (intentionalNavigation || isAjaxNavigation) {
                return;
            }
            
            // Only check forms that are not search forms (to avoid keyword search warnings)
            const forms = document.querySelectorAll('form:not(#keywordSearchForm):not([data-no-warning]) input[type="text"], form:not(#keywordSearchForm):not([data-no-warning]) input[type="email"], form:not(#keywordSearchForm):not([data-no-warning]) textarea');
            let hasContent = false;
            
            forms.forEach(field => {
                if (field.value.trim() !== '') {
                    hasContent = true;
                }
            });
            
            if (hasContent) {
                e.preventDefault();
                e.returnValue = 'Ihre eingegebenen Daten gehen verloren, wenn Sie die Seite verlassen.';
            }
        });

        // Handle loading states for buttons
        this.setupButtonLoadingStates();
    },

    /**
     * Setup loading states for buttons
     */
    setupButtonLoadingStates: function() {
        // Add loading state to buttons when clicked
        document.addEventListener('click', function(e) {
            const button = e.target.closest('button[type="submit"]');
            if (button && !button.disabled) {
                // Store original content
                if (!button.dataset.originalContent) {
                    button.dataset.originalContent = button.innerHTML;
                }
            }
        });
    },

    /**
     * Utility functions
     */
    utils: {
        /**
         * Format currency
         */
        formatCurrency: function(amount, currency = 'EUR') {
            return new Intl.NumberFormat('de-DE', {
                style: 'currency',
                currency: currency
            }).format(amount);
        },

        /**
         * Format date
         */
        formatDate: function(date, options = {}) {
            const defaultOptions = {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            };
            return new Intl.DateTimeFormat('de-DE', { ...defaultOptions, ...options }).format(new Date(date));
        },

        /**
         * Debounce function
         */
        debounce: function(func, wait, immediate) {
            let timeout;
            return function executedFunction() {
                const context = this;
                const args = arguments;
                const later = function() {
                    timeout = null;
                    if (!immediate) func.apply(context, args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func.apply(context, args);
            };
        }
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    NGUEApp.init();
});

// Make app globally available
window.NGUEApp = NGUEApp;