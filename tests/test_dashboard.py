import unittest
from unittest.mock import Mock, patch

from leechdetector import dashboard


class FakeDecks:
    def __init__(self, names_by_did):
        self._names_by_did = names_by_did

    def name(self, did):
        return self._names_by_did[did]


class FakeCollection:
    def __init__(self, cards_by_query, names_by_did=None):
        self._cards_by_query = cards_by_query
        self.find_cards_calls = []
        self.decks = FakeDecks(names_by_did or {})

    def find_cards(self, query):
        self.find_cards_calls.append(query)
        return list(self._cards_by_query.get(query, []))


class TestDashboard(unittest.TestCase):
    def test_get_status_card_ids_runs_expected_queries(self):
        col = FakeCollection(
            {
                "leeches:active": [1, 2],
                "leeches:recovering": [3],
                "leeches:recovered": [4, 5, 6],
            }
        )

        out = dashboard.get_status_card_ids(col)

        self.assertEqual(
            out,
            {
                "active": [1, 2],
                "recovering": [3],
                "recovered": [4, 5, 6],
            },
        )
        self.assertEqual(
            col.find_cards_calls,
            ["leeches:active", "leeches:recovering", "leeches:recovered"],
        )

    def test_get_status_counts_uses_precomputed_status_ids(self):
        col = FakeCollection({"leeches:all": [10, 20, 30, 40]})

        out = dashboard.get_status_counts(
            col,
            status_card_ids={
                "active": [10, 20],
                "recovering": [30],
                "recovered": [],
            },
        )

        self.assertEqual(
            out,
            {"all": 4, "active": 2, "recovering": 1, "recovered": 0},
        )
        self.assertEqual(col.find_cards_calls, ["leeches:all"])

    def test_get_deck_rows_aggregates_counts_per_status(self):
        col = FakeCollection(
            cards_by_query={},
            names_by_did={10: "Spanish", 20: "French", 30: "Biology"},
        )

        status_card_ids = {
            "active": [1, 2],
            "recovering": [3, 4],
            "recovered": [5],
        }

        def fake_counts_by_did(_col, cids):
            key = tuple(cids)
            if key == (1, 2):
                return [(10, 2)]
            if key == (3, 4):
                return [(10, 1), (20, 1)]
            if key == (5,):
                return [(30, 1)]
            return []

        out = dashboard.get_deck_rows(col, status_card_ids, counts_by_did_fn=fake_counts_by_did)

        self.assertEqual(
            out,
            [
                {
                    "did": 10,
                    "deck": "Spanish",
                    "all": 3,
                    "active": 2,
                    "recovering": 1,
                    "recovered": 0,
                },
                {
                    "did": 30,
                    "deck": "Biology",
                    "all": 1,
                    "active": 0,
                    "recovering": 0,
                    "recovered": 1,
                },
                {
                    "did": 20,
                    "deck": "French",
                    "all": 1,
                    "active": 0,
                    "recovering": 1,
                    "recovered": 0,
                },
            ],
        )

    def test_get_deck_rows_sorts_ties_by_deck_name_case_insensitive(self):
        col = FakeCollection(
            cards_by_query={},
            names_by_did={10: "zeta", 20: "Alpha"},
        )

        status_card_ids = {
            "active": [100],
            "recovering": [200],
            "recovered": [],
        }

        def fake_counts_by_did(_col, cids):
            if cids == [100]:
                return [(10, 2)]
            if cids == [200]:
                return [(20, 2)]
            return []

        out = dashboard.get_deck_rows(col, status_card_ids, counts_by_did_fn=fake_counts_by_did)

        self.assertEqual([row["deck"] for row in out], ["Alpha", "zeta"])

    def test_get_status_for_column(self):
        self.assertEqual(dashboard.get_status_for_column(0), "all")
        self.assertEqual(dashboard.get_status_for_column(1), "all")
        self.assertEqual(dashboard.get_status_for_column(2), "active")
        self.assertEqual(dashboard.get_status_for_column(3), "recovering")
        self.assertEqual(dashboard.get_status_for_column(4), "recovered")
        self.assertEqual(dashboard.get_status_for_column(99), "all")

    def test_build_deck_status_query_escapes_deck_name(self):
        out = dashboard.build_deck_status_query('Deck "A"\\B', "recovering")
        self.assertEqual(out, 'deck:"Deck \\"A\\"\\\\B" leeches:recovering')

    def test_get_query_for_cell(self):
        rows = [{"deck": "Spanish"}, {"deck": "French::Verbs"}]

        self.assertEqual(
            dashboard.get_query_for_cell(rows, 0, 2),
            'deck:"Spanish" leeches:active',
        )
        self.assertEqual(
            dashboard.get_query_for_cell(rows, 1, 4),
            'deck:"French::Verbs" leeches:recovered',
        )
        self.assertEqual(
            dashboard.get_query_for_cell(rows, 1, 0),
            'deck:"French::Verbs" leeches:all',
        )
        self.assertIsNone(dashboard.get_query_for_cell(rows, -1, 1))
        self.assertIsNone(dashboard.get_query_for_cell(rows, 2, 1))

    def test_double_click_opens_browser_with_expected_search(self):
        browser = Mock()
        dialog = type("FakeDialog", (), {"deck_rows": [{"deck": "Spanish"}]})()

        with patch("leechdetector.dashboard.dialogs.open", return_value=browser) as open_browser:
            dashboard.LeechSummaryDialog._on_cell_double_clicked(dialog, 0, 3)

        open_browser.assert_called_once()
        browser.search_for.assert_called_once_with('deck:"Spanish" leeches:recovering')

    def test_double_click_does_nothing_for_invalid_row(self):
        dialog = type("FakeDialog", (), {"deck_rows": [{"deck": "Spanish"}]})()

        with patch("leechdetector.dashboard.dialogs.open") as open_browser:
            dashboard.LeechSummaryDialog._on_cell_double_clicked(dialog, 42, 2)

        open_browser.assert_not_called()


if __name__ == "__main__":
    unittest.main()
