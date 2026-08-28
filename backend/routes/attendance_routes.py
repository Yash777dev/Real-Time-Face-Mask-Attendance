# backend/routes/attendance_routes.py

from flask import Blueprint, render_template, Response, request, jsonify, session
from backend.utils.decorators import admin_required
from backend.services.attendance_service import AttendanceService
import logging

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance_routes', __name__)

_attendance_service = None


def get_attendance_service():
    """Get or create AttendanceService singleton"""
    global _attendance_service
    if _attendance_service is None:
        from backend.app import get_face_detector, get_face_recognizer, get_mask_detector
        _attendance_service = AttendanceService(
            face_detector=get_face_detector(),
            face_recognizer=get_face_recognizer(),
            mask_detector=get_mask_detector()
        )
    return _attendance_service


@attendance_bp.route('/camera')
@admin_required
def camera():
    """Live attendance camera page"""
    stats = AttendanceService.get_attendance_stats()
    return render_template('admin/camera.html', stats=stats)


@attendance_bp.route('/video_feed')
@admin_required
def video_feed():
    """MJPEG streaming endpoint"""
    service = get_attendance_service()
    
    if not service.is_running:
        service.start_camera(0)
    
    return Response(
        service.generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@attendance_bp.route('/start', methods=['POST'])
@admin_required
def start_camera():
    """Start camera session"""
    service = get_attendance_service()
    source = request.json.get('source', 0) if request.is_json else 0
    
    success = service.start_camera(source)
    
    if success:
        return jsonify({'success': True, 'message': 'Camera started'})
    else:
        return jsonify({'success': False, 'message': 'Failed to open camera'}), 500


@attendance_bp.route('/stop', methods=['POST'])
@admin_required
def stop_camera():
    """Stop camera session"""
    service = get_attendance_service()
    service.stop_camera()
    return jsonify({'success': True, 'message': 'Camera stopped'})


@attendance_bp.route('/status')
@admin_required
def camera_status():
    """Get camera status"""
    service = get_attendance_service()
    return jsonify({
        'running': service.is_running,
        'embeddings_loaded': len(service.student_embeddings),
        'recognized_today': len(service.recognized_today)
    })