/* This file was developed with assistance from Claude Code (Anthropic)
 * for implementation and optimization. Core design is original work.
 */

/**
 * Payment Status Checker - Database-Driven Version
 *
 * Polls the database status (set by webhooks) instead of Stripe directly.
 * Waits for `pdfs_ready=true` before redirecting to success page.
 *
 * This approach ensures:
 * - No race conditions between success-page and webhook PDF generation
 * - PDFs are guaranteed to exist when user lands on success page
 * - Works correctly for both card (instant) and SEPA (delayed) payments
 */

class PaymentStatusChecker {
    constructor() {
        this.config = window.paymentStatusConfig || {};

        // NEW: Use donationId instead of paymentIntentId
        this.donationId = this.config.donationId;

        // Fallback to paymentIntentId for backward compatibility during transition
        this.paymentIntentId = this.config.paymentIntentId;

        this.checkInterval = this.config.checkInterval || 3000; // 3 seconds
        this.maxChecks = this.config.maxChecks || 100; // ~5 minutes
        this.currentChecks = 0;
        this.intervalId = null;
        this.isChecking = false;
        this.lastStatus = null;
        this.lastPdfsReady = null;

        // Debug mode detection
        this.debugMode = this.config.debugMode || false;

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        // Prefer donationId, fall back to paymentIntentId
        if (!this.donationId && !this.paymentIntentId) {
            this.debugError('No donation ID or payment intent ID provided');
            this.updateStatusBox('danger', 'Fehler', 'Kein gültiger Zahlungsvorgang gefunden.');
            return;
        }

        if (this.donationId) {
            this.debugLog('🔄 Initializing status checker for donation:', this.donationId);
        } else {
            this.debugLog('🔄 Fallback: Using payment intent ID:', this.paymentIntentId);
        }

        // Start status checking
        this.startStatusChecking();

        // Show manual refresh option after some time
        setTimeout(() => {
            this.showManualRefresh();
        }, 30000); // Show after 30 seconds
    }

    startStatusChecking() {
        if (this.isChecking) {
            return;
        }

        this.isChecking = true;
        this.debugLog('▶️ Starting status checking...');

        // Check immediately
        this.checkStatus();

        // Set up interval for subsequent checks
        this.intervalId = setInterval(() => {
            this.checkStatus();
        }, this.checkInterval);
    }

