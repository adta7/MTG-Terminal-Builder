# TODO

Planned features and improvements, roughly in priority order.

---

## Tagging System — Layer 5 Emotional Rule Engine

Layer 5 emotional tags are registered in the DB and ~60 pairs were manually assigned in Stage 2.
Unlike Layers 3 and 4 (which derive from mechanical tags), Layer 5 derives from **functional + archetype tags** combined — making it the most interpretive layer.

**What it is:**
A `tag_emotional_from_rules()` function in `tags.py` that fires at lower confidence (0.60–0.75) using
functional + archetype tag combinations as inputs. Manual tags at 1.0 always win via `tag_card_if_higher()`.

**Rule sketches (functional → emotional):**
- `Engine` + archetype `Aristocrats` or `Big_Mana`     → `Engine_Core` (0.75)
- `Fuel` + `Return_Self_From_Graveyard` (mechanical)   → `Renewable_Fuel` (0.75)
- `Fuel` + archetype `Aristocrats`                     → `Renewable_Fuel` (0.70)
- `Finisher` + archetype `Reanimator`                  → `Apex_Threat` (0.75)
- `Conversion`                                         → `Conversion_Piece` (0.80)
- `Payoff` + archetype `Aristocrats`                   → `Pressure_Piece` (0.75)
- `Return_Self_From_Graveyard` (mechanical)            → `Resilience_Piece` (0.75)
- `Undying_Persist` (mechanical)                       → `Resilience_Piece` (0.70)
- `Finisher` (high confidence)                         → `Grand_Finisher` (0.70)
- `Mana_Engine` + archetype `Big_Mana`                → `Momentum_Spike` (0.70)
- `Recursion` + archetype `Reanimator`                 → `Comeback_Card` (0.70)
- `Finisher` + `Table_Threat` (skip — Table_Threat is meta-dependent, stay manual)
- `Identity_Card` — always manual (too deck-specific to infer)

**Key constraint:** Tags like `Identity_Card` and `Table_Threat` should stay manual-only.
They depend on deck identity and meta context that no rule can reliably capture.

**Files to create / modify:**
- `src/mtgdeck/tags.py` — add `EMOTIONAL_RULES` constant + `tag_emotional_from_rules()`
- `tests/test_tags.py` — 10-15 new tests: rule fires correctly, manual not downgraded, no false positives on generic staples

**Do not build until Phase 3 (profiles) is complete** — emotional tags feed into Phase 4-5 scoring,
not into profile comparison. Build this right before scoring needs it.

---

## Tagging System — Workflow Improvements

These three tools make the tagging system easier to grow over time.
Build them in order — each one builds on the previous.

---

### 1. Oracle Scanner — Discover new pattern candidates

**Problem:** We have 35+ mechanical patterns but only tagged 75 deck cards by hand.
We don't know what we're missing across the full 36k-card oracle base — or even just black cards.

**What it does:**
- Query all black (or black/colorless) cards from `cards.sqlite`
- Run every card through `tag_mechanical()` against an in-memory DB
- Collect cards with zero mechanical tags → these are the gaps
- Group untagged cards by oracle text patterns (keyword frequency, repeated phrases)
- Print a report: top 20 unmatched cards + top 10 repeated phrases not covered by any current pattern

**Why start with black:**
Your deck is mono-black. Scanning all 36k cards at once would produce noise from blue counterspells, red burn, green ramp, etc. Scanning only black surfaces the gaps you actually care about first.

**CLI command idea:**
```bash
python -m mtgdeck scan-oracle --color b --min-cmc 0 --untagged-only
```

**Output example:**
```
Cards with zero mechanical tags (black, showing top 20):
  Nightmare Shepherd   — "If a nontoken creature you control would die..."
  Archghoul of Thraben — "Whenever Archghoul or another Zombie dies..."
  ...

Repeated phrases not covered by any pattern (top 10):
  "put a +1/+1 counter on"   — appears in 47 untagged black cards
  "venture into the dungeon"  — appears in 12 untagged black cards
  ...
```

