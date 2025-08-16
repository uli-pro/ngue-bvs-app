"""
Test configuration and shared fixtures for verse reservation system tests.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from flask import session

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app import app as flask_app
from models import db, Verse, User, VerseReservation


@pytest.fixture(scope='function')
def app():
    """Create test Flask application with PostgreSQL test database."""
    
    # Configure test app to use PostgreSQL test database
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://localhost/ngue_bvs_test',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for tests
        'SESSION_TYPE': 'filesystem',
        'SESSION_PERMANENT': False,
    })
    
    with flask_app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        yield flask_app
        
        # Cleanup - NOTE: Removed dangerous table.delete() to prevent data loss
        # Tests should use a separate test database to avoid affecting production data
        pass


@pytest.fixture
def client(app):
    """Create test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def authenticated_user(app, client):
    """Create and login a test user."""
    with app.app_context():
        # Create test user
        user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            is_verified=True
        )
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
        
        # Login user
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        return user


@pytest.fixture
def sample_verses(app):
    """Create sample verses with different positivity scores."""
    with app.app_context():
        verses = [
            # High positivity verses (90+)
            Verse(
                book='ISA', chapter=43, verse=1,
                text='Fürchte dich nicht, denn ich habe dich erlöst. Ich habe dich bei deinem Namen gerufen; du bist mein!',
                positivity_score=95
            ),
            Verse(
                book='JER', chapter=29, verse=11,
                text='Denn ich weiß, was für Gedanken ich über euch habe, spricht der HERR, Gedanken des Friedens und nicht des Leides.',
                positivity_score=92
            ),
            Verse(
                book='ZEP', chapter=3, verse=17,
                text='Der HERR, dein Gott, ist in deiner Mitte, ein Held, der helfen kann; er wird sich über dich freuen.',
                positivity_score=90
            ),
            
            # Medium positivity verses (70-89)
            Verse(
                book='PSA', chapter=23, verse=1,
                text='Der HERR ist mein Hirte; mir wird nichts mangeln.',
                positivity_score=85
            ),
            Verse(
                book='PRO', chapter=3, verse=5,
                text='Vertraue auf den HERRN von ganzem Herzen und verlaß dich nicht auf deinen Verstand.',
                positivity_score=80
            ),
            
            # Lower positivity verses (50-69)
            Verse(
                book='ECC', chapter=3, verse=1,
                text='Ein jegliches hat seine Zeit, und alles Vorhaben unter dem Himmel hat seine Stunde.',
                positivity_score=60
            ),
            
            # Verses with positive keywords for bonus testing
            Verse(
                book='1JOH', chapter=4, verse=8,
                text='Wer nicht liebt, kennt Gott nicht; denn Gott ist Liebe.',
                positivity_score=70  # Should get keyword bonus for "Liebe"
            ),
            Verse(
                book='ROM', chapter=15, verse=13,
                text='Der Gott der Hoffnung aber erfülle euch mit aller Freude und allem Frieden im Glauben.',
                positivity_score=75  # Should get bonus for "Hoffnung", "Freude", "Frieden"
            ),
            
            # Already sponsored verses
            Verse(
                book='GEN', chapter=1, verse=1,
                text='Im Anfang schuf Gott Himmel und Erde.',
                positivity_score=85,
                is_sponsored=True
            ),
            Verse(
                book='REV', chapter=21, verse=4,
                text='Und Gott wird abwischen alle Tränen von ihren Augen.',
                positivity_score=88,
                is_sponsored=True
            ),
        ]
        
        for verse in verses:
            db.session.add(verse)
        
        db.session.commit()
        
        # Refresh all objects to ensure they stay bound to the session
        for verse in verses:
            db.session.refresh(verse)
        
        return verses


@pytest.fixture
def mock_session_id():
    """Generate mock session ID for testing."""
    return 'test-session-12345'


@pytest.fixture
def verse_with_reservation(app, sample_verses, mock_session_id):
    """Create a verse with an active reservation."""
    with app.app_context():
        verse = sample_verses[0]  # Use first verse
        reservation = VerseReservation(
            verse_id=verse.id,
            session_id=mock_session_id,
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.session.add(reservation)
        db.session.commit()
        return verse, reservation


@pytest.fixture
def expired_reservation(app, sample_verses, mock_session_id):
    """Create a verse with an expired reservation."""
    with app.app_context():
        verse = sample_verses[1]  # Use second verse
        reservation = VerseReservation(
            verse_id=verse.id,
            session_id=mock_session_id,
            expires_at=datetime.utcnow() - timedelta(minutes=5)  # Expired 5 min ago
        )
        db.session.add(reservation)
        db.session.commit()
        return verse, reservation


@pytest.fixture
def client_with_session(client):
    """Test client with session setup."""
    with client.session_transaction() as sess:
        sess['test_mode'] = True
        sess.permanent = True
    return client


class SessionManager:
    """Helper class for managing test sessions."""
    
    def __init__(self, client):
        self.client = client
    
    def set_featured_verses(self, verse_ids):
        """Set featured verse IDs in session."""
        with self.client.session_transaction() as sess:
            sess['featured_verse_ids'] = verse_ids
    
    def set_shown_verses(self, verse_ids):
        """Set shown verse IDs in session."""
        with self.client.session_transaction() as sess:
            sess['shown_verse_ids'] = verse_ids
    
    def set_selected_verse(self, verse_id, reservation_id=None):
        """Set selected verse in session."""
        with self.client.session_transaction() as sess:
            sess['selected_verse_id'] = verse_id
            if reservation_id:
                sess['reservation_id'] = reservation_id
    
    def get_session_data(self):
        """Get current session data."""
        with self.client.session_transaction() as sess:
            return dict(sess)
    
    def clear_session(self):
        """Clear all session data."""
        with self.client.session_transaction() as sess:
            sess.clear()


@pytest.fixture
def session_manager(client):
    """Session management helper for tests."""
    return SessionManager(client)


@pytest.fixture(autouse=True)
def setup_app_context(app):
    """Ensure app context is available for all tests."""
    with app.app_context():
        yield