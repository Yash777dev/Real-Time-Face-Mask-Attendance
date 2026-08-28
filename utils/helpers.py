# utils/helpers.py

import os
import uuid
import base64
from datetime import datetime, date
from werkzeug.utils import secure_filename
from config import Config
import logging

logger = logging.getLogger(__name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS


def save_file(file, folder, prefix=''):
    """
    Save uploaded file to specified folder
    
    Returns:
        Relative path to saved file or None
    """
    try:
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}" if prefix else f"{uuid.uuid4().hex}.{ext}"
            filename = secure_filename(filename)
            
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            file.save(filepath)
            
            return filepath
    except Exception as e:
        logger.error(f"Error saving file: {e}")
    return None


def save_base64_image(base64_data, folder, prefix='face'):
    """
    Save base64 encoded image to file
    
    Args:
        base64_data: Base64 string (with or without data URI prefix)
        folder: Target directory
        prefix: Filename prefix
        
    Returns:
        Filepath string or None
    """
    try:
        # Remove data URI prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        image_data = base64.b64decode(base64_data)
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.jpg"
        
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return filepath
    except Exception as e:
        logger.error(f"Error saving base64 image: {e}")
    return None


def format_date(dt, fmt='%d %b %Y'):
    """Format datetime object to string"""
    if isinstance(dt, (datetime, date)):
        return dt.strftime(fmt)
    return str(dt)


def format_time(t, fmt='%I:%M %p'):
    """Format time object to string"""
    if t:
        return t.strftime(fmt)
    return ''


def get_student_face_folder(student_id, image_type='normal'):
    """Get the face images folder for a student"""
    if image_type == 'masked':
        base = Config.MASKED_FACES_FOLDER
    else:
        base = Config.NORMAL_FACES_FOLDER
    
    folder = os.path.join(base, str(student_id))
    os.makedirs(folder, exist_ok=True)
    return folder


def get_face_images(student_id, image_type='normal'):
    """Get list of face images for a student"""
    folder = get_student_face_folder(student_id, image_type)
    if not os.path.exists(folder):
        return []
    
    images = []
    for f in sorted(os.listdir(folder)):
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            images.append(os.path.join(folder, f))
    return images


def delete_student_files(student_id):
    """Delete all files associated with a student"""
    import shutil
    
    for image_type in ['normal', 'masked']:
        folder = get_student_face_folder(student_id, image_type)
        if os.path.exists(folder):
            shutil.rmtree(folder)
            logger.info(f"Deleted face folder: {folder}")
