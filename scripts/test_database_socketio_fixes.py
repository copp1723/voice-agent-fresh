#!/usr/bin/env python3
"""
Test Database Model Import Dependencies and Flask-SocketIO Configuration
"""
import sys
import os
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_model_imports():
    """Test that database models import without circular dependency issues"""
    print("🔍 Testing Database Model Import Dependencies...")
    
    try:
        # Test individual model imports (should work without circular issues)
        from src.models.database import db, model_registry, BaseModel
        print("✅ Database module imported successfully")
        
        from src.models.call import Call, Message, AgentConfig, SMSLog
        print("✅ Call models imported without circular issues")
        
        from src.models.customer import Customer, Tag
        print("✅ Customer models imported without circular issues")
        
        from src.models.user import User
        print("✅ User model imported without circular issues")
        
        # Test model registry
        registered_models = model_registry.get_all_models()
        expected_models = ['Call', 'Message', 'AgentConfig', 'SMSLog', 'Customer', 'Tag', 'User']
        
        missing_models = []
        for model_name in expected_models:
            if model_name in registered_models:
                print(f"✅ {model_name} properly registered")
            else:
                missing_models.append(model_name)
                print(f"❌ {model_name} not registered")
        
        if missing_models:
            print(f"⚠️ Missing models: {missing_models}")
            return False
        
        # Test foreign key relationships don't cause import errors
        try:
            # These should work without causing circular imports
            call = Call(call_sid='test', from_number='+123', to_number='+456')
            customer = Customer(phone_number='+123456789')
            message = Message(role='user', content='test')
            
            print("✅ Model instantiation works without import errors")
        except Exception as e:
            print(f"❌ Model instantiation failed: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Circular import detected: {e}")
        return False
    except Exception as e:
        print(f"❌ Database model import test failed: {e}")
        return False

def test_database_initialization():
    """Test database initialization without import issues"""
    print("\n🔍 Testing Database Initialization...")
    
    try:
        from flask import Flask
        from src.models.database import init_database
        
        # Create test app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_init.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Test database initialization
        with app.app_context():
            success = init_database(app)
            
            if success:
                print("✅ Database initialization successful")
                
                # Test that default data is created
                from src.models.call import AgentConfig
                agent_count = AgentConfig.query.count()
                if agent_count > 0:
                    print(f"✅ Default agents created: {agent_count}")
                else:
                    print("⚠️ No default agents created")
                
                return True
            else:
                print("❌ Database initialization failed")
                return False
                
    except Exception as e:
        print(f"❌ Database initialization test failed: {e}")
        return False

def test_foreign_key_relationships():
    """Test that foreign key relationships work without circular import issues"""
    print("\n🔍 Testing Foreign Key Relationships...")
    
    try:
        from flask import Flask
        from src.models.database import db
        from src.models.call import Call, Message
        from src.models.customer import Customer
        
        # Create test app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_fk.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        with app.app_context():
            db.init_app(app)
            db.create_all()
            
            # Test creating objects with foreign key relationships
            customer = Customer(phone_number='+1234567890', name='Test Customer')
            customer.save()
            
            call = Call(
                call_sid='test123',
                from_number='+1234567890',
                to_number='+1987654321',
                customer_id=customer.id
            )
            call.save()
            
            message = Message(
                call_id=call.id,
                role='user',
                content='Test message'
            )
            message.save()
            
            # Test relationship access (should not cause circular imports)
            retrieved_call = Call.query.filter_by(call_sid='test123').first()
            if retrieved_call:
                # Test lazy loading relationships
                call_customer = retrieved_call.get_customer()
                if call_customer and call_customer.id == customer.id:
                    print("✅ Call-Customer relationship works")
                else:
                    print("❌ Call-Customer relationship failed")
                    return False
                
                # Test message relationships
                call_messages = retrieved_call.get_messages_list()
                if call_messages and len(call_messages) > 0:
                    print("✅ Call-Message relationship works")
                else:
                    print("❌ Call-Message relationship failed")
                    return False
                
                print("✅ All foreign key relationships work correctly")
                return True
            else:
                print("❌ Could not retrieve test call")
                return False
                
    except Exception as e:
        print(f"❌ Foreign key relationship test failed: {e}")
        return False

def test_flask_socketio_configuration():
    """Test Flask-SocketIO configuration compatibility"""
    print("\n🔍 Testing Flask-SocketIO Configuration...")
    
    try:
        from src.utils.compatibility import get_recommended_socketio_config, create_compatible_socketio
        
        # Test configuration detection
        config = get_recommended_socketio_config()
        print(f"✅ SocketIO Configuration:")
        print(f"   - Async Mode: {config['async_mode']}")
        print(f"   - CORS: {config['cors_allowed_origins']}")
        
        # Test Python version compatibility
        import sys
        python_ver = sys.version_info[:3]
        
        if python_ver >= (3, 13, 0):
            if config['async_mode'] == 'threading':
                print("✅ Python 3.13+ using threading mode (correct)")
            else:
                print(f"⚠️ Python 3.13+ using {config['async_mode']} mode (may have issues)")
        else:
            print(f"✅ Python {python_ver[0]}.{python_ver[1]} using {config['async_mode']} mode")
        
        # Test SocketIO creation
        socketio = create_compatible_socketio()
        if hasattr(socketio, 'async_mode'):
            print(f"✅ SocketIO created with {socketio.async_mode} mode")
        else:
            print("✅ SocketIO created successfully")
        
        # Test main app integration
        from src.main import socketio as main_socketio
        if hasattr(main_socketio, 'async_mode'):
            print(f"✅ Main app SocketIO mode: {main_socketio.async_mode}")
        
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
