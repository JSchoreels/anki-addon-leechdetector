# import the main window object (mw) from aqt
from typing import List
import os

import aqt
from anki.cards import CardId
from aqt import mw
from aqt.qt import *
from aqt import gui_hooks
from aqt.webview import AnkiWebViewKind

LOCAL_DIR = os.path.dirname(__file__)
from leechdetector.leech_detector import LeechDetector

from string import Template

def get_lapseinfos_for_card(webview : "aqt.webview.AnkiWebView") -> dict:
    """
    Get lapse infos for a card.
    """

    if not webview.kind == AnkiWebViewKind.BROWSER_CARD_INFO:
        print(webview.kind)
    leechdetector = LeechDetector()
    lapse_infos = leechdetector.get_lapse_infos(mw.col.sched.getCard().id)

    with (open(os.path.join(LOCAL_DIR, 'leechdetector_table.html'), 'r') as html_template,
          open(os.path.join(LOCAL_DIR, 'card_info_updated.js'), 'r') as js_template):

        table_html = Template(html_template.read()).substitute(lapse_infos.to_dict())

        webview.eval(
            Template(js_template.read())
            .substitute({"table_html" : table_html}))


gui_hooks.webview_did_inject_style_into_page.append(
    lambda w: get_lapseinfos_for_card(w) if isinstance(w, aqt.webview.AnkiWebView) and w.kind == AnkiWebViewKind.BROWSER_CARD_INFO else None
)

def handle_webview_did_receive_js_message(handled, message : str, context):
    print(f"handled : {handled}")
    print(f"message : {message}")
    print(f"context : {context}")
    if "new_card_id:" in message:
        leechdetector = LeechDetector()
        return True, leechdetector.get_lapse_infos(CardId(int(message.split(":")[1]))).past_max_intervals
    return handled

gui_hooks.webview_did_receive_js_message.append(
    handle_webview_did_receive_js_message
)