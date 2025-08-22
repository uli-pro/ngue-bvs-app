# Checkout Flow Redesign Plan - NGÜ Bibelvers-Sponsoring App

## Übersicht
Komplette Neugestaltung des Checkout-Flows mit Progressive Disclosure, verbesserter UX und Vereinheitlichung der Datenerfassung.

## Abhängigkeiten
⚠️ **WICHTIG**: Dieses Redesign sollte NACH der Datenbank-Umstrukturierung (`database-refactoring-plan.md`) implementiert werden, da es auf der neuen Struktur aufbaut.

## Ziele
1. **Vereinfachter Flow** - Ein einheitlicher Pfad statt drei separate
2. **Progressive Disclosure** - Informationen nur wenn nötig zeigen
3. **Bessere UX** - Weniger Klicks, klarere Führung
4. **Mobile-First** - Optimiert für mobile Nutzung

## Aktueller vs. Neuer Flow

### Aktueller Flow (zu komplex)
```
1. Vers auswählen
2. Spendenart-Seite (3 Karten nebeneinander)
3. → Weiterleitung zu 3 verschiedenen Checkout-Seiten
4. Spendenkorb
5. Zahlung
```

### Neuer Flow (vereinfacht)
```
1. Vers auswählen
2. Spendenart mit Progressive Disclosure (Details direkt erfassen)
3. Spendenkorb
4. Zentrale Spendendaten-Erfassung (wenn Bescheinigung gewünscht)
5. Zahlung
```

## Phase 1: Neue Spendenart-Seite mit Progressive Disclosure

### 1.1 Template: `vers-spendenart-enhanced.html`

