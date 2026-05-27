# Changelog

All notable changes to this project will be documented here.
Format: [Version] — Date — Description

---

## [2.5.0] — 2026-05-26

### Added
- `src/mtgdeck/tags.py` — `X_Spell_Effect` mechanical tag (effects that scale with X mana spent — Exsanguinate, Torment of Hailfire)
- `src/mtgdeck/tags.py` — `FUNCTIONAL_RULES` constant: 80+ inference rules mapping mechanical tag combinations to functional tags
- `src/mtgdeck/tags.py` — `tag_functional_from_rules(card_name, db)` function: derives Layer 3 functional tags from Layer 2 mechanical tags via rule engine; best-confidence deduplication, source="rule_engine"
- `tests/test_tags.py` — 29 new tests across 8 new test classes: pattern gap fixes and functional rule engine verification (142 tests total)

### Changed
- `src/mtgdeck/tags.py` — `Forced_Sacrifice` pattern extended to catch "may sacrifice" (Braids, Archon of Cruelty ETB)
- `src/mtgdeck/tags.py` — `Life_Drain` now also catches compound-clause drain ("and loses 3 life" — Archon of Cruelty)
- `src/mtgdeck/tags.py` — `Life_Gain` now also catches "you gain that much life" (Extort reminder text, drain-spell payback)
- `src/mtgdeck/tags.py` — `Token_Generation` now covers artifact tokens (Treasure, Food, Blood, Clue, Gold, Ichor, Map)
- `src/mtgdeck/tags.py` — `Upkeep_Trigger` now covers "each other player's upkeep" (Braids) and "end step" timing
- `src/mtgdeck/tags.py` — `Discard_Effect` now catches "that player discards" (Braids conditional clause)
- `data/cards.sqlite` — All 75 deck cards re-tagged with updated mechanical patterns; 239 functional tags applied across 75 cards (5 Finishers, 27 Engines, 20 Payoffs, 17 Recursion)

---

## [2.4.0] — 2026-05-26

### Added
- `src/mtgdeck/tags.py` — 9 new mechanical tags: `Evasion`, `Lifelink`, `Deathtouch`, `Looting_Effect`, `Combat_Trigger`, `Search_For_Land`, `Undying_Persist`, `Extort`, `Devotion_Effect`
- `src/mtgdeck/tags.py` — `Permanent_Scaling` tag (scales with permanents on board)
- `src/mtgdeck/tags.py` — Landwalk and "is unblockable" (old oracle) patterns for Evasion tag
- `src/mtgdeck/tags.py` — "you gain life equal to" Life_Gain pattern (catches drain spells)
- `tests/test_tags.py` — 65 new pattern tests; full suite is now 113 tests across 17 test classes

### Changed
- `src/mtgdeck/tags.py` — Mechanical layer expanded from 26 to 35 tags (166 tag-card pairs across 76 cards)
- `data/cards.sqlite` — Re-tagged all cards with expanded pattern set

---

## [2.3.0] — 2026-05-26

### Added
- `src/mtgdeck/tags.py` — New mechanical tags: `Forced_Sacrifice`, `Return_Self_From_Graveyard`, `Repeatable_Token_Generation`, `Upkeep_Trigger`, `Trigger_Doubler`, `Scales_With_Deaths`, `Permanent_Scaling`, `Life_Payment`, `Mass_Reanimate`
- `src/mtgdeck/tags.py` — Pattern fixes: ETB modern oracle wording, targeted removal with color qualifiers, stat-based board wipes, Crypt Ghast mana multiplier, Plaguecrafter discard edge case, Living Death mass reanimation

### Changed
- `mtg.py` — Card frame narrowed from width 72 to 57 to make room for tag column
- `mtg.py` — Tags now displayed in ANSI-colored column to the right of the card frame (cyan=mechanical, green=functional, yellow=archetype, magenta=emotional)
- `mtg.py` — Added blank line between each oracle text ability for readability
- `data/cards.sqlite` — Committed with Stage 2 tag data (95 mechanical, 113 functional, 155 archetype, 60 emotional tags across 76 cards)

### Fixed
- `mtg.py` — Removed separate `print_card_tags()` call; tags now integrated directly into `print_card()`

---

## [2.2.0] — 2026-05-26

### Added
- `src/mtgdeck/tags.py` — Five-layer card ontology system (mechanical → functional → archetype → emotional)
- `src/mtgdeck/tags.py` — 26 mechanical tags auto-tagged from oracle text using regex patterns
- `src/mtgdeck/tags.py` — Tag registry with layer labels and descriptions; idempotent seeding via INSERT OR IGNORE
- `src/mtgdeck/tags.py` — `tag_mechanical()`, `get_card_tags()`, `query_cards_by_tag()`, `tag_count_for_deck()`, synergy edge functions
- `src/mtgdeck/database.py` — `tags`, `card_tags`, `synergy_edges` tables added to schema
- `scripts/tag_deck.py` — Script to apply mechanical tags to all cards in a deck
- `data/cards.sqlite` — Schema updated with tag tables; deck cards tagged
- `tests/test_tags.py` — 48 tests for tag CRUD, auto-tagger, synergy edges, and deck tag counting
- `mtg.py` — Card search results now display tag column alongside card frame

