import os
import re
import unittest

from leechdetector.lapse_infos import LapseInfos

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)


class TestCardInfoContract(unittest.TestCase):
    def test_payload_uses_current_lapse_max_performance_key(self):
        payload = LapseInfos(
            card_id="1",
            past_max_intervals=[10, 4],
            current_lapse_max_performance=7,
        ).to_dict_enriched()
        self.assertIn("current_lapse_max_performance", payload)

    def test_js_reads_current_lapse_max_performance_key(self):
        js_path = os.path.join(ROOT_DIR, "leechdetector", "card_info_updated.js")
        with open(js_path, "r") as js_file:
            js_content = js_file.read()
        self.assertRegex(js_content, r"\blapseInfos\.current_lapse_max_performance\b")

    def test_html_and_js_use_same_dom_id_for_current_cycle_cell(self):
        html_path = os.path.join(ROOT_DIR, "leechdetector", "leechdetector_table.html")
        js_path = os.path.join(ROOT_DIR, "leechdetector", "card_info_updated.js")

        with open(html_path, "r") as html_file:
            html_content = html_file.read()
        with open(js_path, "r") as js_file:
            js_content = js_file.read()

        html_id_match = re.search(r'id="(current_lapse_max_[^"]+)"', html_content)
        js_selector_match = re.search(
            r"currentLapseMaxIntervalsCell:\s*document\.querySelector\('#([^']+)'\)",
            js_content,
        )

        self.assertIsNotNone(html_id_match)
        self.assertIsNotNone(js_selector_match)
        self.assertEqual(html_id_match.group(1), js_selector_match.group(1))
        self.assertEqual(html_id_match.group(1), "current_lapse_max_performance")


if __name__ == "__main__":
    unittest.main()
