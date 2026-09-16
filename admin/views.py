from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, session
from admin.decorators import admin_required
from models import db, Person, Verse, Donation, VerseReservation, Certificate, BookPriority, CampaignUrl, SpeakerRequest, CardCampaign, CardRequest
from sqlalchemy import or_, func
from pdf_service import PDFGeneratorService
from email_service import email_service
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
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
        # Nur was tatsächlich angeboten wird. Verse erschienener Buecher sind
        # zwar nicht gesponsert, aber auch nicht mehr verfuegbar.
        query = query.filter_by(is_sponsored=False, is_translated=False)
    elif filter_type == 'translated':
        query = query.filter_by(is_translated=True)
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

    bulk_mail = None
    if donation.is_bulk_sponsoring:
        import bulk_sponsoring_service as _bulk
        subject, text = _bulk.mailvorschlag(donation)
        bulk_mail = {'subject': subject, 'text': text, 'cc': _bulk_cc_default()}

    return render_template('admin/donation_detail.html',
                           bulk_mail=bulk_mail,
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
        tax_receipt = pdf_service.generate_tax_receipt_atomic(donation.id, force=True)
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
                errors.append('Der Kurzlink-Name ist beim Typ Kurzlink ein Pflichtfeld.')
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
                errors.append('Der Kurzlink-Name ist beim Typ Kurzlink ein Pflichtfeld.')
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
        flash('QR-Codes sind nur für Kurzlinks verfügbar.', 'error')
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
        flash('QR-Codes sind nur für Kurzlinks verfügbar.', 'error')
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

# ==========================================
# Referenten-Anfragen (Formular /vortrag)
# ==========================================

@admin_required
def speaker_requests_list():
    """Referenten-Anfragen auflisten, nach Status filtern und durchsuchen."""
    status_filter = request.args.get('status', 'offen')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)

    query = SpeakerRequest.query
    if status_filter == 'offen':
        query = query.filter(SpeakerRequest.status.in_(['neu', 'kontakt', 'termin']))
    elif status_filter != 'alle':
        query = query.filter_by(status=status_filter)

    if search:
        like = f'%{search}%'
        query = query.filter(or_(
            SpeakerRequest.organization.ilike(like),
            SpeakerRequest.contact_name.ilike(like),
            SpeakerRequest.email.ilike(like),
            SpeakerRequest.city.ilike(like),
        ))

    requests_page = query.order_by(SpeakerRequest.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    return render_template(
        'admin/speaker_requests.html',
        requests=requests_page,
        status_filter=status_filter,
        search=search,
        status_choices=SpeakerRequest.STATUS_CHOICES,
    )


@admin_required
def speaker_request_detail(request_id):
    """Eine Anfrage anzeigen, Status und interne Notizen ändern."""
    req = SpeakerRequest.query.get_or_404(request_id)

    if request.method == 'POST':
        new_status = request.form.get('status', '').strip()
        if new_status not in dict(SpeakerRequest.STATUS_CHOICES):
            flash('Ungültiger Status.', 'error')
            return redirect(url_for('admin.speaker_request_detail', request_id=req.id))
        req.status = new_status
        req.admin_notes = request.form.get('admin_notes', '').strip() or None
        req.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Anfrage gespeichert.', 'success')
        return redirect(url_for('admin.speaker_request_detail', request_id=req.id))

    return render_template(
        'admin/speaker_request_detail.html',
        req=req,
        status_choices=SpeakerRequest.STATUS_CHOICES,
    )


@admin_required
def speaker_request_delete(request_id):
    """Anfrage endgültig löschen (z. B. nach Abschluss oder auf Wunsch des Absenders)."""
    req = SpeakerRequest.query.get_or_404(request_id)
    label = f'{req.organization}, {req.city}'
    db.session.delete(req)
    db.session.commit()
    flash(f'Anfrage „{label}" gelöscht.', 'success')
    return redirect(url_for('admin.speaker_requests_list'))


# ==========================================
# Weihnachtskarten-Aktion (Formular /weihnachtskarten, eigene Datenbank)
# ==========================================

BERLIN = ZoneInfo('Europe/Berlin')


def _card_db_available():
    from flask import current_app
    return bool(current_app.config.get('KARTEN_DB_AVAILABLE'))


def _csv_cell(value):
    """CSV-Zelle für LibreOffice: Formel-Injection entschärfen (=, +, -, @, Tab, CR am Anfang)."""
    if value is None:
        return ''
    s = str(value)
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        s = "'" + s
    return s


def _csv_response(rows, filename):
    """Komma-getrennt (RFC 4180), alle Felder in Anführungszeichen, UTF-8-BOM für LibreOffice/Excel."""
    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=',', quoting=csv.QUOTE_ALL, lineterminator='\r\n')
    for row in rows:
        writer.writerow([_csv_cell(v) for v in row])
    data = '\ufeff' + buf.getvalue()
    from flask import Response
    return Response(
        data.encode('utf-8'),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


def _utc_to_berlin_input(dt):
    if not dt:
        return ''
    return dt.replace(tzinfo=timezone.utc).astimezone(BERLIN).strftime('%Y-%m-%dT%H:%M')


def _berlin_input_to_utc(value):
    """'2026-11-27T23:59' (Berlin) → naives UTC-datetime; leer → None; ungültig → ValueError."""
    value = (value or '').strip()
    if not value:
        return None
    local = datetime.strptime(value, '%Y-%m-%dT%H:%M').replace(tzinfo=BERLIN)
    return local.astimezone(timezone.utc).replace(tzinfo=None)


@admin_required
def card_requests_list():
    """Übersicht: Einstellungen, Zähler, Liste der Bestellungen, Export und Löschen."""
    if not _card_db_available():
        flash('KARTEN_DATABASE_URI ist nicht gesetzt. Die Karten-Datenbank ist nicht angebunden.', 'error')
        return render_template('admin/card_requests.html', campaign=None, requests=[], stats={})
    campaign = CardCampaign.get()
    requests_all = CardRequest.query.order_by(CardRequest.created_at.desc()).all()
    stats = {
        'count': len(requests_all),
        'newsletter': sum(1 for r in requests_all if r.newsletter),
        'with_email': sum(1 for r in requests_all if r.email),
        'possible_duplicates': sum(1 for r in requests_all if r.possible_duplicate_of),
        'by_country': {code: sum(1 for r in requests_all if r.country == code) for code, _ in CardRequest.COUNTRIES},
    }
    return render_template(
        'admin/card_requests.html',
        campaign=campaign,
        requests=requests_all,
        stats=stats,
        closes_at_input=_utc_to_berlin_input(campaign.closes_at) if campaign else '',
        default_sender=DEFAULT_LABEL_SENDER,
        countries=dict(CardRequest.COUNTRIES),
    )


@admin_required
def card_campaign_settings():
    """Öffnen/Schließen, Obergrenze und automatisches Ende speichern."""
    campaign = CardCampaign.get()
    if campaign is None:
        flash('Einstellungszeile fehlt in der Karten-Datenbank (Migration ausführen).', 'error')
        return redirect(url_for('admin.card_requests_list'))
    try:
        max_households = int(request.form.get('max_households', '').strip())
        if not 1 <= max_households <= 10000:
            raise ValueError
    except ValueError:
        flash('Die Obergrenze muss eine Zahl zwischen 1 und 10000 sein.', 'error')
        return redirect(url_for('admin.card_requests_list'))
    try:
        closes_at = _berlin_input_to_utc(request.form.get('closes_at'))
    except ValueError:
        flash('Das Enddatum ist ungültig.', 'error')
        return redirect(url_for('admin.card_requests_list'))

    campaign.is_open = bool(request.form.get('is_open'))
    campaign.max_households = max_households
    campaign.closes_at = closes_at
    db.session.commit()
    flash('Einstellungen gespeichert. Formular ist jetzt ' + ('geöffnet' if campaign.is_accepting() else 'geschlossen') + '.', 'success')
    return redirect(url_for('admin.card_requests_list'))


@admin_required
def card_request_delete(request_id):
    """Einzelnen Eintrag löschen (Müll, Doppelmeldung, Bitte des Absenders). Der Platz wird wieder frei."""
    req = CardRequest.query.get_or_404(request_id)
    label = f'{req.name}, {req.postal_code} {req.city}'
    db.session.delete(req)
    db.session.commit()
    flash(f'Eintrag „{label}" gelöscht.', 'success')
    return redirect(url_for('admin.card_requests_list'))


@admin_required
def card_requests_export():
    """CSV für den LibreOffice-Serienbrief (Adressetiketten)."""
    rows = [['Nr', 'Name', 'Adresszusatz', 'Strasse', 'PLZ', 'Ort', 'Landzeile', 'Land', 'E-Mail', 'Newsletter', 'Eingang']]
    for i, r in enumerate(CardRequest.query.order_by(CardRequest.created_at.asc()).all(), start=1):
        rows.append([
            i, r.name, r.address_extra or '', r.street, r.postal_code, r.city, r.country_line, r.country,
            r.email or '', 'ja' if r.newsletter else 'nein',
            r.created_at.replace(tzinfo=timezone.utc).astimezone(BERLIN).strftime('%d.%m.%Y %H:%M'),
        ])
    return _csv_response(rows, f'weihnachtskarten-adressen-{datetime.now(BERLIN).strftime("%Y%m%d")}.csv')


DEFAULT_LABEL_SENDER = '@ngue2029 · U. Probst · Sudetenlandstr. 18 · D-35415 Pohlheim'


def build_label_pdf(entries, skip=0, sender=DEFAULT_LABEL_SENDER):
    """Adressetiketten als PDF für Avery Zweckform 3475 (70 x 36 mm, 3 x 8 = 24 je A4).

    Bogen: kein Seitenrand links/rechts, 4,5 mm oben und unten, keine Stege.
    `skip` lässt auf dem ersten Bogen so viele Etiketten frei (angebrochener Bogen).
    `sender`: Absenderzeile oben im Etikett, klein und unterstrichen; ein führendes
    „@handle" wird fett gesetzt. Zu lange Absender werden an „ · " umbrochen (max. 2 Zeilen).
    Gibt die PDF-Bytes zurück.
    """
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas

    label_w, label_h = 70 * mm, 36 * mm
    cols, rows = 3, 8
    margin_left, margin_top = 0 * mm, 4.5 * mm
    pad_x, pad_y = 5 * mm, 3 * mm
    font, bold = 'Helvetica', 'Helvetica-Bold'
    size, leading = 10.5, 12.5
    s_size, s_leading, s_gap = 7, 8.5, 2 * mm
    max_text_w = label_w - 2 * pad_x
    page_w, page_h = A4

    def fit(text, fnt=font, sz=size):
        """Text auf die Etikettenbreite kürzen (Ellipse), damit nichts über den Rand läuft."""
        if stringWidth(text, fnt, sz) <= max_text_w:
            return text
        while text and stringWidth(text + '…', fnt, sz) > max_text_w:
            text = text[:-1]
        return text.rstrip() + '…'

    def sender_segments(text):
        """[(text, font)] für eine Absenderzeile: führendes @handle fett."""
        if text.startswith('@') and ' ' in text:
            handle, rest = text.split(' ', 1)
            return [(handle, bold), (' ' + rest, font)]
        return [(text, font)]

    def seg_width(segs):
        return sum(stringWidth(t, f, s_size) for t, f in segs)

    # Absender: eine Zeile, wenn er passt; sonst an „ · " so in zwei Zeilen teilen,
    # dass die längere Zeile möglichst kurz wird (ausgewogener Umbruch)
    sender_lines = []
    sender = (sender or '').strip()
    if sender:
        parts = sender.split(' · ')
        if seg_width(sender_segments(sender)) <= max_text_w or len(parts) == 1:
            sender_lines = [sender]
        else:
            best = None
            for i in range(1, len(parts)):
                a, b = ' · '.join(parts[:i]), ' · '.join(parts[i:])
                widest = max(seg_width(sender_segments(a)), seg_width(sender_segments(b)))
                if best is None or widest < best[0]:
                    best = (widest, [a, b])
            sender_lines = best[1]
    sender_h = len(sender_lines) * s_leading + (s_gap if sender_lines else 0)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle('Weihnachtskarten Adressetiketten')
    per_page = cols * rows
    slot = max(0, skip)
    for entry in entries:
        page_index, pos = divmod(slot, per_page)
        if pos == 0 and slot > 0:
            c.showPage()
        col, row = pos % cols, pos // cols
        x = margin_left + col * label_w + pad_x
        y_top = page_h - margin_top - row * label_h - pad_y

        # Absender oben, eine Linie unter dem ganzen Block (so breit wie die längste Zeile)
        y = y_top - s_size
        widest = 0
        for sl in sender_lines:
            segs = sender_segments(fit(sl, font, s_size))
            cx = x
            for t, f in segs:
                c.setFont(f, s_size)
                c.drawString(cx, y, t)
                cx += stringWidth(t, f, s_size)
            widest = max(widest, cx - x)
            y -= s_leading
        if sender_lines:
            c.setLineWidth(0.4)
            c.line(x, y + s_leading - 2, x + widest, y + s_leading - 2)

        lines = [entry.name]
        if entry.address_extra:
            lines.append(entry.address_extra)
        lines.append(entry.street)
        lines.append(f'{entry.postal_code} {entry.city}')
        if entry.country_line:
            lines.append(entry.country_line.upper())
        # Adressblock vertikal mittig im Rest unter dem Absender
        area_top = y_top - sender_h
        area_h = label_h - 2 * pad_y - sender_h
        block_h = leading * len(lines)
        y = area_top - max(0, (area_h - block_h) / 2) - size
        c.setFont(font, size)
        for line in lines:
            c.drawString(x, y, fit(line))
            y -= leading
        slot += 1
    c.showPage()
    c.save()
    return buf.getvalue()


@admin_required
def card_requests_labels_pdf():
    """Etiketten-PDF (Avery 3475) aller aktiven Bestellungen.

    ?skip=N lässt N Etiketten auf dem ersten Bogen frei, ?sender=… setzt die Absenderzeile (leer = keine).
    """
    from flask import Response
    try:
        skip = max(0, min(23, int(request.args.get('skip', 0))))
    except ValueError:
        skip = 0
    sender = (request.args.get('sender') or '').strip()[:200]
    entries = CardRequest.query.order_by(CardRequest.created_at.asc()).all()
    pdf = build_label_pdf(entries, skip=skip, sender=sender)
    return Response(pdf, mimetype='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="weihnachtskarten-etiketten-{datetime.now(BERLIN).strftime("%Y%m%d")}.pdf"',
    })


