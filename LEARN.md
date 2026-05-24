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

### Small Advice

- `git commit` is cheap. Commit often so you always have a safe point to go back to.
- `git push` is when you decide to share. Keep those moments deliberate.
- A 165MB JSON file loaded once per session is fine. Loaded on every search would be a problem.
- The terminal width is not fixed. Always read it at render time, not at startup.
- `pbcopy` only works on Mac. If you ever share this across platforms, you'll need to detect the OS.
- `difflib.get_close_matches` is surprisingly good for card name typos and handles things like "Lighthing Bolt" → "Lightning Bolt" correctly.
