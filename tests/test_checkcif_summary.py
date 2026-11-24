from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_bootstrap  # noqa: F401,E402

from qtpy.QtWidgets import QApplication  # noqa: E402

from finalcif.cif.checkcif.summary import parse_chk, parse_html  # noqa: E402
from finalcif.gui.checkcif_summary import CheckCifSummaryBar  # noqa: E402

app = QApplication.instance() or QApplication([])
ROOT = Path(__file__).resolve().parent.parent


class SummaryParserTests(unittest.TestCase):
    def test_online_fixture(self):
        html = (ROOT / 'tests' / 'checkcif_results' / 'check_html_ab.html').read_text(
            encoding='utf-8', errors='ignore')
        summary = parse_html(html)
        self.assertEqual(summary.counts, {'A': 0, 'B': 0, 'C': 2, 'G': 18})
        self.assertEqual(summary.total, 20)
        self.assertTrue(any(item.code == 'PLAT413' and item.level == 'C'
                            for item in summary.items))
        self.assertTrue(summary.mentioned_keys)

    def test_offline_chk(self):
        text = """
PLAT041_ALERT_1_C Explanatory text for an A-level problem
PLAT300_ALERT_4_G Atom Site Occupancy of O13 Constrained at 0.5
  1 ALERT level A
  0 ALERT level B
  0 ALERT level C
  1 ALERT level G
"""
        summary = parse_chk(text)
        self.assertEqual(summary.counts['A'], 1)
        self.assertEqual(summary.items[0].code, 'PLAT041')
        self.assertEqual(summary.items[0].level, 'C')

    def test_empty_input(self):
        self.assertEqual(parse_html('').total, 0)
        self.assertEqual(parse_chk('').total, 0)


class SummaryBarTests(unittest.TestCase):
    def test_buttons_reflect_counts(self):
        html = (ROOT / 'tests' / 'checkcif_results' / 'check_html_ab.html').read_text(
            encoding='utf-8', errors='ignore')
        summary = parse_html(html)
        bar = CheckCifSummaryBar()
        bar.set_summary(summary, timestamp='12:00:00')
        self.assertFalse(bar.level_buttons['A'].isEnabled())
        self.assertTrue(bar.level_buttons['C'].isEnabled())
        self.assertEqual(bar.level_buttons['G'].text(), 'G 18')
        self.assertIn('12:00:00', bar.result_time_label.text())
        bar.set_stale(True)
        self.assertFalse(bar.stale_label.isHidden())
        bar.clear()
        self.assertFalse(bar.level_buttons['C'].isEnabled())
        bar.deleteLater()


if __name__ == '__main__':
    unittest.main()
