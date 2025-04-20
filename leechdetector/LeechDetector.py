from statistics import mean, median
from typing import Callable

from anki.cards import CardId
from anki.collection import Collection
from anki.stats_pb2 import CardStatsResponse
from aqt import mw

from AnkiValueParser import is_actual_review, is_failed, is_success, interval_to_days, time_to_days

class LapseInfos:

    def __init__(self, card_id : CardId, past_max_intervals : list[int], current_lapse_max_intervals : int):
        self.card_id = card_id
        self.past_max_intervals = past_max_intervals
        self.current_lapse_max_intervals = current_lapse_max_intervals
        self.lapses_count = len(past_max_intervals)

    def drop_count(self):
        return sum([1 for i in range(1, self.lapses_count) if self.past_max_intervals[i - 1] > self.past_max_intervals[i]])

    def biggest_drop_value(self):
        return max([self.past_max_intervals[i-1] - self.past_max_intervals[i] for i in range(1, self.lapses_count)])

    def average_max_interval(self):
        return mean(self.past_max_intervals)

    def median_max_interval(self):
        return median(self.past_max_intervals)


    def __repr__(self):
        return f'Card : {self.card_id} Past Lapses : ({self.lapses_count}) {self.past_max_intervals} (now:{self.current_lapse_max_intervals})  Drops:{self.drop_count()} BiggestDrop:{self.biggest_drop_value()} Mean:{self.average_max_interval():.2f} Median:{self.median_max_interval()}'

class LeechDetector:

    def __init__(self, collection: Collection):
        if not collection:
            self.collection = mw.col
        else:
            self.collection = collection

    def get_max_successful_interval(self, card_id: CardId) -> int:
        """
        Get the biggest successful interval for a card.
        """
        review_log = self.get_sorted_revlog(card_id)

        max_successful_interval = 0
        for i, review in enumerate(review_log):
            if is_actual_review(review) and not is_failed(review):
                max_successful_interval = max(max_successful_interval, review_log[i - 1].interval if i > 0 else 0)
        # Note : The last review is not considered as a successful review
        return max_successful_interval

    def get_max_successful_interval_by_lapse(self, card_id: CardId) -> LapseInfos:
        """
        For each lapse (when a card failed that day), the max successful interval is computed.
        :param card_id:
        :return:
        """
        review_log = self.get_sorted_revlog(card_id)

        current_max_success_ivl = 0
        current_day = time_to_days(review_log[0].time)

        max_successful_interval_by_lapse = []

        for i, review in enumerate(review_log):
            if current_day != time_to_days(review.time):
                if is_success(review):
                    current_max_success_ivl = max(current_max_success_ivl, interval_to_days(review.time) - interval_to_days(review_log[i-1].time))
                elif current_max_success_ivl > 0 : # We don't really want a failed rep after a previous cycle to count as a cycle
                    max_successful_interval_by_lapse.append(current_max_success_ivl)
                    current_max_success_ivl = 0
            current_day = interval_to_days(review.time)

        return LapseInfos(card_id, max_successful_interval_by_lapse, current_max_success_ivl)




    def get_sorted_revlog(self, card_id: CardId, filter: Callable[[CardStatsResponse.StatsRevlogEntry], bool] = lambda review: is_actual_review(review)) -> list:
        """
        Get the review log for a card.
        """
        # review_log = list(self.collection.get_review_logs(card_id=card_id))
        # review_log.reverse()

        return [review for review in reversed(list(self.collection.get_review_logs(card_id=card_id))) if filter(review)]