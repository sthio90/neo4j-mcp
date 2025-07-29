#!/usr/bin/env python3
"""
Simple HTTP server to serve the demo HTML files.
This avoids CORS issues by serving the HTML from the same origin as the MCP server.
"""

import http.server
import socketserver
import os
from pathlib import Path

# Change to demo directory
demo_dir = Path(__file__).parent
os.chdir(demo_dir)

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, mcp-session-id')
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

def main():
    print(f"\n🌐 Starting demo web server on http://localhost:{PORT}")
    print("This serves the HTML demo files to avoid CORS issues.")
    print(f"Demo will be available at: http://localhost:{PORT}/index.html")
    print("Press Ctrl+C to stop\n")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping demo server...")

if __name__ == "__main__":
    main()