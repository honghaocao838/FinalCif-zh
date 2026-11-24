"""Summary bar for CheckCIF results and the per-level alert list."""
from __future__ import annotations

from qtpy import QtCore, QtWidgets

from finalcif.cif.checkcif.summary import AlertItem, CheckCifSummary, LEVELS

_LEVEL_COLORS = {
    'A': ('#f05846', '#ffffff'),
    'B': ('#fc7714', '#ffffff'),
    'C': ('#f7d358', '#202020'),
    'G': ('#4caf50', '#ffffff'),
}


class AlertListDialog(QtWidgets.QDialog):
    """List all alerts of one level; double-click opens the Chinese help."""

    def __init__(self, parent, level: str, items: list[AlertItem],
                 checkdef: list[str] | None = None):
        super().__init__(parent)
        self.level = level
        self.items = items
        self.checkdef = list(checkdef or [])
        self.setWindowTitle(f'{level} 级警报（{len(items)} 条）')
        self.resize(760, 460)
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget(self)
        for alert in items:
            entry = QtWidgets.QListWidgetItem(
                f'{alert.code}  [{alert.level}]  {alert.summary}')
            entry.setData(QtCore.Qt.ItemDataRole.UserRole, alert)
            self.list_widget.addItem(entry)
        layout.addWidget(self.list_widget, 1)
        buttons = QtWidgets.QHBoxLayout()
        self.help_button = QtWidgets.QPushButton('查看解释', self)
        self.close_button = QtWidgets.QPushButton('关闭', self)
        buttons.addStretch(1)
        buttons.addWidget(self.help_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)
        self.help_button.clicked.connect(self._show_help)
        self.list_widget.itemDoubleClicked.connect(lambda _: self._show_help())
        self.close_button.clicked.connect(self.accept)

    def _show_help(self) -> None:
        entry = self.list_widget.currentItem()
        if entry is None and self.list_widget.count():
            entry = self.list_widget.item(0)
        if entry is None:
            return
        alert: AlertItem = entry.data(QtCore.Qt.ItemDataRole.UserRole)
        from finalcif.cif.checkcif.checkcif import AlertHelp
        helptext = AlertHelp(self.checkdef).get_help(alert.code)
        if not helptext:
            helptext = f'未找到帮助文本：{alert.code}。'
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f'checkCIF 帮助：{alert.code}')
        dialog.resize(680, 440)
        layout = QtWidgets.QVBoxLayout(dialog)
        browser = QtWidgets.QTextBrowser(dialog)
        browser.setPlainText(helptext)
        layout.addWidget(browser, 1)
        close_button = QtWidgets.QPushButton('关闭', dialog)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        dialog.exec()


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
