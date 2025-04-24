# Leech Detector

## Introduction
This add-ons aims to offer new ways to understand how your card might not be leeches, based on more criteria than simply looking at lapses count

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

Those flags combines as "OR", meaning the result will be all results merged.

## Contact

### Issues / Feedback

- You can add the issues encountered or your feedback on this project : https://github.com/JSchoreels/anki-addon-leechdetector/issues
- If you don't have a github account, or want to discuss privately about some behaviours, you can contact me on Anki's Discord : @soundjona

## Release Notes :
- 2025/04/24 : Fix Sorting in Browse view when doing `leeches:*` searches