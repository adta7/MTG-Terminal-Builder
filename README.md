# MTG Pipeline Terminal

An interactive terminal application for browsing Magic: The Gathering cards, building decks, and enriching card collections with Scryfall data.

## Overview

This project is a comprehensive MTG toolkit with:
- **Card Search** — quickly look up any card with interactive navigation
- **Pinned Cards** — save cards to your pinned list for quick reference
- **Search History** — revisit past searches with one keystroke
- **Deck Manager** — create, edit, and organize deck lists
- **Card Lookup** — full card rendering with oracle text and mana costs
- **Collection Enricher** — enrich raw card lists with complete Scryfall data

Everything runs from a single interactive command: `python3 mtg.py`

---

## Quick Start

```bash
# 1. Install dependencies (one time only)
pip install pandas openpyxl

# 2. Run the pipeline
python3 mtg.py
```

The script will walk you through everything interactively.

---

## Requirements

- Python 3.8+
- pandas, openpyxl
- A Scryfall Oracle Cards bulk JSON file (see below)
- A card list in .csv or .xlsx format

### Getting the Scryfall JSON

1. Go to scryfall.com/docs/api/bulk-data
2. Download Oracle Cards
3. Place the .json file in the same folder as mtg.py

---

## File Structure

```
mtg-pipeline-terminal/
├── mtg.py                  # Main script — run this
├── README.md               # This file
├── CHANGELOG.md            # Version history
├── TODO.md                 # Planned features
├── userPreferences.md      # Personal deckbuilding profile
└── oracle-cards-YYYYMMDD.json
```

---

## What It Does

When you run mtg.py, you get an interactive main menu:

```
What would you like to do?
──────────────────────────

> 1  Search Cards
  2  Pinned Cards
  3  Search History
  4  Deck Manager
  5  Card Lookup
  6  Collection Enhancer
  7  Quit
```

### Menu Options

**Search Cards** — Interactive card search with arrow key navigation, pin to your list, and dual-panel preview

**Pinned Cards** — View and manage saved cards, complete with full card previews

**Search History** — Review past searches and re-run them instantly

**Deck Manager** — Create new decks, edit existing ones, import/export card lists, organize by sets

**Card Lookup** — Traditional card lookup with full rendering (mana cost, oracle text, P/T, legalities)

**Collection Enhancer** — The original enrichment pipeline: upload a spreadsheet and enrich it with Scryfall data

### Keyboard Navigation

All views use consistent keyboard controls:
- **↑↓** — navigate lists
- **Enter** — select/confirm
- **1-9** — quick number select (menus)
- **p** — pin/unpin cards (search view)
- **/** — new search (search view)
- **u** — unpin card (pinned view)
- **ESC** or **q** — go back one level
