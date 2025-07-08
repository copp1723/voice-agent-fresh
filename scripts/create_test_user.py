#!/usr/bin/env python3
"""
Create a test user for the dashboard
"""
import os
import sys
# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
from src.models import db
from src.models.user import User

# Create a simple Flask app context
from flask import Flask
app = Flask(__name__)

# Use SQLite for simplicity
db_path = os.path.join(os.path.dirname(__file__), 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    
    # Check if admin user exists
    existing_user = User.query.filter_by(email='admin@akillionvoice.xyz').first()
    
    if existing_user:
        print("❌ Admin user already exists!")
        print(f"   Email: {existing_user.email}")
        print(f"   Role: {existing_user.role}")
    else:
        # Create admin user
        admin_user = User(
            email='admin@akillionvoice.xyz',
            password_hash=generate_password_hash('admin123'),
            username='Admin User',
            role='admin',
            is_active=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✅ Test user created successfully!")
        print("   Email: admin@akillionvoice.xyz")
        print("   Password: admin123")
        print("   Role: admin")
        
    print("\n📝 You can now login at http://localhost:3000/login")