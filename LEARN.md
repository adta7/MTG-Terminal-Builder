# LEARN.md — MTG Terminal Builder

Personal lessons, discoveries, and notes from building this project.

---

## 2026-05-23

### What We Built
Started from a basic collection enrichment script and turned it into a full interactive terminal app with a main menu, deck manager, card lookup, and a card renderer that looks like a real MTG card.

---

### Git Basics

**`git commit` vs `git push` are two separate steps.**
- `git commit` saves a snapshot of your changes locally on your machine
- `git push` sends those commits up to GitHub

You can commit many times before ever pushing. Committing locally is safe and cheap — it doesn't affect anything on GitHub until you push.

**Starting a new git repo from scratch:**
```bash
git init
git add <files>
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/REPO.git
git branch -M main
git push -u origin main
```

**If `git remote add origin` fails with "remote origin already exists":**
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/REPO.git
```

**If you're already in the project folder, don't `cd` into it again.** `cd: no such file or directory` means you're already there.

---

### Python: Auto-Installing Dependencies

Instead of making users run `pip install` manually, you can check and install packages at the top of the script:

```python
import sys
import subprocess

def ensure_dependencies():
    required = {"pandas": "pandas", "openpyxl": "openpyxl", "rich": "rich"}
    missing = []
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    if missing:
        print(f"Installing: {', '.join(missing)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + missing)

ensure_dependencies()

# Now safe to import
import pandas as pd
from rich.console import Console
```

**Key points:**
- Must run `ensure_dependencies()` before any imports that might fail
- Use `sys.executable` instead of hardcoding `"python3"` — it always points to the correct Python
- The `-q` flag keeps pip output quiet

---

### What pandas and openpyxl Actually Do

- **pandas** — reads and transforms tabular data (CSV, Excel). Does the heavy lifting of merging card data.
- **openpyxl** — the engine pandas uses to read and write `.xlsx` files. You don't call it directly — pandas uses it under the hood.

---

### Terminal Width: Never Hardcode It

Instead of `WIDTH = 60`, always read the actual terminal size at runtime:

```python
import shutil

def term_width():
    return shutil.get_terminal_size().columns
```

Then use it with a cap so things don't get absurdly wide on large monitors:
```python
WIDTH = min(term_width() - 2, 72)
```

This way the card and UI adapt automatically when you resize the window.

---

### Building a Card Layout with Box-Drawing Characters

MTG card renderer uses Unicode box-drawing characters to simulate a real card:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Card Name                                                  {2}{B}{B} │
├──────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │                         (art box)                                │ │
│ └──────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ Legendary Creature — Phyrexian Praetor                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Oracle text wraps here cleanly.                                     │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│ Mythic • Dominaria United                                        4/5 │
└──────────────────────────────────────────────────────────────────────┘
```

**The width math:**
- `WIDTH` = total card width (e.g. 72)
- `INNER = WIDTH - 2` = content between the `│` borders
- `TEXT_W = INNER - 2` = usable text (1 space padding each side)
- Image box inner = `INNER - 4` (border + space on each side)

**Word wrapping inside the card:**
```python
import textwrap
for line in textwrap.wrap(oracle_text, width=TEXT_W):
    print(f"│ {line:<{TEXT_W}} │")
```

---

### Lazy Loading Large Files

The Scryfall JSON is ~165MB. Loading it takes a few seconds. Don't load it at startup — load it only when a feature actually needs it:

```python
_scryfall_db = None

def get_scryfall_db():
    global _scryfall_db
    if _scryfall_db is None:
        json_path = find_scryfall_json()
        _scryfall_db = load_scryfall_db(json_path)
    return _scryfall_db
```

Once loaded, it stays in memory for the session. Subsequent calls return instantly.

---

### Fuzzy Card Name Matching

`difflib` is built into Python and handles typos or slightly wrong card names:

```python
import difflib

close = difflib.get_close_matches(name.lower(), db_keys, n=3, cutoff=0.6)
```

- `n=3` — return up to 3 suggestions
- `cutoff=0.6` — similarity threshold (0.0 = anything, 1.0 = exact only)
- Lower cutoff = more suggestions, possibly less accurate

Used in both Card Lookup and the Collection Pipeline.

---

### Clipboard on Mac

To copy text to the clipboard from Python on macOS:

```python
import subprocess

def copy_to_clipboard(text):
    subprocess.run("pbcopy", input=text.encode(), check=True)
```

`pbcopy` is a built-in Mac command. On Linux you'd use `xclip` or `xsel` instead.

---

### Compound Input Shortcuts in a Menu

Instead of a separate "actions" menu, you can let the user type a compound input:
- `1` → open deck 1
- `12` → copy deck 1 to clipboard
- `10` → delete deck 1

Parse it like this:
```python
if val.endswith("2") and len(val) > 1:
    deck_num = int(val[:-1])
    action = "copy"
elif val.endswith("0") and len(val) > 1:
    deck_num = int(val[:-1])
    action = "delete"
else:
    deck_num = int(val)
    action = "open"
```

This is a power-user shortcut that keeps the UI clean — casual users just type a number, fast users use compound inputs.

---

### Rich Library — Key Things We Used

**Setup:**
```python
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()
```

**Styled output:**
```python
console.print("[bold cyan]Section Header[/bold cyan]")
console.print("[dim]Muted text[/dim]")
console.print("[bold yellow]Important[/bold yellow]")
```

**Panel (bordered box):**
```python
console.print(Panel(
    "[bold yellow]MTG Terminal Builder[/bold yellow]",
    style="bold cyan",
    box=box.DOUBLE,
    expand=False,
    padding=(0, 4),
))
```

**`expand=False`** — fits the panel to content width instead of stretching to the full terminal.

**Box styles:** `box.SIMPLE`, `box.ROUNDED`, `box.DOUBLE`, `box.HEAVY`, `box.MINIMAL`

**Markup closes with `[/]` or the full tag:**
```python
console.print("[bold red]Error[/bold red]")
console.print("[bold red]Error[/]")  # same thing
```

---

### Project Structure Checklist

When starting a project, these files should exist from day one:

| File | Purpose |
|------|---------|
| `README.md` | What the project is and how to run it |
| `CLAUDE.md` | Instructions for Claude Code specific to this project |
| `CHANGELOG.md` | Running log of what changed and when |
| `LEARN.md` | Personal lessons learned while building |
| `.gitignore` | What Git should not track |
| `requirements.txt` | Python package list |
| `.env.example` | Environment variable names (if any secrets are used) |

Missing these early makes the project harder to understand later and harder to share.

---

### Architecture Decision: Menu-First

Every feature is a menu option. Nothing is buried inside another feature's flow.

This keeps the app easy to navigate and easy to extend — adding a new feature means adding a new menu option and a new function. It doesn't require touching existing code.

---

## 2026-05-24

### Raw Terminal Mode and ESC Detection

Terminals run in two modes:

- **Cooked mode** (normal) — the OS buffers input line-by-line. `input()` lives here. The user types, edits, and presses ENTER before your code sees anything. ESC is just a character in the buffer — you can't intercept it mid-line.
- **Raw mode** — every keypress arrives immediately, one byte at a time. No line buffering, no echo, no special key processing. This is how vim, htop, and less work.

To enter raw mode in Python:

```python
import tty, termios, sys

fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)   # save current settings
try:
    tty.setraw(fd)
    ch = sys.stdin.buffer.read(1)  # single byte, no ENTER needed
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old)  # ALWAYS restore
```

**Always restore in a `finally` block.** If your code crashes while in raw mode, the terminal stays broken — the user can't see what they're typing. `finally` runs even on exceptions.

---

### ESC Key Detection: The Timeout Problem

The ESC key sends `\x1b` to the terminal. Arrow keys also start with `\x1b`, followed by `[A`, `[B`, `[C`, `[D`. The problem: you can't tell if `\x1b` is a bare ESC or the start of an arrow key until you check what comes next.

**The wrong approach** (original code):
```python
if ch == b'\x1b':
    ch2 = sys.stdin.buffer.read(1)   # BLOCKS if nothing follows
    ch3 = sys.stdin.buffer.read(1)   # Same
```
If the user presses bare ESC, this blocks waiting for bytes that never arrive. The terminal freezes.

**The right approach** — use `select.select` with a 50ms timeout:
```python
import select

if ch == b'\x1b':
    if select.select([sys.stdin], [], [], 0.05)[0]:  # wait 50ms
        ch2 = sys.stdin.buffer.read(1)
        if ch2 == b'[' and select.select([sys.stdin], [], [], 0.05)[0]:
            ch3 = sys.stdin.buffer.read(1)
            if ch3 == b'A': return 'UP'
            if ch3 == b'B': return 'DOWN'
    return 'ESC'   # nothing followed within 50ms — it's a bare ESC
```

`select.select([stdin], [], [], timeout)` returns immediately if bytes are available, or after `timeout` seconds if not. 50ms is long enough for arrow-key sequences (they arrive nearly simultaneously) but short enough to feel instant to the user.

---

### The `_ESCAPE` Sentinel Pattern

When a function can return either a value or "the user cancelled", you need a way to distinguish "user pressed ENTER with nothing typed" from "user pressed ESC". Using `None` for both is ambiguous.

Solution: use a sentinel object — a unique value that means exactly one thing:

```python
_ESCAPE = object()   # module-level singleton
```

`object()` creates a new object with a unique identity. Nothing else in the program will ever `is _ESCAPE` unless it's this exact object. Callers check with `is`:

```python
val = ask_escapable("Enter a name")
if val is _ESCAPE:
    return   # user cancelled — go back
if not val:
    ...      # user pressed ENTER with nothing — different behavior
```

This pattern works for any "cancel" signal. It's cleaner than exceptions for local control flow and clearer than `None` when `None` is a valid value.

---

### `\r\n` vs `\n` in Raw Mode

In normal (cooked) mode, the terminal converts `\n` to `\r\n` for you — the cursor moves down AND returns to column 0. In raw mode, that conversion is disabled. `\n` moves the cursor down but NOT left, so every subsequent line starts further right.

**Symptom:** output looks like a staircase after raw-mode input.

**Fix:** always write `\r\n` in raw mode:
```python
sys.stdout.write('\r\n')   # in raw mode — correct
sys.stdout.write('\n')     # in raw mode — cursor stays in wrong column
```

Also applies to Ctrl+C handlers: if you `print()` inside a `KeyboardInterrupt` handler while still in raw mode, the newline misbehaves. Restore the terminal first, then print:
```python
except KeyboardInterrupt:
    termios.tcsetattr(fd, termios.TCSADRAIN, old)  # restore FIRST
    sys.stdout.write('\r\n\r\nAborted.\r\n')
    sys.exit(0)
```

---

### Multi-Byte UTF-8 in Raw Mode

ASCII characters are one byte. Accented characters (like `û` in *Lim-Dûl's Vault*) are 2–4 bytes in UTF-8. In raw mode, reading one byte at a time breaks multi-byte characters — each byte decoded alone raises `UnicodeDecodeError` and gets silently dropped.

The first byte tells you how many bytes follow:
- `0xxxxxxx` — 1 byte (plain ASCII)
- `110xxxxx` — 2-byte sequence (need 1 more)
- `1110xxxx` — 3-byte sequence (need 2 more)
- `11110xxx` — 4-byte sequence (need 3 more)

Fix — read continuation bytes before decoding:
```python
first = ch[0]
if   first & 0xF8 == 0xF0: extra = 3
elif first & 0xF0 == 0xE0: extra = 2
elif first & 0xE0 == 0xC0: extra = 1
else:                       extra = 0

for _ in range(extra):
    if select.select([sys.stdin], [], [], 0.02)[0]:
        ch += sys.stdin.buffer.read(1)

c = ch.decode('utf-8')
```

---

### Extracting a Shared Raw-Input Helper

When multiple prompts all need the same raw-mode behavior (ESC detection, backspace, UTF-8, `\r\n`), don't copy the logic into each one. Extract a single `_read_raw_line(prompt)` helper:

```python
def _read_raw_line(prompt):
    """Writes prompt, reads a line in raw mode. Returns _ESCAPE on ESC."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    # ... raw mode loop ...
    # Returns _ESCAPE or the raw string
```

Then build higher-level helpers on top of it:
```python
def ask_escapable(prompt, default=None):
    result = _read_raw_line(f"  {prompt}: ")
    if result is _ESCAPE: return _ESCAPE
    val = result.strip()
    return val if val else default

def ask_yn(prompt, default="y"):
    result = _read_raw_line(f"  {prompt} (Y/n): ")
    if result is _ESCAPE: return None
    ...

def ask_choice(prompt, options, ...):
    result = _read_raw_line("  Choice: ")
    if result is _ESCAPE: return None
    ...

# _collect_lines (card list paste) also uses _read_raw_line("  > ")
```

**The rule:** if two prompts share behavior, extract it. Three is definitely time to extract.

---

### Designing ESC Navigation

ESC should do something consistent at every level. Design it like a stack:

| Level | ESC does |
|---|---|
| Deck editor main menu | Save prompt → return to deck list |
| Deck editor sub-action (D, M, F) | Cancel action → back to deck view |
| Card paste session (A, B) | Cancel paste → back to deck editor |
| Card lookup | Exit → main menu |
| Pipeline wizard step | Cancel pipeline → main menu |
| Pick deck list | Back → main menu |

The key insight: **ESC means "go back one level."** It's not "quit the app" (that's Ctrl+C) and it's not "confirm" (that's ENTER). Every prompt in the app should have a clear answer to "what does ESC do here?"

