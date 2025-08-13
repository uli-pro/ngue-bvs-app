/**
 * Meine Verse Page JavaScript
 * Handles verse management functionality
 */

const MeineVersePage = {
    /**
     * Initialize verse page functionality
     */
    init: function() {
        // No specific initialization needed, all functions are called via onclick
    },

    /**
     * Filter verses based on form inputs
     */
    filterVerses: function() {
        const status = document.getElementById('statusFilter').value;
        const type = document.getElementById('typeFilter').value;
        const search = document.getElementById('searchFilter').value.toLowerCase();
        
        const verseCards = document.querySelectorAll('.verse-card');
        let visibleCount = 0;
        
        verseCards.forEach(card => {
            const cardStatus = card.dataset.status;
            const cardType = card.dataset.type;
            const cardText = card.textContent.toLowerCase();
            
            const statusMatch = !status || cardStatus === status;
            const typeMatch = !type || cardType === type;
            const searchMatch = !search || cardText.includes(search);
            
            if (statusMatch && typeMatch && searchMatch) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        // Update results count
        const resultsCount = document.getElementById('resultsCount');
        if (resultsCount) {
            resultsCount.textContent = `${visibleCount} Verse gefunden`;
        }
        
        // Show no results message
        const noResults = document.getElementById('noResults');
        if (noResults) {
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    },

    /**
     * Reset all filters
     */
    resetFilters: function() {
        document.getElementById('statusFilter').value = '';
        document.getElementById('typeFilter').value = '';
        document.getElementById('searchFilter').value = '';
        this.filterVerses();
    },

    /**
     * Share a verse
     */
    shareVerse: function(verseId) {
        // Get verse details (in real app, this would come from data)
        const verseReference = "Jeremia 29,11"; // Example
        const verseText = "Denn ich weiß die Gedanken, die ich über euch denke..."; // Example
        
        if (navigator.share) {
            navigator.share({
                title: `Bibelvers ${verseReference}`,
                text: `${verseReference}: ${verseText}`,
                url: window.location.href
            }).then(() => {
                ToastManager.success('Vers erfolgreich geteilt!');
            }).catch(err => {
                console.log('Error sharing:', err);
                this.fallbackShare(verseReference, verseText);
            });
        } else {
            this.fallbackShare(verseReference, verseText);
        }
    },

    /**
     * Fallback share method (copy to clipboard)
     */
    fallbackShare: function(reference, text) {
        const shareText = `${reference}: ${text}`;
        
        if (navigator.clipboard) {
            navigator.clipboard.writeText(shareText).then(() => {
                ToastManager.success('Vers-Text in die Zwischenablage kopiert!');
            }).catch(() => {
                this.showShareModal(shareText);
            });
        } else {
            this.showShareModal(shareText);
        }
    },

    /**
     * Show share modal with text to copy
     */
    showShareModal: function(text) {
        alert(`Kopieren Sie diesen Text:\n\n${text}`);
    },

    /**
     * Resend gift notification
     */
    resendGift: function(verseId) {
        ToastManager.info('Geschenk-Benachrichtigung wird erneut gesendet...');
        
        // Simulate API call
        setTimeout(() => {
            ToastManager.success('Geschenk-Benachrichtigung wurde erfolgreich versendet!');
        }, 2000);
    }
};

// Make functions globally available for onclick handlers
window.filterVerses = function() {
    MeineVersePage.filterVerses();
};

window.resetFilters = function() {
    MeineVersePage.resetFilters();
};

window.shareVerse = function(verseId) {
    MeineVersePage.shareVerse(verseId);
};

window.resendGift = function(verseId) {
    MeineVersePage.resendGift(verseId);
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    MeineVersePage.init();
});