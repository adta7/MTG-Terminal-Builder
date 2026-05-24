# Changelog

All notable changes to this project will be documented here.
Format: [Version] — Date — Description

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
