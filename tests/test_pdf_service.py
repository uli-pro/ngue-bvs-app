"""
Tests for PDF Generator Service
Testing PDF generation functionality with mock data
"""

import pytest
import os
import tempfile
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from pdf_service import PDFGeneratorService, PDFGenerationError, ValidationError
from models import db, Person, Donation, Verse, Certificate


class TestPDFGeneratorService:
    """Test suite for PDFGeneratorService"""
    
    @pytest.fixture
    def pdf_service(self, app):
        """Create PDF service instance"""
        with app.app_context():
            service = PDFGeneratorService(app)
            return service
    
    @pytest.fixture
    def test_person(self, app):
        """Create test person"""
        with app.app_context():
            person = Person(
                email="test@example.com",
                first_name="Max",
                last_name="Mustermann",
                street="Teststraße",
                house_number="123",
                postal_code="12345",
                city="Berlin"
            )
            db.session.add(person)
            db.session.commit()
            return person
    
    @pytest.fixture
    def test_verse(self, app):
        """Create test verse"""
        with app.app_context():
            verse = Verse(
                book="1. Mose",
                chapter=1,
                verse=1,
                reference="1. Mose 1,1",
                text="Am Anfang schuf Gott Himmel und Erde."
            )
            db.session.add(verse)
            db.session.commit()
            return verse
    
    @pytest.fixture
    def test_donation(self, app, test_person, test_verse):
        """Create test donation"""
        with app.app_context():
            donation = Donation(
                person_id=test_person.id,
                verse_id=test_verse.id,
                donation_type='person',
                amount=Decimal('100.00'),
                payment_status='completed',
                completed_at=datetime.now(),
                person_snapshot=test_person.to_snapshot(),
                privacy_consent=True
            )
            db.session.add(donation)
            db.session.commit()
            return donation
    
    def test_service_initialization(self, app):
        """Test service can be initialized with Flask app"""
        with app.app_context():
            service = PDFGeneratorService(app)
            assert service.app == app
            assert app.config.get('CERTIFICATE_STORAGE_PATH') is not None
    
    def test_amount_to_words(self, pdf_service, app):
        """Test German number conversion"""
        with app.app_context():
            # Test standard amount (100 Euro)
            result = pdf_service._amount_to_words(Decimal('100'))
            assert result == "Einhundert"
            
            # Test other amounts
            assert pdf_service._amount_to_words(Decimal('200')) == "Zweihundert"
            assert pdf_service._amount_to_words(Decimal('150')) == "Einhundertfünfzig"
    
    def test_generate_certificate_paths(self, pdf_service, app, test_donation):
        """Test certificate path generation"""
        with app.app_context():
            filename, file_path = pdf_service._generate_certificate_paths(
                test_donation, 'personal_certificate', 'test_session_123'
            )
            
            # Check filename format
            assert filename.startswith('donation_001_personal_certificate_')
            assert filename.endswith('.pdf')
            
            # Check path structure
            assert 'session_test_session_123' in file_path
            assert file_path.endswith(filename)
    
    def test_prepare_certificate_context(self, pdf_service, app, test_donation):
        """Test certificate context preparation"""
        with app.app_context():
            context = pdf_service._prepare_certificate_context(
                test_donation, 'personal_certificate'
            )
            
            # Check required context keys
            assert 'donation' in context
            assert 'person_snapshot' in context
            assert 'verse' in context
            assert 'verses' in context
            assert 'background_image_path' in context
            
            # Check data integrity
            assert context['donation'].id == test_donation.id
            assert context['person_snapshot']['first_name'] == 'Max'
            assert len(context['verses']) == 1
    
    def test_prepare_tax_receipt_context(self, pdf_service, app, test_donation):
        """Test tax receipt context preparation"""
        with app.app_context():
            context = pdf_service._prepare_tax_receipt_context(test_donation)
            
            # Check required context keys
            assert 'donation' in context
            assert 'person_snapshot' in context
            assert 'amount_in_words' in context
            assert 'foundation' in context
            
            # Check foundation data
            foundation = context['foundation']
            assert foundation['name'] == 'Peter-Schöffer-Stiftung'
            assert foundation['tax_number'] == '07/456/78901'
    
    def test_validation_errors(self, pdf_service, app):
        """Test validation error handling"""
        with app.app_context():
            # Test invalid donation ID
            with pytest.raises(ValidationError):
                pdf_service.generate_certificate(999999, 'personal_certificate')
            
            # Test invalid certificate type
            with pytest.raises(ValidationError):
                pdf_service.generate_certificate(1, 'invalid_type')
    
    @patch('pdf_service.weasyprint')
    @patch('pdf_service.render_template')
    def test_generate_certificate_success(self, mock_render, mock_weasyprint, 
                                        pdf_service, app, test_donation):
        """Test successful certificate generation"""
        with app.app_context():
            # Setup mocks
            mock_render.return_value = "<html>Test Certificate</html>"
            mock_html_doc = MagicMock()
            mock_weasyprint.HTML.return_value = mock_html_doc
            mock_weasyprint.CSS.return_value = MagicMock()
            
            # Create temporary directory for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                app.config['CERTIFICATE_STORAGE_PATH'] = temp_dir
                
                # Generate certificate
                certificate = pdf_service.generate_certificate(
                    test_donation.id, 'personal_certificate', 'test_session'
                )
                
                # Verify certificate record
                assert certificate.donation_id == test_donation.id
                assert certificate.certificate_type == 'personal_certificate'
                assert certificate.filename.endswith('.pdf')
                assert certificate.file_path is not None
                
                # Verify template was rendered
                mock_render.assert_called_once()
                
                # Verify WeasyPrint was called
                mock_weasyprint.HTML.assert_called_once()
                mock_html_doc.write_pdf.assert_called_once()
    
    @patch('pdf_service.weasyprint')
    def test_generate_pdf_weasyprint_error(self, mock_weasyprint, pdf_service, app):
        """Test WeasyPrint error handling"""
        with app.app_context():
            # Setup mock to raise exception
            mock_weasyprint.HTML.side_effect = Exception("WeasyPrint failed")
            
            # Test error handling
            with pytest.raises(PDFGenerationError):
                pdf_service._generate_pdf_from_html("<html></html>", "/tmp/test.pdf")
    
    def test_batch_generation_logic(self, pdf_service, app, test_donation):
        """Test batch generation donation type mapping"""
        with app.app_context():
            # Test donation type mapping
            test_cases = [
                ('person', 'personal_certificate'),
                ('gruppe', 'group_certificate'), 
                ('geschenk', 'gift_certificate'),
                ('unknown', 'personal_certificate')  # Default fallback
            ]
            
            for donation_type, expected_cert_type in test_cases:
                test_donation.donation_type = donation_type
                
                # Mock the actual generation to avoid file creation
                with patch.object(pdf_service, 'generate_certificate') as mock_gen:
                    mock_gen.return_value = MagicMock()
                    
                    certificates = pdf_service.generate_certificate_batch(
                        [test_donation.id], 'test_session'
                    )
                    
                    # Verify correct certificate type was used
                    mock_gen.assert_called_with(
                        test_donation.id, expected_cert_type, 'test_session'
                    )


