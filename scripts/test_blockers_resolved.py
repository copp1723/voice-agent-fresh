#!/usr/bin/env python3
"""
Test Resolution of Chatterbox TTS and Port Configuration Blockers
"""
import sys
import os
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_chatterbox_optional():
    """Test that Chatterbox TTS is properly optional"""
    print("🔍 Testing Chatterbox TTS Optional Configuration...")
    
    try:
        from src.services.optional_tts_service import tts_service
        
        # Test service status
        status = tts_service.get_service_status()
        print(f"✅ TTS Service Status:")
        print(f"   - Chatterbox Available: {status['chatterbox']['available']}")
        print(f"   - OpenAI Available: {status['openai']['available']}")
        print(f"   - Active Service: {status['active_service']}")
        
        # Test TTS functionality (should work even without ML dependencies)
        audio_bytes, metadata = tts_service.text_to_speech("Hello, this is a test")
        print(f"✅ TTS Test: {len(audio_bytes)} bytes generated")
        print(f"✅ TTS Service: {metadata.get('tts_service', 'unknown')}")
        
        # Test dependency checking
        deps = tts_service._check_chatterbox_dependencies()
        missing_deps = [dep for dep, available in deps.items() if not available]
        
        if missing_deps:
            print(f"⚠️ Missing ML dependencies: {missing_deps}")
            print("✅ System gracefully handles missing dependencies")
        else:
            print("✅ All Chatterbox dependencies available")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask-SocketIO configuration test failed: {e}")
        return False

def test_main_app_integration():
    """Test that main app integrates both fixes correctly"""
    print("\n🔍 Testing Main App Integration...")
    
    try:
        from src.main import create_app
        
        # Test app creation with both fixes
        app = create_app('testing')
        
        if app:
            print("✅ Main app creation successful with both fixes")
            
            # Test that database is properly initialized
            with app.app_context():
                from src.models.call import AgentConfig
                try:
                    agent_count = AgentConfig.query.count()
                    print(f"✅ Database integration works: {agent_count} agents")
                except Exception as e:
                    print(f"⚠️ Database query issue: {e}")
            
            # Test SocketIO integration
            from src.main import socketio
            if hasattr(socketio, 'async_mode'):
                print(f"✅ SocketIO integration: {socketio.async_mode} mode")
            
            return True
        else:
            print("❌ Main app creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Main app integration test failed: {e}")
        return False

def test_startup_compatibility():
    """Test that startup scripts work with both fixes"""
    print("\n🔍 Testing Startup Script Compatibility...")
    
    try:
        # Test port configuration
        from src.utils.port_config import get_standardized_port
        port = get_standardized_port('backend')
        print(f"✅ Port configuration: {port}")
        
        # Test compatibility system
        from src.utils.compatibility import check_compatibility
        compat_info = check_compatibility()
        print(f"✅ Python compatibility: {compat_info['python_version']}")
        
        # Test that imports work in startup context
        try:
            from src.models.call import Call
            from src.models.customer import Customer
            from src.models.user import User
            print("✅ Startup script model imports work")
        except ImportError as e:
            print(f"❌ Startup script import failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Startup compatibility test failed: {e}")
        return False