### Changed
- `src/mtgdeck/analyzer.py` — Role counts now pull from tag layer in addition to heuristic analysis

---

## [2.1.0] — 2026-05-26

### Added
- `src/mtgdeck/analyzer.py` — `analyze_deck()`: land count, nonland count, avg mana value, mana curve (0–7+ buckets), type breakdown, color identity
- `src/mtgdeck/analyzer.py` — `filter_deck()`: query syntax support (`type:`, `text:`, `cmc:`, `color:`, `name:`)
- `src/mtgdeck/analyzer.py` — `_matches_cmc()` and `_matches_color()` helpers with operator support (`>=`, `<`, `=`)
- `src/mtgdeck/__main__.py` — `analyze` CLI command: `python -m mtgdeck analyze <deck_name>`
- `src/mtgdeck/rules.py` — Commander deck validation (100 cards, color identity, no illegal duplicates, basic land exception, Commander-legal format check)
- `tests/test_analyzer.py` — Deck analysis and filter tests
- `tests/test_rules.py` — Commander validation tests

### Fixed
- `src/mtgdeck/analyzer.py` — Deck breakdown math and type categorization

---

## [2.0.0] — 2026-05-26

### Added
- `src/mtgdeck/` — New modular Python package with separated concerns
- `src/mtgdeck/models.py` — Typed dataclasses: `Card`, `Deck`, `DeckCard`, `DeckAnalysis`, `CardScore`
- `src/mtgdeck/database.py` — SQLite persistence layer with full CRUD; replaces lazy-loaded 165MB JSON
- `src/mtgdeck/scryfall.py` — Download/normalize/index Scryfall bulk card data into SQLite
- `src/mtgdeck/parser.py` — Decklist import (moved from mtg.py, supports 6+ formats including set codes and inline tags)
- `src/mtgdeck/rules.py` — Commander legality validation skeleton
- `src/mtgdeck/__main__.py` — CLI entry point: `python -m mtgdeck setup` and `python -m mtgdeck`
- `data/cards.sqlite` — SQLite database (36k+ cards indexed from Scryfall)
- `pyproject.toml` — Package metadata and editable install support
- `tests/` — Test infrastructure with pytest

### Changed
- `mtg.py` — Still works unchanged; new modules run in parallel, not replacing it yet
- `requirements.txt` — Added `pytest`

### Notes
- Setup: `pip install -e . && python -m mtgdeck setup` (one-time DB initialization)
- The 165MB Scryfall JSON is indexed into SQLite on first run; subsequent startups query the DB directly

---

## [1.0.0] — 2026-05-04

### Added
- `mtg.py` — unified interactive pipeline replacing the two-script workflow
- Auto-detection of card list from `~/Downloads`
- Auto-detection of Scryfall Oracle JSON from current directory
- Spreadsheet preview with name column confirmation
- Full vs. deckbuilding export mode selection
- Custom output filename with automatic date stamp
- Output saved directly to `~/Downloads`
- End-of-run summary: matched cards, not found, type breakdown, color identity breakdown
- `userPreferences.md` — personal deckbuilding profile and philosophy
- `README.md`, `CHANGELOG.md`, `TODO.md` project documentation

### Changed
- Replaced two-step manual pipeline (`fetch_card_text.py` + `prepare_for_deckbuilding.py`) with single interactive `mtg.py`
- Output filenames now always include date stamp (e.g. `my_deck_20260504.xlsx`)
- Output destination changed from script directory to `~/Downloads`

### Fixed
- `openpyxl` engine now explicitly specified to prevent pandas Excel write errors
- Filename stripping now handles paths without extensions gracefully

---

## [0.2.0] — 2026-05-03

### Added
- Date stamp appended to output filenames in both `fetch_card_text.py` and `prepare_for_deckbuilding.py`
- `os` import added to `fetch_card_text.py` for safer path handling

---

## [0.1.0] — 2026-05-02

### Added
- `fetch_card_text.py` — reads card list, looks up data from local Scryfall bulk JSON, outputs enriched Excel file
- `prepare_for_deckbuilding.py` — takes enriched file and produces clean deckbuilding-focused version
- Support for `.csv` and `.xlsx` input
- Double-faced card (DFC) matching by front face name
- Auto-detection of name column
