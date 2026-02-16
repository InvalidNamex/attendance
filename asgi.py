"""
ASGI config for PythonAnywhere deployment
"""
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/attendance/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables if needed
os.environ['DATABASE_URL'] = 'sqlite:///./attendance.db'

# Import your FastAPI app
from main import app

# PythonAnywhere will use this
application = app
