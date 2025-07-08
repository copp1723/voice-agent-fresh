"""
Integration tests for authentication flow
"""
import pytest
import json
from src.models.user import User, db
from src.services.auth import AuthService

class TestAuthIntegration:
    
    def test_complete_auth_flow(self, client):
        """Test complete authentication flow: register, login, use token, refresh"""
        # 1. Register a new user
        register_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepass123'
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'token' in data
        assert 'refresh_token' in data
        assert 'user' in data
        assert data['user']['username'] == 'newuser'
        
        initial_token = data['token']
        refresh_token = data['refresh_token']
        
        # 2. Use the token to access protected endpoint
        headers = {
            'Authorization': f'Bearer {initial_token}',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/api/users/me', headers=headers)
        assert response.status_code == 200
        user_data = json.loads(response.data)
        assert user_data['username'] == 'newuser'
        
        # 3. Logout
        response = client.post('/api/auth/logout', headers=headers)
        assert response.status_code == 200
        
        # 4. Login with credentials
        login_data = {
            'username': 'newuser',
            'password': 'securepass123'
        }
        
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
        assert 'user' in data
        assert data['user']['username'] == 'newuser'
        
        new_token = data['token']
        
        # 5. Refresh token
        refresh_data = {
            'refresh_token': refresh_token
        }
        
        response = client.post(
            '/api/auth/refresh',
            data=json.dumps(refresh_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
        assert 'refresh_token' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        # Create a user first
        with client.application.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('correctpass')
            db.session.add(user)
            db.session.commit()
        
        # Try to login with wrong password
        login_data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        login_data = {
            'username': 'nouser',
            'password': 'anypass'
        }
        
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_access_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get('/api/users')
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        headers = {
            'Authorization': 'Bearer invalid.token.here',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/api/users', headers=headers)
        assert response.status_code == 401
    
    def test_register_duplicate_username(self, client):
        """Test registering with duplicate username"""
        # Register first user
        register_data = {
            'username': 'duplicate',
            'email': 'user1@example.com',
            'password': 'pass123'
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(register_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        # Try to register second user with same username
        register_data['email'] = 'user2@example.com'
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'already exists' in data['error'].lower()
    
    def test_refresh_with_invalid_token(self, client):
        """Test token refresh with invalid refresh token"""
        refresh_data = {
            'refresh_token': 'invalid.refresh.token'
        }
        
        response = client.post(
            '/api/auth/refresh',
            data=json.dumps(refresh_data),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_password_requirements(self, client):
        """Test password validation requirements"""
        register_data = {
            'username': 'shortpass',
            'email': 'short@example.com',
            'password': 'short'  # Less than 8 characters
        }
        
        response = client.post(
            '/api/auth/register',
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'at least 8 characters' in data['error']
    
    def test_role_based_access(self, client):
        """Test role-based access control"""
        # Create admin user
        with client.application.app_context():
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('adminpass')
            regular = User(username='regular', email='regular@example.com', role='user')
            regular.set_password('userpass')
            db.session.add_all([admin, regular])
            db.session.commit()
        
        # Login as regular user
        login_data = {'username': 'regular', 'password': 'userpass'}
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        regular_token = json.loads(response.data)['token']
        
        # Login as admin
        login_data = {'username': 'admin', 'password': 'adminpass'}
        response = client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        admin_token = json.loads(response.data)['token']
        
        # Try to create user as regular user (should fail)
        headers = {
            'Authorization': f'Bearer {regular_token}',
            'Content-Type': 'application/json'
        }
        user_data = {
            'username': 'newuser2',
            'email': 'new2@example.com',
            'password': 'pass12345'
        }
        
        response = client.post(
            '/api/users',
            data=json.dumps(user_data),
            headers=headers
        )
        assert response.status_code == 403  # Forbidden
        
        # Try same operation as admin (should succeed)
        headers['Authorization'] = f'Bearer {admin_token}'
        
        response = client.post(
            '/api/users',
            data=json.dumps(user_data),
            headers=headers
        )
        assert response.status_code == 201  # Created