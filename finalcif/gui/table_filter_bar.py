"""Filter bar for the main CIF table.

The bar only emits changes; the actual row filtering lives in
``AppWindow.apply_table_filter`` so that status, search and the row count
always stay consistent with each other.
"""
from __future__ import annotations

from qtpy import QtCore, QtWidgets


FILTER_ALL = 'all'
FILTER_MISSING = 'missing'
FILTER_DATA = 'data'
FILTER_INVALID = 'invalid'
FILTER_TEMPLATE = 'template'
FILTER_REQUIRED_MISSING = 'required_missing'
FILTER_REQUIRED_ALL = 'required_all'
FILTER_CHECKCIF = 'checkcif'

_STATUS_ITEMS = [
    ('全部', FILTER_ALL),
    ('未填（?）', FILTER_MISSING),
    ('数据源已填', FILTER_DATA),
    ('校验错误', FILTER_INVALID),
    ('有响应模板', FILTER_TEMPLATE),
    ('必填未填', FILTER_REQUIRED_MISSING),
    ('必填（全部）', FILTER_REQUIRED_ALL),
    ('CheckCIF 提到', FILTER_CHECKCIF),
]


class TableFilterBar(QtWidgets.QWidget):
    """One-line filter row above the main CIF table."""

    filterChanged = QtCore.Signal()
    searchChanged = QtCore.Signal(str)
    requiredCountClicked = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setObjectName('tableFilterBar')
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(QtWidgets.QLabel('筛选：'))
        self.status_combo = QtWidgets.QComboBox(self)
        self.status_combo.setObjectName('tableFilterStatusCombo')
        self.status_combo.setMinimumWidth(130)
        for text, value in _STATUS_ITEMS:
            self.status_combo.addItem(text, value)
        layout.addWidget(self.status_combo)

        layout.addWidget(QtWidgets.QLabel('搜索：'))
        self.search_edit = QtWidgets.QLineEdit(self)
        self.search_edit.setObjectName('tableFilterSearchEdit')
        self.search_edit.setPlaceholderText('键名、中文别名或当前值')
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(220)
        layout.addWidget(self.search_edit, 1)

        self.count_label = QtWidgets.QLabel(self)
        self.count_label.setObjectName('tableFilterCountLabel')
        layout.addWidget(self.count_label)

        self.required_button = QtWidgets.QPushButton(self)
        self.required_button.setObjectName('tableFilterRequiredButton')
        self.required_button.setFlat(True)
        self.required_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.required_button.hide()
        layout.addWidget(self.required_button)

        self.status_combo.currentIndexChanged.connect(self._emit_filter_changed)
        self.search_edit.textChanged.connect(self.searchChanged)
        self.required_button.clicked.connect(self.requiredCountClicked)
        self._required_available = False
        self.set_required_options_visible(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def status(self) -> str:
        return str(self.status_combo.currentData() or FILTER_ALL)

    @property
    def search_text(self) -> str:
        return self.search_edit.text()

    def set_search_text(self, text: str) -> None:
        """Set the search text without emitting another searchChanged."""
        blocked = self.search_edit.blockSignals(True)
        self.search_edit.setText(text)
        self.search_edit.blockSignals(blocked)

    def set_counts(self, shown: int, total: int) -> None:
        self.count_label.setText(f'显示 {shown} / {total} 行')

    def set_required_options_visible(self, visible: bool) -> None:
        """Show or hide the three required-item filter entries."""
        self._required_available = visible
        for value in (FILTER_REQUIRED_MISSING, FILTER_REQUIRED_ALL):
            self._set_option_visible(value, visible)
        if visible:
            self.required_button.show()
            if not self.required_button.text():
                self.required_button.setText('必填项已齐')
                self.required_button.setEnabled(False)
        else:
            self.required_button.hide()
        self._set_option_visible(FILTER_CHECKCIF, True)

    def set_checkcif_option_available(self, available: bool, reason: str = '') -> None:
        index = self._index_of(FILTER_CHECKCIF)
        if index < 0:
            return
        item = self.status_combo.model().item(index)
        if item is not None:
            item.setEnabled(available)
            item.setToolTip('' if available else (reason or '请先运行一次 CheckCIF'))
        if not available and self.status == FILTER_CHECKCIF:
            self.status_combo.setCurrentIndex(0)

    def set_required_missing(self, count: int) -> None:
        if not self._required_available:
            return
        self.required_button.show()
        if count > 0:
            self.required_button.setText(f'必填未填 {count} 项')
            self.required_button.setEnabled(True)
        else:
            self.required_button.setText('必填项已齐')
            self.required_button.setEnabled(False)

    def jump_to_required_option(self) -> None:
        """Switch the combo to '必填未填'."""
        index = self._index_of(FILTER_REQUIRED_MISSING)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

    def reset(self) -> None:
        blocked = self.search_edit.blockSignals(True)
        self.search_edit.clear()
        self.search_edit.blockSignals(blocked)
        self.status_combo.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit_filter_changed(self) -> None:
        self.filterChanged.emit()

    def _index_of(self, value: str) -> int:
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == value:
                return i
        return -1

    def _set_option_visible(self, value: str, visible: bool) -> None:
        index = self._index_of(value)
        if index < 0:
            return
        self.status_combo.view().setRowHidden(index, not visible)
        if not visible and self.status == value:
            self.status_combo.setCurrentIndex(0)
