#!/usr/bin/env python3
# NGÜ BVS App - SMTP Email Service with Automatic Fallback
# Versucht primär IONOS, fällt automatisch auf Gmail zurück

"""
E-Mail Service für NGÜ Bibelvers-Sponsoring App
Intelligentes Fallback-System: IONOS → Gmail
"""

import os
import secrets
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid
from typing import Optional, List, Dict, Any, Tuple
from flask import current_app, render_template
import logging

# Custom Exceptions
class EmailServiceError(Exception):
    """Base exception for email service errors"""
    pass

class EmailConfigurationError(EmailServiceError):
    """Configuration error"""
    pass

class EmailTemplateError(EmailServiceError):
    """Template rendering error"""
    pass

# SMTP Provider Implementation
class SMTPProvider:
    """SMTP Provider with automatic IONOS/Gmail fallback"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Store both configurations
        self.configs = []

        # Priority 1: IONOS Configuration (if configured)
        if os.environ.get('SMTP_PASSWORD'):
            ionos_config = {
                'name': 'IONOS',
                'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.ionos.de'),
                'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
                'smtp_username': os.environ.get('SMTP_USERNAME', 'info@ngue-bvs.schoeffer.org'),
                'smtp_password': os.environ.get('SMTP_PASSWORD'),
                'smtp_use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true',
                'from_email': os.environ.get('EMAIL_FROM', 'info@ngue-bvs.schoeffer.org'),
                'from_name': os.environ.get('EMAIL_FROM_NAME', 'NGUE Bibelvers-Sponsoring')
            }
            self.configs.append(ionos_config)
            self.logger.info("IONOS configuration loaded (primary)")

        # Priority 2: Gmail Configuration (fallback)
        if os.environ.get('GMAIL_APP_PASSWORD'):
            gmail_config = {
                'name': 'Gmail',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_username': os.environ.get('GMAIL_USERNAME', 'ngueteam@gmail.com'),
                'smtp_password': os.environ.get('GMAIL_APP_PASSWORD'),
                'smtp_use_tls': True,
                'from_email': os.environ.get('GMAIL_USERNAME', 'ngueteam@gmail.com'),
                'from_name': 'NGUE Bibelvers-Sponsoring'
            }
            self.configs.append(gmail_config)
            self.logger.info("Gmail configuration loaded (fallback)")

        # Check if we should prefer Gmail (for local development)
        if os.environ.get('USE_GMAIL_FALLBACK', 'false').lower() == 'true':
            # Reverse order to prefer Gmail
            self.configs.reverse()
            self.logger.info("Gmail set as preferred provider for local development")

        if not self.configs:
            raise EmailConfigurationError("No email provider configured! Set either SMTP_PASSWORD or GMAIL_APP_PASSWORD")

        # Set active configuration to the first one
        self.active_config = self.configs[0]
        self.logger.info(f"Active email provider: {self.active_config['name']}")

    def _send_with_config(self, config: Dict, to_email: str, subject: str,
                         html_body: str, text_body: str, attachments: List[Dict] = None) -> Tuple[bool, Optional[str]]:
        """Try to send email with specific configuration"""
        try:
            # FIX (2025-01-17): MIME structure for emails with attachments
            # BEFORE: Always used 'alternative' (caused IONOS policy 554 errors + missing PDFs)
            # AFTER: Use 'mixed' for attachments (RFC 2046 compliant)
            # RFC 2046: 'alternative' = "choose one", 'mixed' = "show all parts"
            # ROLLBACK: If IONOS rejects, change back to 'alternative' and investigate policy

            if attachments:
                # Structure: mixed [ alternative[text, html], pdf1, pdf2, ... ]
                msg = MIMEMultipart('mixed')
                self.logger.info(f"Creating email with {len(attachments)} attachments: "
                               f"{[a['filename'] for a in attachments]}")
            else:
                # No attachments: simple alternative (text vs html)
                msg = MIMEMultipart('alternative')

            # Required headers
            msg['From'] = f"{config['from_name']} <{config['from_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = formatdate(localtime=True)

            # Additional headers
            domain = config['from_email'].split('@')[1]
            msg['Message-ID'] = make_msgid(domain=domain)
            # MIME-Version is auto-added by MIMEMultipart - manual setting can cause duplicates
            msg['X-Mailer'] = 'NGUE BVS App/1.0'
            msg['Reply-To'] = config['from_email']
            # Return-Path must be set by MTA, not sender - IONOS rejects if manually set

            # Prevent auto-replies
            msg['X-Auto-Response-Suppress'] = 'All'
            msg['Auto-Submitted'] = 'auto-generated'

            # Add text and HTML parts
            if attachments:
                # Nested structure for proper MIME compliance
                alt_part = MIMEMultipart('alternative')
                alt_part.attach(MIMEText(text_body, 'plain', 'utf-8'))
                alt_part.attach(MIMEText(html_body, 'html', 'utf-8'))
                msg.attach(alt_part)
            else:
                # No attachments: simple structure
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # Add attachments if provided (with improved error handling)
            if attachments:
                for i, attachment in enumerate(attachments, 1):
                    try:
                        self.logger.debug(f"Attaching {i}/{len(attachments)}: {attachment['filename']} "
                                        f"from {attachment['path']}")
                        with open(attachment['path'], 'rb') as f:
                            # Explicit _subtype='pdf' sets Content-Type: application/pdf
                            # (instead of generic application/octet-stream)
                            part = MIMEApplication(f.read(), _subtype='pdf',
                                                 Name=attachment['filename'])
                            part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
                            msg.attach(part)
                        self.logger.debug(f"Successfully attached: {attachment['filename']}")
                    except FileNotFoundError:
                        error_msg = f"Attachment file not found: {attachment['path']}"
                        self.logger.error(error_msg)
                        raise FileNotFoundError(error_msg)
                    except Exception as e:
                        error_msg = f"Failed to attach {attachment['filename']}: {str(e)}"
                        self.logger.error(error_msg)
                        raise

            # Send email
            context = ssl.create_default_context()

            with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=30) as server:
                if config['smtp_use_tls']:
                    server.starttls(context=context)
                server.login(config['smtp_username'], config['smtp_password'])
                server.send_message(msg)

            self.logger.info(f"Email sent successfully via {config['name']} to {to_email}")
            return True, None

        except Exception as e:
            error_msg = f"{config['name']} failed: {str(e)}"
            self.logger.warning(error_msg)
            return False, error_msg

    def send_email(self, to_email: str, subject: str, html_body: str,
                   text_body: str, attachments: List[Dict] = None) -> bool:
        """Send email with automatic fallback"""
        errors = []

        # Try each configuration in order
        for config in self.configs:
            self.logger.info(f"Attempting to send via {config['name']}...")
            success, error = self._send_with_config(config, to_email, subject,
                                                   html_body, text_body, attachments)
            if success:
                # Update active config for future sends
                self.active_config = config
                return True
            else:
                errors.append(error)

        # All providers failed
        error_summary = " | ".join(errors)
        self.logger.error(f"All email providers failed: {error_summary}")
        raise EmailServiceError(f"Email delivery failed. Tried all providers: {error_summary}")

    def test_connection(self) -> bool:
        """Test SMTP connection for all configured providers"""
        results = []

        for config in self.configs:
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=10) as server:
                    if config['smtp_use_tls']:
                        server.starttls(context=context)
                    server.login(config['smtp_username'], config['smtp_password'])
                    self.logger.info(f"{config['name']} connection test successful")
                    results.append(True)
            except Exception as e:
                self.logger.warning(f"{config['name']} connection test failed: {e}")
                results.append(False)

        # Return True if at least one provider works
        return any(results)

# Main Email Service Class
class EmailService:
    """Main email service with automatic fallback"""

    def __init__(self, app=None):
        self.app = app
        self.provider = None
        self.logger = logging.getLogger(__name__)

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app

        # Initialize SMTP provider with fallback support
        self.provider = SMTPProvider()
        self.logger.info("Email service initialized with fallback support")

    def test_connection(self) -> bool:
        """Test email provider connection"""
        if not self.provider:
            raise EmailConfigurationError("Email service not initialized")
        return self.provider.test_connection()

    def _render_template(self, template_name: str, **kwargs) -> tuple:
        """Render email template (HTML and text versions)

        FIX (2025-01-17): Improved logging and error handling
        - Added debug logging for template rendering
        - Better exception handling for missing text templates
        - Clear error messages for debugging
        """
        try:
            html_template = f"email/{template_name}.html"
            text_template = f"email/{template_name}.txt"

            # Render HTML version
            try:
                html_body = render_template(html_template, **kwargs)
                self.logger.debug(f"HTML template '{template_name}.html' rendered: {len(html_body)} chars")
            except Exception as e:
                self.logger.error(f"HTML template rendering failed for '{template_name}.html': {e}")
                self.logger.error(f"Template kwargs: {list(kwargs.keys())}")
                raise EmailTemplateError(f"HTML template '{template_name}.html' failed: {e}")

            # Try to render text version, fallback to HTML conversion
            try:
                text_body = render_template(text_template, **kwargs)
                self.logger.debug(f"Text template '{template_name}.txt' rendered: {len(text_body)} chars")
            except Exception as e:
                # Text template doesn't exist or failed - use HTML to text conversion
                self.logger.debug(f"Text template '{template_name}.txt' not found, using HTML fallback: {e}")
                import re
                text_body = re.sub('<[^<]+?>', '', html_body)
                text_body = re.sub(r'\n\s*\n', '\n\n', text_body.strip())
                self.logger.debug(f"Fallback text generated: {len(text_body)} chars")

            if not html_body:
                raise EmailTemplateError(f"HTML template '{template_name}.html' rendered empty content")
            if not text_body:
                self.logger.warning(f"Text body is empty for template '{template_name}'")

            return html_body, text_body

        except EmailTemplateError:
            # Re-raise EmailTemplateError as-is
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error rendering template '{template_name}': {e}", exc_info=True)
            raise EmailTemplateError(f"Failed to render template '{template_name}': {e}")

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
                subject=f"Ihr NGUE Zertifikat - Spende #{donation_data['id']}",
                html_body=html_body,
                text_body=text_body,
                attachments=attachments
            )

        except Exception as e:
            self.logger.error(f"Certificate email failed: {e}")
            raise EmailServiceError(f"Failed to send certificate email: {e}")

    def send_tax_receipt_email(self, donation_data: Dict[str, Any],
                             pdf_path: str) -> bool:
        """Send tax receipt email with PDF attachment"""
        try:
            html_body, text_body = self._render_template(
                'tax_receipt',
                donation=donation_data,
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M')
            )

            attachments = [{
                'path': pdf_path,
                'filename': f"NGÜ_Spendenbescheinigung_{donation_data['id']}.pdf",
                'mimetype': 'application/pdf'
            }]

            return self.provider.send_email(
                to_email=donation_data['person']['email'],
                subject=f"Ihre NGUE Spendenbescheinigung - Spende #{donation_data['id']}",
                html_body=html_body,
                text_body=text_body,
                attachments=attachments
            )

        except Exception as e:
            self.logger.error(f"Tax receipt email failed: {e}")
            return False

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
                subject=f"Ihre NGUE Dokumente - Spende #{donation_data['id']}",
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
                subject=f"Spendenbestätigung - NGUE Bibelvers #{donation_data['id']}",
                html_body=html_body,
                text_body=text_body
            )

        except Exception as e:
            self.logger.error(f"Confirmation email failed: {e}")
            raise EmailServiceError(f"Failed to send confirmation email: {e}")

    def send_contact_form_email(self, name: str, email: str, subject: str,
                                message: str, send_confirmation: bool = True) -> bool:
        """Send contact form submission to NGÜ team and optional auto-reply to sender

        Args:
            name: Sender's name
            email: Sender's email address
            subject: Message subject
            message: Message content
            send_confirmation: Whether to send auto-reply to sender (default: True)

        Returns:
            bool: True if email(s) sent successfully

        Raises:
            EmailServiceError: If email sending fails
        """
        try:
            timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')

            # 1. Send notification to NGÜ team
            html_body, text_body = self._render_template(
                'contact',
                name=name,
                email=email,
                subject=subject,
                message=message,
                timestamp=timestamp
            )

            # Send to info@ngue-bvs.schoeffer.org (IONOS config)
            recipient_email = self.provider.active_config['from_email']

            success = self.provider.send_email(
                to_email=recipient_email,
                subject=f"Kontaktformular: {subject}",
                html_body=html_body,
                text_body=text_body
            )

            if not success:
                raise EmailServiceError("Failed to send contact form notification to team")

            self.logger.info(f"Contact form submission sent to {recipient_email} from {email}")

            # 2. Send confirmation to sender (optional)
            if send_confirmation:
                try:
                    confirm_html, confirm_text = self._render_template(
                        'contact_confirmation',
                        name=name,
                        subject=subject,
                        message=message,
                        timestamp=timestamp
                    )

                    confirmation_success = self.provider.send_email(
                        to_email=email,
                        subject=f"Ihre Nachricht an NGÜ Bibelvers-Sponsoring",
                        html_body=confirm_html,
                        text_body=confirm_text
                    )

                    if confirmation_success:
                        self.logger.info(f"Confirmation email sent to {email}")
                    else:
                        self.logger.warning(f"Confirmation email to {email} failed (notification sent)")

                except Exception as e:
                    # Log but don't fail the whole operation if confirmation fails
                    self.logger.warning(f"Failed to send confirmation to {email}: {e}")

            return True

        except EmailTemplateError as e:
            self.logger.error(f"Contact form template error: {e}")
            raise EmailServiceError(f"Template rendering failed: {e}")
        except Exception as e:
            self.logger.error(f"Contact form email failed: {e}")
            raise EmailServiceError(f"Failed to send contact form email: {e}")

    def generate_magic_link_token(self, email: str, expiry_minutes: int = 15) -> str:
        """Generate secure token for magic link authentication"""
        token = secrets.token_urlsafe(32)
        self.logger.info(f"Generated magic link token for {email} (expires in {expiry_minutes}min)")
        return token

    def send_admin_magic_link(self, to_email, magic_link):
        """Send magic link for admin login"""
        subject = "NGUE Admin - Ihr Login-Link"

        html_content = f"""
        <h2>Admin Login</h2>
        <p>Sie haben einen Login-Link für den NGÜ Admin-Bereich angefordert.</p>
        <p>
            <a href="{magic_link}" style="display: inline-block; padding: 10px 20px;
               background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px;">
                Jetzt anmelden
            </a>
        </p>
        <p>Oder kopieren Sie diesen Link in Ihren Browser:</p>
        <p>{magic_link}</p>
        <p><strong>Dieser Link ist 15 Minuten gültig.</strong></p>
        <p>Falls Sie diesen Link nicht angefordert haben, ignorieren Sie diese E-Mail.</p>
        """

        text_content = f"""
        Admin Login

        Sie haben einen Login-Link für den NGÜ Admin-Bereich angefordert.

        Klicken Sie hier zum Anmelden:
        {magic_link}

        Dieser Link ist 15 Minuten gültig.

        Falls Sie diesen Link nicht angefordert haben, ignorieren Sie diese E-Mail.
        """

        return self.send_email(to_email, subject, text_content, html_content)

    def send_email(self, to_email: str, subject: str, text_body: str, html_body: str = None) -> bool:
        """Direct email send method with automatic fallback"""
        if not self.provider:
            raise EmailConfigurationError("Email service not initialized")

        html_body = html_body or text_body
        return self.provider.send_email(to_email, subject, html_body, text_body)

    def send_test_email(self, to_email: str) -> bool:
        """Send test email for verification"""
        try:
            # Get current provider name
            provider_name = self.provider.active_config['name'] if self.provider else 'Unknown'

            html_body, text_body = self._render_template(
                'test',
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M'),
                provider=provider_name
            )

            return self.provider.send_email(
                to_email=to_email,
                subject=f"NGUE E-Mail Test - {datetime.now().strftime('%H:%M:%S')}",
                html_body=html_body,
                text_body=text_body
            )

        except Exception as e:
            self.logger.error(f"Test email failed: {e}")
            raise EmailServiceError(f"Failed to send test email: {e}")

# Global instance
email_service = EmailService()