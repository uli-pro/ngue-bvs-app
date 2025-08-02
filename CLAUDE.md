# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **NGÜ Bibelvers-Sponsoring App** - a Flask web application that enables individual verse sponsoring for the NGÜ (Neue Genfer Übersetzung) Bible translation project. This is a CS50 final project that allows donors to sponsor individual Old Testament verses for €100 each and receive personalized certificates.

## Technology Stack

- **Backend**: Python 3.8+ with Flask web framework
- **Database**: PostgreSQL with SQLAlchemy ORM and pgvector extension for semantic search
- **Frontend**: HTML5, CSS3, JavaScript with Jinja2 templating
- **Payments**: Stripe integration
- **Email**: Flask-Mail for automated certificate delivery
- **PDF Generation**: ReportLab or WeasyPrint for certificates
- **Authentication**: Flask-Login
- **Testing**: pytest

## Architecture Overview

### Bible Text Management
The application uses a single-translation approach:
- **Schlachter 1951**: Public domain German translation used for both display AND vectorization
- Based on POC results showing 72.7% accuracy with Schlachter vs. 18.2% with modern translations
- Simplifies architecture and reduces complexity

### Semantic Search Architecture
The app implements advanced verse search using:
- **Vector Embeddings**: Each verse is converted to a high-dimensional vector representation
- **Cosine Similarity**: Mathematical method to find semantically similar verses
- **pgvector Extension**: PostgreSQL extension for efficient vector operations and similarity searches
- **Hybrid Search**: Dynamic weighting between keyword and vector search based on query length
  - 1-2 words: 80% keyword, 20% vector
  - 3-5 words: 50% keyword, 50% vector
  - 6+ words: 20% keyword, 80% vector
- **Use Cases**:
  - Finding alternative verses when desired verse is already sponsored
  - Thematic search based on keywords or phrases
  - Discovering related verses across different books

### Positivity Ranking System (NEW)
Based on extensive testing, a critical insight emerged: Users search for positive, encouraging verses, but both keyword and semantic searches often return negative or difficult verses as top results.

**Solution**: Curated Top-1000 positive verses
- Pre-ranked list of 1000 verses by positivity factor using LLM
- Default: Show top 3 unsponsored positive verses
- Optional: User can search or enter specific reference
- Fallback: Return to top 3 if search unsuccessful

**Technical Implementation**:
- LLM-based positivity scoring for all 11,000 verses
- Stored positivity index in database
- Combined with search scores for final ranking

### Core Data Model
The application revolves around three main entities:
- **BibelVerse**: ~11,000 Old Testament verses with sponsorship status
- **User**: Optional user accounts for sponsors (guest donations allowed)
- **Purchase**: Donation transactions linked to verses via Stripe

### Key Features
- Uniform €100 pricing model (no premium tiers based on user feedback)
- Advanced verse search (full-text, thematic, book browsing)
- Intelligent alternatives when desired verses are already sponsored
- **Automated dual PDF generation: personalized certificate + official donation receipt**
- Automated certificate generation and email delivery
- Guest checkout without registration requirement
- Animated verse sponsoring visualization

### Required Data for Donation Receipt
The app collects the following information for automatic donation receipt generation:
- Salutation (Herr, Frau, Eheleute, Firma)
- First name and last name
- Street and house number
- Postal code and city
- Email address
- Donation amount (€100)
- Donation date
- Donation project: NGÜ
- Data processing consent

## Development Commands

Since the codebase is in early development phase, these commands will be established as the project progresses:

```bash
# Virtual environment setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (when requirements.txt is created)
pip install -r requirements.txt

# Database operations (when Flask-Migrate is set up)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Development server
flask run

# Testing (when tests are implemented)
pytest
pytest --cov=app tests/
```

## Project Structure

```
ngue-bvs-app/
├── app/                    # Main Flask application
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models
│   ├── routes.py          # Flask routes
│   ├── forms.py           # WTForms
│   └── utils.py           # Helper functions
├── static/                # CSS, JS, images
├── templates/             # Jinja2 HTML templates
├── tests/                 # Test suite
├── docs/                  # Project documentation
├── dev-diary/             # Development diary and sessions
└── migrations/            # Database migrations (to be created)
```

## Key Development Phases

The project follows a 7-week development plan documented in `docs/development-plan.md`:

1. **Week 0-1**: Concept and design (user feedback incorporated - single pricing model)
2. **Week 2**: Backend structure and user authentication
3. **Week 3**: Frontend development and verse search implementation
   - Hybrid search with dynamic weighting
   - Positivity ranking integration
4. **Week 4**: Stripe payment integration
5. **Week 5**: Email automation and certificate generation
6. **Week 6**: Testing and optimization
7. **Week 7**: Deployment and launch

### Recent Testing Insights (August 2, 2025)
- Extensive testing with 100, 1,000, and 11,000 verse datasets
- Hybrid search implemented combining keyword and vector search
- Critical discovery: Need for positivity ranking to match user expectations
- Decision: Implement LLM-based positivity scoring for all verses

## Development Context

### Important Design Decisions
- **Single pricing model**: All verses cost €100 (no premium tiers)
- **Guest-friendly**: Registration optional, guest donations supported
- **Search-centric**: Advanced search capabilities for 11,000+ verses
- **Automation focus**: Minimal manual intervention after donation

### Technical Considerations
- **Scalability**: SQLAlchemy chosen for easy database migration from SQLite to PostgreSQL
- **Security**: HTTPS mandatory, no credit card storage (handled by Stripe)
- **GDPR Compliance**: Careful handling of donor personal data
- **Performance**: Database optimization needed for 11,000 verse records

## Environment Configuration

When `.env` file is created, it should include:
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/ngue_bvs_db
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
```

## Development Workflow

The project uses a structured development diary system in `dev-diary/` with:
- Session templates for consistent documentation
- Weekly milestone tracking
- Detailed progress logging per session

When developing new features:
1. Follow the planned session structure in development-plan.md
2. Document progress in the appropriate week file
3. Test incrementally rather than waiting for full completion
4. Commit frequently with descriptive messages

## Integration Notes

This application is designed to integrate with the existing NGÜ WordPress website, with options for:
- iFrame integration
- Subdomain deployment
- WordPress plugin conversion (future consideration)

## CS50 Context

This serves as the final project for Harvard's CS50 course, balancing educational objectives with real-world application for the Peter-Schöffer-Stiftung's Bible translation funding initiative.