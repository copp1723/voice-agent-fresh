#!/usr/bin/env python3
"""
Python 3.13 Compatible Startup Script - Handles version compatibility automatically
"""
import os
import sys
import subprocess
import logging

# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    python_ver = sys.version_info[:3]
    logger.info(f"Python version: {python_ver[0]}.{python_ver[1]}.{python_ver[2]}")
    
    if python_ver < (3, 8, 0):
        logger.error("Python 3.8+ is required")
        return False
    
    if python_ver >= (3, 13, 0):
        logger.info("Python 3.13+ detected - using compatibility mode")
    else:
        logger.info("Python < 3.13 detected - using standard mode")
    
    return True

def install_compatible_packages():
    """Install packages compatible with current Python version"""
    logger.info("Checking package compatibility...")
    
    python_ver = sys.version_info[:3]
    
    # Test critical imports
    try:
        import flask
        import flask_socketio
        import sqlalchemy
        logger.info("Critical packages already installed")
        return True
    except ImportError as e:
        logger.warning(f"Missing packages: {e}")
        
        # Try to install compatible packages
        logger.info("Installing compatible packages...")
        
        if python_ver >= (3, 13, 0):
            requirements_file = "requirements-py313.txt"
        else:
            requirements_file = "requirements.txt"
        
        if os.path.exists(requirements_file):
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                              check=True, capture_output=True)
                logger.info("Packages installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install packages: {e}")
                return False
        else:
            logger.error(f"Requirements file not found: {requirements_file}")
            return False

def setup_environment():
    """Setup environment variables and configuration"""
    logger.info("Setting up environment...")
    
    # Set Python version environment variable
    python_ver = sys.version_info[:3]
    os.environ['PYTHON_VERSION'] = f"{python_ver[0]}.{python_ver[1]}.{python_ver[2]}"
    
    # Set compatibility mode
    if python_ver >= (3, 13, 0):
        os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
        os.environ['GUNICORN_WORKER_CLASS'] = 'gevent'
    else:
        os.environ['SOCKETIO_ASYNC_MODE'] = 'eventlet'
        os.environ['GUNICORN_WORKER_CLASS'] = 'eventlet'
    
    # Set default environment if not set
    if not os.getenv('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    logger.info(f"SocketIO mode: {os.environ.get('SOCKETIO_ASYNC_MODE')}")
    logger.info(f"Gunicorn worker: {os.environ.get('GUNICORN_WORKER_CLASS')}")

def test_compatibility():
    """Test that compatibility fixes work"""
    logger.info("Testing compatibility...")
    
    try:
        from src.utils.compatibility import create_compatible_socketio, check_compatibility
        
        # Check compatibility
        compat_info = check_compatibility()
        logger.info(f"Compatibility check: {compat_info['python_version']}")
        
        # Test SocketIO creation
        socketio = create_compatible_socketio()
        logger.info("SocketIO created successfully")
        
        return True
    except Exception as e:
        logger.error(f"Compatibility test failed: {e}")
        return False

def start_server():
    """Start the Flask server with compatibility"""
    logger.info("Starting Flask server...")
    
    try:
        from src.main import create_app, socketio
        
        # Create app
        app = create_app()
        
        # Get port
        port = int(os.getenv('PORT', 5000))
        
        # Start server
        logger.info(f"Starting server on port {port}...")
        logger.info(f"SocketIO mode: {socketio.async_mode}")
        
        print(f"""
🚀 Voice Agent Server Starting (Python {sys.version_info[:3]})
        
📍 Server URL: http://localhost:{port}
📍 Health Check: http://localhost:{port}/health
📍 API Base: http://localhost:{port}/api
        
🔧 Configuration:
   - Python Version: {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}
   - SocketIO Mode: {socketio.async_mode}
   - Flask Environment: {os.getenv('FLASK_ENV', 'development')}
        
⚡ Endpoints:
   - POST /api/twilio/inbound - Incoming calls
   - GET /api/calls - Call history
   - GET /api/agents - Agent configurations
        
Press Ctrl+C to stop
""")
        
        # Use socketio.run for WebSocket support
        socketio.run(app, host='0.0.0.0', port=port, debug=True, use_reloader=False)
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🐍 Python 3.13 Compatible Voice Agent Server")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install compatible packages
    if not install_compatible_packages():
        logger.error("Failed to install required packages")
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Test compatibility
    if not test_compatibility():
        logger.error("Compatibility test failed")
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
