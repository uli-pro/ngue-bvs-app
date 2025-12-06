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

    def send_payment_failed_email(self, donation_data: Dict[str, Any],
                                  failure_reason: str) -> bool:
        """Send payment failed notification email (no certificate was issued yet)

        This is used for immediate payment failures (e.g., card declined)
        where no certificate/receipt was ever sent to the donor.

        Args:
            donation_data: Donation dict with 'id', 'person', 'total_amount', 'created_at'
            failure_reason: Human-readable failure reason from Stripe

        Returns:
            bool: True if email sent successfully
        """
        try:
            html_body, text_body = self._render_template(
                'payment_failed',
                donation=donation_data,
                failure_reason=failure_reason,
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M')
            )

            success = self.provider.send_email(
                to_email=donation_data['person']['email'],
                subject=f"Zahlung fehlgeschlagen - Spende #{donation_data['id']}",
                html_body=html_body,
                text_body=text_body
            )

            if success:
                self.logger.info(f"Payment failed email sent for donation {donation_data['id']}")
            return success

        except Exception as e:
            self.logger.error(f"Payment failed email failed for donation {donation_data.get('id')}: {e}")
            return False

    def send_storno_email(self, donation_data: Dict[str, Any],
                          storno_pdf_path: str,
                          storno_context: Dict[str, Any]) -> bool:
        """Send storno/cancellation email with PDF attachment

        This is used for delayed payment failures (SEPA) or chargebacks
        where a certificate/receipt was already sent to the donor.

        Args:
            donation_data: Donation dict with 'id', 'person', 'total_amount', etc.
            storno_pdf_path: Path to the generated storno PDF
            storno_context: Context dict from pdf_service._prepare_storno_context() containing:
                - original_receipt_number: Original receipt number being cancelled
                - original_date: Date of original receipt
                - cancellation_reason: Reason for cancellation
                - cancellation_date: Today's date
                - verse_references: List of affected verse references

        Returns:
            bool: True if email sent successfully
        """
        try:
            # Merge donation_data with storno_context for template
            html_body, text_body = self._render_template(
                'storno',
                donation=donation_data,
                original_receipt_number=storno_context.get('original_receipt_number'),
                original_date=storno_context.get('original_date'),
                cancellation_reason=storno_context.get('cancellation_reason'),
                cancellation_date=storno_context.get('cancellation_date'),
                verse_references=storno_context.get('verse_references', []),
                timestamp=datetime.now().strftime('%d.%m.%Y %H:%M')
            )

            # Attachment: Storno-PDF
            attachments = [{
                'path': storno_pdf_path,
                'filename': f"Storno_Bescheinigung_{storno_context.get('original_receipt_number', donation_data['id'])}.pdf",
                'mimetype': 'application/pdf'
            }]

            success = self.provider.send_email(
                to_email=donation_data['person']['email'],
                subject=f"Wichtig: Stornierung Ihrer Zuwendungsbestätigung - {storno_context.get('original_receipt_number')}",
                html_body=html_body,
                text_body=text_body,
                attachments=attachments
            )

            if success:
                self.logger.info(
                    f"Storno email sent for donation {donation_data['id']} "
                    f"(receipt {storno_context.get('original_receipt_number')})"
                )
            return success

        except Exception as e:
            self.logger.error(
                f"Storno email failed for donation {donation_data.get('id')}: {e}"
            )
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

    def send_admin_alert(self, subject: str, message: str,
                        error_details: str = None, context: Dict[str, Any] = None) -> bool:
        """Send alert email to admin for critical errors or notifications

        Args:
            subject: Alert subject (will be prefixed with [NGUE Alert])
            message: Main alert message
            error_details: Optional technical error details
            context: Optional dictionary with additional context (donation_id, user_email, etc.)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            admin_email = current_app.config.get('ADMIN_EMAIL')

            if not admin_email:
                self.logger.warning("ADMIN_EMAIL not configured - cannot send admin alert")
                return False

            timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

            # Build context details string
            context_html = ""
            context_text = ""
            if context:
                context_html = "<h3>Kontext:</h3><ul>"
                context_text = "\nKontext:\n"
                for key, value in context.items():
                    context_html += f"<li><strong>{key}:</strong> {value}</li>"
                    context_text += f"  - {key}: {value}\n"
                context_html += "</ul>"

            # Build error details section
            error_html = ""
            error_text = ""
            if error_details:
                error_html = f"""
                <h3>Technische Details:</h3>
                <pre style="background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto;">{error_details}</pre>
                """
                error_text = f"\nTechnische Details:\n{error_details}\n"

            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #dc3545; color: white; padding: 15px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0;">⚠️ NGÜ Admin Alert</h2>
                </div>
                <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 5px 5px;">
                    <p><strong>Zeitpunkt:</strong> {timestamp}</p>
                    <h3>Nachricht:</h3>
                    <p>{message}</p>
                    {context_html}
                    {error_html}
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        Diese Nachricht wurde automatisch vom NGÜ Bibelvers-Sponsoring System generiert.
                    </p>
                </div>
            </div>
            """

            text_body = f"""
NGÜ Admin Alert
===============

Zeitpunkt: {timestamp}

Nachricht:
{message}
{context_text}{error_text}
---
Diese Nachricht wurde automatisch vom NGÜ Bibelvers-Sponsoring System generiert.
            """

            full_subject = f"[NGUE Alert] {subject}"

            success = self.provider.send_email(
                to_email=admin_email,
                subject=full_subject,
                html_body=html_body,
                text_body=text_body
            )

            if success:
                self.logger.info(f"Admin alert sent to {admin_email}: {subject}")
            else:
                self.logger.error(f"Failed to send admin alert to {admin_email}: {subject}")

            return success

        except Exception as e:
            self.logger.error(f"Admin alert failed: {e}")
            return False

    def send_daily_donation_report(self, report_date: 'date' = None) -> bool:
        """Send daily donation report to admin email.

        Args:
            report_date: Date for the report (default: yesterday)

        Returns:
            bool: True if email sent successfully
        """
        from datetime import date, timedelta
        from decimal import Decimal
        from models import Donation
        from book_names import get_german_book_name

        try:
            admin_email = current_app.config.get('ADMIN_EMAIL')
            if not admin_email:
                self.logger.warning("ADMIN_EMAIL not configured - cannot send daily report")
                return False

            # Default to yesterday
            if report_date is None:
                report_date = date.today() - timedelta(days=1)

            # Query all donations for the given date (00:00:00 - 23:59:59)
            start_of_day = datetime.combine(report_date, datetime.min.time())
            end_of_day = datetime.combine(report_date, datetime.max.time())

            donations = Donation.query.filter(
                Donation.created_at >= start_of_day,
                Donation.created_at <= end_of_day
            ).order_by(Donation.created_at.asc()).all()

            # Prepare donation data with formatted verses
            donation_data = []
            total_amount = Decimal('0')
            bulk_count = 0

            for donation in donations:
                # Format verses display
                verses_display = self._format_verses_for_report(donation)

                # Create a simple object with the data we need
                donation_info = {
                    'id': donation.id,
                    'display_name': donation.display_name,
                    'verses_display': verses_display,
                    'total_amount': donation.total_amount,
                    'payment_status': donation.payment_status,
                    'created_at': donation.created_at,
                    'is_bulk_sponsoring': donation.is_bulk_sponsoring
                }
                donation_data.append(type('DonationInfo', (), donation_info)())

                # Only count non-bulk sponsorings in total
                if not donation.is_bulk_sponsoring:
                    total_amount += donation.total_amount
                else:
                    bulk_count += 1

            # Calculate cumulative totals by status (excluding bulk sponsorings)
            from sqlalchemy import func
            from models import db

            # Helper function to get sum and count for a status
            def get_status_totals(status):
                result = db.session.query(
                    func.sum(Donation.total_amount),
                    func.count(Donation.id)
                ).filter(
                    Donation.payment_status == status,
                    Donation.is_bulk_sponsoring == False,
                    Donation.created_at <= end_of_day
                ).first()
                return {
                    'amount': result[0] or Decimal('0'),
                    'count': result[1] or 0
                }

            # Get totals for each relevant status
            completed_totals = get_status_totals('completed')
            processing_totals = get_status_totals('processing')
            disputed_totals = get_status_totals('disputed')
            failed_totals = get_status_totals('failed')

            # Calculate net total (completed + processing - disputed)
            cumulative_amount = (
                completed_totals['amount'] +
                processing_totals['amount'] -
                disputed_totals['amount']
            )
            cumulative_count = (
                completed_totals['count'] +
                processing_totals['count']
            )  # disputed counted separately

            # Render templates
            generated_at = datetime.now()

            # Add custom filter for currency formatting
            def format_currency(value):
                if value is None:
                    return "0,00 EUR"
                return f"{value:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")

            # Template context with all status breakdowns
            template_context = {
                'report_date': report_date,
                'donations': donation_data,
                'total_amount': total_amount,
                'donation_count': len(donations),
                'bulk_count': bulk_count,
                # Cumulative totals by status
                'completed_totals': completed_totals,
                'processing_totals': processing_totals,
                'disputed_totals': disputed_totals,
                'failed_totals': failed_totals,
                # Net total (completed + processing - disputed)
                'cumulative_amount': cumulative_amount,
                'cumulative_count': cumulative_count,
                'generated_at': generated_at,
                'format_currency': format_currency
            }

            # Render HTML template
            html_body = render_template('email/daily_report.html', **template_context)

            # Render text template
            text_body = render_template('email/daily_report.txt', **template_context)

            # Send email
            subject = f"NGÜ Spenden-Report {report_date.strftime('%d.%m.%Y')}"

            success = self.provider.send_email(
                to_email=admin_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )

            if success:
                self.logger.info(f"Daily donation report sent for {report_date}")
            else:
                self.logger.error(f"Failed to send daily donation report for {report_date}")

            return success

        except Exception as e:
            self.logger.error(f"Daily donation report failed: {e}")
            return False

    def _format_verses_for_report(self, donation) -> str:
        """Format verses for display in report.

        Returns formatted string like:
        - "1. Mose 1,1" (single verse)
        - "Psalm 23,1; 23,2; 23,3" (2-5 verses)
        - "Psalm 23,1-6 (6 Verse)" (6+ verses)
        - "Daniel (komplett)" (bulk sponsoring of entire book)
        """
        from book_names import get_german_book_name

        verses = donation.get_verses_sorted() if hasattr(donation, 'get_verses_sorted') else []

        if not verses:
            return f"{donation.verse_count} Verse"

        # Check if bulk sponsoring - might be entire book or chapter
        if donation.is_bulk_sponsoring:
            # Check if all verses are from same book
            books = set(v.book for v in verses)
            if len(books) == 1:
                book_name = get_german_book_name(verses[0].book)
                # Check if it's all verses in a single chapter
                chapters = set(v.chapter for v in verses)
                if len(chapters) == 1:
                    return f"{book_name} Kap. {verses[0].chapter} (komplett)"
                else:
                    return f"{book_name} (komplett)"

        verse_count = len(verses)

        if verse_count == 1:
            v = verses[0]
            book_name = get_german_book_name(v.book)
            return f"{book_name} {v.chapter},{v.verse}"

        elif verse_count <= 5:
            # Show all verse references
            refs = []
            current_book = None
            for v in verses:
                book_name = get_german_book_name(v.book)
                if current_book != v.book:
                    refs.append(f"{book_name} {v.chapter},{v.verse}")
                    current_book = v.book
                else:
                    refs.append(f"{v.chapter},{v.verse}")
            return "; ".join(refs)

        else:
            # Show range for 6+ verses
            first_v = verses[0]
            last_v = verses[-1]
            first_book = get_german_book_name(first_v.book)

            # Check if all same book
            if all(v.book == first_v.book for v in verses):
                if all(v.chapter == first_v.chapter for v in verses):
                    # Same chapter
                    return f"{first_book} {first_v.chapter},{first_v.verse}-{last_v.verse} ({verse_count} Verse)"
                else:
                    # Same book, different chapters
                    return f"{first_book} {first_v.chapter},{first_v.verse} - {last_v.chapter},{last_v.verse} ({verse_count} Verse)"
            else:
                # Different books
                last_book = get_german_book_name(last_v.book)
                return f"{first_book} - {last_book} ({verse_count} Verse)"


# Global instance
email_service = EmailService()