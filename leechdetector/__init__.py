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

    filename = os.path.join(LOCAL_DIR, 'leechdetector_table.html')

    with open(filename, 'r') as template_table:
        template = Template(f"{template_table.read()}")
        table_html = template.substitute(lapse_infos.to_dict())
        webview.eval(
            f"""
                function add_lapse_stats(){{
                    const rows = document.querySelectorAll('tr');
                    
                    const table = document.getElementsByClassName('stats-table')[0];
                    const tbody = table.querySelector('tbody') || table;
                    tbody.insertAdjacentHTML('beforeend', `{table_html}`)
                    
                    const targetCell = document.querySelector('#past_max_intervals');
                    
                    let oldHref = window.location.href;
                    const observer = new MutationObserver(mutations => {{
                     if (oldHref != document.location.href) {{
                          oldHref = document.location.href;
                          new_card_id = document.location.href.split('/').pop() || parts.pop(); // Handle trailing slash
                          console.log("Card Change Detected")
                          pycmd("new_card_id:"+new_card_id, (new_past_max_intervals) => targetCell.textContent = new_past_max_intervals.toString())
                      }}
                    }});
                    
                    body = document.querySelector('body');
                    observer.observe(body, {{ childList: true, subtree: true }});
                }}
                script = document.createElement('script')
                script.textContent = `
                    setTimeout(add_lapse_stats, 200);
                `
                document.body.append(script)
            """
        )


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