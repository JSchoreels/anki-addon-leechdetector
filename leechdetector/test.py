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
        self.collection = Collection("collection.anki2")
        self.leechdetector = LeechDetector(self.collection)
        self.cardid = CardId(1710712242101)
        self.cardid2 = CardId(1708259347988)


    def test_compute_lapses_sizes(self):
        display_revlog(self.leechdetector.get_sorted_revlog(self.cardid))
        print(interval_to_duration_display(self.leechdetector.get_max_successful_interval(self.cardid)))
        print(interval_to_duration_display(self.leechdetector.get_max_successful_interval(self.cardid2)))

    def test_get_max_successful_interval_by_lapse(self):
        print([interval for interval in self.leechdetector.get_max_successful_interval_by_lapse(self.cardid)])
        print([interval for interval in self.leechdetector.get_max_successful_interval_by_lapse(self.cardid2)])




def is_failed(button_chosen: int) -> bool:
    # Check if the review was a failure
    return button_chosen == 1

def display_revlog(review_log):
    for review in review_log:
        print(f"{time_to_date(review.time)} : {'OK' if not is_failed(review.button_chosen) else 'KO'}({review.button_chosen}) Interval:{interval_to_duration_display(review.interval)}")
