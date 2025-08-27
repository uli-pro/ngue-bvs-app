# HubSpot API Integration - Vollständige Implementierungsanleitung

**Status:** Bereit zur Implementierung  
**Priorität:** Hoch  
**Geschätzter Aufwand:** 4-6 Stunden  
**Datum:** 27. August 2025

## Überblick der Implementierung

Diese Anleitung führt dich durch die komplette HubSpot API-Integration in die NGÜ-Spendenplattform. Die Integration erfolgt ausschließlich server-seitig ohne Website-Tracking oder Cookies.

### Voraussetzungen von Daniel

**Erhaltene Daten von Daniel:**
- [ ] HubSpot Sandbox Access Token (Format: `pat-eu1-xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
- [ ] Bestätigung dass Custom Properties angelegt sind
- [ ] Später: Production Access Token für Beta-Phase

**Custom Properties die Daniel anlegen sollte:**
```
ngu_total_donated     → NGÜ Gesamtspende (Number)
ngu_verses_sponsored  → NGÜ Gesponserte Verse (Number)
ngu_last_donation_date → NGÜ Letzte Spende (Date)
ngu_first_donation_date → NGÜ Erste Spende (Date)
ngu_donation_count    → NGÜ Spendenanzahl (Number)
ngu_donor_type        → NGÜ Spendertyp (Dropdown: Einzelspender, Gruppenspender, Schenkender)
```

## Phase 1: HubSpot Service Klasse erstellen

### 1.1 Neue Datei erstellen: `hubspot_service.py`

```python
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

class HubSpotService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
    def create_or_update_contact(self, person, donation) -> Optional[Dict[str, Any]]:
        """
        Erstellt oder aktualisiert HubSpot-Kontakt basierend auf Person und Donation
        
        Args:
            person: Person-Objekt aus der Datenbank
            donation: Donation-Objekt aus der Datenbank
            
        Returns:
            HubSpot Contact Response oder None bei Fehler
        """
        try:
            # Erst nach existierendem Kontakt suchen
            existing_contact = self._find_contact_by_email(person.email)
            
            if existing_contact:
                return self._update_contact(existing_contact['id'], person, donation)
            else:
                return self._create_contact(person, donation)
                
        except Exception as e:
            logging.error(f"HubSpot API Error: {e}")
            return None
    
    def _find_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Sucht Kontakt nach E-Mail-Adresse"""
        url = f"{self.base_url}/crm/v3/objects/contacts/search"
        
        search_data = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email
                        }
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "ngu_total_donated"]
        }
        
        response = requests.post(url, headers=self.headers, json=search_data)
        response.raise_for_status()
        
        results = response.json().get('results', [])
        return results[0] if results else None
    
    def _create_contact(self, person, donation) -> Dict[str, Any]:
        """Erstellt neuen HubSpot-Kontakt"""
        url = f"{self.base_url}/crm/v3/objects/contacts"
        
        # Berechne Spenderstatistiken
        stats = self._calculate_donor_stats(person)
        
        contact_data = {
            "properties": {
                "email": person.email,
                "firstname": person.vorname or "",
                "lastname": person.nachname or "",
                "phone": person.telefon or "",
                "address": person.strasse or "",
                "zip": person.plz or "",
                "city": person.ort or "",
                "country": person.land or "Deutschland",
                
                # NGÜ Custom Properties
                "ngu_total_donated": str(stats['total_donated']),
                "ngu_verses_sponsored": str(stats['verses_sponsored']),
                "ngu_donation_count": str(stats['donation_count']),
                "ngu_first_donation_date": stats['first_donation_date'],
                "ngu_last_donation_date": stats['last_donation_date'],
                "ngu_donor_type": donation.donation_type or "einzelspende",
                
                # Tracking
                "hs_lead_status": "DONOR",
                "lifecyclestage": "customer"
            }
        }
        
        response = requests.post(url, headers=self.headers, json=contact_data)
        response.raise_for_status()
        return response.json()
    
    def _update_contact(self, contact_id: str, person, donation) -> Dict[str, Any]:
        """Aktualisiert existierenden HubSpot-Kontakt"""
        url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
        
        # Berechne aktuelle Spenderstatistiken
        stats = self._calculate_donor_stats(person)
        
        update_data = {
            "properties": {
                # Aktualisiere nur NGÜ-spezifische Felder
                "ngu_total_donated": str(stats['total_donated']),
                "ngu_verses_sponsored": str(stats['verses_sponsored']),
                "ngu_donation_count": str(stats['donation_count']),
                "ngu_last_donation_date": stats['last_donation_date'],
                
                # Ersten Spendentermin nur setzen falls leer
                "ngu_first_donation_date": stats['first_donation_date'],
                
                # Spendertyp falls noch nicht gesetzt
                "ngu_donor_type": donation.donation_type or "einzelspende"
            }
        }
        
        response = requests.patch(url, headers=self.headers, json=update_data)
        response.raise_for_status()
        return response.json()
    
    def _calculate_donor_stats(self, person) -> Dict[str, Any]:
        """Berechnet Spenderstatistiken aus der Datenbank"""
        from models import Donation  # Import hier um zirkuläre Imports zu vermeiden
        
        donations = Donation.query.filter_by(person_id=person.id).all()
        
        total_donated = sum(d.amount_cents for d in donations) / 100
        verses_sponsored = sum(len(d.verses) for d in donations if d.verses)
        donation_count = len(donations)
        
        # Datum-Formate für HubSpot
        first_donation = min(donations, key=lambda d: d.created_at) if donations else None
        last_donation = max(donations, key=lambda d: d.created_at) if donations else None
        
        first_date = first_donation.created_at.strftime('%Y-%m-%d') if first_donation else None
        last_date = last_donation.created_at.strftime('%Y-%m-%d') if last_donation else None
        
        return {
            'total_donated': total_donated,
            'verses_sponsored': verses_sponsored,
            'donation_count': donation_count,
            'first_donation_date': first_date,
            'last_donation_date': last_date
        }
    
    def test_connection(self) -> bool:
        """Testet die HubSpot-Verbindung"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts?limit=1"
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200
        except:
            return False

# Error Classes
class HubSpotAPIError(Exception):
    """HubSpot API Fehler"""
    pass

class HubSpotConnectionError(HubSpotAPIError):
    """HubSpot Verbindungsfehler"""
    pass
```

### 1.2 Environment-Konfiguration erweitern

Füge zu `.env` hinzu:
```bash
# HubSpot Configuration
HUBSPOT_ACCESS_TOKEN=pat-eu1-xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HUBSPOT_SYNC_ENABLED=true
HUBSPOT_ENVIRONMENT=sandbox  # oder 'production'
```

Füge zu `app.py` (Konfigurationsbereich) hinzu:
```python
# HubSpot Configuration
app.config['HUBSPOT_ACCESS_TOKEN'] = os.getenv('HUBSPOT_ACCESS_TOKEN')
app.config['HUBSPOT_SYNC_ENABLED'] = os.getenv('HUBSPOT_SYNC_ENABLED', 'false').lower() == 'true'
app.config['HUBSPOT_ENVIRONMENT'] = os.getenv('HUBSPOT_ENVIRONMENT', 'sandbox')
```

## Phase 2: Database-Model Erweitern

### 2.1 Donation-Model um HubSpot-Tracking erweitern

Füge zu `models.py` in der `Donation`-Klasse hinzu:
```python
# HubSpot Synchronisation
hubspot_sync_status = db.Column(db.String(20), default='pending')  # pending, synced, failed
hubspot_contact_id = db.Column(db.String(100), nullable=True)
hubspot_synced_at = db.Column(db.DateTime, nullable=True)
hubspot_error_message = db.Column(db.Text, nullable=True)

def mark_hubspot_synced(self, contact_id: str):
    """Markiert Spende als erfolgreich zu HubSpot synchronisiert"""
    self.hubspot_sync_status = 'synced'
    self.hubspot_contact_id = contact_id
    self.hubspot_synced_at = datetime.utcnow()
    self.hubspot_error_message = None

def mark_hubspot_failed(self, error_message: str):
    """Markiert Spende als fehlgeschlagen bei HubSpot-Sync"""
    self.hubspot_sync_status = 'failed'
    self.hubspot_error_message = error_message
```

### 2.2 Database Migration

Führe nach der Model-Änderung aus:
```bash
# Falls Flask-Migrate verwendet wird
flask db migrate -m "Add HubSpot sync fields to Donation"
flask db upgrade

# Falls nicht, füge manuell zur Datenbank hinzu:
# ALTER TABLE donations ADD COLUMN hubspot_sync_status VARCHAR(20) DEFAULT 'pending';
# ALTER TABLE donations ADD COLUMN hubspot_contact_id VARCHAR(100);
# ALTER TABLE donations ADD COLUMN hubspot_synced_at TIMESTAMP;
# ALTER TABLE donations ADD COLUMN hubspot_error_message TEXT;
```

## Phase 3: Integration in bestehenden Code

### 3.1 HubSpot-Sync-Funktion in app.py

Füge zu `app.py` hinzu:
```python
from hubspot_service import HubSpotService, HubSpotAPIError

def sync_donation_to_hubspot(donation):
    """
    Synchronisiert Spende mit HubSpot
    Wird nach erfolgreichem Stripe-Payment aufgerufen
    """
    if not app.config.get('HUBSPOT_SYNC_ENABLED'):
        app.logger.info("HubSpot sync disabled")
        return
    
    try:
        hubspot = HubSpotService(app.config['HUBSPOT_ACCESS_TOKEN'])
        
        # Teste Verbindung
        if not hubspot.test_connection():
            raise HubSpotAPIError("Connection test failed")
        
        # Synchronisiere Kontakt
        result = hubspot.create_or_update_contact(donation.person, donation)
        
        if result:
            # Erfolg
            donation.mark_hubspot_synced(result['id'])
            db.session.commit()
            
            app.logger.info(f"HubSpot sync successful for donation {donation.id}, contact {result['id']}")
        else:
            raise HubSpotAPIError("No result returned")
            
    except Exception as e:
        # Fehler
        error_msg = str(e)
        donation.mark_hubspot_failed(error_msg)
        db.session.commit()
        
        app.logger.error(f"HubSpot sync failed for donation {donation.id}: {error_msg}")
        
        # Wichtig: Fehler nicht weiterwerfen - Spende soll trotzdem erfolgreich sein
```

### 3.2 Integration in Stripe-Webhook

Finde in `app.py` den Stripe-Webhook-Handler und füge HubSpot-Sync hinzu:

```python
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    # ... bestehender Code ...
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Finde donation basierend auf payment_intent_id
        donation = Donation.query.filter_by(
            stripe_payment_intent_id=payment_intent['id']
        ).first()
        
        if donation:
            # Markiere als bezahlt (bestehender Code)
            donation.status = 'completed'
            donation.paid_at = datetime.utcnow()
            
            # NEU: Synchronisiere mit HubSpot
            sync_donation_to_hubspot(donation)
            
            db.session.commit()
            
            # ... Rest des bestehenden Codes ...
    
    return jsonify({'status': 'success'}), 200
```

### 3.3 Manuelle Synchronisation (Admin-Endpoint)

```python
@app.route('/admin/sync-hubspot/<int:donation_id>', methods=['POST'])
def manual_hubspot_sync(donation_id):
    """Manueller HubSpot-Sync für einzelne Spende (für Testing/Admin)"""
    donation = Donation.query.get_or_404(donation_id)
    
    if donation.status != 'completed':
        flash('Spende muss erfolgreich abgeschlossen sein', 'error')
        return redirect(request.referrer)
    
    sync_donation_to_hubspot(donation)
    
    if donation.hubspot_sync_status == 'synced':
        flash('HubSpot-Synchronisation erfolgreich', 'success')
    else:
        flash(f'HubSpot-Sync fehlgeschlagen: {donation.hubspot_error_message}', 'error')
    
    return redirect(request.referrer)
```

## Phase 4: Testing & Debugging

### 4.1 Test-Endpoint erstellen

```python
@app.route('/test/hubspot-connection')
def test_hubspot_connection():
    """Testet HubSpot-Verbindung (nur in Development)"""
    if not app.debug:
        abort(404)
    
    try:
        hubspot = HubSpotService(app.config['HUBSPOT_ACCESS_TOKEN'])
        
        if hubspot.test_connection():
            return jsonify({
                'status': 'success',
                'message': 'HubSpot connection successful',
                'environment': app.config.get('HUBSPOT_ENVIRONMENT'),
                'token_preview': app.config['HUBSPOT_ACCESS_TOKEN'][:20] + '...'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'HubSpot connection failed'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

### 4.2 Logging konfigurieren

```python
# In app.py nach der App-Erstellung
if app.config.get('HUBSPOT_SYNC_ENABLED'):
    # Separater Logger für HubSpot
    hubspot_logger = logging.getLogger('hubspot')
    hubspot_handler = logging.FileHandler('hubspot.log')
    hubspot_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    hubspot_logger.addHandler(hubspot_handler)
    hubspot_logger.setLevel(logging.INFO)
```

### 4.3 Test-Checklist

**Nach der Implementierung testen:**

1. **Connection Test**
   - [ ] `/test/hubspot-connection` aufrufen
   - [ ] Status 'success' erhalten

2. **Test-Spende durchführen**
   - [ ] Spende mit Test-Kreditkarte
   - [ ] Stripe-Webhook feuert
   - [ ] Donation status = 'completed'
   - [ ] hubspot_sync_status = 'synced'
   - [ ] Kontakt in HubSpot-Sandbox sichtbar

3. **Daten-Validierung in HubSpot**
   - [ ] Name und E-Mail korrekt übertragen
   - [ ] NGÜ Custom Properties korrekt befüllt
   - [ ] Spendenbetrag stimmt
   - [ ] Spendertyp korrekt gesetzt

4. **Error-Handling testen**
   - [ ] Ungültigen Token setzen → graceful failure
   - [ ] Netzwerk-Probleme simulieren
   - [ ] Fehler in hubspot.log protokolliert

## Phase 5: Production-Deployment

### 5.1 Environment-Switch

Für Beta-Launch:
```bash
# .env Production
HUBSPOT_ACCESS_TOKEN=pat-eu1-production-token-hier
HUBSPOT_ENVIRONMENT=production
HUBSPOT_SYNC_ENABLED=true
```

### 5.2 Monitoring & Maintenance

**Dashboard-Queries hinzufügen:**
```python
@app.route('/admin/hubspot-stats')
def hubspot_sync_stats():
    """HubSpot Sync-Statistiken für Admin-Dashboard"""
    stats = db.session.query(
        Donation.hubspot_sync_status,
        db.func.count(Donation.id).label('count')
    ).group_by(Donation.hubspot_sync_status).all()
    
    return jsonify({
        'sync_stats': dict(stats),
        'last_sync': Donation.query.filter(
            Donation.hubspot_synced_at.isnot(None)
        ).order_by(Donation.hubspot_synced_at.desc()).first().hubspot_synced_at
    })
```

**Retry-Mechanismus für fehlgeschlagene Syncs:**
```python
@app.route('/admin/retry-failed-syncs', methods=['POST'])
def retry_failed_hubspot_syncs():
    """Versucht fehlgeschlagene HubSpot-Syncs erneut"""
    failed_donations = Donation.query.filter_by(
        hubspot_sync_status='failed',
        status='completed'
    ).all()
    
    success_count = 0
    for donation in failed_donations:
        sync_donation_to_hubspot(donation)
        if donation.hubspot_sync_status == 'synced':
            success_count += 1
    
    db.session.commit()
    
    return jsonify({
        'total_retried': len(failed_donations),
        'successful': success_count,
        'still_failed': len(failed_donations) - success_count
    })
```

## Wichtige Hinweise

### Sicherheit
- Access Token niemals in Code committed
- Fehler nicht an Frontend weitergeben (Security durch Obskurität)
- Rate Limiting von HubSpot beachten (100 requests/10 seconds)

### Performance
- HubSpot-Sync läuft asynchron zum Spendenprozess
- Bei Fehlern wird Spende nicht blockiert
- Retry-Mechanismus für fehlgeschlagene Syncs

### Monitoring
- Alle HubSpot-Operationen loggen
- Dashboard für Sync-Status
- Alerting bei häufigen Fehlern

## Nächste Session - Quick Start

**Für die nächste Session als Prompt verwenden:**

"Implementiere die HubSpot API-Integration basierend auf `/todos/hubspot-api-integration-anleitung.md`. 

Daniel hat mir folgende Daten geschickt:
- Access Token: [TOKEN HIER EINFÜGEN]
- Custom Properties sind angelegt: [JA/NEIN]
- Besonderheiten: [FALLS VORHANDEN]

Beginne mit Phase 1 und arbeite die Anleitung systematisch ab. Teste jeden Schritt bevor du zum nächsten gehst."

**WICHTIG: Diese Anleitung ist vollständig und selbstständig umsetzbar!**