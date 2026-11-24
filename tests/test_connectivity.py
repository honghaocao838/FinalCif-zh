from __future__ import annotations

import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_bootstrap  # noqa: F401,E402

from qtpy.QtWidgets import QApplication  # noqa: E402

from finalcif.tools.connectivity import ConnectivityTest  # noqa: E402

app = QApplication.instance() or QApplication([])


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *args):
        pass


class ConnectivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _run(self, url):
        results = []
        test = ConnectivityTest(url)
        test.result.connect(lambda *args: results.append(args))
        test.run()
        return results[-1]

    def test_success(self):
        ok, message, status, elapsed = self._run(f'http://127.0.0.1:{self.port}/')
        self.assertTrue(ok)
        self.assertEqual(status, 200)
        self.assertIn('可连通', message)

    def test_invalid_url(self):
        ok, message, status, _ = self._run('not-a-url')
        self.assertFalse(ok)
        self.assertEqual(message, 'URL 无效')

    def test_connection_refused(self):
        # Bind and close a port so that it is almost certainly closed.
        import socket
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        sock.close()
        ok, message, status, _ = self._run(f'http://127.0.0.1:{port}/')
        self.assertFalse(ok)
        self.assertIn(message, {'网络不可达', '连接超时'})


if __name__ == '__main__':
    unittest.main()
