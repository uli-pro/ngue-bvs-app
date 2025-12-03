from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, session
from admin.decorators import admin_required
from models import db, Person, Verse, Donation, VerseReservation, Certificate
from sqlalchemy import or_, func
from pdf_service import PDFGeneratorService
from email_service import email_service
from datetime import datetime, timedelta

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
    
    return render_template('admin/donation_detail.html', 
                         donation=donation, 
                         certificate=certificate,
                         tax_receipt=tax_receipt)

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
        tax_receipt = pdf_service.generate_tax_receipt(donation.id)
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