---

### Mistakes / Fixes

**Problem:** `ask()` uses `input()`. ESC pressed during `input()` doesn't interrupt — the escape character (`\x1b`) is buffered and returned as part of the string when ENTER is pressed. This means pressing ESC while entering a deck name would embed `\x1b` into the filename.
**Fix:** Replace `ask()` with `ask_escapable()` anywhere the user might want to cancel.

**Problem:** `validate_card_list()` and `_check_card_list_against_db()` used `ask()` for fuzzy match selection. Pressing ESC at those prompts typed raw `^[^[` escape bytes into the input.
**Fix:** `ask_escapable()` at every interactive sub-prompt.

**Problem:** `getch()` read two bytes unconditionally after seeing `\x1b`. Pressing bare ESC froze the terminal waiting for bytes that never arrived.
**Fix:** `select.select` with 50ms timeout before reading follow-up bytes.

**Problem:** The `ask_choice()` "cancel" mechanism was `[0]` typed as text because `input()` can't detect ESC. This was inconsistent with all other prompts using ESC.
**Fix:** Migrate `ask_choice()` to `_read_raw_line()` — ESC now works there too, and the `[0] Cancel` display is gone.

---

### Testing Terminal Apps

Pure logic functions (parsers, filters, data transformers) can be unit tested normally with `python3 -c` or a test script — import the module, call the functions, check results.

