"""
Saurabh AI - Main entry point for PythonAnywhere
WSGI-compatible wrapper for FastAPI
"""

import sys
import os

# Add project directories to path
project_root = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Change to project directory
os.chdir(project_root)

# Import the FastAPI app from backend/server.py
from backend.server import app

# For PythonAnywhere WSGI, use asgiref to convert ASGI to WSGI
# This is the correct way to bridge FastAPI (ASGI) to WSGI
try:
    from asgiref.wsgi import ASGIHandler
    application = ASGIHandler(app)
except ImportError:
    # Fallback - just use the app directly (might not work)
    application = app

# For local development (uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)