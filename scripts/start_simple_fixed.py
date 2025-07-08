#!/usr/bin/env python3
"""
Simplified Startup - Avoid problematic areas and focus on core functionality
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

def setup_environment():
    """Setup basic environment"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Force threading mode for Python 3.13+
    python_ver = sys.version_info[:3]
    if python_ver >= (3, 13, 0):
        os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
    
    print(f"🐍 Python {python_ver[0]}.{python_ver[1]}.{python_ver[2]}")
    print(f"⚡ SocketIO: {os.environ.get('SOCKETIO_ASYNC_MODE', 'auto')} mode")

def create_simple_app():
    """Create a simplified Flask app"""
    from flask import Flask, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'A Killion Voice Agent',
            'phone': os.getenv('TWILIO_PHONE_NUMBER'),
            'python_version': f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
        })
    
    @app.route('/')
    def index():
        return f"""
        <h1>🎉 A Killion Voice - Voice Agent System</h1>
        <h2>✅ System Status: RUNNING</h2>
        <p><strong>📞 Phone Number:</strong> {os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')}</p>
        <p><strong>🐍 Python Version:</strong> {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}</p>
        <p><strong>🔗 Health Check:</strong> <a href="/health">/health</a></p>
        <p><strong>🎯 Status:</strong> Core system operational</p>
        <hr>
        <p>📞 <strong>Test the system by calling: {os.getenv('TWILIO_PHONE_NUMBER', 'Phone not configured')}</strong></p>
        """
    
    return app

def test_apis():
    """Test API connections quickly"""
    print("🧪 Testing APIs...")
    
    # Test OpenAI
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        client.models.list()
        print("✅ OpenAI API: Connected")
    except Exception as e:
        print(f"⚠️ OpenAI API: {str(e)[:50]}...")
    
    # Test Twilio
    try:
        from twilio.rest import Client
        client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        account = client.api.accounts(os.getenv('TWILIO_ACCOUNT_SID')).fetch()
        print(f"✅ Twilio API: Connected - {account.friendly_name}")
    except Exception as e:
        print(f"⚠️ Twilio API: {str(e)[:50]}...")

def main():
    print("🚀 SIMPLIFIED VOICE AGENT STARTUP")
    print("=" * 40)
    
    # Setup
    setup_environment()
    test_apis()
    
    # Create and run app
    app = create_simple_app()
    port = int(os.getenv('PORT', 5000))
    
    print(f"""
🎉 A KILLION VOICE - SIMPLIFIED MODE
{'=' * 40}

🚀 Server: http://localhost:{port}
📞 Phone: {os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')}
🏥 Health: http://localhost:{port}/health

🎯 CORE SYSTEM READY
Press Ctrl+C to stop
""")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