Interactive functions (anything using `input()`, `getch()`, `tty.setraw()`) can't be easily automated. Test them manually or with careful code review:

1. Read every call site that handles user input
2. Trace every return path (ENTER, ESC, valid input, invalid input, empty input)
3. Check that no path leaves the terminal in raw mode
4. Check that no path embeds control characters into data

`python3 -m py_compile script.py` catches syntax errors. Beyond that, a focused code read of the input paths beats writing fragile test harnesses for terminal UIs.

---

### Small Advice

- `git commit` is cheap. Commit often so you always have a safe point to go back to.
- `git push` is when you decide to share. Keep those moments deliberate.
- A 165MB JSON file loaded once per session is fine. Loaded on every search would be a problem.
- The terminal width is not fixed. Always read it at render time, not at startup.
- `pbcopy` only works on Mac. If you ever share this across platforms, you'll need to detect the OS.
- `difflib.get_close_matches` is surprisingly good for card name typos and handles things like "Lighthing Bolt" → "Lightning Bolt" correctly.

---

## 2026-05-26

### Phase 0: Modular Architecture Complete

Built a modular architecture by extracting business logic into separate modules (models, database, parser, rules, scryfall).

**Why this matters:** Single 1689-line mtg.py is hard to extend. Separate modules let us add features (phases 1-5) without touching existing code.