**Files to create:**
- `src/mtgdeck/scanner.py` — oracle scanning and phrase clustering
- `tests/test_scanner.py` — verify scan returns results, no crashes on empty DB
- Add `scan-oracle` subcommand to `src/mtgdeck/__main__.py`

---

### 2. New Card Onboarding — Interactive check when adding an untagged card

**Problem:** When you import a new deck or add a card mid-session, the card goes in with zero
tags unless you manually run the tagger. There's no prompt or signal that tags are missing.

**What it does:**
- After deck import, compare all card names against `card_tags` table
- For cards with zero mechanical tags OR zero functional tags, surface them one at a time
- Show: card name, oracle text, what tags fired automatically
- Ask: "Does this look right? (y) Accept / (a) Add manual tag / (s) Skip"
- If user adds a tag: show the available tags by layer, let them pick one, write to DB with `source="manual"` and `confidence=1.0`
- At end: summarize how many were auto-tagged, how many needed manual intervention

**Key constraint:** Do not block the import flow. This should be optional — run it after
a successful import with `--onboard` flag, or as its own `mtgdeck onboard <deck>` command.

**CLI command idea:**
```bash
python -m mtgdeck onboard sheoldred           # check existing deck
python -m mtgdeck import deck.txt --onboard   # check immediately after import
```

**Files to create / modify:**
- `src/mtgdeck/onboard.py` — the interactive onboarding loop
- Modify `src/mtgdeck/__main__.py` — add `onboard` subcommand and `--onboard` flag on import

---

### 3. New Tag Wizard — Guided flow for adding a new tag across all layers

**Problem:** Adding a new mechanical tag requires touching 4 separate places:
1. TAGS registry (name, layer, description)
2. `_MECHANICAL_PATTERNS` (1+ regex patterns with confidence values)
3. `FUNCTIONAL_RULES` (which functional tags should derive from this new tag?)
4. Tests (positive match, negative match)

...then re-running the tagger on all existing cards to pick up the new pattern.

**What it does:**
- `python -m mtgdeck tag new` launches an interactive wizard
- Asks: tag name → layer → description
- Asks: "Enter a regex pattern for this tag (leave blank to skip)"
  - Tests the pattern live against a sample of oracle texts from the DB
  - Shows matches: "This pattern matches 47 cards — show them? (y/n)"
  - Asks for confidence value
  - Repeats until user is satisfied or opts out
- Asks: "Which functional tags should derive from this mechanical tag?" (shows list)
  - For each selected functional tag: enter confidence (or use default 0.75)
  - Adds rules to `FUNCTIONAL_RULES`
- Writes updated TAGS entry and patterns to `tags.py` — or prints the code to paste in manually
- Automatically re-tags all existing DB cards with the new pattern
- Automatically re-runs `tag_functional_from_rules` on affected cards

**Two output modes:**
- `--dry-run` — prints the code to add, doesn't touch any files (safe to inspect first)
- `--apply` — writes directly to `tags.py` and re-tags the DB

**Note on auto-editing `tags.py`:**
Auto-editing Python source is fragile. The dry-run mode (print the snippet, paste it in yourself)
is the right default. Only invest in `--apply` mode if you're adding tags frequently enough
to make manual copy-paste annoying.

**Files to create:**
- `src/mtgdeck/tag_wizard.py` — interactive wizard logic
- Add `tag new` subcommand to `src/mtgdeck/__main__.py`

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

## Research / Future Sessions

- [ ] **BigQuery tag comparison experiment** — In a separate session: load the oracle text dataset into
  Google BigQuery and use its SQL-based ML tooling to auto-generate card tags. Then compare BigQuery's
  output against our hand-tuned rule engine (Layers 2-4) card by card.
  - Questions to answer: Does BigQuery surface mechanical patterns our regex missed? Does it
    over-tag? Does it agree on high-confidence cards like Ashnod's Altar?
  - Long-term angle: BigQuery results could feed into the confidence system as a second source
    (e.g. if BigQuery + rule engine both agree → confidence 0.95, if only one fires → 0.70)
  - Could also reveal whether the five-layer ontology maps cleanly to how ML clustering naturally
    groups oracle text, or whether the layers need reshaping
  - **Do not start until Phase 3 and 4 are complete** — need a stable baseline to compare against

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