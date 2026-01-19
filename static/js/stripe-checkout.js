/* This file was developed with assistance from Claude Code (Anthropic)
 * for implementation and optimization. Core design is original work.
 */

/**
 * Stripe Checkout JavaScript
 * Handles Stripe Payment Element with SEPA preference and 3D Secure support
 */

class StripeCheckout {
    constructor() {
        this.stripe = null;
        this.elements = null;
        this.paymentElement = null;
        this.clientSecret = null;
        this.processing = false;
        this.isIntentionalRedirect = false; // Flag for planned redirects
        this.selectedPaymentType = null; // Track selected payment method type

        // Get configuration from window
        this.config = window.stripeConfig || {};

        // Debug mode detection (only in development)
        this.debugMode = window.location.hostname === 'localhost' ||
                        window.location.hostname === '127.0.0.1' ||
                        window.location.port === '5000';

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    async init() {
        try {
            if (!this.config.publicKey) {
                throw new Error('Stripe public key not configured');
            }

            // Initialize Stripe
            this.stripe = Stripe(this.config.publicKey);

            // Don't create PaymentIntent yet - wait for user to select payment method
            // This ensures we can specify the payment method type when creating the intent

            this.debugLog('Stripe initialized successfully - waiting for payment method selection');

        } catch (error) {
            this.debugError('Error initializing Stripe checkout:', error);
            this.showError('Fehler beim Laden der Zahlungsabwicklung. Bitte laden Sie die Seite neu.');
        }
    }
    
    async createPaymentIntent(paymentType = null) {
        try {
            this.debugLog('🔄 Creating PaymentIntent...', paymentType ? `for ${paymentType}` : '');

            const requestBody = {};
            if (paymentType) {
                requestBody.payment_type = paymentType;
            }

            const response = await fetch('/checkout/create-payment-intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(requestBody)
            });
            
            this.debugLog('📡 Response status:', response.status);
            this.debugLog('📡 Response headers:', Object.fromEntries(response.headers.entries()));
            
            const data = await response.json();
            // Remove sensitive data from logs
            const safeData = { ...data };
            if (safeData.client_secret) {
                safeData.client_secret = data.client_secret.substring(0, 20) + '...';
            }
            this.debugLog('📦 Response data:', safeData);
            
            if (!response.ok) {
                this.debugError('❌ HTTP Error:', response.status, safeData);
                throw new Error(data.error || `HTTP ${response.status}: PaymentIntent creation failed`);
            }
            
            if (!data.success || !data.client_secret) {
                this.debugError('❌ Invalid response format:', safeData);
                throw new Error('Invalid PaymentIntent response format');
            }
            
            this.clientSecret = data.client_secret;
            this.debugLog('✅ PaymentIntent created successfully:', data.client_secret.substring(0, 20) + '...');
            
        } catch (error) {
            this.debugError('💥 Error creating PaymentIntent:', error);
            this.debugError('💥 Error stack:', error.stack);
            throw new Error(`Zahlung konnte nicht initialisiert werden: ${error.message}`);
        }
    }
    
    async selectPaymentMethod(type) {
        try {
            // Schweiz + SEPA Validierung (Fallback falls HTML disabled umgangen wird)
            const countryCode = this.config.donorData?.address?.country || 'DE';

            if (type === 'sepa' && countryCode === 'CH') {
                this.showError(
                    'SEPA-Lastschrift ist für Schweizer Bankkonten leider nicht verfügbar. ' +
                    'Bitte wählen Sie die Zahlung per Kreditkarte.'
                );
                return; // Abbruch
            }

            this.selectedPaymentType = type;
            this.debugLog(`Payment method selected: ${type}`);

            // Show loading state
            const selectionDiv = document.getElementById('payment-method-selection');
            const formCard = document.getElementById('payment-form-card');
            const methodTitle = document.getElementById('payment-method-title');

            if (selectionDiv) selectionDiv.style.display = 'none';
            if (formCard) formCard.style.display = 'block';

            // Update title
            if (methodTitle) {
                methodTitle.textContent = type === 'sepa' ? 'SEPA-Lastschrift' : 'Kreditkarte';
            }

            // Show loading indicator
            this.showLoading();

            // Create PaymentIntent with selected payment type
            await this.createPaymentIntent(type);

            // Setup Payment Element with selected method
            await this.setupPaymentElement(type);

            // Hide loading
            this.hideLoading();

            // Setup submit button listener
            this.setupEventListeners();

        } catch (error) {
            this.debugError('Error selecting payment method:', error);
            this.showError('Fehler beim Laden der Zahlungsmethode. Bitte versuchen Sie es erneut.');
            this.hideLoading();
            // Reset on error
            this.resetPaymentMethod();
        }
    }

