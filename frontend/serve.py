"""
serve.py — Static file server for SmartDoc AI frontend
Run this in the same folder as index.html, style.css, script.js

Usage:
    python serve.py

Then open: http://localhost:3000
"""

import http.server
import socketserver
import os

PORT = 3000

# Serve files from the same directory as this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"✅ SmartDoc AI frontend running at: http://localhost:{PORT}")
    print("   Press Ctrl+C to stop.")
    httpd.serve_forever()
