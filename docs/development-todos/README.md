# Development TODOs

Dieses Verzeichnis enthält alle offenen Aufgaben und Anforderungen für die Code-Implementierung der NGÜ Bibelvers-Sponsoring App.

## Aktuell dokumentierte TODOs

### 🔥 Hohe Priorität (MVP-kritisch)
- [`pdf-generator-service-requirements.md`](./pdf-generator-service-requirements.md) - Umfassende Spezifikation für PDF-Zertifikat-Generierung
- [`checkout-form-prefilling.md`](./checkout-form-prefilling.md) - Automatische Formular-Vorausfüllung für eingeloggte User
- [`stripe-billing-integration.md`](./stripe-billing-integration.md) - Stripe-Payment mit automatischen Billing-Details

### 🔶 Mittlere Priorität
- [`account-creation-from-donation.md`](./account-creation-from-donation.md) - Account-Erstellung aus Guest-Spenden-Daten
- [`payment-retry-strategies.md`](./payment-retry-strategies.md) - Strategien für fehlgeschlagene Zahlungen

## Weitere geplante TODOs

### Backend-Services (noch zu dokumentieren)
- [ ] **Email-Service**: Automatischer Versand von Zertifikaten und Bestätigungen
- [ ] **Vers-Search-Service**: Semantische Suche mit pgvector und Positivity-Ranking
- [ ] **Admin-Dashboard**: Verwaltung von Spenden und Zahlungen
- [ ] **Database-Migrations**: SQLAlchemy/Alembic Setup
- [ ] **Environment-Configuration**: Development/Production Configs

### Frontend-Features (noch zu dokumentieren)
- [ ] **User-Dashboard**: Übersicht über gesponserte Verse
- [ ] **Vers-Browser**: Interaktive Vers-Auswahl mit Filter
- [ ] **Responsive Design**: Mobile-first Optimierung
- [ ] **JavaScript-Modules**: Modularisierung der Frontend-Logik

### Testing & Quality (noch zu dokumentieren)
- [ ] **Unit Tests**: Models, Services, Utilities
- [ ] **Integration Tests**: End-to-End Donation-Flow
- [ ] **Performance Tests**: Datenbank-Queries, PDF-Generierung
- [ ] **Security Review**: Input Validation, CSRF, etc.

### Deployment & Operations (noch zu dokumentieren)
- [ ] **Logging & Monitoring**: Error Tracking, Performance Metrics
- [ ] **Backup Strategy**: Database und PDF-Dateien
- [ ] **CI/CD Pipeline**: Automated Testing und Deployment
- [ ] **Production Hardening**: Security, Performance, Scalability

## Implementierungs-Reihenfolge

### Phase 1: MVP Core Features
1. **PDF-Generator-Service** - Kern-Feature für Zertifikate
2. **Checkout-Form-Prefilling** - UX-Optimierung für User
3. **Stripe-Billing-Integration** - Payment-Processing
4. **Email-Service** - Automatischer Versand

### Phase 2: User Experience
1. **Vers-Search-Service** - Erweiterte Vers-Suche
2. **User Dashboard** - Erweiterte User-Features  
3. **Account-Creation-from-Donation** - Conversion-Optimierung
4. **Admin Tools** - Verwaltungs-Interface

### Phase 3: Quality & Scale
1. **Comprehensive Testing** - Unit, Integration, E2E Tests
2. **Performance Optimierung** - Database, Frontend, Caching
3. **Production Deployment** - CI/CD, Monitoring, Backup
4. **Advanced Features** - Analytics, Multi-Language, etc.

## Status-Tracking

### ✅ Abgeschlossen
- Database-Models (User, Donation, PaymentTransaction, Certificate, DonationCartItem)
- Grundlegende Projektstruktur
- NGÜ-Design-System und Templates

### 🔄 In Bearbeitung
- Dokumentation aller MVP-Features als TODOs

### ⏳ Wartend
- Implementierung aller dokumentierten TODOs

## Verwendung

### Neues TODO erstellen
1. Neue `.md`-Datei mit beschreibendem Namen erstellen
2. Template aus unten verwenden
3. Detaillierte Spezifikation schreiben
4. In dieser README verlinken und kategorisieren

### Status-Updates
- TODOs als ✅ markieren wenn abgeschlossen
- Links zu implementierten Features hinzufügen
- Cross-References zwischen verwandten TODOs verwenden

## Template für neue TODOs

```markdown
# [Feature Name]

**Status:** TODO/In Progress/Completed  
**Priorität:** Hoch/Mittel/Niedrig  
**Datum:** [Erstellungsdatum]
**Abhängigkeiten:** [Andere TODOs/Features]

## Überblick
[Kurze Beschreibung was implementiert werden soll]

## Anforderungen
[Detaillierte funktionale Anforderungen]

## Technische Spezifikation
[Code-Struktur, APIs, Interfaces]

## Implementierungs-Details
[Konkrete Schritte zur Umsetzung]

## Testing
[Test-Anforderungen und -Strategien]

## Nächste Schritte
[Konkrete Aktionen zur Umsetzung]

---

**Priorität für MVP:** [Hoch/Mittel/Niedrig]
**Geschätzte Implementierungszeit:** [X Tage/Wochen]
```

## Notizen

- Alle TODOs sollten konkret und umsetzbar sein
- Code-Beispiele helfen bei der späteren Implementierung
- Testing-Anforderungen von Anfang an mitdenken
- Abhängigkeiten zwischen TODOs klar dokumentieren