```html
{% extends "layout.html" %}

{% block title %}Spendenart auswählen{% endblock %}

{% block main %}
<!-- Selected Verse Display (kompakter) -->
<section class="verse-preview py-3 bg-light">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="card border-0 shadow-sm">
                    <div class="card-body p-3">
                        <h5 class="text-primary mb-2">{{ verse.reference }}</h5>
                        <p class="mb-0 text-truncate">{{ verse.text[:150] }}...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Donation Types with Progressive Disclosure -->
<section class="donation-types py-5">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <h2 class="text-center mb-4">Wie möchten Sie spenden?</h2>
                
                <!-- Einzelspende -->
                <div class="donation-option card mb-3" data-type="einzelperson">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-auto">
                                <i class="fas fa-user fa-3x text-success"></i>
                            </div>
                            <div class="col">
                                <h4 class="mb-1">Einzelspende</h4>
                                <p class="text-muted mb-0">Ich spende als Privatperson</p>
                                <small class="text-success">
                                    <i class="fas fa-check-circle"></i> 
                                    Zertifikat & Spendenbescheinigung möglich
                                </small>
                            </div>
                            <div class="col-auto">
                                <button class="btn btn-primary select-btn" data-type="einzelperson">
                                    Auswählen
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Gruppenspende -->
                <div class="donation-option card mb-3" data-type="gruppe">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-auto">
                                <i class="fas fa-users fa-3x text-warning"></i>
                            </div>
                            <div class="col">
                                <h4 class="mb-1">Gruppenspende</h4>
                                <p class="text-muted mb-0">Wir spenden als Gruppe/Organisation</p>
                                <small class="text-warning">
                                    <i class="fas fa-info-circle"></i> 
                                    Gruppenzertifikat, keine automatische Spendenbescheinigung
                                </small>
                            </div>
                            <div class="col-auto">
                                <button class="btn btn-primary expand-btn" data-type="gruppe">
                                    Auswählen
                                </button>
                            </div>
                        </div>
                        
                        <!-- Progressive Disclosure Content -->
                        <div class="expansion-content mt-4" style="display: none;">
                            <hr>
                            <form class="group-form">
                                <h5 class="mb-3">Gruppeninformationen</h5>
                                <div class="row">
                                    <div class="col-md-3 mb-3">
                                        <label class="form-label">Artikel</label>
                                        <select class="form-select" name="group_article" required>
                                            <option value="">Wählen...</option>
                                            <option value="Der">Der</option>
                                            <option value="Die">Die</option>
                                            <option value="Das">Das</option>
                                            <option value="">Ohne</option>
                                        </select>
                                    </div>
                                    <div class="col-md-9 mb-3">
                                        <label class="form-label">Gruppenname</label>
                                        <input type="text" class="form-control" name="group_name" 
                                               placeholder="z.B. Familie Schmidt" required>
                                        <small class="text-muted">Dieser Name erscheint auf dem Zertifikat</small>
                                    </div>
                                </div>
                                <div class="alert alert-warning">
                                    <i class="fas fa-info-circle"></i>
                                    <strong>Hinweis:</strong> Für Gruppenspenden ist keine automatische 
                                    Spendenbescheinigung möglich. Kontaktieren Sie uns bei Bedarf unter 
                                    info@schoeffer.org.
                                </div>
                                <button type="submit" class="btn btn-success">
                                    <i class="fas fa-shopping-cart"></i> 
                                    Zum Spendenkorb hinzufügen
                                </button>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- Geschenkspende -->
                <div class="donation-option card mb-3" data-type="geschenk">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-auto">
                                <i class="fas fa-gift fa-3x text-info"></i>
                            </div>
                            <div class="col">
                                <h4 class="mb-1">Geschenkspende</h4>
                                <p class="text-muted mb-0">Ich verschenke diesen Vers</p>
                                <small class="text-info">
                                    <i class="fas fa-check-circle"></i> 
                                    Geschenkzertifikat & Ihre Spendenbescheinigung
                                </small>
                            </div>
                            <div class="col-auto">
                                <button class="btn btn-primary expand-btn" data-type="geschenk">
                                    Auswählen
                                </button>
                            </div>
                        </div>
                        
                        <!-- Progressive Disclosure Content -->
                        <div class="expansion-content mt-4" style="display: none;">
                            <hr>
                            <form class="gift-form">
                                <h5 class="mb-3">Empfänger-Informationen</h5>
                                <div class="mb-3">
                                    <label class="form-label">Name des Empfängers</label>
                                    <input type="text" class="form-control" name="recipient_name" 
                                           placeholder="Max Mustermann" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">E-Mail des Empfängers (optional)</label>
                                    <input type="email" class="form-control" name="recipient_email" 
                                           placeholder="empfaenger@example.com">
                                    <small class="text-muted">
                                        Wenn angegeben, senden wir das Zertifikat direkt an den Empfänger
                                    </small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Persönliche Nachricht (optional)</label>
                                    <textarea class="form-control" name="gift_message" rows="3" 
                                              placeholder="Herzlichen Glückwunsch zum Geburtstag!"></textarea>
                                </div>
                                <div class="form-check mb-3">
                                    <input type="checkbox" class="form-check-input" 
                                           id="directSend" name="direct_send">
                                    <label class="form-check-label" for="directSend">
                                        Zertifikat direkt an Empfänger senden
                                    </label>
                                </div>
                                <button type="submit" class="btn btn-success">
                                    <i class="fas fa-shopping-cart"></i> 
                                    Zum Spendenkorb hinzufügen
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Back Navigation -->
<div class="container mb-4">
    <a href="/vers-auswaehlen" class="btn btn-link">
        <i class="fas fa-arrow-left"></i> Anderen Vers wählen
    </a>
</div>

<style>
.donation-option {
    transition: all 0.3s ease;
    border: 2px solid #e0e0e0;
}

.donation-option:hover {
    border-color: #007bff;
    box-shadow: 0 4px 12px rgba(0,123,255,0.15);
}

.donation-option.expanded {
    border-color: #28a745;
    box-shadow: 0 4px 12px rgba(40,167,69,0.2);
}

.expansion-content {
    animation: slideDown 0.3s ease;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.text-truncate {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
</style>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Handle Einzelspende (direct to cart)
    document.querySelectorAll('.select-btn[data-type="einzelperson"]').forEach(btn => {
        btn.addEventListener('click', function() {
            addToCart('einzelperson', {});
        });
    });
    
    // Handle expansion for Gruppe and Geschenk
    document.querySelectorAll('.expand-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.donation-option');
            const expansion = card.querySelector('.expansion-content');
            const wasExpanded = card.classList.contains('expanded');
            
            // Close all other expansions
            document.querySelectorAll('.donation-option').forEach(opt => {
                opt.classList.remove('expanded');
                opt.querySelector('.expansion-content').style.display = 'none';
            });
            
            // Toggle current
            if (!wasExpanded) {
                card.classList.add('expanded');
                expansion.style.display = 'block';
                // Focus first input
                const firstInput = expansion.querySelector('input, select');
                if (firstInput) firstInput.focus();
            }
        });
    });
    
    // Handle group form submission
    document.querySelector('.group-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        addToCart('gruppe', {
            group_article: formData.get('group_article'),
            group_name: formData.get('group_name')
        });
    });
    
    // Handle gift form submission
    document.querySelector('.gift-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        addToCart('geschenk', {
            recipient_name: formData.get('recipient_name'),
            recipient_email: formData.get('recipient_email'),
            gift_message: formData.get('gift_message'),
            direct_send: formData.get('direct_send') === 'on'
        });
    });
    
    // Add to cart function
    function addToCart(donationType, donationDetails) {
        const cartItem = {
            verse_id: {{ verse.id }},
            donation_type: donationType,
            donation_details: donationDetails
        };
        
        // Add to session cart via AJAX
        fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'
            },
            body: JSON.stringify(cartItem)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success animation
                showSuccessAnimation();
                
                // Redirect to cart after animation
                setTimeout(() => {
                    window.location.href = '/spendenkorb';
                }, 1000);
            }
        });
    }
    
    function showSuccessAnimation() {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'success-overlay';
        overlay.innerHTML = `
            <div class="success-content">
                <i class="fas fa-check-circle fa-5x text-success"></i>
                <h3 class="mt-3">Zum Korb hinzugefügt!</h3>
            </div>
        `;
        document.body.appendChild(overlay);
        
        // Add animation class
        setTimeout(() => overlay.classList.add('show'), 10);
    }
});
</script>

<style>
.success-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255,255,255,0.95);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.success-overlay.show {
    opacity: 1;
}

.success-content {
    text-align: center;
    animation: bounceIn 0.5s ease;
}

@keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.05); }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); opacity: 1; }
}
</style>
{% endblock %}
```

