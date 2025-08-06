# Phase 2: Schweiz-Integration - Vorbereitungen

## Übersicht

Dieses Dokument beschreibt die notwendigen Vorbereitungen für die spätere Integration der Genfer Bibelgesellschaft als Schweizer Partner. Wir verwenden Option B: Einfacher Start mit Deutschland, strukturierte Erweiterung später.

## Hintergrund

- **Senior-Partner**: Genfer Bibelgesellschaft (Schweiz) - hält Hauptrechte an der NGÜ
- **Junior-Partner**: Peter-Schöffer-Stiftung (Deutschland) - ermöglicht deutsche Spenden
- **Phase 1**: Launch nur für Deutschland
- **Phase 2**: Integration der Schweizer Spendenmöglichkeit

## Datenbank-Vorbereitungen

### Organizations-Tabelle (für Phase 2)

```sql
CREATE TABLE organizations (
    id INTEGER PRIMARY KEY,
    code VARCHAR(2) NOT NULL,  -- 'DE', 'CH'
    name VARCHAR(255) NOT NULL,
    street VARCHAR(255),
    house_number VARCHAR(20),
    postal_code VARCHAR(10),
    city VARCHAR(100),
    country VARCHAR(2),
    currency VARCHAR(3) NOT NULL,  -- 'EUR', 'CHF'
    stripe_account_id VARCHAR(255),
    email_prefix VARCHAR(50),  -- für E-Mail-Templates
    tax_authority_name TEXT,
    tax_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Anpassung der Purchases-Tabelle

```sql
ALTER TABLE purchases ADD COLUMN organization_id INTEGER DEFAULT 1;
ALTER TABLE purchases ADD COLUMN currency VARCHAR(3) DEFAULT 'EUR';
ALTER TABLE purchases ADD COLUMN amount_in_currency DECIMAL(10,2);
```

## Template-Variablen

### Zu ersetzende Hardcoded-Werte

Statt direkter Texte immer Variablen verwenden:

| Hardcoded | Variable |
|-----------|----------|
| Peter-Schöffer-Stiftung | `{ORGANIZATION_NAME}` |
| 100€ | `{AMOUNT} {CURRENCY_SYMBOL}` |
| info@ngue-sponsoring.de | `{SUPPORT_EMAIL}` |
| Deutschland | `{COUNTRY_NAME}` |
| Spendenbescheinigung | `{TAX_RECEIPT_NAME}` |

### Beispiel-Implementierung

```python
# config.py
def get_org_config(org_code='DE'):
    configs = {
        'DE': {
            'name': 'Peter-Schöffer-Stiftung',
            'currency': 'EUR',
            'currency_symbol': '€',
            'amount': 100,
            'country': 'Deutschland',
            'tax_receipt_name': 'Spendenbescheinigung',
            'support_email': 'info@ngue-sponsoring.de'
        },
        # Phase 2:
        'CH': {
            'name': 'Genfer Bibelgesellschaft',
            'currency': 'CHF',
            'currency_symbol': 'CHF',
            'amount': 100,
            'country': 'Schweiz',
            'tax_receipt_name': 'Spendenbestätigung',
            'support_email': 'info@ngue-sponsoring.ch'
        }
    }
    return configs.get(org_code, configs['DE'])
```

## URL-Struktur-Vorbereitung

### Phase 1 (aktuell)
```
/                       # Startseite
/verse-auswahl         # Vers-Auswahl
/checkout/daten        # Checkout
```

### Phase 2 (vorbereitet)
```
/                      # Auto-Redirect basierend auf IP
/de/                   # Deutsche Version
/de/verse-auswahl
/ch/                   # Schweizer Version
/ch/verse-auswahl
```

### Flask-Route-Vorbereitung

```python
# Phase 1: Normale Routes
@app.route('/')
@app.route('/verse-auswahl')

