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
            
            // Create PaymentIntent
            await this.createPaymentIntent();
            
            // Setup Payment Element
            await this.setupPaymentElement();
            
            // Setup event listeners
            this.setupEventListeners();
            
            this.debugLog('Stripe checkout initialized successfully');
            
        } catch (error) {
            this.debugError('Error initializing Stripe checkout:', error);
            this.showError('Fehler beim Laden der Zahlungsabwicklung. Bitte laden Sie die Seite neu.');
        }
    }
    
    async createPaymentIntent() {
        try {
            this.debugLog('🔄 Creating PaymentIntent...');
            
            const response = await fetch('/checkout/create-payment-intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
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
    
    async setupPaymentElement() {
        try {
            if (!this.clientSecret) {
                throw new Error('No client secret available');
            }
            
            // Create Elements instance with SEPA-focused configuration
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
                        '.Tab': {
                            padding: '12px 16px',
                            border: '1px solid #dee2e6'
                        },
                        '.Tab--selected': {
                            backgroundColor: '#007bff',
                            color: '#ffffff',
                            borderColor: '#007bff'
                        },
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
            
            // Create Payment Element with SEPA preference
            this.paymentElement = this.elements.create('payment', {
                defaultValues: {
                    billingDetails: this.config.donorData
                },
                
                // Business information for SEPA mandate
                business: {
                    name: 'Peter-Schöffer-Stiftung'
                },
                
                // Payment method configuration
                paymentMethodOrder: ['sepa_debit', 'card', 'giropay'],
                
                // Terms display for SEPA
                terms: {
                    sepaDebit: 'always'
                },
                
                // Wallets configuration
                wallets: {
                    applePay: 'never',
                    googlePay: 'never'
                },
                
                // Fields configuration
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
                            // Removed state: 'never' to avoid confirmation error
                        }
                    }
                }
            });
            
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
        
        // Handle browser back button
        window.addEventListener('beforeunload', (e) => {
            if (this.processing) {
                e.preventDefault();
                const message = 'Zahlung wird gerade verarbeitet. Möchten Sie wirklich die Seite verlassen?';
                e.returnValue = message; // For older browsers
                return message; // For modern browsers
            }
        });
    }
    
    handlePaymentElementChange(event) {
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
            this.showLoading();
            this.disableSubmitButton();
            this.clearError();
            
            // Confirm payment with Stripe
            const { error, paymentIntent } = await this.stripe.confirmPayment({
                elements: this.elements,
                confirmParams: {
                    return_url: `${window.location.origin}/checkout/erfolg`
                    // Removed payment_method_data - let Stripe Elements handle billing details
                },
                redirect: 'if_required'  // Only redirect for 3DS or SEPA redirects
            });
            
            if (error) {
                // Payment failed or requires action
                this.handlePaymentError(error);
            } else if (paymentIntent) {
                // Payment succeeded without redirect
                this.handlePaymentSuccess(paymentIntent);
            }
            
        } catch (error) {
            this.debugError('Error processing payment:', error);
            this.showError('Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        } finally {
            this.processing = false;
            this.hideLoading();
            this.enableSubmitButton();
        }
    }
    
    handlePaymentError(error) {
        this.debugError('Payment error:', error);
        
        let errorMessage = 'Die Zahlung konnte nicht verarbeitet werden.';
        
        switch (error.type) {
            case 'card_error':
                switch (error.code) {
                    case 'authentication_required':
                        errorMessage = '3D Secure Authentifizierung erforderlich. Sie werden weitergeleitet...';
                        // Stripe will handle the redirect automatically
                        return;
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