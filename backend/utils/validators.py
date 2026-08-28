# utils/validators.py

import re


def validate_email(email):
    """Validate email format"""
    if not email:
        return False, "Email is required"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""


def validate_password(password, min_length=6):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    return True, ""


def validate_register_number(reg_number):
    """Validate student register number"""
    if not reg_number:
        return False, "Register number is required"
    if len(reg_number) < 3 or len(reg_number) > 20:
        return False, "Register number must be between 3 and 20 characters"
    pattern = r'^[A-Za-z0-9]+$'
    if not re.match(pattern, reg_number):
        return False, "Register number must contain only letters and numbers"
    return True, ""


def validate_name(name):
    """Validate student/admin name"""
    if not name:
        return False, "Name is required"
    if len(name) < 2 or len(name) > 100:
        return False, "Name must be between 2 and 100 characters"
    return True, ""


def validate_student_form(data):
    """Validate complete student form data"""
    errors = []
    
    valid, msg = validate_register_number(data.get('register_number', ''))
    if not valid:
        errors.append(msg)
    
    valid, msg = validate_name(data.get('name', ''))
    if not valid:
        errors.append(msg)
    
    valid, msg = validate_email(data.get('email', ''))
    if not valid:
        errors.append(msg)
    
    if not data.get('department'):
        errors.append("Department is required")
    
    if not data.get('year'):
        errors.append("Year is required")
    
    valid, msg = validate_password(data.get('password', ''))
    if not valid:
        errors.append(msg)
    
    return len(errors) == 0, errors
