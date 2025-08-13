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
        // Prevent data loss warning for forms with content
        window.addEventListener('beforeunload', function(e) {
            const forms = document.querySelectorAll('form input[type="text"], form input[type="email"], form textarea');
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