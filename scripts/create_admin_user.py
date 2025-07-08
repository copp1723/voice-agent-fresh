#!/usr/bin/env python3
"""
Create default admin user for the voice agent system
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import create_app
from src.models.user import User, db
from src.services.auth import auth_service

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print("Admin user already exists")
            return
        
        try:
            # Create admin user
            admin = auth_service.create_user(
                username='admin',
                email='admin@akillionvoice.xyz',
                password='admin123!',  # Change this in production!
                role='admin'
            )
            
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123! (Please change this immediately!)")
            print("Email: admin@akillionvoice.xyz")
            
        except Exception as e:
            print(f"Error creating admin user: {e}")

if __name__ == '__main__':
    create_admin_user()