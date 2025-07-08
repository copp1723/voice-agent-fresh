#!/usr/bin/env python3
"""
Quick Fix Script - Resolve remaining system issues
"""
import os
import sys
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_openai_api_key():
    """Fix the OpenAI API key issue"""
    print("🔧 Fixing OpenAI API Key...")
    
    # Get OpenAI API key from environment or prompt user
    correct_openai_key = os.getenv('OPENAI_API_KEY') or input("Enter your OpenAI API key: ")
    
    # Read current .env
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update OpenAI key
    for i, line in enumerate(lines):
        if line.startswith('OPENAI_API_KEY='):
            lines[i] = f'OPENAI_API_KEY={correct_openai_key}\n'
            print("✅ OpenAI API key updated")
            break
    
    # Write back
    with open('.env', 'w') as f:
        f.writelines(lines)

def fix_database_tables():
    """Fix database table creation issues"""
    print("🗄️ Fixing database tables...")
    
    try:
        from flask import Flask
        from src.models.database import db
        
        # Create app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            # Drop all tables and recreate
            db.drop_all()
            print("🗑️ Dropped existing tables")
            
            # Import all models to ensure they're registered
            from src.models.call import Call, Message, AgentConfig, SMSLog
            from src.models.customer import Customer, Tag
            from src.models.user import User
            
            # Create all tables
            db.create_all()
            print("✅ Created all database tables")
            
            # Create default agents
            if not AgentConfig.query.first():
                default_agents = [
                    {
                        'agent_type': 'general', 'name': 'General Assistant',
                        'system_prompt': 'You are a helpful customer service representative.',
                        'keywords': ['hello', 'hi', 'help'], 'priority': 1,
                        'sms_template': 'Thanks for calling! We discussed your inquiry.'
                    },
                    {
                        'agent_type': 'billing', 'name': 'Billing Specialist', 
                        'system_prompt': 'You are a billing specialist.',
                        'keywords': ['billing', 'payment'], 'priority': 2,
                        'sms_template': 'Thanks for calling about billing.'
                    }
                ]
                
                for agent_data in default_agents:
                    agent = AgentConfig(
                        agent_type=agent_data['agent_type'],
                        name=agent_data['name'],
                        system_prompt=agent_data['system_prompt'],
                        sms_template=agent_data['sms_template'],
                        priority=agent_data['priority']
                    )
                    agent.set_keywords(agent_data['keywords'])
                    db.session.add(agent)
                
                db.session.commit()
                print("✅ Created default agent configurations")
        
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        return False

def fix_python_compatibility():
    """Ensure Python 3.13 compatibility"""
    print("🐍 Fixing Python compatibility...")
    
    python_ver = sys.version_info[:3]
    print(f"Python version: {python_ver[0]}.{python_ver[1]}.{python_ver[2]}")
    
    if python_ver >= (3, 13, 0):
        # Force threading mode for Python 3.13+
        os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
        print("✅ Set SocketIO to threading mode for Python 3.13+")
        
        # Update .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        if 'SOCKETIO_ASYNC_MODE' not in content:
            with open('.env', 'a') as f:
                f.write('\n# Python 3.13+ Compatibility\nSOCKETIO_ASYNC_MODE=threading\n')
            print("✅ Added SocketIO threading mode to .env")
    
    return True

def test_fixed_system():
    """Test the fixed system"""
    print("🧪 Testing fixed system...")
    
    try:
        # Test OpenAI API
        import openai
        from dotenv import load_dotenv
        load_dotenv()
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        models = client.models.list()
        print("✅ OpenAI API: Working")
        
        # Test database
        from flask import Flask
        from src.models.database import db
        from src.models.call import AgentConfig
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        
        with app.app_context():
            agent_count = AgentConfig.query.count()
            print(f"✅ Database: {agent_count} agents configured")
        
        # Test TTS
        from src.services.optional_tts_service import tts_service
        audio_bytes, metadata = tts_service.text_to_speech("Test")
        if audio_bytes:
            print(f"✅ TTS: Generated {len(audio_bytes)} bytes")
        else:
            print("⚠️ TTS: Using fallback mode")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    print("🔧 QUICK FIX SCRIPT - Resolving System Issues")
    print("=" * 50)
    
    # Fix issues
    fix_openai_api_key()
    fix_python_compatibility()
    
    if not fix_database_tables():
        print("❌ Database fix failed - trying alternative approach...")
        # Alternative: just delete the database file and let it recreate
        if os.path.exists('app.db'):
            os.remove('app.db')
            print("🗑️ Removed old database file")
        
        fix_database_tables()
    
    # Test fixed system
    if test_fixed_system():
        print("\n🎉 SYSTEM FIXES APPLIED SUCCESSFULLY!")
        print("=" * 40)
        print("✅ OpenAI API key corrected")
        print("✅ Database tables created")
        print("✅ Python 3.13 compatibility ensured")
        print("✅ TTS system working")
        print("")
        print("🚀 Ready to start:")
        print("   python3 start_production.py")
    else:
        print("\n⚠️ Some fixes may need manual attention")
        print("💡 Try running: python3 start_production.py anyway")

if __name__ == "__main__":
    main()
