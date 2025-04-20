import json
import unittest

from leechdetector.lapse_infos import LapseInfos


class TestLapseInfos(unittest.TestCase):

    def setUp(self):
        super().setUp()
        data = [{"card_id": "1710712242101", "past_max_intervals": [2, 20, 25], "current_lapse_max_intervals": 42},
                {"card_id": "1708207159229", "past_max_intervals": [1, 3], "current_lapse_max_intervals": 91},
                {"card_id": "1723541612090", "past_max_intervals": [4, 8], "current_lapse_max_intervals": 28},
                {"card_id": "1708259347988", "past_max_intervals": [1, 5, 6, 27, 30, 21],
                 "current_lapse_max_intervals": 12},
                {"card_id": "1708787872864", "past_max_intervals": [1, 28, 9, 3, 27, 15, 1, 14],
                 "current_lapse_max_intervals": 8},
                {"card_id": "1716748875647", "past_max_intervals": [2, 9, 7, 9, 10, 2, 3, 2, 18],
                 "current_lapse_max_intervals": 0},
                {"card_id": "1715717287839", "past_max_intervals": [5, 9, 4, 8, 8, 32, 9, 4],
                 "current_lapse_max_intervals": 8},
                {"card_id": "1711230892107", "past_max_intervals": [42, 38, 6, 2, 5], "current_lapse_max_intervals": 1},
                {"card_id": "1708440946044", "past_max_intervals": [4, 15, 11, 14, 6, 5, 19, 15],
                 "current_lapse_max_intervals": 9},
                {"card_id": "1727897994100", "past_max_intervals": [1, 1, 1, 6, 12, 9, 7, 5],
                 "current_lapse_max_intervals": 5}]
        self.lapse_infos = [LapseInfos(**item) for item in data]

    def test_drop_count(self):
        self.assertListEqual(
            list1=[lapse_info.drop_count() for lapse_info in self.lapse_infos],
            list2=[0, 0, 0, 1, 4, 3, 3, 3, 4, 3]
        )

    def test_drop_count(self):
        self.assertListEqual(
            list1=[lapse_info.failed_outperformance_count() for lapse_info in self.lapse_infos],
            list2=[1, 0, 0, 3, 4, 4, 4, 3, 4, 5]
        )

    def test_drop_count(self):
        self.assertListEqual(
            list1=[int(100 * lapse_info.failed_outperformance_ratio()) for lapse_info in self.lapse_infos],
            list2=[50, 0, 0, 60, 57, 50, 57, 75, 57, 71]
        )