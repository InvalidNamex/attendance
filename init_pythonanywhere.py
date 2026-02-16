#!/usr/bin/env python
"""
Initialization script for PythonAnywhere deployment

Run this script after uploading your code to PythonAnywhere:
    python init_pythonanywhere.py

This will:
1. Create database tables
2. Initialize default settings
3. Create bootstrap admin user (if not exists)
"""

from database import create_tables, SessionLocal
from models import User, Settings
from auth import hash_password

def initialize_database():
    """Initialize database with tables and default data"""
    
    print("Creating database tables...")
    create_tables()
    print("✓ Database tables created")
    
    db = SessionLocal()
    try:
        # Create default settings if not exists
        existing_settings = db.query(Settings).first()
        if not existing_settings:
            default_settings = Settings(
                latitude=0.0,
                longitude=0.0,
                radius=100,
                in_time="09:00",
                out_time="17:00"
            )
            db.add(default_settings)
            db.commit()
            print("✓ Default settings created")
        else:
            print("✓ Settings already exist")
        
        # Create bootstrap admin user if no users exist
        existing_users = db.query(User).count()
        if existing_users == 0:
            admin_user = User(
                userName="admin",
                password=hash_password("123"),
                deviceID=None,
                isAdmin=True
            )
            db.add(admin_user)
            db.commit()
            print("✓ Bootstrap admin user created")
            print("  Username: admin")
            print("  Password: 123")
            print("  ⚠️  IMPORTANT: Change this password immediately!")
        else:
            print(f"✓ Users already exist ({existing_users} user(s))")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\n✓ Database initialization complete!")
    print("\nYour API should now be ready at:")
    print("  https://YOUR_USERNAME.pythonanywhere.com/docs")

if __name__ == "__main__":
    initialize_database()
