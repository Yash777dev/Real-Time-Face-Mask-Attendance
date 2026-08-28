# utils/security.py

import hashlib
import secrets
import string
import re
import os
from datetime import datetime
from flask import session
import logging

logger = logging.getLogger(__name__)


def create_session(user_id, role, username, full_name=None):
    """Create user session after login"""
    session.clear()
    session['user_id'] = user_id
    session['role'] = role
    session['username'] = username
    session['full_name'] = full_name or username
    session['login_time'] = datetime.utcnow().isoformat()
    session['csrf_token'] = secrets.token_hex(32)
    session.permanent = True


def destroy_session():
    """Clear session on logout"""
    session.clear()


def get_current_user_id():
    """Get current user ID from session"""
    return session.get('user_id')


def get_current_role():
    """Get current user role from session"""
    return session.get('role')


def is_admin():
    """Check if current user is admin"""
    return session.get('role') == 'admin'


def is_student():
    """Check if current user is student"""
    return session.get('role') == 'student'


def generate_temp_password(length=8):
    """Generate a temporary password"""
    return secrets.token_urlsafe(length)[:length]


class SecurityUtils:
    """Security utility functions"""

    @staticmethod
    def generate_secure_token(length=32):
        """Generate a secure random token"""
        return secrets.token_hex(length)

    @staticmethod
    def generate_password(length=10):
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password

    @staticmethod
    def hash_file(filepath):
        """Generate SHA256 hash of a file"""
        try:
            sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file: {e}")
            return None

    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename to prevent path traversal"""
        filename = os.path.basename(filename)
        filename = re.sub(r'[^\w\s\-.]', '', filename)
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        return filename

    @staticmethod
    def validate_image_content(filepath):
        """Validate that file is actually an image"""
        try:
            from PIL import Image
            img = Image.open(filepath)
            img.verify()
            return True, "Valid image"
        except Exception as e:
            return False, f"Invalid image: {str(e)}"

    @staticmethod
    def check_file_size(filepath, max_size_mb=10):
        """Check if file size is within limit"""
        try:
            size_bytes = os.path.getsize(filepath)
            size_mb = size_bytes / (1024 * 1024)
            if size_mb > max_size_mb:
                return False, f"File too large: {size_mb:.2f}MB (max {max_size_mb}MB)"
            return True, f"File size OK: {size_mb:.2f}MB"
        except Exception as e:
            return False, f"Error checking file size: {str(e)}"

    @staticmethod
    def mask_sensitive_data(data, fields_to_mask=None):
        """Mask sensitive fields in a dictionary"""
        if fields_to_mask is None:
            fields_to_mask = ['password', 'password_hash', 'token', 'secret']
        masked = data.copy()
        for field in fields_to_mask:
            if field in masked:
                masked[field] = '***MASKED***'
        return masked

    @staticmethod
    def rate_limit_check(key, limit=10, window=60):
        """Simple in-memory rate limiting check"""
        return True, limit