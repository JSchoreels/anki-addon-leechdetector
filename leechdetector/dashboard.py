from collections import defaultdict

from anki.utils import ids2str
from aqt import dialogs, mw
from aqt.qt import (
    QAbstractItemView,
    QAction,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    qconnect,
)

STATUS_QUERIES = {
    "active": "leeches:active",
    "recovering": "leeches:recovering",
    "recovered": "leeches:recovered",
}
STATUS_BY_COLUMN = {
    0: "all",
    1: "all",
    2: "active",
    3: "recovering",
    4: "recovered",
}

_dashboard_dialog = None
_dashboard_action = None


def get_status_card_ids(col):
    return {status: list(col.find_cards(query)) for status, query in STATUS_QUERIES.items()}


def get_status_counts(col, status_card_ids=None):
    if status_card_ids is None:
        status_card_ids = get_status_card_ids(col)
    return {
        "all": len(col.find_cards("leeches:all")),
        "active": len(status_card_ids["active"]),
        "recovering": len(status_card_ids["recovering"]),
        "recovered": len(status_card_ids["recovered"]),
    }


def get_counts_by_did_for_cards(col, cids):
    if not cids:
        return []
    return col.db.all(f"select did, count(*) from cards where id in {ids2str(cids)} group by did")


def get_deck_rows(col, status_card_ids, counts_by_did_fn=get_counts_by_did_for_cards):
    by_did = defaultdict(lambda: {"all": 0, "active": 0, "recovering": 0, "recovered": 0})

    for status in ("active", "recovering", "recovered"):
        for did, count in counts_by_did_fn(col, status_card_ids[status]):
            by_did[did][status] += count
            by_did[did]["all"] += count

    rows = []
    for did, counts in by_did.items():
        rows.append({
            "did": did,
            "deck": col.decks.name(did),
            "all": counts["all"],
            "active": counts["active"],
            "recovering": counts["recovering"],
            "recovered": counts["recovered"],
        })

    rows.sort(key=lambda row: (-row["all"], row["deck"].lower()))
    return rows


def get_status_for_column(column):
    return STATUS_BY_COLUMN.get(column, "all")


def build_deck_status_query(deck_name, status):
    escaped_deck_name = str(deck_name).replace("\\", "\\\\").replace('"', '\\"')
    return f'deck:"{escaped_deck_name}" leeches:{status}'


def get_query_for_cell(deck_rows, row, column):
    if row < 0 or row >= len(deck_rows):
        return None
    status = get_status_for_column(column)
    return build_deck_status_query(deck_rows[row]["deck"], status)


class LeechSummaryDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Leech Detector Summary")
        self.resize(640, 500)
        self.deck_rows = []

        root_layout = QVBoxLayout(self)

        self.count_labels = {
            "all": QLabel("-"),
            "active": QLabel("-"),
            "recovering": QLabel("-"),
            "recovered": QLabel("-"),
        }

        summary_grid = QGridLayout()
        summary_grid.addWidget(QLabel("All leeches"), 0, 0)
        summary_grid.addWidget(self.count_labels["all"], 0, 1)
        summary_grid.addWidget(QLabel("Active"), 1, 0)
        summary_grid.addWidget(self.count_labels["active"], 1, 1)
        summary_grid.addWidget(QLabel("Recovering"), 2, 0)
        summary_grid.addWidget(self.count_labels["recovering"], 2, 1)
        summary_grid.addWidget(QLabel("Recovered"), 3, 0)
        summary_grid.addWidget(self.count_labels["recovered"], 3, 1)
        root_layout.addLayout(summary_grid)

        controls_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.refresh_button)
        root_layout.addLayout(controls_layout)

        self.deck_table = QTableWidget(0, 5)
        self.deck_table.setHorizontalHeaderLabels(["Deck", "Leeches", "Active", "Recovering", "Recovered"])
        self.deck_table.horizontalHeader().setStretchLastSection(True)
        self.deck_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        root_layout.addWidget(self.deck_table)

        qconnect(self.refresh_button.clicked, self.refresh_data)
        qconnect(self.deck_table.cellDoubleClicked, self._on_cell_double_clicked)

        self.refresh_data()

    def _on_cell_double_clicked(self, row, column):
        query = get_query_for_cell(self.deck_rows, row, column)
        if not query:
            return
        browser = dialogs.open("Browser", mw)
        if browser:
            browser.search_for(query)

    def refresh_data(self):
        col = mw.col
        status_card_ids = get_status_card_ids(col)
        counts = get_status_counts(col, status_card_ids)

        for key, label in self.count_labels.items():
            label.setText(str(counts[key]))

        rows = get_deck_rows(col, status_card_ids)
        self.deck_rows = rows
        self.deck_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.deck_table.setItem(i, 0, QTableWidgetItem(row["deck"]))
            self.deck_table.setItem(i, 1, QTableWidgetItem(str(row["all"])))
            self.deck_table.setItem(i, 2, QTableWidgetItem(str(row["active"])))
            self.deck_table.setItem(i, 3, QTableWidgetItem(str(row["recovering"])))
            self.deck_table.setItem(i, 4, QTableWidgetItem(str(row["recovered"])))
        self.deck_table.resizeColumnsToContents()


def show_leech_summary_dialog():
    global _dashboard_dialog
    if _dashboard_dialog is None:
        _dashboard_dialog = LeechSummaryDialog(mw)
    else:
        _dashboard_dialog.refresh_data()
    _dashboard_dialog.show()
    _dashboard_dialog.raise_()
    _dashboard_dialog.activateWindow()


def add_tools_menu_entry():
    global _dashboard_action
    if _dashboard_action is not None:
        return
    _dashboard_action = QAction("Leech Detector Summary", mw)
    qconnect(_dashboard_action.triggered, show_leech_summary_dialog)
    mw.form.menuTools.addAction(_dashboard_action)
