from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            flash('Bitte melden Sie sich als Administrator an.', 'warning')
            return redirect(url_for('admin.login'))
        
        # Check session timeout (30 minutes)
        from datetime import datetime, timedelta
        login_time = session.get('admin_login_time')
        if login_time:
            login_dt = datetime.fromisoformat(login_time)
            if datetime.utcnow() - login_dt > timedelta(minutes=30):
                session.pop('admin_authenticated', None)
                session.pop('admin_email', None)
                session.pop('admin_login_time', None)
                flash('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.', 'warning')
                return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)
    return decorated_function