@admin_required
def card_requests_export_newsletter():
    """CSV nur mit den Newsletter-Einwilligungen (Name, E-Mail) für den Import in Brevo."""
    rows = [['Name', 'E-Mail', 'Land', 'Einwilligung am']]
    for r in CardRequest.query.filter_by(newsletter=True).order_by(CardRequest.created_at.asc()).all():
        if r.email:
            rows.append([r.name, r.email, r.country,
                         r.created_at.replace(tzinfo=timezone.utc).astimezone(BERLIN).strftime('%d.%m.%Y %H:%M')])
    return _csv_response(rows, f'weihnachtskarten-newsletter-{datetime.now(BERLIN).strftime("%Y%m%d")}.csv')


@admin_required
def card_requests_delete_all():
    """Nach dem Versand alle Adressen löschen. Die Zahlen bleiben für die Auswertung in card_campaign."""
    if request.form.get('confirm') != 'LOESCHEN':
        flash('Zum Löschen aller Adressen bitte LOESCHEN in das Bestätigungsfeld schreiben.', 'error')
        return redirect(url_for('admin.card_requests_list'))
    campaign = CardCampaign.get(for_update=True)
    count = CardRequest.query.count()
    newsletter = CardRequest.query.filter_by(newsletter=True).count()
    CardRequest.query.delete()
    campaign.deleted_count += count
    campaign.deleted_newsletter_count += newsletter
    campaign.deleted_at = datetime.utcnow()
    campaign.is_open = False
    db.session.commit()
    flash(f'{count} Adressen gelöscht ({newsletter} mit Newsletter-Einwilligung). Formular geschlossen.', 'success')
    return redirect(url_for('admin.card_requests_list'))


