"""Asynchronous reachability test for the CheckCIF server."""
from __future__ import annotations

import time
from urllib.parse import urlsplit

import requests
from qtpy import QtCore


def connectivity_advice() -> str:
    return '建议：检查系统代理设置；检查选项中的 CheckCIF 服务器地址；用浏览器打开该地址确认。'


def classify_exception(exc: Exception) -> str:
    message = str(exc).lower()
    if isinstance(exc, (requests.exceptions.MissingSchema,
                        requests.exceptions.InvalidSchema,
                        requests.exceptions.InvalidURL)):
        return 'URL 无效'
    if isinstance(exc, requests.exceptions.SSLError):
        return 'TLS 错误'
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return '连接超时'
    if isinstance(exc, (requests.exceptions.ReadTimeout, requests.exceptions.Timeout)):
        return '服务器超时'
    if isinstance(exc, requests.exceptions.ConnectionError):
        if any(marker in message for marker in (
                'name or service not known', 'nodename nor servname',
                'getaddrinfo', 'temporary failure in name resolution',
                'no address associated with hostname')):
            return 'DNS 解析失败'
        if 'proxy' in message:
            return '代理错误'
        return '网络不可达'
    if isinstance(exc, requests.exceptions.RequestException):
        return f'连接失败：{str(exc)[:120]}'
    return f'连接失败：{str(exc)[:120]}'


class ConnectivityTest(QtCore.QThread):
    """GET the server root address in a worker thread.

    Emits ``(ok, message, http_status, elapsed_ms)``.  A 4xx/5xx response still
    means the server is reachable; only transport errors are reported as
    failures.
    """

    result = QtCore.Signal(bool, str, int, float)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url or ''

    def run(self) -> None:
        parsed = urlsplit(self.url.strip())
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            self.result.emit(False, 'URL 无效', 0, 0.0)
            return
        root = f'{parsed.scheme}://{parsed.netloc}/'
        start = time.perf_counter()
        try:
            response = requests.get(root, timeout=5, allow_redirects=True,
                                    headers={'User-Agent': 'FinalCif-zh connectivity test'})
        except Exception as exc:  # requests exceptions and DNS errors
            self.result.emit(False, classify_exception(exc), 0,
                             (time.perf_counter() - start) * 1000)
            return
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.result.emit(True, f'可连通，延迟 {elapsed_ms:.0f} ms，HTTP {response.status_code}',
                         int(response.status_code), elapsed_ms)
