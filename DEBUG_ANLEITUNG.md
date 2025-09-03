# 🐛 Debug-System Anleitung für Anfänger

## Übersicht: Was wurde implementiert?

Deine NGÜ-App hat jetzt **zwei Arten von Logging**:

### 1. **Printf Debugging** (Kurzfristig - zum Entfernen)
- 🔧 Markiert mit `🔧 DEBUG POINT X` 
- Zeigt **jeden Schritt** im Detail
- Emojis: `🐛` für app.py, `🔧` für models.py, `💳` für stripe_service.py

### 2. **Strategic Logging** (Langfristig - kann bleiben)
- 📊 Markiert mit `📊 STRATEGIC`
- Fokus auf die **3 kritischsten Problemzonen**
- Emoji: `📊` für wichtige Business-Logic

---

## Wo finde ich die Logs?

### **1. Terminal (Live-Ansicht)**
Wenn du die App startest mit `python app.py`, siehst du die Logs **direkt im Terminal**:

```bash
🐛 [14:23:45.123] [DEBUG] [142345-abc123] REQUEST_START: {"method": "GET", "path": "/vers-auswaehlen"}
📊 STRATEGIC [cart_session] session_recovery_start: ✅ - {"session_id": "sess_xyz", "cart_corrupt": false}
🔧 [14:23:45.456] [MODEL-DEBUG] PERSON_FIND_OR_CREATE_START: {"email_domain": "gmail.com", "provided_fields": ["first_name", "last_name"]}
💳 [14:23:46.789] [STRIPE-DEBUG] WEBHOOK_SUCCESS_START: {"payment_intent_id": "pi_1234567890", "amount": 10000}
```

### **2. Log-Datei (Persistente Speicherung)**
Alle Logs werden auch in `debug_flow.log` gespeichert:

```bash
# Datei ansehen
cat debug_flow.log

# Live verfolgen (während die App läuft)
tail -f debug_flow.log
```

---

## Log-Format verstehen

### **Basis-Format:**
```
[Zeitstempel] [Level] [Trace-ID] Aktion: {JSON-Daten}
```

**Beispiel:**
```
🐛 [14:23:45.123] [DEBUG] [142345-abc123] CART_ITEM_VALIDATION: {"item_type": "dict", "verse_id": 1234}
```

- `14:23:45.123` = Genaue Zeit (Stunde:Minute:Sekunde.Millisekunden)
- `142345-abc123` = **Trace-ID** (verfolgt einen kompletten Request)
- `CART_ITEM_VALIDATION` = Was gerade passiert
- `{"item_type": "dict", "verse_id": 1234}` = Konkrete Daten

### **Strategic Logs:**
```
📊 STRATEGIC [cart_session] session_recovery_start: ✅ - {"session_id": "sess_xyz"}
```

- `✅` = Erfolgreich, `❌` = Fehlgeschlagen
- `[cart_session]` = Welcher Bereich betroffen ist

---

## Die wichtigsten Log-Kategorien

### **🛒 Cart & Session Problems**
```bash
# Alle Cart-Probleme finden
grep -E "CART_.*INVALID|CART_CORRUPTION|SESSION_.*FAILED" debug_flow.log

# Beispiel-Output:
# CART_ITEM_INVALID: {"reason": "missing_field", "field": "verse_id"}
# CART_CORRUPTION_FIXED: {"action": "reset_to_empty", "reason": "cart_missing_or_invalid"}
```

### **👤 Person Data Issues**
```bash
# Person-Daten-Konflikte finden
grep -E "PERSON_DATA_UPDATED|PERSON_.*FAILED" debug_flow.log

# Beispiel-Output:
# PERSON_DATA_UPDATED: {"changed_fields": ["street", "postal_code"], "person_id": 42}
```

### **💳 Payment Flow Problems**
```bash
# Stripe/Payment Issues
grep -E "WEBHOOK_.*ERROR|DONATION_.*FAILED" debug_flow.log

# Beispiel-Output:
# WEBHOOK_DONATION_NOT_FOUND: {"payment_intent_id": "pi_123", "error": "donation_not_found"}
```

---

## Praktische Debugging-Strategien

### **1. Problem verfolgen mit Trace-ID**

Wenn ein User meldet "Mein Warenkorb ist verschwunden", findest du so den kompletten Ablauf:

```bash
# 1. Finde die Trace-ID vom Problem-Zeitpunkt
grep -E "CART_.*EMPTY|SESSION_.*CORRUPT" debug_flow.log | tail -5

# Output: [14:23:45.123] [142345-abc123] SESSION_CART_CORRUPTED: {...}

# 2. Alle Logs für diese Trace-ID anzeigen
grep "142345-abc123" debug_flow.log

# Das zeigt dir JEDEN Schritt für diesen einen Request!
```

### **2. Häufigste Fehler finden**

