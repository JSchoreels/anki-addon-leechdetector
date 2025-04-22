import json
import os
import unittest

from anki.collection import Collection

from leechdetector import LeechDetector
from leechdetector.AnkiValueParser import time_to_date, interval_to_duration_display, is_failed

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class LeechDetectorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.collection = Collection(os.path.join(THIS_DIR, "data/collection.anki2"))
        cls.leechdetector = LeechDetector(cls.collection)

        cls.card_ids_reviewed = [1710712242101, 1708207159229, 1723541612090, 1708259347988, 1708787872864, 1716748875647, 1715717287839, 1711230892107, 1708440946044,
                                 1727897994100] # relearn

        cls.card_ids_new = [1549775726971]

        cls.cards_ids_all = cls.card_ids_reviewed + cls.card_ids_new


    def test_get_max_successful_interval(self):
        self.assertListEqual(
            list1 = [interval_to_duration_display(self.leechdetector.get_max_successful_interval(card_id)) for card_id in self.cards_ids_all],
            list2 = ['1.77 months', '3.50 months', '28 days', '30 days', '28 days', '21 days', '1.43 months', '1.43 months', '20 days', '13 days', '0 days']
        )

    def test_past_max_intervals(self):
        self.assertListEqual(
            list1 = [self.leechdetector.get_lapse_infos(card_id).past_max_intervals for card_id in self.cards_ids_all],
            list2 = [[2, 20, 25],
                     [1, 3],
                     [4, 8],
                     [1, 5, 6, 27, 30, 21],
                     [1, 28, 9, 3, 27, 15, 1, 14],
                     [2, 9, 7, 9, 10, 2, 3, 2, 18],
                     [5, 9, 4, 8, 8, 32, 9, 4],
                     [42, 38, 6, 2, 5],
                     [4, 15, 11, 14, 6, 5, 19, 15],
                     [1, 1, 1, 6, 12, 9, 7, 5],
                     []]
        )

    def test_display_stats(self):
        lapse_infos = []
        for card_id in self.collection.find_cards('"deck:Japan::1. Vocabulary" -is:new prop:lapses>0'):
            lapse_infos.append(self.leechdetector.get_lapse_infos(card_id))
        total_card_count = len(self.collection.find_cards('"deck:Japan::1. Vocabulary" -is:new'))
        lapsed_card_count = len(lapse_infos)
        distribution_lapse_count = group_lapse_info_by_key(lapse_infos, lambda lapseInfo: lapseInfo.lapses_count)
        distribution_drops = group_lapse_info_by_key(lapse_infos, lambda lapseInfo: lapseInfo.drop_count())
        print(f"Total Cards reviewed : {total_card_count}")
        print(f"Cards That lapsed at least once: {lapsed_card_count} ({lapsed_card_count / total_card_count * 100:.2f}%)")
        print(f"Cards That had 0 dropping lapse: {distribution_drops[0]} ({distribution_drops[0] / total_card_count * 100:.2f}%)")
        print(f"Cards That had 1 dropping lapse: {distribution_drops[1]} ({distribution_drops[1] / total_card_count * 100:.2f}%)")
        card_count_other = sum([dropCount for (drop, dropCount) in distribution_drops.items() if drop > 1])
        print(f"Cards That had >1 dropping lapse : {card_count_other} ({card_count_other / total_card_count * 100:.2f}%)")

        ## Failed Outperforamce Counts
        failed_outperformance_counts = group_lapse_info_by_key(lapse_infos, lambda lapseInfo: lapseInfo.failed_outperformance_count())
        print(f"Cards That had 0 failed outperformance lapse: {failed_outperformance_counts[0]} ({failed_outperformance_counts[0] / lapsed_card_count * 100:.2f}%)")
        print(f"Cards That had 1 failed outperformance lapse: {failed_outperformance_counts[1]} ({failed_outperformance_counts[1] / lapsed_card_count * 100:.2f}%)")
        card_count_other = sum([failed_outperformance_count_total for (failed_outperformance_count, failed_outperformance_count_total) in failed_outperformance_counts.items() if failed_outperformance_count > 1])
        print(f"Cards That had >1 failed outperformance lapse : {card_count_other} ({card_count_other / lapsed_card_count * 100:.2f}%)")

        ## Failed Outperformance Counts Ratio
        failed_outperformance_ratio = group_lapse_info_by_key(lapse_infos, lambda lapseInfo: int(lapseInfo.failed_outperformance_ratio() * 100 / 33.34))
        print(f"Cards That had [2/3, 1.0] failed outperformance ratio lapse: {failed_outperformance_ratio[2]} ({failed_outperformance_ratio[0] / lapsed_card_count * 100:.2f}%)")
        print(f"Cards That had [1/3, 2.3] failed outperformance ratio lapse: {failed_outperformance_ratio[1]} ({failed_outperformance_ratio[1] / lapsed_card_count * 100:.2f}%)")
        card_count_other = sum([failed_outperformance_ratio_total for (failed_outperformance_ratio, failed_outperformance_ratio_total) in failed_outperformance_ratio.items() if failed_outperformance_ratio > 1])
        print(f"Cards That had [0.0, 1/3] failed outperformance ratio lapse : {card_count_other} ({card_count_other / lapsed_card_count * 100:.2f}%)")


        print(distribution_drops)
        print(distribution_lapse_count)
        lapse_infos.sort(key=lambda lapseInfo: lapseInfo.failed_outperformance_ratio(), reverse=True)
        [ print(lapse_info) for lapse_info in lapse_infos ]

def group_lapse_info_by_key(lapseInfos, key_function):
    distributionDrops = {}
    for lapseInfo in lapseInfos:
        key = key_function(lapseInfo)
        if key in distributionDrops:
            distributionDrops[key] += 1
        else:
            distributionDrops[key] = 1
    return distributionDrops

