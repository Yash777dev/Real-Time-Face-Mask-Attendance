# utils/decorators.py

from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
import logging

logger = logging.getLogger(__name__)


def login_required(f=None, user_type=None):
    """Require any authenticated user or specific role"""
    if f is None:
        return lambda func: login_required(func, user_type=user_type)

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api'):
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth_routes.login', next=request.url))
        
        if user_type and session.get('role') != user_type:
            if request.path.startswith('/api'):
                return jsonify({'success': False, 'message': 'Access denied'}), 403
            flash(f'Access denied. {user_type.capitalize()} privileges required.', 'danger')
            return redirect(url_for('auth_routes.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require authenticated admin user"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api'):
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth_routes.login'))
        if session.get('role') != 'admin':
            if request.path.startswith('/api'):
                return jsonify({'success': False, 'message': 'Access denied'}), 403
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth_routes.login'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Require authenticated student user"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api'):
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth_routes.login'))
        if session.get('role') != 'student':
            if request.path.startswith('/api'):
                return jsonify({'success': False, 'message': 'Access denied'}), 403
            flash('Access denied. Student account required.', 'danger')
            return redirect(url_for('auth_routes.login'))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """Require authentication for API endpoints (returns JSON)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def api_required(f):
    """Alias for api_login_required"""
    return api_login_required(f)