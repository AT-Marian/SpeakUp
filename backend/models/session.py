from bson import ObjectId
from datetime import datetime

class Session:
    """Practice session model"""
    
    collection_name = 'practice_sessions'
    
    def __init__(self, db, user_id: str, mode: str, role: str, industry: str):
        self.db = db
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.mode = mode  # 'interview' or 'meeting'
        self.role = role
        self.industry = industry
        self.started_at = datetime.utcnow()
        self.ended_at = None
        self.questions_answered = 0
        self.grammar_errors = 0
        self.pronunciation_errors = 0
        self.total_errors = 0
        self.total_words = 0
        self.duration_seconds = 0
        self.responses = []
        self.questions = []
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'user_id': self.user_id,
            'mode': self.mode,
            'role': self.role,
            'industry': self.industry,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'questions_answered': self.questions_answered,
            'grammar_errors': self.grammar_errors,
            'pronunciation_errors': self.pronunciation_errors,
            'total_errors': self.total_errors,
            'total_words': self.total_words,
            'duration_seconds': self.duration_seconds,
            'responses': self.responses,
            'questions': self.questions
        }
    
    def create(self):
        """Create session in database"""
        result = self.db[self.collection_name].insert_one(self.to_dict())
        return str(result.inserted_id)
    
    def finish(self):
        """Mark session as finished and calculate duration"""
        self.ended_at = datetime.utcnow()
        # Calculate duration in seconds
        if self.started_at and self.ended_at:
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
        print(f"[✓] Session finished - Duration: {self.duration_seconds} seconds")
    
    def save(self, session_id: str):
        """Save session to database"""
        data = self.to_dict()
        result = self.db[self.collection_name].update_one(
            {'_id': ObjectId(session_id)},
            {'$set': data}
        )
        return result.modified_count > 0
    
    @classmethod
    def find_by_id(cls, db, session_id: str):
        """Find session by ID"""
        return db[cls.collection_name].find_one({'_id': ObjectId(session_id)})
    
    @classmethod
    def find_user_sessions(cls, db, user_id: str, limit: int = 10):
        """Find user's sessions"""
        return list(db[cls.collection_name].find(
            {'user_id': ObjectId(user_id)}
        ).sort('started_at', -1).limit(limit))
    
    @classmethod
    def add_response(cls, db, session_id: str, response: dict):
        """Add response to session"""
        result = db[cls.collection_name].update_one(
            {'_id': ObjectId(session_id)},
            {'$push': {'responses': response}}
        )
        return result.modified_count > 0