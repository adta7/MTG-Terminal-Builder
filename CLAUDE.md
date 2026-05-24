# CLAUDE.md — MTG Terminal Builder

## Project Purpose

Build a clean, helpful Magic: The Gathering card management assistant that runs entirely in the terminal.

The goal is a tool that feels good to use — fast, readable, and smart — without needing a browser or GUI. Everything should be keyboard-driven and easy to navigate.

---

## What This Project Is

A Python terminal app that lets you:
- Manage and build MTG decks interactively
- Look up any card and see its data displayed as a real card layout
- Enrich a card collection spreadsheet with full Scryfall data
- (Planned) Get AI-powered deck suggestions using the Claude API

---

## Tech Stack

- **Python 3.8+** — no frameworks, just the standard library + a few packages
- **Rich** — terminal UI, colors, panels, styled output
- **pandas** — spreadsheet reading and data transformation
- **openpyxl** — Excel file reading and writing
- **Scryfall Oracle Cards JSON** — local card database (~165MB bulk file)
- **difflib** — fuzzy card name matching (built-in)

---

## Architecture

Everything lives in `mtg.py`. The structure is:

```
main()                          # Main menu loop
├── run_deck_manager()          # Deck creation, editing, saving
├── run_card_lookup()           # Card search and display
└── run_collection_pipeline()   # Spreadsheet enrichment pipeline
```

**Key patterns:**
- The Scryfall DB is lazy-loaded via `get_scryfall_db()` — only loads when actually needed since the JSON is 165MB
- Decks are saved as JSON files in `decks/` folder
- All user prompts go through `ask()`, `ask_yn()`, or `ask_choice()` — never raw `input()` directly
- The Rich `console` object is global — import it, don't create new instances
- `term_width()` returns the current terminal width — use it instead of hardcoding widths

---

## Code Standards

- Keep functions focused on one job
- Match the existing prompt and flow style before adding new ones
- New features go in as a new menu option — don't bury them in existing flows
- Use `console.print()` with Rich markup for styled output
- Use plain `print()` only inside the card renderer and progress bars where character-level control matters
- Never hardcode terminal widths — always use `term_width()` or cap with `min()`

---

## Card Renderer

The card renderer in `print_card()` draws a real MTG card layout using box-drawing characters:
- Name top-left, mana cost top-right
- Empty art box (reserved for future image feature)
- Type line
- Oracle text with word wrap
- Rarity, set name bottom-left — P/T or loyalty bottom-right

Width is dynamic: `min(term_width() - 2, 72)`

Do not change this layout without discussing it first — the user has a specific idea for the art box.

---

## Deck Storage

Decks are saved as JSON in `decks/`:

```json
{
  "name": "My Deck",
  "created": "2026-05-23",
  "edited": "2026-05-23",
  "cards": [
    { "name": "Lightning Bolt", "count": 4 }
  ]
}
```

Do not change this format without migrating existing deck files.

---

## Card List Import Format

Simple text format, one card per line:

```
4 Lightning Bolt
2 Counterspell
1 Black Lotus
```

Parsed by `parse_card_list()`. A line with no leading number defaults to count 1.

---

## What to Avoid

- Do not load the Scryfall JSON eagerly at startup — it's 165MB and slow
- Do not add external API calls (Scryfall API, Claude API) without discussing it first
- Do not change the deck JSON format without a migration plan
- Do not create new helper abstractions unless they are clearly reused in 3+ places
- Do not add features outside the menu system

---

## Future: Terminal UI Rewrite

The current deck editor uses a plain text menu. Python is not the right tool for interactive terminal UIs — raw mode (`tty`/`termios`) is low-level and fragile, and Rich's `Live` component has threading conflicts with raw input.

**Planned approach:** Rewrite the terminal UI layer in a language built for it, while keeping Python for all backend logic.

UI layer candidates:
- **Go** with `bubbletea` — gold standard for terminal UIs, fast, single binary
- **Rust** with `ratatui` — same strengths, steeper learning curve
- **Node.js** with `ink` — terminal UIs written in React, gentler entry point

Backend stays Python. The split is clean:
- Python handles: Scryfall DB, deck storage, collection pipeline, card lookup, fuzzy matching
- UI layer handles: keyboard navigation, in-place rendering, cursor control

These can be two separate programs, or the Python side can eventually be exposed as a small local API.

Do not start this migration without discussing which language to learn first.

### What We Learned Building the Python Version (use this when you come back)

**Why Rich.Live failed:**
Rich.Live runs a background refresh thread. Our `getch()` function puts the terminal in raw mode while waiting for a keypress. The background thread fires ANSI cursor-repositioning codes while the terminal is in raw mode — they get mangled, the cursor never moves back up, and each render prints as a new panel below the last instead of overwriting it. The root conflict is: Live owns the terminal on one thread, getch owns it on another.

