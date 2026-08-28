# routes/api_routes.py

import os
import io
import csv
from flask import Blueprint, request, jsonify, send_file, session
from database.models import db, Student, FaceEmbedding, Attendance
from utils.decorators import admin_required, api_login_required
from utils.helpers import save_base64_image, get_student_face_folder
from services.embedding_service import EmbeddingService
from services.attendance_service import AttendanceService
from config import Config
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api_routes', __name__)


@api_bp.route('/capture-image', methods=['POST'])
@admin_required
def capture_image():
    """Capture face image from webcam (base64)"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    student_id = data.get('student_id')
    image_data = data.get('image')
    image_type = data.get('image_type', 'normal')  # 'normal' or 'masked'
    
    if not student_id or not image_data:
        return jsonify({'success': False, 'message': 'Missing student_id or image data'}), 400
    
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    # Save image
    folder = get_student_face_folder(student_id, image_type)
    prefix = f"{student.register_number}_{image_type}"
    filepath = save_base64_image(image_data, folder, prefix)
    
    if filepath:
        # Count existing images
        from utils.helpers import get_face_images
        count = len(get_face_images(student_id, image_type))
        
        logger.info(f"📸 Captured {image_type} image for student {student_id}: {os.path.basename(filepath)}")
        return jsonify({
            'success': True,
            'message': f'{image_type.capitalize()} image captured',
            'count': count,
            'max': Config.FACE_CAPTURE_COUNT
        })
    
    return jsonify({'success': False, 'message': 'Failed to save image'}), 500


@api_bp.route('/generate-embeddings/<int:student_id>', methods=['POST'])
@admin_required
def generate_embeddings(student_id):
    """Generate face embeddings for a student"""
    from app import get_face_recognizer
    
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    recognizer = get_face_recognizer()
    if recognizer is None:
        return jsonify({
            'success': False, 
            'message': 'Face recognition model not available. Please check ML model installation.'
        }), 500
    
    # Delete existing embeddings
    FaceEmbedding.query.filter_by(student_id=student_id).delete()
    db.session.commit()
    
    # Generate new embeddings
    service = EmbeddingService(recognizer)
    result = service.generate_embeddings(student_id)
    
    return jsonify(result)


@api_bp.route('/attendance-stats')
@admin_required
def attendance_stats():
    """Get attendance stats for dashboard charts"""
    stats = AttendanceService.get_attendance_stats()
    weekly = AttendanceService.get_weekly_stats()
    dept_stats = AttendanceService.get_department_stats()
    
    return jsonify({
        'success': True,
        'stats': stats,
        'weekly': weekly,
        'departments': dept_stats
    })


@api_bp.route('/students/search')
@admin_required
def search_students():
    """AJAX search students"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify({'success': True, 'students': []})
    
    students = Student.query.filter(
        db.or_(
            Student.name.ilike(f'%{query}%'),
            Student.register_number.ilike(f'%{query}%')
        ),
        Student.is_active == True
    ).limit(10).all()
    
    return jsonify({
        'success': True,
        'students': [s.to_dict() for s in students]
    })


@api_bp.route('/export-attendance', methods=['POST'])
@admin_required
def export_attendance():
    """Export attendance to CSV"""
    data = request.get_json() or {}
    start_str = data.get('start_date', date.today().isoformat())
    end_str = data.get('end_date', date.today().isoformat())
    department = data.get('department', '')
    
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = date.today()
        end_date = date.today()
    
    records = AttendanceService.get_attendance_by_date_range(
        start_date, end_date, department or None
    )
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'Register No', 'Student Name', 'Department', 'Date', 'Time', 'Mask', 'Confidence'])
    
    for i, (att, student) in enumerate(records, 1):
        writer.writerow([
            i,
            student.register_number,
            student.name,
            student.department,
            att.attendance_date.strftime('%d/%m/%Y'),
            att.attendance_time.strftime('%I:%M %p'),
            'Yes' if att.mask_detected else 'No',
            f'{att.recognition_confidence:.2%}'
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_{start_str}_to_{end_str}.csv'
    )


@api_bp.route('/delete-student/<int:student_id>', methods=['DELETE'])
@admin_required
def api_delete_student(student_id):
    """API: Delete student"""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    try:
        from utils.helpers import delete_student_files
        delete_student_files(student_id)
        db.session.delete(student)
        db.session.commit()
        return jsonify({'success': True, 'message': f'{student.name} deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/embedding-stats/<int:student_id>')
@admin_required
def embedding_stats(student_id):
    """Get embedding stats for a student"""
    from app import get_face_recognizer
    recognizer = get_face_recognizer()
    if recognizer:
        service = EmbeddingService(recognizer)
        stats = service.get_embedding_stats(student_id)
        return jsonify({'success': True, **stats})
    return jsonify({'success': False, 'message': 'Model not available'})
