"""Loopback-only report UI and credential-safe status proxy."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
from urllib.parse import parse_qs, urlsplit


def serve(port=8768):
    from .__main__ import FeedError, fetch_feed, summarize

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(Path(__file__).resolve().parent.parent / 'web'), **kwargs)

        def do_GET(self):
            host = self.headers.get('Host', '')
            allowed = {f'127.0.0.1:{port}', f'localhost:{port}'}
            origin = self.headers.get('Origin')
            if host not in allowed or (origin and origin not in {f'http://{h}' for h in allowed}):
                self.send_error(403, 'Local origin required')
                return
            url = urlsplit(self.path)
            if url.path != '/api/status':
                super().do_GET()
                return
            try:
                query = parse_qs(url.query)
                if set(query) - {'last_good'} or query.get('last_good', ['0']) not in (['0'], ['1']):
                    raise FeedError('Unsupported status option.')
                last_good = query.get('last_good') == ['1']
                data = summarize(fetch_feed(os.environ.get('TESLAFI_API_TOKEN'), last_good),
                                 'last complete logged record' if last_good else 'current feed record')
                status = 200
            except FeedError as error:
                status, data = 400, {'error': str(error)}
            payload = json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def end_headers(self):
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            super().end_headers()

        def log_message(self, format, *args):
            # Do not log query strings or incoming headers.
            pass

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'TeslaFi Connect reports: http://127.0.0.1:{port} (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
