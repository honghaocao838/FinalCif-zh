"""Summary bar for CheckCIF results and the per-level alert list."""
from __future__ import annotations

import re

from qtpy import QtCore, QtWidgets

from finalcif.cif.checkcif.summary import AlertItem, CheckCifSummary, LEVELS
from finalcif.cif.prefilter import load_prefilter, lookup_prefilter, format_prefilter_help
from finalcif.cif.checkcif_tests import (load_checkcif_tests, lookup_checkcif_test,
                                         format_checkcif_test_help)

_LEVEL_COLORS = {
    'A': ('#f05846', '#ffffff'),
    'B': ('#fc7714', '#ffffff'),
    'C': ('#f7d358', '#202020'),
    'G': ('#4caf50', '#ffffff'),
}


class AlertListDialog(QtWidgets.QDialog):
    """List all alerts of one level and show the matching advice inline."""

    def __init__(self, parent, level: str, items: list[AlertItem],
                 checkdef: list[str] | None = None):
        super().__init__(parent)
        self.level = level
        self.items = items
        self.checkdef = list(checkdef or [])
        self._help_cache: dict[str, str] = {}
        self.prefilter = load_prefilter()
        self.checkcif_tests = load_checkcif_tests()
        self.setWindowTitle(f'{level} 级警报（{len(items)} 条）')
        self.resize(1040, 620)

        layout = QtWidgets.QVBoxLayout(self)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)

        left = QtWidgets.QWidget(splitter)
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QtWidgets.QLabel('警报（单击查看建议）', left))
        self.list_widget = QtWidgets.QListWidget(left)
        for alert in items:
            entry = QtWidgets.QListWidgetItem(
                f'{alert.code}  [{alert.level}]  {alert.summary}')
            entry.setData(QtCore.Qt.ItemDataRole.UserRole, alert)
            self.list_widget.addItem(entry)
        left_layout.addWidget(self.list_widget, 1)

        right = QtWidgets.QWidget(splitter)
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QtWidgets.QLabel('解决建议', right))
        self.advice_browser = QtWidgets.QTextBrowser(right)
        advice_font = self.advice_browser.font()
        advice_font.setPointSize(11)
        self.advice_browser.setFont(advice_font)
        self.advice_browser.setOpenExternalLinks(True)
        right_layout.addWidget(self.advice_browser, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.close_button = QtWidgets.QPushButton('关闭', self)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        self.close_button.clicked.connect(self.accept)
        self.list_widget.currentItemChanged.connect(self._update_advice)
        if items:
            first_plat = next((i for i, alert in enumerate(items)
                               if alert.code.upper().startswith('PLAT')), 0)
            self.list_widget.setCurrentRow(first_plat)

    def _update_advice(self, current, previous=None) -> None:
        if current is None:
            self.advice_browser.clear()
            return
        alert: AlertItem = current.data(QtCore.Qt.ItemDataRole.UserRole)
        if alert.code not in self._help_cache:
            if alert.code.upper().startswith('PLAT'):
                from finalcif.cif.checkcif.checkcif import AlertHelp
                self._help_cache[alert.code] = AlertHelp(self.checkdef).get_help(alert.code)
            else:
                entry = lookup_prefilter(self.prefilter, alert.code)
                if entry:
                    self._help_cache[alert.code] = format_prefilter_help(alert.code, entry)
                else:
                    test = lookup_checkcif_test(self.checkcif_tests, alert.code)
                    self._help_cache[alert.code] = (
                        format_checkcif_test_help(alert.code, test) if test else '')
        helptext = self._help_cache[alert.code]
        if not helptext:
            if alert.code.upper().startswith('PLAT'):
                helptext = f'未找到帮助文本：{alert.code}。\n\n{alert.summary}'
            else:
                key_match = re.search(r'(_[A-Za-z][A-Za-z0-9_]*)', alert.summary)
                helptext = (
                    f'{alert.code} 是 IUCr CheckCIF 检查项，但本版本尚未收录该条目的中文说明。\n\n'
                    f'报告内容：{alert.summary}\n\n'
                )
                if key_match:
                    helptext += (f'建议：补全或修正 CIF 中的 {key_match.group(1)}，'
                                 f'然后重新运行 CheckCIF。')
                else:
                    helptext += '建议：根据上面的报告内容修正对应 CIF 数据项，然后重新运行 CheckCIF。'
        self.advice_browser.setPlainText(helptext)
        self.advice_browser.verticalScrollBar().setValue(0)


class CheckCifSummaryBar(QtWidgets.QWidget):
    """Compact alert-count bar shown above a CheckCIF result page."""

    levelClicked = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._summary: CheckCifSummary | None = None
        self.checkdef: list[str] = []
        self.setObjectName('checkcifSummaryBar')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(QtWidgets.QLabel('警报汇总：'))
        self.level_buttons: dict[str, QtWidgets.QPushButton] = {}
        for level in LEVELS:
            button = QtWidgets.QPushButton(f'{level} 0', self)
            button.setObjectName(f'alertLevel{level}Button')
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            button.setMinimumWidth(64)
            button.clicked.connect(lambda _=False, value=level: self._open_level(value))
            top.addWidget(button)
            self.level_buttons[level] = button
        self.no_alerts_label = QtWidgets.QLabel('无警报', self)
        top.addWidget(self.no_alerts_label)
        top.addStretch(1)
        self.result_time_label = QtWidgets.QLabel('', self)
        top.addWidget(self.result_time_label)
        layout.addLayout(top)

        bottom = QtWidgets.QHBoxLayout()
        bottom.setSpacing(6)
        self.status_label = QtWidgets.QLabel('未运行', self)
        self.status_label.setObjectName('checkcifSummaryStatus')
        bottom.addWidget(self.status_label, 1)
        self.stale_label = QtWidgets.QLabel('CIF 已修改，结果可能过期', self)
        self.stale_label.setStyleSheet('color:#b00020; font-weight:bold;')
        self.stale_label.hide()
        bottom.addWidget(self.stale_label)
        layout.addLayout(bottom)

        self.clear()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_summary(self, summary: CheckCifSummary, timestamp: str = '',
                    checkdef: list[str] | None = None) -> None:
        self._summary = summary
        if checkdef is not None:
            self.checkdef = list(checkdef)
        total = 0
        for level in LEVELS:
            count = int(summary.counts.get(level, 0))
            total += count
            button = self.level_buttons[level]
            button.setText(f'{level} {count}')
            button.setEnabled(count > 0)
            background, foreground = _LEVEL_COLORS[level]
            button.setStyleSheet(
                f'QPushButton {{ background:{background}; color:{foreground}; '
                f'border:none; border-radius:3px; padding:2px 6px; }}'
                f'QPushButton:disabled {{ background:#d0d0d0; color:#707070; }}')
        self.no_alerts_label.setVisible(total == 0)
        if timestamp:
            self.result_time_label.setText(f'结果生成于 {timestamp}')
        else:
            self.result_time_label.clear()
        self.show()

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)
        self.show()

    def set_stale(self, stale: bool) -> None:
        self.stale_label.setVisible(bool(stale))

    def show_level(self, level: str, checkdef: list[str] | None = None) -> None:
        """Open the alert list for *level* (if the summary has items)."""
        if checkdef is not None:
            self.checkdef = list(checkdef)
        if self._summary is None:
            return
        items = [item for item in self._summary.items if item.level == level]
        if not items:
            return
        AlertListDialog(self, level, items, self.checkdef).exec()

    def clear(self) -> None:
        self._summary = None
        for level in LEVELS:
            button = self.level_buttons[level]
            button.setText(f'{level} 0')
            button.setEnabled(False)
            button.setStyleSheet(
                'QPushButton { background:#d0d0d0; color:#707070; border:none; '
                'border-radius:3px; padding:2px 6px; }')
        self.no_alerts_label.hide()
        self.result_time_label.clear()
        self.stale_label.hide()
        self.status_label.setText('未运行')
        self.hide()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _open_level(self, level: str) -> None:
        if self._summary is None:
            return
        items = [item for item in self._summary.items if item.level == level]
        self.levelClicked.emit(level)
        if items:
            self.show_level(level)