# ---------------------------------------------------------------------------
# Bulk-Sponsoring: Kapitel-/Buch-Patenschaften zum Sonderpreis
# ---------------------------------------------------------------------------
# Fachlogik in bulk_sponsoring_service.py (gemeinsam mit dem CLI bulk_sponsoring.py).
# Ablauf: Formular -> Vorschau (nichts geschrieben) -> "Eintragen" mit Einmal-Token
# -> Spende + PDFs -> Detailseite mit Sende-Knopf für die persönliche Mail.

import secrets
from decimal import Decimal
from flask import current_app
import bulk_sponsoring_service as bulk

BULK_FORM_FIELDS = (
    'email', 'salutation', 'first_name', 'last_name', 'street', 'house_number',
    'postal_code', 'city', 'country', 'newsletter_consent', 'versangaben_text',
    'gesamtbetrag', 'zuwendungsdatum', 'ausstellungsdatum', 'zahlungsweg', 'notiz',
)


# Standard-CC für die persönliche Mail: Daniel Weninger (Stiftung) und das
# Postfach info@vers-patenschaft.de. Über BULK_MAIL_CC in der .env änderbar,
# im Formular vor dem Senden editierbar.
BULK_MAIL_CC_DEFAULT = 'daniel.weninger@schoeffer.org, info@vers-patenschaft.de'


