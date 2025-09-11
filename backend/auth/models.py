import uuid
import bcrypt
from datetime import datetime
from services.mongodb import mongodb
from pymongo.errors import DuplicateKeyError
import logging

logger = logging.getLogger(__name__)

class User:
    def __init__(self, email, name, password_hash=None, user_id=None, created_at=None, last_login=None, role='user'):
        self.user_id = user_id or str(uuid.uuid4())
        self.email = email.lower()
        self.name = name
        self.password_hash = password_hash
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login
        self.role = role  # 'admin' or 'user'
        self.datasets = []
        self.query_history = []
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def verify_password(self, password):
        """Verify a password against the hash"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)
    
    def to_dict(self, include_password=False):
        """Convert user object to dictionary"""
        user_dict = {
            '_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'datasets': self.datasets,
            'query_history': self.query_history
        }
        
        if include_password and self.password_hash:
            user_dict['password_hash'] = self.password_hash
            
        return user_dict
    
    @classmethod
    def from_dict(cls, data):
        """Create user object from dictionary"""
        return cls(
            email=data['email'],
            name=data['name'],
            password_hash=data.get('password_hash'),
            user_id=data.get('_id'),
            created_at=data.get('created_at'),
            last_login=data.get('last_login'),
            role=data.get('role', 'user')
        )
    
    def save(self):
        """Save or update user in database"""
        try:
            users_collection = mongodb.get_collection('users')
            
            # Create unique index on email if it doesn't exist
            users_collection.create_index("email", unique=True)
            
            user_data = self.to_dict(include_password=True)
            
            # Try to insert new user
            try:
                result = users_collection.insert_one(user_data)
                logger.info(f"✅ Created new user in MongoDB: {self.email} (ID: {self.user_id})")
                return True
            except DuplicateKeyError:
                # User exists, update instead
                result = users_collection.update_one(
                    {'_id': self.user_id},
                    {'$set': user_data}
                )
                if result.matched_count > 0:
                    logger.info(f"📝 Updated existing user in MongoDB: {self.email}")
                    return True
                else:
                    logger.error(f"❌ Failed to update user in MongoDB: {self.email}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error saving user: {str(e)}")
            return False
    
    def update_last_login(self):
        """Update user's last login timestamp"""
        try:
            self.last_login = datetime.utcnow()
            users_collection = mongodb.get_collection('users')
            
            result = users_collection.update_one(
                {'_id': self.user_id},
                {'$set': {'last_login': self.last_login}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
            return False
    
    def add_dataset(self, dataset_info):
        """Add dataset metadata to user document"""
        try:
            users_collection = mongodb.get_collection('users')
            
            # Add timestamp to dataset info
            dataset_info['upload_date'] = datetime.utcnow()
            
            result = users_collection.update_one(
                {'_id': self.user_id},
                {'$push': {'datasets': dataset_info}}
            )
            
            if result.modified_count > 0:
                self.datasets.append(dataset_info)
                logger.info(f"📊 Added dataset '{dataset_info['name']}' for user {self.email}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding dataset: {str(e)}")
            return False
    
    def remove_dataset(self, dataset_id):
        """Remove dataset from user document"""
        try:
            users_collection = mongodb.get_collection('users')
            
            result = users_collection.update_one(
                {'_id': self.user_id},
                {'$pull': {'datasets': {'dataset_id': dataset_id}}}
            )
            
            if result.modified_count > 0:
                self.datasets = [d for d in self.datasets if d['dataset_id'] != dataset_id]
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing dataset: {str(e)}")
            return False
    
    def update_dataset(self, dataset_id, update_data):
        """Update dataset metadata in user document"""
        try:
            users_collection = mongodb.get_collection('users')
            
            # Build update query for nested array element
            update_fields = {}
            for key, value in update_data.items():
                update_fields[f'datasets.$.{key}'] = value
            
            result = users_collection.update_one(
                {'_id': self.user_id, 'datasets.dataset_id': dataset_id},
                {'$set': update_fields}
            )
            
            if result.modified_count > 0:
                # Update local copy
                for dataset in self.datasets:
                    if dataset['dataset_id'] == dataset_id:
                        dataset.update(update_data)
                        break
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating dataset: {str(e)}")
            return False
    
    def add_query_to_history(self, query_info):
        """Add query to user's history"""
        try:
            users_collection = mongodb.get_collection('users')
            
            # Add timestamp and unique ID to query
            query_info['query_id'] = str(uuid.uuid4())
            query_info['timestamp'] = datetime.utcnow()
            
            result = users_collection.update_one(
                {'_id': self.user_id},
                {'$push': {'query_history': query_info}}
            )
            
            if result.modified_count > 0:
                self.query_history.append(query_info)
                logger.info(f"🔍 Added query to history for user {self.email}: '{query_info['query'][:50]}...'")
                return query_info['query_id']
            return None
            
        except Exception as e:
            logger.error(f"Error adding query to history: {str(e)}")
            return None
    
    def clear_query_history(self):
        """Clear all query history for this user"""
        try:
            users_collection = mongodb.get_collection('users')
            
            result = users_collection.update_one(
                {'_id': self.user_id},
                {'$set': {'query_history': []}}
            )
            
            if result.modified_count > 0:
                self.query_history = []
                logger.info(f"🗑️ Cleared query history for user {self.email}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error clearing query history: {str(e)}")
            return False
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        try:
            users_collection = mongodb.get_collection('users')
            user_data = users_collection.find_one({'email': email.lower()})
            
            if user_data:
                user = User.from_dict(user_data)
                user.datasets = user_data.get('datasets', [])
                user.query_history = user_data.get('query_history', [])
                logger.info(f"👤 Found user in MongoDB: {email} ({len(user.datasets)} datasets, {len(user.query_history)} queries)")
                return user
            else:
                logger.info(f"👤 User not found in MongoDB: {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            return None
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        try:
            users_collection = mongodb.get_collection('users')
            user_data = users_collection.find_one({'_id': user_id})
            
            if user_data:
                user = User.from_dict(user_data)
                user.datasets = user_data.get('datasets', [])
                user.query_history = user_data.get('query_history', [])
                return user
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            return None
    
    @staticmethod
    def create_user(email, name, password, role='user'):
        """Create a new user with hashed password"""
        try:
            # Check if user already exists
            if User.find_by_email(email):
                return None, "User with this email already exists"
            
            # Create user with hashed password
            password_hash = User.hash_password(password)
            user = User(email=email, name=name, password_hash=password_hash, role=role)
            
            if user.save():
                return user, None
            else:
                return None, "Failed to create user"
                
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None, str(e)
    
    def get_dataset_by_id(self, dataset_id):
        """Get dataset metadata by ID"""
        for dataset in self.datasets:
            if dataset['dataset_id'] == dataset_id:
                return dataset
        return None
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def is_regular_user(self):
        """Check if user has regular user role"""
        return self.role == 'user'