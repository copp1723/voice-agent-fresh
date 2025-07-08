#!/usr/bin/env python3
"""
Check Twilio phone number configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

def check_twilio_config():
    """Check current Twilio webhook configuration"""
    try:
        from twilio.rest import Client
        
        # Get Twilio credentials
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, phone_number]):
            print("❌ Missing Twilio credentials in .env file")
            return
        
        # Create client
        client = Client(account_sid, auth_token)
        
        print(f"🔍 Checking configuration for {phone_number}")
        
        # Get phone number configuration
        phone_numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
        
        if not phone_numbers:
            print(f"❌ Phone number {phone_number} not found in your Twilio account")
            return
        
        phone_config = phone_numbers[0]
        
        print(f"\n📞 Phone Number: {phone_config.phone_number}")
        print(f"🌐 Voice Webhook URL: {phone_config.voice_url}")
        print(f"📋 Voice Webhook Method: {phone_config.voice_method}")
        print(f"📊 Status Callback URL: {phone_config.status_callback}")
        print(f"🏷️ Friendly Name: {phone_config.friendly_name}")
        
        # Check if webhook URL looks correct
        if not phone_config.voice_url:
            print("\n❌ No webhook URL configured!")
            print("💡 You need to set the webhook URL in Twilio Console")
        elif 'localhost' in phone_config.voice_url or '127.0.0.1' in phone_config.voice_url:
            print(f"\n❌ Webhook URL is localhost - Twilio can't reach it!")
            print("💡 You need to use ngrok or deploy to a public server")
        elif 'ngrok' in phone_config.voice_url:
            print(f"\n✅ Using ngrok URL - should work if ngrok is running")
            print("💡 Make sure ngrok is still running on the same URL")
        else:
            print(f"\n✅ Using public URL - should work")
        
        print(f"\n🧪 Test webhook URL:")
        print(f"Visit: {phone_config.voice_url}/health")
        print(f"Should return: {{'status': 'healthy', ...}}")
        
    except ImportError:
        print("❌ Twilio library not installed. Run: pip install twilio")
    except Exception as e:
        print(f"❌ Error checking Twilio config: {e}")

def suggest_ngrok_setup():
    """Suggest ngrok setup commands"""
    print(f"\n🔧 TO FIX THE ISSUE:")
    print(f"1. Keep your server running: python3 start_debug.py")
    print(f"2. In new terminal, start ngrok: ngrok http 10000")
    print(f"3. Copy the https URL from ngrok (like https://abc123.ngrok.io)")
    print(f"4. Update Twilio webhook in console to: https://abc123.ngrok.io/api/twilio/inbound")
    print(f"5. Test call again")

if __name__ == "__main__":
    print("🔍 TWILIO WEBHOOK CONFIGURATION CHECKER")
    print("=" * 45)
    
    check_twilio_config()
    suggest_ngrok_setup()
