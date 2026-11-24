from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_bootstrap  # noqa: F401,E402

os.environ.setdefault('PYTEST_CURRENT_TEST', 'test_app_filter')
_TEMP = tempfile.mkdtemp(prefix='finalcif-test-')
os.environ['APPDATA'] = _TEMP
os.environ['XDG_CONFIG_HOME'] = _TEMP

from qtpy.QtWidgets import QApplication  # noqa: E402

from finalcif.appwindow import AppWindow  # noqa: E402
from finalcif.gui.custom_classes import Column  # noqa: E402
from finalcif.gui.table_filter_bar import (FILTER_ALL, FILTER_MISSING,  # noqa: E402
                                           FILTER_REQUIRED_MISSING, FILTER_INVALID)

app = QApplication.instance() or QApplication([])
ROOT = Path(__file__).resolve().parent.parent


class AppWindowFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = AppWindow(file=ROOT / 'tests' / 'examples' / '1979688.cif')
        app.processEvents()

    @classmethod
    def tearDownClass(cls):
        cls.window.close()
        cls.window.deleteLater()
        app.processEvents()

    def _visible_rows(self):
        table = self.window.ui.cif_main_table
        return [row for row in range(table.rows_count) if not table.isRowHidden(row)]

    def _set_status(self, value):
        combo = self.window.filter_bar.status_combo
        index = [i for i in range(combo.count()) if combo.itemData(i) == value][0]
        combo.setCurrentIndex(index)
        self.window.apply_table_filter()
        app.processEvents()

    def test_missing_filter(self):
        self._set_status(FILTER_MISSING)
        table = self.window.ui.cif_main_table
        for row in self._visible_rows():
            row_data = table.row_data(row)
            if row_data is None or row_data.is_separator:
                continue
            values = [table.text(row, column) for column in range(3)]
            self.assertTrue(all(value.strip() in {'', '?', '.'} for value in values), row)
        self._set_status(FILTER_ALL)
        self.assertEqual(len(self._visible_rows()), table.rows_count)

    def test_alias_search(self):
        table = self.window.ui.cif_main_table
        key = next((k for k in table.vheaderitems if self.window.key_aliases.get(k)), None)
        self.assertIsNotNone(key)
        alias = self.window.key_aliases[key][0]
        self.window.filter_bar.set_search_text(alias)
        self.window.apply_table_filter()
        visible = self._visible_rows()
        self.assertIn(table.row_from_key(key), visible)
        self.window.filter_bar.set_search_text('不存在的搜索词xyz')
        self.window.apply_table_filter()
        self.assertEqual(self._visible_rows(), [])
        self.window.filter_bar.set_search_text('')
        self.window.apply_table_filter()

    def test_validation_summary(self):
        table = self.window.ui.cif_main_table
        key = '_cell_formula_units_Z'
        if not table.has_key(key):
            self.skipTest('test CIF has no Z value')
        widget = table.widget_from_key(key, Column.EDIT)
        self.assertIsNotNone(widget)
        widget.setPlainText('abc')
        widget.validate_text('abc')
        self.window.update_validation_summary()
        self.assertEqual(self.window._first_invalid_row, table.row_from_key(key))
        self.assertIn('项格式不合法', self.window.validation_summary_button.text())
        widget.setPlainText('4')
        widget.validate_text('4')
        self.window.update_validation_summary()
        self.assertEqual(self.window.validation_summary_button.text(), '格式校验通过')

    def test_required_filter(self):
        table = self.window.ui.cif_main_table
        if not self.window.required_entries:
            self.skipTest('no required list')
        self.window.filter_bar.set_required_options_visible(True)
        self._set_status(FILTER_REQUIRED_MISSING)
        for row in self._visible_rows():
            key = table.vheader_text(row)
            self.assertIn(key, self.window.required_entries)
        self._set_status(FILTER_ALL)

    def test_filter_performance(self):
        start = time.perf_counter()
        self.window.apply_table_filter()
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertLess(elapsed_ms, 250, f'apply_table_filter took {elapsed_ms:.1f} ms')

    def test_layout_state(self):
        self.window._save_layout_state()
        self.window.reset_layout()
        app.processEvents()
        self.assertIn('layout_left_equipment_collapsed', self.window._collapsible_sections)
        self.assertIn('layout_left_report_collapsed', self.window._collapsible_sections)


if __name__ == '__main__':
    unittest.main()
