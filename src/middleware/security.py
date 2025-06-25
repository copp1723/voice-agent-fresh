"""
Twilio Webhook Security - Request signature validation
"""
import os
import logging
from functools import wraps
from flask import request, abort
from twilio.request_validator import RequestValidator

logger = logging.getLogger(__name__)

def validate_twilio_request(f):
    """
    Decorator to validate Twilio webhook requests using signature verification
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip validation in development or if auth token not set
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        if not auth_token or os.getenv('FLASK_ENV') == 'development':
            logger.warning("Twilio signature validation skipped (development mode or missing auth token)")
            return f(*args, **kwargs)
        
        try:
            # Get Twilio signature from headers
            signature = request.headers.get('X-Twilio-Signature', '')
            
            # Get the full URL (Twilio uses the full URL for signature)
            url = request.url
            
            # Get form data for POST requests
            if request.method == 'POST':
                post_vars = request.form.to_dict()
            else:
                post_vars = {}
            
            # Validate the request
            validator = RequestValidator(auth_token)
            if validator.validate(url, post_vars, signature):
                logger.info(f"Twilio request validated for {request.endpoint}")
                return f(*args, **kwargs)
            else:
                logger.error(f"Invalid Twilio signature for {request.endpoint}")
                abort(403, "Invalid Twilio signature")
                
        except Exception as e:
            logger.error(f"Error validating Twilio request: {e}")
            abort(403, "Request validation failed")
    
    return decorated_function

def require_api_key(f):
    """
    Decorator to require API key for admin endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip in development
        if os.getenv('FLASK_ENV') == 'development':
            return f(*args, **kwargs)
        
        # Check for API key
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        expected_key = os.getenv('API_KEY')
        
        if not expected_key:
            logger.warning("API_KEY not configured - allowing request")
            return f(*args, **kwargs)
        
        if api_key != expected_key:
            logger.error(f"Invalid API key for {request.endpoint}")
            abort(401, "Invalid API key")
        
        return f(*args, **kwargs)
    
    return decorated_function

