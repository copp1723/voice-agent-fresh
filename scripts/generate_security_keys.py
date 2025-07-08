#!/usr/bin/env python3
"""
Security Configuration Helper - Generate API keys and configure security settings
"""
import os
import sys
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.middleware.security import generate_api_key

def setup_security_config():
    """Generate and display security configuration"""
    print("🔐 Security Configuration Helper")
    print("=" * 50)
    
    # Generate API key
    api_key = generate_api_key()
    print(f"Generated API Key: {api_key}")
    
    # Generate Flask secret key
    flask_secret = generate_api_key(48)
    print(f"Generated Flask Secret: {flask_secret}")
    
    # Generate JWT secret
    jwt_secret = generate_api_key(64)
    print(f"Generated JWT Secret: {jwt_secret}")
    
    print("\n📝 Add these to your .env file:")
    print("-" * 30)
    print(f"API_KEY={api_key}")
    print(f"FLASK_SECRET_KEY={flask_secret}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    
    print("\n🛡️  Security Features Available:")
    print("- Twilio webhook signature validation")
    print("- API key authentication for admin endpoints")
    print("- Basic HTTP authentication (optional)")
    print("- Rate limiting (basic implementation)")
    print("- Input sanitization")
    print("- Security headers")
    
    print("\n💡 Usage in routes:")
    print("@validate_twilio_request  # For Twilio webhooks")
    print("@require_api_key         # For admin endpoints")
    print("@rate_limit(60, 60)      # 60 requests per minute")
    
    return {
        'api_key': api_key,
        'flask_secret': flask_secret,
        'jwt_secret': jwt_secret
    }

def update_env_file(config):
    """Update .env file with generated keys"""
    env_path = '.env'
    
    if not os.path.exists(env_path):
        print(f"⚠️  {env_path} not found")
        return
    
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update or add keys
    updates = {
        'API_KEY': config['api_key'],
        'FLASK_SECRET_KEY': config['flask_secret'],
        'JWT_SECRET_KEY': config['jwt_secret']
    }
    
    # Update existing lines
    for i, line in enumerate(lines):
        for key, value in updates.items():
            if line.startswith(f'{key}='):
                lines[i] = f'{key}={value}\n'
                del updates[key]
                break
    
    # Add new keys
    for key, value in updates.items():
        lines.append(f'{key}={value}\n')
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated {env_path} with security keys")

if __name__ == "__main__":
    config = setup_security_config()
    
    # Ask if user wants to update .env file
    print("\n❓ Update .env file with these keys? (y/n): ", end="")
    if input().lower().startswith('y'):
        update_env_file(config)
    else:
        print("💡 Copy the keys above and add them to your .env file manually")
