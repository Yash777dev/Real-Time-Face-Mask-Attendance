# database/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import numpy as np

db = SQLAlchemy()


class Admin(db.Model):
    """Admin user model"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class Student(db.Model):
    """Student user model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    register_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    department = db.Column(db.String(50), index=True)
    year = db.Column(db.String(10))
    semester = db.Column(db.String(10))
    section = db.Column(db.String(10))
    password_hash = db.Column(db.String(255), nullable=False)
    profile_image = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    face_embeddings = db.relationship('FaceEmbedding', backref='student', 
                                      cascade='all, delete-orphan', lazy='dynamic')
    attendance_records = db.relationship('Attendance', backref='student', 
                                        cascade='all, delete-orphan', lazy='dynamic')
    
    __table_args__ = (
        db.Index('idx_register_number', 'register_number'),
        db.Index('idx_department', 'department'),
    )
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def get_attendance_percentage(self, total_classes=None):
        """Calculate attendance percentage"""
        total_attendance = self.attendance_records.count()
        
        if total_classes is None:
            total_classes = total_attendance  # If not specified, use actual classes attended
        
        if total_classes == 0:
            return 0.0
        
        return round((total_attendance / total_classes) * 100, 2)
    
    def get_todays_status(self):
        """Check if student marked present today"""
        today = date.today()
        return self.attendance_records.filter_by(attendance_date=today).first() is not None
    
    def to_dict(self, include_password=False):
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'register_number': self.register_number,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'year': self.year,
            'semester': self.semester,
            'section': self.section,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
        
        if include_password:
            data['password_hash'] = self.password_hash
        
        return data


class FaceEmbedding(db.Model):
    """Face embedding storage"""
    __tablename__ = 'face_embeddings'
    
    id = db.Column(db.Integer, primary_key=True)
    embedding_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    embedding = db.Column(db.LargeBinary, nullable=False)  # Store as binary (numpy array)
    image_path = db.Column(db.String(255))
    image_type = db.Column(db.String(20), nullable=False)  # 'normal' or 'masked'
    face_quality = db.Column(db.Float)  # Quality score of the face
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_student_id_type', 'student_id', 'image_type'),
    )
    
    def set_embedding(self, embedding_array):
        """Store numpy array as binary"""
        self.embedding = embedding_array.tobytes()
    
    def get_embedding(self):
        """Retrieve numpy array from binary"""
        if self.embedding:
            return np.frombuffer(self.embedding, dtype=np.float32)
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'embedding_id': self.embedding_id,
            'student_id': self.student_id,
            'image_type': self.image_type,
            'face_quality': self.face_quality,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class Attendance(db.Model):
    """Attendance record"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    attendance_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    attendance_date = db.Column(db.Date, nullable=False, index=True)
    attendance_time = db.Column(db.Time, nullable=False)
    mask_detected = db.Column(db.Boolean, default=False)
    recognition_confidence = db.Column(db.Float, nullable=False)
    camera_source = db.Column(db.String(100), default='default_camera')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    device_info = db.Column(db.String(255))
    remarks = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'attendance_date', 
                           name='unique_attendance_per_day'),
        db.Index('idx_attendance_date', 'attendance_date'),
        db.Index('idx_student_date', 'student_id', 'attendance_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'attendance_id': self.attendance_id,
            'student_id': self.student_id,
            'attendance_date': self.attendance_date.isoformat(),
            'attendance_time': self.attendance_time.isoformat(),
            'mask_detected': self.mask_detected,
            'recognition_confidence': round(self.recognition_confidence, 4),
            'camera_source': self.camera_source,
            'created_at': self.created_at.isoformat()
        }


class AttendanceLog(db.Model):
    """Detailed attendance log for analytics"""
    __tablename__ = 'attendance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), index=True)
    event_type = db.Column(db.String(50))  # 'face_detected', 'recognized', 'marked_present'
    event_data = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'log_id': self.log_id,
            'student_id': self.student_id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'timestamp': self.timestamp.isoformat()
        }


class SystemConfig(db.Model):
    """System configuration storage"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.String(500))
    data_type = db.Column(db.String(20))  # 'string', 'float', 'int', 'boolean'
    description = db.Column(db.String(255))
    is_editable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'config_key': self.config_key,
            'config_value': self.config_value,
            'data_type': self.data_type,
            'description': self.description
        }