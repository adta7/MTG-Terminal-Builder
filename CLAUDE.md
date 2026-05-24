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

## Future: Textual Migration

The deck view currently uses `Rich.Live` + raw keyboard input (`tty`/`termios`) for interactivity.

If the app grows to need true mouse support, scrollable lists, clickable buttons, or multi-pane layouts, the right move is to migrate the deck view to **Textual** (https://textual.textualize.io). Textual is built on Rich by the same author and supports full mouse interaction, reactive components, and CSS-like layouts. It's the natural upgrade path.

Do not start this migration without discussing it — it's a meaningful rewrite of the deck view.

---

## Planned Features (do not build until discussed)

- Claude API integration for deck suggestions and card explainer
- Card art display in the art box (user has a specific idea for this)
- Life counter / Commander damage tracker
- Deck stats view (mana curve, color breakdown, type split)