# Integration Tests
class TestPDFServiceIntegration:
    """Integration tests with real templates"""
    
    def test_template_rendering(self, app):
        """Test that certificate templates can be rendered"""
        with app.app_context():
            # Test basic template rendering without WeasyPrint
            from flask import render_template
            
            # Mock context data
            context = {
                'donation': MagicMock(
                    amount=Decimal('100.00'),
                    completed_at=datetime.now()
                ),
                'person_snapshot': {
                    'first_name': 'Test',
                    'last_name': 'User'
                },
                'verse': MagicMock(
                    reference='Test 1,1',
                    text='Test verse text'
                ),
                'verses': [MagicMock(
                    reference='Test 1,1',
                    text='Test verse text'
                )],
                'background_image_path': '/static/certificates/certificate-background.png'
            }
            
            # Test each template can be rendered
            templates = [
                'certificates/personal_certificate.html',
                'certificates/group_certificate.html', 
                'certificates/gift_certificate.html',
                'certificates/tax_receipt.html'
            ]
            
            for template in templates:
                try:
                    html = render_template(template, **context)
                    assert html is not None
                    assert len(html) > 0
                except Exception as e:
                    pytest.fail(f"Failed to render template {template}: {str(e)}")


if __name__ == '__main__':
    pytest.main([__file__])