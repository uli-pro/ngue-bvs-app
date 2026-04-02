from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, session
from admin.decorators import admin_required
from models import db, Person, Verse, Donation, VerseReservation, Certificate, BookPriority, CampaignUrl
from sqlalchemy import or_, func
from pdf_service import PDFGeneratorService
from email_service import email_service
from datetime import datetime, timedelta
import os

@admin_required
def index():
    """Admin overview page - no dashboard, just links"""
    stats = {
        'total_persons': Person.query.count(),
        'total_donations': Donation.query.count(),
        'sponsored_verses': Verse.query.filter_by(is_sponsored=True).count(),
        'active_reservations': VerseReservation.query.filter(
            VerseReservation.expires_at > datetime.utcnow()
        ).count()
    }
    return render_template('admin/index.html', stats=stats)

@admin_required
def persons_list():
    """List and search persons"""
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = Person.query
    
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Person.email.ilike(search_filter),
                Person.first_name.ilike(search_filter),
                Person.last_name.ilike(search_filter),
                Person.postal_code.ilike(search_filter)
            )
        )
    
    persons = query.order_by(Person.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/persons.html', persons=persons, search=search)

@admin_required
def person_edit(person_id):
    """Edit person data"""
    person = Person.query.get_or_404(person_id)
    
    if request.method == 'POST':
        # Check for email changes
        new_email = request.form.get('email', '').strip().lower()
        email_changed = new_email and new_email != person.email.lower()
        
        if email_changed:
            # Check if new email already exists
            existing_person = Person.query.filter(Person.email.ilike(new_email)).first()
            if existing_person and existing_person.id != person.id:
                flash(f'Fehler: E-Mail {new_email} wird bereits von einer anderen Person verwendet.', 'danger')
                return redirect(url_for('admin.person_edit', person_id=person_id))
            
            # Update email
            old_email = person.email
            person.email = new_email
            flash(f'E-Mail wurde von {old_email} zu {new_email} geändert.', 'warning')
        
        # Update other person data
        person.first_name = request.form.get('first_name', '').strip()
        person.last_name = request.form.get('last_name', '').strip()
        person.salutation = request.form.get('salutation', '').strip() or None
        person.street = request.form.get('street', '').strip()
        person.house_number = request.form.get('house_number', '').strip()
        person.postal_code = request.form.get('postal_code', '').strip()
        person.city = request.form.get('city', '').strip()
        person.newsletter_consent = request.form.get('newsletter_consent') == 'on'

        # Country handling
        country = request.form.get('country', 'DE').strip().upper()
        if len(country) == 2 and country.isalpha():
            person.country = country
        else:
            flash('Ungültiger Ländercode (muss 2 Buchstaben sein).', 'warning')

        person.data_updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'Person {person.full_name} wurde aktualisiert.', 'success')
        return redirect(url_for('admin.persons_list'))
    
    # Get recent donations for this person
    recent_donations = Donation.query.filter_by(person_id=person.id).order_by(Donation.created_at.desc()).limit(10).all()
    
    return render_template('admin/person_edit.html', person=person, recent_donations=recent_donations)

@admin_required
def verses_list():
    """Manage verses"""
    search = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Verse.query
    
    # Filter by status
    if filter_type == 'sponsored':
        query = query.filter_by(is_sponsored=True)
    elif filter_type == 'available':
        query = query.filter_by(is_sponsored=False)
    elif filter_type == 'reserved':
        query = query.join(VerseReservation).filter(
            VerseReservation.expires_at > datetime.utcnow()
        )
    
    # Search
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            or_(
                Verse.book.ilike(search_filter),
                func.concat(Verse.book, ' ', Verse.chapter, ',', Verse.verse).ilike(search_filter),
                Verse.text.ilike(search_filter)
            )
        )
    
    verses = query.order_by(Verse.book, Verse.chapter, Verse.verse).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/verses.html', verses=verses, search=search, filter_type=filter_type)