### 1.2 API Route für Cart Management

```python
# app.py - Neue Cart API

@app.route("/api/cart/add", methods=["POST"])
@csrf.exempt
def api_cart_add():
    """Add item to cart with donation details"""
    data = request.get_json()
    
    # Validate input
    verse_id = data.get('verse_id')
    donation_type = data.get('donation_type')
    donation_details = data.get('donation_details', {})
    
    # Check verse availability
    verse = Verse.query.get(verse_id)
    if not verse or verse.is_sponsored:
        return jsonify({'success': False, 'error': 'Vers nicht verfügbar'}), 400
    
    # Initialize cart if needed
    if 'cart' not in session:
        session['cart'] = []
    
    # Add to cart
    cart_item = {
        'verse_id': verse_id,
        'verse_reference': verse.reference,
        'donation_type': donation_type,
        'donation_details': donation_details,
        'amount': 100.00,
        'currency': 'EUR',
        'added_at': datetime.utcnow().isoformat()
    }
    
    session['cart'].append(cart_item)
    session.modified = True
    
    return jsonify({
        'success': True, 
        'cart_count': len(session['cart']),
        'item': cart_item
    })
```

## Phase 2: Neuer Spendenkorb

### 2.1 Enhanced Cart Template

```html
<!-- spendenkorb-enhanced.html -->
{% extends "layout.html" %}

{% block title %}Spendenkorb{% endblock %}

{% block main %}
<div class="container py-5">
    <h2 class="mb-4">
        <i class="fas fa-shopping-cart"></i> 
        Ihr Spendenkorb
        <span class="badge bg-primary">{{ cart_items|length }}</span>
    </h2>
    
    {% if cart_items %}
    <div class="row">
        <div class="col-lg-8">
            <!-- Cart Items -->
            {% for item in cart_items %}
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col">
                            <h5 class="mb-1">{{ item.verse.reference }}</h5>
                            <p class="text-muted mb-2 small">{{ item.verse.text[:100] }}...</p>
                            
                            <!-- Donation Type Badge -->
                            {% if item.donation_type == 'gruppe' %}
                            <span class="badge bg-warning text-dark">
                                <i class="fas fa-users"></i> 
                                Gruppenspende: {{ item.donation_details.group_article }} 
                                {{ item.donation_details.group_name }}
                            </span>
                            {% elif item.donation_type == 'geschenk' %}
                            <span class="badge bg-info">
                                <i class="fas fa-gift"></i> 
                                Geschenk für: {{ item.donation_details.recipient_name }}
                            </span>
                            {% else %}
                            <span class="badge bg-success">
                                <i class="fas fa-user"></i> 
                                Einzelspende
                            </span>
                            {% endif %}
                        </div>
                        <div class="col-auto">
                            <div class="text-end">
                                <div class="h5 mb-2">100,00 €</div>
                                <button class="btn btn-sm btn-outline-danger remove-item" 
                                        data-index="{{ loop.index0 }}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
            
            <!-- Add More Button -->
            <div class="text-center mt-3">
                <a href="/vers-auswaehlen" class="btn btn-outline-primary">
                    <i class="fas fa-plus-circle"></i> 
                    Weitere Verse sponsern
                </a>
            </div>
        </div>
        
        <div class="col-lg-4">
            <!-- Summary -->
            <div class="card sticky-top">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Zusammenfassung</h5>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span>Verse:</span>
                        <strong>{{ cart_items|length }}</strong>
                    </div>
                    <div class="d-flex justify-content-between mb-3">
                        <span>Einzelpreis:</span>
                        <span>100,00 €</span>
                    </div>
                    <hr>
                    <div class="d-flex justify-content-between mb-4">
                        <h5>Gesamt:</h5>
                        <h5>{{ (cart_items|length * 100)|currency }}</h5>
                    </div>
                    
                    <!-- Receipt Info -->
                    <div class="alert alert-info small">
                        <i class="fas fa-info-circle"></i>
                        {% set has_group = cart_items|selectattr('donation_type', 'equalto', 'gruppe')|list|length > 0 %}
                        {% if has_group %}
                        <strong>Hinweis:</strong> Gruppenspenden erhalten keine automatische 
                        Spendenbescheinigung.
                        {% else %}
                        Sie können im nächsten Schritt eine Spendenbescheinigung anfordern.
                        {% endif %}
                    </div>
                    
                    <a href="/checkout/spendendaten" class="btn btn-success btn-lg w-100">
                        Weiter zur Datenerfassung
                        <i class="fas fa-arrow-right"></i>
                    </a>
                </div>
            </div>
        </div>
    </div>
    {% else %}
    <!-- Empty Cart -->
    <div class="text-center py-5">
        <i class="fas fa-shopping-cart fa-5x text-muted mb-4"></i>
        <h3>Ihr Spendenkorb ist leer</h3>
        <p class="text-muted">Wählen Sie einen Vers aus, um zu beginnen.</p>
        <a href="/vers-auswaehlen" class="btn btn-primary btn-lg">
            <i class="fas fa-book"></i> Vers auswählen
        </a>
    </div>
    {% endif %}
</div>
{% endblock %}
```

