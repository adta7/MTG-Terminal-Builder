# Phase 0: Infrastructure Complete ✓

## What Was Built

Phase 0 establishes the foundation for the AI deckbuilding companion by extracting card data into SQLite and separating business logic from the UI.

### New Modular Architecture

```
src/mtgdeck/
├── __init__.py           # Package definition
├── __main__.py           # Entry point (python -m mtgdeck)
├── models.py             # Typed data structures (Card, Deck, etc.)
├── database.py           # SQLite persistence layer
├── scryfall.py           # Card data sync & normalization
├── parser.py             # Decklist parsing (moved from mtg.py)
└── rules.py              # Commander validation rules
```

### Key Components

| Module | Purpose | Status |
|--------|---------|--------|
| **models.py** | Dataclasses for Card, Deck, DeckCard, DeckAnalysis | ✓ Complete |
| **database.py** | SQLite schema + CRUD operations | ✓ Complete |
| **scryfall.py** | Download/normalize/index card data | ✓ Complete |
| **parser.py** | Supports 6+ decklist formats | ✓ Complete (moved) |
| **rules.py** | Commander legality validation | ✓ Complete |
| **__main__.py** | Setup command + app entry point | ✓ Complete |

## How to Use

### First Time: Initialize the Database

```bash
python -m mtgdeck setup
```

This command:
1. Checks for a local `oracle-cards-*.json` file
2. If not found, downloads the latest from Scryfall (~165MB, ~1 minute)
3. Normalizes card data (handles double-faced cards, etc.)
4. Indexes all cards into `data/cards.sqlite`
5. Prints confirmation when done

The database file is ~50-100MB and will be reused for all future runs.

### Regular Use: Run the App

```bash
python -m mtgdeck
```

This loads the old `mtg.py` UI (which still works unchanged) but now queries the SQLite database instead of the JSON file.

## What Changed (Backward Compatibility)

✓ **Deck manager** — Still works, unchanged
✓ **Card lookup** — Still works, unchanged  
✓ **Collection pipeline** — Still works, unchanged
✓ **Existing decks** — Still load from `decks/` folder as JSON

The old `mtg.py` remains functional. We're building the new architecture *alongside* it, not replacing it yet.

## What's Next: Phase 1

Phase 1 will build the **Static Analyzer**:
- `analyzer.py` — Compute deck stats (mana curve, type distribution, color counts)
- `rules.py` enhancements — Validate Commander legality
- New CLI command: `mtgdeck analyze <deck_name>`

Output will show:
```
Sheoldred, Whispering One
Cards: 100/100
Lands: 35
Mana curve: [4, 7, 11, 15, ...]
Color identity: B
Validation: ✓ Legal Commander deck
```

## Testing

All Phase 0 tests pass:
```bash
python3 -m pytest tests/ -v
```

Currently testing:
- Parser (card list formats)
- Database (card insertion/lookup)
- Models (data structure creation)

## Architecture Rationale

**Why SQLite instead of JSON?**
- One-time conversion from 165MB JSON to optimized database
- Fast queries: "find all blue creatures under 4 mana" → milliseconds
- Enables tagging system (phase 2) and scoring (phase 4-5)
- Persistent storage of user preferences and metadata

**Why separate modules?**
- Testable: each module has clear responsibility
- Reusable: future REST API or web UI can import the same modules
- Maintainable: changes to analyzer don't touch the parser
- Scalable: phases 2-5 add new modules without touching existing ones

## File Structure

```
├── src/mtgdeck/              # New modular code
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── models.py             # ← Start here
│   ├── database.py           # ← Then this
│   ├── scryfall.py
│   ├── parser.py
│   └── rules.py
├── data/
│   ├── cards.sqlite          # Created by `setup`
│   ├── profiles/             # For phase 3
│   ├── tags/                 # For phase 2
│   └── decks/                # Existing JSON decks
├── tests/                    # Unit tests
├── mtg.py                    # Old monolithic app (still works)
├── requirements.txt          # Updated with pytest
├── pyproject.toml            # New: package metadata
└── README.md                 # Update before next phase
```

## Verification Checklist

- [x] All modules import successfully
- [x] Models create typed objects without errors
- [x] Database schema creates correctly
- [x] Parser tests pass (5/5)
- [x] Database tests pass (2/2)
- [x] Old mtg.py still loads
- [x] No regressions to existing functionality

## Next Steps

1. **Before Phase 1:** Update [README.md](../README.md) and [LEARN.md](../LEARN.md) to reflect new architecture
2. **Phase 1 tasks:** 
   - Implement `analyzer.py` with deck statistics
   - Add `analyze` command to CLI
   - Write tests for analyzer
3. **Test Phase 1:** Verify deck analysis output without any decks loaded yet

---

**Phase 0 Status:** ✓ Complete
**Ready for Phase 1:** Yes
**Breaking Changes:** None — all existing functionality preserved
