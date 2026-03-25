"""
Simple HTTP server for Saurabh AI Frontend
"""
import http.server
import socketserver
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

print(f"Starting frontend server at http://localhost:{PORT}")
print(f"Serving files from: {DIRECTORY}")
print("Press Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    httpd.serve_forever()
