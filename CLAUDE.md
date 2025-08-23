# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **NGÜ Bibelvers-Sponsoring App** - a simplified Flask web application that enables individual verse sponsoring for the NGÜ (Neue Genfer Übersetzung) Bible translation project. Donors can sponsor individual Old Testament verses for €100 each through a streamlined checkout process with Stripe payments.

### Current Status (August 2025)
- **Functional Application**: Working verse sponsoring platform ready for production
- **Simplified Architecture**: No user accounts - person-based donations only
- **Complete UI/UX**: 21 responsive templates with NGÜ branding
- **Payment Integration**: Stripe with SEPA Direct Debit preference
- **Advanced Search**: Hybrid keyword + semantic search with AI positivity scoring

## Architecture Overview

### **Simplified Design Philosophy**
The app has been significantly streamlined, removing complex features like user accounts, bible translation progress tracking, and complex session management. The focus is on core functionality: **verse selection → donation data → payment → certificate delivery**.

### **Core Data Model**
- **Person**: Central donor management (replaces User model)
- **Verse**: ~11,000 Old Testament verses with sponsorship status
- **Donation**: Simplified donations with JSONB details
- **VerseReservation**: Temporary verse reservations during checkout
- **PaymentTransaction**: Stripe payment tracking

### **No User Accounts**
The app operates without traditional user registration/login:
- Donors provide email and personal data per donation
- `Person` records created/updated automatically based on email
- No passwords, sessions, or user dashboards
- Guest checkout is the primary flow

## Technology Stack

- **Backend**: Flask 3.0 with SQLAlchemy
- **Database**: PostgreSQL with pgvector extension for semantic search
- **Payments**: Stripe 12.4 (SEPA Direct Debit preference)
- **Search**: Hybrid keyword + vector similarity search
- **Security**: Flask-WTF CSRF, Flask-Limiter rate limiting
- **PDF**: WeasyPrint + ReportLab for certificate generation
- **Frontend**: Bootstrap 5.3, vanilla JavaScript

## Key Features

### **Verse Selection**
- **Featured Verses**: AI-curated positive verses on homepage (adaptive algorithm)
- **Keyword Search**: Full-text PostgreSQL search with German language support
- **Reference Search**: Direct biblical reference lookup (e.g., "Jesaja 43,1")
- **Semantic Search**: Vector similarity using OpenAI embeddings
- **Hybrid Search**: Dynamic weighting based on query complexity

### **Smart Donation Flow**
- **Shopping Cart**: Multiple verses can be added before checkout
- **Reservation System**: Temporary verse reservations prevent conflicts
- **Unified Checkout**: Single form for all donation types
- **Person Management**: Automatic person creation/updates based on email

### **Payment & Certificates**
- **Stripe Integration**: SEPA-first payment with card fallback
- **Automatic Certificates**: PDF generation on successful payment
- **Email Delivery**: Automated certificate and receipt sending
- **Multiple Donation Types**: Individual, group, and gift donations

## Project Structure

```
ngue-bvs-app/
├── app.py                    # Main Flask application (1750+ lines)
├── models.py                 # Database models (Person, Verse, Donation, etc.)
├── stripe_service.py         # Stripe payment integration
├── requirements.txt          # Python dependencies
├── templates/                # 21 HTML templates
│   ├── layout.html          # Base template with NGÜ branding
│   ├── index.html           # Homepage with featured verses
│   ├── vers-auswaehlen*.html # Verse selection pages
│   ├── checkout-*.html      # Payment flow templates
│   └── ...                  # Additional templates
├── static/                   # CSS, JavaScript, images
│   ├── styles.css           # Main stylesheet
│   ├── js/                  # JavaScript modules
│   └── logo-*.png           # NGÜ logos
├── data/
│   └── verses/
│       └── verses.json      # ~11,000 verses with positivity scores
├── docs/                    # Development documentation
├── tests/                   # Comprehensive test suite
├── demo/                    # Demo version (separate implementation)
└── archive/                 # Historical files (ignore for development)
```

