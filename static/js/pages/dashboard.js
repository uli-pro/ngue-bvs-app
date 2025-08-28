/**
 * Dashboard Page JavaScript
 * Handles dashboard-specific functionality
 */

const DashboardPage = {
    /**
     * Initialize dashboard functionality
     */
    init: function() {
        this.initWelcomeAnimation();
    },

    /**
     * Initialize welcome animation for cards
     */
    initWelcomeAnimation: function() {
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'all 0.5s ease';
                
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 100);
            }, index * 100);
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    DashboardPage.init();
});