    resetPaymentMethod() {
        // Unmount payment element if exists
        if (this.paymentElement) {
            this.paymentElement.unmount();
            this.paymentElement = null;
        }

        // Reset elements
        if (this.elements) {
            this.elements = null;
        }

        // Reset client secret (will be recreated with new payment type)
        this.clientSecret = null;

        // Show selection, hide form
        const selectionDiv = document.getElementById('payment-method-selection');
        const formCard = document.getElementById('payment-form-card');

        if (selectionDiv) selectionDiv.style.display = 'block';
        if (formCard) formCard.style.display = 'none';

        // Clear errors
        this.clearError();

        this.selectedPaymentType = null;
        this.debugLog('Payment method selection reset');
    }

    async setupPaymentElement(paymentType) {
        try {
            if (!this.clientSecret) {
                throw new Error('No client secret available');
            }

            // Create Elements instance
            this.elements = this.stripe.elements({
                clientSecret: this.clientSecret,
                appearance: {
                    theme: 'stripe',
                    variables: {
                        colorPrimary: '#007bff',
                        colorBackground: '#ffffff',
                        colorText: '#212529',
                        colorDanger: '#dc3545',
                        fontFamily: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                        spacingUnit: '4px',
                        borderRadius: '6px'
                    },
                    rules: {
                        '.Input': {
                            padding: '12px',
                            fontSize: '16px'
                        },
                        '.Label': {
                            fontWeight: '500',
                            marginBottom: '8px'
                        }
                    }
                }
            });

            // Configure payment element based on selected type
            const paymentConfig = {
                defaultValues: {
                    billingDetails: this.config.donorData
                },
                fields: {
                    billingDetails: {
                        name: 'auto',
                        email: 'auto',
                        address: {
                            line1: 'auto',
                            line2: 'never',
                            city: 'auto',
                            postalCode: 'auto',
                            country: 'auto'
                        }
                    }
                },
                // Disable all wallets
                wallets: {
                    applePay: 'never',
                    googlePay: 'never'
                }
            };

            // Add payment type specific config
            if (paymentType === 'sepa') {
                paymentConfig.business = { name: 'Peter-Schöffer-Stiftung' };
                paymentConfig.terms = { sepaDebit: 'always' };
                // Only allow SEPA, no tabs
                paymentConfig.paymentMethodOrder = ['sepa_debit'];
            } else if (paymentType === 'card') {
                // Only allow cards, no tabs
                paymentConfig.paymentMethodOrder = ['card'];
            }

            // Create Payment Element
            this.paymentElement = this.elements.create('payment', paymentConfig);

            // Mount the Payment Element
            await this.paymentElement.mount('#payment-element');

            // Setup Payment Element event listeners
            this.paymentElement.on('ready', () => {
                this.debugLog('Payment Element is ready');
                this.enableSubmitButton();
            });

            this.paymentElement.on('change', (event) => {
                this.handlePaymentElementChange(event);
            });

            this.paymentElement.on('focus', () => {
                this.clearError();
            });

        } catch (error) {
            this.debugError('Error setting up Payment Element:', error);
            throw new Error(`Zahlungsformular konnte nicht geladen werden: ${error.message}`);
        }
    }
    
    setupEventListeners() {
        // Submit button
        const submitButton = document.getElementById('submit-payment');
        if (submitButton) {
            submitButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }
        
        // Handle browser back button - only warn for unintentional navigation
        window.addEventListener('beforeunload', (e) => {
            if (this.processing && !this.isIntentionalRedirect) {
                e.preventDefault();
                const message = 'Zahlung wird gerade verarbeitet. Möchten Sie wirklich die Seite verlassen?';
                e.returnValue = message; // For older browsers
                return message; // For modern browsers
            }
        });
    }
    
    handlePaymentElementChange(event) {
        // Store selected payment method type for later use
        this.selectedPaymentMethodType = event.value ? event.value.type : null;
        
        // Show/hide SEPA mandate info based on selected payment method
        const sepaInfo = document.getElementById('sepa-mandate-info');
        if (sepaInfo) {
            if (event.value && event.value.type === 'sepa_debit') {
                sepaInfo.style.display = 'block';
            } else {
                sepaInfo.style.display = 'none';
            }
        }
        
        // Update submit button state
        if (event.complete) {
            this.enableSubmitButton();
        } else {
            this.disableSubmitButton();
        }
        
        // Handle validation errors
        if (event.error) {
            this.showError(event.error.message);
        } else {
            this.clearError();
        }
    }
    
