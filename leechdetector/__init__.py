# import the main window object (mw) from aqt
import json
import logging
import re
from typing import Optional

import aqt
from anki.cards import CardId
from aqt import mw
from aqt.qt import *
from aqt import gui_hooks
from aqt.webview import AnkiWebViewKind
from aqt.browser import Column as BuiltinColumn
from aqt.utils import showWarning # Make sure to import this

from .browse_custom_search import RE_CUSTOMSEARCH

LOCAL_DIR = os.path.dirname(__file__)
from .leech_detector import LeechDetector

from string import Template

# Regex to find 'leeches:type(args)' pattern
# Group 1: type (e.g., 'all', 'active')
# Group 2: args (e.g., 'dropcount=2, dropratio=0.2') - optional
LEECH_SEARCH_RE = re.compile(r"leeches:(\w+)(?:\[(.*?)])?")


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

def parse_leech_args(args_str: Optional[str]) -> dict:
    """Parses the argument string from the leech filter into a dictionary."""
    args = {}
    if not args_str:
        return args
    for part in args_str.split(','):
        part = part.strip()
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip()
            try:
                # Attempt to convert to float or int
                args[key] = float(value) if '.' in value else int(value)
            except ValueError:
                logging.warning(f"Could not parse argument value: {key}={value}")
                args[key] = value # Keep as string if conversion fails
    return args

def handle_browser_will_search(context: aqt.browser.SearchContext):
    """
    Handles custom 'leeches:' search terms, parsing arguments
    and filtering cards based on LeechDetector results.
    """
    original_search = context.search
    search_modified = False
    processed_search_parts = []
    remaining_search_parts = []

    # Split search query respecting quotes potentially
    # A simple split might be sufficient if complex queries aren't combined
    search_parts = original_search.split()

    leech_type = None
    leech_args = {}

    for part in search_parts:
        match = LEECH_SEARCH_RE.fullmatch(part)
        if match:
            leech_type = match.group(1)
            args_str = match.group(2)
            leech_args = parse_leech_args(args_str)
            processed_search_parts.append(part) # Mark this part as processed
            search_modified = True
        else:
            remaining_search_parts.append(part)

    # If no custom leech search term was found, do nothing
    if not search_modified:
        return context

    # Reconstruct the search string without the custom leech term
    search_filtered = " ".join(remaining_search_parts)
    context.search = search_filtered # Update context search

    leechdetector = LeechDetector()

    # Determine the base set of card IDs
    if context.ids is None:
        # If no IDs are present, perform the filtered search
        print(f"Context Order : {context.order}, context.reverse {context.reverse}, type(context.order) {type(context.order)}")
        if context.order.key.startswith("_field"): ## To ensure no crash with AdvancedBrowser addon
            context.order.key = "noteFld"
            showWarning("Sorting by addon columns is not supported with 'leeches:' filters. Sorting will revert to the default 'Sort Field'.")
            print("Look like an addon order")
        base_card_ids = mw.col.find_cards(search_filtered, context.order, context.reverse)
        if base_card_ids is None: # Handle case where find_cards returns None
             base_card_ids = []
    else:
        # If IDs exist (e.g., from previous hooks or tag selection), filter those
        base_card_ids = context.ids

    # Filter the base IDs based on the leech criteria and arguments
    filtered_ids = []
    if leech_type: # Ensure a leech type was actually matched
        for card_id_int in base_card_ids:
            card_id = CardId(card_id_int) # Ensure correct type
            try:
                lapse_infos = leechdetector.get_lapse_infos(card_id)
                # Assumes LeechDetector methods accept **kwargs or specific args
                lapse_infos.configure_leech_detection(**leech_args)
                if leech_type == "all" and lapse_infos.is_leech():
                    filtered_ids.append(card_id)
                elif leech_type == "active" and lapse_infos.is_active_leech():
                    filtered_ids.append(card_id)
                elif leech_type == "recovering" and lapse_infos.is_recovering_leech():
                    filtered_ids.append(card_id)
                elif leech_type == "recovered" and lapse_infos.is_recovered_leech():
                    filtered_ids.append(card_id)
                # Add other leech types as needed
            except Exception as e:
                 logging.error(f"Error processing card {card_id} for leech status: {e}")


    context.ids = filtered_ids # Update context IDs with the filtered list

    # print(f"Leech Filter: Type='{leech_type}', Args={leech_args}") # Debugging
    # print(f"Updated context: search='{context.search}', ids_count={len(context.ids)}") # Debugging

    return context # Return the modified context


def handle_browser_did_search(context : aqt.browser.SearchContext):
    pass
    # print(context.addon_metadata)

gui_hooks.browser_will_search.append(
    handle_browser_will_search
)
gui_hooks.browser_did_search.append(
    handle_browser_did_search
)