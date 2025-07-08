#!/usr/bin/env python3
"""
Smart Project Setup - Handles both TTS dependencies and port configuration
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_dependencies(include_ml=False, force_install=False):
    """Setup project dependencies"""
    print("📦 Setting up dependencies...")
    
    # Core dependencies (always required)
    core_requirements = "requirements-core.txt"
    
    if os.path.exists(core_requirements):
        print("📥 Installing core dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", core_requirements], 
                          check=True)
            print("✅ Core dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install core dependencies: {e}")
            return False
    
    # ML dependencies (optional)
    if include_ml:
        ml_requirements = "requirements-ml.txt"
        if os.path.exists(ml_requirements):
            print("📥 Installing ML dependencies (this may take a while)...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", ml_requirements], 
                              check=True)
                print("✅ ML dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install ML dependencies: {e}")
                print("💡 Consider using conda for ML packages:")
                print("   conda install pytorch torchaudio -c pytorch")
                if not force_install:
                    return False
    
    return True

def configure_ports():
    """Configure port standardization"""
    print("🔧 Configuring port standardization...")
    
    try:
        from src.utils.port_config import port_manager
        
        # Get current configuration
        config = port_manager.get_port_config()
        print(f"📍 Current port: {config['detected_port']} (from {config['port_source']})")
        
        # Standardize .env file
        if port_manager.standardize_env_file():
            print("✅ Port configuration standardized")
        else:
            print("⚠️ Could not standardize port configuration")
        
        # Show recommendations
        recommendations = config['recommendations']
        if recommendations['issues']:
            print("\n⚠️ Port configuration issues found:")
            for issue in recommendations['issues']:
                print(f"   - {issue}")
        
        return True
        
    except Exception as e:
        print(f"❌ Port configuration failed: {e}")
        return False

def configure_tts():
    """Configure TTS services"""
    print("🎙️ Configuring TTS services...")
    
    try:
        from src.services.optional_tts_service import tts_service
        
        # Get TTS status
        status = tts_service.get_service_status()
        
        print(f"📊 TTS Service Status:")
        print(f"   - Chatterbox Available: {status['chatterbox']['available']}")
        print(f"   - OpenAI Available: {status['openai']['available']}")
        print(f"   - Active Service: {status['active_service']}")
        
        # Update .env file with TTS configuration
        env_path = '.env'
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Add TTS configuration if not present
            if 'USE_CHATTERBOX' not in content:
                use_chatterbox = status['chatterbox']['available']
                with open(env_path, 'a') as f:
                    f.write(f"\n# TTS Configuration\nUSE_CHATTERBOX={str(use_chatterbox).lower()}\n")
                print(f"✅ TTS configuration added to .env (USE_CHATTERBOX={str(use_chatterbox).lower()})")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS configuration failed: {e}")
        return False

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    # Test core imports
    core_tests = [
        ("Flask", "flask"),
        ("Flask-SocketIO", "flask_socketio"),
        ("SQLAlchemy", "sqlalchemy"),
        ("Twilio", "twilio"),
        ("OpenAI", "openai"),
        ("Requests", "requests"),
    ]
    
    failed_core = []
    for name, module in core_tests:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name}")
            failed_core.append(name)
    
    # Test optional imports
    optional_tests = [
        ("Torch", "torch"),
        ("Torchaudio", "torchaudio"),
        ("Numpy", "numpy"),
    ]
    
    failed_optional = []
    for name, module in optional_tests:
        try:
            __import__(module)
            print(f"   ✅ {name} (optional)")
        except ImportError:
            print(f"   ⚠️ {name} (optional - not installed)")
            failed_optional.append(name)
    
    # Test project imports
    try:
        from src.utils.compatibility import create_compatible_socketio
        from src.utils.port_config import get_standardized_port
        from src.services.optional_tts_service import tts_service
        print("   ✅ Project modules")
    except ImportError as e:
        print(f"   ❌ Project modules: {e}")
        failed_core.append("Project modules")
    
    if failed_core:
        print(f"\n❌ Critical components failed: {', '.join(failed_core)}")
        return False
    
    if failed_optional:
        print(f"\n⚠️ Optional components not available: {', '.join(failed_optional)}")
        print("   (This is OK - ML features will be disabled)")
    
    print("\n✅ Installation test passed!")
    return True

def create_startup_guide():
    """Create a startup guide"""
    guide = """
# 🚀 Voice Agent Startup Guide

## Quick Start Commands

### Option 1: Simple Start (Recommended)
```bash
python start_simple.py
```

### Option 2: Full Features
```bash
python src/main.py
```

### Option 3: Compatible Start (Auto-detects Python version)
```bash
python start_compatible.py
```

## Port Configuration

Your server will automatically use the appropriate port:
- Development: 5000
- Production: 10000

## TTS Configuration

### OpenAI TTS (Recommended)
- Lightweight and fast
- Requires: OPENAI_API_KEY in .env
- Good voice quality

### Chatterbox TTS (Optional)
- Advanced emotion control
- Requires: ML dependencies (torch, torchaudio)
- Higher quality but heavier

## Environment Variables

Essential variables to set in `.env`:
```
# Required
OPENAI_API_KEY=your-api-key-here
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token

# Optional
USE_CHATTERBOX=false
```

## Troubleshooting

### Port Issues
- Check .env file PORT setting
- Ensure no other services using the same port
- Use `python -c "from src.utils.port_config import get_port_config; print(get_port_config())"` to debug

### TTS Issues
- Check TTS service status: `python -c "from src.services.optional_tts_service import tts_service; print(tts_service.get_service_status())"`
- For Chatterbox: Install ML dependencies or disable with USE_CHATTERBOX=false

### Python Version Issues
- Use Python 3.8+ (3.11 recommended)
- For Python 3.13+: System automatically uses compatible modes

## Health Check

Once started, test your server:
```bash
curl http://localhost:5000/health
```
"""
    
    with open('STARTUP_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("📝 Created STARTUP_GUIDE.md")

def main():
    parser = argparse.ArgumentParser(description='Smart Voice Agent Project Setup')
    parser.add_argument('--include-ml', action='store_true', 
                       help='Install ML dependencies for Chatterbox TTS')
    parser.add_argument('--force', action='store_true', 
                       help='Continue even if some installations fail')
    parser.add_argument('--test-only', action='store_true', 
                       help='Only run tests, skip installation')
    
    args = parser.parse_args()
    
    print("🎯 Smart Voice Agent Project Setup")
    print("=" * 45)
    
    if not args.test_only:
        # Setup dependencies
        if not setup_dependencies(include_ml=args.include_ml, force_install=args.force):
            if not args.force:
                print("❌ Setup failed. Use --force to continue anyway.")
                sys.exit(1)
        
        # Configure ports
        if not configure_ports():
            print("⚠️ Port configuration had issues")
        
        # Configure TTS
        if not configure_tts():
            print("⚠️ TTS configuration had issues")
    
    # Test installation
    if not test_installation():
        print("❌ Installation test failed")
        sys.exit(1)
    
    # Create startup guide
    create_startup_guide()
    
    print("\n🎉 Setup Complete!")
    print("=" * 20)
    print("✅ Dependencies installed")
    print("✅ Port configuration standardized")
    print("✅ TTS services configured")
    print("✅ Installation tested")
    print("✅ Startup guide created")
    
    print("\n🚀 Ready to start:")
    print("   python start_simple.py")
    print("\n📖 Read STARTUP_GUIDE.md for more options")

if __name__ == "__main__":
    main()
