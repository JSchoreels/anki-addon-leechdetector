# Leech Detector

## Introduction

This add-ons aims to offer new ways to understand how your card might not be leeches, based on more criteria than simply
looking at lapses count

## Features

### Card Info VIew

Added new field to see the Leech status of a card and the key metrics allowing to determine if it's a leech or not.

<img src="https://github.com/JSchoreels/anki-addon-leechdetector/blob/main/images/card_info_view.png?raw=true" alt="Card Info View, New Leech Metrics" width="500" />

### Browse View

- You can add to your queries new options to filters leeches :
    - `leeches:all`
    - `leeches:active`
    - `leeches:recovering`
    - `leeches:recovered`
    - `leeches:healthy`

Those flags combines as "OR", meaning the result will be all results merged.

You can also specify custom leech detection threshold, those are valid searches :

- `leeches:active[drop_count=5,drop_ratio=.5]`
- `leeches:active[drop_count=5]`
- `leeches:active[drop_ratio=.5]`
- `leeches:recovered[drop_count=1,drop_ratio=.5] leeches:active[drop_count=5,drop_ratio=.5]`

Note :

- All custom filters are under the hood replaced by `*`, and then only the search is filtered. So,
  `(A leeches:active) OR (B leeches:recovered)` will be equal to
  `(A *) OR (B *) AND (leeches:active OR leeches:recovered`.
  If you want proper evaluation of such queries, you should populate a card field with the leech status and filter on it
  like you would do with any normal card fields.
- If you specify more than once the same type of leeches filter, the last one will have priority. Example
  `leeches:active[drop_count=1] leeches:active[drop_count=2]` the `drop_count=2` will replace the `drop_count=1`

### Stats / Plugins Search

`leeches:*` filters are also supported in Stats screens and plugins doing card searches (for example Search Stats Extended).

- This compatibility patch is enabled by default.
- You can disable it in the addon config in Anki with `"enable_stats_graphs_patch": false`.
- Restart after this change.

### Tools Summary Window

From `Tools`, you can open `Leech Detector Summary` to quickly see:

- Total leeches
- Active / Recovering / Recovered counts
- Per-deck split
- Double-click any deck table cell to open Browser directly on the corresponding search

<img src="https://github.com/JSchoreels/anki-addon-leechdetector/blob/main/images/tools_summary_view.jpg?raw=true" alt="Tools Summary Window, Leech Counts by Deck and Status" width="500" />

## Contact

### Issues / Feedback

- You can add the issues encountered or your feedback on this
  project : https://github.com/JSchoreels/anki-addon-leechdetector/issues
- If you don't have a github account, or want to discuss privately about some behaviours, you can contact me on Anki's
  Discord : @soundjona

## Release Notes :

### Unreleased

- Load Card Info lapse history in the background so it cannot block Anki's UI
  while another collection operation is running.

### 2026/03/04

- Support `leeches:*` in Stats / plugins searches
- Add fallback safety and config toggle (`enable_stats_graphs_patch`)
- Add `leeches:healthy`
- Add `Tools > Leech Detector Summary` window (with by-deck breakdown)

### 2025/04/29

- Add dynamic custom filters

### 2025/04/24

- Fix sorting in Browse view when doing `leeches:*` searches like `leeches:recovered[drop_count=1,drop_ratio=.5] leeches:active[drop_count=5,drop_ratio=.5]`
