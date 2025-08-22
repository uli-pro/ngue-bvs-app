/**
 * Payment Status Checker - Simplified Version
 * Handles real-time payment status updates with clear status mapping
 */

class PaymentStatusChecker {
    constructor() {
        this.config = window.paymentStatusConfig || {};
        this.paymentIntentId = this.config.paymentIntentId;
        this.checkInterval = this.config.checkInterval || 3000; // 3 seconds
        this.maxChecks = this.config.maxChecks || 100; // ~5 minutes
        this.currentChecks = 0;
        this.intervalId = null;
        this.isChecking = false;
        this.lastStatus = null;
        
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
        if (!this.paymentIntentId) {
            this.debugError('No payment intent ID provided');
            this.updateStatusBox('danger', 'Fehler', 'Kein gültiger Zahlungsvorgang gefunden.');
            return;
        }
        
        this.debugLog('🔄 Initializing payment status checker for:', this.paymentIntentId);
        
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
            this.debugLog('🛑 Reached maximum checks, stopping automatic polling');
            return;
        }
        
        this.currentChecks++;
        this.debugLog(`🔍 Check #${this.currentChecks}: Checking status for ${this.paymentIntentId}`);
        
        try {
            const response = await fetch(`/api/payment/status/${this.paymentIntentId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.debugLog('📊 Status response:', data);
            
            if (data.success) {
                this.handleStatusUpdate(data);
            } else {
                throw new Error(data.error || 'Status check failed');
            }
            
        } catch (error) {
            this.debugError('❌ Error checking status:', error);
            
            // Only show error if we've tried multiple times
            if (this.currentChecks > 3) {
                this.updateStatusBox('warning', 'Verbindungsfehler', 
                    'Fehler beim Prüfen des Zahlungsstatus. Bitte laden Sie die Seite neu.');
            }
        }
    }
    
    handleStatusUpdate(data) {
        const status = data.status;
        const paymentMethodType = data.payment_method_type;
        
        // Only update if status has changed
        if (this.lastStatus === status) {
            return;
        }
        
        this.lastStatus = status;
        this.debugLog(`📈 Status changed to: ${status} (method: ${paymentMethodType})`);
        
        // Map status to user-friendly messages
        this.mapStatusToUI(status, paymentMethodType, data.error_message, data.redirect_url);
    }
    
    mapStatusToUI(status, paymentMethodType, errorMessage, redirectUrl) {
        switch (status) {
            case 'processing':
                // IMPORTANT: processing does NOT mean "accepted" for SEPA!
                // It means the payment is still being processed
                this.updateStatusBox('info', 'Zahlung wird verarbeitet...', 
                    'Wir überprüfen Ihre Zahlung. Dies kann einige Minuten dauern.');
                // Continue checking
                break;
                
            case 'succeeded':
                // Payment actually completed
                this.updateStatusBox('success', 'Zahlung erfolgreich!', 
                    'Ihre Spende wurde erfolgreich verarbeitet. Sie werden weitergeleitet...');
                this.stopStatusChecking();
                
                // Redirect after showing success message
                setTimeout(() => {
                    if (redirectUrl) {
                        window.location.href = redirectUrl;
                    }
                }, 2500); // Give user time to read the message
                break;
                
            case 'requires_action':
                this.updateStatusBox('warning', 'Zusätzliche Bestätigung erforderlich', 
                    'Ihre Bank benötigt eine weitere Bestätigung für diese Zahlung.');
                // Continue checking
                break;
                
            case 'requires_payment_method':
            case 'canceled':
            case 'payment_failed':
                // Payment failed - show simple, friendly German message
                this.updateStatusBox('danger', 'Zahlung fehlgeschlagen', 
                    'Die Zahlung ist leider fehlgeschlagen. Bitte versuchen Sie es erneut oder wählen Sie eine andere Zahlungsmethode.', true);
                this.stopStatusChecking();
                break;
                
            default:
                this.debugLog(`⚠️ Unknown status: ${status}`);
                // Continue checking for unknown statuses
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