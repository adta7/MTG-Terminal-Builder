"""
mtg.py — MTG Terminal Builder
Interactive terminal tool for Magic: The Gathering deck building and collection management.

Usage:
    python3 mtg.py
"""

import os
import sys
import json
import glob
import difflib
import subprocess
import textwrap
import tty
import termios
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
from rich.live import Live
from rich import box

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
    hint = "Y/n" if default == "y" else "y/N"
    try:
        val = input(f"  {prompt} ({hint}): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\nAborted.")
        sys.exit(0)
    if not val:
        return default == "y"
    return val.startswith("y")

def ask_choice(prompt, options, labels=None):
    print(f"\n  {prompt}")
    for i, opt in enumerate(options):
        label = labels[i] if labels else opt
        print(f"    [{i+1}] {label}")
    while True:
        try:
            val = input("  Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAborted.")
            sys.exit(0)
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

def parse_card_list(lines):
    cards = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[0].isdigit():
            cards.append({"name": parts[1].strip(), "count": int(parts[0])})
        else:
            cards.append({"name": line, "count": 1})
    return cards

def import_card_list():
    print("\n  Paste your card list below.")
    print("  Format: '4 Lightning Bolt' (one card per line)")
    print("  Type END on a new line when done.\n")
    lines = []
    while True:
        try:
            line = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAborted.")
            sys.exit(0)
        if line.upper() == "END":
            break
        lines.append(line)
    return parse_card_list(lines)

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
    """Read a single keypress without requiring Enter. Handles arrow keys."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.buffer.read(1)
        if ch == b'\x03':
            raise KeyboardInterrupt
        if ch == b'\x1b':
            ch2 = sys.stdin.buffer.read(1)
            ch3 = sys.stdin.buffer.read(1)
            if ch2 == b'[':
                if ch3 == b'A': return 'UP'
                if ch3 == b'B': return 'DOWN'
            return 'ESC'
        return ch.decode('utf-8', errors='replace')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def build_deck_panel(deck, cursor, status=""):
    """Build the interactive deck view as a Rich renderable."""
    cards = sorted(deck["cards"], key=lambda c: c["name"])
    total = sum(c["count"] for c in deck["cards"])

    table = Table.grid(padding=(0, 1))
    table.add_column(width=2)
    table.add_column(width=4, justify="right")
    table.add_column()

    if not cards:
        table.add_row(" ", "", "[dim]No cards yet — press A to add[/dim]")
    else:
        for i, card in enumerate(cards):
            if i == cursor:
                table.add_row(
                    "[bold cyan]▶[/bold cyan]",
                    f"[bold cyan]{card['count']}x[/bold cyan]",
                    f"[bold cyan]{card['name']}[/bold cyan]",
                )
            else:
                table.add_row(" ", f"[dim]{card['count']}x[/dim]", card["name"])

    hints = Text.from_markup(
        "\n [dim]↑↓[/dim] Navigate   "
        "[bold cyan]A[/bold cyan] Add   "
        "[bold red]D[/bold red] Delete   "
        "[bold green]S[/bold green] Save   "
        "[dim]Q[/dim] Quit"
    )

    body = Table.grid()
    body.add_row(Text(""))
    body.add_row(table)
    body.add_row(hints)
    if status:
        body.add_row(Text.from_markup(f"\n [green]✓ {status}[/green]"))
    else:
        body.add_row(Text(""))

    return Panel(
        body,
        title=f"[bold cyan]{deck['name']}[/bold cyan]",
        subtitle=f"[dim]{total} cards[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
    )

def print_deck(deck):
    total = sum(c["count"] for c in deck["cards"])
    header(f"Deck: {deck['name']}  ({total} cards)")
    if not deck["cards"]:
        print("\n  No cards yet.\n")
        return
    print()
    for card in sorted(deck["cards"], key=lambda c: c["name"]):
        print(f"    {card['count']}x  {card['name']}")
    print()

def pick_deck(decks):
    """Show deck list and handle open / copy / delete shortcuts."""
    new_idx = len(decks) + 1

    print(f"\n  Your decks:")
    for i, d in enumerate(decks, start=1):
        print(f"    [{i}] {d['name']}  (edited {d['edited']})")
    print(f"    [{new_idx}] ── Create New Deck ──")
    print()
    print(f"  Shortcuts:  [N] open  [N2] copy to clipboard  [N0] delete")

    while True:
        try:
            val = input("  Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAborted.")
            sys.exit(0)

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
        deck_name = ask("Deck name")
        if not deck_name:
            print("  No name entered. Returning to menu.\n")
            return
        deck = {
            "name": deck_name,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "edited": "",
            "cards": [],
        }
        mode_idx = ask_choice(
            "How do you want to start?",
            ["import", "blank"],
            ["Import from card list", "Start blank"],
        )
        if mode_idx == 0:
            cards = import_card_list()
            deck["cards"] = cards
            total = sum(c["count"] for c in cards)
            print(f"\n  ✓ Imported {total} cards ({len(cards)} unique).")

    # Deck edit loop — keyboard driven
    cursor = 0
    status = ""

    while True:
        cards = sorted(deck["cards"], key=lambda c: c["name"])

        with Live(build_deck_panel(deck, cursor, status), console=console, refresh_per_second=4):
            key = getch()

        status = ""

        if key == 'UP':
            cursor = max(0, cursor - 1)

        elif key == 'DOWN':
            cursor = min(max(len(cards) - 1, 0), cursor + 1)

        elif key in ('a', 'A'):
            console.print()
            new_cards = import_card_list()
            if new_cards:
                deck["cards"] = merge_cards(deck["cards"], new_cards)
                cursor = 0
                status = f"Added {len(new_cards)} card type(s)."

        elif key in ('d', 'D'):
            if cards:
                removed = cards[cursor]["name"]
                deck["cards"] = [c for c in deck["cards"] if c["name"] != removed]
                cursor = min(cursor, max(len(deck["cards"]) - 1, 0))
                status = f"Removed '{removed}'."

        elif key in ('s', 'S'):
            path = save_deck(deck)
            status = f"Saved: {os.path.basename(path)}"
            console.print(build_deck_panel(deck, cursor, status))
            break

        elif key in ('q', 'Q', 'ESC'):
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
        name = ask("Card name (or press ENTER to go back)")
        if not name:
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
                val = ask("Enter number to select, or ENTER to skip")
                if val and val.isdigit() and 1 <= int(val) <= len(close):
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
        path = ask("Enter full path to your card list")
        if not path or not os.path.exists(path):
            print("  File not found. Returning to menu.")
            return None
        return path

    if len(files) == 1:
        f = files[0]
        print(f"\n  Found: {os.path.basename(f)}")
        if ask_yn("Use this file?"):
            return f
        path = ask("Enter full path to your card list")
        return path

    labels = [f"{os.path.basename(f)}  ({_mod_date(f)})" for f in files[:10]]
    idx = ask_choice("Multiple files found in Downloads — which one?", files[:10], labels)
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
    if ask_yn("Is this correct?"):
        return auto

    print("\n  All columns:")
    for i, col in enumerate(df.columns):
        print(f"    [{i+1}] {col}")
    while True:
        val = ask("Enter column number or name")
        if val and val.isdigit() and 1 <= int(val) <= len(df.columns):
            return df.columns[int(val) - 1]
        if val in df.columns:
            return val
        print("  Column not found, try again.")

def find_scryfall_json():
    header("Step 3 — Scryfall Data")
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
        print(f"\n  No Scryfall JSON found in {SCRIPT_DIR}")
        print("  Download 'Oracle Cards' from: https://scryfall.com/docs/api/bulk-data")
        print("  Then place the .json file in this folder and run again.")
        sys.exit(1)

    if len(files) == 1:
        f = files[0]
        size_mb = os.path.getsize(f) / 1024 / 1024
        print(f"\n  Found: {os.path.basename(f)} ({size_mb:.0f} MB)")
        if ask_yn("Use this file?"):
            return f

    labels = [f"{os.path.basename(f)}  ({os.path.getsize(f)//1024//1024} MB)" for f in files]
    idx = ask_choice("Which Scryfall JSON?", files, labels)
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
        ]
    )
    return ["deckbuilding", "full"][idx]

def pick_output_name(input_path, mode):
    header("Step 5 — Output Filename")
    default_stem = os.path.splitext(os.path.basename(input_path))[0]
    date_stamp = datetime.now().strftime("%Y%m%d")
    print(f"\n  Output will be saved to: {DOWNLOADS}")
    print(f"  Date stamp '{date_stamp}' will be appended automatically.")
    stem = ask("Name your output file (no extension)", default=default_stem)
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

def run_collection_pipeline():
    card_list_path = pick_card_list()
    if not card_list_path:
        return

    df = load_spreadsheet(card_list_path)
    name_col = preview_and_pick_column(df)
    print(f"\n  Name column: '{name_col}'  ({len(df)} cards total)")

    db = get_scryfall_db()
    mode = pick_export_mode()
    output_path = pick_output_name(card_list_path, mode)

    print()
    divider()
    print(f"  Ready to run!")
    print(f"  Input:  {os.path.basename(card_list_path)}  ({len(df)} cards)")
    print(f"  Mode:   {mode}")
    print(f"  Output: {os.path.basename(output_path)}")
    divider()
    print()
    if not ask_yn("Start the pipeline?"):
        print("  Cancelled.")
        return

    results, not_found_names, blank_rows, fuzzy_matches = run_pipeline(df, name_col, db)
    out_df = build_output(df, results, mode, output_path)
    print_summary(out_df, results, output_path, mode, not_found_names=not_found_names, blank_rows=blank_rows, fuzzy_matches=fuzzy_matches)

# ─── Main Menu ────────────────────────────────────────────────────────────────

def main():
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

        idx = ask_choice(
            "What would you like to do?",
            ["deck", "lookup", "pipeline", "quit"],
            [
                "Deck Manager",
                "Card Lookup",
                "Collection Enhancer Pipeline",
                "Quit",
            ],
        )

        print()

        if idx == 0:
            run_deck_manager()
        elif idx == 1:
            run_card_lookup()
        elif idx == 2:
            run_collection_pipeline()
        elif idx == 3:
            print("  Bye!\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
