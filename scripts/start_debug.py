#!/usr/bin/env python3
"""
🔧 ONEKEEL AI - SIMPLIFIED WORKING VERSION 
Fixes the application error by ensuring robust webhook handling
"""
import os
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Load environment first
load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

def setup_environment():
    """Setup environment with fallback configuration"""
    # Force threading mode for Python 3.13+
    python_ver = sys.version_info[:3]
    if python_ver >= (3, 13, 0):
        os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
    
    # Use reliable TTS configuration
    os.environ['USE_CHATTERBOX'] = 'false'  # Start with reliable TTS first
    os.environ['PREFER_OPENROUTER'] = 'true'

def init_database_and_agents():
    """Initialize database with simple agent config"""
    try:
        db_path = 'app.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Simple agent configs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                system_prompt TEXT NOT NULL,
                keywords TEXT,
                priority INTEGER DEFAULT 1
            )
        ''')
        
        # Insert one working agent
        cursor.execute('''
            INSERT OR REPLACE INTO agent_configs 
            (agent_type, name, system_prompt, keywords, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'general',
            'OneKeel General Assistant',
            'You are a helpful customer service representative for OneKeel AI. Keep responses under 30 words for phone calls.',
            '["hello", "help", "general"]',
            1
        ))
        
        conn.commit()
        conn.close()
        print("✅ Database initialized with basic configuration")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def get_ai_response(user_input):
    """Simple AI response function"""
    try:
        import requests
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            return "Thank you for calling OneKeel AI. How can I help you today?"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'openai/gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful customer service representative for OneKeel AI. Keep responses under 30 words for phone calls.'
                },
                {
                    'role': 'user', 
                    'content': user_input
                }
            ],
            'max_tokens': 100,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions', 
            headers=headers, 
            json=data, 
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "I'm here to help with OneKeel AI services. What can I assist you with?"
            
    except Exception as e:
        print(f"AI response error: {e}")
        return "Thank you for calling OneKeel AI. How can I help you?"

