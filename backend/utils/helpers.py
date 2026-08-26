from datetime import datetime, timedelta
from bson import ObjectId
import json

def generate_response(success, message, data=None, status_code=200):
    """Generate standardized API response"""
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    if not success:
        response['error'] = message
    if data is not None:
        response['data'] = data
    return response, status_code


def serialize_mongo_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    
    doc['_id'] = str(doc['_id'])
    
    # Convert datetime objects
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
        elif isinstance(value, ObjectId):
            doc[key] = str(value)
    
    return doc


def serialize_mongo_docs(docs):
    """Convert list of MongoDB documents to JSON-serializable format"""
    return [serialize_mongo_doc(doc) for doc in docs]


def calculate_accuracy(errors_count, total_words):
    """Calculate accuracy percentage"""
    if total_words == 0:
        return 100
    accuracy = ((total_words - errors_count) / total_words) * 100
    return round(max(0, min(100, accuracy)), 2)


def format_duration(seconds):
    """Format seconds to readable duration"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def get_session_summary(session_data):
    """Generate session summary from session data"""
    try:
        total_questions = session_data.get('questions_answered', 0)
        grammar_errors = session_data.get('grammar_errors', 0)
        pronunciation_errors = session_data.get('pronunciation_errors', 0)
        duration_seconds = session_data.get('duration_seconds', 0)
        total_words = session_data.get('total_words', 1)
        total_errors = session_data.get('total_errors', 0)
        
        # Calculate accuracy
        accuracy = 100
        if total_words > 0:
            accuracy = max(0, 100 - (total_errors * 100 / total_words))
        
        # Format time
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        
        if hours > 0:
            time_str = f"{hours}h {minutes}m"
        elif minutes > 0:
            time_str = f"{minutes}m {seconds}s"
        else:
            time_str = f"{seconds}s"
        
        return {
            'totalQuestions': total_questions,
            'grammarErrors': grammar_errors,
            'pronunciationErrors': pronunciation_errors,
            'totalTime': time_str,
            'accuracy': round(accuracy, 1)
        }
    except Exception as e:
        Logger.error(f"Error generating session summary: {str(e)}")
        return {
            'totalQuestions': 0,
            'grammarErrors': 0,
            'pronunciationErrors': 0,
            'totalTime': '0s',
            'accuracy': 0
        }


class Logger:
    """Simple logger"""
    @staticmethod
    def info(message):
        print(f"[INFO] {datetime.now().isoformat()} - {message}")
    
    @staticmethod
    def error(message):
        print(f"[ERROR] {datetime.now().isoformat()} - {message}")
    
    @staticmethod
    def warning(message):
        print(f"[WARNING] {datetime.now().isoformat()} - {message}")