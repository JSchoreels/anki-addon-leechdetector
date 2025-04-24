# import the main window object (mw) from aqt
import json
import logging
from typing import List
import os

import aqt
from anki.cards import CardId
from aqt import mw
from aqt.qt import *
from aqt import gui_hooks
from aqt.webview import AnkiWebViewKind

LOCAL_DIR = os.path.dirname(__file__)
from .leech_detector import LeechDetector

from string import Template

def get_lapseinfos_for_card(webview : "aqt.webview.AnkiWebView") -> dict:
    """
    Get lapse infos for a card.
    """

    with (open(os.path.join(LOCAL_DIR, 'leechdetector_table.html'), 'r') as html_template,
          open(os.path.join(LOCAL_DIR, 'card_info_updated.js'), 'r') as js_template):

        try:
            table_html = Template(html_template.read()).safe_substitute({})

            webview.eval(
                Template(js_template.read())
                .substitute({"table_html" : table_html}))
        except KeyError as error:
            logging.error(f"leechdetector addon was unable to modify the webview. Missing Key : {str(error)}")

gui_hooks.webview_did_inject_style_into_page.append(
    lambda w: get_lapseinfos_for_card(w) if isinstance(w, aqt.webview.AnkiWebView) and w.kind == AnkiWebViewKind.BROWSER_CARD_INFO else None
)

def handle_webview_did_receive_js_message(handled, message : str, context):
    # print(f"Received JS message. Handled : {handled}, Message : {message}, Context : {context}")
    if "leechdetector:getcard:" in message:
        leechdetector = LeechDetector()
        card_id_received = message.split("leechdetector:getcard:")[1]
        try:
            int(card_id_received)
            return True, json.dumps(leechdetector.get_lapse_infos(CardId(int(card_id_received))).to_dict_enriched())
        except ValueError:
            logging.error(f'Received a non integer card id : "{card_id_received}"')
    return handled

gui_hooks.webview_did_receive_js_message.append(
    handle_webview_did_receive_js_message
)

def handle_browser_will_search(context : aqt.browser.SearchContext):
    # print(f"handle_browser_will_search : {context}")
    splitted_search = context.search.split(" ")
    if len([term for term in splitted_search if term.startswith("leeches:")]) > 0:
        leechdetector = LeechDetector()
        if context.ids is None:
            search_filtered = " ".join([term for term in splitted_search if not term.startswith("leeches:")])
            card_ids = mw.col.find_cards(search_filtered, context.order, context.reverse)
        else:
            card_ids = context.ids
        if "leeches:all" in splitted_search:
            context.ids = [ card_id for card_id in card_ids if leechdetector.get_lapse_infos(card_id).is_leech()]
        else:
            context.ids = []
            if "leeches:active" in splitted_search:
                context.ids = context.ids + [ card_id for card_id in card_ids if leechdetector.get_lapse_infos(card_id).is_active_leech()]
            if "leeches:recovering" in splitted_search:
                context.ids = context.ids + [ card_id for card_id in card_ids if leechdetector.get_lapse_infos(card_id).is_recovering_leech()]
            if "leeches:recovered" in splitted_search:
                context.ids = context.ids + [ card_id for card_id in card_ids if leechdetector.get_lapse_infos(card_id).is_recovered_leech()]
        print(f"handle_browser_will_search : {context}")
        return context

def handle_browser_did_search(context : aqt.browser.SearchContext):
    pass

gui_hooks.browser_will_search.append(
    handle_browser_will_search
)
gui_hooks.browser_did_search.append(
    handle_browser_did_search
)