**What actually works in raw terminals:**
1. Hide the cursor at the start: `\x1b[?25l`
2. Set raw mode so keypresses fire instantly without Enter
3. On each keypress: clear the screen and reprint the full UI
4. Restore the cursor when exiting: `\x1b[?25h`

This is exactly what vim, htop, and less do. The clear+reprint approach feels instant because the terminal redraws faster than your eye can catch it, especially with the cursor hidden.

**The ANSI codes worth knowing:**
- `\x1b[?25l` — hide cursor
- `\x1b[?25h` — show cursor
- `\x1b[2J\x1b[H` — clear screen, move cursor to top-left
- `\x1b[?1049h` — switch to alternate screen buffer (what vim uses)
- `\x1b[?1049l` — restore original screen buffer

**How to use this knowledge:**
- In Go/bubbletea or Rust/ratatui — the framework handles all of this for you. You write the layout and key handlers; the library manages raw mode, cursor hiding, and redraws. This is the right level to work at.
- In Node/ink — same, React-style components, framework handles the terminal.
- If you ever build a raw UI from scratch — follow the hide cursor → raw mode → keypress loop → clear+reprint → restore cursor pattern above.
- The Python version we built (`render_deck_view` + `getch()`) already follows this pattern and is a working reference.

---

## Planned Features (do not build until discussed)

- Interactive keyboard-driven deck editor (arrow keys, in-place rendering) — see UI rewrite above
- Claude API integration for deck suggestions and card explainer
- Card art display in the art box (user has a specific idea for this)
- Life counter / Commander damage tracker
- Deck stats view (mana curve, color breakdown, type split)

---

## AI Deckbuilding Companion

This section captures the full design vision for turning this project into a serious terminal-based MTG deckbuilding companion. Do not start building any of this until the current backend is stable. Follow the phases in order.

### Vision

Build a local deckbuilding workstation that helps make better decisions by combining:
- Local card data (Scryfall)
- Commander legality validation
- Decklist parsing
- Collection awareness
- Role tagging
- Deck structure analysis
- Card scoring
- Suggestion and cut logic
- Optional AI explanations on top of validated data

The app should answer:
- Is this deck legal?
- What does this deck actually do?
- Do I have enough lands, ramp, draw, removal, recursion, protection, win conditions, sac outlets, token makers?
- What cards in my collection fit the strategy?
- What cards are powerful but off-plan?
- What should I cut?
- What should I test next?

**Target format: Commander / EDH first.**

---

### Core Philosophy

**Deterministic logic first. AI second.**

Build reliable local systems before touching AI:
1. Card database
2. Deck parser
3. Analyzer
4. Commander legality checker
5. Role counter
6. Scoring system
7. Collection matcher

AI is added later as an explanation layer on top of validated facts. The LLM must never be trusted as the source of truth for card text, legality, deck size, color identity, or ownership.

**Never let the LLM guess card data.** Card text, mana cost, types, color identity, legality, and rulings must come from a trusted local dataset. Cache Scryfall bulk data locally in SQLite — do not call the Scryfall API on every analysis.

---

### Planned Tech Stack

```
Python
Typer or Click — CLI
Rich — terminal output (current)
Textual — full TUI (later, Phase 6)
SQLite — local card/deck/collection database
Pydantic or dataclasses — models
YAML — deck profiles and user preferences
pytest — tests
```

Do not build the Textual TUI immediately. Start with a clean CLI.

---

### Target CLI Commands

Phase 1–5 MVP:

```bash
mtgdeck import collection path/to/collection.csv
mtgdeck import deck path/to/deck.txt --name sheoldred
mtgdeck analyze sheoldred
mtgdeck validate sheoldred
mtgdeck suggest sheoldred --role draw --owned-only
mtgdeck cuts sheoldred --count 5
mtgdeck search "mono black draw under 4 mana"
```

Later (Phase 6+):

```bash
mtgdeck testlog sheoldred
mtgdeck profile sheoldred --profile mono_black_reanimator
mtgdeck explain sheoldred
mtgdeck ai-review sheoldred
```

---

### Planned Project Structure

Adapt this to the existing project — do not blindly replace what already works:

