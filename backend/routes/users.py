from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.session import Session
from utils.validators import token_required, validate_email, validate_name
from datetime import datetime, timedelta  # ← ADD THIS LINE
from utils.helpers import generate_response, serialize_mongo_doc, Logger

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

# MongoDB database instance
db = None

def set_database(database):
    global db
    db = database


@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        
        # Get user
        user_doc = User.find_by_id(db, user_id)
        if not user_doc:
            return generate_response(False, 'User not found', None, 404)
        
        # Remove sensitive data
        user_data = serialize_mongo_doc(user_doc)
        user_data.pop('password', None)
        
        return generate_response(True, 'Profile retrieved', {'user': user_data}, 200)
    
    except Exception as e:
        Logger.error(f"Get profile error: {str(e)}")
        return generate_response(False, 'Failed to get profile', None, 500)


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate data
        update_data = {}
        
        if 'name' in data:
            valid, msg = validate_name(data['name'])
            if not valid:
                return generate_response(False, msg, None, 400)
            update_data['name'] = data['name']
        
        if 'email' in data:
            if not validate_email(data['email']):
                return generate_response(False, 'Invalid email', None, 400)
            
            # Check if email already used by another user
            existing = db['users'].find_one({
                'email': data['email'],
                '_id': {'$ne': ObjectId(user_id)}
            })
            if existing:
                return generate_response(False, 'Email already in use', None, 409)
            
            update_data['email'] = data['email']
        
        # Update user
        success = User.update(db, user_id, update_data)
        
        if not success:
            return generate_response(False, 'Failed to update profile', None, 500)
        
        Logger.info(f"Profile updated: {user_id}")
        
        return generate_response(True, 'Profile updated successfully', None, 200)
    
    except Exception as e:
        Logger.error(f"Update profile error: {str(e)}")
        return generate_response(False, 'Failed to update profile', None, 500)


@users_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Calculate dynamic stats and fetch recent history for the dashboard"""
    try:
        user_id = get_jwt_identity()
        
        # Fetch all completed sessions for this user
        sessions = list(db['practice_sessions'].find({
            'user_id': ObjectId(user_id),
            'questions_answered': {'$gt': 0}
        }).sort('started_at', -1))
        
        print(f"\n[→] Fetching stats for user {user_id}")
        print(f"[→] Found {len(sessions)} completed sessions")
        
        # 1. Calculate Sessions This Week
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        sessions_this_week = len([s for s in sessions if s.get('started_at', datetime.utcnow()) >= one_week_ago])
        
        # 2. Calculate Total Practice Time
        total_seconds = 0
        total_words = 0
        total_errors = 0
        recent_history = []
        
        for s in sessions:
            # Time calculation
            started = s.get('started_at')
            ended = s.get('ended_at')
            
            if started and ended:
                duration = (ended - started).total_seconds()
                total_seconds += duration
            
            # Accuracy calculation
            total_words += s.get('total_words', 0)
            total_errors += s.get('total_errors', 0)
            
            # Format recent history (limit to 3 for the dashboard)
            if len(recent_history) < 3:
                session_accuracy = 100 if s.get('total_words', 0) == 0 else max(0, 100 - (s.get('total_errors', 0) * 100 / s.get('total_words', 1)))
                
                try:
                    date_str = s.get('started_at').strftime('%b %d, %Y') if s.get('started_at') else 'Recently'
                except:
                    date_str = 'Recently'
                
                recent_history.append({
                    'id': str(s['_id']),
                    'role': s.get('role', 'Practice'),
                    'mode': s.get('mode', 'interview').capitalize(),
                    'date': date_str,
                    'accuracy': round(session_accuracy, 1)
                })
        
        # Format time dynamically
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        if hours > 0:
            practice_time = f"{hours}h {minutes}m"
        elif minutes > 0:
            practice_time = f"{minutes}m {seconds}s"
        else:
            practice_time = f"{seconds}s"
        
        # Calculate overall average accuracy
        avg_accuracy = 100
        if total_words > 0:
            avg_accuracy = max(0, 100 - (total_errors * 100 / total_words))
        
        print(f"[✓] Stats calculated:")
        print(f"    Sessions this week: {sessions_this_week}")
        print(f"    Practice time: {practice_time}")
        print(f"    Avg accuracy: {round(avg_accuracy, 1)}%")
        print(f"    Recent sessions: {len(recent_history)}")
        
        return jsonify({
            'sessionsThisWeek': sessions_this_week,
            'practiceTime': practice_time,
            'avgAccuracy': round(avg_accuracy, 1),
            'recentSessions': recent_history
        }), 200

    except Exception as e:
        print(f"[✗] Stats Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch stats'}), 500 


from bson import ObjectId