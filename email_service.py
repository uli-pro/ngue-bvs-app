#!/usr/bin/env python3
"""
E-Mail Service für NGÜ Bibelvers-Sponsoring App
Unterstützt Gmail (SMTP) und Mailgun (REST API) Provider
"""

import os
import secrets
import smtplib
import ssl
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod
from flask import current_app, render_template
from flask_mail import Mail, Message
import logging

# Custom Exceptions
class EmailServiceError(Exception):
    """Base exception for email service errors"""
    pass

class EmailProviderError(EmailServiceError):
    """Provider-specific error"""
    pass

class EmailTemplateError(EmailServiceError):
    """Template rendering error"""
    pass

class EmailConfigurationError(EmailServiceError):
    """Configuration error"""
    pass

# Abstract Base Provider
class BaseEmailProvider(ABC):
    """Abstract base class for email providers"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_body: str, 
                   text_body: str, attachments: List[Dict] = None) -> bool:
        """Send email with optional attachments"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test provider connection"""
        pass

# Gmail Provider Implementation
class GmailProvider(BaseEmailProvider):
    """Gmail SMTP Provider using Flask-Mail"""
    
    def __init__(self, mail_instance: Mail):
        super().__init__()
        self.mail = mail_instance
        self.from_email = os.environ.get('GMAIL_USERNAME')
        self.from_name = os.environ.get('EMAIL_FROM_NAME', 'NGÜ Zertifikate')
    
    def send_email(self, to_email: str, subject: str, html_body: str, 
                   text_body: str, attachments: List[Dict] = None) -> bool:
        """Send email via Gmail SMTP"""
        try:
            msg = Message(
                subject=subject,
                sender=(self.from_name, self.from_email),
                recipients=[to_email]
            )
            
            msg.body = text_body
            msg.html = html_body
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    with open(attachment['path'], 'rb') as f:
                        msg.attach(
                            attachment['filename'],
                            attachment['mimetype'],
                            f.read()
                        )
            
            self.mail.send(msg)
            self.logger.info(f"Gmail: Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Gmail send error: {e}")
            raise EmailProviderError(f"Gmail send failed: {e}")
    
    def test_connection(self) -> bool:
        """Test Gmail SMTP connection"""
        try:
            # Simple connection test via smtplib
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls(context=context)
                server.login(self.from_email, os.environ.get('GMAIL_APP_PASSWORD'))
                self.logger.info("Gmail connection test successful")
                return True
        except Exception as e:
            self.logger.error(f"Gmail connection test failed: {e}")
            return False

