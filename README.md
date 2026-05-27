# MTG Terminal Builder

A personal Magic: The Gathering deckbuilding workstation that runs entirely in the terminal.

## What It Does

- **Deck manager** — create, edit, import, delete, and copy decks interactively
- **Card lookup** — search any card, see it rendered as a real MTG card layout with tags displayed alongside
- **Collection pipeline** — enrich a collection CSV with full Scryfall data
- **Deck analysis** — count lands, mana curve, type breakdown, role distribution
- **Commander validation** — check deck size, color identity legality, banned cards
- **Card tagging** — five-layer mechanical ontology auto-tags cards from oracle text

Everything is keyboard-driven, no browser or GUI needed.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -e .

# 2. Build the card database (one time — indexes ~36k cards from Scryfall JSON)
python -m mtgdeck setup

# 3. Run the app
python -m mtgdeck
```

> The Scryfall bulk JSON (~165MB) must be in the project directory.
> Download it from [scryfall.com/docs/api/bulk-data](https://scryfall.com/docs/api/bulk-data) → "Oracle Cards".

---

## CLI Commands

```bash
python -m mtgdeck                     # Launch interactive app
python -m mtgdeck setup               # Initialize / re-index card database
python -m mtgdeck analyze <deck>      # Analyze a deck and print report
```

---

## Project Structure

```
mtg-pipeline-terminal/
├── src/mtgdeck/
│   ├── __init__.py
│   ├── __main__.py       # CLI entry point
│   ├── models.py         # Typed dataclasses (Card, Deck, DeckCard, DeckAnalysis)
│   ├── database.py       # SQLite layer — cards, decks, tags, synergy edges
│   ├── scryfall.py       # Bulk download, normalization, DB indexing
│   ├── parser.py         # Decklist import (plain text, set codes, inline tags)
│   ├── rules.py          # Commander legality validation
│   ├── analyzer.py       # Deck stats, mana curve, role counts, filter queries
│   └── tags.py           # Five-layer mechanical tagging system
├── data/
│   ├── cards.sqlite      # Scryfall card database (built by setup)
│   └── decks/            # Saved deck JSON files
├── tests/
│   ├── test_analyzer.py
│   ├── test_parser.py
│   ├── test_rules.py
│   └── test_tags.py
├── mtg.py                # Original interactive terminal app (still works)
├── pyproject.toml
├── requirements.txt
├── CHANGELOG.md
├── LEARN.md
└── userPreferences.md    # Personal deckbuilding philosophy
```

---

## Decklist Import Format

```
# Commander
1 Sheoldred, Whispering One

# Lands
1 Cabal Coffers
37 Swamp

# Main deck
1 Ashnod's Altar
1 Animate Dead (ema)            # set code in parens
1 Blood Artist [Aristocrats]    # inline tag
```

One card per line. Leading number optional (defaults to 1). Supports Moxfield paste format.

---

## Card Tagging System

Cards are automatically tagged from oracle text across five layers:

| Layer | Examples |
|---|---|
| Mechanical (what it does) | `Sacrifice_Outlet`, `Death_Trigger`, `Reanimation`, `Evasion`, `Extort` |
| Functional (role in deck) | `Mana_Acceleration`, `Card_Advantage`, `Removal`, `Engine`, `Payoff` |
| Archetype (strategy fit) | `Aristocrats`, `Reanimator`, `Big_Mana`, `Graveyard`, `Tokens` |
| Emotional (strategic identity) | `Engine_Core`, `Apex_Threat`, `Renewable_Fuel`, `Grand_Finisher` |

Tags are displayed in a color-coded column to the right of the card frame during card lookup.

---

## Running Tests

```bash
python -m pytest tests/ -q
```

113 tests covering the parser, analyzer, rules engine, and tag system.

---

## Build Phases

| Phase | Status | What It Does |
|---|---|---|
| 0 — Infrastructure | ✅ Done | Modular architecture, SQLite, card indexing |
| 1 — Static Analyzer | ✅ Done | Deck stats, mana curve, Commander validation |
| 2 — Card Tagging | 🔄 In progress | Five-layer oracle-text auto-tagging (Layer 2 complete) |
| 3 — Deck Profiles | ⬜ Planned | Compare deck against target role distributions |
| 4 — Suggestions | ⬜ Planned | Recommend adds from collection, explain why |
| 5 — Cut Logic | ⬜ Planned | Score and rank cards to cut |
| 6 — AI Layer | ⬜ Planned | LLM explanations on top of validated local data |

---

## Requirements

- Python 3.8+
- `rich`, `pandas`, `openpyxl` (installed via `pip install -e .`)
- Scryfall Oracle Cards JSON (manual download, ~165MB)
