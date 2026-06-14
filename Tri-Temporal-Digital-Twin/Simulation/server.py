#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation/server.py - Dashboard HTTP Server for T3DT UI
Provides a web interface to view the live dashboard and trigger the high-fidelity simulation.
"""

import http.server
import socketserver
import os
import sys
import json
import subprocess
import threading

PORT = 8000
DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pipeline_thread = None
pipeline_status_msg = "Idle"

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Allow CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        global pipeline_thread, pipeline_status_msg
        
        if self.path == '/api/run_pipeline':
            if pipeline_thread and pipeline_thread.is_alive():
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Pipeline already running"}).encode('utf-8'))
                return

            def run_pipeline():
                global pipeline_status_msg
                pipeline_status_msg = "Running"
                try:
                    # Run the full simulation and figure generation script
                    result = subprocess.run(
                        [sys.executable, "Simulation/run_all.py"],
                        cwd=DIRECTORY,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    if result.returncode == 0:
                        pipeline_status_msg = "Completed successfully"
                    else:
                        pipeline_status_msg = f"Failed with exit code {result.returncode}: {result.stderr}"
                except Exception as e:
                    pipeline_status_msg = f"Execution error: {str(e)}"

            pipeline_thread = threading.Thread(target=run_pipeline, name="PipelineThread")
            pipeline_thread.start()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        global pipeline_status_msg
        
        if self.path == '/api/pipeline_status':
            status = "idle"
            if pipeline_thread and pipeline_thread.is_alive():
                status = "running"
            elif pipeline_status_msg != "Idle" and "Failed" not in pipeline_status_msg and "error" not in pipeline_status_msg:
                status = "completed"
            elif "Failed" in pipeline_status_msg or "error" in pipeline_status_msg:
                status = "failed"
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": status,
                "message": pipeline_status_msg
            }).encode('utf-8'))
            
        elif self.path == '/api/results':
            results_path = os.path.join(DIRECTORY, "analysis_results.md")
            if os.path.exists(results_path):
                try:
                    with open(results_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"content": content}).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Results file not found. Run simulation first."}).encode('utf-8'))
        else:
            # Standard static file serving
            super().do_GET()

def main():
    # Make sure we run in the project root
    os.chdir(DIRECTORY)
    
    # Enable socket address reuse to prevent "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), DashboardHTTPRequestHandler) as httpd:
        print("=====================================================================")
        print(f" T3DT Simulation Dashboard Web Server running on port {PORT}")
        print(f" Open http://localhost:{PORT}/ index.html in your browser to view.")
        print("=====================================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            sys.exit(0)

if __name__ == "__main__":
    main()