    stopStatusChecking() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isChecking = false;
        this.debugLog('⏹️ Stopped status checking');
    }

    async checkStatus() {
        // Stop if we've reached max checks
        if (this.currentChecks >= this.maxChecks) {
            this.stopStatusChecking();
            this.showManualRefresh();
            this.updateStatusBox('warning', 'Zeitüberschreitung',
                'Die Statusprüfung hat zu lange gedauert. Bitte laden Sie die Seite neu oder kontaktieren Sie uns.');
            this.debugLog('🛑 Reached maximum checks, stopping automatic polling');
            return;
        }

        this.currentChecks++;

        try {
            let response;
            let data;

            // Use new donation status endpoint if donationId is available
            if (this.donationId) {
                this.debugLog(`🔍 Check #${this.currentChecks}: Checking donation status for ${this.donationId}`);

                response = await fetch(`/api/donation/status/${this.donationId}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    if (response.status === 403) {
                        throw new Error('Session abgelaufen. Bitte laden Sie die Seite neu.');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                data = await response.json();
                this.debugLog('📊 Donation status response:', data);

                if (data.success) {
                    this.handleDonationStatusUpdate(data);
                } else {
                    throw new Error(data.error || 'Status check failed');
                }
            } else {
                // Fallback to old payment status endpoint
                this.debugLog(`🔍 Check #${this.currentChecks}: Fallback - checking payment status for ${this.paymentIntentId}`);

                response = await fetch(`/api/payment/status/${this.paymentIntentId}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                data = await response.json();
                this.debugLog('📊 Payment status response (fallback):', data);

                if (data.success) {
                    this.handlePaymentStatusUpdate(data);
                } else {
                    throw new Error(data.error || 'Status check failed');
                }
            }

        } catch (error) {
            this.debugError('❌ Error checking status:', error);

            // Only show error if we've tried multiple times
            if (this.currentChecks > 3) {
                this.updateStatusBox('warning', 'Verbindungsfehler',
                    error.message || 'Fehler beim Prüfen des Zahlungsstatus. Bitte laden Sie die Seite neu.');
            }
        }
    }

    /**
     * NEW: Handle database-driven donation status updates
     * This is the primary handler when donationId is available
     */
    handleDonationStatusUpdate(data) {
        const status = data.status;
        const pdfsReady = data.pdfs_ready;
        const redirectUrl = data.redirect_url;
        const errorRedirectUrl = data.error_redirect_url;

        // Only update UI if status or pdfs_ready has changed
        if (this.lastStatus === status && this.lastPdfsReady === pdfsReady) {
            return;
        }

        this.lastStatus = status;
        this.lastPdfsReady = pdfsReady;
        this.debugLog(`📈 Status: ${status}, PDFs ready: ${pdfsReady}`);

        // Map database status to UI
        this.mapDonationStatusToUI(status, pdfsReady, redirectUrl, errorRedirectUrl);
    }

    /**
     * NEW: Map database status to user-friendly UI
     *
     * Key difference from Stripe status:
     * - We wait for `pdfs_ready=true` (certificate_sent_at IS NOT NULL)
     * - This ensures PDFs exist before redirecting to success page
     */
    mapDonationStatusToUI(status, pdfsReady, redirectUrl, errorRedirectUrl) {
        // Handle error states first
        if (status === 'failed' || status === 'disputed') {
            this.updateStatusBox('danger', 'Zahlung fehlgeschlagen',
                'Die Zahlung konnte leider nicht abgeschlossen werden. Bitte versuchen Sie es erneut.', true);
            this.stopStatusChecking();

            // Redirect to error page after showing message
            if (errorRedirectUrl) {
                setTimeout(() => {
                    window.location.href = errorRedirectUrl;
                }, 3000);
            }
            return;
        }

        // PDFs are ready - redirect to success page!
        if (pdfsReady && redirectUrl) {
            this.updateStatusBox('success', 'Zahlung erfolgreich!',
                'Ihre Spende wurde erfolgreich verarbeitet. Sie werden weitergeleitet...');
            this.stopStatusChecking();

            // Redirect after showing success message
            setTimeout(() => {
                window.location.href = redirectUrl;
            }, 2000);
            return;
        }

        // Still processing - show appropriate message based on status
        switch (status) {
            case 'pending':
                this.updateStatusBox('info', 'Zahlung wird eingeleitet...',
                    'Wir verarbeiten Ihre Zahlung. Dies kann einen Moment dauern.');
                break;

            case 'processing':
                // SEPA payments stay in "processing" until bank confirms (5-6 days)
                // But we use "Optimistic Completion" - PDFs are sent early
                this.updateStatusBox('info', 'Zahlung wird verarbeitet...',
                    'Ihre Zahlung wird von der Bank verarbeitet. Das Zertifikat wird vorbereitet...');
                break;

            case 'completed':
                // Payment completed but PDFs not yet ready (rare edge case)
                this.updateStatusBox('info', 'Zahlung abgeschlossen',
                    'Ihre Zahlung war erfolgreich. Das Zertifikat wird erstellt...');
                break;

            default:
                this.debugLog(`⚠️ Unknown status: ${status}`);
                this.updateStatusBox('info', 'Status wird geprüft...',
                    'Wir überprüfen den Zahlungsstatus...');
                break;
        }
    }

    /**
     * LEGACY: Handle Stripe payment status updates (fallback)
     * Used when only paymentIntentId is available
     */
    handlePaymentStatusUpdate(data) {
        const status = data.status;
        const paymentMethodType = data.payment_method_type;

        // Only update if status has changed
        if (this.lastStatus === status) {
            return;
        }

        this.lastStatus = status;
        this.debugLog(`📈 Payment status changed to: ${status} (method: ${paymentMethodType})`);

        // Map status to user-friendly messages
        this.mapPaymentStatusToUI(status, paymentMethodType, data.error_message, data.redirect_url);
    }

    /**
     * LEGACY: Map Stripe status to UI (fallback)
     */
    mapPaymentStatusToUI(status, paymentMethodType, errorMessage, redirectUrl) {
        switch (status) {
            case 'processing':
                this.updateStatusBox('info', 'Zahlung wird verarbeitet...',
                    'Wir überprüfen Ihre Zahlung. Dies kann einige Minuten dauern.');
                break;

            case 'succeeded':
                this.updateStatusBox('success', 'Zahlung erfolgreich!',
                    'Ihre Spende wurde erfolgreich verarbeitet. Sie werden weitergeleitet...');
                this.stopStatusChecking();

                setTimeout(() => {
                    if (redirectUrl) {
                        window.location.href = redirectUrl;
                    }
                }, 2500);
                break;

            case 'requires_action':
                this.updateStatusBox('warning', 'Zusätzliche Bestätigung erforderlich',
                    'Ihre Bank benötigt eine weitere Bestätigung für diese Zahlung.');
                break;

            case 'requires_payment_method':
            case 'canceled':
            case 'payment_failed':
                this.updateStatusBox('danger', 'Zahlung fehlgeschlagen',
                    'Die Zahlung ist leider fehlgeschlagen. Bitte versuchen Sie es erneut oder wählen Sie eine andere Zahlungsmethode.', true);
                this.stopStatusChecking();
                break;

            default:
                this.debugLog(`⚠️ Unknown status: ${status}`);
                break;
        }
    }

    updateStatusBox(type, title, message, showRetryButton = false) {
        const statusBox = document.getElementById('status-box');
        const statusSpinner = document.getElementById('status-spinner');
        const statusTitle = document.getElementById('status-title');
        const statusMessage = document.getElementById('status-message');

        if (!statusBox) return;

        // Remove all alert classes
        statusBox.className = 'alert mb-4';
        statusBox.classList.add(`alert-${type}`);

        // Update spinner visibility
        if (statusSpinner) {
            statusSpinner.style.display = (type === 'info') ? 'block' : 'none';
        }

        // Update title with appropriate icon
        if (statusTitle) {
            let icon = '';
            switch (type) {
                case 'success':
                    icon = '<i class="fas fa-check-circle me-2"></i>';
                    break;
                case 'danger':
                    icon = '<i class="fas fa-exclamation-triangle me-2"></i>';
                    break;
                case 'warning':
                    icon = '<i class="fas fa-exclamation-circle me-2"></i>';
                    break;
                case 'info':
                default:
                    icon = '<i class="fas fa-clock me-2"></i>';
                    break;
            }
            statusTitle.innerHTML = icon + title;
        }

        // Update message
        if (statusMessage) {
            statusMessage.textContent = message;
        }

        // Add retry button if needed
        if (showRetryButton) {
            setTimeout(() => {
                const existingButton = statusBox.querySelector('.retry-button');
                if (!existingButton) {
                    const retryDiv = document.createElement('div');
                    retryDiv.className = 'mt-3 retry-button';
                    retryDiv.innerHTML = '<a href="/checkout/zahlung" class="btn btn-danger btn-sm"><i class="fas fa-redo me-1"></i> Zur Zahlungsseite zurück</a>';
                    statusBox.appendChild(retryDiv);
                }
            }, 500);
        }

        // Update progress bar based on status
        this.updateProgressBar(type);
    }

    updateProgressBar(type) {
        const progressBar = document.querySelector('.progress-bar');
        if (!progressBar) return;

        // Remove existing classes
        progressBar.classList.remove('bg-warning', 'bg-success', 'bg-danger');

        switch (type) {
            case 'success':
                progressBar.style.width = '100%';
                progressBar.classList.add('bg-success');
                break;
            case 'danger':
                progressBar.style.width = '100%';
                progressBar.classList.add('bg-danger');
                break;
            default:
                progressBar.style.width = '90%';
                progressBar.classList.add('bg-warning');
                break;
        }
    }

    showManualRefresh() {
        const manualRefreshDiv = document.getElementById('manual-refresh');
        if (manualRefreshDiv) {
            manualRefreshDiv.style.display = 'block';
        }
    }

    // Debug helper methods
    debugLog(...args) {
        if (this.debugMode) {
            console.log(...args);
        }
    }

    debugError(...args) {
        if (this.debugMode) {
            console.error(...args);
        } else {
            // In production, only log that an error occurred
            console.error('Payment status check error occurred');
        }
    }
}

// Initialize when script loads
window.paymentStatus = new PaymentStatusChecker();

// Export for global access
window.PaymentStatusChecker = PaymentStatusChecker;