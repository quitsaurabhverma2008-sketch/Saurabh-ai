"""
Saurabh AI - WSGI Wrapper for PythonAnywhere
FastAPI to WSGI conversion
"""

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_path))
sys.path.insert(0, str(project_path / 'backend'))

# Set working directory
os.chdir(str(project_path))

# Import FastAPI app
from server import app

# For PythonAnywhere, we use uvicorn to run the app
# The actual run command will be in the PythonAnywhere web config:
# Source virtualenv: /home/yourusername/.virtualenvs/saurabh-ai
# Working directory: /home/yourusername/saurabh-ai
# WSGI config file: /home/yourusername/saurabh-ai/wsgi.py

# For static files, we'll handle separately in PythonAnywhere dashboard

# This is the WSGI callable that PythonAnywhere will use
# Actually we need to use a different approach - use uvicorn directly

def application(environ, start_response):
    """
    WSGI application wrapper
    Note: For FastAPI on PythonAnywhere, we use uvicorn directly
    This file is mainly for reference
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    # Configure CORS for PythonAnywhere
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Forward to the actual app
    return app(environ, start_response)
