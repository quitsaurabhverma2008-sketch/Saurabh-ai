#!/usr/bin/env python
"""
Saurabh AI - PythonAnywhere Deployment Helper

This file helps configure Saurabh AI for PythonAnywhere hosting.

Instructions:
1. Upload all files to PythonAnywhere (use Files tab or Git clone)
2. Create virtual environment in PythonAnywhere Bash:
   mkvirtualenv --python=/usr/bin/python3.11 saurabh-ai
   pip install -r requirements.txt
3. Go to Web tab → Add new web app
4. Configure:
   - Virtualenv: /home/YOUR_USERNAME/.virtualenvs/saurabh-ai
   - Working directory: /home/YOUR_USERNAME/saurabh-ai
   - WSGI config file: /home/YOUR_USERNAME/saurabh-ai/wsgi.py
5. Static files configuration in PythonAnywhere:
   - URL: /static/
   - Directory: /home/YOUR_USERNAME/saurabh-ai/
6. Edit wsgi.py if needed to point to main:app
7. Reload the web app

Good luck! 🚀
"""

import os
import sys

# Your PythonAnywhere username
PYTHONANYWHERE_USERNAME = "your_username_here"

# Domain will be: your_username.pythonanywhere.com

# Required files to upload:
REQUIRED_FILES = [
    "backend/server.py",
    "main.py", 
    "wsgi.py",
    "requirements.txt",
    "index.html",
    "memory_system.js",
    "css/main.css",
    "css/theme.js",
    "auth/login.html",
    "config/api_keys.json",  # Make sure this is in .gitignore!
]

# Static files directories (configure in PythonAnywhere Web tab):
STATIC_URLS = {
    "/static/": "/home/YOUR_USERNAME/saurabh-ai/",
    "/css/": "/home/YOUR_USERNAME/saurabh-ai/css/",
    "/auth/": "/home/YOUR_USERNAME/saurabh-ai/auth/",
}

def check_environment():
    """Check if running on PythonAnywhere"""
    on_pa = "pythonanywhere" in os.environ.get("HOSTNAME", "")
    print(f"Running on PythonAnywhere: {on_pa}")
    return on_pa

if __name__ == "__main__":
    print("=" * 50)
    print("Saurabh AI - PythonAnywhere Deployment Helper")
    print("=" * 50)
    check_environment()
    print("\nPlease follow the instructions above!")
    print("\nOnce deployed, your site will be at:")
    print(f"https://{PYTHONANYWHERE_USERNAME}.pythonanywhere.com")
