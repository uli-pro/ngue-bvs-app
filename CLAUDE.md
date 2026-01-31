# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NGÜ Bibelvers-Sponsoring App - Flask web application enabling individual verse sponsoring for the NGÜ (Neue Genfer Übersetzung) Bible translation. Donors sponsor Old Testament verses for €100 each via Stripe payments (SEPA-first).

**Core Flow**: Verse selection → Shopping cart → Donor data → Payment → Certificate delivery

## Environments

| Environment | URL | Notes |
|-------------|-----|-------|
| **Claude Testing** | http://localhost:5000 | When Claude runs the app |
| **Manual Development** | http://localhost:5001 | When user runs manually |
| **Production** | https://ngue-bvs.schoeffer.org | Server: 213.165.95.155 |

## Development Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database setup (requires PostgreSQL with pgvector)
python3 setup_db.py

# Run development server
python3 app.py  # Port 5000 (Claude) or 5001 (manual)

# Testing (from project root)
pytest do-not-deploy/tests/                     # Run all tests
pytest do-not-deploy/tests/test_checkout_flow.py  # Single test file
pytest do-not-deploy/tests/ -k "test_name"      # Run specific test
pytest do-not-deploy/tests/ --cov              # With coverage

# Stripe CLI for webhook testing
stripe listen --forward-to localhost:5000/stripe/webhook

# Daily report (production)
python3 send_daily_report.py
```

## Architecture

### Core Files (root directory)
- `app.py` - Main Flask application (~2000 lines): routes, cart logic, session handling
- `models.py` - SQLAlchemy models: Person, Verse, Donation, VerseReservation, Certificate
- `stripe_service.py` - Stripe integration, SEPA/card payment handling, webhook processing
- `pdf_service.py` - PDF generation for certificates and tax receipts (WeasyPrint + ReportLab)
- `email_service.py` - Email automation (IONOS SMTP)
- `hubspot_service.py` - CRM integration
- `book_names.py` - German/English Bible book mappings

### Admin Module (`admin/`)
- Blueprint with magic-link authentication (no passwords)
- Routes: `/admin/` for person/verse/donation management
- Protected by `@admin_required` decorator

### Data Flow
1. **Verse Selection**: `Verse.search_hybrid()` combines keyword + semantic search
2. **Cart**: Session-based, validates against `VerseReservation` to prevent conflicts
3. **Checkout**: Creates `Person` via `Person.find_or_create()`, then `Donation`
4. **Payment**: Stripe webhook at `/stripe/webhook` triggers certificate generation
5. **Certificates**: `pdf_service.py` generates PDFs, stored in `certificates/`

## Key Patterns

### Database Operations
```python
# Person management - auto-creates or updates based on email
person = Person.find_or_create(email, **donor_data)

# Verse search - hybrid keyword + semantic
verses = Verse.search_hybrid(query, limit=20)

# Reservations - prevent double-booking
VerseReservation.create_or_update(verse_id, session_id, duration_minutes=30)
```

### Route Groups
- `/vers-auswaehlen*` - Verse selection and search
- `/checkout/*` - Checkout flow (spendendaten → zahlung → erfolg)
- `/spendenkorb` - Shopping cart management
- `/api/*` - AJAX endpoints for search/cart
- `/stripe/webhook` - Stripe payment webhooks

## Critical: Docker Build

**`.dockerignore` uses a whitelist for Python files!**

When adding a new `.py` file, you MUST add it to the whitelist in `.dockerignore` (lines ~128-140):
```
!neue_datei.py
```
Without this entry, new Python files will NOT be copied into the Docker image.

## Environment Variables

Required in `.env`:
```
SECRET_KEY=...
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/ngue_db
STRIPE_PUBLIC_KEY=pk_...
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
ADMIN_EMAIL=...
```

## Testing Notes

- Tests are in `do-not-deploy/tests/` (excluded from Docker)
- Tests use mocks to avoid database operations (see `conftest.py`)
- Never run tests against production database (safety check in conftest.py)
- Vector search tests require `do-not-deploy/tests/vector-poc/`

## Directory Structure Notes

- **Ignore `/do-not-deploy/`**: Contains tests, archives, and development files
- **Focus on root level**: Main application files are in project root
- `/demo/` is a separate demo implementation
- `/archive/` contains outdated files from previous iterations

## Stripe Webhook Events

- `payment_intent.succeeded` - Complete donation, mark verse sponsored, generate certificate
- `payment_intent.payment_failed` - Mark donation failed, release verse reservation
- `charge.dispute.created` - Handle chargebacks (SEPA recalls)

## Search Implementation

- **Keyword**: PostgreSQL full-text search with German language support
- **Semantic**: pgvector cosine similarity using OpenAI embeddings
- **Hybrid weighting**: 1-2 words → 80% keyword, 6+ words → 80% semantic
- **Positivity scoring**: AI-scored verses (0-100) prioritized in results (stored in `verses.json`)
