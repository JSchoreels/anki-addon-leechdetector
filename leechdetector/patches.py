import logging
import re

import aqt
from anki.collection import Collection
from anki.stats_pb2 import GraphsRequest

from .hooks import LEECH_SEARCH_RE, filter_cards_with_detector, parse_search_for_leech_filters
from .leech_detector import LeechDetector


def normalize_search_query(query):
    if isinstance(query, bytes):
        return query.decode("utf-8", errors="replace")
    return str(query)


def find_cards_with_custom_leech_filters(
    query,
    order,
    reverse,
    find_cards_func,
    leechdetector_factory=LeechDetector,
):
    query = normalize_search_query(query)
    leech_filters = parse_search_for_leech_filters(query)
    query_without_leech_filters = re.sub(LEECH_SEARCH_RE, "*", query)
    card_ids = find_cards_func(query_without_leech_filters, order, reverse)
    if len(leech_filters) == 0:
        return card_ids
    return filter_cards_with_detector(card_ids, leech_filters, leechdetector_factory())


def patch_find_cards_for_leech_filters(collection_cls: type[Collection]):
    if getattr(collection_cls, "_leechdetector_find_cards_patched", False):
        return

    if not hasattr(collection_cls, "_leechdetector_original_find_cards"):
        collection_cls._leechdetector_original_find_cards = collection_cls.find_cards

    def _find_cards_with_custom_leech_filters(self, query, order=False, reverse=False):
        original_find_cards = collection_cls._leechdetector_original_find_cards
        return find_cards_with_custom_leech_filters(
            query=query,
            order=order,
            reverse=reverse,
            find_cards_func=lambda q, o, r: original_find_cards(self, q, o, r),
            leechdetector_factory=lambda: LeechDetector(self),
        )

    collection_cls.find_cards = _find_cards_with_custom_leech_filters
    collection_cls._leechdetector_find_cards_patched = True


def is_stats_graphs_patch_enabled(config):
    if not isinstance(config, dict):
        return True
    return bool(config.get("enable_stats_graphs_patch", True))


def patch_graphs_raw_for_leech_filters(backend_cls, col_provider=lambda: aqt.mw.col):
    if getattr(backend_cls, "_leechdetector_graphs_raw_patched", False):
        return

    if not hasattr(backend_cls, "_leechdetector_original_graphs_raw"):
        backend_cls._leechdetector_original_graphs_raw = backend_cls.graphs_raw

    def _graphs_raw_with_custom_leech_filters(self, message):
        original_graphs_raw = backend_cls._leechdetector_original_graphs_raw
        original_message = message
        try:
            request = GraphsRequest()
            request.ParseFromString(message)
            search = normalize_search_query(request.search)
            if re.search(LEECH_SEARCH_RE, search):
                col = col_provider()
                cids = list(col.find_cards(search)) if col else []
                request.search = f"cid:{','.join(str(cid) for cid in cids)}" if cids else "cid:0"
                message = request.SerializeToString()
            return original_graphs_raw(self, message)
        except Exception:
            logging.exception("leechdetector graphs patch failed; falling back to original graphs query")
            return original_graphs_raw(self, original_message)

    backend_cls.graphs_raw = _graphs_raw_with_custom_leech_filters
    backend_cls._leechdetector_graphs_raw_patched = True
