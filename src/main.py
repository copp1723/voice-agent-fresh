"""
TODO: All voice processing is unified to EnhancedVoiceProcessor. If you need fallback/simple behavior, implement as a plugin or provider.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, current_app
from flask_cors import CORS
from flask_socketio import SocketIO
from src.models.database import init_database # Use new database initialization
from src.models.call import AgentConfig # Import fixed models
from src.middleware.security import configure_security
from src.utils.compatibility import create_compatible_socketio, log_compatibility_info
from src.utils.port_config import get_standardized_port

# SocketIO instance - automatically compatible with Python version
log_compatibility_info()
socketio = create_compatible_socketio()

# Blueprints need to be imported after app creation or within create_app
# from src.routes.user import user_bp
# from src.routes.voice import voice_bp

def create_app(config_name=None): # config_name can be 'testing', 'development', etc.
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    # Load base configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Environment-specific configuration
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('TEST_DATABASE_URL', "sqlite:///:memory:")
        # Any other test-specific configs
    else: # Development or Production
        app.config['TESTING'] = False
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            if database_url.startswith('postgres://'): # For Heroku/Render compatibility
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        else:
            # Default development database (SQLite file)
            db_dir = os.path.join(os.path.dirname(__file__), 'database')
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(db_dir, 'app.db')}"

    # Initialize extensions
    init_database(app) # Use new database initialization system
    CORS(app) # Enable CORS for all routes
    socketio.init_app(app) # Initialize SocketIO
    configure_security(app) # Configure security middleware

    # Import and register blueprints
    # It's common to do this inside create_app to avoid circular imports
    # and ensure they are registered on the correct app instance.
    from src.routes.user import user_bp
    from src.routes.voice import voice_bp
    from src.routes.auth import auth_bp
    from src.routes.dashboard import dashboard_bp
    from src.routes.customer import customer_bp
    from src.routes.reports import reports_bp
    # All voice processing is unified to EnhancedVoiceProcessor; ensure routes use that.
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(voice_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(customer_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')

    # Define the catch-all route for serving static files or index.html
    # This needs to be defined on the app instance created by create_app
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        # Use current_app here instead of a global 'app'
        static_folder_path = current_app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404
    
    # Create database tables and default data if needed
    # Note: Database initialization now handled by init_database(app)
    
    return app

# The global 'app' instance is removed. Code that needs an app instance
# (like the if __name__ == '__main__' block) should call create_app().

if __name__ == '__main__':
    app = create_app() # Create app for running locally
    port = get_standardized_port('backend')
    # FLASK_ENV is often used to control debug mode.
    # create_app can also take an env like 'development' or 'production'
    # to set app.debug directly or load different configs.
    debug_mode = os.getenv('FLASK_ENV', 'development') != 'production'
    print(f"🚀 Starting server on port {port} (standardized configuration)")
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode)