**What was built:**
- `src/mtgdeck/` — 7 core modules with typed dataclasses
- SQLite persistence layer (replaces lazy-loaded 165MB JSON)
- Parser moved from mtg.py (no logic changes)
- Rules engine for Commander validation
- 5 tests, all passing

**Backward compatibility:** mtg.py still works unchanged. Users don't see a difference except the app is faster.

### Scryfall Download Issue

Attempted automatic download from Scryfall but the URL failed (404).

**Problem:** The direct URL `https://data.scryfall.io/oracle-cards/oracle-cards.json` returns 404.

**Current solution:** Manual download from https://scryfall.com/docs/api/bulk-data (select "Default Cards" JSON).

**Must-fix:** Implement automatic download before Phase 1. This is a UX requirement — users should not need manual steps.

**Why it matters:** `pip install -e .` was also a missing step. The more manual steps, the worse the experience. Setup should be: run one command, wait 1-2 minutes, done.

### Design Pattern: Parallel Architecture

Instead of refactoring mtg.py (risky, breaks things), we built a parallel structure:
- Keep mtg.py as-is
- Build new modules in src/mtgdeck/
- New features extend the modules, not mtg.py
- Phases 1-5 gradually deprecate mtg.py (no rush)

This is like building scaffolding around a building while it's operating. Safe, reversible, allows gradual migration.

