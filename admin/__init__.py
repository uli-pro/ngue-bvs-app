from flask import Blueprint
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def init_admin(app):
    """Initialize admin module with app context"""
    # Get limiter from app
    limiter = app.extensions.get('limiter')
    
    # Import views after limiter is available
    from admin import auth, views
    
    # Set limiter in auth module
    auth.limiter = limiter
    
    # Register routes
    # Auth routes
    admin_bp.add_url_rule('/login', 'login', auth.login, methods=['GET', 'POST'])
    admin_bp.add_url_rule('/verify/<token>', 'verify_token', auth.verify_token)
    admin_bp.add_url_rule('/logout', 'logout', auth.logout)
    
    # Admin routes
    admin_bp.add_url_rule('/', 'index', views.index)
    
    # Person management
    admin_bp.add_url_rule('/persons', 'persons_list', views.persons_list)
    admin_bp.add_url_rule('/persons/<int:person_id>/edit', 'person_edit', views.person_edit, methods=['GET', 'POST'])
    
    # Verse management
    admin_bp.add_url_rule('/verses', 'verses_list', views.verses_list)
    admin_bp.add_url_rule('/verses/<int:verse_id>/toggle', 'verse_toggle', views.verse_toggle, methods=['POST'])
    admin_bp.add_url_rule('/verses/clear-reservations', 'clear_reservations', views.clear_reservations, methods=['POST'])
    
    # Donation management
    admin_bp.add_url_rule('/donations', 'donations_list', views.donations_list)
    admin_bp.add_url_rule('/donations/<int:donation_id>', 'donation_detail', views.donation_detail)
    admin_bp.add_url_rule('/donations/<int:donation_id>/update-comment', 'update_donation_comment', views.update_donation_comment, methods=['POST'])
    admin_bp.add_url_rule('/donations/<int:donation_id>/regenerate-certificate', 'regenerate_certificate', views.regenerate_certificate, methods=['POST'])
    admin_bp.add_url_rule('/donations/<int:donation_id>/resend-certificate', 'resend_certificate', views.resend_certificate, methods=['POST'])
    admin_bp.add_url_rule('/donations/<int:donation_id>/view-certificate', 'view_certificate', views.view_certificate, methods=['GET'])
    
    # Tax receipt management
    admin_bp.add_url_rule('/donations/<int:donation_id>/regenerate-tax-receipt', 'regenerate_tax_receipt', views.regenerate_tax_receipt, methods=['POST'])
    admin_bp.add_url_rule('/donations/<int:donation_id>/resend-tax-receipt', 'resend_tax_receipt', views.resend_tax_receipt, methods=['POST'])
    admin_bp.add_url_rule('/donations/<int:donation_id>/view-tax-receipt', 'view_tax_receipt', views.view_tax_receipt, methods=['GET'])

    # Database cleanup management
    admin_bp.add_url_rule('/cleanup', 'cleanup_orphaned', views.cleanup_orphaned, methods=['POST'])
    admin_bp.add_url_rule('/api/cleanup-stats', 'get_cleanup_stats', views.get_cleanup_stats, methods=['GET'])

    # Apply rate limiting - skip for now as it requires route-specific setup

    return admin_bp