```bash
# Top 10 Error-Typen der letzten Stunde
grep -E "ERROR|FAILED|INVALID" debug_flow.log | \
awk -F'[\\[\\]]' '{print $6}' | \
sort | uniq -c | sort -nr | head -10

# Beispiel-Output:
#    15 CART_ITEM_INVALID
#     8 PERSON_DATA_UPDATED  
#     3 WEBHOOK_DONATION_NOT_FOUND
```

### **3. User-spezifische Probleme**

```bash
# Alle Logs für eine Email-Domain
grep "gmail.com" debug_flow.log

# Alle Payment-Probleme heute
grep "$(date +%Y-%m-%d)" debug_flow.log | grep -E "WEBHOOK_.*ERROR|DONATION_.*FAILED"
```

---

## Typische Fehlerszenarien & Lösungen

### **❌ Problem: "Warenkorb ist leer"**

**Log suchen:**
```bash
grep -E "CART_.*EMPTY|SESSION_.*CORRUPT" debug_flow.log | tail -10
```

**Typischer Log-Verlauf:**
```
🐛 CART_PAGE_ACCESS: {"has_cart": false, "session_id": "unknown"}
📊 STRATEGIC [cart_session] session_recovery_start: ✅ - {"cart_corrupt": true}
🐛 SESSION_CART_CORRUPTED: {"problem": "missing_or_invalid_cart"}
📊 STRATEGIC [cart_session] cart_corruption_fixed: ✅ - {"action": "reset_to_empty"}
```

**Bedeutung:** Session war korrupt → wurde automatisch repariert → Warenkorb geleert

---

### **❌ Problem: "Spende kam nicht an"**

**Log suchen:**
```bash
grep -E "WEBHOOK_.*pi_[a-zA-Z0-9]+" debug_flow.log | tail -10
```

**Typischer Log-Verlauf:**
```
💳 WEBHOOK_SUCCESS_START: {"payment_intent_id": "pi_1234567890", "amount": 10000}
💳 WEBHOOK_DONATION_LOOKUP: {"donation_id": 42}
💳 WEBHOOK_DONATION_FOUND: {"verse_count": 1, "current_status": "pending"}
💳 DONATION_MARKED_COMPLETE: {"new_status": "completed"}
📊 STRIPE-STRATEGIC [webhook] donation_completed_successfully: ✅
```

**Bedeutung:** Payment wurde erfolgreich verarbeitet

---

### **❌ Problem: "Daten wurden überschrieben"**

**Log suchen:**
```bash
grep "PERSON_DATA_UPDATED" debug_flow.log | tail -10
```

**Typischer Log:**
```
🔧 PERSON_DATA_UPDATED: {
  "person_id": 42,
  "changed_fields": ["street", "postal_code"],
  "changes": {
    "street": {"old": "Alte Straße 1", "new": "Neue Straße 5"},
    "postal_code": {"old": "12345", "new": "54321"}
  }
}
```

**Bedeutung:** Person mit ID 42 hat neue Adressdaten eingegeben → alte wurden überschrieben

---

## Live-Monitoring während der Entwicklung

### **Terminal 1: App starten**
```bash
python app.py
```

### **Terminal 2: Logs live verfolgen**
```bash
tail -f debug_flow.log | grep -E --color=always "ERROR|FAILED|❌|✅"
```

### **Terminal 3: Spezifische Probleme suchen**
```bash
# Cart-Probleme
tail -f debug_flow.log | grep -E --color=always "CART_.*INVALID|SESSION_.*CORRUPT"

# Person-Probleme  
tail -f debug_flow.log | grep -E --color=always "PERSON_.*UPDATED|PERSON_.*FAILED"

# Payment-Probleme
tail -f debug_flow.log | grep -E --color=always "WEBHOOK_.*ERROR|DONATION_.*FAILED"
```

---

## Debug-System später entfernen

### **Printf Debug entfernen** (nach Problemlösung):
```bash
# Alle Debug-Points finden und entfernen
grep -r "🔧 DEBUG POINT" . --include="*.py"
grep -r "debug_print\|model_debug_print\|stripe_debug_print" . --include="*.py"

# Debug-Infrastruktur entfernen (markiert mit 🔧)
grep -r "🔧.*REMOVE AFTER DEBUGGING" . --include="*.py"
```

### **Strategic Logging behalten** (längerfristig nützlich):
```bash
# Diese können bleiben - sind für Production nützlich:
grep -r "strategic_log\|STRATEGIC" . --include="*.py"
```

---

## Zusammenfassung: Dein neues Debugging-Workflow

1. **Problem auftritt** → Terminal oder debug_flow.log prüfen
2. **Trace-ID finden** → alle Schritte für einen Request verfolgen
3. **Specific Greps** → gezielt nach Fehlertypen suchen
4. **Pattern erkennen** → häufigste Probleme identifizieren
5. **Fix implementieren** → dann Debug-Points entfernen

**Du hast jetzt volle Transparenz über jeden Datenfluss in deiner App!** 🎉
