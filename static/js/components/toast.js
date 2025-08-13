/**
 * Toast Notification Component
 * Provides consistent toast notifications across the application
 */

const ToastManager = {
    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - The type of toast (info, success, warning, danger)
     * @param {number} duration - How long to show the toast (default: 4000ms)
     */
    show: function(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after specified duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    },

    /**
     * Show success toast
     */
    success: function(message, duration = 4000) {
        this.show(message, 'success', duration);
    },

    /**
     * Show error toast
     */
    error: function(message, duration = 5000) {
        this.show(message, 'danger', duration);
    },

    /**
     * Show warning toast
     */
    warning: function(message, duration = 4000) {
        this.show(message, 'warning', duration);
    },

    /**
     * Show info toast
     */
    info: function(message, duration = 4000) {
        this.show(message, 'info', duration);
    }
};

// Make it globally available
window.ToastManager = ToastManager;

// Legacy compatibility function
window.showToast = function(message, type = 'info') {
    ToastManager.show(message, type);
};