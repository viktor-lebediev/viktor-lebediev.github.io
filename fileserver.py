import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
import cgi
import base64

UPLOAD_DIR = "/mnt/plex"
os.makedirs(UPLOAD_DIR, exist_ok=True)

USERNAME = "kosa"
PASSWORD = "z11x32"

def check_auth(headers):
    auth_header = headers.get('Authorization')
    if auth_header is None or not auth_header.startswith('Basic '):
        return False
    encoded = auth_header.split(' ', 1)[1].strip()
    decoded = base64.b64decode(encoded).decode('utf-8')
    user, pwd = decoded.split(':', 1)
    return user == USERNAME and pwd == PASSWORD

class AuthHTTPRequestHandler(SimpleHTTPRequestHandler):

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Upload Server"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def authenticate(self):
        if not check_auth(self.headers):
            self.do_AUTHHEAD()
            self.wfile.write(b'Authentication required.')
            return False
        return True

    def do_POST(self):
        if not self.authenticate():
            return
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        fileitem = form['file']
        if fileitem.filename:
            filename = os.path.basename(fileitem.filename)
            filepath = os.path.join(UPLOAD_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(fileitem.file.read())
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'File uploaded successfully.')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'No file uploaded.')

    def do_GET(self):
        if not self.authenticate():
            return
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"""
                <html><body>
                <h1>Upload file</h1>
                <form enctype="multipart/form-data" method="post">
                <input name="file" type="file"/>
                <input type="submit" value="Upload"/>
                </form>
                <hr>
                <a href="/files">View uploaded files</a>
                </body></html>
            """)
        elif self.path.startswith('/files'):
            requested_file = unquote(self.path[len('/files'):]).lstrip('/')
            target_path = os.path.join(UPLOAD_DIR, requested_file)
            if os.path.isdir(target_path) or requested_file == '':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<html><body><h2>Uploaded files:</h2><ul>")
                for filename in os.listdir(UPLOAD_DIR):
                    self.wfile.write(f'<li><a href="/files/{filename}">{filename}</a></li>'.encode())
                self.wfile.write(b"</ul></body></html>")
            elif os.path.isfile(target_path):
                self.send_response(200)
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(target_path)}"')
                self.end_headers()
                with open(target_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "Not Found")

if __name__ == '__main__':
    port = 8000
    print(f"Serving on port {port} with Basic Auth")
    httpd = HTTPServer(('', port), AuthHTTPRequestHandler)
    httpd.serve_forever()