def _bulk_cc_liste(text):
    return [a.strip().lower() for a in (text or '').replace(';', ',').split(',') if a.strip()]


def _bulk_cc_default():
    return os.getenv('BULK_MAIL_CC', BULK_MAIL_CC_DEFAULT)


def _bulk_form_data():
    """Rohwerte aus dem Formular, wie eingegeben (für das Wieder-Befüllen)."""
    fd = {f: request.form.get(f, '').strip() for f in BULK_FORM_FIELDS}
    fd['newsletter_consent'] = request.form.get('newsletter_consent') == 'on'
    return fd


def _bulk_validate(fd):
    """Formularwerte -> (daten-dict für den Service, angaben-Liste, Fehlerliste)."""
    errors = []
    daten = {
        'email': fd['email'].lower(),
        'salutation': fd['salutation'] or None,
        'first_name': fd['first_name'],
        'last_name': fd['last_name'],
        'street': fd['street'],
        'house_number': fd['house_number'],
        'postal_code': fd['postal_code'],
        'city': fd['city'],
        'country': (fd['country'] or 'DE').upper(),
        'newsletter_consent': bool(fd['newsletter_consent']),
        'zahlungsweg': fd['zahlungsweg'] or 'Überweisung',
        'notiz': fd['notiz'] or None,
    }
    import re as _re
    if not _re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", daten['email']):
        errors.append('Bitte eine gültige E-Mail-Adresse angeben.')
    if daten['salutation'] and daten['salutation'] not in bulk.ANREDEN:
        errors.append('Ungültige Anrede.')
    for feld, name in (('first_name', 'Vorname'), ('last_name', 'Nachname'), ('street', 'Straße'),
                       ('house_number', 'Hausnummer'), ('postal_code', 'PLZ'), ('city', 'Ort')):
        if not daten[feld]:
            errors.append(f'{name} ist ein Pflichtfeld.')
    if not _re.fullmatch(r"\d{4,5}", daten['postal_code'] or ''):
        errors.append('PLZ muss aus 4 oder 5 Ziffern bestehen.')
    if daten['country'] not in bulk.LAENDER:
        errors.append('Land muss DE, CH oder AT sein.')

    angaben = []
    try:
        angaben = bulk.parse_versangaben_text(fd['versangaben_text'])
    except bulk.BulkSponsoringFehler as e:
        errors.append(str(e))
    for feld, name in (('gesamtbetrag', bulk.parse_betrag), ('zuwendungsdatum', bulk.parse_datum),
                       ('ausstellungsdatum', bulk.parse_datum)):
        try:
            daten[feld] = name(fd[feld]) if fd[feld] else None
        except bulk.BulkSponsoringFehler as e:
            errors.append(str(e))
            daten[feld] = None
    if daten.get('gesamtbetrag') is None and not any('Betrag' in e for e in errors):
        errors.append('Gesamtbetrag ist ein Pflichtfeld.')
    if daten.get('zuwendungsdatum') is None and not any('Datum' in e for e in errors):
        errors.append('Tag der Zuwendung ist ein Pflichtfeld.')
    if daten.get('ausstellungsdatum') is None:
        daten['ausstellungsdatum'] = daten.get('zuwendungsdatum')
    return daten, angaben, errors