```
mtg-deck-companion/
├── src/
│   └── mtgdeck/
│       ├── __init__.py
│       ├── cli.py          # Thin CLI entry points only
│       ├── database.py     # SQLite connection, tables, migrations
│       ├── scryfall.py     # Bulk data download, normalization, DFC handling
│       ├── parser.py       # Decklist import (plain text, Moxfield, tagged)
│       ├── models.py       # Card, Deck, DeckCard, CollectionEntry, DeckAnalysis, etc.
│       ├── analyzer.py     # Deck stats, role counts, mana curve
│       ├── rules.py        # Commander legality validation (deterministic)
│       ├── tags.py         # YAML role tag loader and lookup
│       ├── scoring.py      # Card scoring against deck needs and preferences
│       ├── recommender.py  # Suggest adds, cuts, swaps
│       ├── collection.py   # Collection CSV import and lookup
│       ├── profiles.py     # YAML deck profile loader
│       ├── testlog.py      # Game outcome tracking (Phase 6)
│       └── tui.py          # Textual TUI (Phase 6)
├── data/
│   ├── cards.sqlite
│   ├── collection.csv
│   └── decks/
├── profiles/
│   ├── commander.yaml
│   └── mono_black_reanimator.yaml
├── tests/
├── README.md
├── CHANGELOG.md
├── CLAUDE.md
├── pyproject.toml
└── .env.example
```

---

### File Responsibilities

**`cli.py`** — Thin only. Calls functions from other modules. No business logic here.

**`models.py`** — Core data structures: `Card`, `DeckCard`, `Deck`, `Commander`, `CollectionEntry`, `DeckAnalysis`, `RoleCount`, `Suggestion`, `ValidationIssue`. Use typed models, not raw dicts.

**`scryfall.py`** — Download bulk data, update local DB, normalize card names, handle double-faced cards, extract mana value, colors, color identity, type line, oracle text, legalities. No deckbuilding logic here.

**`database.py`** — SQLite connection, table creation/migrations, card lookup, deck storage, collection storage, tag storage. Tables: `cards`, `decks`, `deck_cards`, `collection`, `card_tags`, `deck_profiles`, `game_logs`.

**`parser.py`** — Import decklists from common formats. Must handle:
```
1x Animate Dead
1 Animate Dead
1x Animate Dead (soc) [Recursion]
1x Path to Exile (cmm) [Removal] ^To Remove,#FF0000^
# Sideboard / Commander / Maybeboard
```
Extracts: quantity, card name, set code (if present), tags (if present), section (if present). Forgiving but reports unresolved names.

**`rules.py`** — Commander validation (deterministic, tested):
- Deck has a commander
- Exactly 100 cards including commander
- No illegal duplicates (basic lands excepted)
- Cards exist in DB
- Card color identity is within commander color identity
- Card and commander are Commander-legal

**`analyzer.py`** — Computes: total cards, land count, nonland count, average MV, mana curve, type counts, role counts (ramp, draw, removal, board wipes, reanimation, sac outlets, token makers, protection, wincons). Returns a structured `DeckAnalysis` object.

**`tags.py`** — YAML role tag system with strength values. Manual tags take priority over inferred ones. Classify cards by deck function and rate how strong they are in that role (1-10 scale). This helps the scorer understand card quality without hard-coding formulas:
```yaml
Animate Dead:
  roles:
    reanimation: 5      # Brings back 1 creature, tempo-negative, but reliable
    recursion: 7        # Can recur itself with sac outlets
    graveyard_synergy: 6 # Fuels graveyard, but doesn't create synergy on its own

Ashnod's Altar:
  roles:
    ramp: 8             # Converts creatures into colorless mana
    sac_outlet: 10      # Unlimited sac outlet
    combo_piece: 7      # Infinite mana potential with some creatures

Blood Artist:
  roles:
    drain: 8            # Consistent damage with any creature death
    aristocrat: 9       # Payoff that scales with sac engine
    payoff: 8           # Needs creatures to die, but repeatable

Counterspell:
  roles:
    removal: 9          # Instant-speed interaction
    tempo: 10           # Blue's efficient interaction
    cost: 10            # Mana cost 2 is excellent
```

