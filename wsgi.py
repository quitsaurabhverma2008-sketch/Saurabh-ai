"""
Saurabh AI - WSGI Wrapper for PythonAnywhere
Simple wrapper for FastAPI ASGI app
"""

import sys
import os

# Path setup
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

# Change working directory
os.chdir(path)

# Import the ASGI app
from backend.server import app

# Create a simple WSGI wrapper for health checks
# Note: PythonAnywhere's free tier uses WSGI, not ASGI
# For full ASGI support, you need a paid plan or use their manual uvicorn setup

# Simple WSGI application for health checks
def simple_app(environ, start_response):
    """Simple WSGI app for basic routing"""
    path_info = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Health check endpoint
    if path_info == '/health' or path_info == '/':
        status = '200 OK'
        response = b'Saurabh AI Backend - Running!'
    elif path_info == '/api':
        status = '200 OK'
        response = b'{"status": "ok", "service": "saurabh-ai"}'
    else:
        # For all other routes, return 404
        # PythonAnywhere WSGI doesn't support ASGI properly
        # Full support needs paid plan or manual uvicorn
        status = '404 Not Found'
        response = b'Not Found - Use /health or /api'
    
    start_response(status, [('Content-Type', 'text/plain')])
    return [response]

# Export for PythonAnywhere
# Note: For full ASGI functionality on PythonAnywhere,
# you need to use their Consoles to run:
# uvicorn backend.server:app --host 0.0.0.0 --port 8000
application = simple_app
