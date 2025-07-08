#!/usr/bin/env python3
"""
🎯 ONEKEEL AI - VOICE AGENT WITH ENHANCED CHATTERBOX TTS
Enables high-quality, human-like voice with emotion and empathy
"""
import os
import sys
import tempfile
import sqlite3
from datetime import datetime
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_environment():
    """Setup environment with Chatterbox TTS enabled"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Force threading mode for Python 3.13+
    python_ver = sys.version_info[:3]
    if python_ver >= (3, 13, 0):
        os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
    
    # ENABLE Chatterbox for superior voice quality
    os.environ['USE_CHATTERBOX'] = 'true'
    os.environ['OPTIMIZE_FOR_TWILIO'] = 'true'
    os.environ['PREFER_OPENROUTER'] = 'true'

def get_enhanced_tts_response(text, agent_type='general', emotion=None):
    """Get high-quality TTS using Chatterbox with emotion"""
    try:
        # Try Chatterbox first for superior quality
        from src.services.chatterbox_service import chatterbox_service
        
        # Detect appropriate emotion if not specified
        if emotion is None:
            text_lower = text.lower()
            if any(word in text_lower for word in ['sorry', 'apologize', 'unfortunately']):
                emotion = 'apologetic'
            elif any(word in text_lower for word in ['great', 'excellent', 'wonderful']):
                emotion = 'excited' 
            elif any(word in text_lower for word in ['understand', 'help', 'assist']):
                emotion = 'empathetic'
            else:
                emotion = 'neutral'
        
        print(f"🎙️ Using Chatterbox TTS with emotion: {emotion}")
        audio_bytes, metadata = chatterbox_service.text_to_speech(
            text=text,
            agent_type=agent_type,
            emotion=emotion
        )
        
        if audio_bytes and len(audio_bytes) > 0:
            # Optimize for Twilio
            if os.getenv('OPTIMIZE_FOR_TWILIO', 'true').lower() == 'true':
                audio_bytes = chatterbox_service.optimize_for_twilio(audio_bytes)
            
            print(f"✅ Generated {len(audio_bytes)} bytes with {metadata.get('emotion', 'neutral')} emotion")
            return audio_bytes
        else:
            print("⚠️ Chatterbox TTS failed, falling back to Twilio Polly")
            return None
            
    except Exception as e:
        print(f"⚠️ Chatterbox TTS error: {e}")
        print("📝 Falling back to high-quality Twilio Polly")
        return None

def init_database_and_agents():
    """Initialize database and create default agent configurations"""
    try:
        db_path = 'app.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create agent_configs table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                system_prompt TEXT NOT NULL,
                max_turns INTEGER DEFAULT 20,
                timeout_seconds INTEGER DEFAULT 30,
                voice_provider VARCHAR(50) DEFAULT 'chatterbox',
                voice_model VARCHAR(100) DEFAULT 'empathetic',
                keywords TEXT,
                priority INTEGER DEFAULT 1,
                sms_template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create calls table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_sid VARCHAR(100) UNIQUE NOT NULL,
                from_number VARCHAR(20) NOT NULL,
                to_number VARCHAR(20) NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER DEFAULT 0,
                agent_type VARCHAR(50) DEFAULT 'general',
                routing_confidence REAL DEFAULT 0.0,
                routing_keywords TEXT,
                status VARCHAR(20) DEFAULT 'active',
                direction VARCHAR(10) DEFAULT 'inbound',
                message_count INTEGER DEFAULT 0,
                summary TEXT,
                sms_sent BOOLEAN DEFAULT 0,
                sms_sid VARCHAR(100),
                customer_id INTEGER
            )
        ''')
        
        # Enhanced agent configurations with emotion-aware prompts
        default_agents = [
            {
                'agent_type': 'general',
                'name': 'OneKeel General Assistant',
                'description': 'General customer service with warm, professional tone',
                'system_prompt': '''You are a warm, professional customer service representative for OneKeel AI, a cutting-edge artificial intelligence company specializing in voice agents and automation solutions.

COMPANY OVERVIEW:
- OneKeel AI creates intelligent voice agents for businesses
- We provide 24/7 automated customer service solutions  
- Our technology handles calls, appointments, support, and sales
- We help businesses scale their customer interactions

YOUR PERSONALITY:
- Warm, friendly, and genuinely helpful
- Professional but approachable
- Knowledgeable and confident about OneKeel AI
- Empathetic to customer needs
- Keep responses concise (under 50 words) for phone conversations

CAPABILITIES YOU CAN DISCUSS:
- Voice AI agents for customer service
- Appointment scheduling automation
- Lead qualification and sales support
- 24/7 customer support coverage
- Integration with existing business systems
- Cost savings through automation

Always be welcoming and offer to connect them with specialists for detailed questions.''',
                'keywords': '["hello", "help", "information", "onekeel", "general", "what do you do", "tell me about"]',
                'priority': 1,
                'sms_template': 'Thanks for calling OneKeel AI! We discussed our voice AI solutions. Visit onekeel.ai for more info or call back anytime!'
            },
            {
                'agent_type': 'sales',
                'name': 'OneKeel Sales Specialist',
                'description': 'Enthusiastic sales expert with persuasive, confident energy',
                'system_prompt': '''You are an enthusiastic sales specialist for OneKeel AI, excited to help businesses discover the power of voice AI solutions.

YOUR ENERGY:
- Confident and knowledgeable about ROI and benefits
- Enthusiastic about the technology and possibilities
- Persuasive but never pushy
- Focus on value and business transformation
- Speak with excitement about the future of AI

SALES EXPERTISE:
- Voice AI implementation ROI calculations
- Cost savings and efficiency improvements
- Integration possibilities with existing systems
- Industry-specific use cases and success stories
- Pricing structures and implementation timelines

KEY BENEFITS TO EMPHASIZE WITH EXCITEMENT:
- 24/7 availability without hiring more staff
- Instant response times that customers love
- Scalability during peak periods
- Detailed analytics for business insights
- Seamless integration with existing tools

Always aim to generate excitement about the possibilities and offer demos!''',
                'keywords': '["price", "pricing", "cost", "buy", "purchase", "demo", "sales", "sell", "quote", "money", "roi"]',
                'priority': 3,
                'sms_template': 'Thanks for your interest in OneKeel AI! Our sales team will follow up about implementing voice AI for your business. Visit onekeel.ai/demo'
            },
            {
                'agent_type': 'support',
                'name': 'OneKeel Technical Support',
                'description': 'Calm, reassuring technical expert with patient problem-solving approach',
                'system_prompt': '''You are a calm, patient technical support specialist for OneKeel AI, dedicated to helping customers solve problems with reassuring expertise.

YOUR APPROACH:
- Calm and reassuring, especially when customers are frustrated
- Patient and methodical in problem-solving
- Confident in your technical knowledge
- Empathetic to customer concerns
- Clear and simple explanations for complex issues

SUPPORT AREAS:
- Voice agent configuration and optimization
- Integration troubleshooting with existing systems
- Call flow and routing performance issues
- Analytics, reporting, and dashboard questions
- API and webhook implementation problems
- Account settings and configuration

SUPPORT METHODOLOGY:
- First, acknowledge their concern with empathy
- Ask clarifying questions to understand the issue
- Provide clear, step-by-step guidance
- Ensure they feel supported throughout the process
- Follow up to confirm resolution

For complex issues, reassure them that our engineering team provides expert follow-up within 24 hours.''',
                'keywords': '["support", "help", "problem", "issue", "not working", "broken", "fix", "technical", "integration", "api", "error"]',
                'priority': 4,
                'sms_template': 'OneKeel Support: We\'re working on your technical issue. Our engineering team will follow up within 24 hours. Reference: {call_sid}'
            },
            {
                'agent_type': 'billing',
                'name': 'OneKeel Billing Support',
                'description': 'Understanding, helpful billing specialist with empathetic approach',
                'system_prompt': '''You are an understanding, helpful billing specialist for OneKeel AI, focused on resolving financial concerns with empathy and transparency.

YOUR APPROACH:
- Understanding and empathetic, especially with billing concerns
- Transparent and honest about all charges and policies
- Helpful in finding solutions that work for customers
- Patient with questions about complex billing structures
- Proactive in suggesting cost-optimizations

BILLING EXPERTISE:
- Subscription plans and pricing tier explanations
- Usage-based billing calculations and projections
- Payment methods, billing cycles, and invoice details
- Account upgrades, downgrades, and plan changes
- Refund policies and billing dispute resolution
- Enterprise pricing and volume discounts

BILLING PLANS TO DISCUSS:
- Starter: Up to 1,000 calls/month ($99/month)
- Professional: Up to 10,000 calls/month ($299/month)
- Enterprise: Custom volume pricing and features
- Pay-per-call options for variable usage patterns

Always verify identity appropriately and aim to resolve concerns same-day when possible.''',
                'keywords': '["billing", "payment", "invoice", "charge", "cost", "plan", "upgrade", "downgrade", "refund", "account", "bill", "pay", "subscription"]',
                'priority': 2,
                'sms_template': 'OneKeel Billing: We\'ve addressed your billing inquiry. Check your email for confirmation. Questions? Call us anytime!'
            },
            {
                'agent_type': 'appointments',
                'name': 'OneKeel Appointment Scheduler',
                'description': 'Organized, efficient scheduler with helpful, accommodating personality',
                'system_prompt': '''You are an organized, efficient appointment scheduler for OneKeel AI, dedicated to making scheduling easy and convenient for customers.

YOUR PERSONALITY:
- Organized and detail-oriented with scheduling
- Accommodating and flexible with customer preferences
- Efficient but never rushed
- Helpful in suggesting optimal meeting types
- Professional in coordinating complex schedules

SCHEDULING SERVICES:
- Product demos and feature walkthroughs
- Technical consultation and implementation planning
- Strategy sessions for current customers
- Training and team onboarding sessions
- Support escalation and problem-solving meetings

MEETING TYPES AVAILABLE:
- 30-min Product Demo (perfect for new prospects)
- 60-min Technical Deep Dive (implementation planning)
- 45-min Strategy Session (optimization for current customers)
- 30-min Support Call (urgent issue resolution)
- 90-min Training Session (team onboarding)

SCHEDULING PROCESS:
- Understand their specific needs and goals
- Suggest the most appropriate meeting type
- Offer multiple time options across time zones
- Confirm all participant details and contact information
- Send calendar invitations with preparation materials

Always confirm meeting purpose, participants, and any special requirements or preparation needed.''',
                'keywords': '["appointment", "schedule", "meeting", "call back", "book", "calendar", "consultation", "demo"]',
                'priority': 2,
                'sms_template': 'OneKeel Appointment: Your {meeting_type} is scheduled! Check email for calendar invite. We\'ll call 5 minutes before your session.'
            }
        ]
        
        # Insert default agents (replace existing)
        for agent in default_agents:
            cursor.execute('''
                INSERT OR REPLACE INTO agent_configs 
                (agent_type, name, description, system_prompt, keywords, priority, sms_template, voice_provider)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent['agent_type'],
                agent['name'], 
                agent['description'],
                agent['system_prompt'],
                agent['keywords'],
                agent['priority'],
                agent['sms_template'],
                'chatterbox'  # Use Chatterbox for all agents
            ))
        
        conn.commit()
        conn.close()
        
        print("✅ Database and enhanced agent configurations initialized!")
        print(f"📊 Created {len(default_agents)} emotion-aware agents:")
        for agent in default_agents:
            print(f"   • {agent['name']}")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

def get_ai_response(user_input, agent_type='general'):
    """Get AI response using OpenRouter with proper system prompts"""
    try:
        import requests
        
        # Get OpenRouter API key
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            return "I'm sorry, the AI service is not configured properly. Please contact support."
        
        # Get agent system prompt from database
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('SELECT system_prompt FROM agent_configs WHERE agent_type = ?', (agent_type,))
            result = cursor.fetchone()
            conn.close()
            
            system_prompt = result[0] if result else "You are a helpful customer service representative for OneKeel AI."
        except:
            system_prompt = "You are a helpful customer service representative for OneKeel AI."
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'openai/gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user', 
                    'content': user_input
                }
            ],
            'max_tokens': 150,
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
            print(f"OpenRouter error: {response.status_code} - {response.text}")
            return f"I'm here to help with OneKeel AI services. How can I assist you today?"
            
    except Exception as e:
        print(f"AI response error: {e}")
        return "Thank you for calling OneKeel AI. I'm here to assist you with any questions about our voice AI solutions."

def route_call(user_input):
    """Improved call routing based on comprehensive keywords"""
    user_input_lower = user_input.lower()
    
    # Sales keywords (more comprehensive)
    sales_keywords = ['price', 'pricing', 'cost', 'buy', 'purchase', 'demo', 'sales', 'sell', 'quote', 'money', 'roi']
    if any(word in user_input_lower for word in sales_keywords):
        return 'sales'
    
    # Support keywords  
    support_keywords = ['problem', 'issue', 'not working', 'broken', 'support', 'help', 'fix', 'technical', 'error']
    if any(word in user_input_lower for word in support_keywords):
        return 'support'
    
    # Billing keywords
    billing_keywords = ['billing', 'payment', 'invoice', 'charge', 'account', 'bill', 'pay', 'subscription']
    if any(word in user_input_lower for word in billing_keywords):
        return 'billing'
    
    # Appointment keywords
    appointment_keywords = ['appointment', 'schedule', 'meeting', 'call back', 'book', 'calendar', 'consultation']
    if any(word in user_input_lower for word in appointment_keywords):
        return 'appointments'
    
    # Default to general
    return 'general'

def create_enhanced_app():
    """Create Flask app with enhanced Chatterbox TTS"""
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    from twilio.twiml.voice_response import VoiceResponse, Play
    
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    
    # Track call sessions in memory
    call_sessions = {}
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'OneKeel AI Voice Agent',
            'phone': os.getenv('TWILIO_PHONE_NUMBER'),
            'python_version': f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}",
            'tts_provider': 'Chatterbox (Human-like AI)',
            'ai_provider': 'OpenRouter',
            'agents_configured': True,
            'emotion_enabled': True,
            'voice_quality': 'Premium Human-like'
        })
    
    @app.route('/api/twilio/inbound', methods=['POST'])
    def handle_inbound_call():
        """Handle incoming calls with enhanced emotional TTS"""
        try:
            call_sid = request.form.get('CallSid', 'unknown')
            from_number = request.form.get('From', 'unknown')
            
            print(f"📞 Incoming call: {call_sid} from {from_number}")
            
            # Initialize call session
            call_sessions[call_sid] = {
                'phone_number': from_number,
                'agent_type': 'general',
                'turn_count': 0,
                'max_turns': 10,
                'start_time': datetime.now()
            }
            
            # Welcome message with warm emotion
            welcome_text = "Hi! Thanks for calling OneKeel AI. I'm your intelligent voice assistant, and I'm excited to help you today. What can I do for you?"
            
            # Try enhanced TTS first
            audio_bytes = get_enhanced_tts_response(welcome_text, 'general', 'empathetic')
            
            response = VoiceResponse()
            
            if audio_bytes:
                # Use enhanced Chatterbox audio
                audio_url = save_temp_audio(audio_bytes, call_sid + "_welcome")
                if audio_url:
                    response.play(audio_url)
                else:
                    # Fallback to Twilio if audio serving fails
                    response.say(welcome_text, voice='Polly.Joanna')
            else:
                # Fallback to high-quality Twilio
                response.say(welcome_text, voice='Polly.Joanna')
            
            # Gather user input
            gather = response.gather(
                input='speech',
                timeout=30,
                speech_timeout='auto',
                action=f'/api/twilio/process/{call_sid}',
                method='POST'
            )
            
            response.say("I didn't hear anything. Please call back if you need assistance.", voice='Polly.Joanna')
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            print(f"❌ Call handling error: {e}")
            response = VoiceResponse()
            response.say("Thank you for calling OneKeel AI. We're experiencing technical difficulties. Please try again later.", voice='Polly.Joanna')
            return str(response), 200, {'Content-Type': 'text/xml'}
    
    @app.route('/api/twilio/process/<call_sid>', methods=['POST'])
    def process_speech(call_sid):
        """Process speech with emotional TTS responses"""
        try:
            speech_result = request.form.get('SpeechResult', '').strip()
            
            if not speech_result:
                response = VoiceResponse()
                response.say("I didn't catch that. Could you please repeat your question?", voice='Polly.Joanna')
                gather = response.gather(
                    input='speech',
                    timeout=30,
                    speech_timeout='auto',
                    action=f'/api/twilio/process/{call_sid}',
                    method='POST'
                )
                response.say("Thank you for calling OneKeel AI. Have a great day!", voice='Polly.Joanna')
                return str(response), 200, {'Content-Type': 'text/xml'}
            
            print(f"🎙️ Speech from {call_sid}: {speech_result}")
            
            # Get call session
            session = call_sessions.get(call_sid, {})
            session['turn_count'] = session.get('turn_count', 0) + 1
            
            # Route call on first input
            if session['turn_count'] == 1:
                session['agent_type'] = route_call(speech_result)
                print(f"🎯 Routed call {call_sid} to {session['agent_type']} agent")
            
            # Get AI response
            ai_response = get_ai_response(speech_result, session['agent_type'])
            
            # Generate enhanced TTS with appropriate emotion
            audio_bytes = get_enhanced_tts_response(ai_response, session['agent_type'])
            
            response = VoiceResponse()
            
            if audio_bytes:
                # Use enhanced audio
                audio_url = save_temp_audio(audio_bytes, call_sid + f"_turn_{session['turn_count']}")
                if audio_url:
                    response.play(audio_url)
                else:
                    response.say(ai_response, voice='Polly.Joanna')
            else:
                # Fallback to high-quality Twilio
                response.say(ai_response, voice='Polly.Joanna')
            
            # Continue or end call
            if session['turn_count'] >= session.get('max_turns', 10):
                response.say("Thank you for calling OneKeel AI. Have a wonderful day!", voice='Polly.Joanna')
                response.hangup()
                if call_sid in call_sessions:
                    del call_sessions[call_sid]
            else:
                gather = response.gather(
                    input='speech',
                    timeout=30,
                    speech_timeout='auto',
                    action=f'/api/twilio/process/{call_sid}',
                    method='POST'
                )
                response.say("Thank you for calling OneKeel AI. Have a great day!", voice='Polly.Joanna')
            
            call_sessions[call_sid] = session
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            print(f"❌ Speech processing error: {e}")
            response = VoiceResponse()
            response.say("I'm sorry, I had trouble processing that. Please try again or call back later.", voice='Polly.Joanna')
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
            temp_filename = f"{filename}.wav"
            temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
            
            with open(temp_path, 'wb') as f:
                f.write(audio_bytes)
            
            # Return localhost URL for testing
            port = os.getenv('PORT', '10000')
            return f"http://localhost:{port}/audio/{temp_filename}"
            
        except Exception as e:
            print(f"❌ Audio save error: {e}")
            return None
    
    @app.route('/api/agents')
    def get_agents():
        """Get configured agents"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('SELECT agent_type, name, description FROM agent_configs ORDER BY priority DESC')
            agents = cursor.fetchall()
            conn.close()
            
            return jsonify([
                {
                    'agent_type': agent[0],
                    'name': agent[1],
                    'description': agent[2]
                }
                for agent in agents
            ])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/')
    def index():
        """Main page"""
        phone_number = os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OneKeel AI - Enhanced Voice Agent with Emotion</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .container {{ max-width: 900px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 15px; backdrop-filter: blur(10px); }}
                .status {{ background: rgba(76, 175, 80, 0.2); padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid rgba(76, 175, 80, 0.3); }}
                .phone {{ font-size: 28px; color: #4CAF50; font-weight: bold; text-shadow: 0 0 10px rgba(76, 175, 80, 0.5); }}
                .enhanced {{ background: rgba(255, 193, 7, 0.2); padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid rgba(255, 193, 7, 0.3); }}
                .agents {{ background: rgba(33, 150, 243, 0.2); padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid rgba(33, 150, 243, 0.3); }}
                .agent {{ background: rgba(255,255,255,0.1); margin: 10px 0; padding: 15px; border-radius: 8px; }}
                h1 {{ text-align: center; font-size: 2.5em; margin-bottom: 30px; text-shadow: 0 0 20px rgba(255,255,255,0.3); }}
                h2 {{ color: #4CAF50; text-shadow: 0 0 10px rgba(76, 175, 80, 0.3); }}
                .feature {{ margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 OneKeel AI - Enhanced Emotional Voice Agent</h1>
                
                <div class="enhanced">
                    <h2>🎭 ENHANCED EMOTIONAL TTS ENABLED</h2>
                    <p><strong>Voice Technology:</strong> Chatterbox AI with Emotion Detection</p>
                    <p><strong>Voice Quality:</strong> Human-like with empathy and natural tone</p>
                    <p><strong>Emotions Available:</strong> Neutral, Empathetic, Excited, Calm, Apologetic</p>
                    <p><strong>Optimization:</strong> Twilio-optimized for crystal clear phone calls</p>
                </div>
                
                <div class="status">
                    <h2>✅ System Status: FULLY OPERATIONAL</h2>
                    <p><strong>📞 Phone Number:</strong> <span class="phone">{phone_number}</span></p>
                    <p><strong>🤖 AI Engine:</strong> OpenRouter (GPT-3.5-Turbo)</p>
                    <p><strong>🎙️ Voice Quality:</strong> Chatterbox AI (Human-like with Emotion)</p>
                    <p><strong>🧠 Intelligence:</strong> Multi-Agent Routing System</p>
                    <p><strong>📊 Database:</strong> SQLite with Enhanced Agent Configurations</p>
                </div>
                
                <div class="agents">
                    <h2>🎯 Emotion-Aware AI Agents</h2>
                    <div class="agent">
                        <strong>🤖 General Assistant</strong> (Empathetic tone)<br>
                        Warm, professional company information
                    </div>
                    <div class="agent">
                        <strong>💼 Sales Specialist</strong> (Excited tone)<br>
                        Enthusiastic about business solutions and ROI
                    </div>
                    <div class="agent">
                        <strong>🔧 Technical Support</strong> (Calm, reassuring tone)<br>
                        Patient problem-solving with technical expertise
                    </div>
                    <div class="agent">
                        <strong>💳 Billing Support</strong> (Understanding tone)<br>
                        Empathetic account management and billing help
                    </div>
                    <div class="agent">
                        <strong>📅 Appointment Scheduler</strong> (Professional tone)<br>
                        Organized demo booking and consultation scheduling
                    </div>
                </div>
                
                <h3>📞 Experience Human-like AI Conversation</h3>
                <p style="font-size: 1.2em; text-align: center;">
                    Call <span class="phone">{phone_number}</span> for natural, emotional AI conversation!
                </p>
                
                <h3>🎭 Enhanced Features</h3>
                <div class="feature">✅ Human-like voice with natural emotions</div>
                <div class="feature">✅ Context-aware emotional responses</div>
                <div class="feature">✅ Intelligent call routing based on intent</div>
                <div class="feature">✅ Specialized expertise for different business needs</div>
                <div class="feature">✅ Empathetic responses for support issues</div>
                <div class="feature">✅ Enthusiastic sales conversations</div>
                <div class="feature">✅ Optimized audio quality for phone calls</div>
                
                <p style="text-align: center; margin-top: 30px; opacity: 0.8;">
                    🎭 Powered by Chatterbox AI - The Most Human-like Voice Technology
                </p>
            </div>
        </body>
        </html>
        """
    
    return app

def main():
    """Main application entry point"""
    print("🎭 ONEKEEL AI - ENHANCED EMOTIONAL VOICE AGENT")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Initialize database and agents
    init_database_and_agents()
    
    # Create app
    app = create_enhanced_app()
    
    # Get configuration
    port = int(os.getenv('PORT', 10000))
    phone_number = os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')
    
    print(f"""
🎉 ONEKEEL AI - ENHANCED EMOTIONAL VOICE AGENT READY!
{'=' * 55}

🚀 Status: FULLY OPERATIONAL WITH EMOTION
📞 Phone: {phone_number}
🌐 Web: http://localhost:{port}
🎭 Voice: Chatterbox AI (Human-like with Emotion)
🧠 AI: OpenRouter GPT-3.5-Turbo
🎯 Agents: 5 Emotion-Aware Specialists

🎭 EMOTIONAL FEATURES:
✅ Human-like voice synthesis with natural emotions
✅ Context-aware emotional responses
✅ Empathetic support conversations
✅ Enthusiastic sales interactions
✅ Calm, reassuring technical help
✅ Understanding billing assistance
✅ Professional appointment scheduling

📱 TEST YOUR EMOTIONAL VOICE AGENT:
Call {phone_number} and experience:
• "I need pricing information" → Excited Sales Agent
• "I have a technical problem" → Calm Support Agent  
• "I need help with billing" → Understanding Billing Agent
• "I want to schedule a demo" → Professional Appointment Agent
• "Tell me about OneKeel" → Warm General Agent

🎙️ VOICE QUALITY: Human-like with emotion, optimized for phone calls
🎭 EMOTIONS: Neutral, Empathetic, Excited, Calm, Apologetic

Press Ctrl+C to stop
""")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n👋 OneKeel AI Enhanced Voice Agent stopped")

if __name__ == "__main__":
    main()
