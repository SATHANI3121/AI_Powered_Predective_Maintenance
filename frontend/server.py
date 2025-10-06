#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def main():
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    # Server configuration
    PORT = 3000
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🌐 Frontend server starting...")
            print(f"📁 Serving from: {frontend_dir}")
            print(f"🔗 Frontend URL: http://localhost:{PORT}")
            print(f"🔗 API URL: http://localhost:8000")
            print(f"📊 API Docs: http://localhost:8000/docs")
            print(f"\n✨ Opening browser...")
            
            # Open browser
            webbrowser.open(f'http://localhost:{PORT}')
            
            print(f"\n🚀 Server running! Press Ctrl+C to stop.")
            print(f"💡 Make sure your API server is running on port 8000")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped.")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Trying port {PORT + 1}...")
            PORT += 1
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"🔗 Frontend URL: http://localhost:{PORT}")
                webbrowser.open(f'http://localhost:{PORT}')
                httpd.serve_forever()
        else:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()

