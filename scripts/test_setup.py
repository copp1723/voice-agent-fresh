#!/usr/bin/env python3
"""
Test script to verify the setup is working
"""
import requests
import sys

def test_backend():
    """Test if backend is running"""
    print("🔍 Testing backend...")
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:10000/health')
        if response.status_code == 200:
            print("✅ Backend is running on port 10000")
            print(f"   Response: {response.json()}")
        else:
            print("❌ Backend health check failed")
            return False
            
        # Test basic UI
        response = requests.get('http://localhost:10000/')
        if response.status_code == 200:
            print("✅ Basic UI is accessible")
        else:
            print("❌ Basic UI not accessible")
            
        # Test API endpoints
        response = requests.get('http://localhost:10000/api/users')
        print(f"✅ API endpoint test: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running on port 10000")
        print("   Run: python3 start_simple.py")
        return False

def test_frontend():
    """Test if frontend is running"""
    print("\n🔍 Testing frontend...")
    
    try:
        response = requests.get('http://localhost:3000/')
        if response.status_code == 200:
            print("✅ Frontend is running on port 3000")
            return True
        else:
            print("❌ Frontend returned error")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Frontend is not running on port 3000")
        print("   Run: cd frontend && npm run dev")
        return False

def main():
    print("🧪 Testing Voice Agent Dashboard Setup\n")
    
    backend_ok = test_backend()
    frontend_ok = test_frontend()
    
    print("\n📊 Summary:")
    print(f"   Backend: {'✅ Working' if backend_ok else '❌ Not working'}")
    print(f"   Frontend: {'✅ Working' if frontend_ok else '❌ Not working'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 Everything is working! Access the dashboard at http://localhost:3000")
    else:
        print("\n⚠️  Some components need to be started")
        
if __name__ == "__main__":
    main()