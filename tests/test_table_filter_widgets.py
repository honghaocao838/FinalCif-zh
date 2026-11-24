from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_bootstrap  # noqa: F401,E402

from qtpy.QtWidgets import QApplication  # noqa: E402

from finalcif.gui.cif_table_model import CifRowData  # noqa: E402
from finalcif.gui.cif_table_view import CifTableView  # noqa: E402
from finalcif.gui.table_filter_bar import (TableFilterBar, FILTER_ALL, FILTER_MISSING,  # noqa: E402
                                           FILTER_REQUIRED_MISSING, FILTER_CHECKCIF)

app = QApplication.instance() or QApplication([])


class TableFilterBarTests(unittest.TestCase):
    def test_options_and_counts(self):
        bar = TableFilterBar()
        self.assertEqual(bar.status, FILTER_ALL)
        bar.set_counts(12, 100)
        self.assertEqual(bar.count_label.text(), '显示 12 / 100 行')
        bar.set_required_options_visible(True)
        bar.set_required_missing(6)
        self.assertEqual(bar.required_button.text(), '必填未填 6 项')
        self.assertTrue(bar.required_button.isEnabled())
        bar.set_required_missing(0)
        self.assertEqual(bar.required_button.text(), '必填项已齐')
        self.assertFalse(bar.required_button.isEnabled())

    def test_checkcif_option_disabled(self):
        bar = TableFilterBar()
        bar.set_checkcif_option_available(False)
        index = [i for i in range(bar.status_combo.count())
                 if bar.status_combo.itemData(i) == FILTER_CHECKCIF][0]
        self.assertFalse(bar.status_combo.model().item(index).isEnabled())
        bar.set_checkcif_option_available(True)
        self.assertTrue(bar.status_combo.model().item(index).isEnabled())


class CifTableViewTests(unittest.TestCase):
    def setUp(self):
        self.view = CifTableView()
        self.view.bulk_load([
            CifRowData(key='_cell_length_a', cif_value='10.1', data_value='10.2'),
            CifRowData(key='_space_group_name_H-M_alt', cif_value='P 1'),
            CifRowData(key='These below are already in:', is_separator=True),
            CifRowData(key='_cell_volume', cif_value='?', edit_value='123.4'),
        ])

    def tearDown(self):
        self.view.deleteLater()

    def test_effective_value_precedence(self):
        self.assertEqual(self.view.effective_value(0), '10.2')
        self.assertEqual(self.view.effective_value(1), 'P 1')
        self.assertEqual(self.view.effective_value(3), '123.4')

    def test_row_data_separator(self):
        self.assertTrue(self.view.row_data(2).is_separator)
        self.assertFalse(self.view.row_data(0).is_separator)

    def test_column_widths_roundtrip(self):
        self.assertTrue(self.view.set_column_widths([200, 300, 400]))
        self.assertEqual(self.view.column_widths(), [200, 300, 400])
        self.assertFalse(self.view.set_column_widths([1, 2]))

    def test_filter_speed_2000_rows(self):
        rows = [CifRowData(key=f'_key_{i}', cif_value=str(i), data_value='') for i in range(2000)]
        self.view.bulk_load(rows)
        start = time.perf_counter()
        for row in range(self.view.rows_count):
            self.view.setRowHidden(row, row % 2 == 0)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertLess(elapsed_ms, 100, f'setRowHidden took {elapsed_ms:.1f} ms')


if __name__ == '__main__':
    unittest.main()
