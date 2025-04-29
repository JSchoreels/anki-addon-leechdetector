import logging
import re
from typing import Optional

import aqt
from anki.cards import CardId
from aqt.utils import showWarning
from werkzeug.middleware.lint import check_type

from . import LeechDetector

# Regex to find 'leeches:type(args)' pattern
# Group 1: type (e.g., 'all', 'active')
# Group 2: args (e.g., 'dropcount=2, dropratio=0.2') - optional
LEECH_SEARCH_RE = re.compile(r"leeches:(\w+)(?:\[(.*?)])?")


def parse_leech_args(args_str: str) -> dict:
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

    leech_filters = parse_search_for_leech_filters(context.search)

    context.search = re.sub(LEECH_SEARCH_RE, "*", context.search)

    if context.ids is None:
        if len(leech_filters) > 0:
            check_cross_addon_compatibility(context)
            context.ids = aqt.mw.col.find_cards(context.search, context.order, context.reverse)
            context.ids = filter_cards(context.ids, leech_filters)

    return context


def parse_search_for_leech_filters(search):
    leech_filters = {}
    for (leech_type, args_str) in re.findall(LEECH_SEARCH_RE, search):
        leech_filters[leech_type] = parse_leech_args(args_str)
    return leech_filters


def check_cross_addon_compatibility(context):
    print(f"context.order {context.order}")
    if context.order.key.startswith("_field"):  ## To ensure no crash with AdvancedBrowser addon
        context.order.key = "noteFld"
        showWarning(
            "Sorting by addon columns is not supported with 'leeches:' filters. Sorting will revert to the default 'Sort Field'.")


def filter_cards(card_ids, leech_filters):
    leechdetector = LeechDetector()
    filtered_ids = []
    if len(leech_filters) > 0:
        for card_id in card_ids:
            for leech_type, leech_args in leech_filters.items():
                lapse_infos = leechdetector.get_lapse_infos(card_id)
                lapse_infos.configure_leech_detection(**leech_args)
                leech_type_to_predicate = {
                    "all": lapse_infos.is_leech,
                    "active": lapse_infos.is_active_leech,
                    "recovering": lapse_infos.is_recovering_leech,
                    "recovered": lapse_infos.is_recovered_leech
                }
                if leech_type_to_predicate[leech_type]():
                    filtered_ids.append(card_id)
    else:
        filtered_ids = card_ids
    return filtered_ids


def handle_browser_did_search(context : aqt.browser.SearchContext):
    pass
    # print(context.addon_metadata)