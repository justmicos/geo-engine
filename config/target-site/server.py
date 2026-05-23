"""GEOEngine target site example server. Listens for distributed content."""
import http.server, json, os

class Handler(http.server.BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    def do_GET(self):
        if self.path == '/agent/health':
            self._json({"status":"ok","version":"2.0"})
        else:
            self._json({"error":"not_found"},404)
    def do_POST(self):
        length = int(self.headers.get('Content-Length',0))
        body = json.loads(self.rfile.read(length)) if length else {}
        if self.path == '/agent/articles':
            print(f"Article received: {body.get('title','?')}")
            self._json({"status":"accepted","article_id":body.get('article_id')},201)
        elif self.path == '/agent/sync-settings':
            self._json({"status":"synced"})
        else:
            self._json({"error":"not_found"},404)
    def log_message(self,*a): pass

if __name__ == '__main__':
    port = int(os.environ.get('TARGET_PORT',3459))
    http.server.HTTPServer(('0.0.0.0',port), Handler).serve_forever()
