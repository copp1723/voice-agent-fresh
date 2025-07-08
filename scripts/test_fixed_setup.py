#!/usr/bin/env python3
"""
Quick test script to verify the fixed voice agent setup
"""
import os
import sqlite3
import requests
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

def test_database_setup():
    """Test database initialization"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Check if agent_configs table exists and has data
        cursor.execute('SELECT COUNT(*) FROM agent_configs')
        agent_count = cursor.fetchone()[0]
        
        print(f"✅ Database: {agent_count} agents configured")
        
        # Show agent types
        cursor.execute('SELECT agent_type, name FROM agent_configs ORDER BY priority DESC')
        agents = cursor.fetchall()
        
        for agent_type, name in agents:
            print(f"   • {name} ({agent_type})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    required_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'TWILIO_PHONE_NUMBER',
        'OPENROUTER_API_KEY'
    ]
    
    print("🔍 Checking environment variables:")
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"   ❌ {var}: Not found")
        else:
            # Show partial value for security
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"   ✅ {var}: {masked_value}")
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("💡 Make sure your .env file is in the current directory")
        return False
    else:
        print("✅ Environment: All required variables configured")
        return True

def test_openrouter_connection():
    """Test OpenRouter API connection"""
    try:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("❌ OpenRouter: No API key configured")
            return False
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'openai/gpt-3.5-turbo',
            'messages': [
                {'role': 'user', 'content': 'Test message'}
            ],
            'max_tokens': 10
        }
        
        print("🔗 Testing OpenRouter API connection...")
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ OpenRouter: API connection successful")
            return True
        else:
            print(f"❌ OpenRouter: API error {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter: Connection failed - {e}")
        return False

def test_call_routing():
    """Test call routing logic"""
    def route_call(user_input):
        """Improved call routing logic"""
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
        appointment_keywords = ['appointment', 'schedule', 'meeting', 'call back', 'book', 'calendar', 'demo', 'consultation']
        if any(word in user_input_lower for word in appointment_keywords):
            return 'appointments'
        
        # Default to general
        return 'general'
    
    try:
        # Test routing logic
        test_inputs = [
            ("I need pricing information", "sales"),
            ("What are your prices", "sales"),
            ("I have a technical problem", "support"),
            ("Help with billing", "billing"),
            ("Schedule a demo", "appointments"),
            ("Book a meeting", "appointments"),
            ("What do you do", "general"),
            ("Tell me about OneKeel", "general")
        ]
        
        print("✅ Call Routing Tests:")
        
        passed = 0
        for input_text, expected in test_inputs:
            result = route_call(input_text)
            status = "✅" if result == expected else "❌"
            print(f"   {status} '{input_text}' → {result} (expected: {expected})")
            if result == expected:
                passed += 1
        
        print(f"📊 Routing Test Results: {passed}/{len(test_inputs)} passed")
        return passed == len(test_inputs)
        
    except Exception as e:
        print(f"❌ Call routing test failed: {e}")
        return False

def test_twilio_config():
    """Test Twilio configuration"""
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, phone_number]):
            print("❌ Twilio: Missing configuration")
            return False
        
        print(f"✅ Twilio Configuration:")
        print(f"   • Account SID: {account_sid[:8]}...")
        print(f"   • Auth Token: {auth_token[:8]}...")
        print(f"   • Phone Number: {phone_number}")
        
        return True
        
    except Exception as e:
        print(f"❌ Twilio configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 ONEKEEL AI VOICE AGENT - COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)
    
    # Initialize database first
    try:
        from start_fixed import init_database_and_agents
        init_database_and_agents()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    tests = [
        ("Environment Configuration", test_environment),
        ("Twilio Configuration", test_twilio_config),
        ("Database Setup", test_database_setup),
        ("OpenRouter Connection", test_openrouter_connection),
        ("Call Routing Logic", test_call_routing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️ {test_name} failed")
    
    print(f"\n📊 FINAL TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your voice agent is ready to go!")
        print("\n🚀 NEXT STEPS:")
        print("1. Start the server: python3 start_fixed.py")
        print(f"2. Test by calling: {os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')}")
        print("3. Try different phrases to test agent routing:")
        print("   • 'I need pricing' → Sales Agent")
        print("   • 'I have a problem' → Support Agent")
        print("   • 'Help with billing' → Billing Agent")
        print("   • 'Schedule a demo' → Appointments Agent")
        print("   • 'What do you do' → General Agent")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the configuration.")
        
    print(f"\n📞 Your phone number: {os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')}")
    print(f"🌐 Web dashboard will be at: http://localhost:{os.getenv('PORT', '10000')}")

if __name__ == "__main__":
    main()
