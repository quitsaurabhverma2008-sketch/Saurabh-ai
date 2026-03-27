#!/usr/bin/env python3
"""
Saurabh AI - PythonAnywhere Auto-Deploy Script
Run this in PythonAnywhere Bash console to complete deployment
"""

import os
import sys

print("=" * 50)
print("Saurabh AI - Auto Deploy Script")
print("=" * 50)

# Step 1: Update WSGI file
wsgi_path = "/var/www/saurabhai2008_pythonanywhere_com_wsgi.py"

wsgi_content = '''import sys
import os

# Add project to path
sys.path.insert(0, '/home/saurabhai2008/Saurabh-ai')

# Change to project directory
os.chdir('/home/saurabhai2008/Saurabh-ai')

# Import FastAPI app
from main import application
'''

print("\n[1/3] Updating WSGI file...")

try:
    with open(wsgi_path, 'w') as f:
        f.write(wsgi_content)
    print("✓ WSGI file updated!")
except Exception as e:
    print(f"✗ Error: {e}")
    print("Please edit WSGI file manually:")
    print("Path:", wsgi_path)
    sys.exit(1)

print("\n[2/3] WSGI Configuration:")
print("""
The WSGI file now points to:
- Project: /home/saurabhai2008/Saurabh-ai
- App: from main import application
""")

print("\n[3/3] Next Steps:")
print("1. Go to Web tab in PythonAnywhere")
print("2. Click 'Reload' button")
print("3. Visit: https://saurabhai2008.pythonanywhere.com")

print("\n" + "=" * 50)
print("Deployment configuration complete!")
print("=" * 50)