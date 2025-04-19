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

        self.card_ids = [1710712242101, 1708207159229, 1723541612090, 1708259347988, 1708787872864, 1716748875647, 1715717287839]


    def test_compute_lapses_sizes(self):
        display_revlog(self.leechdetector.get_sorted_revlog(self.cardid))
        for card_id in self.card_ids:
            print(interval_to_duration_display(self.leechdetector.get_max_successful_interval(card_id)))

    def test_get_max_successful_interval_by_lapse(self):
        for card_id in self.card_ids:
            print(self.leechdetector.get_max_successful_interval_by_lapse(card_id))




def is_failed(button_chosen: int) -> bool:
    # Check if the review was a failure
    return button_chosen == 1

def display_revlog(review_log):
    for review in review_log:
        print(f"{time_to_date(review.time)} : {'OK' if not is_failed(review.button_chosen) else 'KO'}({review.button_chosen}) Interval:{interval_to_duration_display(review.interval)}")
