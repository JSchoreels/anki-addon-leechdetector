from aqt import gui_hooks

from .leechdetector.hooks import handle_browser_will_search, handle_browser_did_search

gui_hooks.browser_will_search.append(
    handle_browser_will_search
)
gui_hooks.browser_did_search.append(
    handle_browser_did_search
)