@admin_required
def verse_toggle(verse_id):
    """Toggle verse sponsored status"""
    verse = Verse.query.get_or_404(verse_id)
    
    if verse.is_sponsored:
        # Unmark as sponsored
        verse.is_sponsored = False
        verse.sponsored_at = None
        flash(f'Vers {verse.reference} wurde als verfuegbar markiert.', 'success')
    else:
        # Mark as sponsored (manual)
        verse.is_sponsored = True
        verse.sponsored_at = datetime.utcnow()
        flash(f'Vers {verse.reference} wurde als gesponsert markiert.', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.verses_list'))

@admin_required
def clear_reservations():
    """Clear expired reservations"""
    count = VerseReservation.query.filter(
        VerseReservation.expires_at < datetime.utcnow()
    ).delete()
    db.session.commit()
    flash(f'{count} abgelaufene Reservierungen wurden geloescht.', 'success')
    return redirect(url_for('admin.verses_list'))

@admin_required
def donations_list():
    """List donations"""
    filter_type = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Donation.query
    
    # Filter by status
    if filter_type == 'completed':
        query = query.filter_by(payment_status='completed')
    elif filter_type == 'pending':
        query = query.filter_by(payment_status='pending')
    elif filter_type == 'failed':
        query = query.filter_by(payment_status='failed')
    elif filter_type == 'disputed':
        query = query.filter_by(payment_status='disputed')
    elif filter_type == 'refunded':
        query = query.filter_by(payment_status='refunded')

    donations = query.order_by(Donation.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/donations.html', donations=donations, filter_type=filter_type)

@admin_required
def donation_detail(donation_id):
    """Show donation details with actions"""
    donation = Donation.query.get_or_404(donation_id)

    # Check if certificates exist for this donation (get newest)
    certificate = Certificate.query.filter_by(
        donation_id=donation_id,
        certificate_type='personal_certificate'
    ).order_by(Certificate.generated_at.desc()).first()

    # Check if tax receipt exists for this donation (get newest)
    tax_receipt = Certificate.query.filter_by(
        donation_id=donation_id,
        certificate_type='tax_receipt'
    ).order_by(Certificate.generated_at.desc()).first()

    # Check if storno certificate exists
    storno_cert = Certificate.query.filter_by(
        donation_id=donation_id,
        certificate_type='storno'
    ).order_by(Certificate.generated_at.desc()).first()

    # Get Stripe account ID for correct dashboard links
    stripe_account_id = os.getenv('STRIPE_ACCOUNT_ID', 'acct_1QzchbLmJHIgYDey')

    return render_template('admin/donation_detail.html',
                         donation=donation,
                         certificate=certificate,
                         tax_receipt=tax_receipt,
                         storno_cert=storno_cert,
                         stripe_account_id=stripe_account_id)

@admin_required
def update_donation_comment(donation_id):
    """Update admin comment for a donation"""
    donation = Donation.query.get_or_404(donation_id)

    if request.method == 'POST':
        admin_comment = request.form.get('admin_comment', '').strip()
        donation.admin_comment = admin_comment if admin_comment else None
        db.session.commit()
        flash('Kommentar wurde gespeichert.', 'success')

    return redirect(url_for('admin.donation_detail', donation_id=donation_id))

@admin_required
def regenerate_certificate(donation_id):
    """Regenerate certificate for donation"""
    donation = Donation.query.get_or_404(donation_id)
    
    if donation.payment_status != 'completed':
        flash('Zertifikat kann nur fuer abgeschlossene Spenden generiert werden.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))
    
    # Generate new certificate using the existing PDF service
    pdf_service = PDFGeneratorService()
    try:
        certificate = pdf_service.generate_certificate(donation.id, 'personal_certificate')
        if certificate:
            flash('Zertifikat wurde neu generiert.', 'success')
        else:
            flash('Fehler beim Generieren des Zertifikats.', 'danger')
    except Exception as e:
        flash(f'Fehler beim Generieren des Zertifikats: {str(e)}', 'danger')
    
    return redirect(url_for('admin.donation_detail', donation_id=donation_id))

@admin_required
def resend_certificate(donation_id):
    """Resend certificate email"""
    donation = Donation.query.get_or_404(donation_id)
    
    # Get the latest certificate for this donation
    certificate = Certificate.query.filter_by(donation_id=donation_id).order_by(Certificate.generated_at.desc()).first()
    if not certificate or not certificate.exists_on_disk:
        flash('Kein Zertifikat vorhanden. Bitte zuerst generieren.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))
    
    # Send email using existing certificate email method
    # The email service expects donation data in a specific format
    donation_data = {
        'id': donation.id,
        'created_at': donation.created_at,
        'total_amount': float(donation.total_amount),
        'person': {
            'email': donation.person.email,
            'full_name': donation.person.full_name,
            'first_name': donation.person.first_name,
            'last_name': donation.person.last_name
        },
        # Add verses information for completeness
        'verses': [{'reference': v.verse.reference, 'text': v.verse.text} 
                  for v in donation.verse_associations]
    }
    
    success = email_service.send_certificate_email(
        donation_data,
        certificate.file_path
    )
    
    if success:
        donation.email_sent = True
        donation.email_sent_at = datetime.utcnow()
        db.session.commit()
        
        # Send copy to admin
        admin_email = session.get('admin_email')
        if admin_email:
            admin_donation_data = donation_data.copy()
            admin_donation_data['person'] = donation_data['person'].copy()
            admin_donation_data['person']['email'] = admin_email
            try:
                email_service.send_certificate_email(
                    admin_donation_data,
                    certificate.file_path
                )
                flash('Zertifikat wurde per E-Mail versendet (Admin-Kopie gesendet).', 'success')
            except:
                flash('Zertifikat wurde per E-Mail versendet (Admin-Kopie fehlgeschlagen).', 'warning')
        else:
            flash('Zertifikat wurde per E-Mail versendet.', 'success')
    else:
        flash('Fehler beim Versenden der E-Mail.', 'danger')
    
    return redirect(url_for('admin.donation_detail', donation_id=donation_id))

@admin_required
def view_certificate(donation_id):
    """View/Download certificate PDF"""
    donation = Donation.query.get_or_404(donation_id)
    
    # Get the latest certificate for this donation
    certificate = Certificate.query.filter_by(
        donation_id=donation_id,
        certificate_type='personal_certificate'
    ).order_by(Certificate.generated_at.desc()).first()
    if not certificate or not certificate.exists_on_disk:
        flash('Kein Zertifikat vorhanden. Bitte zuerst generieren.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))
    
    # Send the PDF file to the browser for viewing
    return send_file(
        certificate.file_path,
        as_attachment=False,  # Display in browser instead of download
        download_name=certificate.filename,
        mimetype='application/pdf'
    )

@admin_required
def regenerate_tax_receipt(donation_id):
    """Regenerate tax receipt for donation"""
    donation = Donation.query.get_or_404(donation_id)
    
    if donation.payment_status != 'completed':
        flash('Spendenbescheinigung kann nur fuer abgeschlossene Spenden generiert werden.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))
    
    # Generate new tax receipt using the existing PDF service
    pdf_service = PDFGeneratorService()
    try:
        tax_receipt = pdf_service.generate_tax_receipt_atomic(donation.id)
        if tax_receipt:
            flash('Spendenbescheinigung wurde neu generiert.', 'success')
        else:
            flash('Fehler beim Generieren der Spendenbescheinigung.', 'danger')
    except Exception as e:
        flash(f'Fehler beim Generieren der Spendenbescheinigung: {str(e)}', 'danger')
    
    return redirect(url_for('admin.donation_detail', donation_id=donation_id))

@admin_required
def resend_tax_receipt(donation_id):
    """Resend tax receipt email"""
    donation = Donation.query.get_or_404(donation_id)
    
    # Get the latest tax receipt for this donation
    tax_receipt = Certificate.query.filter_by(
        donation_id=donation_id,
        certificate_type='tax_receipt'
    ).order_by(Certificate.generated_at.desc()).first()
    if not tax_receipt or not tax_receipt.exists_on_disk:
        flash('Keine Spendenbescheinigung vorhanden. Bitte zuerst generieren.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    # Send email using existing tax receipt email method
    # The email service expects donation data in a specific format
    donation_data = {
        'id': donation.id,
        'created_at': donation.created_at,
        'total_amount': float(donation.total_amount),
        'person': {
            'email': donation.person.email,
            'full_name': donation.person.full_name,
            'first_name': donation.person.first_name,
            'last_name': donation.person.last_name
        },
        # Add verses information for completeness
        'verses': [{'reference': v.verse.reference, 'text': v.verse.text} 
                  for v in donation.verse_associations]
    }
    
    success = email_service.send_tax_receipt_email(
        donation_data,
        tax_receipt.file_path
    )
    
    if success:
        # Send copy to admin
        admin_email = session.get('admin_email')
        if admin_email:
            admin_donation_data = donation_data.copy()
            admin_donation_data['person'] = donation_data['person'].copy()
            admin_donation_data['person']['email'] = admin_email
            try:
                email_service.send_tax_receipt_email(
                    admin_donation_data,
                    tax_receipt.file_path
                )
                flash('Spendenbescheinigung wurde per E-Mail versendet (Admin-Kopie gesendet).', 'success')
            except:
                flash('Spendenbescheinigung wurde per E-Mail versendet (Admin-Kopie fehlgeschlagen).', 'warning')
        else:
            flash('Spendenbescheinigung wurde per E-Mail versendet.', 'success')
    else:
        flash('Fehler beim Versenden der E-Mail.', 'danger')
    
    return redirect(url_for('admin.donation_detail', donation_id=donation_id))

@admin_required
def view_tax_receipt(donation_id):
    """View/Download tax receipt PDF"""
    donation = Donation.query.get_or_404(donation_id)

    # Get the latest tax receipt for this donation
    tax_receipt = Certificate.query.filter_by(
        donation_id=donation_id,
        certificate_type='tax_receipt'
    ).order_by(Certificate.generated_at.desc()).first()
    if not tax_receipt or not tax_receipt.exists_on_disk:
        flash('Keine Spendenbescheinigung vorhanden. Bitte zuerst generieren.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    # Send the PDF file to the browser for viewing
    return send_file(
        tax_receipt.file_path,
        as_attachment=False,  # Display in browser instead of download
        download_name=tax_receipt.filename,
        mimetype='application/pdf'
    )


@admin_required
def view_storno(donation_id):
    """View/Download storno certificate PDF"""
    donation = Donation.query.get_or_404(donation_id)

    storno_cert = Certificate.query.filter_by(
        donation_id=donation_id,
        certificate_type='storno'
    ).order_by(Certificate.generated_at.desc()).first()

    if not storno_cert or not storno_cert.exists_on_disk:
        flash('Keine Storno-Bescheinigung vorhanden.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    return send_file(
        storno_cert.file_path,
        as_attachment=False,
        download_name=storno_cert.filename,
        mimetype='application/pdf'
    )


@admin_required
def regenerate_storno(donation_id):
    """Regenerate storno certificate for donation"""
    donation = Donation.query.get_or_404(donation_id)

    if donation.payment_status not in ('failed', 'disputed', 'refunded'):
        flash('Storno-Bescheinigung nur fuer fehlgeschlagene, angefochtene oder rueckerstattete Spenden moeglich.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    # Reset storno_generated flag to allow regeneration
    donation.storno_generated = False
    db.session.commit()

    pdf_service = PDFGeneratorService()
    try:
        storno_path = pdf_service.generate_storno_certificate(donation.id)
        if storno_path:
            flash('Storno-Bescheinigung wurde neu generiert.', 'success')
        else:
            flash('Fehler beim Generieren der Storno-Bescheinigung.', 'danger')
    except Exception as e:
        flash(f'Fehler: {str(e)}', 'danger')

    return redirect(url_for('admin.donation_detail', donation_id=donation_id))


@admin_required
def resend_storno(donation_id):
    """Resend storno certificate email"""
    donation = Donation.query.get_or_404(donation_id)

    storno_cert = Certificate.query.filter_by(
        donation_id=donation_id,
        certificate_type='storno'
    ).order_by(Certificate.generated_at.desc()).first()

    if not storno_cert or not storno_cert.exists_on_disk:
        flash('Keine Storno-Bescheinigung vorhanden. Bitte zuerst generieren.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    # Prepare storno context for email
    pdf_service = PDFGeneratorService()
    storno_context = pdf_service._prepare_storno_context(donation)

    # Prepare donation data dict (same pattern as resend_certificate)
    donation_data = {
        'id': donation.id,
        'created_at': donation.created_at,
        'total_amount': float(donation.total_amount),
        'person': {
            'email': donation.person.email,
            'full_name': donation.person.full_name,
            'first_name': donation.person.first_name,
            'last_name': donation.person.last_name
        },
        'verses': [{'reference': v.verse.reference, 'text': v.verse.text}
                  for v in donation.verse_associations]
    }

    success = email_service.send_storno_email(
        donation_data,
        storno_cert.file_path,
        storno_context
    )

    if success:
        donation.storno_sent_at = datetime.utcnow()
        db.session.commit()
        flash('Storno-Bescheinigung wurde per E-Mail versendet.', 'success')
    else:
        flash('Fehler beim Versenden der E-Mail.', 'danger')

    return redirect(url_for('admin.donation_detail', donation_id=donation_id))


# ==========================================
# DATABASE CLEANUP MANAGEMENT
# ==========================================

@admin_required
def get_cleanup_stats():
    """API endpoint to get cleanup statistics for dashboard display.

    Returns JSON with counts of:
    - Expired reservations (ready to clean)
    - Orphaned pending donations (older than 24h)
    - Active reservations (not expired)
    - Recent cleanup results (if available)
    """
    try:
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)

        stats = {
            'expired_reservations': VerseReservation.query.filter(
                VerseReservation.expires_at < datetime.utcnow()
            ).count(),
            'orphaned_pending_donations': Donation.query.filter(
                Donation.payment_status == 'pending',
                Donation.created_at < cutoff_24h
            ).count(),
            'active_reservations': VerseReservation.query.filter(
                VerseReservation.expires_at > datetime.utcnow()
            ).count(),
            'pending_donations_total': Donation.query.filter(
                Donation.payment_status == 'pending'
            ).count(),
            'timestamp': datetime.utcnow().isoformat()
        }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_required
def cleanup_orphaned():
    """Manual cleanup of orphaned pending donations and expired reservations.

    This endpoint performs:
    1. Cleanup of expired verse reservations
    2. Cleanup of orphaned pending donations (older than 24h)

    Returns redirect to admin index with flash messages showing results.
    """
    try:
        # Step 1: Cleanup expired reservations
        expired_res = VerseReservation.cleanup_expired()

        # Step 2: Cleanup orphaned pending donations
        orphaned_don = Donation.cleanup_orphaned_pending(max_age_hours=24)

        # Build result message
        if expired_res > 0 or orphaned_don > 0:
            flash(
                f'Cleanup erfolgreich: {expired_res} abgelaufene Reservierungen, '
                f'{orphaned_don} verwaiste Pending-Donations gelöscht.',
                'success'
            )
        else:
            flash('Keine Daten zum Bereinigen gefunden.', 'info')

        return redirect(url_for('admin.index'))

    except Exception as e:
        flash(f'Cleanup fehlgeschlagen: {str(e)}', 'danger')
        return redirect(url_for('admin.index'))


# ==========================================
# BOOK PRIORITIZATION MANAGEMENT
# ==========================================

@admin_required
def book_priorities():
    """
    Admin page for managing book prioritization boosts.

    GET: Display current boosts and form
    POST: Apply or remove boost
    """

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'apply_boost':
            # Get form data
            book_code = request.form.get('book_code')
            boost_value = request.form.get('boost_value', type=int)
            reason = request.form.get('reason')
            admin_email = session.get('admin_email')

            # Validate
            if not book_code:
                flash('Bitte ein Buch auswählen', 'error')
                return redirect(url_for('admin.book_priorities'))

            if boost_value is None or boost_value < -25 or boost_value > 25:
                flash('Boost-Wert muss zwischen -25 und +25 liegen', 'error')
                return redirect(url_for('admin.book_priorities'))

            # Apply boost
            try:
                BookPriority.apply_boost(book_code, boost_value, reason, admin_email)
                flash(f'Boost für {book_code} auf {boost_value:+d} gesetzt', 'success')
            except ValueError as e:
                flash(f'Fehler: {str(e)}', 'error')
            except Exception as e:
                flash(f'Unerwarteter Fehler: {str(e)}', 'error')

        elif action == 'remove_boost':
            book_code = request.form.get('book_code')

            try:
                BookPriority.remove_boost(book_code)
                flash(f'Boost für {book_code} entfernt', 'success')
            except Exception as e:
                flash(f'Fehler beim Entfernen: {str(e)}', 'error')

        return redirect(url_for('admin.book_priorities'))

    # GET: Display page
    try:
        # Get active boosts
        active_boosts = BookPriority.get_active_boosts()

        # Get statistics
        boost_stats = BookPriority.get_boost_statistics()

        # Get all available books
        all_books = db.session.query(Verse.book.distinct()).order_by(Verse.book).all()
        all_books = [book[0] for book in all_books]

        return render_template(
            'admin/book_priorities.html',
            active_boosts=active_boosts,
            boost_stats=boost_stats,
            all_books=all_books
        )

    except Exception as e:
        flash(f'Fehler beim Laden der Seite: {str(e)}', 'error')
        return redirect(url_for('admin.index'))


# --- Campaign URL Management ---

CAMPAIGN_PRESETS = {
    'instagram': {'name': 'Instagram Post', 'utm_source': 'instagram', 'utm_medium': 'social', 'target_url': 'vers-patenschaft.de'},
    'facebook': {'name': 'Facebook Post', 'utm_source': 'facebook', 'utm_medium': 'social', 'target_url': 'vers-patenschaft.de'},
    'newsletter': {'name': 'Newsletter', 'utm_source': 'newsletter', 'utm_medium': 'email', 'target_url': 'vers-patenschaft.de'},
}


def _get_reserved_slugs():
    """Get all registered Flask route prefixes as reserved slugs."""
    from flask import current_app
    reserved = set()
    for rule in current_app.url_map.iter_rules():
        parts = rule.rule.strip('/').split('/')
        if parts and parts[0]:
            reserved.add(parts[0])
    return reserved


def _sanitize_utm_value(value):
    """Sanitize a UTM parameter value: lowercase, underscores, no special chars."""
    if not value:
        return value
    value = value.strip().lower()
    value = value.replace(' ', '_')
    # Replace umlauts
    for old, new in [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')]:
        value = value.replace(old, new)
    # Only allow alphanumeric + underscores
    import re
    value = re.sub(r'[^a-z0-9_]', '', value)
    return value


def _sanitize_slug(value):
    """Sanitize a slug value: lowercase, hyphens, no special chars."""
    if not value:
        return value
    value = value.strip().lower()
    import re
    value = re.sub(r'[^a-z0-9-]', '', value)
    return value[:60]


def _validate_target_url(url):
    """Validate target_url is a safe HTTP(S) URL. Returns error message or None."""
    if not url:
        return None
    # Strip protocol for check
    lower = url.lower().strip()
    if lower.startswith('javascript:') or lower.startswith('data:'):
        return 'Ungültiges URL-Schema. Nur HTTP/HTTPS-URLs sind erlaubt.'
    # Must look like a domain (contains at least one dot)
    domain = lower.replace('https://', '').replace('http://', '').split('/')[0]
    if '.' not in domain:
        return 'Die Zielseite muss eine gültige Domain enthalten (z.B. vers-patenschaft.de).'
    return None


@admin_required
def campaign_urls_list():
    """List all campaign URLs with search and filter."""
    search = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', 'active')
    page = request.args.get('page', 1, type=int)

    query = CampaignUrl.query

    # Search
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                CampaignUrl.name.ilike(search_filter),
                CampaignUrl.utm_source.ilike(search_filter),
                CampaignUrl.utm_campaign.ilike(search_filter),
                CampaignUrl.slug.ilike(search_filter),
            )
        )

    # Filter
    if filter_type == 'online':
        query = query.filter_by(url_type='online')
    elif filter_type == 'offline':
        query = query.filter_by(url_type='offline')
    elif filter_type == 'active':
        query = query.filter_by(is_active=True)
    elif filter_type == 'archived':
        query = query.filter_by(is_active=False)

    campaigns = query.order_by(CampaignUrl.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )

    return render_template(
        'admin/campaign_urls.html',
        campaigns=campaigns,
        search=search,
        filter_type=filter_type,
        presets=CAMPAIGN_PRESETS,
    )


@admin_required
def campaign_url_create():
    """Create a new campaign URL."""
    if request.method == 'POST':
        # Sanitize inputs
        name = request.form.get('name', '').strip()
        url_type = request.form.get('url_type', 'online')
        slug = _sanitize_slug(request.form.get('slug', ''))
        target_url = request.form.get('target_url', 'vers-patenschaft.de').strip()
        utm_source = _sanitize_utm_value(request.form.get('utm_source', ''))
        utm_medium = request.form.get('utm_medium', '')
        utm_campaign = _sanitize_utm_value(request.form.get('utm_campaign', ''))
        utm_content = _sanitize_utm_value(request.form.get('utm_content', ''))
        utm_term = _sanitize_utm_value(request.form.get('utm_term', ''))
        notes = request.form.get('notes', '').strip()

        # Validation
        errors = []
        if not name:
            errors.append('Bezeichnung ist ein Pflichtfeld.')
        if not utm_source:
            errors.append('Quelle ist ein Pflichtfeld.')
        if not utm_medium:
            errors.append('Kanal-Typ ist ein Pflichtfeld.')
        if utm_medium and utm_medium not in dict(CampaignUrl.MEDIUM_CHOICES):
            errors.append('Ungültiger Kanal-Typ.')

        url_error = _validate_target_url(target_url)
        if url_error:
            errors.append(url_error)

        if url_type == 'offline':
            if not slug:
                errors.append('Kurzlink ist bei Offline-Links ein Pflichtfeld.')
            elif not CampaignUrl.is_slug_available(slug):
                errors.append('Dieser Kurzlink ist bereits vergeben.')
            elif slug in _get_reserved_slugs():
                errors.append(f'Der Kurzlink "{slug}" ist reserviert und kann nicht verwendet werden.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'admin/campaign_url_form.html',
                campaign=None,
                existing_sources=CampaignUrl.get_existing_sources(),
                medium_choices=CampaignUrl.MEDIUM_CHOICES,
                form_data=request.form,
            )

        campaign = CampaignUrl(
            name=name,
            url_type=url_type,
            slug=slug if url_type == 'offline' else None,
            target_url=target_url or 'vers-patenschaft.de',
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign or None,
            utm_content=utm_content or None,
            utm_term=utm_term or None,
            notes=notes or None,
            created_by=session.get('admin_email'),
        )
        db.session.add(campaign)
        db.session.commit()

        flash(f'Kampagnen-URL "{name}" wurde erstellt.', 'success')
        return redirect(url_for('admin.campaign_url_edit', campaign_id=campaign.id))

    # GET: Show form
    preset = request.args.get('preset')
    duplicate_id = request.args.get('duplicate', type=int)

    form_data = {}
    if preset and preset in CAMPAIGN_PRESETS:
        form_data = CAMPAIGN_PRESETS[preset]
    elif duplicate_id:
        source = db.session.get(CampaignUrl, duplicate_id)
        if source:
            form_data = {
                'name': f'{source.name} (Kopie)',
                'url_type': source.url_type,
                'target_url': source.target_url,
                'utm_source': source.utm_source,
                'utm_medium': source.utm_medium,
                'utm_campaign': source.utm_campaign or '',
                'utm_content': source.utm_content or '',
                'utm_term': source.utm_term or '',
                'notes': source.notes or '',
            }

    return render_template(
        'admin/campaign_url_form.html',
        campaign=None,
        existing_sources=CampaignUrl.get_existing_sources(),
        medium_choices=CampaignUrl.MEDIUM_CHOICES,
        form_data=form_data,
    )


@admin_required
def campaign_url_edit(campaign_id):
    """Edit an existing campaign URL."""
    campaign = CampaignUrl.query.get_or_404(campaign_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        url_type = request.form.get('url_type', 'online')
        slug = _sanitize_slug(request.form.get('slug', ''))
        target_url = request.form.get('target_url', 'vers-patenschaft.de').strip()
        utm_source = _sanitize_utm_value(request.form.get('utm_source', ''))
        utm_medium = request.form.get('utm_medium', '')
        utm_campaign = _sanitize_utm_value(request.form.get('utm_campaign', ''))
        utm_content = _sanitize_utm_value(request.form.get('utm_content', ''))
        utm_term = _sanitize_utm_value(request.form.get('utm_term', ''))
        notes = request.form.get('notes', '').strip()
        is_active = 'is_active' in request.form

        errors = []
        if not name:
            errors.append('Bezeichnung ist ein Pflichtfeld.')
        if not utm_source:
            errors.append('Quelle ist ein Pflichtfeld.')
        if not utm_medium:
            errors.append('Kanal-Typ ist ein Pflichtfeld.')
        if utm_medium and utm_medium not in dict(CampaignUrl.MEDIUM_CHOICES):
            errors.append('Ungültiger Kanal-Typ.')

        url_error = _validate_target_url(target_url)
        if url_error:
            errors.append(url_error)

        if url_type == 'offline':
            if not slug:
                errors.append('Kurzlink ist bei Offline-Links ein Pflichtfeld.')
            elif not CampaignUrl.is_slug_available(slug, exclude_id=campaign.id):
                errors.append('Dieser Kurzlink ist bereits vergeben.')
            elif slug in _get_reserved_slugs():
                errors.append(f'Der Kurzlink "{slug}" ist reserviert.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'admin/campaign_url_form.html',
                campaign=campaign,
                existing_sources=CampaignUrl.get_existing_sources(),
                medium_choices=CampaignUrl.MEDIUM_CHOICES,
                form_data=request.form,
            )

        campaign.name = name
        campaign.url_type = url_type
        campaign.slug = slug if url_type == 'offline' else None
        campaign.target_url = target_url or 'vers-patenschaft.de'
        campaign.utm_source = utm_source
        campaign.utm_medium = utm_medium
        campaign.utm_campaign = utm_campaign or None
        campaign.utm_content = utm_content or None
        campaign.utm_term = utm_term or None
        campaign.notes = notes or None
        campaign.is_active = is_active

        db.session.commit()
        flash(f'Kampagnen-URL "{name}" wurde gespeichert.', 'success')
        return redirect(url_for('admin.campaign_url_edit', campaign_id=campaign.id))

    return render_template(
        'admin/campaign_url_form.html',
        campaign=campaign,
        existing_sources=CampaignUrl.get_existing_sources(),
        medium_choices=CampaignUrl.MEDIUM_CHOICES,
        form_data=None,
    )


@admin_required
def campaign_url_delete(campaign_id):
    """Delete a campaign URL permanently."""
    campaign = CampaignUrl.query.get_or_404(campaign_id)
    name = campaign.name
    db.session.delete(campaign)
    db.session.commit()
    flash(f'Kampagnen-URL "{name}" wurde gelöscht.', 'success')
    return redirect(url_for('admin.campaign_urls_list'))


@admin_required
def campaign_url_toggle(campaign_id):
    """Toggle active/archived status."""
    campaign = CampaignUrl.query.get_or_404(campaign_id)
    campaign.is_active = not campaign.is_active
    db.session.commit()
    status = 'aktiviert' if campaign.is_active else 'archiviert'
    flash(f'Kampagnen-URL "{campaign.name}" wurde {status}.', 'success')
    return redirect(url_for('admin.campaign_urls_list'))


@admin_required
def campaign_url_qr_png(campaign_id):
    """Generate QR code as PNG."""
    campaign = CampaignUrl.query.get_or_404(campaign_id)
    if campaign.url_type != 'offline' or not campaign.slug:
        flash('QR-Codes sind nur für Offline-Links verfügbar.', 'error')
        return redirect(url_for('admin.campaign_urls_list'))

    import qrcode
    from io import BytesIO

    size = request.args.get('size', 300, type=int)
    size = min(size, 2000)  # Cap at 2000px

    qr = qrcode.QRCode(version=1, box_size=max(1, size // 30), border=4)
    qr.add_data(campaign.short_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    download = request.args.get('download', False, type=bool)
    return send_file(
        buffer,
        mimetype='image/png',
        as_attachment=download,
        download_name=f'qr-{campaign.slug}.png',
    )


@admin_required
def campaign_url_qr_svg(campaign_id):
    """Generate QR code as SVG."""
    campaign = CampaignUrl.query.get_or_404(campaign_id)
    if campaign.url_type != 'offline' or not campaign.slug:
        flash('QR-Codes sind nur für Offline-Links verfügbar.', 'error')
        return redirect(url_for('admin.campaign_urls_list'))

    import qrcode
    import qrcode.image.svg
    from io import BytesIO

    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(version=1, box_size=10, border=4, image_factory=factory)
    qr.add_data(campaign.short_url)
    qr.make(fit=True)
    img = qr.make_image()

    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='image/svg+xml',
        as_attachment=True,
        download_name=f'qr-{campaign.slug}.svg',
    )


@admin_required
def check_slug(slug):
    """AJAX endpoint: check if a slug is available."""
    slug = _sanitize_slug(slug)
    exclude_id = request.args.get('exclude', type=int)

    if not slug:
        return jsonify({'available': False, 'reason': 'Kurzlink darf nicht leer sein.'})

    if slug in _get_reserved_slugs():
        return jsonify({'available': False, 'reason': f'"{slug}" ist ein reservierter Pfad.'})

    if CampaignUrl.is_slug_available(slug, exclude_id=exclude_id):
        return jsonify({'available': True})

    existing = CampaignUrl.query.filter_by(slug=slug).first()
    return jsonify({
        'available': False,
        'reason': f'Bereits vergeben durch: {existing.name}' if existing else 'Bereits vergeben.',
    })