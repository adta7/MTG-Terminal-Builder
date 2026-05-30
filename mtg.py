"""
mtg.py — MTG Terminal Builder
Interactive terminal tool for Magic: The Gathering deck building and collection management.

Usage:
    python3 mtg.py
"""

import os
import re
import sys
import json
import glob
import difflib
import subprocess
import textwrap
import tty
import termios
import select
from datetime import datetime

# ─── Auto-install dependencies ────────────────────────────────────────────────

def ensure_dependencies():
    required = {"pandas": "pandas", "openpyxl": "openpyxl", "rich": "rich"}
    missing = []
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    if missing:
        print(f"\n  Installing required packages: {', '.join(missing)}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + missing)
            print(f"  ✓ Installation complete.\n")
        except Exception as e:
            print(f"  ✗ Error installing packages: {e}")
            sys.exit(1)

ensure_dependencies()

import shutil
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Import UI components and views
from ui import SessionState, MenuItem, ask_choice_interactive
from search_view import run_card_search_view
from pinned_view import run_pinned_cards_view

console = Console()

# ─── Constants ────────────────────────────────────────────────────────────────

DOWNLOADS = os.path.expanduser("~/Downloads")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DECKS_DIR = os.path.join(SCRIPT_DIR, "decks")

DECKBUILDING_COLUMNS = [
    "Name", "Count", "Foil",
    "scryfall_name", "mana_cost", "cmc", "type_line", "oracle_text",
    "power", "toughness", "loyalty", "colors", "color_identity",
    "keywords", "rarity", "legalities_commander", "legalities_modern", "legalities_standard",
]

DECKBUILDING_RENAME = {
    "scryfall_name":        "Verified Name",
    "mana_cost":            "Mana Cost",
    "cmc":                  "CMC",
    "type_line":            "Type",
    "oracle_text":          "Card Text",
    "power":                "Power",
    "toughness":            "Toughness",
    "loyalty":              "Loyalty",
    "colors":               "Colors",
    "color_identity":       "Color Identity",
    "keywords":             "Keywords",
    "rarity":               "Rarity",
    "legalities_commander": "Commander Legal",
    "legalities_modern":    "Modern Legal",
    "legalities_standard":  "Standard Legal",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def term_width():
    return shutil.get_terminal_size().columns

def term_height():
    return shutil.get_terminal_size().lines

def divider(char="─", width=None):
    print(char * (width or min(term_width(), 80)))

def header(text):
    console.print(f"\n[bold cyan]{text}[/bold cyan]")
    console.print("[dim cyan]" + "─" * min(term_width(), 80) + "[/dim cyan]")

def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"  {prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nAborted.")
        sys.exit(0)
    return val if val else default

def ask_yn(prompt, default="y"):
    """Prompt for yes/no. Returns True, False, or None if ESC was pressed."""
    hint = "Y/n" if default == "y" else "y/N"
    result = _read_raw_line(f"  {prompt} ({hint}): ")
    if result is _ESCAPE:
        return None
    val = result.strip().lower()
    if not val:
        return default == "y"
    return val.startswith("y")

def ask_choice(prompt, options, labels=None, cancellable=False):
    """Display a numbered menu and return the 0-based index of the chosen option.

    ESC always returns None. If cancellable=True, an empty line or '0' also
    returns None. The main menu ignores None and re-prompts; pipeline steps
    treat it as cancel.
    """
    print(f"\n  {prompt}")
    for i, opt in enumerate(options):
        label = labels[i] if labels else opt
        print(f"    [{i+1}] {label}")
    while True:
        result = _read_raw_line("  Choice: ")
        if result is _ESCAPE:
            return None
        val = result.strip()
        if cancellable and (not val or val == '0'):
            return None
        if val.isdigit() and 1 <= int(val) <= len(options):
            return int(val) - 1
        print(f"  Please enter a number between 1 and {len(options)}.")

# ─── Scryfall DB (lazy load, shared) ──────────────────────────────────────────

_scryfall_db = None

def get_scryfall_db():
    global _scryfall_db
    if _scryfall_db is None:
        json_path = find_scryfall_json()
        _scryfall_db = load_scryfall_db(json_path)
    return _scryfall_db

# ─── Deck Manager ─────────────────────────────────────────────────────────────

def ensure_decks_dir():
    os.makedirs(DECKS_DIR, exist_ok=True)

def list_decks():
    ensure_decks_dir()
    files = glob.glob(os.path.join(DECKS_DIR, "*.json"))
    decks = []
    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            decks.append({
                "path": f,
                "name": data.get("name", os.path.basename(f)),
                "created": data.get("created", ""),
                "edited": data.get("edited", ""),
                "cards": data.get("cards", []),
            })
        except Exception:
            pass
    decks.sort(key=lambda d: d["edited"], reverse=True)
    return decks

def save_deck(deck):
    ensure_decks_dir()
    safe_name = deck["name"].lower().replace(" ", "_")
    path = deck.get("path") or os.path.join(DECKS_DIR, f"{safe_name}.json")
    deck["edited"] = datetime.now().strftime("%Y-%m-%d")
    with open(path, "w") as f:
        json.dump({k: v for k, v in deck.items() if k != "path"}, f, indent=2)
    return path

# Matches section header lines from Moxfield, Arena, Archidekt, MTGO exports.
# Examples: "Sideboard", "Sideboard (15)", "Commander (1)", "Deck:", "Maybeboard"
# Does NOT match card names like "Commander Eesha" (extra non-paren text after keyword).
_SECTION_RE = re.compile(
    r'^(commander|deck|sideboard|maybeboard|companion|mainboard|main|'
    r'attractions|stickers|schemes|planes)'
    r'(\s*:|\s+\(\d+\))?$',
    re.IGNORECASE,
)
_SKIP_SECTIONS = {"maybeboard", "companion", "attractions", "stickers", "schemes", "planes"}
_MAIN_SECTIONS = {"commander", "deck", "mainboard", "main"}


def _clean_card_name(raw):
    """
    Strip metadata from a raw card name string:
      (set_code)        e.g. (m19), (soc), (2x2), (hob)
      [tags]            e.g. [Protection], [Maybeboard{noDeck}{noPrice},Draw]
      trailing number   e.g. trailing collector number like 196 in "Swamp (hob) 196"
    Returns the cleaned card name, or None if the result is empty.
    """
    name = raw
    name = re.sub(r'\s*\([a-z0-9]{2,6}\)\s*', ' ', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\[[^\]]*\]\s*', ' ', name)
    name = re.sub(r'\s+\d+\s*$', '', name)
    return name.strip() or None


def _inline_tag_section(raw_name):
    """
    Return the lowercase content of the first [...] tag in the name string,
    or an empty string if no tag is present.
    Used to detect Archidekt inline maybeboard/sideboard markers.
    """
    m = re.search(r'\[([^\]]+)\]', raw_name)
    return m.group(1).lower() if m else ""


def parse_card_list(lines):
    """
    Parse a card list from common export formats. Returns (main, sideboard) tuple.

      4 Lightning Bolt                          plain text → main
      4x Lightning Bolt                         Moxfield / Archidekt (x suffix) → main
      1x Animate Dead (soc) [Recursion]         Archidekt — set code and tag stripped → main
      1x Cabal Ritual (tor) [Sideboard,Ramp]    Archidekt inline sideboard tag → sideboard
      1x Bolas's Citadel (war) [Maybeboard...]  Archidekt maybeboard — skipped entirely
      26x Swamp (hob) 196                       set code + collector number stripped → main
      SB: 4 Counterspell                        MTGO sideboard prefix → sideboard
      # comment / // comment                    skipped
      Sideboard (15)                            section header — cards below → sideboard
      Maybeboard                                section header — cards below skipped
      Commander (1) / Deck (98)                 section header — cards below → main
    """
    main      = []
    sideboard = []
    commander = None
    current_section = "main"  # "main", "sideboard", or "skip"

    for raw in lines:
        line = raw.strip()

        # Blank lines and comment lines
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        # MTGO sideboard prefix "SB: 4 Card Name" → route to sideboard
        mtgo_sb = re.match(r'^SB:\s*(.+)', line, re.IGNORECASE)
        if mtgo_sb:
            name = _clean_card_name(mtgo_sb.group(1).strip())
            if name:
                sideboard.append({"name": name, "count": 1})
            continue

        # Section header detection (Moxfield / Arena / MTGO style)
        m = _SECTION_RE.match(line)
        if m:
            key = m.group(1).lower()
            if key == "sideboard":
                current_section = "sideboard"
            elif key in _SKIP_SECTIONS:
                current_section = "skip"
            else:
                current_section = "main"
            continue

        if current_section == "skip":
            continue

        # Split count prefix. Handles "4", "4x", "4X".
        parts = line.split(" ", 1)
        count_str = parts[0].rstrip("xX")
        if len(parts) == 2 and count_str.isdigit():
            count    = int(count_str)
            name_raw = parts[1].strip()
        else:
            count    = 1
            name_raw = line

        # Archidekt inline tag routing.
        # [Maybeboard{noDeck}...] → skip.
        # [Sideboard,...] → sideboard.
        # [Commander{top}] → main deck + mark as commander.
        tag = _inline_tag_section(name_raw)
        if "maybeboard" in tag:
            continue
        is_inline_sb  = "sideboard"  in tag and "commander" not in tag
        is_commander  = "commander"  in tag

        # Strip set codes, remaining tags, and trailing collector numbers.
        name = _clean_card_name(name_raw)
        if not name:
            continue

        if is_inline_sb or current_section == "sideboard":
            sideboard.append({"name": name, "count": count})
        else:
            main.append({"name": name, "count": count})
            if is_commander and commander is None:
                commander = name

    return main, sideboard, commander


def _collect_lines(prompt_extra=""):
    """Shared input loop for card list pasting.

    Returns a list of lines, or _ESCAPE if the user pressed ESC to cancel.
    """
    if prompt_extra:
        print(prompt_extra)
    print("  Type END on a new line when done, or ESC to cancel.\n")
    lines = []
    while True:
        line = _read_raw_line("  > ")
        if line is _ESCAPE:
            return _ESCAPE
        line = line.strip()
        if line.upper() == "END":
            break
        lines.append(line)
    return lines


def import_card_list():
    print("\n  Paste your card list below.")
    print("  Supports: plain text, Moxfield, Arena, Archidekt exports.")
    print("  Sideboard cards are captured separately. Maybeboard is skipped.")
    lines = _collect_lines()
    if lines is _ESCAPE:
        return [], [], None
    return parse_card_list(lines)  # returns (main, sideboard, commander_name)


def import_sideboard_list():
    """Paste a plain card list — everything goes straight to the sideboard, no tags needed."""
    print("\n  Paste cards to add to the sideboard.")
    print("  Plain names or counts work fine — no tags needed.")
    lines = _collect_lines()
    if lines is _ESCAPE:
        return []
    # Parse normally and merge all buckets: user may or may not use tags,
    # but the intent is sideboard so everything lands there.
    main, sideboard, _ = parse_card_list(lines)
    return main + sideboard

def merge_cards(existing_cards, new_cards):
    index = {c["name"].lower(): c for c in existing_cards}
    for card in new_cards:
        key = card["name"].lower()
        if key in index:
            index[key]["count"] += card["count"]
        else:
            existing_cards.append(card)
            index[key] = card
    return existing_cards

def deck_to_text(deck):
    lines = []
    for card in sorted(deck["cards"], key=lambda c: c["name"]):
        lines.append(f"{card['count']} {card['name']}")
    sideboard = deck.get("sideboard", [])
    if sideboard:
        lines.append("")
        lines.append("Sideboard")
        for card in sorted(sideboard, key=lambda c: c["name"]):
            lines.append(f"{card['count']} {card['name']}")
    return "\n".join(lines)

def copy_to_clipboard(text):
    try:
        subprocess.run("pbcopy", input=text.encode(), check=True)
        return True
    except Exception:
        return False

def delete_deck(deck):
    path = deck.get("path")
    if path and os.path.exists(path):
        os.remove(path)

def getch():
    """Read a single keypress without requiring Enter. Handles arrow keys and ESC.

    Uses a 50ms timeout after seeing \\x1b so a bare ESC press doesn't block
    waiting for arrow-key bytes that may never arrive.
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.buffer.read(1)
        if ch == b'\x03':
            raise KeyboardInterrupt
        if ch == b'\x1b':
            # Wait up to 50 ms for a follow-up byte (arrow-key escape sequence)
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch2 = sys.stdin.buffer.read(1)
                if ch2 == b'[' and select.select([sys.stdin], [], [], 0.05)[0]:
                    ch3 = sys.stdin.buffer.read(1)
                    if ch3 == b'A': return 'UP'
                    if ch3 == b'B': return 'DOWN'
                    if ch3 == b'C': return 'RIGHT'
                    if ch3 == b'D': return 'LEFT'
            return 'ESC'
        return ch.decode('utf-8', errors='replace')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# Sentinel returned by ask_escapable() when the user presses ESC.
# Distinct from None (empty ENTER) so callers can tell the difference.
_ESCAPE = object()


def _read_raw_line(prompt):
    """Core raw-mode line reader used by ask_escapable and _collect_lines.

    Writes `prompt` as-is, then reads char-by-char with backspace and ESC
    support. Returns _ESCAPE on a bare ESC press, or the raw line string
    (possibly empty) on ENTER. Uses \\r\\n in raw mode so the cursor returns
    to column 0 correctly.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.buffer.read(1)
            if ch == b'\x03':
                raise KeyboardInterrupt
            if ch == b'\x1b':
                # Consume trailing escape-sequence bytes (arrow keys, etc.)
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    ch2 = sys.stdin.buffer.read(1)
                    if ch2 == b'[' and select.select([sys.stdin], [], [], 0.05)[0]:
                        sys.stdin.buffer.read(1)  # ch3 — discard
                    continue  # ignore all escape sequences inside text input
                # Bare ESC — cancel
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                return _ESCAPE
            if ch in (b'\r', b'\n'):
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                return ''.join(buf)
            if ch in (b'\x7f', b'\x08'):  # backspace / delete
                if buf:
                    buf.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            else:
                try:
                    # Reassemble multi-byte UTF-8 sequences (e.g. accented card names).
                    # The first byte's high bits tell us how many continuation bytes follow.
                    first = ch[0]
                    if   first & 0xF8 == 0xF0: extra = 3   # 4-byte sequence
                    elif first & 0xF0 == 0xE0: extra = 2   # 3-byte sequence
                    elif first & 0xE0 == 0xC0: extra = 1   # 2-byte sequence
                    else:                       extra = 0   # plain ASCII or stray byte
                    for _ in range(extra):
                        if select.select([sys.stdin], [], [], 0.02)[0]:
                            ch += sys.stdin.buffer.read(1)
                    c = ch.decode('utf-8')
                    if c.isprintable():
                        buf.append(c)
                        sys.stdout.write(c)
                        sys.stdout.flush()
                except UnicodeDecodeError:
                    pass
    except KeyboardInterrupt:
        # Restore terminal before any output so \n works correctly
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write('\r\n\r\nAborted.\r\n')
        sys.stdout.flush()
        sys.exit(0)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def ask_escapable(prompt, default=None):
    """Like ask(), but pressing ESC returns _ESCAPE immediately."""
    suffix = f" [{default}]" if default else ""
    result = _read_raw_line(f"  {prompt}{suffix}: ")
    if result is _ESCAPE:
        return _ESCAPE
    val = result.strip()
    return val if val else default

def show_deck(deck, filter_query="", filter_db=None):
    """Print the current deck contents, including sideboard if present.
    If filter_query + filter_db are set, only matching cards are shown but
    with their original index numbers so D/S# deletes still work correctly.
    """
    cards     = sorted(deck["cards"],             key=lambda c: c["name"])
    sideboard = sorted(deck.get("sideboard", []), key=lambda c: c["name"])
    total     = sum(c["count"] for c in deck["cards"])
    sb_total  = sum(c["count"] for c in sideboard)
    commander = deck.get("commander")

    console.print(f"\n  [bold cyan]{deck['name']}[/bold cyan]  [dim]{total} cards[/dim]")
    if commander:
        console.print(f"  [bold yellow]⚔  {commander}[/bold yellow]")

    filtering = bool(filter_query and filter_db)

    if filtering:
        matched    = {c["name"] for c in apply_deck_filter(cards,     filter_query, filter_db)}
        sb_matched = {c["name"] for c in apply_deck_filter(sideboard, filter_query, filter_db)}
        n_matched  = sum(1 for c in cards if c["name"] in matched)
        console.print(f"  [dim]Filter:[/dim] [yellow]{filter_query}[/yellow]"
                      f"  [dim]— {n_matched} of {len(cards)} cards[/dim]")
        console.print()

        shown = 0
        for i, card in enumerate(cards, 1):
            if card["name"] in matched:
                qty = f"{card['count']}x" if card["count"] > 1 else ""
                console.print(f"  [dim]{i:>3}.[/dim]  {qty:<4}{card['name']}")
                shown += 1
        if not shown:
            console.print("  [dim]No cards match this filter.[/dim]")

        if sideboard:
            sb_hits = [c for c in sideboard if c["name"] in sb_matched]
            if sb_hits:
                sb_n = sum(c["count"] for c in sb_hits)
                console.print(f"\n  [dim]── Sideboard  {sb_n} match(es) ──[/dim]\n")
                for i, card in enumerate(sideboard, 1):
                    if card["name"] in sb_matched:
                        qty = f"{card['count']}x" if card["count"] > 1 else ""
                        console.print(f"  [dim]S{i:>2}.[/dim]  {qty:<4}{card['name']}")
    else:
        console.print()
        if not cards:
            console.print("  [dim]No cards yet.[/dim]")
        else:
            for i, card in enumerate(cards, 1):
                qty = f"{card['count']}x" if card["count"] > 1 else ""
                console.print(f"  [dim]{i:>3}.[/dim]  {qty:<4}{card['name']}")

        if sideboard:
            console.print(f"\n  [dim]── Sideboard  {sb_total} cards ──[/dim]\n")
            for i, card in enumerate(sideboard, 1):
                qty = f"{card['count']}x" if card["count"] > 1 else ""
                console.print(f"  [dim]S{i:>2}.[/dim]  {qty:<4}{card['name']}")

    console.print()

def validate_card_list(cards, db):
    """Check each card against the DB. Offer fuzzy suggestions for mismatches."""
    db_keys = list(db.keys())
    validated = []

    for card in cards:
        name = card["name"]
        found = db.get(name.lower())

        if found is None and "//" in name:
            found = db.get(name.split("//")[0].strip().lower())

        if found:
            validated.append({"name": found["name"], "count": card["count"]})
            continue

        close = difflib.get_close_matches(name.lower(), db_keys, n=3, cutoff=0.6)
        if close:
            console.print(f"\n  [yellow]?[/yellow] '{name}' not found. Did you mean:")
            for i, c in enumerate(close, 1):
                console.print(f"      [{i}] {db[c]['name']}")
            val = ask_escapable("Enter number to use, or ESC/ENTER to skip")
            if val is _ESCAPE or not val:
                console.print(f"  [dim]Skipped '{name}'.[/dim]")
            elif val.isdigit() and 1 <= int(val) <= len(close):
                correct = db[close[int(val) - 1]]
                console.print(f"  [green]✓ Using: {correct['name']}[/green]")
                validated.append({"name": correct["name"], "count": card["count"]})
            else:
                console.print(f"  [dim]Skipped '{name}'.[/dim]")
        else:
            console.print(f"  [red]✗[/red] '{name}' — not found, no close matches. Skipping.")

    return validated

def _check_card_list_against_db(card_list, db, db_keys, section_label):
    """Check one list (main or sideboard) against the DB, fixing names in place."""
    issues = []
    for card in card_list:
        found = db.get(card["name"].lower())
        if found is None and "//" in card["name"]:
            found = db.get(card["name"].split("//")[0].strip().lower())
        if found is None:
            issues.append(card)

    if not issues:
        console.print(f"  [green]✓ All {section_label} cards found.[/green]")
        return

    console.print(f"  [yellow]{len(issues)} {section_label} card(s) not recognised:[/yellow]\n")
    for card in issues:
        close = difflib.get_close_matches(card["name"].lower(), db_keys, n=3, cutoff=0.6)
        if close:
            console.print(f"  [yellow]?[/yellow] '{card['name']}'. Did you mean:")
            for i, c in enumerate(close, 1):
                console.print(f"      [{i}] {db[c]['name']}")
            val = ask_escapable("Enter number to fix, or ESC/ENTER to skip")
            if val is not _ESCAPE and val and val.isdigit() and 1 <= int(val) <= len(close):
                correct_name = db[close[int(val) - 1]]["name"]
                for c in card_list:
                    if c["name"] == card["name"]:
                        c["name"] = correct_name
                        break
                console.print(f"  [green]✓ Fixed: '{card['name']}' → '{correct_name}'[/green]")
        else:
            console.print(f"  [red]✗[/red] '{card['name']}' — no close matches found.")


def check_deck_against_db(deck, db):
    """Validate main deck and sideboard against Scryfall. Offer to fix unrecognised names."""
    db_keys   = list(db.keys())
    main      = sorted(deck["cards"], key=lambda c: c["name"])
    sideboard = sorted(deck.get("sideboard", []), key=lambda c: c["name"])
    total     = len(main) + len(sideboard)

    console.print(f"\n  Checking {total} cards against Scryfall...\n")
    _check_card_list_against_db(deck["cards"], db, db_keys, "main deck")
    if sideboard:
        console.print()
        _check_card_list_against_db(deck["sideboard"], db, db_keys, "sideboard")
    console.print()


def apply_deck_filter(cards, query, db):
    """
    Filter a list of deck card entries by a query string. Returns matching entries.

    Syntax:
      lightning          name contains "lightning"
      type:creature      type line contains "creature"
      text:draw          oracle text contains "draw"
      cmc:3              CMC equals 3
      cmc:>=4            CMC greater than or equal to 4  (also >, <, <=, !=)
      color:b            color identity includes Black  (w/u/b/r/g or full name)
      color:colorless    no color identity
      color:multicolor   two or more colors
      keyword:flying     keywords list contains "flying"
    """
    if not query:
        return cards

    COLOR_MAP = {
        "white": "W", "blue": "U", "black": "B", "red": "R", "green": "G",
        "w": "W", "u": "U", "b": "B", "r": "R", "g": "G",
    }

    field_m = re.match(r'^(type|text|cmc|color|keyword|name):(.+)$', query.strip(), re.IGNORECASE)
    field   = field_m.group(1).lower() if field_m else None
    value   = field_m.group(2).strip().lower() if field_m else query.strip().lower()

    results = []
    for entry in cards:
        name = entry["name"]
        card = db.get(name.lower())
        if card is None and "//" in name:
            card = db.get(name.split("//")[0].strip().lower())

        match = False

        # Default (no prefix) or explicit name: search card name
        if field is None or field == "name":
            match = value in name.lower()

        elif field == "type":
            tl = (card.get("type_line", "") if card else "").lower()
            match = value in tl

        elif field == "text":
            oracle = (card.get("oracle_text", "") if card else "").lower()
            match = value in oracle

        elif field == "cmc":
            cmc = float(card.get("cmc", 0) or 0) if card else 0
            m2  = re.match(r'^([><=!]{0,2})(\d+(?:\.\d+)?)$', value)
            if m2:
                op, num = (m2.group(1) or "="), float(m2.group(2))
                if   op in ("", "=", "=="): match = cmc == num
                elif op == ">":             match = cmc >  num
                elif op == ">=":            match = cmc >= num
                elif op == "<":             match = cmc <  num
                elif op == "<=":            match = cmc <= num
                elif op in ("!", "!="):     match = cmc != num

        elif field == "color":
            ci = card.get("color_identity", []) if card else []
            if value == "colorless":
                match = len(ci) == 0
            elif value == "multicolor":
                match = len(ci) > 1
            else:
                target = COLOR_MAP.get(value, value.upper())
                match  = target in ci

        elif field == "keyword":
            kw = " ".join(card.get("keywords", []) if card else []).lower()
            match = value in kw

        if match:
            results.append(entry)

    return results


def show_deck_stats(deck, db):
    cards = deck["cards"]
    if not cards:
        console.print("  [dim]No cards to analyze.[/dim]\n")
        return

    total = sum(c["count"] for c in cards)

    BROAD_TYPES = ["Land", "Creature", "Instant", "Sorcery", "Artifact", "Enchantment", "Planeswalker", "Battle"]
    COLOR_LABELS = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green", "C": "Colorless"}

    cmc_curve   = {}   # cmc bucket (0–7) -> count, non-lands only
    type_counts = {}   # broad type -> count
    color_counts = {}  # color letter -> count
    total_cmc    = 0.0
    nonland_count = 0
    skipped = 0

    for entry in cards:
        count = entry["count"]
        card = db.get(entry["name"].lower())
        if card is None and "//" in entry["name"]:
            card = db.get(entry["name"].split("//")[0].strip().lower())
        if card is None:
            skipped += count
            continue

        type_line = card.get("type_line", "")
        matched = next((t for t in BROAD_TYPES if t in type_line), "Other")
        type_counts[matched] = type_counts.get(matched, 0) + count

        ci = card.get("color_identity", [])
        for c in (ci if ci else ["C"]):
            color_counts[c] = color_counts.get(c, 0) + count

        if matched != "Land":
            cmc = card.get("cmc", 0) or 0
            bucket = min(int(cmc), 7)
            cmc_curve[bucket] = cmc_curve.get(bucket, 0) + count
            total_cmc += cmc * count
            nonland_count += count

    avg_cmc = total_cmc / nonland_count if nonland_count else 0

    console.print(f"\n  [bold cyan]── Stats: {deck['name']} ──[/bold cyan]\n")
    console.print(f"  Total cards  {total}")
    console.print(f"  Avg CMC      {avg_cmc:.2f}  [dim](non-lands)[/dim]")
    if skipped:
        console.print(f"  [yellow]  {skipped} card(s) not in DB — excluded from stats[/yellow]")
    console.print()

    if cmc_curve:
        max_v = max(cmc_curve.values())
        console.print("  [bold]Mana Curve[/bold]  [dim](non-lands)[/dim]")
        for i in range(8):
            cnt = cmc_curve.get(i, 0)
            label = f"{i}+" if i == 7 else str(i)
            bar = "█" * round(cnt / max_v * 24) if max_v else ""
            console.print(f"    {label}  {bar:<24}  {cnt}")
        console.print()

    if type_counts:
        max_v = max(type_counts.values())
        console.print("  [bold]Card Types[/bold]")
        for t in BROAD_TYPES + ["Other"]:
            cnt = type_counts.get(t, 0)
            if not cnt:
                continue
            bar = "█" * round(cnt / max_v * 24) if max_v else ""
            pct = round(cnt / total * 100)
            console.print(f"    {t:<15}  {bar:<24}  {cnt:>3}  {pct:>3}%")
        console.print()

    if color_counts:
        max_v = max(color_counts.values())
        console.print("  [bold]Color Identity[/bold]")
        for letter in ["W", "U", "B", "R", "G", "C"]:
            cnt = color_counts.get(letter, 0)
            if not cnt:
                continue
            label = COLOR_LABELS[letter]
            bar = "█" * round(cnt / max_v * 24) if max_v else ""
            console.print(f"    {label:<10}  {bar:<24}  {cnt}")
        console.print()


def pick_deck(decks):
    """Show deck list and handle open / copy / delete shortcuts."""
    new_idx = len(decks) + 1

    print(f"\n  Your decks:")
    for i, d in enumerate(decks, start=1):
        print(f"    [{i}] {d['name']}  (edited {d['edited']})")
    print(f"    [{new_idx}] ── Create New Deck ──")
    print()
    print(f"  Shortcuts:  [N] open  [N2] copy to clipboard  [N0] delete  [0] back")

    while True:
        try:
            val = input("  Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAborted.")
            sys.exit(0)

        if not val or val == "0":
            return "back", None

        if not val.isdigit():
            print(f"  Please enter a valid number.")
            continue

        # Split into deck number and optional action suffix
        if val.endswith("2") and len(val) > 1:
            deck_num = int(val[:-1])
            action = "copy"
        elif val.endswith("0") and len(val) > 1:
            deck_num = int(val[:-1])
            action = "delete"
        else:
            deck_num = int(val)
            action = "open"

        if deck_num == new_idx and action == "open":
            return "new", None

        if 1 <= deck_num <= len(decks):
            return action, decks[deck_num - 1]

        print(f"  Please enter a number between 1 and {new_idx}.")

def run_deck_manager():
    header("Deck Manager")
    decks = list_decks()

    action, deck = pick_deck(decks)

    if action == "back":
        return

    # Copy to clipboard
    if action == "copy":
        text = deck_to_text(deck)
        if copy_to_clipboard(text):
            total = sum(c["count"] for c in deck["cards"])
            print(f"\n  ✓ Copied {total} cards from '{deck['name']}' to clipboard.\n")
        else:
            print(f"\n  ✗ Clipboard copy failed (pbcopy not available).\n")
        return

    # Delete deck
    if action == "delete":
        print(f"\n  Delete '{deck['name']}'? This cannot be undone.")
        if ask_yn("Confirm delete", default="n"):
            delete_deck(deck)
            print(f"  ✓ Deleted '{deck['name']}'.\n")
        else:
            print("  Cancelled.\n")
        return

    # Create new deck
    if action == "new":
        deck_name = ask_escapable("Deck name")
        if not deck_name or deck_name is _ESCAPE:
            print("  Returning to menu.\n")
            return
        deck = {
            "name": deck_name,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "edited": "",
            "commander": None,
            "cards": [],
            "sideboard": [],
        }
        mode_idx = ask_choice(
            "How do you want to start?",
            ["import", "blank"],
            ["Import from card list", "Start blank"],
        )
        if mode_idx is None:
            print("  Returning to menu.\n")
            return
        if mode_idx == 0:
            main_cards, sb_cards, detected_cmdr = import_card_list()
            deck["cards"]     = main_cards
            deck["sideboard"] = sb_cards
            if detected_cmdr:
                deck["commander"] = detected_cmdr
            total    = sum(c["count"] for c in main_cards)
            sb_total = sum(c["count"] for c in sb_cards)
            print(f"\n  ✓ Imported {total} cards ({len(main_cards)} unique).")
            if sb_cards:
                print(f"  ✓ Sideboard: {sb_total} cards ({len(sb_cards)} unique).")
            if detected_cmdr:
                print(f"  ✓ Commander detected: {detected_cmdr}")

    # Ensure keys exist on decks loaded from older JSON files
    deck.setdefault("sideboard", [])
    deck.setdefault("commander", None)

    active_filter    = ""
    active_filter_db = None

    # Deck edit loop — single-key menu (no ENTER needed)
    while True:
        show_deck(deck, filter_query=active_filter, filter_db=active_filter_db)
        console.print(
            "  [bold cyan]A[/bold cyan] Add   "
            "[bold cyan]B[/bold cyan] +Sideboard   "
            "[bold red]D[/bold red] Delete   "
            "[bold yellow]M[/bold yellow] Commander   "
            "[bold blue]F[/bold blue] Filter   "
            "[dim]C[/dim] Check   "
            "[dim]T[/dim] Stats   "
            "[bold green]W[/bold green] Save   "
            "[dim]ESC[/dim] Save+Exit"
        )
        sys.stdout.write("  Choice: ")
        sys.stdout.flush()
        key = getch()
        choice = key if key in ('ESC', 'UP', 'DOWN', 'LEFT', 'RIGHT') else key.upper()
        # Echo the key on the same line so it reads "Choice: D"
        if key == 'ESC':
            print("ESC")
        elif len(key) == 1 and key.isprintable():
            print(key.upper())
        else:
            print()

        if choice == 'B':
            sb_new = import_sideboard_list()
            if sb_new:
                db = get_scryfall_db()
                sb_new = validate_card_list(sb_new, db)
                if sb_new:
                    deck["sideboard"] = merge_cards(deck["sideboard"], sb_new)
                    console.print(f"\n  [green]✓ Added {len(sb_new)} card type(s) to sideboard.[/green]")

        elif choice == 'A':
            main_new, sb_new, detected_cmdr = import_card_list()
            db = get_scryfall_db()
            if main_new:
                main_new = validate_card_list(main_new, db)
                if main_new:
                    deck["cards"] = merge_cards(deck["cards"], main_new)
                    console.print(f"\n  [green]✓ Added {len(main_new)} card type(s) to main deck.[/green]")
            if sb_new:
                sb_new = validate_card_list(sb_new, db)
                if sb_new:
                    deck["sideboard"] = merge_cards(deck["sideboard"], sb_new)
                    console.print(f"  [green]✓ Added {len(sb_new)} card type(s) to sideboard.[/green]")
            if detected_cmdr and deck["commander"] != detected_cmdr:
                deck["commander"] = detected_cmdr
                console.print(f"  [green]✓ Commander updated: {detected_cmdr}[/green]")

        elif choice == 'D':
            main_sorted = sorted(deck["cards"],             key=lambda c: c["name"])
            sb_sorted   = sorted(deck.get("sideboard", []), key=lambda c: c["name"])
            if not main_sorted and not sb_sorted:
                console.print("  No cards to delete.")
                continue
            val = ask_escapable("Remove (number, S# for sideboard, or name fragment)")
            if val is _ESCAPE or not val:
                continue
            val = val.strip()

            val_upper = val.upper()

            # ── Numeric: S3 = sideboard slot 3, 3 = main slot 3 ──────────────
            if re.match(r'^S\d+$', val_upper):
                idx = int(val_upper[1:])
                if 1 <= idx <= len(sb_sorted):
                    removed = sb_sorted[idx - 1]["name"]
                    deck["sideboard"] = [c for c in deck["sideboard"] if c["name"] != removed]
                    console.print(f"\n  [green]✓ Removed '{removed}' from sideboard.[/green]")
                else:
                    console.print(f"  [yellow]Sideboard only has {len(sb_sorted)} card(s).[/yellow]")

            elif val.isdigit():
                idx = int(val)
                if 1 <= idx <= len(main_sorted):
                    removed = main_sorted[idx - 1]["name"]
                    deck["cards"] = [c for c in deck["cards"] if c["name"] != removed]
                    console.print(f"\n  [green]✓ Removed '{removed}'.[/green]")
                else:
                    console.print(f"  [yellow]Main deck only has {len(main_sorted)} card(s).[/yellow]")

            # ── Name search across both lists ─────────────────────────────────
            else:
                needle = val.lower()
                main_hits = [(i + 1, c) for i, c in enumerate(main_sorted)
                             if needle in c["name"].lower()]
                sb_hits   = [(i + 1, c) for i, c in enumerate(sb_sorted)
                             if needle in c["name"].lower()]

                all_hits = [("main", i, c) for i, c in main_hits] + \
                           [("sb",   i, c) for i, c in sb_hits]

                if not all_hits:
                    console.print(f"  [yellow]No card found matching '{val}'.[/yellow]")
                elif len(all_hits) == 1:
                    section, _, card = all_hits[0]
                    if section == "main":
                        deck["cards"]     = [c for c in deck["cards"]     if c["name"] != card["name"]]
                        console.print(f"\n  [green]✓ Removed '{card['name']}'.[/green]")
                    else:
                        deck["sideboard"] = [c for c in deck["sideboard"] if c["name"] != card["name"]]
                        console.print(f"\n  [green]✓ Removed '{card['name']}' from sideboard.[/green]")
                else:
                    console.print(f"\n  Multiple matches for '{val}':")
                    for n, (section, slot, card) in enumerate(all_hits, 1):
                        loc = f"main #{slot}" if section == "main" else f"sideboard S{slot}"
                        console.print(f"    [{n}] {card['name']}  [dim]({loc})[/dim]")
                    pick = ask_escapable("Enter number to remove, or ESC/ENTER to cancel")
                    if pick is _ESCAPE or not pick:
                        continue
                    pick = pick.strip()
                    if pick.isdigit() and 1 <= int(pick) <= len(all_hits):
                        section, _, card = all_hits[int(pick) - 1]
                        if section == "main":
                            deck["cards"]     = [c for c in deck["cards"]     if c["name"] != card["name"]]
                        else:
                            deck["sideboard"] = [c for c in deck["sideboard"] if c["name"] != card["name"]]
                        console.print(f"\n  [green]✓ Removed '{card['name']}'.[/green]")

        elif choice == 'M':
            cards_sorted = sorted(deck["cards"], key=lambda c: c["name"])
            if not cards_sorted:
                console.print("  [dim]No cards in deck yet.[/dim]")
                continue
            current = deck.get("commander")
            if current:
                console.print(f"\n  Current commander: [bold yellow]{current}[/bold yellow]")
            console.print("  [dim]Enter a card number, part of a name, ENTER to clear, or ESC to cancel.[/dim]")
            val = ask_escapable("Set commander")
            if val is _ESCAPE:
                continue
            val = (val or "").strip()
            if not val:
                deck["commander"] = None
                console.print("  [dim]Commander cleared.[/dim]")
            elif val.isdigit() and 1 <= int(val) <= len(cards_sorted):
                deck["commander"] = cards_sorted[int(val) - 1]["name"]
                console.print(f"\n  [green]✓ Commander: {deck['commander']}[/green]")
            else:
                matches = [c for c in cards_sorted if val.lower() in c["name"].lower()]
                if len(matches) == 1:
                    deck["commander"] = matches[0]["name"]
                    console.print(f"\n  [green]✓ Commander: {deck['commander']}[/green]")
                elif len(matches) > 1:
                    console.print(f"  [yellow]Multiple matches — be more specific:[/yellow]")
                    for m in matches:
                        console.print(f"    {m['name']}")
                else:
                    console.print(f"  [yellow]No card matching '{val}' found in deck.[/yellow]")

        elif choice == 'F':
            console.print("  [dim]Filter fields: type: text: cmc: color: keyword: — or just a name fragment[/dim]")
            console.print("  [dim]Examples:  type:creature   cmc:>=4   color:b   text:draw   keyword:flying[/dim]")
            q = ask_escapable("Filter query (ENTER to clear, ESC to keep current)")
            if q is _ESCAPE:
                continue  # leave active_filter unchanged
            q = (q or "").strip()
            if q:
                active_filter    = q
                active_filter_db = get_scryfall_db()
            else:
                active_filter    = ""
                active_filter_db = None

        elif choice == 'C':
            db = get_scryfall_db()
            check_deck_against_db(deck, db)

        elif choice == 'T':
            db = get_scryfall_db()
            console.clear()
            show_deck_stats(deck, db)
            ask_escapable("Press ENTER or ESC to return")

        elif choice == 'W':
            path = save_deck(deck)
            console.print(f"\n  [green]✓ Saved: {os.path.basename(path)}[/green]\n")

        elif choice == 'ESC':
            if ask_yn("Save before exiting?", default="y"):
                path = save_deck(deck)
                console.print(f"\n  [green]✓ Saved: {os.path.basename(path)}[/green]\n")
            break

# ─── Card Lookup ──────────────────────────────────────────────────────────────

def print_card(card):
    WIDTH = min(term_width() - 2, 72)
    INNER = WIDTH - 2
    TEXT_W = INNER - 2

    def row(content):
        return f"│{content}│"

    def text_row(text=""):
        return row(f" {text:<{TEXT_W}} ")

    def mid_divider():
        return f"├{'─' * INNER}┤"

    # Gather fields
    name      = card.get("name", "Unknown")
    mana      = card.get("mana_cost", "")
    type_line = card.get("type_line", "")
    oracle    = card.get("oracle_text", "")

    if "card_faces" in card:
        faces     = card["card_faces"]
        mana      = " // ".join(f.get("mana_cost", "") for f in faces if f.get("mana_cost"))
        type_line = " // ".join(f.get("type_line", "") for f in faces)
        oracle    = "\n\n".join(f.get("oracle_text", "") for f in faces)

    power    = card.get("power")
    toughness = card.get("toughness")
    loyalty  = card.get("loyalty")
    rarity   = card.get("rarity", "").capitalize()
    set_name = card.get("set_name", "")

    lines = []

    # Top border
    lines.append(f"┌{'─' * INNER}┐")

    # Name (left) + mana cost (right)
    mana_part = f"{mana} " if mana else " "
    name_w    = INNER - len(mana_part) - 1
    lines.append(row(f" {name[:name_w]:<{name_w}}{mana_part}"))

    # Image box
    img_inner = INNER - 4  # 54 chars inside the art border
    lines.append(mid_divider())
    lines.append(row(f" ┌{'─' * img_inner}┐ "))
    for _ in range(5):
        lines.append(row(f" │{' ' * img_inner}│ "))
    lines.append(row(f" └{'─' * img_inner}┘ "))

    # Type line
    lines.append(mid_divider())
    lines.append(text_row(type_line))

    # Oracle text
    lines.append(mid_divider())
    lines.append(text_row())
    if oracle:
        for para in oracle.split("\n"):
            if para.strip():
                for wrapped in textwrap.wrap(para, width=TEXT_W):
                    lines.append(text_row(wrapped))
            else:
                lines.append(text_row())
    lines.append(text_row())

    # Bottom bar: rarity • set (left) and P/T or loyalty (right)
    lines.append(mid_divider())
    if power is not None and toughness is not None:
        pt = f"{power}/{toughness}"
    elif loyalty:
        pt = f"[{loyalty}]"
    else:
        pt = ""
    pt_part      = f"{pt} " if pt else " "
    bottom_left_w = INNER - len(pt_part) - 1
    bottom_left  = f"{rarity} • {set_name}" if set_name else rarity
    lines.append(row(f" {bottom_left[:bottom_left_w]:<{bottom_left_w}}{pt_part}"))

    # Bottom border
    lines.append(f"└{'─' * INNER}┘")

    print()
    print("\n".join(lines))
    print()

def run_card_lookup():
    header("Card Lookup")
    db = get_scryfall_db()

    while True:
        name = ask_escapable("Card name (ESC or ENTER to go back)")
        if name is _ESCAPE or not name:
            break

        card = db.get(name.lower())

        if card is None and "//" in name:
            front = name.split("//")[0].strip()
            card = db.get(front.lower())

        if card is None:
            close = difflib.get_close_matches(name.lower(), list(db.keys()), n=3, cutoff=0.6)
            if close:
                print(f"\n  '{name}' not found. Did you mean:")
                for i, c in enumerate(close):
                    print(f"    [{i+1}] {db[c]['name']}")
                val = ask_escapable("Enter number to select, or ESC/ENTER to skip")
                if val is _ESCAPE or not val:
                    continue
                if val.isdigit() and 1 <= int(val) <= len(close):
                    card = db[close[int(val) - 1]]
            else:
                print(f"  No match found for '{name}'.\n")
                continue

        if card:
            print_card(card)

# ─── Collection Enhancer Pipeline ─────────────────────────────────────────────

def find_card_lists():
    patterns = [
        os.path.join(DOWNLOADS, "*.csv"),
        os.path.join(DOWNLOADS, "*.xlsx"),
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    files.sort(key=os.path.getmtime, reverse=True)
    return files

def pick_card_list():
    header("Step 1 — Card List")
    files = find_card_lists()

    if not files:
        print(f"\n  No .csv or .xlsx files found in {DOWNLOADS}.")
        path = ask_escapable("Enter full path to your card list")
        if path is _ESCAPE or not path:
            return None
        if not os.path.exists(path):
            print("  File not found. Returning to menu.")
            return None
        return path

    if len(files) == 1:
        f = files[0]
        print(f"\n  Found: {os.path.basename(f)}")
        confirm = ask_yn("Use this file?")
        if confirm is None:   # ESC
            return None
        if confirm:
            return f
        path = ask_escapable("Enter full path to your card list (ESC to cancel)")
        if path is _ESCAPE:
            return None
        return path

    labels = [f"{os.path.basename(f)}  ({_mod_date(f)})" for f in files[:10]]
    idx = ask_choice("Multiple files found in Downloads — which one?", files[:10], labels, cancellable=True)
    if idx is None:
        return None
    return files[idx]

def _mod_date(path):
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

def load_spreadsheet(path):
    if path.endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_excel(path)

def preview_and_pick_column(df):
    header("Step 2 — Name Column")
    candidates = [c for c in df.columns if any(k in c.strip().lower() for k in ["name", "card", "title"])]
    auto = candidates[0] if candidates else df.columns[0]

    preview_cols = list(df.columns[:5])
    print(f"\n  Preview (first 5 rows):\n")
    preview = df[preview_cols].head(5).fillna("")
    col_widths = [max(len(str(c)), preview[c].astype(str).str.len().max()) for c in preview_cols]
    col_widths = [min(w, 30) for w in col_widths]
    print("  " + "  ".join(str(c).ljust(w) for c, w in zip(preview_cols, col_widths)))
    print("  " + "  ".join("─" * w for w in col_widths))
    for _, row in preview.iterrows():
        print("  " + "  ".join(str(row[c])[:w].ljust(w) for c, w in zip(preview_cols, col_widths)))

    print(f"\n  Detected name column: '{auto}'")
    confirm = ask_yn("Is this correct?")
    if confirm is None:   # ESC
        return None
    if confirm:
        return auto

    print("\n  All columns:")
    for i, col in enumerate(df.columns):
        print(f"    [{i+1}] {col}")
    while True:
        val = ask_escapable("Enter column number or name (ESC to cancel)")
        if val is _ESCAPE or not val:
            return None
        if val.isdigit() and 1 <= int(val) <= len(df.columns):
            return df.columns[int(val) - 1]
        if val in df.columns:
            return val
        print("  Column not found, try again.")

def find_scryfall_json():
    patterns = [
        os.path.join(SCRIPT_DIR, "oracle-cards*.json"),
        os.path.join(SCRIPT_DIR, "*.json"),
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    files = list(set(files))
    files.sort(key=os.path.getmtime, reverse=True)

    if not files:
        console.print(f"\n  [red]No Scryfall JSON found in {SCRIPT_DIR}[/red]")
        console.print("  Download 'Oracle Cards' from: https://scryfall.com/docs/api/bulk-data")
        console.print("  Then place the .json file in this folder and run again.")
        sys.exit(1)

    if len(files) == 1:
        return files[0]

    # Multiple files — ask which one to use
    labels = [f"{os.path.basename(f)}  ({os.path.getsize(f)//1024//1024} MB)" for f in files]
    idx = ask_choice("Multiple Scryfall JSON files found — which one?", files, labels, cancellable=True)
    if idx is None:
        console.print("  [dim]Cancelled.[/dim]")
        sys.exit(0)
    return files[idx]

def load_scryfall_db(json_path):
    print(f"\n  Loading Scryfall database...")
    with open(json_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    db = {}
    for card in cards:
        name = card.get("name", "").strip().lower()
        if name:
            db[name] = card
    print(f"  Loaded {len(db):,} unique cards.")
    return db

def pick_export_mode():
    header("Step 4 — Export Mode")
    idx = ask_choice(
        "Which export type?",
        ["deckbuilding", "full"],
        [
            "Deckbuilding  — clean, focused columns (CMC, type, oracle text, legalities)",
            "Full Scryfall — all available fields (set, rarity, prices, URIs, etc.)",
        ],
        cancellable=True,
    )
    if idx is None:
        return None
    return ["deckbuilding", "full"][idx]

def pick_output_name(input_path, mode):
    header("Step 5 — Output Filename")
    default_stem = os.path.splitext(os.path.basename(input_path))[0]
    date_stamp = datetime.now().strftime("%Y%m%d")
    print(f"\n  Output will be saved to: {DOWNLOADS}")
    print(f"  Date stamp '{date_stamp}' will be appended automatically.")
    stem = ask_escapable("Name your output file (no extension, ESC to cancel)", default=default_stem)
    if stem is _ESCAPE:
        return None
    stem = stem or default_stem
    filename = f"{stem}_{mode}_{date_stamp}.xlsx"
    full_path = os.path.join(DOWNLOADS, filename)
    print(f"\n  Will save as: {filename}")
    return full_path

def extract_fields(card):
    if card is None:
        return {
            "scryfall_name": None, "mana_cost": None, "cmc": None,
            "type_line": None, "oracle_text": None, "power": None,
            "toughness": None, "loyalty": None, "colors": None,
            "color_identity": None, "keywords": None, "rarity": None,
            "set_name": None, "legalities_standard": None,
            "legalities_commander": None, "legalities_modern": None,
            "scryfall_uri": None, "error": "Not found",
        }

    if "card_faces" in card:
        face = card["card_faces"][0]
        oracle_text = " // ".join(f.get("oracle_text", "") for f in card["card_faces"])
        mana_cost = " // ".join(f.get("mana_cost", "") for f in card["card_faces"] if f.get("mana_cost"))
        type_line = " // ".join(f.get("type_line", "") for f in card["card_faces"])
        power, toughness, loyalty = face.get("power"), face.get("toughness"), face.get("loyalty")
    else:
        oracle_text = card.get("oracle_text", "")
        mana_cost = card.get("mana_cost", "")
        type_line = card.get("type_line", "")
        power, toughness, loyalty = card.get("power"), card.get("toughness"), card.get("loyalty")

    legalities = card.get("legalities", {})
    return {
        "scryfall_name": card.get("name"),
        "mana_cost": mana_cost,
        "cmc": card.get("cmc"),
        "type_line": type_line,
        "oracle_text": oracle_text,
        "power": power,
        "toughness": toughness,
        "loyalty": loyalty,
        "colors": ", ".join(card.get("colors", [])),
        "color_identity": ", ".join(card.get("color_identity", [])),
        "keywords": ", ".join(card.get("keywords", [])),
        "rarity": card.get("rarity"),
        "set_name": card.get("set_name"),
        "legalities_standard": legalities.get("standard"),
        "legalities_commander": legalities.get("commander"),
        "legalities_modern": legalities.get("modern"),
        "scryfall_uri": card.get("scryfall_uri"),
        "error": None,
    }

def run_pipeline(df, name_col, db):
    header("Running Pipeline")
    print()
    results = []
    not_found_names = []
    fuzzy_matches = []
    blank_rows = 0
    total = len(df)
    db_keys = list(db.keys())

    for i, card_name in enumerate(df[name_col], start=1):
        if pd.isna(card_name) or str(card_name).strip() == "":
            blank_rows += 1
            results.append(extract_fields(None))
            continue

        card_name = str(card_name).strip()
        card = db.get(card_name.lower())
        if card is None and "//" in card_name:
            front = card_name.split("//")[0].strip()
            card = db.get(front.lower())
        if card is None:
            close = difflib.get_close_matches(card_name.lower(), db_keys, n=1, cutoff=0.85)
            if close:
                card = db[close[0]]
                fuzzy_matches.append((card_name, card["name"]))

        fields = extract_fields(card)
        if fields["scryfall_name"] is None:
            not_found_names.append(card_name)
        bar_filled = int((i / total) * 30)
        bar = "█" * bar_filled + "░" * (30 - bar_filled)
        print(f"\r  [{bar}] {i}/{total}  {card_name[:30]:<30}", end="", flush=True)
        results.append(fields)

    print()
    return results, not_found_names, blank_rows, fuzzy_matches

def build_output(df, results, mode, output_path):
    enriched = pd.concat([df.reset_index(drop=True), pd.DataFrame(results)], axis=1)

    if mode == "deckbuilding":
        out = enriched[enriched["error"].isna()].copy() if "error" in enriched.columns else enriched.copy()
        available = [c for c in DECKBUILDING_COLUMNS if c in out.columns]
        out = out[available].copy()
        out.rename(columns=DECKBUILDING_RENAME, inplace=True)
        sort_cols = [c for c in ["CMC", "Name"] if c in out.columns]
        if sort_cols:
            out.sort_values(sort_cols, inplace=True, ignore_index=True)
        for col in ["Commander Legal", "Modern Legal", "Standard Legal"]:
            if col in out.columns:
                out[col] = out[col].str.capitalize()
    else:
        out = enriched.copy()

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="Collection")
        ws = writer.sheets["Collection"]
        for col_cells in ws.columns:
            max_len = max(
                (len(str(cell.value)) if cell.value is not None else 0 for cell in col_cells),
                default=0
            )
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 60)
        ws.freeze_panes = "A2"

    return out

def print_summary(df, results, output_path, mode, not_found_names=None, blank_rows=0, fuzzy_matches=None):
    header("Summary")
    found = sum(1 for r in results if r.get("error") is None)
    not_found_count = len(not_found_names) if not_found_names else 0
    fuzzy_count = len(fuzzy_matches) if fuzzy_matches else 0
    print(f"\n  Cards matched:   {found}")
    if fuzzy_count:
        print(f"  Auto-corrected:  {fuzzy_count}")
    print(f"  Not found:       {not_found_count}")
    if blank_rows:
        print(f"  Blank rows:      {blank_rows}  (skipped)")
    print(f"  Export mode:     {mode}")
    print(f"\n  Saved to: {output_path}")

    type_col = next((c for c in ["type_line", "Type"] if c in df.columns), None)
    if type_col:
        types = df[type_col].dropna().str.split("—").str[0].str.strip().value_counts()
        max_count = types.iloc[0] if len(types) else 1
        total_types = types.sum()
        print(f"\n  Top card types:")
        for t, count in types.head(8).items():
            bar = "█" * round(count / max_count * 20)
            pct = round(count / total_types * 100)
            print(f"    {t:<30} {count:>4}  {bar:<20}  {pct:>3}%")

    ci_col = next((c for c in ["color_identity", "Color Identity"] if c in df.columns), None)
    if ci_col:
        ci = df[ci_col].fillna("Colorless").value_counts()
        max_count = ci.iloc[0] if len(ci) else 1
        total_ci = ci.sum()
        print(f"\n  Color identity breakdown:")
        for c, count in ci.head(8).items():
            label = c if c else "Colorless"
            bar = "█" * round(count / max_count * 20)
            pct = round(count / total_ci * 100)
            print(f"    {label:<30} {count:>4}  {bar:<20}  {pct:>3}%")

    if fuzzy_matches:
        print(f"\n  Auto-corrected ({len(fuzzy_matches)}):")
        for original, matched in fuzzy_matches:
            print(f"    ~  \"{original}\"  →  {matched}")

    if not_found_names:
        print(f"\n  Cards not found in Scryfall ({len(not_found_names)}):")
        for name in sorted(not_found_names):
            print(f"    ✗  {name}")

    divider()
    print()

def pipeline_interactive_fixes(not_found_names, db, db_keys):
    """
    After the pipeline run, show fuzzy suggestions for each unmatched card.
    Returns a corrections dict: {original_name: matched_db_card}.
    """
    if not not_found_names:
        return {}

    console.print(f"\n  [bold]{len(not_found_names)} card(s) not found — searching for close matches...[/bold]\n")
    corrections = {}

    for name in not_found_names:
        close = difflib.get_close_matches(name.lower(), db_keys, n=3, cutoff=0.6)
        if not close:
            console.print(f"  [dim]✗  '{name}' — no suggestions.[/dim]")
            continue
        console.print(f"\n  [yellow]?[/yellow]  '{name}'. Did you mean:")
        for i, c in enumerate(close, 1):
            console.print(f"      [{i}] {db[c]['name']}")
        val = ask_escapable("Enter number to use, or ESC/ENTER to skip")
        if val is _ESCAPE or not val:
            console.print(f"  [dim]  Skipped.[/dim]")
            continue
        if val.isdigit() and 1 <= int(val) <= len(close):
            card = db[close[int(val) - 1]]
            console.print(f"  [green]✓  Using: {card['name']}[/green]")
            corrections[name] = card
        else:
            console.print(f"  [dim]  Skipped.[/dim]")

    return corrections


def apply_pipeline_corrections(df, name_col, results, corrections):
    """Patch a results list in-place using a {original_name: db_card} corrections dict."""
    for i, raw_name in enumerate(df[name_col]):
        if pd.isna(raw_name):
            continue
        name = str(raw_name).strip()
        if name in corrections:
            results[i] = extract_fields(corrections[name])
    return results


def run_collection_pipeline():
    card_list_path = pick_card_list()
    if not card_list_path:
        console.print("  [dim]Pipeline cancelled.[/dim]")
        return

    df = load_spreadsheet(card_list_path)
    name_col = preview_and_pick_column(df)
    if name_col is None:
        console.print("  [dim]Pipeline cancelled.[/dim]")
        return
    print(f"\n  Name column: '{name_col}'  ({len(df)} cards total)")

    db = get_scryfall_db()
    mode = pick_export_mode()
    if mode is None:
        console.print("  [dim]Pipeline cancelled.[/dim]")
        return

    output_path = pick_output_name(card_list_path, mode)
    if output_path is None:
        console.print("  [dim]Pipeline cancelled.[/dim]")
        return

    print()
    divider()
    print(f"  Ready to run!")
    print(f"  Input:  {os.path.basename(card_list_path)}  ({len(df)} cards)")
    print(f"  Mode:   {mode}")
    print(f"  Output: {os.path.basename(output_path)}")
    divider()
    print()
    yn = ask_yn("Start the pipeline?")
    if yn is None or not yn:
        console.print("  [dim]Pipeline cancelled.[/dim]")
        return

    results, not_found_names, blank_rows, fuzzy_matches = run_pipeline(df, name_col, db)
    out_df = build_output(df, results, mode, output_path)
    print_summary(out_df, results, output_path, mode, not_found_names=not_found_names, blank_rows=blank_rows, fuzzy_matches=fuzzy_matches)

    # Interactive fix pass for unmatched cards
    if not_found_names:
        db_keys = list(db.keys())
        corrections = pipeline_interactive_fixes(not_found_names, db, db_keys)
        if corrections:
            console.print(f"\n  Rebuilding output with {len(corrections)} correction(s)...")
            results = apply_pipeline_corrections(df, name_col, results, corrections)
            out_df  = build_output(df, results, mode, output_path)
            console.print(f"  [green]✓ Output updated: {os.path.basename(output_path)}[/green]\n")

# ─── Main Menu ────────────────────────────────────────────────────────────────

def main():
    # Session state: shared across the app (in-memory, not persisted)
    session_state = SessionState()

    # Define main menu items
    main_menu_items = [
        MenuItem("search", "Search Cards", "Browse and search the card database"),
        MenuItem("pinned", "Pinned Cards", "View cards pinned this session"),
        MenuItem("deck", "Deck Manager", "Create and manage decks"),
        MenuItem("lookup", "Card Lookup", "Look up individual cards"),
        MenuItem("pipeline", "Collection Enhancer", "Enrich spreadsheets with card data"),
        MenuItem("quit", "Quit", "Exit the application"),
    ]

    while True:
        console.print()
        console.print(Panel(
            "[bold yellow]MTG Terminal Builder[/bold yellow]  🃏",
            style="bold cyan",
            box=box.DOUBLE,
            expand=False,
            padding=(0, 4),
        ))
        console.print()

        choice = ask_choice_interactive(
            "What would you like to do?",
            main_menu_items,
        )

        print()

        if choice is None:
            # User cancelled
            continue

        if choice.key == "search":
            # Search Cards
            try:
                db = get_scryfall_db()
                run_card_search_view(db, session_state)
            except Exception as e:
                print(f"  ✗ Error in search view: {e}")
                import traceback
                traceback.print_exc()
            # Always clear and return to menu
            print("\n  Returning to menu...\n")

        elif choice.key == "pinned":
            # Pinned Cards
            run_pinned_cards_view(session_state)
            print()

        elif choice.key == "deck":
            run_deck_manager()

        elif choice.key == "lookup":
            run_card_lookup()

        elif choice.key == "pipeline":
            run_collection_pipeline()

        elif choice.key == "quit":
            print("  Bye!\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
