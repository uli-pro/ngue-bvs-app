/**
 * Download Utilities
 * Common download functionality across the application
 */

const DownloadManager = {
    /**
     * Download a certificate for a specific verse
     * @param {string} verseId - The verse ID
     */
    downloadCertificate: function(verseId) {
        // Simulate certificate download
        window.open(`/downloads/zertifikat-${verseId}.pdf`, '_blank');
        ToastManager.success('Zertifikat wird heruntergeladen...');
    },

    /**
     * Download a donation receipt for a specific verse
     * @param {string} verseId - The verse ID
     */
    downloadReceipt: function(verseId) {
        // Simulate receipt download
        window.open(`/downloads/spendenbescheinigung-${verseId}.pdf`, '_blank');
        ToastManager.success('Spendenbescheinigung wird heruntergeladen...');
    },

    /**
     * Download all documents as ZIP
     */
    downloadAllDocuments: function() {
        // Simulate bulk download
        setTimeout(() => {
            ToastManager.info('Alle Dokumente werden als ZIP-Datei heruntergeladen...');
        }, 500);
        
        // In real app, this would trigger a ZIP download
        window.open('/downloads/alle-dokumente.zip', '_blank');
    },

    /**
     * Download user data export
     */
    downloadUserData: function() {
        ToastManager.info('Ihr Datenexport wird vorbereitet. Sie erhalten eine E-Mail, wenn er fertig ist.');
        
        // Simulate data preparation
        setTimeout(() => {
            ToastManager.success('Datenexport bereit! Check your email.');
        }, 3000);
    },

    /**
     * Generic file download with toast notification
     * @param {string} url - The download URL
     * @param {string} filename - Optional filename for display
     * @param {string} message - Optional custom success message
     */
    downloadFile: function(url, filename = null, message = null) {
        window.open(url, '_blank');
        const displayMessage = message || `${filename || 'Datei'} wird heruntergeladen...`;
        ToastManager.success(displayMessage);
    }
};

// Make it globally available
window.DownloadManager = DownloadManager;

// Legacy compatibility functions
window.downloadCertificate = function(verseId) {
    DownloadManager.downloadCertificate(verseId);
};

window.downloadReceipt = function(verseId) {
    DownloadManager.downloadReceipt(verseId);
};

window.downloadAllDocuments = function() {
    DownloadManager.downloadAllDocuments();
};

window.downloadData = function() {
    DownloadManager.downloadUserData();
};