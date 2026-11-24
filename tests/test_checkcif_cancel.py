from __future__ import annotations

import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_bootstrap  # noqa: F401,E402

import requests  # noqa: E402
from qtpy import QtCore  # noqa: E402

from finalcif.cif.checkcif.checkcif import (CheckCif, classify_request_exception)  # noqa: E402


class FakeCif:
    hkl_file: list = []

    def cif_as_string(self, without_hkl: bool = False) -> str:
        return 'data_test\n_test 1\n'


class FakeResponse:
    status_code = 200
    reason = 'OK'
    content = b'<html><body>PLAT041_ALERT_1_C Test</body></html>'


class CheckCifCancelTests(unittest.TestCase):
    def test_classification(self):
        self.assertEqual(classify_request_exception(requests.exceptions.MissingSchema('x')),
                         'URL 无效')
        self.assertEqual(classify_request_exception(requests.exceptions.SSLError('x')),
                         'TLS 错误')
        self.assertEqual(classify_request_exception(requests.exceptions.ConnectTimeout('x')),
                         '连接超时')
        self.assertEqual(classify_request_exception(requests.exceptions.ReadTimeout('x')),
                         '服务器超时')
        self.assertEqual(classify_request_exception(
            requests.exceptions.ConnectionError('getaddrinfo failed')), 'DNS 解析失败')

    def test_cancel_before_request(self):
        with tempfile_outfile() as outfile:
            check = CheckCif(parent=None, cif=FakeCif(), outfile=outfile,
                             url='https://example.invalid/check')
            states = []
            check.state.connect(states.append)
            check.cancel()
            check.run()
            self.assertIn('cancelled', states)
            self.assertFalse(outfile.exists())

    def test_cancel_during_request_discards_result(self):
        with tempfile_outfile() as outfile:
            def slow_post(*args, **kwargs):
                time.sleep(0.35)
                return FakeResponse()

            check = CheckCif(parent=None, cif=FakeCif(), outfile=outfile,
                             url='https://example.invalid/check')
            states, failures = [], []
            check.state.connect(states.append, QtCore.Qt.ConnectionType.DirectConnection)
            check.failed.connect(failures.append, QtCore.Qt.ConnectionType.DirectConnection)
            worker = threading.Thread(target=check.run)
            with mock.patch('finalcif.cif.checkcif.checkcif.requests.post', slow_post):
                worker.start()
                time.sleep(0.1)
                check.cancel()
                worker.join(2)
            self.assertIn('cancelled', states)
            self.assertEqual(failures, [])
            self.assertFalse(outfile.exists())

    def test_http_error_message(self):
        with tempfile_outfile() as outfile:
            def post_503(*args, **kwargs):
                response = FakeResponse()
                response.status_code = 503
                response.reason = 'Service Unavailable'
                return response

            check = CheckCif(parent=None, cif=FakeCif(), outfile=outfile,
                             url='https://example.invalid/check')
            failures = []
            check.failed.connect(failures.append)
            with mock.patch('finalcif.cif.checkcif.checkcif.requests.post', post_503):
                check.run()
            self.assertTrue(failures)
            self.assertIn('503', failures[0])
            self.assertFalse(outfile.exists())


class tempfile_outfile:
    def __enter__(self):
        import tempfile
        self._dir = tempfile.TemporaryDirectory()
        return Path(self._dir.name) / 'result.html'

    def __exit__(self, *args):
        self._dir.cleanup()


if __name__ == '__main__':
    unittest.main()
