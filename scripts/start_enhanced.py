#!/usr/bin/env python3
"""
Enhanced Voice Agent with Chatterbox TTS - Much better voice quality
"""
import os
import sys
import tempfile
import base64
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_environment():
    """Setup environment for Chatterbox TTS"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Force threading mode for Python 3.13+
    python_ver = sys.version_info[:3]
    if python_ver >= (3, 13, 0):
        os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
    
    # Enable Chatterbox
    os.environ['USE_CHATTERBOX'] = 'true'
    os.environ['OPTIMIZE_FOR_TWILIO'] = 'true'

def get_enhanced_tts_response(text):
    """Get high-quality TTS using available services"""
    try:
        # Try Chatterbox first
        from src.services.optional_tts_service import tts_service
        audio_bytes, metadata = tts_service.text_to_speech(text)
        
        if audio_bytes and len(audio_bytes) > 0:
            print(f"🎙️ Using {metadata.get('tts_service', 'unknown')} TTS")
            return audio_bytes
        else:
            print("⚠️ TTS service failed, using OpenAI TTS")
            return get_openai_tts(text)
            
    except Exception as e:
        print(f"⚠️ Enhanced TTS failed: {e}")
        return get_openai_tts(text)

def get_openai_tts(text):
    """Fallback to OpenAI TTS"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        return response.content
        
    except Exception as e:
        print(f"⚠️ OpenAI TTS failed: {e}")
        return None

def create_enhanced_app():
    """Create Flask app with enhanced TTS"""
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    from twilio.twiml.voice_response import VoiceResponse, Play
    import sqlite3
    
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'OneKeel AI Voice Agent',
            'phone': os.getenv('TWILIO_PHONE_NUMBER'),
            'python_version': f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}",
            'tts_enhanced': True,
            'chatterbox_enabled': os.getenv('USE_CHATTERBOX', 'false').lower() == 'true'
        })
    
    @app.route('/api/twilio/inbound', methods=['POST'])
    def handle_inbound_call():
        """Handle incoming Twilio calls with enhanced TTS"""
        try:
            # Get call data
            call_sid = request.form.get('CallSid', 'unknown')
            from_number = request.form.get('From', 'unknown')
            
            print(f"📞 Incoming call: {call_sid} from {from_number}")
            
            # Generate welcome message with enhanced TTS
            welcome_text = "Hi thanks for calling OneKeel AI, how can I assist you?"
            
            # Get high-quality audio
            audio_bytes = get_enhanced_tts_response(welcome_text)
            
            response = VoiceResponse()
            
            if audio_bytes:
                # Save audio temporarily and serve it
                audio_url = save_temp_audio(audio_bytes, call_sid + "_welcome")
                response.play(audio_url)
            else:
                # Fallback to Twilio TTS
                response.say(welcome_text, voice='Polly.Joanna')
            
            # Gather user input
            gather = response.gather(
                input='speech',
                timeout=30,
                speech_timeout='auto',
                action='/api/twilio/process'
            )
            
            # Fallback
            response.say("I didn't hear anything. Please call back if you need assistance.", voice='Polly.Joanna')
            
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            print(f"❌ Call handling error: {e}")
            
            # Emergency fallback
            response = VoiceResponse()
            response.say("Thank you for calling OneKeel AI. We're experiencing technical difficulties. Please try again later.", voice='Polly.Joanna')
            return str(response), 200, {'Content-Type': 'text/xml'}
    
    @app.route('/api/twilio/process', methods=['POST'])
    def process_speech():
        """Process speech with enhanced TTS response"""
        try:
            # Get speech input
            speech_result = request.form.get('SpeechResult', '')
            call_sid = request.form.get('CallSid', 'unknown')
            
            print(f"🎙️ Speech from {call_sid}: {speech_result}")
            
            # Get AI response
            ai_response = get_ai_response(speech_result)
            
            # Generate enhanced TTS
            audio_bytes = get_enhanced_tts_response(ai_response)
            
            response = VoiceResponse()
            
            if audio_bytes:
                # Use enhanced TTS
                audio_url = save_temp_audio(audio_bytes, call_sid + "_response")
                response.play(audio_url)
            else:
                # Fallback to Twilio TTS
                response.say(ai_response, voice='Polly.Joanna')
            
            # Continue conversation
            gather = response.gather(
                input='speech',
                timeout=30,
                speech_timeout='auto',
                action='/api/twilio/process'
            )
            
            response.say("Thank you for calling OneKeel AI. Have a great day!", voice='Polly.Joanna')
            
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            print(f"❌ Speech processing error: {e}")
            
            response = VoiceResponse()
            response.say("I'm sorry, I didn't understand that. Please try again or call back later.", voice='Polly.Joanna')
            return str(response), 200, {'Content-Type': 'text/xml'}
    
    @app.route('/audio/<filename>')
    def serve_audio(filename):
        """Serve temporary audio files"""
        try:
            audio_path = os.path.join(tempfile.gettempdir(), filename)
            if os.path.exists(audio_path):
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                return audio_data, 200, {'Content-Type': 'audio/wav'}
            else:
                return "Audio not found", 404
        except Exception as e:
            print(f"❌ Audio serving error: {e}")
            return "Audio error", 500
    
    def save_temp_audio(audio_bytes, filename):
        """Save audio temporarily and return URL"""
        try:
            # Save to temp file
            temp_filename = f"{filename}.wav"
            temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
            
            with open(temp_path, 'wb') as f:
                f.write(audio_bytes)
            
            # Return public URL
            ngrok_url = get_ngrok_url()
            return f"{ngrok_url}/audio/{temp_filename}"
            
        except Exception as e:
            print(f"❌ Audio save error: {e}")
            return None
    
    def get_ngrok_url():
        """Get the current ngrok URL"""
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                for tunnel in tunnels:
                    if tunnel['config']['addr'] == 'localhost:10000':
                        return tunnel['public_url']
            return 'https://your-ngrok-url.ngrok.io'  # fallback
        except:
            return 'https://your-ngrok-url.ngrok.io'  # fallback
    
    # Include other routes from original script...
    @app.route('/api/calls')
    def get_calls():
        """Get call history"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('SELECT call_sid, from_number, start_time, agent_type FROM calls ORDER BY start_time DESC LIMIT 10')
            calls = cursor.fetchall()
            conn.close()
            
            return jsonify({
                'calls': [
                    {
                        'call_sid': call[0],
                        'from_number': call[1], 
                        'start_time': call[2],
                        'agent_type': call[3]
                    } for call in calls
                ]
            })
        except Exception as e:
            return jsonify({'calls': [], 'error': str(e)})
    
    @app.route('/')
    def index():
        """Main page"""
        phone_number = os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OneKeel AI - Enhanced Voice Agent</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                .status {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .phone {{ font-size: 24px; color: #007bff; font-weight: bold; }}
                .enhanced {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 OneKeel AI - Enhanced Voice Agent</h1>
                
                <div class="enhanced">
                    <h2>🎙️ ENHANCED TTS ENABLED</h2>
                    <p><strong>Voice Quality:</strong> High-quality Chatterbox TTS</p>
                    <p><strong>Sound:</strong> Natural, human-like speech</p>
                    <p><strong>Optimization:</strong> Optimized for phone calls</p>
                </div>
                
                <div class="status">
                    <h2>✅ System Status: OPERATIONAL</h2>
                    <p><strong>📞 Phone Number:</strong> <span class="phone">{phone_number}</span></p>
                    <p><strong>🤖 AI Engine:</strong> OpenRouter</p>
                    <p><strong>🎙️ TTS:</strong> Chatterbox (Enhanced)</p>
                    <p><strong>📊 Database:</strong> SQLite</p>
                </div>
                
                <h3>📞 Test the Enhanced Voice System</h3>
                <p><strong>Call:</strong> <span class="phone">{phone_number}</span></p>
                <p>Experience natural, human-like AI conversation!</p>
                
                <h3>🎯 Enhanced Features</h3>
                <ul>
                    <li>✅ Natural voice synthesis</li>
                    <li>✅ Human-like speech patterns</li>
                    <li>✅ Optimized for phone quality</li>
                    <li>✅ AI conversation processing</li>
                    <li>✅ Real-time speech recognition</li>
                </ul>
            </div>
        </body>
        </html>
        """
    
    return app

