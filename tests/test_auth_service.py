"""
Unit tests for authentication service
"""
import pytest
from datetime import datetime, timedelta
from src.services.auth import AuthService, JWT_SECRET_KEY, JWT_ALGORITHM
from src.models.user import User
import jwt

class TestAuthService:
    
    def test_generate_tokens(self):
        """Test token generation"""
        user_id = 1
        tokens = AuthService.generate_tokens(user_id)
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['token_type'] == 'Bearer'
        assert tokens['expires_in'] > 0
        
        # Verify access token
        access_payload = jwt.decode(
            tokens['access_token'], 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM]
        )
        assert access_payload['user_id'] == user_id
        assert access_payload['type'] == 'access'
        
        # Verify refresh token
        refresh_payload = jwt.decode(
            tokens['refresh_token'], 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM]
        )
        assert refresh_payload['user_id'] == user_id
        assert refresh_payload['type'] == 'refresh'
    
    def test_verify_valid_token(self):
        """Test verification of valid token"""
        user_id = 1
        tokens = AuthService.generate_tokens(user_id)
        
        # Verify access token
        payload = AuthService.verify_token(tokens['access_token'])
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['type'] == 'access'
        
        # Verify refresh token
        payload = AuthService.verify_token(tokens['refresh_token'], token_type='refresh')
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['type'] == 'refresh'
    
    def test_verify_expired_token(self):
        """Test verification of expired token"""
        # Create expired token
        expired_payload = {
            'user_id': 1,
            'type': 'access',
            'iat': datetime.utcnow() - timedelta(days=2),
            'exp': datetime.utcnow() - timedelta(days=1)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        # Verify returns None for expired token
        payload = AuthService.verify_token(expired_token)
        assert payload is None
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        invalid_token = 'invalid.token.here'
        
        payload = AuthService.verify_token(invalid_token)
        assert payload is None
    
    def test_verify_wrong_token_type(self):
        """Test verification with wrong token type"""
        tokens = AuthService.generate_tokens(1)
        
        # Try to verify access token as refresh token
        payload = AuthService.verify_token(tokens['access_token'], token_type='refresh')
        assert payload is None
        
        # Try to verify refresh token as access token
        payload = AuthService.verify_token(tokens['refresh_token'], token_type='access')
        assert payload is None
    
    def test_authenticate_user_success(self, app):
        """Test successful user authentication"""
        with app.app_context():
            # Create test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass123')
            
            # Mock database query
            User.query.filter_by = lambda **kwargs: type('obj', (object,), {
                'first': lambda: user if kwargs.get('username') == 'testuser' else None
            })()
            
            # Test authentication
            authenticated = AuthService.authenticate_user('testuser', 'testpass123')
            assert authenticated is not None
            assert authenticated.username == 'testuser'
    
    def test_authenticate_user_wrong_password(self, app):
        """Test authentication with wrong password"""
        with app.app_context():
            # Create test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass123')
            
            # Mock database query
            User.query.filter_by = lambda **kwargs: type('obj', (object,), {
                'first': lambda: user if kwargs.get('username') == 'testuser' else None
            })()
            
            # Test authentication with wrong password
            authenticated = AuthService.authenticate_user('testuser', 'wrongpass')
            assert authenticated is None
    
    def test_authenticate_nonexistent_user(self, app):
        """Test authentication with non-existent user"""
        with app.app_context():
            # Mock database query to return None
            User.query.filter_by = lambda **kwargs: type('obj', (object,), {
                'first': lambda: None
            })()
            
            # Test authentication
            authenticated = AuthService.authenticate_user('nouser', 'anypass')
            assert authenticated is None
    
    def test_create_user_success(self, app, db):
        """Test successful user creation"""
        with app.app_context():
            # Ensure user doesn't exist
            existing = User.query.filter_by(username='newuser').first()
            if existing:
                db.session.delete(existing)
                db.session.commit()
            
            # Create new user
            user = AuthService.create_user(
                username='newuser',
                email='new@example.com',
                password='newpass123',
                role='user'
            )
            
            assert user is not None
            assert user.username == 'newuser'
            assert user.email == 'new@example.com'
            assert user.role == 'user'
            assert user.check_password('newpass123')
    
    def test_create_duplicate_username(self, app, db):
        """Test creating user with duplicate username"""
        with app.app_context():
            # Create first user
            user1 = AuthService.create_user(
                username='duplicate',
                email='user1@example.com',
                password='pass123'
            )
            
            # Try to create second user with same username
            with pytest.raises(ValueError, match="Username already exists"):
                AuthService.create_user(
                    username='duplicate',
                    email='user2@example.com',
                    password='pass123'
                )
    
    def test_create_duplicate_email(self, app, db):
        """Test creating user with duplicate email"""
        with app.app_context():
            # Create first user
            user1 = AuthService.create_user(
                username='user1',
                email='duplicate@example.com',
                password='pass123'
            )
            
            # Try to create second user with same email
            with pytest.raises(ValueError, match="Email already exists"):
                AuthService.create_user(
                    username='user2',
                    email='duplicate@example.com',
                    password='pass123'
                )