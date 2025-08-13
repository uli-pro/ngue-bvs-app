/**
 * FAQ Page JavaScript
 * Handles FAQ functionality
 */

const FAQPage = {
    /**
     * Initialize FAQ functionality
     */
    init: function() {
        // No specific initialization needed
    },

    /**
     * Scroll to a specific category
     */
    scrollToCategory: function(categoryId) {
        NavigationManager.scrollTo(categoryId);
        
        // Optional: Highlight the target category briefly
        const targetElement = document.getElementById(categoryId);
        if (targetElement) {
            targetElement.style.backgroundColor = '#fff3cd';
            setTimeout(() => {
                targetElement.style.backgroundColor = '';
            }, 2000);
        }
    }
};

// Make function globally available for onclick handlers
window.scrollToCategory = function(categoryId) {
    FAQPage.scrollToCategory(categoryId);
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    FAQPage.init();
});