# Mailgun Provider Implementation  
class MailgunProvider(BaseEmailProvider):
    """Mailgun REST API Provider"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get('MAILGUN_API_KEY')
        self.domain = os.environ.get('MAILGUN_DOMAIN')
        self.from_email = os.environ.get('MAILGUN_FROM_EMAIL')
        self.from_name = os.environ.get('EMAIL_FROM_NAME', 'NGÜ Zertifikate')
        # Use EU API for European domains
        self.api_url = f"https://api.eu.mailgun.net/v3/{self.domain}/messages"
    
    def send_email(self, to_email: str, subject: str, html_body: str, 
                   text_body: str, attachments: List[Dict] = None) -> bool:
        """Send email via Mailgun API"""
        try:
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to_email,
                "subject": subject,
                "text": text_body,
                "html": html_body
            }
            
            files = []
            if attachments:
                for attachment in attachments:
                    files.append(
                        ("attachment", (attachment['filename'], 
                         open(attachment['path'], 'rb'),
                         attachment['mimetype']))
                    )
            
            response = requests.post(
                self.api_url,
                auth=("api", self.api_key),
                data=data,
                files=files,
                timeout=30
            )
            
            # Close file handles
            for _, file_tuple in files:
                if hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()
            
            if response.status_code == 200:
                self.logger.info(f"Mailgun: Email sent successfully to {to_email}")
                return True
            else:
                self.logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
                raise EmailProviderError(f"Mailgun send failed: {response.text}")
                
        except Exception as e:
            self.logger.error(f"Mailgun send error: {e}")
            raise EmailProviderError(f"Mailgun send failed: {e}")
    
    def test_connection(self) -> bool:
        """Test Mailgun API connection"""
        try:
            domain_url = f"https://api.eu.mailgun.net/v3/domains/{self.domain}"
            response = requests.get(
                domain_url,
                auth=("api", self.api_key),
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Mailgun connection test successful")
                return True
            else:
                self.logger.error(f"Mailgun connection test failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Mailgun connection test failed: {e}")
            return False

# Main Email Service Class
class EmailService:
    """Main email service with provider abstraction"""
    
    def __init__(self, app=None):
        self.app = app
        self.provider = None
        self.mail = None
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Initialize Flask-Mail for Gmail
        self.mail = Mail(app)
        
        # Select and initialize provider
        provider_name = os.environ.get('EMAIL_PROVIDER', 'gmail').lower()
        
        if provider_name == 'gmail':
            self.provider = GmailProvider(self.mail)
        elif provider_name == 'mailgun':
            self.provider = MailgunProvider()
        else:
            raise EmailConfigurationError(f"Unknown email provider: {provider_name}")
        
        self.logger.info(f"Email service initialized with {provider_name} provider")
    
    def test_connection(self) -> bool:
        """Test email provider connection"""
        if not self.provider:
            raise EmailConfigurationError("Email service not initialized")
        return self.provider.test_connection()
    
    def _render_template(self, template_name: str, **kwargs) -> tuple:
        """Render email template (HTML and text versions)"""
        try:
            html_template = f"email/{template_name}.html"
            text_template = f"email/{template_name}.txt"
            
            html_body = render_template(html_template, **kwargs)
            
            # Try to render text version, fallback to HTML conversion
            try:
                text_body = render_template(text_template, **kwargs)
            except:
                # Simple HTML to text conversion
                import re
                text_body = re.sub('<[^<]+?>', '', html_body)
                text_body = re.sub(r'\n\s*\n', '\n\n', text_body.strip())
            
            return html_body, text_body
            
        except Exception as e:
            self.logger.error(f"Template rendering error: {e}")
            raise EmailTemplateError(f"Failed to render template {template_name}: {e}")
    
    def send_certificate_email(self, donation_data: Dict[str, Any], 
                             pdf_path: str) -> bool:
        """Send certificate email with PDF attachment"""
        try:
            html_body, text_body = self._render_template(
                'certificate',
                donation=donation_data,
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M')
            )
            
            attachments = [{
                'path': pdf_path,
                'filename': f"NGÜ_Zertifikat_{donation_data['id']}.pdf",
                'mimetype': 'application/pdf'
            }]
            
            return self.provider.send_email(
                to_email=donation_data['person']['email'],
                subject=f"Ihr NGÜ Zertifikat - Spende #{donation_data['id']}",
                html_body=html_body,
                text_body=text_body,
                attachments=attachments
            )
            
        except Exception as e:
            self.logger.error(f"Certificate email failed: {e}")
            raise EmailServiceError(f"Failed to send certificate email: {e}")
    
    def send_certificate_email_with_attachments(self, donation_data: Dict[str, Any], 
                                              pdf_attachments: List[Dict[str, str]]) -> bool:
        """Send certificate email with multiple PDF attachments"""
        try:
            html_body, text_body = self._render_template(
                'certificate',
                donation=donation_data,
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M')
            )
            
            return self.provider.send_email(
                to_email=donation_data['person']['email'],
                subject=f"Ihre NGÜ Dokumente - Spende #{donation_data['id']}",
                html_body=html_body,
                text_body=text_body,
                attachments=pdf_attachments
            )
            
        except Exception as e:
            self.logger.error(f"Certificate email with attachments failed: {e}")
            raise EmailServiceError(f"Failed to send certificate email with attachments: {e}")
    
    def send_donation_confirmation(self, donation_data: Dict[str, Any]) -> bool:
        """Send donation confirmation email"""
        try:
            html_body, text_body = self._render_template(
                'confirmation',
                donation=donation_data,
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M')
            )
            
            return self.provider.send_email(
                to_email=donation_data['person']['email'],
                subject=f"Spendenbestätigung - NGÜ Bibelvers #{donation_data['id']}",
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            self.logger.error(f"Confirmation email failed: {e}")
            raise EmailServiceError(f"Failed to send confirmation email: {e}")
    
    def generate_magic_link_token(self, email: str, expiry_minutes: int = 15) -> str:
        """Generate secure token for magic link authentication"""
        token = secrets.token_urlsafe(32)
        self.logger.info(f"Generated magic link token for {email} (expires in {expiry_minutes}min)")
        return token
    
    def send_magic_link_email(self, email: str, token: str, 
                            login_url: str, expiry_minutes: int = 15) -> bool:
        """Send magic link login email (prepared for future admin functionality)"""
        try:
            magic_link = f"{login_url}?token={token}"
            
            html_body, text_body = self._render_template(
                'magic_link',
                email=email,
                magic_link=magic_link,
                expiry_minutes=expiry_minutes,
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M')
            )
            
            return self.provider.send_email(
                to_email=email,
                subject="NGÜ Admin Login - Ihr Anmelde-Link",
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            self.logger.error(f"Magic link email failed: {e}")
            raise EmailServiceError(f"Failed to send magic link email: {e}")
    
    def send_test_email(self, to_email: str) -> bool:
        """Send test email for verification"""
        try:
            html_body, text_body = self._render_template(
                'test',
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M'),
                provider=self.provider.__class__.__name__
            )
            
            return self.provider.send_email(
                to_email=to_email,
                subject=f"NGÜ E-Mail Test - {datetime.now().strftime('%H:%M:%S')}",
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            self.logger.error(f"Test email failed: {e}")
            raise EmailServiceError(f"Failed to send test email: {e}")

# Global instance
email_service = EmailService()