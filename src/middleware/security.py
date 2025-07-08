"""
Security Middleware - Twilio validation and API authentication
"""
import os
import hmac
import hashlib
import base64
from functools import wraps
from flask import request, jsonify, current_app
from twilio.request_validator import RequestValidator
import logging

logger = logging.getLogger(__name__)

def validate_twilio_request(f):
    """
    Decorator to validate Twilio webhook requests using signature validation
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip validation in development mode
        if os.getenv('FLASK_ENV') == 'development':
            logger.info("Skipping Twilio validation in development mode")
            return f(*args, **kwargs)
        
        # Get Twilio auth token
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        if not auth_token:
            logger.error("TWILIO_AUTH_TOKEN not configured")
            return jsonify({'error': 'Server configuration error'}), 500
        
        # Create validator
        validator = RequestValidator(auth_token)
        
        # Get request data
        url = request.url
        params = request.form.to_dict()
        signature = request.headers.get('X-Twilio-Signature', '')
        
        # Validate signature
        if not validator.validate(url, params, signature):
            logger.warning(f"Invalid Twilio signature for URL: {url}")
            return jsonify({'error': 'Invalid request signature'}), 403
        
        logger.info(f"Valid Twilio request: {request.form.get('CallSid', 'unknown')}")
        return f(*args, **kwargs)
    
    return decorated_function

def require_api_key(f):
    """
    Decorator to require API key authentication for admin endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        # Get expected API key from environment
        expected_api_key = os.getenv('API_KEY')
        
        # Skip validation in development if no API key is configured
        if not expected_api_key and os.getenv('FLASK_ENV') == 'development':
            logger.info("Skipping API key validation in development mode")
            return f(*args, **kwargs)
        
        # Require API key in production
        if not api_key:
            logger.warning("Missing API key in request")
            return jsonify({'error': 'API key required'}), 401
        
        if not expected_api_key:
            logger.error("API_KEY not configured")
            return jsonify({'error': 'Server configuration error'}), 500
        
        # Validate API key using constant-time comparison
        if not hmac.compare_digest(api_key, expected_api_key):
            logger.warning(f"Invalid API key provided: {api_key[:8]}...")
            return jsonify({'error': 'Invalid API key'}), 403
        
        logger.info("Valid API key provided")
        return f(*args, **kwargs)
    
    return decorated_function

def validate_basic_auth(f):
    """
    Decorator for basic HTTP authentication (optional, for simple admin access)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        
        # Get basic auth credentials from environment
        username = os.getenv('BASIC_AUTH_USERNAME')
        password = os.getenv('BASIC_AUTH_PASSWORD')
        
        # Skip if not configured
        if not username or not password:
            return f(*args, **kwargs)
        
        # Validate credentials
        if not auth or not (auth.username == username and auth.password == password):
            logger.warning("Invalid basic auth credentials")
            return jsonify({'error': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(max_requests=60, window=60):
    """
    Simple rate limiting decorator (per IP)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # For production, you'd want to use Redis or a proper rate limiter
            # This is a simple in-memory implementation
            
            # Skip in development
            if os.getenv('FLASK_ENV') == 'development':
                return f(*args, **kwargs)
            
            # Get client IP
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            # Simple rate limiting logic would go here
            # For now, just log and continue
            logger.info(f"Rate limiting check for IP: {client_ip}")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def cors_headers(f):
    """
    Add CORS headers for API endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add CORS headers
        if hasattr(response, 'headers'):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
        
        return response
    
    return decorated_function

def log_request(f):
    """
    Log incoming requests for debugging
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Request: {request.method} {request.path}")
        if request.form:
            logger.info(f"Form data: {dict(request.form)}")
        if request.json:
            logger.info(f"JSON data: {request.json}")
        
        return f(*args, **kwargs)
    
    return decorated_function

# Security utility functions
def generate_api_key(length=32):
    """Generate a secure API key"""
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8')

def validate_phone_number(phone_number):
    """Basic phone number validation"""
    # Remove non-digits
    digits = ''.join(filter(str.isdigit, phone_number))
    
    # Check if it's a valid US/international number
    if len(digits) >= 10:
        return True
    
    return False

def sanitize_input(text, max_length=1000):
    """Sanitize user input"""
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Basic sanitization - remove potentially dangerous characters
    # For production, you'd want more sophisticated sanitization
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

# Security configuration helper
def configure_security(app):
    """Configure security settings for the Flask app"""
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Log security events
    logger.info("Security middleware configured")
    
    return app
