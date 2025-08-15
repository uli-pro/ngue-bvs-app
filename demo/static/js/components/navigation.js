/**
 * Navigation Component
 * Handles navigation highlighting and common navigation functionality
 */

const NavigationManager = {
    /**
     * Initialize navigation highlighting
     */
    init: function() {
        this.highlightActiveLink();
    },

    /**
     * Highlight the active navigation link based on current page
     */
    highlightActiveLink: function() {
        const currentLocation = location.pathname;
        const menuItems = document.querySelectorAll('.navbar-nav .nav-link');
        
        menuItems.forEach(item => {
            if(item.getAttribute('href') === currentLocation){
                item.classList.add('active');
            }
        });
    },

    /**
     * Go back in browser history
     */
    goBack: function() {
        window.history.back();
    },

    /**
     * Navigate to a specific URL
     * @param {string} url - The URL to navigate to
     */
    navigateTo: function(url) {
        window.location.href = url;
    },

    /**
     * Smooth scroll to an element
     * @param {string} targetId - The ID of the target element
     */
    scrollTo: function(targetId) {
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
};

// Make it globally available
window.NavigationManager = NavigationManager;

// Legacy compatibility function
window.goBack = function() {
    NavigationManager.goBack();
};