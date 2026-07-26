from bson import ObjectId
from datetime import datetime
import bcrypt

class User:
    """User model for MongoDB"""
    
    collection_name = 'users'
    
    def __init__(self, db, name: str, email: str, password: str):
        self.db = db
        self.name = name
        self.email = email
        self.password = self._hash_password(password)
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.last_login = None
        self.is_active = True
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(stored_hash: str, password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            'is_active': self.is_active
        }
    
    def create(self):
        """Create user in database"""
        result = self.db[self.collection_name].insert_one(self.to_dict())
        return str(result.inserted_id)
    
    @classmethod
    def find_by_email(cls, db, email: str):
        """Find user by email"""
        return db[cls.collection_name].find_one({'email': email})
    
    @classmethod
    def find_by_id(cls, db, user_id: str):
        """Find user by ID"""
        return db[cls.collection_name].find_one({'_id': ObjectId(user_id)})
    
    @classmethod
    def update(cls, db, user_id: str, data: dict):
        """Update user"""
        data['updated_at'] = datetime.utcnow()
        result = db[cls.collection_name].update_one(
            {'_id': ObjectId(user_id)},
            {'$set': data}
        )
        return result.modified_count > 0
    
    @classmethod
    def delete(cls, db, user_id: str):
        """Delete user"""
        result = db[cls.collection_name].delete_one({'_id': ObjectId(user_id)})
        return result.deleted_count > 0
    
    @classmethod
    def update_last_login(cls, db, user_id: str):
        """Update last login timestamp"""
        return cls.update(db, user_id, {'last_login': datetime.utcnow()})