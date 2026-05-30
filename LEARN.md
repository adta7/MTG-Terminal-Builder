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

## 2026-05-27

### Arrow Key Timeout on macOS: Don't Use `select()` Timeout for Continuation Bytes

**Problem:** Arrow keys send three bytes: `\x1b [ A` (for UP). If you use `select.select([stdin], [], [], 0.05)` to wait for the second and third bytes, **the timeout may expire before those bytes arrive**, especially on macOS. This causes arrow keys to be misdetected as bare ESC.

**Why it happens:** On some terminal emulators (iTerm2, Terminal.app), escape sequence bytes don't arrive immediately in sequence. They may take 100–500ms to arrive, well beyond typical 50ms timeouts.

**Solution:** Use `select()` **only for the first byte**. After detecting `\x1b`, read the remaining bytes in **pure blocking mode without a timeout**:

```python
def getch() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        
        # Wait for FIRST byte with select (first byte timing is normal)
        if not select.select([sys.stdin], [], [], 10)[0]:
            return None
        
        ch = sys.stdin.buffer.read(1)
        
        if ch == b'\x1b':
            # Read the NEXT bytes in blocking mode (no timeout)
            # They WILL arrive eventually, just maybe slowly
            ch2 = sys.stdin.buffer.read(1)
            if ch2 == b'[':
                ch3 = sys.stdin.buffer.read(1)
                if ch3 == b'A': return 'UP'
                if ch3 == b'B': return 'DOWN'
                if ch3 == b'C': return 'RIGHT'
                if ch3 == b'D': return 'LEFT'
            return 'ESC'
        
        return ch.decode('utf-8', errors='replace')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
```

**Key insight:** Escape sequence continuation bytes aren't like the initial byte — users don't initiate them. The terminal generates them automatically after sending `\x1b`. So it's safe to wait for them in blocking mode. They **will** arrive.

**Don't overcomplicate it:** Avoid `fcntl` non-blocking mode, retry loops, or multiple `select()` calls for continuation bytes. Just read them blocking. It works and it's simple.

---

### Mistakes / Fixes (Updated)

**Problem:** Escape sequence byte detection had a `select()` timeout on all three bytes, causing arrows to timeout and be misdetected as ESC.
**Previous (incorrect) fix:** Increase the timeout to 200ms or 500ms.
**What actually worked:** Remove the timeout for continuation bytes — use blocking reads for bytes 2 and 3.

**Problem:** Interactive search view tried to switch between normal mode (`input()`) and raw mode (`getch()`) mid-interaction. This caused the search input to fail silently — users typed search queries but nothing happened.
**Root cause:** Mixing terminal modes within a single loop creates state confusion. When `getch()` exits and restores terminal settings, then `input()` is called, the buffering and mode switching causes unpredictable behavior.
**What actually worked:** Separate the concerns cleanly:
  1. Get user input in **normal mode** first (use `input()`)
  2. Then execute the search
  3. Then enter **raw mode** for the interactive navigation loop (use `getch()`)
  4. Never try to switch modes within the same interaction loop

The separation makes it simple and reliable.

---