def _bulk_render(fd, preview=None, errors=()):
    for e in errors:
        flash(e, 'error')
    return render_template(
        'admin/bulk_sponsoring_form.html',
        form_data=fd,
        preview=preview,
        anreden=bulk.ANREDEN,
        laender=bulk.LAENDER,
    )


@admin_required
def bulk_sponsoring_new():
    """Formular, Vorschau und Eintragen für ein Bulk-Sponsoring."""
    if request.method == 'GET':
        fd = {f: '' for f in BULK_FORM_FIELDS}
        fd.update(country='DE', zahlungsweg='Überweisung', newsletter_consent=False,
                  zuwendungsdatum=datetime.now().strftime('%Y-%m-%d'))
        return _bulk_render(fd)

    fd = _bulk_form_data()
    action = request.form.get('action', 'vorschau')
    daten, angaben, errors = _bulk_validate(fd)
    if errors:
        return _bulk_render(fd, errors=errors)

    try:
        aufloesung = bulk.loese_verse_auf(angaben)
    except bulk.BulkSponsoringFehler as e:
        return _bulk_render(fd, errors=[str(e)])

    if action != 'eintragen':
        # --- Vorschau: nichts wird geschrieben ---
        bestand, aenderungen = bulk.person_vorschau(daten)
        etiketten = bulk.etiketten_fuer_verse(aufloesung.verse)
        betraege = bulk.verteile_betrag(daten['gesamtbetrag'], len(aufloesung.verse))
        token = secrets.token_hex(16)
        session['bulk_token'] = token
        aktive_reservierungen = bulk.aktive_reservierungen(aufloesung.verse)
        preview = {
            'token': token,
            'person_bestand': bestand,
            'person_aenderungen': aenderungen,
            'aufloesung': aufloesung,
            'etiketten': etiketten,
            'etiketten_zertifikat': [e.text.upper() for e in etiketten[:bulk.MAX_ETIKETTEN_ZERTIFIKAT]],
            'zu_viele_etiketten': len(etiketten) > bulk.MAX_ETIKETTEN_ZERTIFIKAT,
            'vortext': bulk.vortext(etiketten),
            'beschreibung': bulk.beschreibung_fliesstext(etiketten, len(aufloesung.verse)),
            'betraege': betraege,
            'regulaer': bulk.REGULAERER_VERSPREIS * len(aufloesung.verse),
            'aktive_reservierungen': aktive_reservierungen,
            'daten': daten,
        }
        return _bulk_render(fd, preview=preview)

    # --- Eintragen ---
    token = request.form.get('token', '')
    if not token or token != session.get('bulk_token'):
        return _bulk_render(fd, errors=['Die Vorschau ist abgelaufen oder wurde schon eingetragen. Bitte erneut prüfen.'])
    session.pop('bulk_token', None)

    try:
        donation, receipt_number, etiketten = bulk.erstelle_bulk_sponsoring(
            daten, aufloesung, admin_email=session.get('admin_email')
        )
        db.session.commit()
    except Exception as e:  # noqa: BLE001 — Meldung wird dem Admin gezeigt
        db.session.rollback()
        current_app.logger.exception('Bulk-Sponsoring konnte nicht eingetragen werden')
        return _bulk_render(fd, errors=[f'Eintragen fehlgeschlagen, nichts geschrieben: {e}'])

    donation_id = donation.id
    flash(f'Bulk-Sponsoring eingetragen: Spende #{donation_id}, Bescheinigung {receipt_number}, '
          f'{len(aufloesung.verse)} Verse.', 'success')

    dokumente = bulk.erzeuge_dokumente(current_app._get_current_object(), donation_id)
    for fehler in dokumente['fehler']:
        flash(f'PDF-Erzeugung fehlgeschlagen ({fehler}). Bitte auf der Detailseite neu generieren.', 'warning')
    if not dokumente['fehler']:
        flash('Zertifikat und Spendenbescheinigung wurden erzeugt. Bitte beide prüfen, dann die Mail senden.', 'info')

    return redirect(url_for('admin.donation_detail', donation_id=donation_id))


