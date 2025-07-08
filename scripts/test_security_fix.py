#!/usr/bin/env python3
"""
Test script to verify that the security middleware fixes import issues
"""
import sys
import os
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_security_imports():
    """Test that security middleware imports work"""
    print("🔍 Testing security middleware imports...")
    
    try:
        from src.middleware.security import validate_twilio_request, require_api_key
        print("✅ Security middleware imports successful")
        return True
    except ImportError as e:
        print(f"❌ Security middleware import failed: {e}")
        return False

def test_route_imports():
    """Test that route imports work with security middleware"""
    print("🔍 Testing route imports with security middleware...")
    
    try:
        from src.routes.voice import voice_bp
        print("✅ Voice route imports successful")
        return True
    except ImportError as e:
        print(f"❌ Voice route import failed: {e}")
        return False

def test_basic_security_functions():
    """Test that security functions work"""
    print("🔍 Testing security functions...")
    
    try:
        from src.middleware.security import generate_api_key, validate_phone_number, sanitize_input
        
        # Test API key generation
        api_key = generate_api_key()
        print(f"✅ Generated API key: {api_key[:10]}...")
        
        # Test phone validation
        valid_phone = validate_phone_number("+1234567890")
        invalid_phone = validate_phone_number("123")
        print(f"✅ Phone validation: {valid_phone} / {invalid_phone}")
        
        # Test input sanitization
        clean_input = sanitize_input("Hello <script>alert('test')</script>")
        print(f"✅ Input sanitization: {clean_input}")
        
        return True
    except Exception as e:
        print(f"❌ Security function test failed: {e}")
        return False

def main():
    print("🧪 Testing Security Middleware Fix\n")
    
    security_imports = test_security_imports()
    route_imports = test_route_imports()
    security_functions = test_basic_security_functions()
    
    print("\n📊 Results:")
    print(f"   Security imports: {'✅ Working' if security_imports else '❌ Failed'}")
    print(f"   Route imports: {'✅ Working' if route_imports else '❌ Failed'}")
    print(f"   Security functions: {'✅ Working' if security_functions else '❌ Failed'}")
    
    if security_imports and route_imports and security_functions:
        print("\n🎉 Security middleware blocker is RESOLVED!")
        print("   The server should now start without import errors")
    else:
        print("\n⚠️  Some issues remain")

if __name__ == "__main__":
    main()
