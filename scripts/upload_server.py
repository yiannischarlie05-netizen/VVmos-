#!/usr/bin/env python3
"""Simple HTTP upload server - accepts PUT requests to save files."""
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

UPLOAD_DIR = "/tmp/os_extract"

class UploadHandler(BaseHTTPRequestHandler):
    def do_PUT(self):
        # Sanitize path to prevent directory traversal
        path = self.path.lstrip("/")
        basename = os.path.basename(path)
        if not basename or ".." in path:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad filename")
            return

        length = int(self.headers.get("Content-Length", 0))
        filepath = os.path.join(UPLOAD_DIR, basename)

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        with open(filepath, "wb") as f:
            remaining = length
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 1024 * 1024))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)

        size = os.path.getsize(filepath)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"OK: {basename} ({size} bytes)\n".encode())
        print(f"  Saved: {basename} ({size:,} bytes)")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        files = os.listdir(UPLOAD_DIR) if os.path.isdir(UPLOAD_DIR) else []
        self.wfile.write(f"Upload server ready. Files: {len(files)}\n".encode())
        for f in sorted(files):
            size = os.path.getsize(os.path.join(UPLOAD_DIR, f))
            self.wfile.write(f"  {f} ({size:,} bytes)\n".encode())

    def log_message(self, format, *args):
        pass  # Suppress default logging

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 19000
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    server = HTTPServer(("0.0.0.0", port), UploadHandler)
    print(f"Upload server listening on port {port}, saving to {UPLOAD_DIR}")
    server.serve_forever()
