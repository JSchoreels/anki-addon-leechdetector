from statistics import mean, median

from anki.cards import CardId

import json

class LapseInfos:

    def __init__(self, card_id : CardId, past_max_intervals : list[int], current_lapse_max_intervals : int, outperformance_factor : float = 1.25):
        self.card_id = card_id
        self.past_max_intervals = past_max_intervals
        self.current_lapse_max_intervals = current_lapse_max_intervals
        self.lapses_count = len(past_max_intervals)
        self.outperformance_factor = outperformance_factor

    def drop_count(self):
        return sum([1 for i in range(1, self.lapses_count) if self.past_max_intervals[i - 1] > self.past_max_intervals[i]])

    def failed_outperformance_count(self):
        return sum([1 for i in range(1, self.lapses_count) if not self.past_max_intervals[i - 1] < self.past_max_intervals[i] * self.outperformance_factor])

    def failed_outperformance_ratio(self):
        if self.lapses_count <= 1:
            return 0
        return self.failed_outperformance_count() / (self.lapses_count - 1)

    def biggest_interval_drop(self):
        if self.drop_count() == 0:
            return 0
        return max([self.past_max_intervals[i-1] - self.past_max_intervals[i] for i in range(1, self.lapses_count) if self.past_max_intervals[i-1] - self.past_max_intervals[i] > 0])

    def average_max_interval(self):
        return mean(self.past_max_intervals)

    def median_max_interval(self):
        return median(self.past_max_intervals)


    def __repr__(self):
        if self.lapses_count > 0:
            return f'Card : {self.card_id} Past Lapses : ({self.lapses_count}) {self.past_max_intervals} (now:{self.current_lapse_max_intervals})  Drops:{self.drop_count()} BiggestDrop:{self.biggest_interval_drop()} Mean:{self.average_max_interval():.2f} Median:{self.median_max_interval()} FailedOutperforamnce:{self.failed_outperformance_count()} FailedOutperforamnceRatio:{self.failed_outperformance_ratio() * 100:.2f}'
        else:
            return f'Card : {self.card_id} No Lapse, Current Max Interval : {self.current_lapse_max_intervals}'

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
            "failed_outperformance_ratio" : self.failed_outperformance_ratio()
        })
        print(base)
        return base