**Strength values inform the scorer:** A 10/10 reanimation effect (Animate Dead is 5) vs. a 10/10 sac outlet (Ashnod's Altar) get different multipliers. This lets the AI explain why Ashnod's Altar is "critical" but Animate Dead is "solid support."

**`profiles.py`** — YAML deck profiles with target ranges. Example:
```yaml
mono_black_reanimator:
  lands: [35, 37]
  ramp: [10, 13]
  draw: [10, 14]
  removal: [8, 11]
  board_wipes: [2, 4]
  reanimation: [9, 14]
  sac_outlets: [5, 8]
  protection: [3, 6]
  graveyard_fill: [5, 9]
  token_makers: [4, 8]
  wincons: [4, 7]
  avg_mana_value: [2.8, 3.8]
```

**`scoring.py`** — Scores how well a card fits the deck. Formula factors:
- Role match strength (uses tags.yaml values — a 10/10 ramp card scores higher than 6/10)
- Fills missing category (weighted by how short we are)
- Synergy with commander
- Synergy with existing tagged cards (cross-checks tag compatibility)
- Low MV bonus (when appropriate)
- Collection ownership bonus
- Supports deck profile (targets from profiles.yaml)
- High MV penalty (when deck is already top-heavy)
- Duplicate role penalty (when category is overfilled)
- Off-strategy penalty
- Preference penalty (see below)

The strength values in tags.yaml let the scorer explain *why* Solemn Simulacrum (ramp 8) beats Wayfarer's Bauble (ramp 6) — not just that both are ramp, but *how much* ramp they provide.

**User preferences — avoid:** stealing opponents' graveyards, early infinite combos, pure combo wins, excessive counterspell/control play.

**User preferences — favor:** sacrifice engines, recursion, reanimation, big black creatures, drain + combat, resilient board states, commander protection, token generation, value engines.

**`recommender.py`** — Suggests cards by missing role, from collection only, or from all cards. Suggests cuts and swaps. Output must include a reason, not just a ranked list:
```
Best owned draw candidates:

1. Morbid Opportunist
   Reason: Low MV, repeatable draw, supports creature death plan.

2. Disciple of Bolas
   Reason: Converts large creatures into cards and life.
```

**`collection.py`** — CSV import (card name, quantity, set code, foil, condition). Recommender can run in owned-only or all-cards mode.

**`testlog.py`** (Phase 6) — Track real game outcomes: land drops, draw sufficiency, removal issues, sac outlets, payoffs, dead cards, overperformers, win/loss, turn became threatening.

---

### Build Phases

**Phase 1 — Static Analyzer** (first priority)

No AI. No TUI. No recommender yet.

- Import decklist
- Look up cards in local Scryfall data
- Count cards, lands, mana curve, card types
- Validate Commander legality
- Print analysis report

Example output:
```
Sheoldred, Whispering One — Mono Black Reanimator

Cards: 100/100
Lands: 35
Average MV: 3.42

Role Counts:
Ramp: 11 / Draw: 8 / Removal: 9 / Board Wipes: 3
Reanimation: 12 / Sac Outlets: 6 / Token Makers: 4
Protection: 3 / Wincons: 5

Warnings:
- Draw is below target.
- High MV cards may be slightly high.
```

CLI: `mtgdeck analyze path/to/deck.txt`

**Phase 2 — Manual Role Tags**

- Load role tags from YAML
- Merge tags with card data
- Show role counts in analysis
- Add command: `mtgdeck untagged sheoldred`

**Phase 3 — Deck Profile Comparison**

- Add YAML profiles
- CLI: `mtgdeck analyze sheoldred --profile mono_black_reanimator`
- Output: short on draw (+2), overloaded on expensive sorceries, etc.

**Phase 4 — Collection-Based Suggestions**

- CLI: `mtgdeck suggest sheoldred --role draw --owned-only`
- Suggestions based on: owned cards, role match, color identity, MV, profile needs, preferences

**Phase 5 — Cut Suggestions**

- CLI: `mtgdeck cuts sheoldred --count 5`
- Cut candidates based on: off-plan, high MV, redundant, low synergy, untagged, preference conflicts
- Present candidates with reasons — never auto-remove

**Phase 6 — Terminal UI**

Only after CLI works. Rich first, Textual later. Possible screens: Deck Dashboard, Mana Curve, Role Breakdown, Card Detail, Suggestion Panel, Cut Candidates, Collection Search, Game Log.

**Phase 7 — Optional AI Layer**

Only after deterministic analysis works. AI explains analysis, summarizes deck identity, explains cuts, turns user goals into profile adjustments. AI must receive validated context only — never raw card lookup.

AI prompt structure:
```
You are an expert MTG deckbuilding assistant.

You may only reason from the validated data provided.
Do not invent card text. Do not suggest cards outside the provided candidate list.
Do not claim a card has an ability unless the card data says so.
Respect Commander legality and the user's preferences.

Deck Analysis: {analysis}
Commander: {commander}
Deck Profile: {profile}
Candidate Cards: {candidate_cards}
User Preferences: {preferences}
User Request: {request}
```

AI output should be validated before display.

---

### Testing Priorities

Write tests for:
- Decklist parsing (plain text, Moxfield style, tagged lines)
- Card name normalization
- Duplicate detection
- Commander deck size (must be 100)
- Color identity legality
- Basic land exception
- Role counting
- Profile comparison (detects low draw, etc.)
- Suggestion scoring
- Cut scoring

---

### Strongest Build Order

```
CLI analyzer → role tags → profile comparison → owned-card suggestions → cut suggestions → TUI → AI layer
```

Do not jump to the AI companion before the deterministic core works. A working analyzer that produces structured facts makes the AI actually useful instead of vague.
