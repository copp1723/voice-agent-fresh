import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.call import Call, Message, AgentConfig, SMSLog
from src.routes.user import user_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

from src.routes.user import user_bp
from src.routes.voice import voice_bp

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(voice_bp, url_prefix='/')

# Flask configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Database configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Production database (PostgreSQL on Render)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development database (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    
    # Create default agent configurations if they don't exist
    try:
        if not AgentConfig.query.first():
            default_agents = [
                {
                    'agent_type': 'general',
                    'name': 'General Assistant',
                    'description': 'General purpose customer service agent',
                    'system_prompt': 'You are a helpful customer service representative for A Killion Voice. Be friendly, professional, and concise in your responses.',
                    'keywords': ['hello', 'hi', 'help', 'general', 'information'],
                    'priority': 1,
                    'sms_template': 'Thanks for calling A Killion Voice! We discussed your inquiry and provided assistance. Reply if you need more help!'
                },
                {
                    'agent_type': 'billing',
                    'name': 'Billing Specialist',
                    'description': 'Handles billing, payments, and subscription inquiries',
                    'system_prompt': 'You are a billing specialist for A Killion Voice. Help customers with payment issues, billing questions, and subscription management. Be empathetic and provide clear explanations.',
                    'keywords': ['billing', 'payment', 'invoice', 'charge', 'refund', 'subscription', 'cancel', 'money', 'cost', 'price'],
                    'priority': 2,
                    'sms_template': 'Thanks for calling A Killion Voice about your billing inquiry. {summary} If you need further assistance, please reply or call us back.'
                },
                {
                    'agent_type': 'support',
                    'name': 'Technical Support',
                    'description': 'Provides technical assistance and troubleshooting',
                    'system_prompt': 'You are a technical support specialist for A Killion Voice. Help customers resolve technical issues with clear, step-by-step guidance. Ask clarifying questions when needed.',
                    'keywords': ['help', 'problem', 'issue', 'error', 'broken', 'not working', 'bug', 'technical', 'support', 'fix'],
                    'priority': 2,
                    'sms_template': 'Thanks for calling A Killion Voice technical support. {summary} We\'ve provided troubleshooting steps. Reply if you need more assistance!'
                },
                {
                    'agent_type': 'sales',
                    'name': 'Sales Representative',
                    'description': 'Handles sales inquiries and product information',
                    'system_prompt': 'You are a sales representative for A Killion Voice. Help customers understand our products and services. Be consultative, not pushy. Focus on their needs.',
                    'keywords': ['buy', 'purchase', 'pricing', 'demo', 'trial', 'features', 'plans', 'upgrade', 'sales', 'interested'],
                    'priority': 2,
                    'sms_template': 'Thanks for your interest in A Killion Voice services! {summary} I\'ll follow up with more information. Questions? Just reply!'
                },
                {
                    'agent_type': 'scheduling',
                    'name': 'Scheduling Coordinator',
                    'description': 'Manages appointments and scheduling',
                    'system_prompt': 'You are a scheduling coordinator for A Killion Voice. Help customers book appointments, check availability, and manage their calendar needs professionally.',
                    'keywords': ['appointment', 'schedule', 'meeting', 'book', 'calendar', 'available', 'time', 'date'],
                    'priority': 3,
                    'sms_template': 'Thanks for scheduling with A Killion Voice! {summary} We\'ll send appointment confirmations and reminders. Reply to make changes.'
                }
            ]
            
            for agent_data in default_agents:
                agent = AgentConfig(
                    agent_type=agent_data['agent_type'],
                    name=agent_data['name'],
                    description=agent_data['description'],
                    system_prompt=agent_data['system_prompt'],
                    sms_template=agent_data['sms_template'],
                    priority=agent_data['priority']
                )
                agent.set_keywords(agent_data['keywords'])
                db.session.add(agent)
            
            db.session.commit()
            print("✅ Default agent configurations created")
    except Exception as e:
        print(f"⚠️ Agent configuration setup: {e}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
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


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
