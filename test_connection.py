"""Test Supabase database connection"""
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Display loaded configuration (hide password)
print("=== Configuration ===")
print(f"User: {os.getenv('user')}")
print(f"Host: {os.getenv('host')}")
print(f"Port: {os.getenv('port')}")
print(f"Database: {os.getenv('dbname')}")
print(f"Password: {'*' * len(os.getenv('password', ''))}")
print()

# Test connection
from database import engine

try:
    print("Attempting connection...")
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()
        print("✓ Connection successful!")
        print(f"PostgreSQL version: {version[0]}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    import traceback
    traceback.print_exc()
