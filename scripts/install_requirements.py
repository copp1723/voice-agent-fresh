#!/usr/bin/env python3
"""
Smart Requirements Installer - Installs compatible packages based on Python version
"""
import sys
import subprocess
import os

def get_python_version():
    """Get current Python version"""
    return sys.version_info[:3]

def install_requirements():
    """Install requirements based on Python version"""
    python_ver = get_python_version()
    
    print(f"🐍 Detected Python {python_ver[0]}.{python_ver[1]}.{python_ver[2]}")
    
    if python_ver >= (3, 13, 0):
        print("📦 Installing Python 3.13+ compatible packages...")
        requirements_file = "requirements-py313.txt"
        
        # Check if file exists
        if not os.path.exists(requirements_file):
            print(f"❌ {requirements_file} not found")
            print("💡 Using standard requirements.txt (may have compatibility issues)")
            requirements_file = "requirements.txt"
        
        # Install packages
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                          check=True)
            print("✅ Python 3.13+ compatible packages installed successfully")
            
            # Print compatibility info
            print("\n🔧 Python 3.13+ Configuration:")
            print("   - Using threading mode for SocketIO (not eventlet)")
            print("   - Using gevent for gunicorn workers")
            print("   - Skipping eventlet dependency")
            print("   - ML packages (torch) may need conda installation")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            print("💡 Try installing manually:")
            print(f"   pip install -r {requirements_file}")
            return False
            
    else:
        print("📦 Installing standard packages (eventlet compatible)...")
        requirements_file = "requirements.txt"
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                          check=True)
            print("✅ Standard packages installed successfully")
            
            print("\n🔧 Standard Configuration:")
            print("   - Using eventlet mode for SocketIO")
            print("   - Using eventlet for gunicorn workers")
            print("   - Full ML package support")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            return False
    
    return True

def test_imports():
    """Test critical imports"""
    print("\n🧪 Testing critical imports...")
    
    tests = [
        ("Flask", "flask"),
        ("Flask-SocketIO", "flask_socketio"),
        ("SQLAlchemy", "sqlalchemy"),
        ("Twilio", "twilio"),
        ("OpenAI", "openai"),
        ("Requests", "requests"),
    ]
    
    failed = []
    
    for name, module in tests:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError as e:
            print(f"   ❌ {name}: {e}")
            failed.append(name)
    
    if failed:
        print(f"\n⚠️  {len(failed)} packages failed to import")
        return False
    else:
        print("\n🎉 All critical packages imported successfully!")
        return True

def main():
    print("🚀 Smart Requirements Installer")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("\n💡 Some packages failed to import. Try:")
        print("   - Upgrading pip: python -m pip install --upgrade pip")
        print("   - Installing in clean environment: python -m venv venv")
        print("   - Using conda for ML packages")
        sys.exit(1)
    
    print("\n🎯 Installation complete!")
    print("Next steps:")
    print("   1. Run compatibility check: python src/utils/compatibility.py")
    print("   2. Generate security keys: python generate_security_keys.py")
    print("   3. Start server: python start_simple.py")

if __name__ == "__main__":
    main()