@admin_required
def person_by_email():
    """Bestehende Person zur E-Mail nachschlagen (für das Vorbefüllen im Formular)."""
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({'found': False})
    person = Person.query.filter_by(email=email).first()
    if not person:
        return jsonify({'found': False})
    return jsonify({
        'found': True,
        'id': person.id,
        'salutation': person.salutation or '',
        'first_name': person.first_name or '',
        'last_name': person.last_name or '',
        'street': person.street or '',
        'house_number': person.house_number or '',
        'postal_code': person.postal_code or '',
        'city': person.city or '',
        'country': person.country or 'DE',
        'newsletter_consent': bool(person.newsletter_consent),
        'donations': Donation.query.filter_by(person_id=person.id, payment_status='completed').count(),
    })


@admin_required
def send_bulk_email(donation_id):
    """Persönliche Mail mit Zertifikat und Spendenbescheinigung an den Bulk-Spender."""
    donation = Donation.query.get_or_404(donation_id)
    if not donation.is_bulk_sponsoring:
        flash('Diese Spende ist kein Bulk-Sponsoring.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    subject = request.form.get('subject', '').strip()
    text = request.form.get('text', '').strip()
    cc = _bulk_cc_liste(request.form.get('cc', ''))
    if not subject or not text:
        flash('Betreff und Text dürfen nicht leer sein.', 'error')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))
    import re as _re
    for adresse in cc:
        if not _re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", adresse):
            flash(f'Ungültige CC-Adresse: {adresse}', 'error')
            return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    certificate = Certificate.query.filter_by(
        donation_id=donation_id, certificate_type='personal_certificate'
    ).order_by(Certificate.generated_at.desc()).first()
    tax_receipt = Certificate.query.filter_by(
        donation_id=donation_id, certificate_type='tax_receipt'
    ).order_by(Certificate.generated_at.desc()).first()
    if not (certificate and certificate.exists_on_disk and tax_receipt and tax_receipt.exists_on_disk):
        flash('Zertifikat und Spendenbescheinigung müssen vorhanden sein, bevor die Mail gesendet wird.', 'warning')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    attachments = [
        {'path': certificate.file_path,
         'filename': f'NGUE_Zertifikat_{donation.id}.pdf', 'mimetype': 'application/pdf'},
        {'path': tax_receipt.file_path,
         'filename': f'NGUE_Spendenbescheinigung_{donation.id}.pdf', 'mimetype': 'application/pdf'},
    ]

    try:
        email_service.send_bulk_documents_email(donation.person.email, subject, text, attachments, cc=cc)
    except Exception as e:  # noqa: BLE001
        current_app.logger.exception('Bulk-Mail konnte nicht gesendet werden')
        flash(f'Fehler beim Versenden: {e}', 'danger')
        return redirect(url_for('admin.donation_detail', donation_id=donation_id))

    now = datetime.utcnow()
    donation.email_sent = True
    donation.email_sent_at = now
    donation.certificate_sent_at = now
    donation.admin_comment = (donation.admin_comment or '') + (
        f"\nMail mit Zertifikat und Bescheinigung gesendet am {now.strftime('%d.%m.%Y %H:%M')} UTC "
        f"an {donation.person.email}" + (f", CC: {', '.join(cc)}" if cc else "") + f" (Betreff: {subject})"
    )
    db.session.commit()

    flash(f'Mail an {donation.person.email} gesendet' + (f' (CC: {", ".join(cc)})' if cc else '') + '.', 'success')
    return redirect(url_for('admin.donation_detail', donation_id=donation_id))
