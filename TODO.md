# TODO

Planned features and improvements, roughly in priority order.

---

## High Priority

- [ ] **`mtg.py` — build the unified interactive script**
  - Auto-detect card list from ~/Downloads
  - Auto-detect Scryfall JSON from current folder
  - Show spreadsheet preview + name column confirmation
  - Full vs. deckbuilding export choice
  - Custom filename prompt with date stamp
  - Live progress output
  - Summary at end (matched, not found, type breakdown, color breakdown)
  - Save output to ~/Downloads

- [ ] **Scryfall API mode** — optional fallback when no local JSON is present
  - Fetch card data directly from Scryfall API (no file download needed)
  - Respect Scryfall rate limit (max 10 req/sec)
  - Display download link if user prefers the JSON approach

---

## Medium Priority

- [ ] **Strength-rated role tags** — extend role tagging system to include 1-10 strength values (e.g., `reanimation: 5`, `sac_outlet: 10`). This helps the scorer understand card quality and lets explanations say "critical sac outlet" vs. "situational recursion"
- [ ] **Duplicate detection** — warn if the same card name appears multiple times in the input
- [ ] **Not-found suggestions** — for unmatched cards, suggest the closest Scryfall match by name (fuzzy match)
- [ ] **Multi-JSON support** — if multiple oracle JSON files are in the folder, show a picker with file dates
- [ ] **Commander legal filter** — quick mode to show only Commander-legal cards from the collection
- [ ] **Color identity filter** — filter cards by color identity when building a specific deck

---

## Lower Priority / Ideas

- [ ] **Web UI integration** — connect `mtg.py` logic to the Flask web app (app.py) in the other pipeline folder
- [ ] **Claude-powered deck suggestions** — pipe enriched collection into Claude API to suggest a 99-card deck
  - Would use the Anthropic API
  - Reference userPreferences.md for deckbuilding philosophy
- [ ] **Witherbloom mode** — dedicated export filtered to Witherbloom-relevant cards (GB color identity)
- [ ] **Price tracking** — optionally pull current market prices from Scryfall card data
- [ ] **Shopping list export** — given a target decklist, output which cards you own vs. still need to buy
- [ ] **Condition-aware deduplication** — when you own multiple copies, flag which are best condition

---

## Completed

- [x] Date stamp on output filenames
- [x] Fix openpyxl engine error on to_excel()
- [x] Safer base filename handling (no extension edge cases)
- [x] fetch_card_text.py — initial build
- [x] prepare_for_deckbuilding.py — initial build

---

## Big Picture / App Ideas

- [ ] **Turn this into a full app (mobile or desktop)**
  - Package the pipeline into a proper GUI app — no terminal required
  - Could be a Mac app (using PyQt or Tauri) or a mobile app
  - Would include all pipeline features in a clean point-and-click interface

- [ ] **Life counter**
  - Multi-player Commander life tracker (supports 4 players)
  - Tracks commander damage separately per player
  - Poison/infect counter support
  - History log so you can see how the game unfolded
  - Could live as a tab inside the future app

- [ ] **Card scan feature — "Quirks & Gotchas" explainer**
  - Scan or search a card by name
  - Claude analyzes the oracle text and surfaces:
    - Non-obvious rules interactions (e.g. "dies" vs. "is put into a graveyard")
    - Timing quirks (when abilities trigger, stack interactions)
    - Common misplays and how to avoid them
    - Political/strategic notes — when to use it, when to hold it
    - Synergies with cards in your known collection
  - Powered by Claude API + Scryfall oracle text
  - Especially useful for complex cards like Sheoldred, Yawgmoth, Bolas's Citadel