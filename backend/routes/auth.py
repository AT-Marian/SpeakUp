from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import secrets
import os

from models.user import User
from utils.validators import validate_email, validate_password, validate_name
from utils.helpers import generate_response, serialize_mongo_doc, Logger
from utils.email_service import send_password_reset_email

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# MongoDB database instance (passed from app.py)
db = None

def set_database(database):
    global db
    db = database


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('name') or not data.get('email') or not data.get('password'):
            return generate_response(False, 'Missing required fields', None, 400)
        
        email = data['email'].strip().lower()
        name = data['name'].strip()

        # Validate email
        if not validate_email(email):
            return generate_response(False, 'Invalid email format', None, 400)
        
        # Validate name
        valid, msg = validate_name(name)
        if not valid:
            return generate_response(False, msg, None, 400)
        
        # Validate password
        valid, msg = validate_password(data['password'])
        if not valid:
            return generate_response(False, msg, None, 400)
        
        # Check if user exists
        if User.find_by_email(db, email):
            return generate_response(False, 'Email already registered', None, 409)
        
        # Create user
        user = User(db, name, email, data['password'])
        user_id = user.create()
        
        Logger.info(f"New user registered: {email}")
        
        return generate_response(
            True,
            'User registered successfully',
            {'user_id': user_id, 'email': email},
            201
        )
    
    except Exception as e:
        Logger.error(f"Registration error: {str(e)}")
        return generate_response(False, 'Registration failed', None, 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('email') or not data.get('password'):
            return generate_response(False, 'Email and password required', None, 400)
        
        email = data['email'].strip().lower()

        # Find user
        user_doc = User.find_by_email(db, email)
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
        user_data = serialize_mongo_doc(user_doc) or {}
        if isinstance(user_data, dict):
            user_data.pop('password', None)
        
        Logger.info(f"User logged in: {email}")
        
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
    """Request password reset link"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return generate_response(False, 'Email is required', None, 400)
        
        email = data['email'].strip().lower()
        
        # Check if user exists
        user_doc = User.find_by_email(db, email)
        if not user_doc:
            # Security: return success to prevent user enumeration
            return generate_response(
                True,
                'If an account with that email exists, a password reset link has been sent.',
                None,
                200
            )
        
        # Generate secure random token with 1-hour expiry
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        
        # Persist token in database
        db['users'].update_one(
            {'_id': user_doc['_id']},
            {'$set': {'reset_token': token, 'reset_token_expires': expires}}
        )
        
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password?token={token}"
        user_name = user_doc.get('name', '').split()[0] if user_doc.get('name') else 'User'

        print(f"\n[→] Sending password reset email to: {email}")
        print(f"[→] Reset URL: {reset_url}\n")

        # Attempt to send real email
        email_sent = send_password_reset_email(
            to_email=email,
            reset_url=reset_url,
            user_name=user_name
        )

        if email_sent:
            Logger.info(f"Password reset email sent to {email}")
            return generate_response(
                True,
                'Password reset link has been sent to your email address!',
                {'reset_url': reset_url, 'token': token},
                200
            )
        else:
            # Email not configured or failed — return link in response for dev testing
            print(f"\n{'='*70}")
            print(f"[RESET LINK - Email service fallback]")
            print(f"Test this URL in browser:")
            print(f"{reset_url}")
            print(f"{'='*70}\n")
            
            return generate_response(
                True,
                'Password reset link created.',
                {'reset_url': reset_url, 'token': token},
                200
            )
    
    except Exception as e:
        Logger.error(f"Forgot password error: {str(e)}")
        import traceback
        traceback.print_exc()
        return generate_response(False, 'Failed to process password reset request', None, 500)


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token"""
    if db is None:
        return generate_response(False, 'Database connection is not available', None, 500)

    try:
        data = request.get_json()
        
        if not data or not data.get('token') or not data.get('password'):
            return generate_response(False, 'Token and new password are required', None, 400)
        
        token = data['token'].strip()
        new_password = data['password']
        
        # Validate password format
        valid, msg = validate_password(new_password)
        if not valid:
            return generate_response(False, msg, None, 400)
        
        # Find user with matching token
        user_doc = db['users'].find_one({'reset_token': token})
        
        if not user_doc:
            return generate_response(False, 'Invalid or expired password reset token', None, 400)
        
        # Check token expiration
        expires = user_doc.get('reset_token_expires')
        if not expires:
            return generate_response(False, 'Invalid password reset token', None, 400)

        if isinstance(expires, str):
            try:
                expires = datetime.fromisoformat(expires)
            except ValueError:
                return generate_response(False, 'Invalid token expiration format', None, 400)

        now = datetime.now(expires.tzinfo) if expires.tzinfo is not None else datetime.utcnow()

        if expires < now:
            return generate_response(False, 'Password reset token has expired. Please request a new link.', None, 400)
        
        # Hash new password and update user in database
        hashed_password = User._hash_password(new_password)
        
        db['users'].update_one(
            {'_id': user_doc['_id']},
            {
                '$set': {'password': hashed_password, 'updated_at': datetime.utcnow()},
                '$unset': {'reset_token': '', 'reset_token_expires': ''}
            }
        )
        
        Logger.info(f"Password reset successful for user: {user_doc.get('email')}")
        
        return generate_response(
            True,
            'Password has been reset successfully! You can now log in with your new password.',
            None,
            200
        )
    
    except Exception as e:
        Logger.error(f"Reset password error: {str(e)}")
        return generate_response(False, 'Failed to reset password', None, 500)


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