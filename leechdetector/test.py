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
        lapse_infos.sort(key=lambda lapseInfo: lapseInfo.lapses_count, reverse=True)
        distribution_drops = group_lapse_info_by_key(lapse_infos, lambda lapseInfo: lapseInfo.drop_count())
        distribution_lapse_count = group_lapse_info_by_key(lapse_infos, lambda lapseInfo: lapseInfo.lapses_count)
        total_card_count = len(self.collection.find_cards('"deck:Japan::1. Vocabulary" -is:new'))
        print(f"Total Cards reviewed : {total_card_count}")
        print(f"Cards That lapsed at least once: {len(lapse_infos)} ({len(lapse_infos) / total_card_count * 100:.2f}%)")
        print(f"Cards That had 0 dropping lapse: {distribution_drops[0]} ({distribution_drops[0] / total_card_count * 100:.2f}%)")
        print(f"Cards That had 1 dropping lapse: {distribution_drops[1]} ({distribution_drops[1] / total_card_count * 100:.2f}%)")
        card_count_other = sum([dropCount for (drop, dropCount) in distribution_drops.items() if drop > 1])
        print(f"Cards That had >1 dropping lapse : {card_count_other} ({card_count_other / total_card_count * 100:.2f}%)")
        print(distribution_drops)
        print(distribution_lapse_count)
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
