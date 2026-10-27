#!/usr/bin/env python3
"""Verify installed workbench assets and loopback serving outside the checkout."""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import threading
from zipfile import ZipFile


def verify(wheel):
    from plaintrace import ui
    checkout = Path(__file__).resolve().parents[1]
    installed = Path(ui.__file__).resolve()
    if installed.is_relative_to(checkout):
        raise RuntimeError('Installed smoke imported the checkout')
    resources = ui.assets()
    with ZipFile(wheel) as archive:
        names = [n for n in archive.namelist() if n.startswith('plaintrace/web/') and not n.endswith('/')]
        if not names:
            raise RuntimeError('Wheel contains no workbench assets')
        for name in names:
            if (installed.parent.parent / name).read_bytes() != archive.read(name):
                raise RuntimeError('Installed asset differs from wheel: ' + name)
        for route, (data, _mime) in resources.items():
            name = 'plaintrace/web/' + ('index.html' if route == '/' else route.lstrip('/'))
            if data != archive.read(name):
                raise RuntimeError('Served asset differs from wheel: ' + route)
    console = Path(sysconfig.get_path('scripts')) / ('plaintrace-ui.exe' if os.name == 'nt' else 'plaintrace-ui')
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
    for command in ([str(console), '--help'], [sys.executable, '-I', '-m', 'plaintrace.ui', '--help']):
        result = subprocess.run(command, env=env, capture_output=True, timeout=30, check=True)
        if b'--port' not in result.stdout:
            raise RuntimeError('Workbench entry-point help is incomplete')
    with ui.create_server() as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for route, (data, mime) in resources.items():
                connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
                try:
                    connection.request('GET', route)
                    response = connection.getresponse()
                    if response.status != 200 or response.getheader('Content-Type') != mime or response.read() != data:
                        raise RuntimeError('Installed HTTP asset mismatch: ' + route)
                    if "connect-src 'none'" not in response.getheader('Content-Security-Policy', ''):
                        raise RuntimeError('Installed CSP missing')
                finally:
                    connection.close()
        finally:
            server.shutdown()
            thread.join(timeout=10)
    return {'status': 'passed', 'import_location': 'outside_checkout', 'served_routes': len(resources),
            'wheel_assets': len(names), 'wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
            'checks': ['wheel_asset_bytes', 'console_and_isolated_module_help', 'loopback_http_assets_and_csp'],
            'browser_rendering': 'not_tested'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.wheel.resolve()), indent=2))


if __name__ == '__main__':
    main()
