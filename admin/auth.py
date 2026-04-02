import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, AdminToken
from email_service import email_service

# Get limiter from app (will be passed in during blueprint registration)
limiter = None

def get_admin_emails():
    """Get list of authorized admin emails from environment"""
    admin_emails = os.getenv('ADMIN_EMAILS', '')
    return [email.strip().lower() for email in admin_emails.split(',') if email.strip()]

def login():
    """Show login form and handle magic link request"""
    if request.method == 'GET':
        # Already logged in?
        if session.get('admin_authenticated'):
            return redirect(url_for('admin.index'))
        return render_template('admin/login.html')
    
    # POST: Request magic link
    email = request.form.get('email', '').strip().lower()
    
    # Check whitelist
    if email not in get_admin_emails():
        flash('Diese E-Mail-Adresse ist nicht als Administrator autorisiert.', 'danger')
        return render_template('admin/login.html')
    
    # Create token
    ip_address = request.remote_addr
    token = AdminToken.create_token(email, ip_address)
    
    # Send email
    magic_link = url_for('admin.verify_token', token=token.token, _external=True)
    
    email_service.send_admin_magic_link(email, magic_link)
    
    return render_template('admin/login_sent.html', email=email)

def verify_token(token):
    """Verify magic link token and log in admin"""
    admin_token = AdminToken.verify_token(token)
    
    if not admin_token:
        flash('Ung�ltiger oder abgelaufener Login-Link.', 'danger')
        return redirect(url_for('admin.login'))
    
    # Check whitelist again
    if admin_token.email not in get_admin_emails():
        flash('Diese E-Mail-Adresse ist nicht mehr autorisiert.', 'danger')
        return redirect(url_for('admin.login'))
    
    # Create session
    session['admin_authenticated'] = True
    session['admin_email'] = admin_token.email
    session['admin_login_time'] = datetime.utcnow().isoformat()
    session.permanent = True  # Use Flask's permanent session timeout
    
    # Cleanup old tokens
    AdminToken.cleanup_expired()
    
    return redirect(url_for('admin.index'))

def logout():
    """Log out admin"""
    session.pop('admin_authenticated', None)
    session.pop('admin_email', None)
    session.pop('admin_login_time', None)
    flash('Sie wurden erfolgreich abgemeldet.', 'success')
    return redirect(url_for('index'))