def get_ai_response(user_input):
    """Get AI response using OpenRouter"""
    try:
        import requests
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            return "I'm sorry, the AI service is not configured properly."
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'openai/gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful customer service representative for OneKeel AI. Be friendly, professional, and concise. Keep responses under 50 words for phone conversations.'
                },
                {
                    'role': 'user', 
                    'content': user_input
                }
            ],
            'max_tokens': 150
        }
        
        response = requests.post('https://openrouter.ai/api/v1/chat/completions', 
                               headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "I'm here to help, but I'm having trouble processing your request right now."
            
    except Exception as e:
        print(f"AI response error: {e}")
        return "Thank you for calling OneKeel AI. I'm here to assist you with any questions you may have."

def main():
    print("🎙️ ONEKEEL AI - ENHANCED VOICE AGENT WITH CHATTERBOX TTS")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Create app
    app = create_enhanced_app()
    
    # Get port
    port = int(os.getenv('PORT', 10000))
    phone_number = os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')
    
    print(f"""
🎉 ONEKEEL AI - ENHANCED VOICE AGENT
{'=' * 40}

🚀 Status: RUNNING WITH ENHANCED TTS
📞 Phone: {phone_number}
🌐 Web: http://localhost:{port}
🎙️ TTS: Chatterbox (High Quality)

🎯 READY FOR NATURAL VOICE CALLS!
📱 Call {phone_number} for human-like AI conversation

Enhanced Features:
✅ Natural voice synthesis
✅ Human-like speech patterns  
✅ Optimized phone quality
✅ AI conversation processing
✅ Real-time speech recognition

Press Ctrl+C to stop
""")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n👋 OneKeel AI Enhanced Voice Agent stopped")

if __name__ == "__main__":
    main()
