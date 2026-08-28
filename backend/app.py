# backend/app.py

import os
import sys
import logging
from flask import Flask, redirect, url_for, render_template, session
from flask_cors import CORS
from flask_migrate import Migrate

# Add backend directory to sys.path if not present
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.config import Config
from backend.database.models import db, Admin
from backend.routes.auth_routes import auth_bp
from backend.routes.admin_routes import admin_bp
from backend.routes.student_routes import student_bp
from backend.routes.attendance_routes import attendance_bp
from backend.routes.api_routes import api_bp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

migrate = Migrate()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'frontend', 'static')


def create_app():
    """Application Factory with separated frontend/backend folders"""
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR
    )
    app.config.from_object(Config)
    
    # Initialize upload directories
    Config.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Root route - Landing page
    @app.route('/')
    def index():
        stats = None
        try:
            from backend.services.attendance_service import AttendanceService
            stats = AttendanceService.get_attendance_stats()
        except Exception as e:
            logger.warning(f"Could not load landing stats: {e}")
        
        return render_template('index.html', stats=stats)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Create tables and default admin
    with app.app_context():
        db.create_all()
        _create_default_admin()
        logger.info("Application initialized successfully")
    
    return app


def _create_default_admin():
    """Create default admin user if none exists"""
    if Admin.query.first() is None:
        admin = Admin(
            username=Config.DEFAULT_ADMIN_USERNAME,
            email=Config.DEFAULT_ADMIN_EMAIL,
            full_name=Config.DEFAULT_ADMIN_FULLNAME,
            is_active=True
        )
        admin.set_password(Config.DEFAULT_ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        logger.info(f"Default admin created: {Config.DEFAULT_ADMIN_USERNAME}")


# ML Service singletons (lazy loaded)
_face_recognizer = None
_face_detector = None
_mask_detector = None


def get_face_recognizer():
    """Get or create FaceRecognizer singleton"""
    global _face_recognizer
    if _face_recognizer is None:
        try:
            from backend.services.face_recognition import FaceRecognizer
            _face_recognizer = FaceRecognizer(model_name=Config.ARCFACE_MODEL)
        except Exception as e:
            logger.error(f"Failed to initialize FaceRecognizer: {e}")
            _face_recognizer = None
    return _face_recognizer


def get_face_detector():
    """Get or create FaceDetector singleton"""
    global _face_detector
    if _face_detector is None:
        try:
            from backend.services.face_detection import FaceDetector
            _face_detector = FaceDetector(model_name=Config.FACE_DETECTOR_MODEL)
        except Exception as e:
            logger.error(f"Failed to initialize FaceDetector: {e}")
            _face_detector = None
    return _face_detector


def get_mask_detector():
    """Get or create MaskDetector singleton"""
    global _mask_detector
    if _mask_detector is None:
        try:
            from backend.services.mask_detection import MaskDetector
            _mask_detector = MaskDetector(model_path=Config.MASK_DETECTOR_MODEL)
        except Exception as e:
            logger.error(f"Failed to initialize MaskDetector: {e}")
            _mask_detector = None
    return _mask_detector


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
