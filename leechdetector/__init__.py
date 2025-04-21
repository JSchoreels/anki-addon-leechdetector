# import the main window object (mw) from aqt
from typing import List
import os
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

                    let cardidTd = null;
                    
                    rows.forEach(row => {{
                      const th = row.querySelector('th');
                      const td = row.querySelector('td');
                    
                      if (th && td && th.textContent.trim() === 'Card ID') {{
                        cardidTd = td;
                      }}
                    }});
                    
                    if (cardidTd) {{
                      console.log('Found the target <td>:', cardidTd);
                    }}
                    
                    console.log(document.getElementsByClassName('stats-table')[0]);
                    const table = document.getElementsByClassName('stats-table')[0];
                    console.log(table)
                    const tbody = table.querySelector('tbody') || table;
                    console.log(tbody)
                    tbody.insertAdjacentHTML('beforeend', `{table_html}`)
                    
                    const targetCell = document.querySelector('#past_max_intervals');
                    
                    const observer = new MutationObserver(mutations => {{
                      mutations.forEach(mutation => {{
                          console.log("Mutation detected")
                          targetCell.textContent = {(lambda : leechdetector.get_lapse_infos(mw.col.sched.getCard().id).past_max_intervals)()};
                      }});
                    }});
                    
                    observer.observe(cardidTd, {{ characterData: true, subtree: true, childList: true }});
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
