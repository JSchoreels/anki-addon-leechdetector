import json
import unittest

from leechdetector.lapse_infos import LapseInfos


class TestLapseInfos(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.lapse_infos_input = [
            {"card_id": "1710712242101", "past_max_intervals": [2, 20, 25], "current_lapse_max_performance": 42},
            {"card_id": "1708207159229", "past_max_intervals": [1, 3], "current_lapse_max_performance": 91},
            {"card_id": "1723541612090", "past_max_intervals": [4, 8], "current_lapse_max_performance": 28},
            {"card_id": "1708259347988", "past_max_intervals": [1, 5, 6, 27, 30, 21],
             "current_lapse_max_performance": 12},
            {"card_id": "1708787872864", "past_max_intervals": [1, 28, 9, 3, 27, 15, 1, 14],
             "current_lapse_max_performance": 8},
            {"card_id": "1716748875647", "past_max_intervals": [2, 9, 7, 9, 10, 2, 3, 2, 18],
             "current_lapse_max_performance": 0},
            {"card_id": "1715717287839", "past_max_intervals": [5, 9, 4, 8, 8, 32, 9, 4],
             "current_lapse_max_performance": 8},
            {"card_id": "1711230892107", "past_max_intervals": [42, 38, 6, 2, 5], "current_lapse_max_performance": 1},
            {"card_id": "1708440946044", "past_max_intervals": [4, 15, 11, 14, 6, 5, 19, 15],
             "current_lapse_max_performance": 9},
            {"card_id": "1727897994100", "past_max_intervals": [1, 1, 1, 6, 12, 9, 7, 5],
             "current_lapse_max_performance": 5},
            {"card_id": "1727897994100", "past_max_intervals": [], "current_lapse_max_performance": 0}]
        self.lapse_infos = [LapseInfos(**item) for item in self.lapse_infos_input]

    def test_drop_count(self):
        self.assertListEqual(
            list1=[lapse_info.performance_drop_count() for lapse_info in self.lapse_infos],
            list2=[0, 0, 0, 1, 4, 3, 3, 3, 4, 3, 0]
        )

    def test_failed_improvement_count(self):
        self.assertListEqual(
            list1=[lapse_info.failed_improvement_count() for lapse_info in self.lapse_infos],
            list2=[0, 0, 0, 1, 4, 3, 3, 3, 4, 3, 0]
        )

    def test_failed_improvement_ratio(self):
        self.assertListEqual(
            list1=[int(100 * lapse_info.failed_improvement_ratio()) for lapse_info in self.lapse_infos],
            list2=[0, 0, 0, 20, 57, 37, 42, 75, 57, 42, 0]
        )

    def test_to_dict(self):
        self.assertListEqual(
            list1=[lapse_info.to_dict() for lapse_info in self.lapse_infos],
            list2=self.lapse_infos_input
        )


    def test_is_leech_threshold_boundaries(self):
        equal_drop_count = LapseInfos(card_id=1, past_max_intervals=[10, 5], current_lapse_max_performance=0)
        equal_drop_count.configure_leech_detection(drop_count=1, drop_ratio=0)
        self.assertFalse(equal_drop_count.is_leech())

        equal_drop_ratio = LapseInfos(card_id=2, past_max_intervals=[10, 5, 6], current_lapse_max_performance=0)
        equal_drop_ratio.configure_leech_detection(drop_count=0, drop_ratio=0.5)
        self.assertFalse(equal_drop_ratio.is_leech())

        above_both = LapseInfos(card_id=3, past_max_intervals=[10, 5, 4], current_lapse_max_performance=0)
        above_both.configure_leech_detection(drop_count=1, drop_ratio=0.5)
        self.assertTrue(above_both.is_leech())

    def test_leech_status_boundaries(self):
        active = LapseInfos(card_id=10, past_max_intervals=[10, 5, 4], current_lapse_max_performance=10)
        recovering_boundary = LapseInfos(card_id=11, past_max_intervals=[10, 5, 4], current_lapse_max_performance=20)
        recovered = LapseInfos(card_id=12, past_max_intervals=[10, 5, 4], current_lapse_max_performance=21)
        healthy = LapseInfos(card_id=13, past_max_intervals=[10, 12], current_lapse_max_performance=30)

        self.assertTrue(active.is_active_leech())
        self.assertEqual(active.leech_status(), "Leech")

        self.assertTrue(recovering_boundary.is_recovering_leech())
        self.assertFalse(recovering_boundary.is_recovered_leech())
        self.assertEqual(recovering_boundary.leech_status(), "Recovering")

        self.assertTrue(recovered.is_recovered_leech())
        self.assertEqual(recovered.leech_status(), "Recovered")

        self.assertEqual(healthy.leech_status(), "Healthy")

    def test_to_dict_enriched(self):
        for lapse_info in self.lapse_infos:
            self.assertListEqual(
                list1=list(lapse_info.to_dict_enriched().keys()),
                list2=['card_id', 'past_max_intervals', 'current_lapse_max_performance', 'biggest_interval_drop', 'failed_improvement_ratio', 'leech_status', 'performance_drop_count', 'performance_drop_ratio']
            )
