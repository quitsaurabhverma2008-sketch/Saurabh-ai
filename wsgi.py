"""
Saurabh AI - WSGI Wrapper for PythonAnywhere
FastAPI to WSGI conversion using uvicorn
"""

import sys
import os

# Add project to path
project_path = os.path.dirname(os.path.abspath(__file__))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Also add backend folder
backend_path = os.path.join(project_path, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change to project directory
os.chdir(project_path)

# Import FastAPI app
from main import application

# PythonAnywhere WSGI expects 'application' variable
application = application