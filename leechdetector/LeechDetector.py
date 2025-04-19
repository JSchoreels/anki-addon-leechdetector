from anki.collection import Collection
from aqt import mw

from AnkiValueParser import is_actual_review, is_failed, is_success, interval_to_days, time_to_days


class LeechDetector:

    def __init__(self, collection: Collection):
        if not collection:
            self.collection = mw.col
        else:
            self.collection = collection

    def get_max_successful_interval(self, card_id: int) -> int:
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

    def get_max_successful_interval_by_lapse(self, card_id: int) -> list[int]:
        """
        For each lapse (when a card failed that day), the max successful interval is computed.
        :param card_id:
        :return:
        """
        review_log = self.get_sorted_revlog(card_id)

        current_max_success_ivl = 0
        current_day = time_to_days(review_log[0].time)
        previous_review = review_log[0]

        max_successful_interval_by_lapse = []

        for i, review in enumerate(review_log):
            if is_actual_review(review):
                if current_day != time_to_days(review.time):
                    if is_success(review):
                        current_max_success_ivl = max(current_max_success_ivl, interval_to_days(review.time) - interval_to_days(previous_review.time))
                    else:
                        max_successful_interval_by_lapse.append(current_max_success_ivl)
                        current_max_success_ivl = 0
                previous_review = review
                current_day = interval_to_days(review.time)

        if is_success(review):
            max_successful_interval_by_lapse.append(current_max_success_ivl)

        return max_successful_interval_by_lapse




    def get_sorted_revlog(self, card_id: int) -> list:
        """
        Get the review log for a card.
        """
        review_log = list(self.collection.get_review_logs(card_id=card_id))
        review_log.reverse()
        return review_log