## Phase 3: Zentrale Spendendaten-Erfassung

### 3.1 Unified Checkout Data Page

```html
<!-- checkout-spendendaten.html -->
{% extends "layout.html" %}

{% block title %}Ihre Daten{% endblock %}

{% block main %}
<div class="container py-5">
    <!-- Progress Bar -->
    <div class="progress mb-4" style="height: 5px;">
        <div class="progress-bar" style="width: 60%;"></div>
    </div>
    
    <div class="row">
        <div class="col-lg-8">
            <h2 class="mb-4">Ihre Kontaktdaten</h2>
            
            <form id="checkoutForm" method="POST">
                <!-- Email (always required) -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">E-Mail-Adresse</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">E-Mail *</label>
                            <input type="email" class="form-control" id="email" 
                                   name="email" required>
                            <small class="text-muted">
                                Für den Versand der Zertifikate und Kommunikation
                            </small>
                        </div>
                        
                        <!-- Auto-fill notification -->
                        <div id="autoFillNotice" class="alert alert-success" style="display:none;">
                            <i class="fas fa-check-circle"></i>
                            Wir haben Ihre Daten vom letzten Besuch. Bitte überprüfen Sie diese.
                        </div>
                    </div>
                </div>
                
                <!-- Receipt Section (conditional) -->
                {% set needs_receipt = not has_only_groups %}
                {% if needs_receipt %}
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">Spendenbescheinigung</h5>
                    </div>
                    <div class="card-body">
                        <div class="form-check form-switch mb-3">
                            <input type="checkbox" class="form-check-input" 
                                   id="wantsReceipt" name="wantsReceipt">
                            <label class="form-check-label" for="wantsReceipt">
                                Ich möchte eine Spendenbescheinigung erhalten
                            </label>
                        </div>
                        
                        <!-- Receipt Form (hidden by default) -->
                        <div id="receiptForm" style="display:none;">
                            <hr>
                            <h6 class="mb-3">Angaben für die Spendenbescheinigung</h6>
                            
                            <!-- Name Fields -->
                            <div class="row mb-3">
                                <div class="col-md-3">
                                    <label class="form-label">Anrede *</label>
                                    <select class="form-select" name="salutation">
                                        <option value="">Bitte wählen</option>
                                        <option value="Herr">Herr</option>
                                        <option value="Frau">Frau</option>
                                        <option value="Eheleute">Eheleute</option>
                                        <option value="Firma">Firma</option>
                                    </select>
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label">Vorname *</label>
                                    <input type="text" class="form-control" name="firstName">
                                </div>
                                <div class="col-md-5">
                                    <label class="form-label">Nachname *</label>
                                    <input type="text" class="form-control" name="lastName">
                                </div>
                            </div>
                            
                            <!-- Address Fields -->
                            <div class="row mb-3">
                                <div class="col-md-8">
                                    <label class="form-label">Straße *</label>
                                    <input type="text" class="form-control" name="street">
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label">Hausnummer *</label>
                                    <input type="text" class="form-control" name="houseNumber">
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <label class="form-label">PLZ *</label>
                                    <input type="text" class="form-control" name="postalCode">
                                </div>
                                <div class="col-md-8">
                                    <label class="form-label">Ort *</label>
                                    <input type="text" class="form-control" name="city">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {% else %}
                <!-- Info for group-only donations -->
                <div class="alert alert-warning">
                    <i class="fas fa-info-circle"></i>
                    <strong>Hinweis:</strong> Für reine Gruppenspenden ist keine automatische 
                    Spendenbescheinigung möglich. Bei Bedarf kontaktieren Sie uns unter 
                    info@schoeffer.org.
                </div>
                {% endif %}
                
                <!-- Newsletter & Privacy -->
                <div class="card mb-4">
                    <div class="card-body">
                        <div class="form-check mb-3">
                            <input type="checkbox" class="form-check-input" 
                                   id="newsletter" name="newsletter">
                            <label class="form-check-label" for="newsletter">
                                Ich möchte über den Fortschritt der NGÜ-Übersetzung informiert werden
                            </label>
                        </div>
                        
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input" 
                                   id="privacy" name="privacy" required>
                            <label class="form-check-label" for="privacy">
                                Ich habe die <a href="/datenschutz" target="_blank">Datenschutzerklärung</a> 
                                gelesen und akzeptiere diese *
                            </label>
                        </div>
                        
                        <div class="form-check mt-2">
                            <input type="checkbox" class="form-check-input" 
                                   id="saveData" name="saveData" checked>
                            <label class="form-check-label" for="saveData">
                                Meine Daten für zukünftige Spenden speichern (Vorausfüllung)
                            </label>
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="btn btn-success btn-lg">
                    Weiter zur Zahlung
                    <i class="fas fa-lock"></i>
                </button>
            </form>
        </div>
        
        <!-- Side Summary -->
        <div class="col-lg-4">
            <div class="card sticky-top">
                <div class="card-header bg-secondary text-white">
                    <h5 class="mb-0">Ihre Spende</h5>
                </div>
                <div class="card-body">
                    <!-- List cart items -->
                    {% for item in cart_items %}
                    <div class="mb-2">
                        <strong>{{ item.verse.reference }}</strong><br>
                        <small class="text-muted">
                            {% if item.donation_type == 'gruppe' %}
                                Gruppe: {{ item.donation_details.group_name }}
                            {% elif item.donation_type == 'geschenk' %}
                                Geschenk für: {{ item.donation_details.recipient_name }}
                            {% else %}
                                Einzelspende
                            {% endif %}
                        </small>
                    </div>
                    {% endfor %}
                    
                    <hr>
                    <div class="d-flex justify-content-between">
                        <strong>Gesamt:</strong>
                        <strong>{{ total_amount|currency }}</strong>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('email');
    const receiptCheckbox = document.getElementById('wantsReceipt');
    const receiptForm = document.getElementById('receiptForm');
    const autoFillNotice = document.getElementById('autoFillNotice');
    
    // Toggle receipt form
    if (receiptCheckbox) {
        receiptCheckbox.addEventListener('change', function() {
            receiptForm.style.display = this.checked ? 'block' : 'none';
            
            // Make fields required when shown
            const fields = receiptForm.querySelectorAll('input, select');
            fields.forEach(field => {
                field.required = this.checked;
            });
        });
    }
    
    // Email auto-fill check
    emailInput.addEventListener('blur', async function() {
        const email = this.value.trim();
        if (!email || !email.includes('@')) return;
        
        try {
            const response = await fetch(`/api/person/check?email=${encodeURIComponent(email)}`);
            const data = await response.json();
            
            if (data.exists && data.hasData) {
                // Show PLZ verification modal
                showPlzVerification(email);
            }
        } catch (error) {
            console.error('Auto-fill check failed:', error);
        }
    });
    
    function showPlzVerification(email) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Willkommen zurück!</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Wir haben Ihre Daten von einem früheren Besuch gefunden.</p>
                        <p>Bitte geben Sie Ihre Postleitzahl zur Bestätigung ein:</p>
                        <input type="text" class="form-control" id="plzVerify" 
                               placeholder="Ihre PLZ" maxlength="5">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            Neu eingeben
                        </button>
                        <button type="button" class="btn btn-primary" id="verifyBtn">
                            Daten laden
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Handle verification
        document.getElementById('verifyBtn').addEventListener('click', async function() {
            const plz = document.getElementById('plzVerify').value;
            
            const response = await fetch('/api/verify-plz', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: email, plz: plz})
            });
            
            const data = await response.json();
            
            if (data.success) {
                fillForm(data.data);
                autoFillNotice.style.display = 'block';
                bsModal.hide();
            } else {
                alert('Die Postleitzahl stimmt nicht überein.');
            }
        });
    }
    
    function fillForm(data) {
        // Fill all matching fields
        for (const [key, value] of Object.entries(data)) {
            const field = document.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = value;
                } else {
                    field.value = value;
                }
            }
        }
        
        // Show receipt form if data available
        if (data.firstName && receiptCheckbox) {
            receiptCheckbox.checked = true;
            receiptForm.style.display = 'block';
        }
    }
});
</script>
{% endblock %}
```

