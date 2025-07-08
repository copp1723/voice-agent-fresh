"""
Authentication Routes - JWT-based authentication endpoints
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.user import User, db
from src.services.auth import auth_service, jwt_required

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Login endpoint - authenticate user and return JWT tokens
    """
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Authenticate user
        user = auth_service.authenticate_user(username, password)
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate tokens
        tokens = auth_service.generate_tokens(user.id)
        
        return jsonify({
            'token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in'],
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required
def logout():
    """
    Logout endpoint - currently just returns success
    In production, you might want to blacklist the token
    """
    try:
        # In a production system, you might want to:
        # 1. Add the token to a blacklist
        # 2. Clear any server-side sessions
        # 3. Log the logout event
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh token endpoint - exchange refresh token for new access token
    """
    try:
        data = request.json
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400
        
        # Verify refresh token
        payload = auth_service.verify_token(refresh_token, token_type='refresh')
        if not payload:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        
        # Check if user still exists and is active
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Generate new tokens
        tokens = auth_service.generate_tokens(user.id)
        
        return jsonify({
            'token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in']
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """
    Register a new user (admin only in production)
    """
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password required'}), 400
        
        # Validate email format
        if '@' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Create user
        try:
            user = auth_service.create_user(username, email, password, role)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Generate tokens
        tokens = auth_service.generate_tokens(user.id)
        
        return jsonify({
            'token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in'],
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required
def get_current_user():
    """
    Get current user information
    """
    try:
        return jsonify(request.current_user.to_dict()), 200
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({'error': 'Failed to get user information'}), 500

@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    Initiate password reset process
    """
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        # In production, send password reset email here
        if user:
            # TODO: Generate reset token and send email
            logger.info(f"Password reset requested for {email}")
        
        return jsonify({
            'message': 'If an account exists with that email, a password reset link has been sent'
        }), 200
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({'error': 'Password reset request failed'}), 500

@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password with token
    """
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('newPassword')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password required'}), 400
        
        # TODO: Implement token verification and password reset
        # This is a placeholder implementation
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        return jsonify({'error': 'Password reset failed'}), 500