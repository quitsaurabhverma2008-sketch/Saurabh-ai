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

# Import the FastAPI app from server.py
from server import app

# This is the WSGI callable for PythonAnywhere
# Using uvicorn's ASGI-to-WSGI bridge
def get_wsgi_application():
    """Get WSGI application for PythonAnywhere"""
    try:
        # Try using uvicorn if available
        from uvicorn.main import get_wsgi_server
        return app
    except ImportError:
        return app

# For PythonAnywhere, we'll use the app directly
# The key is that the variable must be named 'application'
try:
    from fastapi import FastAPI
    from starlette.middleware.wsgi import WSGIMiddleware
    
    # Use Starlette's WSGI middleware
    application = WSGIMiddleware(app)
except Exception as e:
    # Fallback - use the app directly
    print(f"WSGI middleware error: {e}")
    application = app

# Make sure app works
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
