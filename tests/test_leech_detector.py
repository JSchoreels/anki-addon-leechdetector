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

        cls.card_ids_testset_reviewed = [1710712242101, 1708207159229, 1723541612090, 1708259347988, 1708787872864, 1716748875647, 1715717287839, 1711230892107, 1708440946044,
                                         1727897994100] # relearn

        cls.card_ids_testset_new = [1549775726971]

        cls.cards_ids_testset_all = cls.card_ids_testset_reviewed + cls.card_ids_testset_new

        cls.cards_ids_collection_all = cls.collection.find_cards('-is:new')
        cls.lapse_infos_collection = [ cls.leechdetector.get_lapse_infos(card_id, improvement_factor=1.00) for card_id in  cls.cards_ids_collection_all ]
        cls.total_card_count = len(cls.cards_ids_collection_all)
        cls.lapsed_card_collection = [lapse_info for lapse_info in cls.lapse_infos_collection if lapse_info.lapses_count > 0]
        cls.lapsed_card_count = len(cls.lapsed_card_collection)


    def test_get_max_successful_interval(self):
        self.assertListEqual(
            list1 = [interval_to_duration_display(self.leechdetector.get_max_successful_interval(card_id)) for card_id in self.cards_ids_testset_all],
            list2 = ['1.77 months', '3.50 months', '28 days', '30 days', '28 days', '21 days', '1.43 months', '1.43 months', '20 days', '13 days', '0 days']
        )

    def test_past_max_intervals(self):
        self.assertListEqual(
            list1 = [self.leechdetector.get_lapse_infos(card_id).past_max_intervals for card_id in self.cards_ids_testset_all],
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

    def test_is_leech(self):
        lapse_infos = []
        for card_id in self.collection.find_cards('-is:new prop:lapses>0'):
            lapse_infos.append(self.leechdetector.get_lapse_infos(card_id, improvement_factor=0.75))
        total_card_count = len(self.collection.find_cards('-is:new'))


    def test_display_stats(self):
        print(f"Total Cards reviewed : {self.total_card_count}")
        print(f"Cards That lapsed at least once: {self.lapsed_card_count} ({self.lapsed_card_count / self.total_card_count * 100:.2f}%)")


        # distribution_lapse_count = group_lapse_info_by_key(self.lapsed_card_collection, lambda lapseInfo: lapseInfo.lapses_count)
        # distribution_drops = group_lapse_info_by_key(self.lapsed_card_collection, lambda lapseInfo: lapseInfo.drop_count())
        # print(f"Cards That had 0 dropping lapse: {distribution_drops[0]} ({distribution_drops[0] / self.total_card_count * 100:.2f}%)")
        # print(f"Cards That had 1 dropping lapse: {distribution_drops[1]} ({distribution_drops[1] / self.total_card_count * 100:.2f}%)")
        # card_count_other = sum([dropCount for (drop, dropCount) in distribution_drops.items() if drop > 1])
        # print(f"Cards That had >1 dropping lapse : {card_count_other} ({card_count_other / self.total_card_count * 100:.2f}%)")


        def improvement_count_analysis(minimum_failed_improvement_ratio):
            ## Failed Outperforamce Counts
            failed_improvement_counts = group_lapse_info_by_key(self.lapsed_card_collection, lambda lapseInfo: lapseInfo.failed_improvement_count(), filter=lambda lapse_info: lapse_info.failed_improvement_ratio() >= minimum_failed_improvement_ratio)
            if 0 in failed_improvement_counts:
                print(f"Cards That had 0 failed improvement lapse (rati o ≥{minimum_failed_improvement_ratio}): {failed_improvement_counts[0]} ({failed_improvement_counts[0] / self.lapsed_card_count * 100:.2f}% of Lapsed, {failed_improvement_counts[0] / self.total_card_count * 100:.2f}% of All)")
            if 1 in failed_improvement_counts:
                print(f"Cards That had 1 failed improvement lapse (ratio ≥ {minimum_failed_improvement_ratio}): {failed_improvement_counts[1]} ({failed_improvement_counts[1] / self.lapsed_card_count * 100:.2f}% of Lapsed, {failed_improvement_counts[1] / self.total_card_count * 100:.2f}% of All)")
            card_count_other = sum([failed_improvement_count_total for (failed_improvement_count, failed_improvement_count_total) in failed_improvement_counts.items() if failed_improvement_count > 1])
            print(f"Cards That had >1 failed improvement lapse (ratio ≥ {minimum_failed_improvement_ratio}): {card_count_other} ({card_count_other / self.lapsed_card_count * 100:.2f}% of Lapsed, {card_count_other / self.total_card_count * 100:.2f}% of All)")
            print(f"failed_improvement_count : {dict(sorted(failed_improvement_counts.items()))}")

        print("----------------------------------")
        print("Failed improvement Cost Analysis")
        improvement_count_analysis(0)
        improvement_count_analysis(0.33)
        improvement_count_analysis(0.5)
        print("----------------------------------")

        ## Failed improvement Counts Ratio
        failed_improvement_ratio = group_lapse_info_by_key(self.lapsed_card_collection, lambda lapseInfo: int(lapseInfo.failed_improvement_ratio() * 100 / 33.33))
        print(f"Cards That had [2/3, 1.0] failed improvement ratio lapse: {failed_improvement_ratio[2]} ({failed_improvement_ratio[2] / self.lapsed_card_count * 100:.2f}% of Lapsed, {failed_improvement_ratio[2] / self.total_card_count * 100:.2f}% of All)")
        print(f"Cards That had [1/3, 2.3] failed improvement ratio lapse: {failed_improvement_ratio[1]} ({failed_improvement_ratio[1] / self.lapsed_card_count * 100:.2f}% of Lapsed, {failed_improvement_ratio[1] / self.total_card_count * 100:.2f}% of All)")
        print(f"Cards That had [0.0, 1/3] failed improvement ratio lapse : {failed_improvement_ratio[0]} ({failed_improvement_ratio[0] / self.lapsed_card_count * 100:.2f}% of Lapsed, {failed_improvement_ratio[0] / self.total_card_count * 100:.2f}% of All)")

        ## Failed Days/Reviews Counts Ratio
        days_by_reviews = group_lapse_info_by_key(self.lapse_infos_collection, lambda lapseInfo: int(lapseInfo.days_by_reviews() / 5), filter=lambda lapse_info: lapse_info.review_count > 20)
        for i in range(max(days_by_reviews.keys())):
            if i in days_by_reviews.keys():
                print(f"Cards That have [{i*3:2d}, {i*3+2:2d}] days by reviews :: {days_by_reviews[i]} ({days_by_reviews[i] / self.lapsed_card_count * 100:.2f}%)")
            else:
                print(f"Cards That have [{i*3:2d}, {i*3+2:2d}] days by reviews :: 0")

        self.lapsed_card_collection.sort(key=lambda lapseInfo: lapseInfo.failed_improvement_count(), reverse=True)

        leeches = [lapse_info for lapse_info in self.lapsed_card_collection if lapse_info.is_leech()]
        leeches_count = len(leeches)
        print(f"Leech Count : {leeches_count} ({leeches_count / self.lapsed_card_count * 100:.2f}% of Lapsed, {leeches_count / self.total_card_count * 100:.2f}% of All)")

        active_leeches = [lapse_info for lapse_info in self.lapsed_card_collection if lapse_info.is_active_leech()]
        active_leeches_count = len(active_leeches)
        print(f"Active Leech Count : {active_leeches_count} ({active_leeches_count / self.lapsed_card_count * 100:.2f}% of Lapsed, {active_leeches_count / self.total_card_count * 100:.2f}% of All)")
        # [ print(leech) for leech in active_leeches[0:10] ]
        # print(','.join([str(leech.card_id) for leech in active_leeches]))


        recovering_leeches = [ lapse_info for lapse_info in self.lapsed_card_collection if lapse_info.is_recovering_leech() ]
        recovering_leech_count = len(recovering_leeches)
        print(f"Recovering Leech Count : {recovering_leech_count} ({recovering_leech_count / leeches_count * 100:.2f}% of All Leech, {recovering_leech_count / self.lapsed_card_count * 100:.2f}% of Lapsed, {recovering_leech_count / self.total_card_count * 100:.2f}% of All)")
        [ print(leech) for leech in recovering_leeches[0:10] ]
        print(','.join([str(leech.card_id) for leech in recovering_leeches]))

def group_lapse_info_by_key(lapseInfos, key_function, filter=lambda lapseInfo: True):
    distributionDrops = {}
    for lapseInfo in lapseInfos:
        if filter(lapseInfo):
            key = key_function(lapseInfo)
            if key in distributionDrops:
                distributionDrops[key] += 1
            else:
                distributionDrops[key] = 1
    return distributionDrops

