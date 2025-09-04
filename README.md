# NGÜ Bible Verse Sponsorship App - CS50x Final Project

**Video URL:** https://youtu.be/Y-6t70ljBxE

**GitHub:** uli-pro  
**edX:** uli_probst  
**Location:** Pohlheim, Germany  
**Date:** September 2025  

## Description

This web application facilitates crowdfunding for the Neue Genfer Übersetzung (NGÜ) Bible translation project through individual verse sponsorships. The NGÜ is a modern German Bible translation where the New Testament has been completed, but approximately 11,000 Old Testament verses remain untranslated. The application allows donors to sponsor specific verses for €100 each, receiving a certificate and optional tax receipt in return.

### Problem Statement

The project addresses several technical and domain-specific challenges. The primary challenge involved creating a system to help users select meaningful verses from a large dataset of Old Testament texts, many of which contain difficult historical or theological content. Additionally, the application needed to handle German nonprofit requirements for donation processing and receipt generation while maintaining compliance with GDPR regulations.

The solution implements a multi-layered search system. Each of the 11,003 available verses was analyzed using Claude Haiku API to assign a positivity score between 0 and 100, based on themes such as hope, wisdom, and encouragement. This scoring enables the system to present more appealing verses to early donors while maintaining fairness as popular verses are sponsored. The search functionality combines PostgreSQL full-text search for German language content, direct biblical reference lookup, and semantic similarity search using OpenAI embeddings stored in pgvector.

### Technical Implementation

The application is built with Flask 3.0 and PostgreSQL, utilizing the pgvector extension for vector similarity operations. The database schema implements a many-to-many relationship between donations and verses through a junction table, allowing single donations to cover multiple verses. A reservation system using session storage and timestamp-based expiration prevents double-booking during concurrent checkouts.

Payment processing is handled through Stripe's API, supporting both SEPA Direct Debit (preferred for German users) and credit card payments. The implementation uses webhook endpoints to handle asynchronous payment confirmations, ensuring reliable transaction completion even if users navigate away during processing. Payment states are tracked through a simple state machine: pending, processing, completed, or failed.

The application generates two types of PDF documents: a decorative sponsor certificate and a legally compliant donation receipt for tax purposes. These are created using WeasyPrint libraries, then automatically sent via email using either Gmail SMTP or Mailgun API depending on configuration.

### User Interface Design

The interface was designed with accessibility in mind, particularly for older users who represent the primary donor demographic. The donation flow requires five clicks total: three for verse selection and navigation to the donation form, one for payment method entry, and one for final confirmation. The interface uses Bootstrap 5.3 for responsive design and maintains clear visual hierarchy through consistent button placement and sizing.

Form validation occurs both client-side and server-side, with clear error messages in German. The shopping cart persists in the session, allowing users to add multiple verses before checkout. CSRF protection is implemented on all forms, and rate limiting prevents abuse of payment endpoints.

### Production Considerations

The application includes features necessary for real-world deployment. An administrative interface, secured through magic link authentication, allows foundation staff to monitor donations and manage content. The system generates legally compliant German donation receipts following Zuwendungsbestätigung requirements, which required research into nonprofit tax law.

GDPR compliance is achieved through explicit consent checkboxes, minimal data collection, and complete avoidance of tracking cookies or analytics. All personal data collection serves specific legal or functional requirements. The privacy policy and terms of service were drafted in consultation with the foundation's requirements.

The application is containerized using Docker, with separate containers for the Flask application, PostgreSQL database, Nginx static file server, and Traefik reverse proxy. This architecture enables consistent deployment across development and production environments. The alpha-stage deployment at https://ngue.familieprobst.org uses Docker Compose for orchestration.

### Development Process

The project required approximately 180-200 hours of development time over two months. Roughly 25% of this time was spent on non-coding activities: understanding legal requirements, coordinating with stakeholders at the Peter Schöffer Foundation and Brunnen Publishing House, and researching German nonprofit regulations.

AI tools, particularly Claude, were used throughout development for code assistance, debugging, and content analysis. All AI-assisted code files are marked with appropriate comments as required by CS50's academic honesty policy. 

## File Structure

### Core Application
- `app.py` - Main Flask application containing routes and business logic (2000+ lines)
- `models.py` - SQLAlchemy database models for Person, Verse, Donation, and related entities
- `stripe_service.py` - Stripe payment integration and webhook handling
- `pdf_service.py` - PDF generation for certificates and receipts
- `email_service.py` - Email sending functionality with template support
- `certificate_manager.py` - Certificate generation and storage logic
- `book_names.py` - German/English Bible book name mappings

### Database and Setup
- `setup_db.py` - Database initialization script with index creation
- `vectorize.py` - Script for generating OpenAI embeddings for semantic search
- `verses.json` - Dataset containing 11,003 Old Testament verses with positivity scores

### Frontend
- `templates/` - 21 Jinja2 HTML templates
- `static/` - CSS, JavaScript, and image assets

### Deployment
- `app-deployment/` - Docker configuration files
- `requirements.txt` - Python package dependencies

## Design Decisions

**Framework Choice:** Flask was selected over Django due to its lighter weight and greater flexibility for this specific use case and also because I was familiar with Flask from CS50.

**Database Design:** PostgreSQL with pgvector extension was chosen to enable semantic search without external services. The many-to-many relationship between donations and verses allows flexibility in donation structures.

**Authentication:** The decision to avoid user accounts reduces friction for donors while maintaining necessary records through email-based person tracking. This simplifies the codebase and (hopefully) improves conversion rates.

**Payment Method:** SEPA Direct Debit is prioritized as it's preferred by German users and has lower transaction fees than credit cards.

**Deployment Architecture:** Docker containerization ensures reproducible deployments and simplifies server management. The multi-container approach with specialized services follows microservices principles while remaining manageable for a small application.

## Conclusion

This project demonstrates the application of CS50 concepts including database design, web frameworks, API integration, and deployment practices to solve a real-world problem. The combination of technical implementation and domain-specific requirements provided valuable experience in full-stack development and stakeholder communication.