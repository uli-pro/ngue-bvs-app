"""
Helper functions and factories for verse reservation system tests.
"""

from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from models import db, Verse, VerseReservation, User


class VerseFactory:
    """Factory for creating test verses."""
    
    @staticmethod
    def create(book='TEST', chapter=1, verse=1, text='Test verse text', 
               positivity_score=70, is_sponsored=False, **kwargs):
        """Create a verse with given parameters."""
        verse_obj = Verse(
            book=book,
            chapter=chapter,
            verse=verse,
            text=text,
            positivity_score=positivity_score,
            is_sponsored=is_sponsored,
            **kwargs
        )
        db.session.add(verse_obj)
        db.session.commit()
        return verse_obj
    
    @staticmethod
    def create_batch(count=5, base_score=70, **kwargs):
        """Create multiple verses with incrementing scores."""
        verses = []
        for i in range(count):
            verse = VerseFactory.create(
                book='TEST',
                chapter=1,
                verse=i + 1,
                text=f'Test verse {i + 1} text',
                positivity_score=base_score + i,
                **kwargs
            )
            verses.append(verse)
        return verses
    
    @staticmethod
    def create_with_keywords(keywords, base_score=70, **kwargs):
        """Create verse with specific keywords for testing bonus calculation."""
        text = f"This verse contains {' and '.join(keywords)} for testing."
        return VerseFactory.create(
            text=text,
            positivity_score=base_score,
            **kwargs
        )


class ReservationFactory:
    """Factory for creating test reservations."""
    
    @staticmethod
    def create(verse_id, session_id='test-session', minutes_from_now=15, **kwargs):
        """Create a reservation with given parameters."""
        reservation = VerseReservation(
            verse_id=verse_id,
            session_id=session_id,
            expires_at=datetime.utcnow() + timedelta(minutes=minutes_from_now),
            **kwargs
        )
        db.session.add(reservation)
        db.session.commit()
        return reservation
    
    @staticmethod
    def create_expired(verse_id, session_id='test-session', minutes_ago=5, **kwargs):
        """Create an expired reservation."""
        return ReservationFactory.create(
            verse_id=verse_id,
            session_id=session_id,
            minutes_from_now=-minutes_ago,
            **kwargs
        )


class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def create(email='test@example.com', password='testpass123', 
               first_name='Test', last_name='User', **kwargs):
        """Create a test user."""
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_verified=True,
            **kwargs
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user


class ResponseParser:
    """Helper for parsing HTML responses."""
    
    @staticmethod
    def get_verses_from_response(response):
        """Extract verse data from /vers-auswaehlen response."""
        soup = BeautifulSoup(response.data, 'html.parser')
        verses = []
        
        # Find all verse cards
        verse_cards = soup.find_all('div', class_='verse-card')
        
        for card in verse_cards:
            # Extract reference
            reference_elem = card.find('h4', class_='text-primary')
            reference = reference_elem.text.strip() if reference_elem else None
            
            # Extract text
            text_elem = card.find('blockquote').find('p')
            text = text_elem.text.strip().strip('"') if text_elem else None
            
            # Extract URL
            link_elem = card.find('a', class_='btn-primary')
            url = link_elem.get('href') if link_elem else None
            
            if reference and text and url:
                verses.append({
                    'reference': reference,
                    'text': text,
                    'url': url
                })
        
        return verses
    
    @staticmethod
    def extract_verse_id_from_url(url):
        """Extract verse ID from URL like /vers/jesaja-43-1/spendenart."""
        match = re.search(r'/vers/([^/]+)/spendenart', url)
        return match.group(1) if match else None
    
    @staticmethod
    def get_flash_messages(response):
        """Extract flash messages from response."""
        soup = BeautifulSoup(response.data, 'html.parser')
        messages = []
        
        # Find all divs with any alert class
        alert_divs = soup.find_all('div', class_=lambda x: x and any('alert' in cls for cls in x))
        for alert in alert_divs:
            text = alert.get_text().strip()
            if text and 'alert' in ' '.join(alert.get('class', [])):
                # Determine message type from CSS classes
                classes = alert.get('class', [])
                if 'alert-success' in classes:
                    msg_type = 'success'
                elif 'alert-warning' in classes:
                    msg_type = 'warning'
                elif 'alert-danger' in classes or 'alert-error' in classes:
                    msg_type = 'error'
                elif 'alert-info' in classes:
                    msg_type = 'info'
                else:
                    # Default fallback for any other alert types
                    msg_type = 'info'
                
                messages.append({
                    'type': msg_type,
                    'text': text
                })
        
        return messages


