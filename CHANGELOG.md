# Changelog

All notable changes to this project will be documented here.
Format: [Version] — Date — Description

---

## [Unreleased] — 2026-05-30

### Added
- `test_getch.py` — debug script for testing keyboard input detection

### Changed
- `ui.py` — consolidated arrow key and ESC detection with optimized 50ms timeout
  - Refined escape sequence handling to support both CSI (`[`) and SS3 (`O`) formats
  - Use explicit file descriptor in `select()` for clarity
  - Reduced continuation byte timeout to 50ms (proven sweet spot via debugging)
- `search_view.py`, `pinned_view.py`, `history_view.py` — unified breadcrumb styling
  - Use `render_view_header()` for consistent plain-text breadcrumb display
  - Import and use `Console` from `rich.console` for Rich markup rendering
  - Consistent status line formatting with `render_status_line()`

### Fixed
- Arrow key navigation in interactive menu — was returning 'UP'/'DOWN' but menu wasn't responding
  - Root cause: First implementation used sys.stdin in select() with unclear timeout logic
  - Fix: Use explicit file descriptor (fd), 50ms timeout for continuation bytes only
  - Verified via detailed logging that escape sequence detection now works correctly
- Screen flicker on menu transitions — removed unnecessary `print()` calls in render loops
- Literal Rich markup appearing in terminal (e.g., `[yellow]text[/yellow]`)
  - Fix: Changed from plain `print()` to `console.print()` for Rich-formatted strings
- Missing imports in `mtg.py` — added missing `clear_screen` to import statements

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
