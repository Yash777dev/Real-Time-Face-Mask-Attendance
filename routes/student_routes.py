# routes/student_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database.models import db, Student, Attendance, FaceEmbedding
from utils.decorators import student_required
from datetime import date
import logging

logger = logging.getLogger(__name__)

student_bp = Blueprint('student_routes', __name__)


@student_bp.route('/dashboard')
@student_required
def dashboard():
    """Student dashboard with personal stats"""
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)
    
    # Attendance stats
    total_attendance = Attendance.query.filter_by(student_id=student_id).count()
    today_record = Attendance.query.filter_by(
        student_id=student_id,
        attendance_date=date.today()
    ).first()
    
    mask_count = Attendance.query.filter_by(
        student_id=student_id, mask_detected=True
    ).count()
    
    # Recent attendance
    recent = Attendance.query.filter_by(student_id=student_id).order_by(
        Attendance.attendance_date.desc()
    ).limit(7).all()
    
    # Embedding status
    embedding_count = FaceEmbedding.query.filter_by(
        student_id=student_id, is_active=True
    ).count()
    
    return render_template('student/dashboard.html',
                         student=student,
                         total_attendance=total_attendance,
                         today_present=today_record is not None,
                         today_record=today_record,
                         mask_count=mask_count,
                         recent=recent,
                         embedding_count=embedding_count)


@student_bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    """Student profile view/edit"""
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'change_password':
            current = request.form.get('current_password', '')
            new = request.form.get('new_password', '')
            confirm = request.form.get('confirm_password', '')
            
            if not student.check_password(current):
                flash('Current password is incorrect.', 'danger')
            elif len(new) < 6:
                flash('New password must be at least 6 characters.', 'danger')
            elif new != confirm:
                flash('Passwords do not match.', 'danger')
            else:
                student.set_password(new)
                db.session.commit()
                flash('Password changed successfully!', 'success')
        
        return redirect(url_for('student_routes.profile'))
    
    # Get embedding stats
    embedding_count = FaceEmbedding.query.filter_by(
        student_id=student_id, is_active=True
    ).count()
    
    total_attendance = Attendance.query.filter_by(student_id=student_id).count()
    
    return render_template('student/profile.html',
                         student=student,
                         embedding_count=embedding_count,
                         total_attendance=total_attendance)


@student_bp.route('/attendance')
@student_required
def attendance():
    """Student attendance history"""
    student_id = session.get('user_id')
    
    records = Attendance.query.filter_by(student_id=student_id).order_by(
        Attendance.attendance_date.desc()
    ).all()
    
    return render_template('student/attendance.html', attendance=records)


@student_bp.route('/api/attendance-percentage')
@student_required
def attendance_percentage():
    """API: Get attendance percentage for current student"""
    student_id = session.get('user_id')
    student = Student.query.get(student_id)
    
    if not student:
        return jsonify({'success': False, 'percentage': 0, 'present_status': False})
    
    total = Attendance.query.filter_by(student_id=student_id).count()
    today_present = Attendance.query.filter_by(
        student_id=student_id,
        attendance_date=date.today()
    ).first() is not None
    
    if student.created_at:
        days_enrolled = max((date.today() - student.created_at.date()).days, 1)
        working_days = max(int(days_enrolled * 5 / 7), 1)
        percentage = round((total / working_days) * 100, 1)
        percentage = min(percentage, 100)
    else:
        percentage = 0
    
    return jsonify({
        'success': True,
        'percentage': percentage,
        'total_present': total,
        'present_status': today_present
    })
