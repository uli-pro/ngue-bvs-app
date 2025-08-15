# Payment Retry Strategien

**Status:** TODO - Noch zu entscheiden  
**Datum:** 15. August 2025

## Übersicht

Die NGÜ Bibelvers-Sponsoring App implementiert ein `retry_count` System in der Donations-Tabelle, um fehlgeschlagene Zahlungen zu verwalten. Diese Dokumentation beschreibt die möglichen Strategien für den Umgang mit Zahlungsfehlern.

## Aktuelle Implementierung

```python
retry_count = db.Column(db.Integer, default=0)
payment_status = db.Column(db.String(20), default='pending')
payment_failed_at = db.Column(db.DateTime)
stripe_last_error = db.Column(db.Text)
```

## Mögliche Retry-Strategien

### 1. Manueller User-Retry (Empfohlen für MVP)

**Ablauf:**
- Zahlung schlägt fehl → User wird zur Fehlerseite geleitet
- User kann neue Zahlungsmethode wählen und erneut versuchen
- `retry_count` wird bei jedem Versuch erhöht
- Nach 3 Versuchen: Warnung oder temporärer Block

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ User behält Kontrolle
- ✅ Keine automatischen Belastungen

**Code-Beispiel:**
```python
if donation.payment_status == 'failed' and donation.retry_count < 3:
    # Neuen PaymentIntent erstellen
    return redirect(url_for('retry_payment', donation_id=donation.id))
else:
    # Maximale Versuche erreicht
    return render_template('payment_blocked.html')
```

### 2. Automatischer Retry (Für temporäre Fehler)

**Anwendungsfälle:**
- Netzwerk-Timeouts
- Temporäre Bankprobleme
- "processing_error" von Stripe

**Ablauf:**
- Fehler wird klassifiziert
- Bei retryable Fehlern: Automatischer Retry nach 5/15/30 Minuten
- Bei permanenten Fehlern: Sofort an User weiterleiten

**Code-Beispiel:**
```python
retryable_errors = ['processing_error', 'temporary_failure']
if error_code in retryable_errors and donation.retry_count < 3:
    # Queue background job for retry
    schedule_payment_retry.delay(donation.id, delay_minutes=5)
```

### 3. Admin-gestützter Retry

**Anwendungsfall:**
- Kunde kontaktiert Support wegen fehlgeschlagener Zahlung
- Admin kann manuell Retry auslösen
- Nützlich für Edge-Cases

### 4. Intelligenter Retry basierend auf Fehlertyp

| Stripe Error | Aktion | Retry? |
|--------------|--------|---------|
| `card_declined` | User informieren, andere Karte vorschlagen | Ja |
| `insufficient_funds` | User informieren | Ja |
| `processing_error` | Automatisch retry | Ja |
| `invalid_cvc` | Sofort neue CVC anfordern | Nein |
| `expired_card` | Neue Karte anfordern | Nein |

## Entscheidungen die getroffen werden müssen

### 1. Retry-Limits
- **Wie viele Versuche** sollen erlaubt sein? (Empfehlung: 3)
- **Zeitfenster:** Wie lange bleiben fehlgeschlagene Spenden "retry-bar"? (24h? 7 Tage?)

### 2. User Experience
- Soll der User sofort zur Fehlerseite oder erst nach finaler Bestätigung?
- Welche Zahlungsmethoden sollen bei Retry angeboten werden?
- Automatische E-Mail bei fehlgeschlagener Zahlung?

### 3. Verse-Status
- Bei fehlgeschlagener Zahlung: Vers sofort wieder freigeben oder X Minuten warten?
- Bei temporären Fehlern: Vers "reserviert" halten?

### 4. Kommunikation
- E-Mail-Templates für verschiedene Fehlerfälle
- Admin-Dashboard für fehlgeschlagene Zahlungen
- Monitoring und Alerts

## Technische TODOs

1. **Error-Classification System** implementieren
2. **Background Jobs** für automatische Retries (Celery/Redis)
3. **Admin Dashboard** für Payment-Management
4. **E-Mail-Templates** für Fehlerbenachrichtigungen
5. **Monitoring** für Payment-Success-Rate

## Empfehlung für Phase 1

**Minimaler Ansatz für MVP:**
- Manueller User-Retry (max. 3 Versuche)
- Einfache Fehlerseite mit "Nochmal versuchen" Button
- Vers wird nach 30 Minuten wieder freigegeben
- Admin-Dashboard zeigt fehlgeschlagene Zahlungen

**Später erweitern:**
- Automatische Retries für temporäre Fehler
- Intelligente Fehlerklassifizierung
- E-Mail-Benachrichtigungen
- Erweiterte Analytics

---

**Nächste Schritte:** Business-Entscheidung über Retry-Strategie treffen, dann technische Umsetzung planen.