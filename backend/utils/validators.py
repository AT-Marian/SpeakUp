import re
from functools import wraps
from flask import request, jsonify
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from datetime import datetime
import os

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letters"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain numbers"
    return True, "Valid"


def validate_name(name):
    """Validate name"""
    if not name or len(name) < 2:
        return False, "Name must be at least 2 characters"
    if len(name) > 100:
        return False, "Name cannot exceed 100 characters"
    return True, "Valid"


def token_required(f):
    """Decorator to check JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            from flask import current_app
            data = decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            user_id = data['user_id']
        except ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(user_id, *args, **kwargs)
    
    return decorated


def validate_audio_file(file):
    """Validate uploaded audio file"""
    if not file:
        return False, "No file provided"
    
    allowed_extensions = {'wav', 'mp3', 'm4a', 'webm', 'ogg'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return False, "Invalid file format. Allowed: wav, mp3, m4a, webm, ogg"
    
    if file.content_length > 25 * 1024 * 1024:  # 25MB limit
        return False, "File size exceeds 25MB limit"
    
    return True, "Valid"