## Phase 4: Backend-Anpassungen

### 4.1 Updated Routes

```python
# app.py - New unified checkout flow

@app.route("/checkout/spendendaten", methods=["GET", "POST"])
def checkout_spendendaten():
    """Unified data collection after cart"""
    
    # Check cart exists
    if 'cart' not in session or not session['cart']:
        flash("Ihr Spendenkorb ist leer.", "warning")
        return redirect(url_for("vers_auswaehlen"))
    
    cart_items = []
    has_only_groups = True
    
    # Load cart data
    for item in session['cart']:
        verse = Verse.query.get(item['verse_id'])
        if verse:
            cart_items.append({
                'verse': verse,
                'donation_type': item['donation_type'],
                'donation_details': item.get('donation_details', {})
            })
            
            if item['donation_type'] != 'gruppe':
                has_only_groups = False
    
    total_amount = len(cart_items) * 100
    
    if request.method == "POST":
        email = request.form.get('email', '').strip().lower()
        
        # Find or create person
        person = Person.find_or_create(
            email=email,
            first_name=request.form.get('firstName'),
            last_name=request.form.get('lastName'),
            salutation=request.form.get('salutation'),
            street=request.form.get('street'),
            house_number=request.form.get('houseNumber'),
            postal_code=request.form.get('postalCode'),
            city=request.form.get('city'),
            newsletter_opt_in=request.form.get('newsletter') == 'on',
            save_data_consent=request.form.get('saveData') != 'off'
        )
        
        db.session.commit()
        
        # Store person_id for payment processing
        session['checkout_person_id'] = person.id
        session['wants_receipt'] = request.form.get('wantsReceipt') == 'on'
        
        return redirect(url_for('checkout_zahlung'))
    
    return render_template("checkout-spendendaten.html",
                         cart_items=cart_items,
                         total_amount=total_amount,
                         has_only_groups=has_only_groups)

@app.route("/checkout/zahlung")
def checkout_zahlung():
    """Final payment page"""
    
    if 'checkout_person_id' not in session:
        return redirect(url_for('checkout_spendendaten'))
    
    person = Person.query.get(session['checkout_person_id'])
    cart_items = session.get('cart', [])
    
    # Create donations in pending state
    donations = []
    for item in cart_items:
        verse = Verse.query.get(item['verse_id'])
        if verse and not verse.is_sponsored:
            donation = Donation(
                person_id=person.id,
                verse_id=verse.id,
                donation_type=item['donation_type'],
                donation_details=item.get('donation_details'),
                person_snapshot=person.to_snapshot(),
                amount=100.00,
                wants_receipt=session.get('wants_receipt', False),
                privacy_consent=True,
                payment_status='pending'
            )
            db.session.add(donation)
            donations.append(donation)
    
    db.session.commit()
    
    # Store donation IDs for payment confirmation
    session['pending_donation_ids'] = [d.id for d in donations]
    
    return render_template("checkout-zahlung.html",
                         person=person,
                         donations=donations,
                         total_amount=len(donations) * 100,
                         stripe_public_key=os.environ.get('STRIPE_PUBLIC_KEY'))
```