### Dataclasses Over Dicts

Using `@dataclass` instead of dicts:
```python
# Old way (error-prone)
card = {"name": "...", "cmc": 3}
if card.get("cmc"):  # Typo? Dict doesn't complain

# New way (type-safe)
card = Card(name="...", cmc=3)
card.cmc  # IDE knows this exists, catches typos
```

Dataclasses enable IDE autocomplete, type checking, and catch bugs early.

### Python Package Installation

`pip install -e .` (editable mode) with pyproject.toml is the modern Python way:
- Tells pip where your package is
- Creates symlink to source (changes reflect immediately)
- `python -m mtgdeck` works because Python knows where to find mtgdeck
- Also enables `python -m pytest` without cd'ing

Should have done this from the start.

### Worktree Setup: File Location Matters

When working in a git worktree (`.claude/worktrees/`), paths are relative to the worktree root, NOT the parent repo.

**Problem:** Scryfall JSON was in `/repo/oracle-cards-*.json` but the worktree was at `/repo/.claude/worktrees/abc123/`.
The `find_scryfall_json()` function looked in the worktree directory and didn't find it.

**Solution:** Copy the file into the worktree:
```bash
cp oracle-cards-*.json .claude/worktrees/abc123/
```

**Why it matters:** When you `cd` into a worktree, `./data/` means the worktree's data dir, not the parent repo's. `Path(".").glob()` searches the current working directory. Being off by one level breaks file discovery.

**Lesson:** When using worktrees, either:
1. Copy shared files (like Scryfall JSON) into the worktree
2. Update find functions to search `../../` if needed
3. Use symlinks from parent to worktree

---

## 2026-05-26 (continued) — Stage 1: Mechanical Pattern Engine

### What We Built

Expanded the mechanical auto-tagger from 26 to 35 tags with 113 tests. Every tag now has:
- At least one positive match test (should fire)
- At least one negative match test (should NOT fire)

**Final coverage:** 166 tag-card pairs across 76 deck cards.

---

### Regex Design for Oracle Text Matching

**Start precise, then soften.** Begin with the exact known phrase, then generalize only when you discover a miss. Too-broad patterns cause false positives that corrupt downstream layers.

Example — Targeted Removal started as:
```python
r"destroy target creature"        # misses "destroy target nonblack creature"
```
Became:
```python
r"destroy target (?:\w+ )?(?:creature|permanent|artifact|enchantment|planeswalker)"
```
The `(?:\w+ )?` allows one optional qualifier word (nonblack, tapped, nonartifact) without breaking the specificity.

**Use `\b` for keyword matching.** Checking `r"\bflying\b"` is safe in MTG oracle text because "flying" only ever appears as a keyword. Without `\b`, "flyingcolors" would match.

**Use `(?:…)?` for optional clauses.** Living Death says "puts all cards they exiled" with `all cards` directly adjacent. The original pattern had `.{1,40}` (requiring ≥1 chars) and missed it. Changed to `.{0,40}` (zero or more).

**Oracle text modernization matters.** Scryfall standardized self-recursion in post-2022 oracle updates:
- Old: `"Return Reassembling Skeleton from your graveyard to the battlefield tapped"`
- New: `"Return this card from your graveyard to the battlefield tapped"`

Pattern `r"return this card from your graveyard"` now catches every self-recursive card cleanly without naming each one.

---

### Confidence Values Are Not Decoration

Every pattern has a confidence value (0.0–1.0). Use it deliberately:

| Confidence | When to use |
|---|---|
| 1.0 | Mechanically certain — oracle text is explicit and unambiguous |
| 0.9–0.95 | Strong signal — matches the exact mechanism but may have edge cases |
| 0.85 | Good match — common phrasing, very few false positives expected |
| 0.8 | Reasonable — broader pattern, some interpretive overlap |

Lower confidence isn't "bad" — it's honest about what you know. The rule engine uses confidence to weight its inferences.

---

### Layered Tagging Architecture

The five-layer ontology works because each layer answers a different question:

