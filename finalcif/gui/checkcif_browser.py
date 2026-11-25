from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

import requests
from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices, QImage, QTextDocument
from qtpy.QtWidgets import QDialog, QTextBrowser, QToolTip, QVBoxLayout, QWidget

from finalcif.cif.prefilter import load_prefilter, lookup_prefilter, format_prefilter_help
from finalcif.cif.checkcif_tests import (load_checkcif_tests, lookup_checkcif_test,
                                         format_checkcif_test_help)

_IMG_SRC = re.compile(r'<img[^>]*\bsrc\s*=\s*["\']?([^"\'>\s]+)', re.IGNORECASE)
# Matches the checkCIF help popup links, e.g.: javascript:makeHelpWindow("PLAT042.html")
_HELP_WINDOW_LINK = re.compile(r'makeHelpWindow\(["\']?([A-Za-z][A-Za-z0-9_]*)\.html["\']?\)', re.IGNORECASE)
_PREFILTER_LINK = re.compile(r"makeHelpWindow.{0,3}prefilter.html#([A-Za-z0-9_]+)", re.IGNORECASE)
# The small alert-level logos, e.g. ".../iucr-top/logos/yellow.gif". IUCr's server is behind
# Cloudflare bot protection and refuses these requests, so a same-colored square is drawn locally.
_ALERT_LOGO = re.compile(r'/logos/(\w+)\.gif$', re.IGNORECASE)


class CheckCifBrowser(QTextBrowser):
    """A QTextBrowser that renders the images embedded in CheckCIF HTML results.

    QTextBrowser only resolves resources lazily on paint and never fetches network
    resources, so the IUCr alert-level logos and the structure image stay blank.
    All ``<img>`` sources are therefore downloaded up front and registered as
    document resources before the HTML is set.

    The CheckCIF HTML also contains ``javascript:makeHelpWindow(...)`` links that
    are meant to pop up a small help window explaining the PLATON alert. Since
    QTextBrowser cannot execute JavaScript, these links are intercepted and the
    matching help text (parsed from PLATON's ``check.def``) is shown in a
    dialog instead.
    """

    def __init__(self, parent: QWidget | None = None, checkdef: list[str] | None = None) -> None:
        super().__init__(parent)
        self.checkdef = checkdef or []
        self.setOpenLinks(False)
        self.anchorClicked.connect(self._on_anchor_clicked)
        self._image_cache: dict[str, QImage] = {}
        self._help_dialog: QDialog | None = None
        self._help_cache: dict[str, str] = {}
        self._prefilter = load_prefilter()
        self._checkcif_tests = load_checkcif_tests()
        self._last_tooltip_alert = ''
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setToolTip('将鼠标移到 PLAT 编号上可预览中文解释；点击打开完整帮助。')

    def set_checkcif_html(self, html: str, local_images: dict[str, Path] | None = None) -> None:
        """Register every embedded image, then display the HTML.

        Args:
            html: The CheckCIF result HTML.
            local_images: Optional mapping of image ``src`` URL → local file path to
                use instead of downloading (e.g. the locally saved structure image).
        """
        local_images = local_images or {}
        for src in dict.fromkeys(_IMG_SRC.findall(html)):
            image = self._load_image(src, local_images.get(src))
            if not image.isNull():
                self.document().addResource(QTextDocument.ResourceType.ImageResource, QUrl(src), image)
        self.setHtml(html)

    def _load_image(self, src: str, local_file: Path | None) -> QImage:
        if src in self._image_cache:
            return self._image_cache[src]
        image = QImage()
        if local_file and local_file.exists():
            image.load(str(local_file))
        if image.isNull() and src.startswith(('http://', 'https://')):
            try:
                image.loadFromData(requests.get(src, timeout=10).content)
            except requests.RequestException:
                pass
        self._image_cache[src] = image
        return image

    def _help_text(self, alert: str) -> str:
        """Return the full help text for *alert*, cached for hover previews."""
        if alert not in self._help_cache:
            if alert.upper().startswith('PLAT'):
                from finalcif.cif.checkcif.checkcif import AlertHelp
                self._help_cache[alert] = AlertHelp(self.checkdef).get_help(alert) or ''
            else:
                entry = lookup_prefilter(self._prefilter, alert)
                if entry:
                    self._help_cache[alert] = format_prefilter_help(alert, entry)
                else:
                    test = lookup_checkcif_test(self._checkcif_tests, alert)
                    self._help_cache[alert] = (
                        format_checkcif_test_help(alert, test) if test else '')
        return self._help_cache[alert]

    @staticmethod
    def _chinese_only(helptext: str) -> str:
        marker = '【English 原文'
        if marker in helptext:
            helptext = helptext.split(marker, 1)[0]
        return helptext.replace('【中文】', '').strip()

    def _alert_preview(self, alert: str) -> str:
        text = self._chinese_only(self._help_text(alert))
        if not text:
            return f'{alert}：暂无中文解释。'
        text = re.sub(r'\s+', ' ', text)
        if len(text) > 320:
            text = text[:320].rstrip() + '…'
        return f'{alert}\n{text}'

    def mouseMoveEvent(self, event) -> None:
        anchor = self.anchorAt(event.pos())
        text = unquote(anchor or '')
        match = _PREFILTER_LINK.search(text) or _HELP_WINDOW_LINK.search(text)
        if match:
            alert = match.group(1)
            if alert != self._last_tooltip_alert:
                QToolTip.showText(self.mapToGlobal(event.pos()),
                                  self._alert_preview(alert), self)
                self._last_tooltip_alert = alert
        elif self._last_tooltip_alert:
            QToolTip.hideText()
            self._last_tooltip_alert = ''
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        QToolTip.hideText()
        self._last_tooltip_alert = ''
        super().leaveEvent(event)

    def _on_anchor_clicked(self, url: QUrl) -> None:
        """Handle link clicks: show a help dialog for PLATON alert links, open others externally."""
        text = unquote(url.toString())
        match = _PREFILTER_LINK.search(text) or _HELP_WINDOW_LINK.search(text)
        if match:
            self._show_help_window(match.group(1))
            return
        QDesktopServices.openUrl(url)

    def _show_help_window(self, alert: str) -> None:
        """Open a small dialog showing the PLATON alert explanation.

        Args:
            alert: The alert code, e.g. ``PLAT042``.
        """
        helptext = self._help_text(alert) or f'未找到帮助文本：{alert}.'
        dialog = QDialog(self)
        dialog.setWindowTitle(f'checkCIF 帮助：{alert}')
        dialog.resize(600, 350)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser(dialog)
        browser.setPlainText(helptext)
        layout.addWidget(browser)
        self._help_dialog = dialog
        dialog.show()