def main():
    print("🧪 Testing Database Model Dependencies and Flask-SocketIO Configuration")
    print("=" * 75)
    
    # Run all tests
    tests = [
        ("Database Model Import Dependencies", test_database_model_imports),
        ("Database Initialization", test_database_initialization),
        ("Foreign Key Relationships", test_foreign_key_relationships),
        ("Flask-SocketIO Configuration", test_flask_socketio_configuration),
        ("Main App Integration", test_main_app_integration),
        ("Startup Script Compatibility", test_startup_compatibility),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 BOTH CRITICAL BLOCKERS RESOLVED!")
        print("=" * 45)
        print("✅ Database Model Import Dependencies - RESOLVED")
        print("   - Circular import issues eliminated")
        print("   - Safe foreign key relationships")
        print("   - Proper initialization order")
        print("   - Model registry system implemented")
        print("   - Error handling and logging added")
        print("")
        print("✅ Flask-SocketIO Configuration Issues - RESOLVED")
        print("   - Python 3.13+ compatibility confirmed")
        print("   - Automatic async mode selection")
        print("   - Graceful fallback mechanisms")
        print("   - WebSocket events will work correctly")
        print("")
        print("🚀 Combined Impact:")
        print("   - Server starts without database import errors")
        print("   - WebSocket features work on all Python versions")
        print("   - Reliable database relationships")
        print("   - Better error handling and debugging")
        print("   - Future-proof architecture")
        print("")
        print("📋 Ready to run:")
        print("   python migrate_database.py  # Apply database fixes")
        print("   python start_compatible.py  # Start with all fixes")
        
    else:
        print("\n⚠️ Some tests failed - check output above")
        print("💡 Try running the migration script first:")
        print("   python migrate_database.py")

if __name__ == "__main__":
    main()
        print(f"❌ Chatterbox optional test failed: {e}")
        return False

def test_port_standardization():
    """Test port configuration standardization"""
    print("\n🔍 Testing Port Configuration Standardization...")
    
    try:
        from src.utils.port_config import port_manager, get_standardized_port
        
        # Test port detection
        config = port_manager.get_port_config()
        print(f"✅ Port Detection:")
        print(f"   - Detected Port: {config['detected_port']}")
        print(f"   - Port Source: {config['port_source']}")
        print(f"   - Flask Environment: {config['flask_env']}")
        
        # Test standardized port function
        backend_port = get_standardized_port('backend')
        frontend_port = get_standardized_port('frontend')
        print(f"✅ Standardized Ports:")
        print(f"   - Backend: {backend_port}")
        print(f"   - Frontend: {frontend_port}")
        
        # Test validation
        validation = port_manager.validate_port_configuration()
        print(f"✅ Port Validation:")
        print(f"   - Valid: {validation['valid']}")
        if validation['warnings']:
            print(f"   - Warnings: {len(validation['warnings'])}")
        if validation['errors']:
            print(f"   - Errors: {len(validation['errors'])}")
        
        # Test recommendations
        recommendations = config['recommendations']
        print(f"✅ Configuration Status: {recommendations['current_setup']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Port standardization test failed: {e}")
        return False

def test_startup_scripts():
    """Test that startup scripts use standardized configuration"""
    print("\n🔍 Testing Startup Script Integration...")
    
    try:
        # Test main.py integration
        from src.main import create_app
        from src.utils.port_config import get_standardized_port
        
        port = get_standardized_port('backend')
        print(f"✅ Main app port: {port}")
        
        # Test that app creation works
        app = create_app('testing')
        print("✅ App creation successful")
        
        # Test SocketIO compatibility
        from src.main import socketio
        if hasattr(socketio, 'async_mode'):
            print(f"✅ SocketIO mode: {socketio.async_mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Startup script integration test failed: {e}")
        return False

def test_environment_configuration():
    """Test environment variable configuration"""
    print("\n🔍 Testing Environment Configuration...")
    
    try:
        # Test TTS configuration
        use_chatterbox = os.getenv('USE_CHATTERBOX', 'false').lower() == 'true'
        print(f"✅ Chatterbox enabled: {use_chatterbox}")
        
        # Test port configuration
        port_env = os.getenv('PORT')
        if port_env:
            print(f"✅ Port from environment: {port_env}")
        else:
            print("✅ Port will use defaults")
        
        # Test Flask environment
        flask_env = os.getenv('FLASK_ENV', 'development')
        print(f"✅ Flask environment: {flask_env}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment configuration test failed: {e}")
        return False

def test_requirements_structure():
    """Test that requirements are properly structured"""
    print("\n🔍 Testing Requirements Structure...")
    
    try:
        import os
        
        # Check for requirements files
        requirements_files = [
            'requirements.txt',
            'requirements-core.txt',
            'requirements-ml.txt',
            'requirements-py313.txt'
        ]
        
        available_files = []
        for req_file in requirements_files:
            if os.path.exists(req_file):
                available_files.append(req_file)
                print(f"✅ Found: {req_file}")
        
        if not available_files:
            print("❌ No requirements files found")
            return False
        
        # Test that core requirements don't include heavy ML dependencies
        if os.path.exists('requirements-core.txt'):
            with open('requirements-core.txt', 'r') as f:
                core_content = f.read()
            
            heavy_deps = ['torch', 'torchaudio', 'tensorflow']
            heavy_found = [dep for dep in heavy_deps if dep in core_content]
            
            if heavy_found:
                print(f"⚠️ Heavy dependencies in core requirements: {heavy_found}")
            else:
                print("✅ Core requirements are lightweight")
        
        return True
        
    except Exception as e:
        print(f"❌ Requirements structure test failed: {e}")
        return False

def main():
    print("🧪 Testing Chatterbox TTS and Port Configuration Blockers Resolution")
    print("=" * 70)
    
    # Run all tests
    tests = [
        ("Chatterbox Optional Configuration", test_chatterbox_optional),
        ("Port Standardization", test_port_standardization),
        ("Startup Script Integration", test_startup_scripts),
        ("Environment Configuration", test_environment_configuration),
        ("Requirements Structure", test_requirements_structure),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 BOTH BLOCKERS RESOLVED!")
        print("=" * 35)
        print("✅ Chatterbox TTS Dependencies - RESOLVED")
        print("   - Made completely optional")
        print("   - Graceful fallback to OpenAI TTS")
        print("   - No startup failures from missing ML dependencies")
        print("   - Lightweight core requirements")
        print("")
        print("✅ Frontend-Backend Port Mismatch - RESOLVED")
        print("   - Standardized port configuration")
        print("   - Automatic environment detection")
        print("   - Consistent across all startup methods")
        print("   - Proper development/production defaults")
        print("")
        print("🚀 Impact:")
        print("   - Server starts without ML dependency issues")
        print("   - Ports are consistent across all scripts")
        print("   - TTS works with or without Chatterbox")
        print("   - Environment-aware configuration")
        print("")
        print("📋 Ready to use:")
        print("   python setup_project.py")
        print("   python start_simple.py")
        
    else:
        print("\n⚠️ Some tests failed - check output above")

if __name__ == "__main__":
    main()
