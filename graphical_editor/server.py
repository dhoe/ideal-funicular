#!/usr/bin/env python3
"""
Graphical Code Editor - HTTP Server

A simple HTTP server that:
1. Serves the static frontend files
2. Provides an API endpoint to parse Python code
3. Can parse entire directories

Usage:
    python server.py [port] [directory_to_parse]

Examples:
    python server.py                    # Start on port 8000
    python server.py 3000               # Start on port 3000
    python server.py 8000 ./my_project  # Parse ./my_project on startup
"""

import http.server
import json
import os
import sys
import urllib.parse
from pathlib import Path
from functools import partial

# Import our code parser
from code_parser import CodeParser, parse_directory, module_to_dict


class GraphicalEditorHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the Graphical Code Editor"""

    def __init__(self, *args, static_dir=None, initial_modules=None, **kwargs):
        self.static_dir = static_dir or os.path.join(os.path.dirname(__file__), 'static')
        self.initial_modules = initial_modules or []
        super().__init__(*args, directory=self.static_dir, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == '/api/modules':
            # Return initial modules if any
            self.send_json_response(self.initial_modules)
        elif parsed_path.path == '/api/health':
            self.send_json_response({'status': 'ok'})
        else:
            # Serve static files
            super().do_GET()

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == '/api/parse':
            self.handle_parse_code()
        elif parsed_path.path == '/api/parse-directory':
            self.handle_parse_directory()
        else:
            self.send_error(404, 'Not Found')

    def handle_parse_code(self):
        """Parse Python source code submitted via POST"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            source = data.get('source', '')
            filename = data.get('filename', 'module.py')

            parser = CodeParser(source, filename)
            module = parser.parse_module()
            result = module_to_dict(module)

            self.send_json_response(result)

        except json.JSONDecodeError as e:
            self.send_error_response(400, f'Invalid JSON: {e}')
        except SyntaxError as e:
            self.send_error_response(400, f'Python syntax error: {e}')
        except Exception as e:
            self.send_error_response(500, f'Server error: {e}')

    def handle_parse_directory(self):
        """Parse all Python files in a directory"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            directory = data.get('directory', '.')

            if not os.path.isdir(directory):
                self.send_error_response(400, f'Directory not found: {directory}')
                return

            modules = parse_directory(directory)
            result = [module_to_dict(m) for m in modules]

            self.send_json_response(result)

        except json.JSONDecodeError as e:
            self.send_error_response(400, f'Invalid JSON: {e}')
        except Exception as e:
            self.send_error_response(500, f'Server error: {e}')

    def send_json_response(self, data):
        """Send a JSON response"""
        response = json.dumps(data, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def send_error_response(self, code, message):
        """Send an error response"""
        response = json.dumps({'error': message})
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {args[0]}")


def run_server(port=8000, directory=None):
    """Run the HTTP server"""
    # Parse initial directory if provided
    initial_modules = []
    if directory and os.path.isdir(directory):
        print(f"Parsing Python files in: {directory}")
        modules = parse_directory(directory)
        initial_modules = [module_to_dict(m) for m in modules]
        print(f"Found {len(initial_modules)} Python modules")

    # Create handler with initial modules
    static_dir = os.path.join(os.path.dirname(__file__), 'static')

    handler = partial(
        GraphicalEditorHandler,
        static_dir=static_dir,
        initial_modules=initial_modules
    )

    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, handler)

    print(f"""
╔════════════════════════════════════════════════════════════╗
║          🔍 Graphical Code Editor                          ║
╠════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:{port:<5}                ║
║                                                            ║
║  Zoom Levels:                                              ║
║    • Level 1 (zoom out): Architecture view                 ║
║    • Level 2 (normal):   Function signatures               ║
║    • Level 3 (zoom in):  Full code                         ║
║                                                            ║
║  Controls:                                                 ║
║    • Scroll/pinch to zoom                                  ║
║    • Drag to pan                                           ║
║    • Click nodes to see code                               ║
║                                                            ║
║  Press Ctrl+C to stop the server                           ║
╚════════════════════════════════════════════════════════════╝
""")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


if __name__ == '__main__':
    port = 8000
    directory = None

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            directory = sys.argv[1]

    if len(sys.argv) > 2:
        directory = sys.argv[2]

    run_server(port, directory)
