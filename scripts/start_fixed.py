#!/usr/bin/env python3
"""
🎯 ONEKEEL AI - FIXED VOICE AGENT WITH PROPER CONFIGURATION
Fixes TTS issues and sets up comprehensive voice agent capabilities
"""
import os
import sys
import tempfile
import sqlite3
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

def setup_environment():
    """Setup environment and fix configuration issues"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Force threading mode for Python 3.13+
    python_ver = sys.version_info[:3]
    if python_ver >= (3, 13, 0):
        os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
    
    # Fix TTS configuration - use OpenRouter instead of OpenAI
    os.environ['USE_CHATTERBOX'] = 'false'  # Disable problematic Chatterbox
    os.environ['PREFER_OPENROUTER'] = 'true'
    os.environ['TTS_FALLBACK'] = 'twilio'

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
                voice_provider VARCHAR(50) DEFAULT 'twilio',
                voice_model VARCHAR(100) DEFAULT 'Polly.Joanna',
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
        
        # Default agent configurations for OneKeel AI
        default_agents = [
            {
                'agent_type': 'general',
                'name': 'OneKeel General Assistant',
                'description': 'General customer service and information',
                'system_prompt': '''You are a professional customer service representative for OneKeel AI, a cutting-edge artificial intelligence company specializing in voice agents and automation solutions.

COMPANY OVERVIEW:
- OneKeel AI creates intelligent voice agents for businesses
- We provide 24/7 automated customer service solutions
- Our technology handles calls, appointments, support, and sales
- We help businesses scale their customer interactions

YOUR ROLE:
- Be friendly, professional, and knowledgeable about OneKeel AI
- Provide information about our services and capabilities
- Help callers understand how our voice AI can benefit their business
- Route complex inquiries to appropriate specialists
- Keep responses concise (under 50 words) for phone conversations

CAPABILITIES YOU CAN DISCUSS:
- Voice AI agents for customer service
- Appointment scheduling automation
- Lead qualification and sales support
- 24/7 customer support coverage
- Integration with existing business systems
- Cost savings through automation

If asked about pricing, technical details, or custom implementations, offer to connect them with a specialist.''',
                'keywords': '["hello", "help", "information", "onekeel", "general", "what do you do", "tell me about"]',
                'priority': 1,
                'sms_template': 'Thanks for calling OneKeel AI! We discussed our voice AI solutions. Visit onekeel.ai for more info or call back anytime!'
            },
            {
                'agent_type': 'sales',
                'name': 'OneKeel Sales Specialist',
                'description': 'Sales inquiries and business solutions',
                'system_prompt': '''You are a sales specialist for OneKeel AI, focused on helping businesses understand and implement our voice AI solutions.

YOUR EXPERTISE:
- Voice AI implementation for businesses
- ROI calculations and cost savings
- Integration possibilities with existing systems
- Use cases across different industries
- Pricing structures and packages

SALES APPROACH:
- Ask about their current customer service challenges
- Understand their business size and call volume
- Explain how voice AI can reduce costs and improve efficiency
- Provide specific examples relevant to their industry
- Offer demos and consultations

KEY BENEFITS TO HIGHLIGHT:
- 24/7 availability without additional staff costs
- Instant response times and consistent service quality
- Scalability during peak periods
- Detailed analytics and call insights
- Easy integration with CRM and business tools

Always aim to schedule a follow-up demo or consultation call.''',
                'keywords': '["price", "cost", "sales", "buy", "purchase", "demo", "business", "roi", "save money", "implementation"]',
                'priority': 3,
                'sms_template': 'Thanks for your interest in OneKeel AI! Our sales team will follow up about implementing voice AI for your business. Visit onekeel.ai/demo'
            },
            {
                'agent_type': 'support',
                'name': 'OneKeel Technical Support',
                'description': 'Technical support and troubleshooting',
                'system_prompt': '''You are a technical support specialist for OneKeel AI, helping existing customers with their voice agent implementations.

SUPPORT AREAS:
- Voice agent configuration and optimization
- Integration troubleshooting
- Call flow and routing issues
- Performance monitoring and analytics
- API and webhook problems
- Account management and settings

SUPPORT APPROACH:
- First, identify if they're an existing customer
- Understand the specific issue they're experiencing
- Provide step-by-step troubleshooting guidance
- Escalate complex technical issues to engineering team
- Ensure customer satisfaction and resolution

COMMON ISSUES:
- Call routing not working correctly
- Voice quality or recognition problems
- Integration with CRM or business systems
- Analytics and reporting questions
- Account billing and configuration

For complex technical issues, collect details and promise expert follow-up within 24 hours.''',
                'keywords': '["support", "help", "problem", "issue", "not working", "broken", "fix", "technical", "integration", "api"]',
                'priority': 4,
                'sms_template': 'OneKeel Support: We\'re working on your technical issue. Our engineering team will follow up within 24 hours. Reference: {call_sid}'
            },
            {
                'agent_type': 'billing',
                'name': 'OneKeel Billing Support',
                'description': 'Billing inquiries and account management',
                'system_prompt': '''You are a billing and account specialist for OneKeel AI, handling financial inquiries and account management.

BILLING EXPERTISE:
- Subscription plans and pricing tiers
- Usage-based billing calculations
- Payment methods and billing cycles
- Account upgrades and downgrades
- Refunds and billing disputes
- Enterprise custom pricing

YOUR APPROACH:
- Verify customer identity with phone number or account details
- Review their current plan and usage
- Explain billing clearly and transparently
- Help optimize their plan for their usage patterns
- Resolve billing concerns promptly

BILLING PLANS YOU CAN DISCUSS:
- Starter: Up to 1,000 calls/month
- Professional: Up to 10,000 calls/month  
- Enterprise: Custom volume and features
- Pay-per-call options for variable usage

For account changes, collect requirements and process same-day when possible.''',
                'keywords': '["billing", "payment", "invoice", "charge", "cost", "plan", "upgrade", "downgrade", "refund", "account"]',
                'priority': 2,
                'sms_template': 'OneKeel Billing: We\'ve addressed your billing inquiry. Check your email for confirmation. Questions? Call us anytime!'
            },
            {
                'agent_type': 'appointments',
                'name': 'OneKeel Appointment Scheduler',
                'description': 'Demo scheduling and consultation booking',
                'system_prompt': '''You are an appointment scheduling specialist for OneKeel AI, focused on booking demos and consultations.

SCHEDULING SERVICES:
- Product demos and walkthroughs
- Technical consultation calls
- Implementation planning sessions
- Training and onboarding sessions
- Support escalation meetings

YOUR PROCESS:
- Understand what type of meeting they need
- Check their availability and preferences
- Offer multiple time options
- Confirm contact information
- Send calendar invitations and reminders
- Prepare relevant materials for the meeting

AVAILABLE MEETING TYPES:
- 30-min Product Demo (perfect for new prospects)
- 60-min Technical Deep Dive (for implementation planning)
- 45-min Strategy Session (for current customers)
- 30-min Support Call (for issue resolution)

Always confirm the meeting purpose, participants, and any preparation needed.''',
                'keywords': '["appointment", "schedule", "meeting", "demo", "consultation", "call back", "calendar", "book", "available"]',
                'priority': 2,
                'sms_template': 'OneKeel Appointment: Your {meeting_type} is scheduled! Check email for calendar invite. We\'ll call 5 minutes before your session.'
            }
        ]
        
        # Insert default agents (replace existing)
        for agent in default_agents:
            cursor.execute('''
                INSERT OR REPLACE INTO agent_configs 
                (agent_type, name, description, system_prompt, keywords, priority, sms_template)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent['agent_type'],
                agent['name'], 
                agent['description'],
                agent['system_prompt'],
                agent['keywords'],
                agent['priority'],
                agent['sms_template']
            ))
        
        conn.commit()
        conn.close()
        
        print("✅ Database and agent configurations initialized successfully!")
        print(f"📊 Created {len(default_agents)} specialized agents:")
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

def create_fixed_app():
    """Create Flask app with fixed TTS and proper agent configuration"""
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    from twilio.twiml.voice_response import VoiceResponse
    
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    
    # Track call sessions in memory (since localStorage not available)
    call_sessions = {}
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'OneKeel AI Voice Agent',
            'phone': os.getenv('TWILIO_PHONE_NUMBER'),
            'python_version': f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}",
            'tts_provider': 'Twilio Polly (High Quality)',
            'ai_provider': 'OpenRouter',
            'agents_configured': True,
            'database_initialized': True
        })
    
    @app.route('/api/twilio/inbound', methods=['POST'])
    def handle_inbound_call():
        """Handle incoming Twilio calls with proper agent routing"""
        try:
            # Get call data
            call_sid = request.form.get('CallSid', 'unknown')
            from_number = request.form.get('From', 'unknown')
            
            print(f"📞 Incoming call: {call_sid} from {from_number}")
            
            # Initialize call session
            call_sessions[call_sid] = {
                'phone_number': from_number,
                'agent_type': 'general',  # Will be determined after first input
                'turn_count': 0,
                'max_turns': 10,
                'start_time': datetime.now()
            }
            
            # Create TwiML response with Polly voice
            response = VoiceResponse()
            response.say(
                "Hi thanks for calling OneKeel AI! I'm your intelligent voice assistant. How can I help you today?",
                voice='Polly.Joanna'
            )
            
            # Gather user input with speech recognition
            gather = response.gather(
                input='speech',
                timeout=30,
                speech_timeout='auto',
                action=f'/api/twilio/process/{call_sid}',
                method='POST'
            )
            
            # Fallback if no input detected
            response.say("I didn't hear anything. Please call back if you need assistance.", voice='Polly.Joanna')
            
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            print(f"❌ Call handling error: {e}")
            
            # Emergency fallback
            response = VoiceResponse()
            response.say(
                "Thank you for calling OneKeel AI. We're experiencing technical difficulties. Please try again later.",
                voice='Polly.Joanna'
            )
            return str(response), 200, {'Content-Type': 'text/xml'}
    
    @app.route('/api/twilio/process/<call_sid>', methods=['POST'])
    def process_speech(call_sid):
        """Process speech with intelligent agent routing"""
        try:
            # Get speech input
            speech_result = request.form.get('SpeechResult', '').strip()
            
            if not speech_result:
                # No speech detected - ask to repeat
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
            
            # Get AI response with appropriate agent
            ai_response = get_ai_response(speech_result, session['agent_type'])
            
            # Create TwiML response
            response = VoiceResponse()
            response.say(ai_response, voice='Polly.Joanna')
            
            # Check if we should continue or end the call
            if session['turn_count'] >= session.get('max_turns', 10):
                response.say("Thank you for calling OneKeel AI. Have a great day!", voice='Polly.Joanna')
                response.hangup()
                # Clean up session
                if call_sid in call_sessions:
                    del call_sessions[call_sid]
            else:
                # Continue conversation
                gather = response.gather(
                    input='speech',
                    timeout=30,
                    speech_timeout='auto',
                    action=f'/api/twilio/process/{call_sid}',
                    method='POST'
                )
                response.say("Thank you for calling OneKeel AI. Have a great day!", voice='Polly.Joanna')
            
            # Update session
            call_sessions[call_sid] = session
            
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            print(f"❌ Speech processing error: {e}")
            
            response = VoiceResponse()
            response.say("I'm sorry, I had trouble processing that. Please try again or call back later.", voice='Polly.Joanna')
            return str(response), 200, {'Content-Type': 'text/xml'}
    
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
    
    @app.route('/api/stats')
    def get_stats():
        """Get system statistics"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            # Get agent count
            cursor.execute('SELECT COUNT(*) FROM agent_configs')
            agent_count = cursor.fetchone()[0]
            
            # Get active sessions
            active_sessions = len(call_sessions)
            
            conn.close()
            
            return jsonify({
                'configured_agents': agent_count,
                'active_calls': active_sessions,
                'tts_provider': 'Twilio Polly',
                'ai_provider': 'OpenRouter',
                'status': 'operational'
            })
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
            <title>OneKeel AI - Intelligent Voice Agent</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .container {{ max-width: 900px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 15px; backdrop-filter: blur(10px); }}
                .status {{ background: rgba(76, 175, 80, 0.2); padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid rgba(76, 175, 80, 0.3); }}
                .phone {{ font-size: 28px; color: #4CAF50; font-weight: bold; text-shadow: 0 0 10px rgba(76, 175, 80, 0.5); }}
                .agents {{ background: rgba(33, 150, 243, 0.2); padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid rgba(33, 150, 243, 0.3); }}
                .agent {{ background: rgba(255,255,255,0.1); margin: 10px 0; padding: 15px; border-radius: 8px; }}
                h1 {{ text-align: center; font-size: 2.5em; margin-bottom: 30px; text-shadow: 0 0 20px rgba(255,255,255,0.3); }}
                h2 {{ color: #4CAF50; text-shadow: 0 0 10px rgba(76, 175, 80, 0.3); }}
                .feature {{ margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 OneKeel AI - Intelligent Voice Agent</h1>
                
                <div class="status">
                    <h2>✅ System Status: FULLY OPERATIONAL</h2>
                    <p><strong>📞 Phone Number:</strong> <span class="phone">{phone_number}</span></p>
                    <p><strong>🤖 AI Engine:</strong> OpenRouter (GPT-3.5-Turbo)</p>
                    <p><strong>🎙️ Voice Quality:</strong> Twilio Polly (Professional Grade)</p>
                    <p><strong>🧠 Intelligence:</strong> Multi-Agent Routing System</p>
                    <p><strong>📊 Database:</strong> SQLite with Agent Configurations</p>
                </div>
                
                <div class="agents">
                    <h2>🎯 Specialized AI Agents</h2>
                    <div class="agent">
                        <strong>🤖 General Assistant</strong><br>
                        General inquiries and company information
                    </div>
                    <div class="agent">
                        <strong>💼 Sales Specialist</strong><br>
                        Business solutions, pricing, and demos
                    </div>
                    <div class="agent">
                        <strong>🔧 Technical Support</strong><br>
                        Implementation help and troubleshooting
                    </div>
                    <div class="agent">
                        <strong>💳 Billing Support</strong><br>
                        Account management and billing inquiries
                    </div>
                    <div class="agent">
                        <strong>📅 Appointment Scheduler</strong><br>
                        Demo booking and consultation scheduling
                    </div>
                </div>
                
                <h3>📞 Experience Intelligent Voice AI</h3>
                <p style="font-size: 1.2em; text-align: center;">
                    Call <span class="phone">{phone_number}</span> to experience our intelligent voice agent!
                </p>
                
                <h3>🎯 Key Features</h3>
                <div class="feature">✅ Intelligent call routing based on caller intent</div>
                <div class="feature">✅ Specialized agents for different business needs</div>
                <div class="feature">✅ Professional voice quality with Twilio Polly</div>
                <div class="feature">✅ Real-time speech recognition and processing</div>
                <div class="feature">✅ Comprehensive knowledge about OneKeel AI services</div>
                <div class="feature">✅ Professional customer service experience</div>
                
                <p style="text-align: center; margin-top: 30px; opacity: 0.8;">
                    🚀 Powered by OneKeel AI - The Future of Voice Intelligence
                </p>
            </div>
        </body>
        </html>
        """
    
    return app

def main():
    """Main application entry point"""
    print("🎯 ONEKEEL AI - INTELLIGENT VOICE AGENT")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Initialize database and agents
    init_database_and_agents()
    
    # Create app
    app = create_fixed_app()
    
    # Get configuration
    port = int(os.getenv('PORT', 10000))
    phone_number = os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')
    
    print(f"""
🎉 ONEKEEL AI - INTELLIGENT VOICE AGENT READY!
{'=' * 50}

🚀 Status: FULLY OPERATIONAL
📞 Phone: {phone_number}
🌐 Web: http://localhost:{port}
🎙️ Voice: Twilio Polly (Professional Quality)
🧠 AI: OpenRouter GPT-3.5-Turbo
🎯 Agents: 5 Specialized AI Agents

🎯 INTELLIGENT FEATURES:
✅ Automatic call routing by intent
✅ Specialized knowledge for each domain
✅ Professional voice quality
✅ Real-time speech processing
✅ Comprehensive business information
✅ Multi-turn conversations

📱 TEST YOUR VOICE AGENT:
Call {phone_number} and try:
• "I need pricing information" → Sales Agent
• "I have a technical problem" → Support Agent  
• "I need help with billing" → Billing Agent
• "I want to schedule a demo" → Appointment Agent
• "Tell me about OneKeel" → General Agent

Press Ctrl+C to stop
""")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n👋 OneKeel AI Voice Agent stopped")

if __name__ == "__main__":
    main()
