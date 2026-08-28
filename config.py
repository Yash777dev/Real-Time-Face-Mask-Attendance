# config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application Configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:Admin@localhost:5432/face_attendance_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Upload
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv('UPLOAD_FOLDER', 'uploads'))
    FACES_FOLDER = os.path.join(UPLOAD_FOLDER, 'faces')
    NORMAL_FACES_FOLDER = os.path.join(FACES_FOLDER, 'normal')
    MASKED_FACES_FOLDER = os.path.join(FACES_FOLDER, 'masked')
    PROFILES_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # ML Models
    ML_MODELS_DIR = os.path.join(BASE_DIR, 'ml_models')
    FACE_DETECTOR_MODEL = os.getenv('FACE_DETECTOR_MODEL', 'yolov8n-face.pt')
    MASK_DETECTOR_MODEL = os.getenv('MASK_DETECTOR_MODEL', 'mask_detector.pt')
    ARCFACE_MODEL = os.getenv('ARCFACE_MODEL', 'buffalo_l')
    
    # Face Recognition
    RECOGNITION_THRESHOLD = float(os.getenv('RECOGNITION_THRESHOLD', 0.55))
    MIN_FACE_SIZE = float(os.getenv('MIN_FACE_SIZE', 0.3))
    FACE_CAPTURE_COUNT = int(os.getenv('FACE_CAPTURE_COUNT', 5))
    
    # Admin Defaults
    DEFAULT_ADMIN_USERNAME = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_EMAIL = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@faceattendance.com')
    DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
    DEFAULT_ADMIN_FULLNAME = os.getenv('DEFAULT_ADMIN_FULLNAME', 'System Administrator')
    
    # Departments
    DEPARTMENTS = ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE', 'IT', 'AIDS', 'AIML', 'CSM']
    YEARS = ['1st Year', '2nd Year', '3rd Year', '4th Year']
    SEMESTERS = ['1', '2', '3', '4', '5', '6', '7', '8']
    SECTIONS = ['A', 'B', 'C', 'D']
    
    @staticmethod
    def init_app(app):
        """Initialize upload directories"""
        dirs = [
            Config.UPLOAD_FOLDER,
            Config.FACES_FOLDER,
            Config.NORMAL_FACES_FOLDER,
            Config.MASKED_FACES_FOLDER,
            Config.PROFILES_FOLDER,
            Config.ML_MODELS_DIR,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