class DatabaseHelper:
    """Helper for database operations in tests."""
    
    @staticmethod
    def get_verse_by_slug(slug):
        """Get verse by URL slug like 'isa-43-1'."""
        parts = slug.split('-')
        if len(parts) != 3:
            return None
        
        try:
            book = parts[0].upper()
            chapter = int(parts[1])
            verse_num = int(parts[2])
            return Verse.query.filter_by(book=book, chapter=chapter, verse=verse_num).first()
        except ValueError:
            return None
    
    @staticmethod
    def count_active_reservations():
        """Count all active (non-expired) reservations."""
        return VerseReservation.query.filter(
            VerseReservation.expires_at > datetime.utcnow()
        ).count()
    
    @staticmethod
    def count_expired_reservations():
        """Count all expired reservations."""
        return VerseReservation.query.filter(
            VerseReservation.expires_at <= datetime.utcnow()
        ).count()
    
    @staticmethod
    def clear_all_reservations():
        """Remove all reservations from database."""
        VerseReservation.query.delete()
        db.session.commit()


class AssertionHelper:
    """Custom assertion helpers for tests."""
    
    @staticmethod
    def assert_verse_reserved(verse_id, session_id):
        """Assert that a verse is reserved by specific session."""
        reservation = VerseReservation.query.filter_by(
            verse_id=verse_id,
            session_id=session_id
        ).first()
        
        assert reservation is not None, f"No reservation found for verse {verse_id} by session {session_id}"
        assert not reservation.is_expired, f"Reservation for verse {verse_id} is expired"
        return reservation
    
    @staticmethod
    def assert_verse_not_reserved(verse_id, session_id=None):
        """Assert that a verse is not reserved (by specific session if given)."""
        query = VerseReservation.query.filter_by(verse_id=verse_id)
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        # Check for active reservations only
        reservation = query.filter(
            VerseReservation.expires_at > datetime.utcnow()
        ).first()
        
        assert reservation is None, f"Unexpected reservation found for verse {verse_id}"
    
    @staticmethod
    def assert_verses_different(verses1, verses2):
        """Assert that two lists of verses are different."""
        refs1 = [v['reference'] for v in verses1]
        refs2 = [v['reference'] for v in verses2]
        
        assert refs1 != refs2, f"Verse lists are identical: {refs1}"
    
    @staticmethod
    def assert_verses_same(verses1, verses2):
        """Assert that two lists of verses are the same."""
        refs1 = [v['reference'] for v in verses1]
        refs2 = [v['reference'] for v in verses2]
        
        assert refs1 == refs2, f"Verse lists differ: {refs1} vs {refs2}"
    
    @staticmethod
    def assert_flash_message(response, message_type, text_contains):
        """Assert that response contains a flash message with specific type and text."""
        messages = ResponseParser.get_flash_messages(response)
        
        matching_messages = [
            msg for msg in messages 
            if msg['type'] == message_type and text_contains.lower() in msg['text'].lower()
        ]
        
        assert len(matching_messages) > 0, (
            f"No {message_type} flash message containing '{text_contains}' found. "
            f"Available messages: {messages}"
        )


def advance_time_minutes(minutes):
    """Helper for time manipulation in tests (to be used with freezegun)."""
    from freezegun import freeze_time
    from datetime import datetime, timedelta
    
    new_time = datetime.utcnow() + timedelta(minutes=minutes)
    return freeze_time(new_time)


def create_test_session_data(verse_ids=None, selected_verse_id=None, reservation_id=None):
    """Create test session data dictionary."""
    session_data = {}
    
    if verse_ids:
        session_data['featured_verse_ids'] = verse_ids
        session_data['shown_verse_ids'] = verse_ids.copy()
    
    if selected_verse_id:
        session_data['selected_verse_id'] = selected_verse_id
    
    if reservation_id:
        session_data['reservation_id'] = reservation_id
    
    return session_data