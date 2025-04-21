# import the main window object (mw) from aqt
from typing import List
import os

from anki.cards import CardId
from anki.collection import Collection
import aqt
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

    html_template_filename = os.path.join(LOCAL_DIR, 'leechdetector_table.html')
    js_template_filename = os.path.join(LOCAL_DIR, 'card_info_updated.js')

    with open(html_template_filename, 'r') as html_template, open(js_template_filename, 'r') as js_template:
        html_template = Template(html_template.read())
        table_html = html_template.substitute(lapse_infos.to_dict())

        js_template = Template(js_template.read())
        webview.eval(js_template.substitute({"table_html" : table_html}))


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