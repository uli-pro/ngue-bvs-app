/**
 * Shopping Cart JavaScript
 * Handles cart functionality for the donation system
 */

const CartManager = {
    /**
     * Initialize cart functionality
     */
    init: function() {
        this.updateCartCounter();
        this.setupCartEvents();
    },

    /**
     * Update cart counter in navigation
     */
    updateCartCounter: function() {
        // Get cart count from session or local storage
        const cartCount = this.getCartCount();
        const cartCounters = document.querySelectorAll('.cart-counter');
        
        cartCounters.forEach(counter => {
            if (cartCount > 0) {
                counter.textContent = cartCount;
                counter.style.display = 'inline-block';
            } else {
                counter.style.display = 'none';
            }
        });
    },

    /**
     * Get cart count from session
     */
    getCartCount: function() {
        // This would be set by the server-side template
        if (typeof window.cartCount !== 'undefined') {
            return window.cartCount;
        }
        
        // Fallback to localStorage for client-side updates
        const cartData = localStorage.getItem('ngue_cart_count');
        return cartData ? parseInt(cartData) : 0;
    },

    /**
     * Set cart count in localStorage
     */
    setCartCount: function(count) {
        localStorage.setItem('ngue_cart_count', count.toString());
        window.cartCount = count;
        this.updateCartCounter();
    },

    /**
     * Setup cart-related event handlers
     */
    setupCartEvents: function() {
        // Handle "add to cart" buttons
        const addToCartButtons = document.querySelectorAll('.add-to-cart');
        addToCartButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.handleAddToCart(e);
            });
        });

        // Handle cart item removal
        const removeButtons = document.querySelectorAll('.remove-cart-item');
        removeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.handleRemoveFromCart(e);
            });
        });
    },

    /**
     * Handle adding items to cart
     */
    handleAddToCart: function(event) {
        event.preventDefault();
        
        const button = event.target.closest('.add-to-cart');
        const verseId = button.dataset.verseId;
        const donationType = button.dataset.donationType || 'einzelperson';
        
        // Show loading state
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Wird hinzugefügt...';
        
        // Add to cart via AJAX
        this.addToCart(verseId, donationType)
            .then(response => {
                if (response.success) {
                    // Update cart counter
                    this.setCartCount(response.cartCount);
                    
                    // Show success message
                    if (typeof ToastManager !== 'undefined') {
                        ToastManager.success('Vers wurde zum Spendenkorb hinzugefügt!');
                    }
                    
                    // Update button state
                    button.innerHTML = '<i class="fas fa-check me-2"></i>Im Korb';
                    button.classList.remove('btn-primary');
                    button.classList.add('btn-success');
                    
                    // Re-enable after delay
                    setTimeout(() => {
                        button.disabled = false;
                        button.innerHTML = originalText;
                        button.classList.remove('btn-success');
                        button.classList.add('btn-primary');
                    }, 2000);
                    
                } else {
                    throw new Error(response.message || 'Fehler beim Hinzufügen zum Korb');
                }
            })
            .catch(error => {
                console.error('Cart error:', error);
                
                // Show error message
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.error('Fehler: ' + error.message);
                }
                
                // Reset button
                button.disabled = false;
                button.innerHTML = originalText;
            });
    },

    /**
     * Handle removing items from cart
     */
    handleRemoveFromCart: function(event) {
        event.preventDefault();
        
        const button = event.target.closest('.remove-cart-item');
        const itemIndex = parseInt(button.dataset.itemIndex);
        
        if (confirm('Möchten Sie diesen Vers wirklich aus dem Spendenkorb entfernen?')) {
            // Show loading state
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            // Remove from cart via AJAX
            this.removeFromCart(itemIndex)
                .then(response => {
                    if (response.success) {
                        // Reload page to update cart display
                        window.location.reload();
                    } else {
                        throw new Error(response.message || 'Fehler beim Entfernen aus dem Korb');
                    }
                })
                .catch(error => {
                    console.error('Remove error:', error);
                    alert('Fehler beim Entfernen: ' + error.message);
                    
                    // Reset button
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-trash"></i>';
                });
        }
    },

    /**
     * Add item to cart via AJAX
     */
    addToCart: function(verseId, donationType) {
        return fetch('/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                verse_id: verseId,
                donation_type: donationType
            })
        })
        .then(response => response.json());
    },

    /**
     * Remove item from cart via AJAX
     */
    removeFromCart: function(itemIndex) {
        return fetch('/spendenkorb/entfernen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                item_index: itemIndex
            })
        })
        .then(response => response.json());
    },

    /**
     * Get CSRF token for AJAX requests
     */
    getCSRFToken: function() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    },

    /**
     * Clear cart
     */
    clearCart: function() {
        return fetch('/cart/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                this.setCartCount(0);
                window.location.href = '/vers-auswaehlen';
            }
            return response;
        });
    }
};

// Initialize cart when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    CartManager.init();
});

// Make CartManager globally available
window.CartManager = CartManager;