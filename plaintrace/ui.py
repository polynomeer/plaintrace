"""Offline report workbench: serve packaged assets on IPv4 loopback only.

No evidence paths, upload endpoints or parser invocation are exposed. Browser
file selection reads schema-15 JSON in browser memory, never through this server.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import sys
from urllib.parse import urlsplit
import webbrowser

MIME = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
        '.mjs': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml'}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
       "font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; "
       "form-action 'none'; frame-ancestors 'none'")


def assets():
    """Read only known packaged resource types; never serve a working directory."""
    result = {}
    root = files('plaintrace').joinpath('web')
    for entry in root.iterdir():
        suffix = '.' + entry.name.rsplit('.', 1)[-1]
        if entry.is_file() and suffix in MIME:
            result['/' + entry.name] = (entry.read_bytes(), MIME[suffix])
    for entry in root.joinpath('icons').iterdir():
        if entry.is_file() and entry.name.endswith('.svg'):
            result['/icons/' + entry.name] = (entry.read_bytes(), MIME['.svg'])
    result['/'] = result['/index.html']
    return result


def handler_for(resources):
    class ViewerHandler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # No request paths, report names or browser metadata in logs.

        def respond(self, head=False):
            origin = f'http://127.0.0.1:{self.server.server_port}'
            try:
                parsed = urlsplit(self.path)
            except ValueError:
                return self.reject(403)
            if (self.headers.get('Host') != origin.removeprefix('http://') or
                    self.headers.get('Origin', origin) != origin or parsed.scheme or parsed.netloc):
                return self.reject(403)
            entry = resources.get(parsed.path)
            if entry is None:
                return self.reject(404)
            data, mime = entry
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Content-Security-Policy', CSP)
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            if not head:
                self.wfile.write(data)

        def reject(self, status):
            self.send_response(status)
            self.send_header('Content-Length', '0')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()

        def do_GET(self):
            self.respond()

        def do_HEAD(self):
            self.respond(head=True)

        def do_POST(self):
            self.reject(405)

        do_PUT = do_POST
        do_DELETE = do_POST
        do_PATCH = do_POST
        do_OPTIONS = do_POST

    return ViewerHandler


def create_server(port=0):
    return ThreadingHTTPServer(('127.0.0.1', port), handler_for(assets()))


def port_number(value):
    number = int(value)
    if not 0 <= number <= 65535:
        raise argparse.ArgumentTypeError('port must be between 0 and 65535')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=port_number, default=0, help='Loopback port; default chooses a free port')
    parser.add_argument('--open', action='store_true', help='Open the local workbench in your browser')
    args = parser.parse_args(argv)
    try:
        with create_server(args.port) as server:
            url = f'http://127.0.0.1:{server.server_port}/'
            print(f'Plaintrace workbench: {url}', flush=True)
            print('Read-only report viewer. Stop with Ctrl+C.', flush=True)
            if args.open:
                webbrowser.open(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
        return 0
    except OSError as error:
        print(f'plaintrace-ui: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
