/* This file was developed with assistance from Claude Code (Anthropic)
 * for implementation and optimization. Core design is original work.
 */

/**
 * CSRF Token Helper for NGÜ BVS App
 * Provides centralized CSRF token management for all AJAX requests
 */

class CSRFHelper {
    constructor() {
        this.token = this.getCSRFToken();
    }

    /**
     * Get CSRF token from meta tag
     * @returns {string|null} CSRF token or null if not found
     */
    getCSRFToken() {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }
        
        // Fallback: try to find token in any form
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        console.warn('CSRF token not found! Requests may fail.');
        return null;
    }

    /**
     * Get headers object with CSRF token for JSON requests
     * @returns {Object} Headers object with Content-Type and CSRF token
     */
    getJSONHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['X-CSRFToken'] = this.token;
        }
        
        return headers;
    }

    /**
     * Get headers object with CSRF token for form requests
     * @returns {Object} Headers object with CSRF token
     */
    getFormHeaders() {
        const headers = {};
        
        if (this.token) {
            headers['X-CSRFToken'] = this.token;
        }
        
        return headers;
    }

    /**
     * Make a secure JSON POST request with CSRF protection
     * @param {string} url - Request URL
     * @param {Object} data - Request data
     * @param {Object} options - Additional fetch options
     * @returns {Promise<Response>} Fetch response
     */
    async postJSON(url, data, options = {}) {
        return fetch(url, {
            method: 'POST',
            headers: {
                ...this.getJSONHeaders(),
                ...(options.headers || {})
            },
            body: JSON.stringify(data),
            ...options
        });
    }

    /**
     * Make a secure GET request with CSRF protection (if needed)
     * @param {string} url - Request URL
     * @param {Object} options - Additional fetch options
     * @returns {Promise<Response>} Fetch response
     */
    async get(url, options = {}) {
        return fetch(url, {
            method: 'GET',
            headers: {
                ...(options.headers || {})
            },
            ...options
        });
    }
}

// Create global instance
window.csrfHelper = new CSRFHelper();

// Export for module systems (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CSRFHelper;
}