## Phase 5: Mobile Optimization

### 5.1 Responsive CSS

```css
/* Mobile-first responsive design */

/* Mobile (default) */
.donation-option {
    margin-bottom: 1rem;
}

.donation-option .row {
    flex-direction: column;
    text-align: center;
}

.donation-option .col-auto {
    width: 100%;
    margin-top: 1rem;
}

.donation-option .btn {
    width: 100%;
}

/* Tablet and up */
@media (min-width: 768px) {
    .donation-option .row {
        flex-direction: row;
        text-align: left;
    }
    
    .donation-option .col-auto {
        width: auto;
        margin-top: 0;
    }
    
    .donation-option .btn {
        width: auto;
    }
}

/* Sticky summary only on desktop */
@media (max-width: 991px) {
    .sticky-top {
        position: relative !important;
    }
}

/* Compact verse preview on mobile */
@media (max-width: 576px) {
    .verse-preview .card-body {
        padding: 0.75rem !important;
    }
    
    .verse-preview h5 {
        font-size: 1rem;
    }
    
    .verse-preview p {
        font-size: 0.875rem;
    }
}
```

## Phase 6: Testing Plan

### 6.1 User Flow Tests

```python
# test_checkout_flow.py

def test_einzelspende_flow():
    """Test direct einzelspende to cart"""
    # Select verse
    response = client.get('/vers/jesaja-43-1/spendenart')
    assert response.status_code == 200
    
    # Add einzelspende to cart
    response = client.post('/api/cart/add', json={
        'verse_id': 123,
        'donation_type': 'einzelperson',
        'donation_details': {}
    })
    assert response.json['success']
    
    # Check cart
    response = client.get('/spendenkorb')
    assert b'Einzelspende' in response.data

def test_gruppe_progressive_disclosure():
    """Test gruppe with inline form"""
    # Add gruppe to cart with details
    response = client.post('/api/cart/add', json={
        'verse_id': 123,
        'donation_type': 'gruppe',
        'donation_details': {
            'group_article': 'Die',
            'group_name': 'Familie Schmidt'
        }
    })
    assert response.json['success']
    
    # Verify details in cart
    with client.session_transaction() as sess:
        cart_item = sess['cart'][0]
        assert cart_item['donation_details']['group_name'] == 'Familie Schmidt'

def test_unified_checkout():
    """Test unified checkout data page"""
    # Add mixed items to cart
    with client.session_transaction() as sess:
        sess['cart'] = [
            {'verse_id': 1, 'donation_type': 'einzelperson', 'donation_details': {}},
            {'verse_id': 2, 'donation_type': 'gruppe', 'donation_details': {'group_name': 'Test'}}
        ]
    
    # Go to checkout
    response = client.get('/checkout/spendendaten')
    assert b'Spendenbescheinigung' in response.data  # Should show receipt option
    
    # Submit data
    response = client.post('/checkout/spendendaten', data={
        'email': 'test@example.com',
        'wantsReceipt': 'on',
        'firstName': 'Max',
        'lastName': 'Mustermann',
        'privacy': 'on'
    })
    assert response.status_code == 302  # Redirect to payment
```

