/**
 * Profile Page JavaScript
 * Handles profile-specific functionality
 */

const ProfilePage = {
    autoSaveTimeout: null,

    /**
     * Initialize profile functionality
     */
    init: function() {
        this.setupForms();
        this.setupAutoSave();
    },

    /**
     * Setup all forms on the profile page
     */
    setupForms: function() {
        // Profile form
        const profileForm = document.getElementById('profileForm');
        if (profileForm) {
            FormManager.setupForm(profileForm, {
                loadingText: 'Speichere...',
                successMessage: 'Ihre Änderungen wurden gespeichert.'
            });
        }

        // Password form
        const passwordForm = document.getElementById('passwordForm');
        if (passwordForm) {
            this.setupPasswordForm(passwordForm);
        }

        // Preferences form
        const preferencesForm = document.getElementById('preferencesForm');
        if (preferencesForm) {
            FormManager.setupForm(preferencesForm, {
                loadingText: 'Speichere...',
                successMessage: 'Ihre Einstellungen wurden aktualisiert.',
                delay: 1000
            });
        }
    },

    /**
     * Setup password form with custom validation
     */
    setupPasswordForm: function(form) {
        const newPasswordInput = document.getElementById('newPassword');
        const confirmPasswordInput = document.getElementById('confirmPassword');
        
        // Password confirmation validation
        if (confirmPasswordInput && newPasswordInput) {
            confirmPasswordInput.addEventListener('input', function() {
                if (this.value !== newPasswordInput.value) {
                    this.setCustomValidity('Die Passwörter stimmen nicht überein.');
                } else {
                    this.setCustomValidity('');
                }
            });
        }

        // Custom form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (this.checkValidity()) {
                const submitBtn = this.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Ändere Passwort...';
                
                setTimeout(() => {
                    ToastManager.success('Ihr Passwort wurde erfolgreich geändert.');
                    this.reset();
                    this.classList.remove('was-validated');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-key me-2"></i>Passwort ändern';
                }, 2000);
            }
            
            this.classList.add('was-validated');
        });
    },

    /**
     * Setup auto-save functionality
     */
    setupAutoSave: function() {
        const profileFields = document.querySelectorAll('#profileForm input, #profileForm select');
        
        profileFields.forEach(field => {
            field.addEventListener('input', () => {
                clearTimeout(this.autoSaveTimeout);
                this.autoSaveTimeout = setTimeout(() => {
                    console.log('Auto-saving profile data...');
                    // Could implement auto-save here
                }, 2000);
            });
        });
    },

    /**
     * Request account deletion
     */
    requestAccountDeletion: function() {
        if (confirm('Sind Sie sicher, dass Sie Ihr Konto löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden.')) {
            ToastManager.warning('Ihre Anfrage zur Kontolöschung wurde eingereicht. Wir werden uns in Kürze bei Ihnen melden.');
        }
    }
};

// Make functions globally available for onclick handlers
window.requestAccountDeletion = function() {
    ProfilePage.requestAccountDeletion();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    ProfilePage.init();
});