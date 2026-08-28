# database/__init__.py

from database.models import db, Admin, Student, FaceEmbedding, Attendance, AttendanceLog, SystemConfig

__all__ = ['db', 'Admin', 'Student', 'FaceEmbedding', 'Attendance', 'AttendanceLog', 'SystemConfig']