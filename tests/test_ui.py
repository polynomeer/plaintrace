"""Loopback static-asset and installed-entry contracts, no evidence inputs."""
import argparse
import ast
import http.client
import json
from pathlib import Path
import threading
import re
import unittest
from unittest.mock import patch

from plaintrace import ui
from plaintrace.model import Report

ROOT = Path(__file__).resolve().parents[1]


class WorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ui.create_server()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, path='/', method='GET', headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            conn.request(method, path, headers=headers or {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_only_packaged_assets_and_loopback_bind(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        self.assertIn('text/html', headers['Content-Type'])
        self.assertIn('보고서 열기'.encode(), body)
        self.assertNotIn(b'https://', body)
        self.assertIn('/icons/files.svg', ui.assets())

    def test_scripts_styles_and_icons_have_explicit_types(self):
        for path, expected in [('/app.mjs','text/javascript'),('/core.mjs','text/javascript'),
                               ('/styles.css','text/css'),('/icons/files.svg','image/svg+xml')]:
            with self.subTest(path=path):
                status, headers, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertTrue(headers['Content-Type'].startswith(expected))
                self.assertTrue(body)

    def test_no_working_directory_or_traversal_served(self):
        for path in ['/pyproject.toml','/../pyproject.toml','/%2e%2e/plaintrace/ui.py',
                     '/.git/config','/icons/../../README.md','/support.json']:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)

    def test_host_and_cross_origin_requests_rejected(self):
        for headers in [{'Host':'attacker.invalid'}, {'Origin':'https://attacker.invalid'}]:
            self.assertEqual(self.request(headers=headers)[0], 403)
        self.assertEqual(self.request('http://attacker.invalid/')[0], 403)
        # BaseHTTPRequestHandler may normalize leading // before dispatch.
        self.assertIn(self.request('//[invalid')[0], (403, 404))

    def test_no_upload_or_mutation_methods(self):
        for method in ('POST','PUT','DELETE','PATCH','OPTIONS'):
            with self.subTest(method=method):
                self.assertEqual(self.request('/reports',method)[0], 405)

    def test_head_security_headers_and_query_do_not_expose_files(self):
        status, headers, body = self.request('/?demo=1', 'HEAD')
        self.assertEqual(status, 200)
        self.assertFalse(body)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(headers['X-Frame-Options'], 'DENY')
        self.assertIn("connect-src 'none'", headers['Content-Security-Policy'])
        self.assertIn("script-src 'self'", headers['Content-Security-Policy'])
        self.assertNotIn('Access-Control-Allow-Origin', headers)

    def test_support_projection_matches_registry(self):
        module = (ROOT/'plaintrace/web/support.mjs').read_text(encoding='utf-8')
        projection = json.loads(module.split('export default ',1)[1].rstrip(';\n'))
        registry = json.loads((ROOT/'compatibility/support.json').read_text(encoding='utf-8'))
        self.assertEqual(projection['schema'],Report().as_dict()['format_version'])
        self.assertEqual(projection['adapters'],[{k:a[k] for k in ['id','implementation_maturity','format_predicate','known_gaps']} for a in registry['adapters']])
        self.assertEqual(projection['hosts'],[{k:h[k] for k in ['runner_label','os_family','python_minors','host_qualification']} for h in registry['host_targets']])
        core = (ROOT/'plaintrace/web/core.mjs').read_text(encoding='utf-8')
        names = ast.literal_eval(re.search(r'COLLECTIONS = Object.freeze\((\[[^\n]+\])\)',core)[1])
        self.assertEqual(set(names),set(Report().as_dict()['counts']))

    def test_invalid_port_and_help_do_not_start_server(self):
        for value in ('-1','65536'):
            with self.assertRaises(argparse.ArgumentTypeError):
                ui.port_number(value)
        with patch.object(ui,'create_server') as create:
            with self.assertRaises(SystemExit) as result:
                ui.main(['--help'])
            self.assertEqual(result.exception.code,0)
            create.assert_not_called()

    def test_asset_bundle_has_no_remote_dependencies_or_inline_scripts(self):
        assets = ui.assets()
        html = assets['/index.html'][0].decode()
        self.assertNotIn('<script>',html)
        self.assertIn('type="module" src="app.mjs"',html)
        for name in ('/app.mjs','/core.mjs','/demo.mjs','/support.mjs','/styles.css'):
            self.assertIn(name,assets)
        self.assertTrue((ROOT/'plaintrace/web/icons/LICENSE').is_file())


if __name__ == '__main__':
    unittest.main()
