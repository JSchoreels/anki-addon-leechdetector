from statistics import mean, median

from anki.cards import CardId

import json

class LapseInfos:

    def __init__(self, card_id : CardId, past_max_intervals : list[int], current_lapse_max_intervals : int = 0, date_first_review : int = 0, review_count : int = 0, improvement_factor : float = 1.25, drop_factor : float = 0.75):
        self.card_id = card_id
        self.past_max_intervals = past_max_intervals
        self.date_first_review = date_first_review
        self.review_count = review_count
        self.current_lapse_max_intervals = current_lapse_max_intervals
        self.lapses_count = len(past_max_intervals)
        self.improvement_factor = improvement_factor
        self.configure_leech_detection()

    def configure_leech_detection(self, drop_count=1, drop_ratio=0.33):
        self.drop_count = drop_count
        self.drop_ratio = drop_ratio

    def performance_drop_count(self):
        return sum([1 for i in range(1, self.lapses_count) if self.past_max_intervals[i - 1] > self.past_max_intervals[i]])

    def performance_drop_ratio(self):
        if self.lapses_count <= 1:
            return 0
        return self.performance_drop_count() / (self.lapses_count - 1)

    def failed_improvement_count(self):
        return sum([1 for i in range(1, self.lapses_count) if not self.past_max_intervals[i - 1] * self.improvement_factor <= self.past_max_intervals[i]])

    def failed_improvement_ratio(self):
        if self.lapses_count <= 1:
            return 0
        return self.failed_improvement_count() / (self.lapses_count - 1)

    def biggest_interval_drop(self):
        if self.performance_drop_count() == 0:
            return 0
        return max([self.past_max_intervals[i-1] - self.past_max_intervals[i] for i in range(1, self.lapses_count) if self.past_max_intervals[i-1] - self.past_max_intervals[i] > 0])

    def average_max_interval(self):
        return mean(self.past_max_intervals)

    def median_max_interval(self):
        return median(self.past_max_intervals)

    def days_by_reviews(self):
        return self.date_first_review / self.review_count

    def is_leech(self):
        is_leech = True
        is_leech = is_leech and self.performance_drop_count() > self.drop_count
        is_leech = is_leech and self.performance_drop_ratio() > self.drop_ratio
        return is_leech

    def is_recovering_leech(self):
        return self.is_leech() and self.days_above_past_max_intervals() > max(self.past_max_intervals) and not self.is_recovered_leech()

    def is_recovered_leech(self):
        return self.is_leech() and self.days_above_past_max_intervals() > max(self.past_max_intervals) * 2

    def days_above_past_max_intervals(self):
        return self.current_lapse_max_intervals - max(self.past_max_intervals)

    def is_active_leech(self):
        return self.is_leech() and not self.is_recovering_leech() and not self.is_recovered_leech()

    def leech_status(self):
        if self.is_active_leech():
            return "Leech"
        elif self.is_recovered_leech():
            return f"Recovered"
        elif self.is_recovering_leech():
            return f"Recovering"
        else:
            return "Healthy"

    def __repr__(self):
        if self.lapses_count > 0:
            return f'Card : {self.card_id} Days:{self.date_first_review:3d} Reviews:{self.review_count}({self.date_first_review/self.review_count:3.2f}d/r Lapses:{self.lapses_count}) PastLapses:{self.past_max_intervals} (now:{self.current_lapse_max_intervals}({self.days_above_past_max_intervals():+d}))  Drops:{self.performance_drop_count()} FailedImprovement:{self.failed_improvement_count()} FailedImprovementRatio:{self.failed_improvement_ratio() * 100:.2f}'
        else:
            return f'Card : {self.card_id} Days:{self.date_first_review:3d} Reviews:{self.review_count}({self.date_first_review/self.review_count:3.2f}d/r) No Lapse, Current Max Interval : {self.current_lapse_max_intervals}'

    def to_dict(self):
        return {
            "card_id": str(self.card_id),  # Convert card_id to string if it's not JSON serializable
            "past_max_intervals": self.past_max_intervals,
            "current_lapse_max_intervals": self.current_lapse_max_intervals,
        }

    def to_dict_enriched(self):
        base = self.to_dict()
        base.update({
            "biggest_interval_drop" : self.biggest_interval_drop(),
            "failed_improvement_ratio" : self.failed_improvement_ratio(),
            "leech_status" : self.leech_status(),
            "performance_drop_count": self.performance_drop_count(),
            "performance_drop_ratio":self.performance_drop_ratio()
        })
        return base
