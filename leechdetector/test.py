import unittest
from typing import Sequence

from anki import stats_pb2
from anki._backend import RustBackend
from anki.collection import Collection
from anki.cards import CardId
from google.protobuf.message import Message

from AnkiValueParser import time_to_date, interval_to_duration_display
from LeechDetector import LeechDetector

class LeechDetectorTest(unittest.TestCase):

    def setUp(self):
        self.collection = Collection("data/collection.anki2")
        self.leechdetector = LeechDetector(self.collection)

        self.card_ids = [1710712242101, 1708207159229, 1723541612090, 1708259347988, 1708787872864, 1716748875647, 1715717287839, 1711230892107, 1708440946044,
                         1727897994100] # relearn


    def test_compute_lapses_sizes(self):
        display_revlog(self.leechdetector.get_sorted_revlog(self.cardid))
        for card_id in self.card_ids:
            print(interval_to_duration_display(self.leechdetector.get_max_successful_interval(card_id)))

    def test_get_max_successful_interval_by_lapse(self):
        for card_id in self.card_ids:
            print(self.leechdetector.get_max_successful_interval_by_lapse(card_id))

    def test_get_max_successful_interval_by_lapse(self):
        lapse_infos = []
        for card_id in self.collection.find_cards('"deck:Japan::1. Vocabulary" -is:new prop:lapses>0'):
            lapse_infos.append(self.leechdetector.get_max_successful_interval_by_lapse(card_id))
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

def is_failed(button_chosen: int) -> bool:
    # Check if the review was a failure
    return button_chosen == 1

def display_revlog(review_log):
    for review in review_log:
        print(f"{time_to_date(review.time)} : {'OK' if not is_failed(review.button_chosen) else 'KO'}({review.button_chosen}) Interval:{interval_to_duration_display(review.interval)}")
