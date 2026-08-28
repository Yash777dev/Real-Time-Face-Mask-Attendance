# backend/routes/admin_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from backend.database.models import db, Admin, Student, FaceEmbedding, Attendance, AttendanceLog
from backend.utils.decorators import admin_required
from backend.utils.validators import validate_student_form
from backend.utils.helpers import get_face_images, delete_student_files
from backend.services.attendance_service import AttendanceService
from backend.config import Config
from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin_routes', __name__)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with stats and charts"""
    stats = AttendanceService.get_attendance_stats()
    weekly = AttendanceService.get_weekly_stats()
    dept_stats = AttendanceService.get_department_stats()
    
    recent = db.session.query(Attendance, Student).join(
        Student, Attendance.student_id == Student.id
    ).order_by(Attendance.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         weekly=weekly,
                         dept_stats=dept_stats,
                         recent=recent)


@admin_bp.route('/students')
@admin_required
def students():
    """List all students with search/filter"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    per_page = 15
    
    query = Student.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.register_number.ilike(f'%{search}%'),
                Student.email.ilike(f'%{search}%')
            )
        )
    
    if department:
        query = query.filter_by(department=department)
    
    students_page = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    embedding_counts = {}
    for student in students_page.items:
        embedding_counts[student.id] = FaceEmbedding.query.filter_by(
            student_id=student.id, is_active=True
        ).count()
    
    return render_template('admin/students.html',
                         students=students_page,
                         search=search,
                         department=department,
                         departments=Config.DEPARTMENTS,
                         embedding_counts=embedding_counts)


@admin_bp.route('/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    """Add new student"""
    if request.method == 'POST':
        data = {
            'register_number': request.form.get('register_number', '').strip().upper(),
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip().lower(),
            'department': request.form.get('department', ''),
            'year': request.form.get('year', ''),
            'semester': request.form.get('semester', ''),
            'section': request.form.get('section', ''),
            'password': request.form.get('password', '').strip(),
        }
        
        valid, errors = validate_student_form(data)
        if not valid:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/add_student.html',
                                 departments=Config.DEPARTMENTS,
                                 years=Config.YEARS,
                                 semesters=Config.SEMESTERS,
                                 sections=Config.SECTIONS,
                                 form_data=data)
        
        if Student.query.filter_by(register_number=data['register_number']).first():
            flash('Register number already exists.', 'danger')
            return render_template('admin/add_student.html',
                                 departments=Config.DEPARTMENTS,
                                 years=Config.YEARS,
                                 semesters=Config.SEMESTERS,
                                 sections=Config.SECTIONS,
                                 form_data=data)
        
        if Student.query.filter_by(email=data['email']).first():
            flash('Email already exists.', 'danger')
            return render_template('admin/add_student.html',
                                 departments=Config.DEPARTMENTS,
                                 years=Config.YEARS,
                                 semesters=Config.SEMESTERS,
                                 sections=Config.SECTIONS,
                                 form_data=data)
        
        try:
            student = Student(
                register_number=data['register_number'],
                name=data['name'],
                email=data['email'],
                department=data['department'],
                year=data['year'],
                semester=data['semester'],
                section=data['section'],
                is_active=True
            )
            student.set_password(data['password'])
            db.session.add(student)
            db.session.commit()
            
            logger.info(f"Student added: {data['register_number']} - {data['name']}")
            flash(f'Student {data["name"]} added successfully! Now register their face.', 'success')
            return redirect(url_for('admin_routes.register_face', student_id=student.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding student: {e}")
            flash('Error adding student. Please try again.', 'danger')
    
    return render_template('admin/add_student.html',
                         departments=Config.DEPARTMENTS,
                         years=Config.YEARS,
                         semesters=Config.SEMESTERS,
                         sections=Config.SECTIONS,
                         form_data={})


@admin_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    """Edit student details"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        student.name = request.form.get('name', student.name).strip()
        student.email = request.form.get('email', student.email).strip().lower()
        student.department = request.form.get('department', student.department)
        student.year = request.form.get('year', student.year)
        student.semester = request.form.get('semester', student.semester)
        student.section = request.form.get('section', student.section)
        
        new_password = request.form.get('password', '').strip()
        if new_password:
            student.set_password(new_password)
        
        try:
            db.session.commit()
            flash(f'Student {student.name} updated successfully!', 'success')
            return redirect(url_for('admin_routes.students'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating student.', 'danger')
    
    return render_template('admin/add_student.html',
                         student=student,
                         departments=Config.DEPARTMENTS,
                         years=Config.YEARS,
                         semesters=Config.SEMESTERS,
                         sections=Config.SECTIONS,
                         form_data=student.to_dict(),
                         edit_mode=True)


@admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    """Delete student and their files"""
    student = Student.query.get_or_404(student_id)
    name = student.name
    
    try:
        delete_student_files(student_id)
        db.session.delete(student)
        db.session.commit()
        
        logger.info(f"Student deleted: {name}")
        flash(f'Student {name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting student: {e}")
        flash('Error deleting student.', 'danger')
    
    return redirect(url_for('admin_routes.students'))


@admin_bp.route('/students/<int:student_id>/register-face')
@admin_required
def register_face(student_id):
    """Face registration page with webcam capture"""
    student = Student.query.get_or_404(student_id)
    
    normal_images = get_face_images(student_id, 'normal')
    masked_images = get_face_images(student_id, 'masked')
    
    embedding_count = FaceEmbedding.query.filter_by(
        student_id=student_id, is_active=True
    ).count()
    
    return render_template('admin/register_face.html',
                         student=student,
                         normal_count=len(normal_images),
                         masked_count=len(masked_images),
                         embedding_count=embedding_count,
                         max_captures=Config.FACE_CAPTURE_COUNT)


@admin_bp.route('/attendance')
@admin_required
def attendance():
    """View attendance records"""
    start_date_str = request.args.get('start_date', date.today().isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    department = request.args.get('department', '')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = date.today()
        end_date = date.today()
    
    records = AttendanceService.get_attendance_by_date_range(start_date, end_date, department or None)
    
    return render_template('admin/attendance.html',
                         records=records,
                         start_date=start_date_str,
                         end_date=end_date_str,
                         department=department,
                         departments=Config.DEPARTMENTS)


@admin_bp.route('/reports')
@admin_required
def reports():
    """Reports page"""
    return render_template('admin/reports.html',
                         departments=Config.DEPARTMENTS)
