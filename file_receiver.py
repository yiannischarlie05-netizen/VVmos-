#!/usr/bin/env python3
"""Simple HTTP file receiver for extracting data from VMOS devices."""
import http.server
import os
import sys

UPLOAD_DIR = "/root/CascadeProjects/vmos-titan-unified/neighbor_clones"
PORT = 8888

os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadHandler(http.server.BaseHTTPRequestHandler):
    def _receive_body(self, filename):
        """Read request body and save to file."""
        length = int(self.headers.get('Content-Length', 0))
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            remaining = length
            while remaining > 0:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        size = os.path.getsize(filepath)
        print(f"[RECEIVED] {filename}: {size:,} bytes", flush=True)
        return size

    def do_PUT(self):
        filename = os.path.basename(self.path.strip('/'))
        if not filename:
            self.send_response(400)
            self.end_headers()
            return
        size = self._receive_body(filename)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"OK {size}".encode())

    def do_POST(self):
        filename = os.path.basename(self.path.strip('/')) or 'upload.bin'
        size = self._receive_body(filename)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"OK {size}".encode())
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        """Health check."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"CLONE_RECEIVER_OK")

    def log_message(self, format, *args):
        print(f"[HTTP] {args[0]}")

print(f"Starting file receiver on 0.0.0.0:{PORT}")
print(f"Upload dir: {UPLOAD_DIR}")
server = http.server.HTTPServer(('0.0.0.0', PORT), UploadHandler)
server.serve_forever()
