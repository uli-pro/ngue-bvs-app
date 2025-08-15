/**
 * Checkout Pages JavaScript
 * Handles checkout flow functionality
 */

const CheckoutPage = {
    currentDonationType: null,

    /**
     * Initialize checkout functionality
     */
    init: function() {
        this.loadStoredDonationType();
        this.setupDonationTypeSelection();
        this.setupContactForm();
    },

    /**
     * Load stored donation type from session storage
     */
    loadStoredDonationType: function() {
        this.currentDonationType = sessionStorage.getItem('ngue_donation_type') || 'einzelperson';
    },

    /**
     * Setup donation type selection (for pages that have it)
     */
    setupDonationTypeSelection: function() {
        const donationCards = document.querySelectorAll('.donation-type-card');
        if (donationCards.length === 0) return;

        donationCards.forEach(card => {
            card.addEventListener('click', function() {
                const radio = this.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    CheckoutPage.updateSelectedType();
                }
            });
        });
        
        const donationTypeRadios = document.querySelectorAll('input[name="donation_type"]');
        donationTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => this.updateSelectedType());
        });

        // Initial setup
        this.updateSelectedType();
    },

    /**
     * Update selected donation type
     */
    updateSelectedType: function() {
        const selectedType = document.querySelector('input[name="donation_type"]:checked');
        if (!selectedType) return;
        
        this.currentDonationType = selectedType.value;
        
        // Store in session storage
        sessionStorage.setItem('ngue_donation_type', this.currentDonationType);
        
        // Show contact form for donation
        document.getElementById('donation-type-selection').style.display = 'none';
        document.getElementById('contact-form').classList.remove('d-none');
        this.setupContactForm();
    },

    /**
     * Proceed with selected type
     */
    proceedWithType: function() {
        const selectedType = document.querySelector('input[name="donation_type"]:checked');
        if (!selectedType) {
            ToastManager.error('Bitte wählen Sie eine Spende-Art aus.');
            return;
        }
        
        this.currentDonationType = selectedType.value;
        
        // Store in session storage
        sessionStorage.setItem('ngue_donation_type', this.currentDonationType);
        
        // Show contact form for donation
        document.getElementById('donation-type-selection').style.display = 'none';
        document.getElementById('contact-form').classList.remove('d-none');
        this.setupContactForm();
    },

    /**
     * Setup contact form functionality
     */
    setupContactForm: function() {
        const form = document.getElementById('contactForm');
        if (!form) return;

        const wantReceiptCheckbox = document.getElementById('wantReceipt');
        const receiptForm = document.getElementById('receipt-form');
        
        // Setup gift recipient form
        this.setupGiftForm();
        
        // Handle receipt checkbox (only for non-group donations)
        if (wantReceiptCheckbox && receiptForm) {
            wantReceiptCheckbox.addEventListener('change', function() {
                const requiredFields = receiptForm.querySelectorAll('[required]');
                
                if (this.checked) {
                    receiptForm.style.display = 'block';
                    requiredFields.forEach(field => field.setAttribute('required', 'required'));
                } else {
                    receiptForm.style.display = 'none';
                    requiredFields.forEach(field => field.removeAttribute('required'));
                }
            });
        }

        // Setup form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (this.checkValidity()) {
                const submitBtn = this.querySelector('button[type="submit"]');
                const originalText = submitBtn.innerHTML;
                
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Speichere Daten...';
                
                setTimeout(() => {
                    window.location.href = '/checkout/zusammenfassung';
                }, 1000);
            }
            
            this.classList.add('was-validated');
        });
    },

    /**
     * Edit data (from summary page)
     */
    editData: function() {
        window.history.back();
    },

    /**
     * Process payment (from summary page)
     */
    processPayment: function() {
        ToastManager.info('Weiterleitung zur Zahlungsabwicklung...');
        
        // Simulate redirect to payment provider
        setTimeout(() => {
            // In real app, this would redirect to Stripe or other payment provider
            window.location.href = '/checkout/erfolg';
        }, 2000);
    },

    /**
     * Setup gift recipient form functionality
     */
    setupGiftForm: function() {
        const giftDirectCheckbox = document.getElementById('gift_direct_send');
        const giftDirectFields = document.getElementById('gift_direct_fields');
        const giftRecipientEmail = document.getElementById('gift_recipient_email');
        const giftMessageField = document.getElementById('gift_message_field');
        
        if (!giftDirectCheckbox || !giftDirectFields || !giftRecipientEmail || !giftMessageField) return;
        
        // Toggle direct send fields visibility
        giftDirectCheckbox.addEventListener('change', function() {
            if (this.checked) {
                giftDirectFields.style.display = 'block';
                giftRecipientEmail.required = true;
            } else {
                giftDirectFields.style.display = 'none';
                giftRecipientEmail.required = false;
                giftRecipientEmail.value = '';
                // Hide message field when checkbox is unchecked
                giftMessageField.style.display = 'none';
                document.getElementById('gift_message').value = '';
            }
        });

        // Show personal message field when user starts typing email
        giftRecipientEmail.addEventListener('input', function() {
            if (this.value.length > 0 && giftDirectCheckbox.checked) {
                giftMessageField.style.display = 'block';
            } else {
                giftMessageField.style.display = 'none';
                if (this.value.length === 0) {
                    document.getElementById('gift_message').value = '';
                }
            }
        });

        // Initialize: Since checkbox is checked by default, show fields
        if (giftDirectCheckbox.checked) {
            giftDirectFields.style.display = 'block';
            giftRecipientEmail.required = true;
        }
    }
};

// Make functions globally available for onclick handlers
window.proceedWithType = function() {
    CheckoutPage.proceedWithType();
};

window.editData = function() {
    CheckoutPage.editData();
};

window.processPayment = function() {
    CheckoutPage.processPayment();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    CheckoutPage.init();
});