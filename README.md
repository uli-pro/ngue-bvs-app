# NGÜ Bible Verse Sponsoring App

**A Flask web application for sponsoring individual Old Testament verses of the NGÜ Bible translation project.**

This is my CS50 final project that enables donors to sponsor biblical verses for €100 each and receive personalized certificates as a meaningful acknowledgment of their contribution to the NGÜ (Neue Genfer Übersetzung) Bible translation project.

## Features

- **Individual Verse Sponsoring**: Sponsor any available Old Testament verse for €100
- **Intelligent Verse Search**: Find verses by keyword, reference, or thematic similarity
- **Automated Certificate Generation**: Personalized PDF certificates automatically generated and emailed
- **User Accounts**: Optional registration with donation history tracking
- **Guest Donations**: Contribute without creating an account
- **Semantic Search**: AI-powered verse recommendation using vector embeddings
- **Multi-language Support**: Prepared for future expansion to Switzerland

## Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Database**: PostgreSQL with pgvector extension
- **Payments**: Stripe integration
- **Frontend**: HTML5, CSS3, Bootstrap 5.3
- **AI/ML**: Sentence-BERT embeddings for semantic search
- **PDF Generation**: Automated certificate creation

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 14+ with pgvector extension
- Stripe account (for payments)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ngue-bvs-app.git
   cd ngue-bvs-app
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Stripe credentials
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

Visit `http://localhost:5000` to see the application.

## Project Structure

```
ngue-bvs-app/
├── app.py                  # Main Flask application
├── templates/              # HTML templates (17 pages)
├── static/                 # CSS, JavaScript, images
├── content/                # Page content and forms
├── data/                   # Bible text data (Schlachter 1951)
├── design/                 # Design system and assets
├── docs/                   # Project documentation
├── tests/                  # Test suite
└── requirements.txt        # Python dependencies
```

## Key Components

### Semantic Verse Search
- **Vector Embeddings**: Each verse converted to 768-dimensional vectors
- **Hybrid Search**: Combines keyword and semantic similarity
- **Positivity Ranking**: AI-curated positive verses prioritized in results

### Database Schema
- **BibelVerse**: ~11,000 Old Testament verses with sponsorship status
- **User**: Optional user accounts for sponsors
- **Purchase**: Donation transactions with Stripe integration
- **VerseVector**: AI-generated embeddings for semantic search

### Payment Flow
1. User selects verse (search, browse, or direct reference)
2. Checkout with personal details (required for donation receipt)
3. Stripe payment processing
4. Automated certificate and receipt generation
5. Email delivery of documents

## Development

### Running Tests
```bash
pytest
pytest --cov=app tests/  # With coverage
```

### Database Setup
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Contributing

This is a CS50 final project currently in active development. While I'm working on it individually for academic purposes, feedback and suggestions are welcome!

**Found a bug or have a suggestion?** Please [open an issue](../../issues) on GitHub.

## Roadmap

- **Phase 1**: Germany launch with Peter-Schöffer-Stiftung (Current)
- **Phase 2**: Switzerland expansion with Genfer Bibelgesellschaft (Planned)

## License

[To be determined]

## Acknowledgments

- **Harvard CS50** for excellent computer science education
- **Peter-Schöffer-Stiftung** for partnership and support
- **NGÜ Translation Team** for trusting this project

## Contact

Ulrich Probst - [your-email@example.com]

Project Link: [https://github.com/yourusername/ngue-bvs-app](https://github.com/yourusername/ngue-bvs-app)