def create_working_app():
    """Create a simple, reliable Flask app"""
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    from twilio.twiml.voice_response import VoiceResponse
    
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    
    # Simple call tracking
    call_sessions = {}
    
    @app.route('/health')
    def health():
        """Health check"""
        return jsonify({
            'status': 'healthy',
            'service': 'OneKeel AI Voice Agent',
            'phone': os.getenv('TWILIO_PHONE_NUMBER', 'Not configured'),
            'webhook_ready': True
        })
    
    @app.route('/api/twilio/inbound', methods=['POST'])
    def handle_inbound_call():
        """Handle incoming calls - simplified and robust"""
        try:
            # Get call information
            call_sid = request.form.get('CallSid', 'unknown')
            from_number = request.form.get('From', 'unknown')
            
            print(f"📞 Incoming call: {call_sid} from {from_number}")
            
            # Initialize session
            call_sessions[call_sid] = {
                'from': from_number,
                'turn_count': 0
            }
            
            # Create simple TwiML response
            response = VoiceResponse()
            response.say(
                "Hello! Thank you for calling OneKeel AI. How can I help you today?",
                voice='Polly.Joanna'
            )
            
            # Gather speech input
            gather = response.gather(
                input='speech',
                timeout=30,
                action=f'/api/twilio/process/{call_sid}',
                method='POST'
            )
            
            # Timeout message
            response.say("I didn't hear anything. Please call back. Goodbye!", voice='Polly.Joanna')
            response.hangup()
            
            print("✅ Generated TwiML response successfully")
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            print(f"❌ Inbound call error: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
            # Emergency fallback
            try:
                response = VoiceResponse()
                response.say("Thank you for calling OneKeel AI.", voice='alice')
                response.hangup()
                return str(response), 200, {'Content-Type': 'text/xml'}
            except:
                return "<?xml version='1.0' encoding='UTF-8'?><Response><Say>Thank you for calling.</Say><Hangup/></Response>", 200, {'Content-Type': 'text/xml'}
    
    @app.route('/api/twilio/process/<call_sid>', methods=['POST'])
    def process_speech(call_sid):
        """Process speech input - simplified"""
        try:
            # Get speech result
            speech_result = request.form.get('SpeechResult', '').strip()
            
            print(f"🎙️ Speech from {call_sid}: {speech_result}")
            
            # Get or create session
            session = call_sessions.get(call_sid, {'from': 'unknown', 'turn_count': 0})
            session['turn_count'] += 1
            
            if not speech_result:
                # No speech detected
                response = VoiceResponse()
                response.say("I didn't catch that. Could you repeat your question?", voice='Polly.Joanna')
                
                if session['turn_count'] < 3:
                    gather = response.gather(
                        input='speech',
                        timeout=30,
                        action=f'/api/twilio/process/{call_sid}',
                        method='POST'
                    )
                
                response.say("Thank you for calling OneKeel AI. Goodbye!", voice='Polly.Joanna')
                response.hangup()
                return str(response), 200, {'Content-Type': 'text/xml'}
            
            # Get AI response
            ai_response = get_ai_response(speech_result)
            
            # Create response
            response = VoiceResponse()
            response.say(ai_response, voice='Polly.Joanna')
            
            # Continue conversation or end
            if session['turn_count'] < 5:
                gather = response.gather(
                    input='speech',
                    timeout=30,
                    action=f'/api/twilio/process/{call_sid}',
                    method='POST'
                )
            
            response.say("Thank you for calling OneKeel AI. Have a great day!", voice='Polly.Joanna')
            response.hangup()
            
            # Update session
            call_sessions[call_sid] = session
            
            print("✅ Processed speech successfully")
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            print(f"❌ Speech processing error: {e}")
            import traceback
            traceback.print_exc()
            
            # Emergency fallback
            try:
                response = VoiceResponse()
                response.say("I'm sorry, I had trouble with that. Please try again.", voice='Polly.Joanna')
                response.hangup()
                return str(response), 200, {'Content-Type': 'text/xml'}
            except:
                return "<?xml version='1.0' encoding='UTF-8'?><Response><Say>Sorry, please try again.</Say><Hangup/></Response>", 200, {'Content-Type': 'text/xml'}
    
    @app.route('/api/twilio/status', methods=['POST'])
    def call_status():
        """Handle call status updates"""
        try:
            call_sid = request.form.get('CallSid', 'unknown')
            status = request.form.get('CallStatus', 'unknown')
            print(f"📊 Call {call_sid} status: {status}")
            
            # Clean up completed calls
            if status in ['completed', 'busy', 'failed', 'no-answer'] and call_sid in call_sessions:
                del call_sessions[call_sid]
            
            return '', 200
        except Exception as e:
            print(f"❌ Status callback error: {e}")
            return '', 200
    
    @app.route('/')
    def index():
        """Simple status page"""
        phone_number = os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OneKeel AI - Working Voice Agent</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                .status {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .phone {{ font-size: 24px; color: #007bff; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>OneKeel AI - Voice Agent Status</h1>
                
                <div class="status">
                    <h2>✅ System Status: OPERATIONAL</h2>
                    <p><strong>Phone Number:</strong> <span class="phone">{phone_number}</span></p>
                    <p><strong>Webhook URL:</strong> Working</p>
                    <p><strong>TTS:</strong> Twilio Polly</p>
                    <p><strong>AI:</strong> OpenRouter</p>
                </div>
                
                <h3>Test Instructions:</h3>
                <ol>
                    <li>Call <strong>{phone_number}</strong></li>
                    <li>Wait for the greeting</li>
                    <li>Speak clearly when prompted</li>
                    <li>The AI will respond to your questions</li>
                </ol>
                
                <p><strong>Active Sessions:</strong> {len(call_sessions) if 'call_sessions' in locals() else 0}</p>
            </div>
        </body>
        </html>
        """
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        print(f"❌ Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

def main():
    """Main function"""
    print("🔧 ONEKEEL AI - SIMPLIFIED WORKING VERSION")
    print("=" * 50)
    
    # Setup
    setup_environment()
    init_database_and_agents()
    
    # Create app
    app = create_working_app()
    
    # Configuration
    port = int(os.getenv('PORT', 10000))
    phone_number = os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')
    
    print(f"""
🚀 SIMPLIFIED VERSION STARTING
{'=' * 30}

📞 Phone: {phone_number}
🌐 Server: http://localhost:{port}
🎙️ Voice: Twilio Polly (Reliable)
🧠 AI: OpenRouter

🔧 DEBUGGING MODE:
- Simplified webhook handling
- Robust error recovery
- Detailed error logging
- Fallback responses

📱 TEST: Call {phone_number}

Server starting on port {port}...
""")
    
    try:
        # Start with debug mode for better error reporting
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=True,  # Enable debug mode
            use_reloader=False  # Prevent double startup
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
