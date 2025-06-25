import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, current_app
from flask_cors import CORS
from flask_migrate import Migrate # Import Migrate
from src.models import db # Import the centralized db instance
from src.models.call import AgentConfig # Call, Message, SMSLog are also needed if used directly here

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
    db.init_app(app)
    CORS(app) # Enable CORS for all routes
    migrate = Migrate(app, db) # Initialize Flask-Migrate

    # Import and register blueprints
    # It's common to do this inside create_app to avoid circular imports
    # and ensure they are registered on the correct app instance.
    from src.routes.user import user_bp
    from src.routes.voice import voice_bp
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(voice_bp, url_prefix='/')

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
    # This is now handled by a separate CLI command `flask init-db`
    # to allow Alembic to correctly generate the initial migration.
    # Also, populate_default_agents is not called here for the same reason.
    # It will be called by the init-db command.
    # with app.app_context():
    #     db.create_all()
    #     populate_default_agents(app)

    return app

def populate_default_agents(app_instance):
    """Populates default agent configurations if they don't exist."""
    # This function needs to run within an app context.
    # The caller (create_app) ensures this.
    try:
        if not AgentConfig.query.first():
            default_agents = [
                {
                    'agent_type': 'general', 'name': 'General Assistant',
                    'description': 'General purpose customer service agent',
                    'system_prompt': 'You are a helpful customer service representative for A Killion Voice. Be friendly, professional, and concise in your responses.',
                    'keywords': ['hello', 'hi', 'help', 'general', 'information'], 'priority': 1,
                    'sms_template': 'Thanks for calling A Killion Voice! We discussed your inquiry and provided assistance. Reply if you need more help!'
                },
                {
                    'agent_type': 'billing', 'name': 'Billing Specialist',
                    'description': 'Handles billing, payments, and subscription inquiries',
                    'system_prompt': 'You are a billing specialist for A Killion Voice. Help customers with payment issues, billing questions, and subscription management. Be empathetic and provide clear explanations.',
                    'keywords': ['billing', 'payment', 'invoice', 'charge', 'refund', 'subscription', 'cancel', 'money', 'cost', 'price'], 'priority': 2,
                    'sms_template': 'Thanks for calling A Killion Voice about your billing inquiry. {summary} If you need further assistance, please reply or call us back.'
                },
                {
                    'agent_type': 'support', 'name': 'Technical Support',
                    'description': 'Provides technical assistance and troubleshooting',
                    'system_prompt': 'You are a technical support specialist for A Killion Voice. Help customers resolve technical issues with clear, step-by-step guidance. Ask clarifying questions when needed.',
                    'keywords': ['help', 'problem', 'issue', 'error', 'broken', 'not working', 'bug', 'technical', 'support', 'fix'], 'priority': 2,
                    'sms_template': 'Thanks for calling A Killion Voice technical support. {summary} We\'ve provided troubleshooting steps. Reply if you need more assistance!'
                },
                {
                    'agent_type': 'sales', 'name': 'Sales Representative',
                    'description': 'Handles sales inquiries and product information',
                    'system_prompt': 'You are a sales representative for A Killion Voice. Help customers understand our products and services. Be consultative, not pushy. Focus on their needs.',
                    'keywords': ['buy', 'purchase', 'pricing', 'demo', 'trial', 'features', 'plans', 'upgrade', 'sales', 'interested'], 'priority': 2,
                    'sms_template': 'Thanks for your interest in A Killion Voice services! {summary} I\'ll follow up with more information. Questions? Just reply!'
                },
                {
                    'agent_type': 'scheduling', 'name': 'Scheduling Coordinator',
                    'description': 'Manages appointments and scheduling',
                    'system_prompt': 'You are a scheduling coordinator for A Killion Voice. Help customers book appointments, check availability, and manage their calendar needs professionally.',
                    'keywords': ['appointment', 'schedule', 'meeting', 'book', 'calendar', 'available', 'time', 'date'], 'priority': 3,
                    'sms_template': 'Thanks for scheduling with A Killion Voice! {summary} We\'ll send appointment confirmations and reminders. Reply to make changes.'
                }
            ]
            
            for agent_data in default_agents:
                agent = AgentConfig(
                    agent_type=agent_data['agent_type'], name=agent_data['name'],
                    description=agent_data['description'], system_prompt=agent_data['system_prompt'],
                    sms_template=agent_data['sms_template'], priority=agent_data['priority']
                )
                agent.set_keywords(agent_data['keywords'])
                db.session.add(agent)
            
            db.session.commit()
            print("✅ Default agent configurations created or already exist.")
    except Exception as e:
        # Use app_instance.logger or print for CLI context
        print(f"⚠️ Agent configuration setup error: {e}")


# The global 'app' instance is removed. Code that needs an app instance
# (like the if __name__ == '__main__' block) should call create_app().

# It's good practice to create a single app instance for CLI commands if you have them.
# However, Flask-Migrate's `flask db` commands work by using FLASK_APP to call create_app.
# So, we only need to define the command if we want to run it directly.

def register_cli_commands(app_instance):
    @app_instance.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables and default agents."""
        click.echo("Dropping existing database tables...")
        db.drop_all()
        click.echo("Creating new database tables...")
        db.create_all()
        click.echo("Populating default agent configurations...")
        populate_default_agents(app_instance) # Pass the app instance
        click.echo("Initialized the database.")

if __name__ == '__main__':
    app = create_app() # Create app for running locally
    import click # For CLI command echo
    register_cli_commands(app) # Register CLI commands

    port = int(os.getenv('PORT', 5000))
    # FLASK_ENV is often used to control debug mode.
    # create_app can also take an env like 'development' or 'production'
    # to set app.debug directly or load different configs.
    debug_mode = os.getenv('FLASK_ENV', 'development') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
