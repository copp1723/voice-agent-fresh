"""
Python Version Compatibility Helper - Handles Python 3.13+ compatibility issues
"""
import sys
import logging

logger = logging.getLogger(__name__)

def get_python_version():
    """Get current Python version as a tuple"""
    return sys.version_info[:3]

def get_recommended_socketio_config():
    """
    Get recommended SocketIO configuration based on Python version
    """
    python_ver = get_python_version()
    
    if python_ver >= (3, 13, 0):
        # Python 3.13+ - use threading mode
        config = {
            'async_mode': 'threading',
            'cors_allowed_origins': "*",
            'logger': True,
            'engineio_logger': True
        }
        logger.info(f"Python {python_ver} detected - using threading mode for SocketIO")
        return config
    else:
        # Python < 3.13 - can use eventlet
        config = {
            'async_mode': 'eventlet',
            'cors_allowed_origins': "*",
            'logger': True,
            'engineio_logger': True
        }
        logger.info(f"Python {python_ver} detected - using eventlet mode for SocketIO")
        return config

def get_compatible_requirements():
    """
    Get Python version-specific requirements
    """
    python_ver = get_python_version()
    
    if python_ver >= (3, 13, 0):
        # Python 3.13+ compatible requirements
        return {
            'socketio_deps': [
                'flask-socketio>=5.3.6',
                'python-socketio>=5.11.0',
                # Skip eventlet for Python 3.13+
            ],
            'web_server': [
                'gunicorn>=21.2.0',
                # Use gevent instead of eventlet for gunicorn
                'gevent>=23.0.0',
            ]
        }
    else:
        # Python < 3.13 - can use eventlet
        return {
            'socketio_deps': [
                'flask-socketio>=5.3.6',
                'python-socketio>=5.11.0',
                'eventlet>=0.35.2',
            ],
            'web_server': [
                'gunicorn>=21.2.0',
                'eventlet>=0.35.2',
            ]
        }

def get_gunicorn_worker_class():
    """
    Get appropriate gunicorn worker class based on Python version
    """
    python_ver = get_python_version()
    
    if python_ver >= (3, 13, 0):
        # Python 3.13+ - use gevent instead of eventlet
        return 'gevent'
    else:
        # Python < 3.13 - can use eventlet
        return 'eventlet'

def check_compatibility():
    """
    Check current environment compatibility and provide recommendations
    """
    python_ver = get_python_version()
    
    issues = []
    recommendations = []
    
    if python_ver >= (3, 13, 0):
        # Check for eventlet usage
        try:
            import eventlet
            issues.append("eventlet is installed but may not work with Python 3.13+")
            recommendations.append("Consider using threading mode for SocketIO")
        except ImportError:
            pass
        
        # Check SocketIO configuration
        recommendations.append("Use async_mode='threading' for Flask-SocketIO")
        recommendations.append("Use 'gevent' worker class for gunicorn")
    
    return {
        'python_version': f"{python_ver[0]}.{python_ver[1]}.{python_ver[2]}",
        'compatible_with_eventlet': python_ver < (3, 13, 0),
        'issues': issues,
        'recommendations': recommendations
    }

def create_compatible_socketio():
    """
    Create SocketIO instance with compatible configuration
    """
    from flask_socketio import SocketIO
    
    config = get_recommended_socketio_config()
    
    try:
        socketio = SocketIO(**config)
        logger.info(f"SocketIO created successfully with {config['async_mode']} mode")
        return socketio
    except Exception as e:
        logger.error(f"Failed to create SocketIO with {config['async_mode']} mode: {e}")
        
        # Fallback to threading mode
        fallback_config = {
            'async_mode': 'threading',
            'cors_allowed_origins': "*",
            'logger': True,
            'engineio_logger': True
        }
        
        try:
            socketio = SocketIO(**fallback_config)
            logger.info("SocketIO created with fallback threading mode")
            return socketio
        except Exception as e2:
            logger.error(f"Failed to create SocketIO with fallback mode: {e2}")
            raise

def log_compatibility_info():
    """
    Log compatibility information for debugging
    """
    compat_info = check_compatibility()
    
    logger.info("=" * 50)
    logger.info("PYTHON COMPATIBILITY CHECK")
    logger.info("=" * 50)
    logger.info(f"Python Version: {compat_info['python_version']}")
    logger.info(f"Compatible with eventlet: {compat_info['compatible_with_eventlet']}")
    
    if compat_info['issues']:
        logger.warning("Issues found:")
        for issue in compat_info['issues']:
            logger.warning(f"  - {issue}")
    
    if compat_info['recommendations']:
        logger.info("Recommendations:")
        for rec in compat_info['recommendations']:
            logger.info(f"  - {rec}")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    # Run compatibility check
    log_compatibility_info()
    
    # Test SocketIO creation
    try:
        socketio = create_compatible_socketio()
        print("✅ SocketIO compatibility test passed")
    except Exception as e:
        print(f"❌ SocketIO compatibility test failed: {e}")
