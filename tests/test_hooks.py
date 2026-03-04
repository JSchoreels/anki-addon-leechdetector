import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import leechdetector.hooks as hooks
from leechdetector.lapse_infos import LapseInfos


class FakeLapseInfos:
    def __init__(self, card_id, active=False, recovering=False, recovered=False, leech=False):
        self.card_id = card_id
        self.active = active
        self.recovering = recovering
        self.recovered = recovered
        self.leech = leech
        self.configure_calls = []

    def configure_leech_detection(self, **kwargs):
        self.configure_calls.append(kwargs)

    def is_leech(self):
        return self.leech

    def is_active_leech(self):
        return self.active

    def is_recovering_leech(self):
        return self.recovering

    def is_recovered_leech(self):
        return self.recovered


class FakeLeechDetector:
    def __init__(self, lapse_infos_by_card):
        self.lapse_infos_by_card = lapse_infos_by_card

    def get_lapse_infos(self, card_id):
        return self.lapse_infos_by_card[card_id]


class TestHooks(unittest.TestCase):

    def test_parse_leech_args_typed_values(self):
        parsed = hooks.parse_leech_args(" drop_count = 2, drop_ratio = 0.5, note = abc ")
        self.assertEqual(parsed, {"drop_count": 2, "drop_ratio": 0.5, "note": "abc"})

    def test_parse_search_for_leech_filters_last_definition_wins(self):
        search = (
            "deck:test leeches:active[drop_count=1] "
            "leeches:active[drop_count=2, drop_ratio=0.5] "
            "leeches:recovering"
        )

        parsed = hooks.parse_search_for_leech_filters(search)

        self.assertEqual(
            parsed,
            {
                "active": {"drop_count": 2, "drop_ratio": 0.5},
                "recovering": {},
            },
        )

    def test_filter_cards_keeps_matches_from_multiple_leech_types(self):
        card_1 = FakeLapseInfos(1, active=True, leech=True)
        card_2 = FakeLapseInfos(2, recovering=True, leech=True)
        card_3 = FakeLapseInfos(3, leech=False)

        fake_detector = FakeLeechDetector({1: card_1, 2: card_2, 3: card_3})
        leech_filters = {
            "active": {"drop_count": 3},
            "recovering": {"drop_ratio": 0.5},
        }

        with patch("leechdetector.hooks.LeechDetector", return_value=fake_detector):
            filtered = hooks.filter_cards([1, 2, 3], leech_filters)

        self.assertEqual(filtered, [1, 2])
        self.assertEqual(card_1.configure_calls, [{"drop_count": 3}, {"drop_ratio": 0.5}])
        self.assertEqual(card_2.configure_calls, [{"drop_count": 3}, {"drop_ratio": 0.5}])
        self.assertEqual(card_3.configure_calls, [{"drop_count": 3}, {"drop_ratio": 0.5}])

    def test_filter_cards_raises_for_unknown_arg_name(self):
        class RealDetector:
            def get_lapse_infos(self, card_id):
                return LapseInfos(card_id=card_id, past_max_intervals=[10, 5])

        with patch("leechdetector.hooks.LeechDetector", return_value=RealDetector()):
            with self.assertRaises(TypeError):
                hooks.filter_cards([1], {"active": {"dropcount": 2}})

    def test_handle_browser_will_search_filters_when_ids_absent(self):
        class DummyOrder:
            def __init__(self, key):
                self.key = key

        class DummyContext:
            def __init__(self):
                self.search = "deck:test leeches:active[drop_count=2] leeches:recovering"
                self.ids = None
                self.order = DummyOrder("noteFld")
                self.reverse = False

        context = DummyContext()
        expected_filters = {"active": {"drop_count": 2}, "recovering": {}}
        fake_col = Mock()
        fake_col.find_cards.return_value = [10, 20, 30]
        fake_mw = SimpleNamespace(col=fake_col)

        with patch("leechdetector.hooks.check_cross_addon_compatibility"), \
                patch.object(hooks.aqt, "mw", fake_mw), \
                patch("leechdetector.hooks.filter_cards", return_value=[20]) as filter_cards:
            out = hooks.handle_browser_will_search(context)

        self.assertIs(out, context)
        self.assertNotIn("leeches:", context.search)
        self.assertEqual(context.ids, [20])
        fake_col.find_cards.assert_called_once_with(context.search, context.order, context.reverse)
        filter_cards.assert_called_once_with([10, 20, 30], expected_filters)

    def test_handle_browser_will_search_keeps_existing_ids(self):
        class DummyOrder:
            def __init__(self, key):
                self.key = key

        class DummyContext:
            def __init__(self):
                self.search = "leeches:active[drop_count=1]"
                self.ids = [1, 2, 3]
                self.order = DummyOrder("noteFld")
                self.reverse = False

        context = DummyContext()
        fake_col = Mock()
        fake_mw = SimpleNamespace(col=fake_col)

        with patch.object(hooks.aqt, "mw", fake_mw), \
                patch("leechdetector.hooks.filter_cards") as filter_cards:
            out = hooks.handle_browser_will_search(context)

        self.assertIs(out, context)
        self.assertEqual(context.ids, [1, 2, 3])
        self.assertNotIn("leeches:", context.search)
        fake_col.find_cards.assert_not_called()
        filter_cards.assert_not_called()

    def test_handle_browser_will_search_without_leech_filter(self):
        class DummyOrder:
            def __init__(self, key):
                self.key = key

        class DummyContext:
            def __init__(self):
                self.search = "deck:test is:review"
                self.ids = None
                self.order = DummyOrder("noteFld")
                self.reverse = False

        context = DummyContext()
        fake_col = Mock()
        fake_mw = SimpleNamespace(col=fake_col)

        with patch.object(hooks.aqt, "mw", fake_mw), \
                patch("leechdetector.hooks.filter_cards") as filter_cards:
            out = hooks.handle_browser_will_search(context)

        self.assertIs(out, context)
        self.assertEqual(context.search, "deck:test is:review")
        self.assertIsNone(context.ids)
        fake_col.find_cards.assert_not_called()
        filter_cards.assert_not_called()

    def test_check_cross_addon_compatibility_rewrites_order_key(self):
        class DummyOrder:
            def __init__(self, key):
                self.key = key

        class DummyContext:
            def __init__(self):
                self.order = DummyOrder("_field_Custom")

        context = DummyContext()

        with patch("leechdetector.hooks.showWarning") as show_warning:
            hooks.check_cross_addon_compatibility(context)

        self.assertEqual(context.order.key, "noteFld")
        show_warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
