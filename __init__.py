from aqt import gui_hooks, mw
from anki._backend import RustBackend
from anki.collection import Collection

from .leechdetector.hooks import (
    handle_browser_will_search,
    handle_browser_did_search,
)
from .leechdetector.patches import (
    patch_find_cards_for_leech_filters,
    patch_graphs_raw_for_leech_filters,
    is_stats_graphs_patch_enabled,
)

gui_hooks.browser_will_search.append(
    handle_browser_will_search
)
gui_hooks.browser_did_search.append(
    handle_browser_did_search
)

patch_find_cards_for_leech_filters(Collection)

addon_config = {}
try:
    addon_config = mw.addonManager.getConfig(__name__) or {}
except Exception:
    addon_config = {}

if is_stats_graphs_patch_enabled(addon_config):
    patch_graphs_raw_for_leech_filters(RustBackend)