# Phase 2-ready: Mit optionalem Länder-Prefix
@app.route('/')
@app.route('/<country>/')
def index(country=None):
    if not country:
        country = detect_country_from_ip()
    org_config = get_org_config(country.upper())
    return render_template('index.html', org=org_config)
```

## E-Mail-Template-Struktur

### Ordnerstruktur vorbereiten

```
templates/
├── email/
│   ├── de/
│   │   ├── standard-spender.html
│   │   ├── geschenk-empfaenger.html
│   │   └── ...
│   └── ch/  # Phase 2
│       ├── standard-spender.html
│       └── ...
```

### Template-Loader

```python
def get_email_template(template_name, country='de'):
    return f'email/{country}/{template_name}'
```

## Konfigurationsdatei-Struktur

### .env-Vorbereitung

```bash
# Phase 1
ORGANIZATION_DE_NAME="Peter-Schöffer-Stiftung"
ORGANIZATION_DE_STRIPE_KEY="sk_..."
ORGANIZATION_DE_CURRENCY="EUR"

# Phase 2 (vorbereitet, aber auskommentiert)
# ORGANIZATION_CH_NAME="Genfer Bibelgesellschaft"
# ORGANIZATION_CH_STRIPE_KEY="sk_..."
# ORGANIZATION_CH_CURRENCY="CHF"
```

## Was NICHT in Phase 1 implementiert wird

1. **Länderauswahl-UI** - kein Dropdown/Toggle
2. **Währungsumrechnung** - nur EUR
3. **IP-Geolocation** - keine automatische Erkennung
4. **Multi-Stripe-Accounts** - nur ein Account
5. **Schweizer Rechtstexte** - nur deutsche Texte

## Migrations-Strategie für Phase 2

### Schritt 1: Datenbank erweitern
```sql
-- Organizations-Tabelle hinzufügen
-- Bestehende Daten auf organization_id=1 setzen
UPDATE purchases SET organization_id = 1;
```

### Schritt 2: Templates duplizieren
```bash
cp -r templates/email/ templates/email/de/
# Später: Schweizer Versionen in templates/email/ch/
```

### Schritt 3: Routes erweitern
- Länder-Prefix optional machen
- Config-Loader implementieren

## Testing-Überlegungen

### Phase 1 Tests
- Fokus auf deutsche Funktionalität
- Hardcoded-Werte in Tests okay

### Phase 2 Tests vorbereiten
```python
# Parametrisierte Tests vorbereiten
@pytest.mark.parametrize("country,currency", [
    ('de', 'EUR'),
    # ('ch', 'CHF'),  # Phase 2
])
def test_checkout_currency(country, currency):
    # Test implementation
```

## Entwickler-Notizen

### DOS für Phase 1:
- ✅ Verwende Template-Variablen statt Hardcoding
- ✅ Strukturiere Datenbank mit Erweiterung im Hinterkopf
- ✅ Halte E-Mail-Templates modular
- ✅ Nutze Konfigurationsdateien

### DON'TS für Phase 1:
- ❌ Keine komplexe Multi-Tenant-Logik
- ❌ Keine Währungsauswahl implementieren
- ❌ Keine Länder-Routing-Logik
- ❌ Keine Schweizer Spezialfälle

## Zeitplan

- **Phase 1**: Wochen 1-7 (wie geplant)
- **Phase 2**: Nach erfolgreichem Launch und Abstimmung mit Genfer Bibelgesellschaft
- **Geschätzter Aufwand Phase 2**: 2-3 Wochen

## Offene Fragen für Phase 2

1. Verwendet die Genfer Bibelgesellschaft eigene Stripe-Accounts?
2. Sollen Spenden-Pools getrennt oder gemeinsam verwaltet werden?
3. Wie erfolgt die Abstimmung bei Vers-Reservierungen?
4. Gemeinsame oder getrennte Admin-Bereiche?
5. Wie werden die Zertifikat-Designs angepasst?

---

*Letzte Aktualisierung: {DATUM}*