    async handleSubmit() {
        if (this.processing) {
            return;
        }
        
        try {
            this.processing = true;
            
            // Provide immediate visual feedback
            this.disableSubmitButton();
            this.showLoading();
            this.clearError();
            
            this.debugLog('🚀 Starting payment confirmation with method type:', this.selectedPaymentMethodType);
            
            // Confirm payment with Stripe
            const { error, paymentIntent } = await this.stripe.confirmPayment({
                elements: this.elements,
                confirmParams: {
                    return_url: `${window.location.origin}/checkout/erfolg`
                },
                redirect: 'if_required'  // Only redirect for 3DS or specific requirements
            });
            
            if (error) {
                // Payment failed or requires action
                this.handlePaymentError(error);
            } else if (paymentIntent) {
                // Payment confirmed - check if it's SEPA
                this.handlePaymentConfirmed(paymentIntent);
            }
            
        } catch (error) {
            this.debugError('Error processing payment:', error);
            this.showError('Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
            this.processing = false;
            this.hideLoading();
            this.enableSubmitButton();
        }
    }
    
    handlePaymentConfirmed(paymentIntent) {
        this.debugLog('Payment confirmed:', paymentIntent.id, 'Status:', paymentIntent.status);

        // 2025-11-26: Simplified to always go to processing page
        // All payments wait for webhook to set certificate_sent_at
        // This ensures consistent flow for both card and SEPA payments

        this.debugLog('🔄 Redirecting to processing page, waiting for webhook...');
        this.isIntentionalRedirect = true;
        window.location.href = '/checkout/verarbeitung';

        /* COMMENTED OUT 2025-11-26: Old logic that bypassed webhook for instant card payments
        // Check if this is a SEPA payment or if payment is still processing
        const isSepaPayment = this.selectedPaymentMethodType === 'sepa_debit';
        const isProcessing = paymentIntent.status === 'processing';
        const isRequiresAction = paymentIntent.status === 'requires_action';

        if (isSepaPayment || isProcessing || isRequiresAction) {
            // Redirect to processing page for SEPA or processing payments
            this.debugLog('🏦 SEPA or processing payment detected, redirecting to processing page');
            this.showProcessingMessage();

            // Mark as intentional redirect to prevent browser warning
            this.isIntentionalRedirect = true;

            setTimeout(() => {
                window.location.href = `/checkout/verarbeitung?payment_intent=${paymentIntent.id}`;
            }, 1000);
        } else if (paymentIntent.status === 'succeeded') {
            // Direct success for instant payments (cards)
            this.handlePaymentSuccess(paymentIntent);
        } else {
            // Unknown status - redirect to processing page to be safe
            this.debugLog('⚠️ Unknown payment status, redirecting to processing page');

            // Mark as intentional redirect to prevent browser warning
            this.isIntentionalRedirect = true;

            setTimeout(() => {
                window.location.href = `/checkout/verarbeitung?payment_intent=${paymentIntent.id}`;
            }, 1000);
        }
        END COMMENTED OUT */
    }
    
    showProcessingMessage() {
        // Show specific message for SEPA payments
        const message = this.selectedPaymentMethodType === 'sepa_debit' 
            ? 'SEPA-Lastschrift wurde eingereicht. Sie werden zur Statusseite weitergeleitet...'
            : 'Zahlung wird verarbeitet. Sie werden zur Statusseite weitergeleitet...';
            
        this.showSuccess(message);
    }
    
    handlePaymentError(error) {
        this.debugError('Payment error:', error);

        // KRITISCHER FIX: State SOFORT zurücksetzen, BEVOR wir den Fehlertyp prüfen
        // Dies stellt sicher, dass die UI bei ALLEN Fehlern wieder bedienbar ist
        this.processing = false;
        this.hideLoading();
        this.enableSubmitButton();

        let errorMessage = 'Die Zahlung konnte nicht verarbeitet werden.';

        switch (error.type) {
            case 'card_error':
                switch (error.code) {
                    case 'authentication_required':
                        // 3DS-Authentifizierung - Stripe handled den Redirect normalerweise automatisch
                        // Falls nicht, zeigen wir eine Meldung und der User kann erneut versuchen
                        errorMessage = '3D Secure Authentifizierung erforderlich. Bitte versuchen Sie es erneut.';
                        break;
                    case 'card_declined':
                        errorMessage = 'Ihre Karte wurde abgelehnt. Bitte versuchen Sie eine andere Zahlungsmethode.';
                        break;
                    case 'insufficient_funds':
                        errorMessage = 'Nicht ausreichende Deckung. Bitte wählen Sie eine andere Zahlungsmethode.';
                        break;
                    case 'incorrect_cvc':
                        errorMessage = 'Die CVC-Nummer ist nicht korrekt.';
                        break;
                    case 'expired_card':
                        errorMessage = 'Ihre Karte ist abgelaufen.';
                        break;
                    default:
                        errorMessage = error.message || 'Kartenzahlung fehlgeschlagen.';
                }
                break;

            case 'validation_error':
                errorMessage = 'Bitte überprüfen Sie Ihre Eingaben.';
                break;

            case 'api_connection_error':
            case 'api_error':
                errorMessage = 'Verbindungsfehler. Bitte versuchen Sie es erneut.';
                break;

            case 'rate_limit_error':
                errorMessage = 'Zu viele Anfragen. Bitte warten Sie einen Moment.';
                break;

            default:
                errorMessage = error.message || errorMessage;
        }

        this.showError(errorMessage);
    }
    
    handlePaymentSuccess(paymentIntent) {
        this.debugLog('Payment succeeded:', paymentIntent.id);
        
        // Show success message briefly before redirect
        this.showSuccess('Zahlung erfolgreich! Sie werden weitergeleitet...');
        
        // Mark as intentional redirect to prevent browser warning
        this.isIntentionalRedirect = true;
        
        // Redirect to success page after short delay
        setTimeout(() => {
            window.location.href = `/checkout/erfolg?payment_intent=${paymentIntent.id}`;
        }, 1500);
    }
    
    showError(message) {
        const errorDiv = document.getElementById('payment-errors');
        const errorMessage = document.getElementById('error-message');
        
        if (errorDiv && errorMessage) {
            errorMessage.textContent = message;
            errorDiv.style.display = 'block';
            
            // Scroll error into view
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        this.debugError('Payment error shown to user:', message);
    }
    
    clearError() {
        const errorDiv = document.getElementById('payment-errors');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }
    
    showSuccess(message) {
        // Remove any existing success alerts
        const existingAlert = document.querySelector('.alert-success');
        if (existingAlert) {
            existingAlert.remove();
        }
        
        // Create success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success mt-3';
        alertDiv.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
        `;
        
        // Insert before payment element
        const paymentElement = document.getElementById('payment-element');
        if (paymentElement && paymentElement.parentNode) {
            paymentElement.parentNode.insertBefore(alertDiv, paymentElement);
        }
    }
    
    showLoading() {
        const loadingDiv = document.getElementById('payment-loading');
        if (loadingDiv) {
            loadingDiv.style.display = 'block';
        }
    }
    
    hideLoading() {
        const loadingDiv = document.getElementById('payment-loading');
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    }
    
    enableSubmitButton() {
        const submitButton = document.getElementById('submit-payment');
        if (submitButton && !this.processing) {
            submitButton.disabled = false;
            submitButton.innerHTML = `
                <i class="fas fa-lock me-2"></i>
                Jetzt sicher spenden - ${this.config.totalAmount?.toFixed(2) || '0.00'} €
            `;
        }
    }
    
    disableSubmitButton() {
        const submitButton = document.getElementById('submit-payment');
        if (submitButton) {
            submitButton.disabled = true;
            if (this.processing) {
                submitButton.innerHTML = `
                    <i class="fas fa-spinner fa-spin me-2"></i>
                    Zahlung wird verarbeitet...
                `;
            }
        }
    }
    
    getCSRFToken() {
        // Get CSRF token from meta tag or form
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }
        
        // Try to get from form field
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return '';
    }
    
    // Debug helper methods - only log in development
    debugLog(...args) {
        if (this.debugMode) {
            console.log(...args);
        }
    }
    
    debugError(...args) {
        if (this.debugMode) {
            console.error(...args);
        } else {
            // In production, only log critical errors without sensitive data
            console.error('Payment processing error occurred');
        }
    }
}

// Initialize Stripe Checkout when script loads
window.stripeCheckout = new StripeCheckout();

// Export for global access
window.StripeCheckout = StripeCheckout;

// Global functions for onclick handlers
window.selectPaymentMethod = function(type) {
    if (window.stripeCheckout) {
        window.stripeCheckout.selectPaymentMethod(type);
    }
};

window.resetPaymentMethod = function() {
    if (window.stripeCheckout) {
        window.stripeCheckout.resetPaymentMethod();
    }
};