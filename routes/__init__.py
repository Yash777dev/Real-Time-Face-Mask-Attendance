# routes/__init__.py

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.student_routes import student_bp
from routes.attendance_routes import attendance_bp
from routes.api_routes import api_bp

__all__ = ['auth_bp', 'admin_bp', 'student_bp', 'attendance_bp', 'api_bp']