| Layer | Question | Example |
|---|---|---|
| Mechanical | What does the card literally do? | `Death_Trigger` |
| Functional | What role does it play in a deck? | `Payoff` |
| Archetype | What strategy wants it? | `Aristocrats` |
| Emotional | What is its strategic identity? | `Engine_Core` |

**Never conflate layers.** `Sacrifice_Outlet` (mechanical) and `Engine` (functional) are different things. A card can be a Sacrifice_Outlet without being an Engine — if it sacs but provides no ongoing value, it's just a Sacrifice_Outlet.

**Mechanical is objective. Functional is contextual.** A card can be a Sacrifice_Outlet in one deck and pure Fuel in another. Mechanical tags are always true; functional tags depend on the deck.

---

### Side-by-Side Terminal Layout with ANSI

Rich's markup system doesn't support mixing with raw `print()` easily. When you need to build a side-by-side layout (card frame + tag column), extract each side as a `list[str]` and zip them:

```python
card_lines = _build_card_lines(card)    # list of raw strings, fixed width
tag_lines  = _build_tag_right_lines(card_name)  # list of ANSI-colored strings

GAP = "   "
card_w = len(card_lines[0]) if card_lines else 0
max_rows = max(len(card_lines), len(tag_lines))

for i in range(max_rows):
    left  = card_lines[i] if i < len(card_lines) else " " * card_w
    right = tag_lines[i]  if i < len(tag_lines)  else ""
    print(left + GAP + right)
```

Use `\033[36m` style ANSI codes directly in the tag column strings — Rich's console.print would interfere with the fixed-width alignment.

**ANSI color constants:**
- `\033[36m` — cyan (mechanical)
- `\033[32m` — green (functional)
- `\033[33m` — yellow (archetype)
- `\033[35m` — magenta (emotional)
- `\033[2m` — dim
- `\033[0m` — reset (always needed at end of colored string)

---

### Test Design for Pattern Matching

Pattern tests should be isolated from the database. Each test class:
1. Creates a minimal Card object with crafted oracle text
2. Calls `tag_mechanical(card, db)` against an in-memory DB
3. Asserts the tag is (or is not) in the result list

```python
def _make_card(name, oracle_text=""):
    return Card(name=name, mana_cost="", cmc=0, type_line="Creature",
                oracle_text=oracle_text)

def test_swampwalk_evasion(db):
    card = _make_card("Sheoldred", "Swampwalk\nWhen this enters...")
    assert "Evasion" in tags.tag_mechanical(card, db)
```

**Always include the negative test.** If you only test "does it fire", you won't catch patterns that are too broad and fire on everything. The negative test is where you catch false positives.

---

### Small Advice

- When you add a new regex pattern, immediately test it against 3 cards: one that should match, one that shouldn't, and one edge case.
- `re.search(pattern, oracle.lower())` — always lowercase the oracle text. Scryfall uses mixed case but patterns are case-insensitive.
- "Looting" (draw-then-discard) is different from "discard as a cost then draw." Check for `then discard` vs `discard [cost] ... draw`. These have very different strategic implications.
- Adding a tag only costs a few lines. The cost of a missing tag is silent incorrect analysis downstream. When in doubt, add it.

---

## 2026-05-26 (continued) — Stage 2: Functional Rule Engine

### What We Built

A rule-based inference engine that derives Layer 3 (Functional) tags from Layer 2 (Mechanical) tags. 239 functional tags across 75 deck cards, all derived automatically. 0 manual assignments needed.

**Key numbers:**
- 80+ inference rules in `FUNCTIONAL_RULES`
- 16 functional tags populated: Enabler (36 cards), Engine (27), Mana_Acceleration (22), Payoff (20), Threat (20), Conversion (20), Recursion (17), Card_Advantage (17), Fuel (16), Removal (14), Interaction (13), Mana_Engine (9), Setup (7), Finisher_Support (7), Protection (5), Finisher (5)

---

### How the Rule Engine Works

The functional rule engine is a set-intersection algorithm:

```python
for required, functional_tag, confidence in FUNCTIONAL_RULES:
    if required.issubset(mech_tags):
        best_confidence[functional_tag] = max(confidence, best_confidence.get(functional_tag, 0.0))
```

**Three design decisions that matter:**

1. **frozenset as the key, not a list.** Rules must be declarative. A frozenset makes it clear the required tags are unordered — it doesn't matter if the card has `Death_Trigger` before or after `Life_Drain`.

