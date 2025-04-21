from typing import Callable

from anki.cards import CardId
from anki.collection import Collection
from anki.stats_pb2 import CardStatsResponse
from aqt import mw

from leechdetector.AnkiValueParser import is_actual_review, is_failed, is_success, interval_to_days, time_to_days, \
    time_to_date
from leechdetector.lapse_infos import LapseInfos


class LeechDetector:

    def __init__(self, collection: Collection = None):
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

    def get_lapse_infos(self, card_id: CardId) -> LapseInfos:
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

    def display_revlog(review_log):
        for review in review_log:
            print(
                f"{time_to_date(review.time)} : {'OK' if not is_failed(review.button_chosen) else 'KO'}({review.button_chosen}) Interval:{interval_to_duration_display(review.interval)}")
