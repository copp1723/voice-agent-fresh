"""
Fixed User Model - Consistent with other models
"""
from .database import db, BaseModel, register_model
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class User(BaseModel):
    """
    User model for authentication and access control
    Fixed to be consistent with other models
    """
    __tablename__ = 'user'
    
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user', nullable=False)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Set password hash"""
        try:
            self.password_hash = generate_password_hash(password)
        except Exception as e:
            logger.error(f"Error setting password for user {self.username}: {e}")
            raise

    def check_password(self, password):
        """Check if password matches"""
        try:
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            logger.error(f"Error checking password for user {self.username}: {e}")
            return False

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'lastLogin': self.last_login.isoformat() if self.last_login else None,
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data['passwordHash'] = self.password_hash
            
        return data
    
    def update_last_login(self):
        """Update last login timestamp"""
        try:
            self.last_login = datetime.utcnow()
            self.save()
        except Exception as e:
            logger.error(f"Error updating last login for user {self.username}: {e}")
    
    @classmethod
    def find_by_username(cls, username: str):
        """Find user by username"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_email(cls, email: str):
        """Find user by email"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def create_user(cls, username: str, email: str, password: str, role: str = 'user'):
        """Create a new user"""
        try:
            # Check if user already exists
            if cls.find_by_username(username):
                raise ValueError(f"Username {username} already exists")
            
            if cls.find_by_email(email):
                raise ValueError(f"Email {email} already exists")
            
            # Create user
            user = cls(username=username, email=email, role=role)
            user.set_password(password)
            user.save()
            
            logger.info(f"Created user: {username}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            raise


# Register model in the registry
register_model('User', User)

# Export model
__all__ = ['User']
