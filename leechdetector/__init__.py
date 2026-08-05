# import the main window object (mw) from aqt
import json
import logging
import re
import weakref
from typing import Optional

import aqt
from anki.cards import CardId
from aqt import mw
from aqt.qt import *
from aqt import gui_hooks
from aqt.operations import QueryOp
from aqt.webview import AnkiWebViewKind
from aqt.browser import Column as BuiltinColumn
from aqt.utils import showWarning # Make sure to import this

from .browse_custom_search import RE_CUSTOMSEARCH

LOCAL_DIR = os.path.dirname(__file__)
from .leech_detector import LeechDetector

from string import Template

LEECHDETECTOR_CARD_COMMAND = "leechdetector:getcard:"
_card_info_webviews = {}


def _register_card_info_webview(webview):
    token = str(id(webview))

    def remove_stale_reference(reference):
        if _card_info_webviews.get(token) is reference:
            _card_info_webviews.pop(token, None)

    _card_info_webviews[token] = weakref.ref(webview, remove_stale_reference)
    return token

def get_lapseinfos_for_card(webview : "aqt.webview.AnkiWebView") -> dict:
    """
    Get lapse infos for a card.
    """

    with (open(os.path.join(LOCAL_DIR, 'leechdetector_table.html'), 'r') as html_template,
          open(os.path.join(LOCAL_DIR, 'card_info_updated.js'), 'r') as js_template):

        try:
            table_html = Template(html_template.read()).safe_substitute({})
            webview_token = _register_card_info_webview(webview)

            webview.eval(
                Template(js_template.read())
                .substitute({
                    "table_html" : table_html,
                    "webview_token": json.dumps(webview_token),
                }))
        except KeyError as error:
            logging.error(f"leechdetector addon was unable to modify the webview. Missing Key : {str(error)}")

gui_hooks.webview_did_inject_style_into_page.append(
    lambda w: get_lapseinfos_for_card(w) if isinstance(w, aqt.webview.AnkiWebView) and w.kind == AnkiWebViewKind.BROWSER_CARD_INFO else None
)

def handle_webview_did_receive_js_message(handled, message : str, context):
    # print(f"Received JS message. Handled : {handled}, Message : {message}, Context : {context}")
    if not message.startswith(LEECHDETECTOR_CARD_COMMAND):
        return handled

    request = message.removeprefix(LEECHDETECTOR_CARD_COMMAND)
    try:
        webview_token, request_id_text, card_id_text = request.split(":", 2)
        request_id = int(request_id_text)
        card_id = CardId(int(card_id_text))
    except ValueError:
        logging.error(f'Received an invalid leechdetector card request: "{request}"')
        return handled

    webview_reference = _card_info_webviews.get(webview_token)
    webview = webview_reference() if webview_reference is not None else None
    if webview is None:
        _card_info_webviews.pop(webview_token, None)
        return True, None

    def load_lapse_infos(collection):
        return LeechDetector(collection).get_lapse_infos(card_id).to_dict_enriched()

    def deliver_lapse_infos(lapse_infos):
        current_reference = _card_info_webviews.get(webview_token)
        current_webview = (
            current_reference() if current_reference is not None else None
        )
        if current_webview is None:
            _card_info_webviews.pop(webview_token, None)
            return

        try:
            current_webview.eval(
                "window.leechDetectorReceive(%s, %s, %s);"
                % (request_id, int(card_id), json.dumps(lapse_infos))
            )
        except RuntimeError:
            _card_info_webviews.pop(webview_token, None)

    def report_failure(error):
        logging.error(
            "leechdetector failed to load card %s in the background: %s",
            int(card_id),
            error,
        )

    QueryOp(
        parent=webview,
        op=load_lapse_infos,
        success=deliver_lapse_infos,
    ).failure(report_failure).run_in_background()
    return True, None

gui_hooks.webview_did_receive_js_message.append(
    handle_webview_did_receive_js_message
)


