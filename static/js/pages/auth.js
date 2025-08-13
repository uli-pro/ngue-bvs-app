/**
 * Authentication Pages JavaScript
 * Handles login, register, and password reset functionality
 */

const AuthPage = {
    /**
     * Initialize auth functionality
     */
    init: function() {
        this.setupPasswordValidation();
        this.setupPasswordStrength();
    },

    /**
     * Setup password validation for forms with password confirmation
     */
    setupPasswordValidation: function() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const passwordInput = form.querySelector('input[name="password"]');
            const confirmInput = form.querySelector('input[name="password_confirm"], input[name="confirmPassword"]');
            
            if (passwordInput && confirmInput) {
                confirmInput.addEventListener('input', function() {
                    if (this.value !== passwordInput.value) {
                        this.setCustomValidity('Die Passwörter stimmen nicht überein.');
                    } else {
                        this.setCustomValidity('');
                    }
                });

                // Also validate when password changes
                passwordInput.addEventListener('input', function() {
                    if (confirmInput.value && confirmInput.value !== this.value) {
                        confirmInput.setCustomValidity('Die Passwörter stimmen nicht überein.');
                    } else {
                        confirmInput.setCustomValidity('');
                    }
                });
            }
        });
    },

    /**
     * Setup password strength indicator
     */
    setupPasswordStrength: function() {
        const passwordInput = document.querySelector('input[name="password"]');
        const strengthContainer = document.getElementById('passwordStrength');
        
        if (passwordInput && strengthContainer) {
            passwordInput.addEventListener('input', function() {
                AuthPage.updatePasswordStrength(this.value, strengthContainer);
            });
        }
    },

    /**
     * Update password strength indicator
     */
    updatePasswordStrength: function(password, container) {
        if (!container) return;

        const strength = FormManager.calculatePasswordStrength(password);
        const progressBar = container.querySelector('.progress-bar');
        const feedback = container.querySelector('.password-feedback');
        const strengthText = container.querySelector('.strength-text');

        if (progressBar) {
            progressBar.className = `progress-bar ${strength.class}`;
            progressBar.style.width = `${(strength.score / 5) * 100}%`;
        }

        if (strengthText) {
            strengthText.textContent = strength.text || '';
        }

        if (feedback) {
            if (strength.score === 5) {
                feedback.textContent = strength.feedback[0];
            } else {
                feedback.textContent = 'Benötigt: ' + strength.feedback.join(', ');
            }
        }

        // Show/hide container based on password content
        container.style.display = password ? 'block' : 'none';
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    AuthPage.init();
});