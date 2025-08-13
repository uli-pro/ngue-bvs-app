/**
 * Form Handling Component
 * Provides form validation and common form functionality
 */

const FormManager = {
    /**
     * Initialize Bootstrap form validation
     */
    initValidation: function() {
        // Bootstrap validation
        (function() {
            'use strict';
            window.addEventListener('load', function() {
                var forms = document.getElementsByClassName('needs-validation');
                var validation = Array.prototype.filter.call(forms, function(form) {
                    form.addEventListener('submit', function(event) {
                        if (form.checkValidity() === false) {
                            event.preventDefault();
                            event.stopPropagation();
                        }
                        form.classList.add('was-validated');
                    }, false);
                });
            }, false);
        })();
    },

    /**
     * Setup password validation for forms with password confirmation
     */
    setupPasswordValidation: function() {
        const newPasswordInputs = document.querySelectorAll('input[name="newPassword"], input[name="password"]');
        const confirmPasswordInputs = document.querySelectorAll('input[name="confirmPassword"], input[name="password_confirm"]');

        if (newPasswordInputs.length && confirmPasswordInputs.length) {
            confirmPasswordInputs.forEach(confirmInput => {
                const newPasswordInput = confirmInput.form.querySelector('input[name="newPassword"], input[name="password"]');
                if (newPasswordInput) {
                    confirmInput.addEventListener('input', function() {
                        if (this.value !== newPasswordInput.value) {
                            this.setCustomValidity('Die Passwörter stimmen nicht überein.');
                        } else {
                            this.setCustomValidity('');
                        }
                    });
                }
            });
        }
    },

    /**
     * Calculate password strength
     * @param {string} password - The password to check
     * @returns {Object} - Strength information
     */
    calculatePasswordStrength: function(password) {
        let score = 0;
        let feedback = [];

        if (!password) return { score: 0, feedback: ['Passwort eingeben'], class: 'bg-danger' };

        // Length check
        if (password.length >= 8) score += 1;
        else feedback.push('Mindestens 8 Zeichen');

        // Uppercase letters
        if (/[A-Z]/.test(password)) score += 1;
        else feedback.push('Großbuchstabe');

        // Lowercase letters
        if (/[a-z]/.test(password)) score += 1;
        else feedback.push('Kleinbuchstabe');

        // Numbers
        if (/\d/.test(password)) score += 1;
        else feedback.push('Zahl');

        // Special characters
        if (/[^A-Za-z0-9]/.test(password)) score += 1;
        else feedback.push('Sonderzeichen');

        // Return strength assessment
        if (score < 2) return { score, feedback, class: 'bg-danger', text: 'Schwach' };
        if (score < 4) return { score, feedback, class: 'bg-warning', text: 'Mittel' };
        return { score, feedback: ['Starkes Passwort!'], class: 'bg-success', text: 'Stark' };
    },

    /**
     * Update password strength indicator
     * @param {HTMLElement} passwordInput - The password input element
     * @param {HTMLElement} strengthIndicator - The strength indicator element
     */
    updatePasswordStrength: function(passwordInput, strengthIndicator) {
        if (!passwordInput || !strengthIndicator) return;

        passwordInput.addEventListener('input', function() {
            const strength = FormManager.calculatePasswordStrength(this.value);
            const progressBar = strengthIndicator.querySelector('.progress-bar');
            const feedbackText = strengthIndicator.querySelector('.password-feedback');

            if (progressBar) {
                progressBar.className = `progress-bar ${strength.class}`;
                progressBar.style.width = `${(strength.score / 5) * 100}%`;
            }

            if (feedbackText) {
                feedbackText.textContent = strength.feedback.join(', ');
            }
        });
    },

    /**
     * Setup form with common functionality
     * @param {HTMLElement} form - The form element
     * @param {Object} options - Configuration options
     */
    setupForm: function(form, options = {}) {
        if (!form) return;

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn ? submitBtn.innerHTML : '';

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (this.checkValidity()) {
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>' + (options.loadingText || 'Lädt...');
                }
                
                // Simulate processing (replace with actual form submission)
                setTimeout(() => {
                    if (options.onSuccess) {
                        options.onSuccess(new FormData(this));
                    } else {
                        ToastManager.success(options.successMessage || 'Erfolgreich gespeichert!');
                    }
                    
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalBtnText;
                    }
                    
                    if (options.resetForm) {
                        this.reset();
                        this.classList.remove('was-validated');
                    }
                }, options.delay || 1500);
            }
            
            this.classList.add('was-validated');
        });
    }
};

// Make it globally available
window.FormManager = FormManager;