## Development Guidelines

### **Working with the Codebase**
- **Ignore `/archive`**: Contains outdated files from previous iterations
- **Focus on root level**: Main application files are in project root
- **Demo vs Production**: `/demo` is separate; main app is in root directory

### **Database Operations**
- **Models**: Use SQLAlchemy models in `models.py`
- **Person Management**: `Person.find_or_create()` for automatic person handling
- **Verse Search**: Use `Verse.search_hybrid()` for best search results
- **Reservations**: `VerseReservation.create_or_update()` prevents conflicts

### **Payment Flow**
- **Cart Management**: Session-based shopping cart with validation
- **Stripe Service**: Use `stripe_service.py` for all payment operations
- **Webhook Handling**: Automated donation completion via Stripe webhooks

### **Key Route Patterns**
- `/vers-auswaehlen*` - Verse selection and search
- `/checkout/*` - Payment flow (spendendaten → zahlung → erfolg)
- `/spendenkorb` - Shopping cart management
- `/api/*` - AJAX endpoints for search and cart operations

## Current Features Status

### **✅ Complete & Working**
- Verse selection with multiple search methods
- Shopping cart with reservation system
- Simplified checkout flow (no accounts required)
- Stripe payment integration with SEPA preference
- PDF certificate generation (dummy templates ready)
- Email automation framework
- Comprehensive error handling and validation

### **🔄 In Development**
- Real PDF certificate generation (templates exist)
- Email service integration (Flask-Mail configured)
- Admin cleanup endpoints
- Performance optimizations

### **⏳ Planned**
- Production deployment configuration
- Admin dashboard for monitoring
- Switzerland expansion preparation
- Advanced analytics and reporting

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
python setup_db_v2.py  # Initialize database with verses

# Run application
python app.py  # Development server on port 5000

# Testing
pytest  # Run test suite
pytest --cov  # With coverage
```

## Environment Configuration

Required environment variables:
```bash
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/ngue_db
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Integration Notes

### **Stripe Webhooks**
- **Endpoint**: `/stripe/webhook`
- **Events**: `payment_intent.succeeded`, `payment_intent.payment_failed`
- **Function**: Automatic donation completion and verse marking

### **Search Implementation**
- **Keyword**: PostgreSQL full-text search with German language support
- **Semantic**: pgvector cosine similarity using OpenAI embeddings
- **Hybrid**: Dynamic weighting (1-2 words: 80% keyword, 6+ words: 80% semantic)
- **Positivity**: AI-scored verses (0-100) prioritized in results

### **Session Management**
- **Flask-Session**: Database-backed sessions (not file-based)
- **Shopping Cart**: Session-based with corruption handling
- **Reservations**: Session-tied verse reservations with expiration

## CS50 Context

This Flask application serves as a CS50 final project, demonstrating:
- **Web Development**: Flask, SQLAlchemy, responsive design
- **Database Design**: PostgreSQL with advanced features (pgvector)
- **Payment Integration**: Stripe API with webhook handling
- **AI/ML**: Semantic search using vector embeddings
- **Real-world Application**: Solving actual funding needs for Bible translation

The app balances academic learning objectives with practical functionality for the Peter-Schöffer-Stiftung's NGÜ Bible translation funding initiative.

## Security Considerations

- **CSRF Protection**: Flask-WTF on all forms
- **Rate Limiting**: Flask-Limiter on API endpoints and payment routes
- **Input Validation**: Comprehensive form validation and sanitization
- **Session Security**: HTTPOnly, Secure (in production), SameSite cookies
- **Payment Security**: No credit card data stored (handled by Stripe)
- **Data Privacy**: GDPR-compliant data collection with explicit consent

## Performance Features

- **Database Indexes**: Optimized for verse search operations
- **Caching Strategy**: Session-based verse selection caching
- **Efficient Search**: Combined tsvector and vector similarity search
- **Background Tasks**: Webhook-based async donation processing