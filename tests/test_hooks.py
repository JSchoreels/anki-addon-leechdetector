import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import leechdetector.hooks as hooks
import leechdetector.patches as patches
from leechdetector.lapse_infos import LapseInfos
from anki.stats_pb2 import GraphsRequest


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

    def test_filter_cards_deduplicates_when_same_card_matches_multiple_filters(self):
        card_1 = FakeLapseInfos(1, active=True, recovering=True, leech=True)
        card_2 = FakeLapseInfos(2, active=False, recovering=True, leech=True)
        fake_detector = FakeLeechDetector({1: card_1, 2: card_2})

        with patch("leechdetector.hooks.LeechDetector", return_value=fake_detector):
            filtered = hooks.filter_cards(
                [1, 2],
                {"active": {"drop_count": 1}, "recovering": {"drop_ratio": 0.5}},
            )

        self.assertEqual(filtered, [1, 2])

    def test_filter_cards_raises_for_unknown_arg_name(self):
        class RealDetector:
            def get_lapse_infos(self, card_id):
                return LapseInfos(card_id=card_id, past_max_intervals=[10, 5])

        with patch("leechdetector.hooks.LeechDetector", return_value=RealDetector()):
            with self.assertRaises(TypeError):
                hooks.filter_cards([1], {"active": {"dropcount": 2}})

    def test_find_cards_with_custom_leech_filters_without_filters(self):
        find_cards_mock = Mock(return_value=[10, 20])

        with patch("leechdetector.patches.filter_cards_with_detector") as filter_mock:
            out = patches.find_cards_with_custom_leech_filters(
                query="deck:test is:review",
                order=False,
                reverse=False,
                find_cards_func=find_cards_mock,
            )

        self.assertEqual(out, [10, 20])
        find_cards_mock.assert_called_once_with("deck:test is:review", False, False)
        filter_mock.assert_not_called()

    def test_find_cards_with_custom_leech_filters_with_filters(self):
        find_cards_mock = Mock(return_value=[10, 20, 30])
        fake_detector = object()

        with patch("leechdetector.patches.filter_cards_with_detector", return_value=[20]) as filter_mock:
            out = patches.find_cards_with_custom_leech_filters(
                query="deck:test leeches:all leeches:active[drop_count=2]",
                order="noteFld",
                reverse=True,
                find_cards_func=find_cards_mock,
                leechdetector_factory=lambda: fake_detector,
            )

        self.assertEqual(out, [20])
        find_cards_mock.assert_called_once_with("deck:test * *", "noteFld", True)
        filter_mock.assert_called_once_with(
            [10, 20, 30],
            {"all": {}, "active": {"drop_count": 2}},
            fake_detector,
        )

    def test_find_cards_with_custom_leech_filters_accepts_bytes_query(self):
        find_cards_mock = Mock(return_value=[10, 20, 30])
        fake_detector = object()

        with patch("leechdetector.patches.filter_cards_with_detector", return_value=[20]) as filter_mock:
            out = patches.find_cards_with_custom_leech_filters(
                query=b"deck:test leeches:all",
                order=False,
                reverse=False,
                find_cards_func=find_cards_mock,
                leechdetector_factory=lambda: fake_detector,
            )

        self.assertEqual(out, [20])
        find_cards_mock.assert_called_once_with("deck:test *", False, False)
        filter_mock.assert_called_once_with([10, 20, 30], {"all": {}}, fake_detector)

    def test_patch_find_cards_for_leech_filters_is_idempotent(self):
        class FakeCollection:
            def find_cards(self, query, order=False, reverse=False):
                return [1, 2, 3]

        original_find_cards = FakeCollection.find_cards

        with patch("leechdetector.patches.find_cards_with_custom_leech_filters", return_value=[2]) as helper:
            patches.patch_find_cards_for_leech_filters(FakeCollection)
            first_wrapped = FakeCollection.find_cards
            patches.patch_find_cards_for_leech_filters(FakeCollection)

            self.assertIs(FakeCollection.find_cards, first_wrapped)
            self.assertIs(FakeCollection._leechdetector_original_find_cards, original_find_cards)

            collection = FakeCollection()
            out = collection.find_cards("leeches:all", "noteFld", True)

        self.assertEqual(out, [2])
        helper.assert_called_once()

    def test_patch_graphs_raw_for_leech_filters_rewrites_leech_query_to_cids(self):
        class FakeBackend:
            def graphs_raw(self, message):
                req = GraphsRequest()
                req.ParseFromString(message)
                return req.search.encode("utf-8")

        class FakeCollection:
            def find_cards(self, query):
                self.query = query
                return [10, 20, 30]

        fake_col = FakeCollection()

        patches.patch_graphs_raw_for_leech_filters(FakeBackend, col_provider=lambda: fake_col)

        request = GraphsRequest(search="deck:test leeches:all", days=30)
        out = FakeBackend().graphs_raw(request.SerializeToString())

        self.assertEqual(fake_col.query, "deck:test leeches:all")
        self.assertEqual(out.decode("utf-8"), "cid:10,20,30")

    def test_patch_graphs_raw_for_leech_filters_sets_empty_cid_query(self):
        class FakeBackend:
            def graphs_raw(self, message):
                req = GraphsRequest()
                req.ParseFromString(message)
                return req.search.encode("utf-8")

        class FakeCollection:
            def find_cards(self, query):
                self.query = query
                return []

        fake_col = FakeCollection()

        patches.patch_graphs_raw_for_leech_filters(FakeBackend, col_provider=lambda: fake_col)

        request = GraphsRequest(search="leeches:all", days=30)
        out = FakeBackend().graphs_raw(request.SerializeToString())

        self.assertEqual(fake_col.query, "leeches:all")
        self.assertEqual(out.decode("utf-8"), "cid:0")

    def test_patch_graphs_raw_for_leech_filters_keeps_non_leech_query(self):
        class FakeBackend:
            def graphs_raw(self, message):
                req = GraphsRequest()
                req.ParseFromString(message)
                return req.search.encode("utf-8")

        class FakeCollection:
            def find_cards(self, query):
                raise AssertionError("find_cards should not be called for non-leech queries")

        patches.patch_graphs_raw_for_leech_filters(FakeBackend, col_provider=lambda: FakeCollection())

        request = GraphsRequest(search="deck:test is:review", days=30)
        out = FakeBackend().graphs_raw(request.SerializeToString())

        self.assertEqual(out.decode("utf-8"), "deck:test is:review")

    def test_patch_graphs_raw_for_leech_filters_is_idempotent(self):
        class FakeBackend:
            def graphs_raw(self, message):
                return message

        original_graphs_raw = FakeBackend.graphs_raw
        patches.patch_graphs_raw_for_leech_filters(FakeBackend, col_provider=lambda: None)
        first_wrapped = FakeBackend.graphs_raw
        patches.patch_graphs_raw_for_leech_filters(FakeBackend, col_provider=lambda: None)

        self.assertIs(FakeBackend.graphs_raw, first_wrapped)
        self.assertIs(FakeBackend._leechdetector_original_graphs_raw, original_graphs_raw)

    def test_patch_graphs_raw_for_leech_filters_falls_back_on_error(self):
        class FakeBackend:
            def graphs_raw(self, message):
                req = GraphsRequest()
                req.ParseFromString(message)
                return f"orig:{req.search}".encode("utf-8")

        patches.patch_graphs_raw_for_leech_filters(
            FakeBackend,
            col_provider=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        request = GraphsRequest(search="leeches:all", days=30)
        out = FakeBackend().graphs_raw(request.SerializeToString())
        self.assertEqual(out.decode("utf-8"), "orig:leeches:all")

    def test_is_stats_graphs_patch_enabled_defaults_to_true(self):
        self.assertTrue(patches.is_stats_graphs_patch_enabled({}))
        self.assertTrue(patches.is_stats_graphs_patch_enabled(None))

    def test_is_stats_graphs_patch_enabled_reads_config_flag(self):
        self.assertFalse(patches.is_stats_graphs_patch_enabled({"enable_stats_graphs_patch": False}))
        self.assertTrue(patches.is_stats_graphs_patch_enabled({"enable_stats_graphs_patch": True}))

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