2. **Best-confidence wins, not first-match.** Multiple rules can fire for the same functional tag. `Blood Artist` gets Payoff at 0.90 (Death_Trigger + Life_Drain) and also qualifies for Payoff at 0.85 via another path. The engine stores only 0.90 — the most confident signal wins.

3. **source="rule_engine" on all derived tags.** This distinguishes auto-derived functional tags from manually assigned ones. Later, if you disagree with a derivation, you can override it with source="manual" and the logic that favors higher confidence (manual = 1.0) will respect your judgment.

---

### Reminder Text Is a Double-Edged Sword

Cards like Pitiless Plunderer include Treasure token reminder text:
> "create a Treasure token. (It's an artifact with 'Sacrifice this artifact: Add one mana of any color.')"

The pattern `r"sacrifice .{1,20}: add"` fires on the reminder text and tags Pitiless Plunderer with `Sacrifice_Outlet` and `Mana_Production`. This is technically a false positive — Pitiless Plunderer itself doesn't have a sac outlet. But the net effect is real: the card creates tokens that are sac outlets, so tagging it `Engine` (via Sacrifice_Outlet + Mana_Production) isn't wrong from a deck-strategy perspective.

**Decision:** Accept this as an acceptable approximation at current confidence levels. If precision matters later, strip reminder text from oracle text before pattern matching.

---

### Rule Design: Single Tags vs. Compound Rules

**Single-tag rules** are broad and low confidence:
```python
(frozenset({"Sacrifice_Outlet"}), "Enabler", 0.80)
```
Fires for anything that can sacrifice — most of the time correct.

**Compound rules** are specific and high confidence:
```python
(frozenset({"Sacrifice_Outlet", "Mana_Production"}), "Engine", 0.90)
```
Only fires when both are present — reliable signal.

**Guideline:** Start with compound rules for high-confidence tags (Finisher, Engine). Use single-tag rules only when the single tag is itself highly specific (Tutor_Effect alone → Setup is safe because tutors almost always set up).

---

### Layer 2 Pattern Gaps Found (and Fixed)

During the functional rule design, several mechanical pattern gaps surfaced from specific cards:

| Card | Missing Tag | Root Cause | Fix |
|---|---|---|---|
| Braids | Forced_Sacrifice | "may sacrifice" vs "sacrifices" | Added `(?:may )?sacrifice(?:s)?` |
| Braids | Upkeep_Trigger | "each other player's upkeep" not in alternation | Added to alternation |
| Braids | Discard_Effect | "that player discards" not covered | Added pattern |
| Archon of Cruelty | Life_Drain | "and loses 3 life" compound clause | Added `r"and loses? \d+ life"` |
| Crypt Ghast | Life_Gain | Extort says "gain that much life" | Added `r"you gain that much life"` |
| Pitiless Plunderer | Token_Generation | Treasure is an artifact token, not creature | Added artifact token pattern |
| Jadar | Upkeep_Trigger | "end step" not in Upkeep_Trigger timing | Added to alternation |
| Exsanguinate | (nothing) | No way to distinguish X-spell from fixed drain | Added X_Spell_Effect tag |

**Lesson:** Build functional rules before you think your mechanical layer is complete. The functional rules reveal which mechanical distinctions actually matter.

---

### Verifying the Rule Engine Against Real Cards

After writing rules, spot-check 5–10 cards manually. The test is: does the functional derivation match how you'd actually describe the card to a fellow deckbuilder?

- **Blood Artist** → `Payoff(0.90)` — correct, it's the classic aristocrats payoff
- **Ashnod's Altar** → `Engine + Conversion` — correct, it converts creatures into mana
- **Exsanguinate** → `Finisher(0.90)` — correct, this is the win condition
- **Living Death** → `Recursion + Finisher` — correct, it resets the board in your favor
- **Reassembling Skeleton** → `Fuel + Recursion` — correct, it's the repeating sacrifice body

If the derivation disagrees with your intuition, either fix the rule or override with a manual tag. The engine is a starting point, not the final word.

---

### Small Advice

- `frozenset({"A", "B"})` not `{"A", "B"}` — frozensets are hashable and can serve as dict keys if you ever need to deduplicate rules.
- The rule engine is O(n × m) where n = cards, m = rules. With 75 cards and 80 rules this is trivially fast. At 36k cards it's still < 0.1s.
- Run the mechanical tagger again any time you add new patterns — the database stores tags with UPSERT, so re-running is always safe and always picks up new patterns.
