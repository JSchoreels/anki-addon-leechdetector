import unittest
from unittest.mock import mock_open, patch

import leechdetector as addon


class DummyWebView:
    def __init__(self):
        self.eval_calls = []

    def eval(self, script):
        self.eval_calls.append(script)


class DummyLapseInfos:
    def __init__(self, payload):
        self.payload = payload

    def to_dict_enriched(self):
        return self.payload


class DummyDetector:
    def __init__(self, payload):
        self.payload = payload
        self.received_card_ids = []

    def get_lapse_infos(self, card_id):
        self.received_card_ids.append(int(card_id))
        return DummyLapseInfos(self.payload)


class DummyQueryOp:
    instances = []

    def __init__(self, *, parent, op, success):
        self.parent = parent
        self.op = op
        self.success = success
        self.failure_callback = None
        self.started = False
        self.instances.append(self)

    def failure(self, callback):
        self.failure_callback = callback
        return self

    def run_in_background(self):
        self.started = True


class TestInitModule(unittest.TestCase):
    def setUp(self):
        addon._card_info_webviews.clear()
        DummyQueryOp.instances.clear()

    def test_get_lapseinfos_for_card_injects_script(self):
        webview = DummyWebView()

        addon.get_lapseinfos_for_card(webview)

        self.assertEqual(len(webview.eval_calls), 1)
        injected_script = webview.eval_calls[0]
        self.assertIn("Current Cycle Max Interval", injected_script)
        self.assertIn('"leechdetector:getcard:"', injected_script)

    def test_get_lapseinfos_for_card_logs_missing_template_key(self):
        webview = DummyWebView()

        html_file = mock_open(read_data="<tr><td>ok</td></tr>").return_value
        js_file = mock_open(read_data="const row = '$missing_key';").return_value

        with patch("builtins.open", side_effect=[html_file, js_file]), \
                patch("leechdetector.logging.error") as log_error:
            addon.get_lapseinfos_for_card(webview)

        self.assertEqual(webview.eval_calls, [])
        log_error.assert_called_once()

    def test_handle_webview_did_receive_js_message_loads_payload_in_background(self):
        webview = DummyWebView()
        addon.get_lapseinfos_for_card(webview)
        webview_token = next(iter(addon._card_info_webviews))
        detector = DummyDetector(payload={"card_id": "123", "leech_status": "Healthy"})

        with patch("leechdetector.LeechDetector", return_value=detector), \
                patch("leechdetector.QueryOp", DummyQueryOp):
            response = addon.handle_webview_did_receive_js_message(
                False,
                f"leechdetector:getcard:{webview_token}:7:123",
                None,
            )

            self.assertEqual(response, (True, None))
            self.assertEqual(detector.received_card_ids, [])
            self.assertEqual(len(DummyQueryOp.instances), 1)
            query = DummyQueryOp.instances[0]
            self.assertIs(query.parent, webview)
            self.assertTrue(query.started)

            payload = query.op(object())
            query.success(payload)

        self.assertEqual(detector.received_card_ids, [123])
        self.assertIn(
            'window.leechDetectorReceive(7, 123, {"card_id": "123", "leech_status": "Healthy"});',
            webview.eval_calls[-1],
        )

    def test_handle_webview_did_receive_js_message_logs_invalid_card_id(self):
        original_handled = (False, None)

        with patch("leechdetector.LeechDetector"), \
                patch("leechdetector.logging.error") as log_error:
            out = addon.handle_webview_did_receive_js_message(
                original_handled,
                "leechdetector:getcard:not_an_int",
                None,
            )

        self.assertEqual(out, original_handled)
        log_error.assert_called_once()

    def test_handle_webview_did_receive_js_message_ignores_unrelated_messages(self):
        original_handled = "already_handled"

        with patch("leechdetector.LeechDetector") as detector_cls:
            out = addon.handle_webview_did_receive_js_message(
                original_handled,
                "some:other:message",
                None,
            )

        self.assertEqual(out, original_handled)
        detector_cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