## Phase 7: Migration Strategy

### 7.1 Schrittweise Migration

1. **Deploy neue Templates** parallel zu alten
2. **Feature Flag** für neuen Flow
3. **A/B Testing** mit kleiner Nutzergruppe
4. **Monitoring** der Conversion Rates
5. **Vollständige Umstellung** nach Validierung

### 7.2 Rollback Plan

```python
# Feature flag in app.py
USE_NEW_CHECKOUT_FLOW = os.environ.get('USE_NEW_CHECKOUT_FLOW', 'false').lower() == 'true'

@app.route("/vers/<verse_id>/spendenart")
def vers_spendenart(verse_id):
    if USE_NEW_CHECKOUT_FLOW:
        return render_template("vers-spendenart-enhanced.html", verse=verse)
    else:
        return render_template("vers-spendenart.html", verse=verse)
```

## Zeitplan

- **Phase 1**: 4 Stunden (Progressive Disclosure UI)
- **Phase 2**: 2 Stunden (Cart Enhancement)
- **Phase 3**: 3 Stunden (Unified Checkout)
- **Phase 4**: 2 Stunden (Backend)
- **Phase 5**: 2 Stunden (Mobile Optimization)
- **Phase 6**: 2 Stunden (Testing)

**Gesamt**: ~15 Stunden

## Abhängigkeiten

⚠️ **WICHTIG**: Implementierung NACH `database-refactoring-plan.md`:
- Neue `persons` Tabelle muss existieren
- JSONB `donation_details` in `donations`
- Person.find_or_create() Methode verfügbar

## Vorteile des neuen Flows

1. **Weniger Klicks**: 5 → 3-4 Schritte
2. **Klarere Struktur**: Ein Pfad statt drei
3. **Bessere Mobile UX**: Progressive Disclosure optimal für kleine Screens
4. **Flexibler**: Einfach neue Spendenarten hinzufügen
5. **Wartbarer Code**: Weniger Templates, einheitliche Logik

## Metriken zum Tracking

- **Conversion Rate**: Vers-Auswahl → Zahlung
- **Drop-off Points**: Wo brechen Nutzer ab?
- **Time to Checkout**: Durchschnittliche Zeit
- **Mobile vs Desktop**: Conversion-Unterschiede
- **A/B Test Results**: Alt vs Neu