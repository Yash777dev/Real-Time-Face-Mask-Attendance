# backend/routes/auth_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.database.models import db, Admin, Student
from backend.utils.security import create_session, destroy_session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth_routes', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login for admin and student"""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_routes.dashboard'))
        return redirect(url_for('student_routes.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'admin')
        
        if not username or not password:
            flash('Please enter username and password.', 'warning')
            return render_template('login.html')
        
        if role == 'admin':
            admin = Admin.query.filter_by(username=username, is_active=True).first()
            if admin and admin.check_password(password):
                admin.last_login = datetime.utcnow()
                db.session.commit()
                
                create_session(
                    user_id=admin.id,
                    role='admin',
                    username=admin.username,
                    full_name=admin.full_name
                )
                
                logger.info(f"Admin logged in: {username}")
                flash(f'Welcome back, {admin.full_name}!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin_routes.dashboard'))
            else:
                flash('Invalid admin credentials.', 'danger')
        
        elif role == 'student':
            student = Student.query.filter_by(register_number=username, is_active=True).first()
            if student and student.check_password(password):
                create_session(
                    user_id=student.id,
                    role='student',
                    username=student.register_number,
                    full_name=student.name
                )
                
                logger.info(f"Student logged in: {username}")
                flash(f'Welcome, {student.name}!', 'success')
                return redirect(url_for('student_routes.dashboard'))
            else:
                flash('Invalid student credentials. Use your register number.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    username = session.get('username', 'Unknown')
    role = session.get('role', 'unknown')
    destroy_session()
    logger.info(f"User logged out: {username} ({role})")
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth_routes.login'))