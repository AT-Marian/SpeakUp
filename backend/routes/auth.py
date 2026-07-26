from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models.user import User
from utils.validators import validate_email, validate_password, validate_name
from utils.helpers import generate_response, serialize_mongo_doc, Logger
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# MongoDB database instance (passed from app.py)
db = None

def set_database(database):
    global db
    db = database


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name') or not data.get('email') or not data.get('password'):
            return generate_response(False, 'Missing required fields', None, 400)
        
        # Validate email
        if not validate_email(data['email']):
            return generate_response(False, 'Invalid email format', None, 400)
        
        # Validate name
        valid, msg = validate_name(data['name'])
        if not valid:
            return generate_response(False, msg, None, 400)
        
        # Validate password
        valid, msg = validate_password(data['password'])
        if not valid:
            return generate_response(False, msg, None, 400)
        
        # Check if user exists
        if User.find_by_email(db, data['email']):
            return generate_response(False, 'Email already registered', None, 409)
        
        # Create user
        user = User(db, data['name'], data['email'], data['password'])
        user_id = user.create()
        
        Logger.info(f"New user registered: {data['email']}")
        
        return generate_response(
            True,
            'User registered successfully',
            {'user_id': user_id, 'email': data['email']},
            201
        )
    
    except Exception as e:
        Logger.error(f"Registration error: {str(e)}")
        return generate_response(False, 'Registration failed', None, 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('email') or not data.get('password'):
            return generate_response(False, 'Email and password required', None, 400)
        
        # Find user
        user_doc = User.find_by_email(db, data['email'])
        if not user_doc:
            return generate_response(False, 'Invalid credentials', None, 401)
        
        # Verify password
        if not User.verify_password(user_doc['password'], data['password']):
            return generate_response(False, 'Invalid credentials', None, 401)
        
        # Check if user is active
        if not user_doc.get('is_active', True):
            return generate_response(False, 'Account is inactive', None, 401)
        
        # Update last login
        User.update_last_login(db, str(user_doc['_id']))
        
        # Create JWT token
        access_token = create_access_token(
            identity=str(user_doc['_id']),
            expires_delta=timedelta(days=30)
        )
        
        # Prepare user response
        user_data = serialize_mongo_doc(user_doc)
        user_data.pop('password', None)
        
        Logger.info(f"User logged in: {data['email']}")
        
        return generate_response(
            True,
            'Login successful',
            {
                'token': access_token,
                'user': user_data
            },
            200
        )
    
    except Exception as e:
        Logger.error(f"Login error: {str(e)}")
        return generate_response(False, 'Login failed', None, 500)


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return generate_response(False, 'Email required', None, 400)
        
        # Check if user exists
        user_doc = User.find_by_email(db, data['email'])
        if not user_doc:
            # Don't reveal if email exists (security best practice)
            return generate_response(
                True,
                'If email exists, reset link has been sent',
                None,
                200
            )
        
        # TODO: Generate reset token and send email
        # For now, just return success
        
        Logger.info(f"Password reset requested for: {data['email']}")
        
        return generate_response(
            True,
            'Password reset link sent to email',
            None,
            200
        )
    
    except Exception as e:
        Logger.error(f"Forgot password error: {str(e)}")
        return generate_response(False, 'Request failed', None, 500)


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    try:
        user_id = get_jwt_identity()
        Logger.info(f"User logged out: {user_id}")
        
        return generate_response(True, 'Logout successful', None, 200)
    
    except Exception as e:
        Logger.error(f"Logout error: {str(e)}")
        return generate_response(False, 'Logout failed', None, 500)