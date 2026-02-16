"""
WSGI configuration for PythonAnywhere (using a2wsgi adapter)

This file converts the FastAPI ASGI app to WSGI for PythonAnywhere compatibility.

Instructions:
1. Install a2wsgi: pip install a2wsgi
2. Copy this content to your PythonAnywhere WSGI configuration file
3. Replace YOUR_USERNAME with your actual PythonAnywhere username
4. Reload your web app
"""

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/attendance/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Activate virtual environment
activate_this = '/home/YOUR_USERNAME/attendance/backend/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite:///./attendance.db'

# Import FastAPI app
from main import app

# Convert ASGI to WSGI using a2wsgi
from a2wsgi import ASGIMiddleware

# PythonAnywhere expects 'application'
application = ASGIMiddleware(app)
