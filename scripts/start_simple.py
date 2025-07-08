#!/usr/bin/env python3
"""
Simple startup script that avoids Python 3.13 compatibility issues
"""
import os
import sys
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models import db
from src.routes.user import user_bp
from src.routes.voice import voice_bp
from src.utils.port_config import get_standardized_port

# Create Flask app
app = Flask(__name__, static_folder='src/static')

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database - use SQLite for simplicity
db_path = os.path.join(os.path.dirname(__file__), 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# Initialize extensions
db.init_app(app)
CORS(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(voice_bp, url_prefix='/api/twilio')

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Voice agent API is running'})

# Serve static files
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Create tables
with app.app_context():
    db.create_all()
    print(f"✅ Database created at: {db_path}")

if __name__ == '__main__':
    port = get_standardized_port('backend')
    print(f"""
    🚀 Voice Agent Backend Starting...
    
    📍 API URL: http://localhost:{port}
    📍 Basic UI: http://localhost:{port}
    📍 Health Check: http://localhost:{port}/health
    
    ⚡ Endpoints:
    - POST /api/twilio/inbound - Incoming calls
    - POST /api/twilio/process/<call_sid> - Process voice
    - GET /api/users - User management
    
    🔧 Configuration: Standardized port management
    
    Press Ctrl+C to stop
    """)
    
    app.run(debug=True, port=port, use_reloader=False)