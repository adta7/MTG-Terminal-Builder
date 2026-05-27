"""
__main__.py — Entry point for MTG deckbuilding companion.

Run with: python -m mtgdeck
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import mtgdeck
sys.path.insert(0, str(Path(__file__).parent.parent))

from mtgdeck.database import Database
from mtgdeck.scryfall import (
    find_scryfall_json,
    download_scryfall_bulk,
    index_cards_into_db,
)
from mtgdeck.analyzer import analyze_deck
from mtgdeck.profiles import (
    count_roles_in_deck,
    compare_to_profile,
    find_profile,
    load_profile,
    CATEGORY_DISPLAY_NAMES,
)
from rich.console import Console

console = Console()


def get_db_path() -> str:
    """Get path to the cards database."""
    proj_root = Path(__file__).parent.parent.parent
    return str(proj_root / "data" / "cards.sqlite")


def main():
    """Main entry point."""
    # Check for 'setup' command
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup()
        return

    # Check if database exists
    db_path = get_db_path()
    if not Path(db_path).exists():
        print("\n  Database not found. Run:")
        print(f"    python -m mtgdeck setup\n")
        print("  to initialize the database.\n")
        sys.exit(1)

    # Phase 1+3: Handle 'analyze' command
    # Usage: python -m mtgdeck analyze <deck_name> [--profile <profile_name>]
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        if len(sys.argv) < 3:
            print("\n  Usage: python -m mtgdeck analyze <deck_name> [--profile <name>]\n")
            sys.exit(1)
        deck_name = sys.argv[2]
        # Parse optional --profile flag
        profile_name = None
        if "--profile" in sys.argv:
            idx = sys.argv.index("--profile")
            if idx + 1 < len(sys.argv):
                profile_name = sys.argv[idx + 1]
            else:
                print("\n  --profile requires a profile name.\n")
                sys.exit(1)
        run_analyzer(db_path, deck_name, profile_name=profile_name)
        return

    # Load the old mtg.py for now (until we fully refactor the UI)
    print("  Loading application...\n")
    import mtg
    mtg.main()


def setup():
    """Initialize the database by downloading and indexing Scryfall data."""
    print("\n  MTG Deckbuilding Companion — Setup\n")
    print("  This will build a database from Scryfall card data.")
    print("  It's a one-time operation (~1-2 minutes).\n")

    try:
        # Find or download Scryfall JSON
        proj_root = Path(__file__).parent.parent.parent
        json_dir = proj_root

        try:
            json_path = find_scryfall_json(str(json_dir))
            print(f"  Found Scryfall JSON: {json_path}\n")
        except FileNotFoundError:
            print("  No local Scryfall JSON found.\n")
            print("  Download from: https://scryfall.com/docs/api/bulk-data")
            print("  (Look for 'Default Cards' and download the .json file)\n")
            print("  Then place it in this directory and run:")
            print("    python -m mtgdeck setup\n")
            sys.exit(1)

        # Initialize database and index cards
        db_path = get_db_path()
        db = Database(db_path)
        db.init_db()
        db.connect()

        count = index_cards_into_db(json_path, db)
        db.close()

        print(f"\n  ✓ Setup complete! Database ready at: {db_path}\n")
        print(f"  Run: python -m mtgdeck\n")

    except Exception as e:
        print(f"\n  ✗ Setup failed: {e}\n")
        sys.exit(1)


def run_analyzer(db_path: str, deck_name: str, profile_name: str | None = None):
    """Phase 1: Analyze a deck."""
    import json
    import glob
    from mtgdeck.models import Deck, DeckCard

    # Find the deck file
    # mtg.py saves decks in ./decks/ (project root), not data/decks/
    proj_root = Path(db_path).parent.parent
    decks_dir = proj_root / "decks"
    deck_files = glob.glob(str(decks_dir / "*.json"))

    deck_file = None
    for f in deck_files:
        with open(f) as fh:
            data = json.load(fh)
        if data.get("name", "").lower() == deck_name.lower():
            deck_file = f
            break

    if not deck_file:
        console.print(f"\n  ✗ Deck '{deck_name}' not found\n")
        sys.exit(1)

    # Load deck
    with open(deck_file) as fh:
        data = json.load(fh)

    cards = [DeckCard(name=c["name"], count=c["count"]) for c in data.get("cards", [])]
    sideboard = [DeckCard(name=c["name"], count=c["count"]) for c in data.get("sideboard", [])]

    deck = Deck(
        name=data["name"],
        cards=cards,
        sideboard=sideboard,
        commander=data.get("commander"),
        created=data.get("created", ""),
        edited=data.get("edited", ""),
    )

    # Analyze — keep db open through profile comparison if needed
    db = Database(db_path)
    db.connect()

    analysis = analyze_deck(deck, db)

    # Print results
    console.print()
    console.print(f"[bold cyan]{analysis.deck_name}[/bold cyan]")
    if deck.commander:
        console.print(f"[dim]Commander: {deck.commander}[/dim]")

    console.print()
    console.print(f"Cards: {analysis.total_cards}/100")
    console.print(f"Lands: {analysis.land_count} | Spell Permanents: {analysis.spell_permanent_count} | Spell NonPermanents: {analysis.spell_nonpermanent_count}")
    console.print(f"Avg Mana Value: {analysis.avg_mana_value:.2f}")
    console.print(f"Color Identity: {', '.join(analysis.color_identity) or 'None'}")

    # Mana curve
    console.print()
    console.print("[bold]Mana Curve:[/bold]")
    for cmc in range(8):
        count = analysis.mana_curve.get(cmc, 0)
        bar = "█" * min(count, 30)
        console.print(f"  {cmc}: {count:2d} {bar}")

    # Type breakdown
    if analysis.type_counts:
        console.print()
        console.print("[bold]Type Breakdown:[/bold]")
        for type_name in sorted(analysis.type_counts.keys()):
            count = analysis.type_counts[type_name]
            console.print(f"  {type_name}: {count}")

    # Warnings
    if analysis.warnings:
        console.print()
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in analysis.warnings:
            console.print(f"  ⚠ {warning}")

    # Phase 3: Profile comparison (only when --profile is given)
    if profile_name:
        _print_profile_comparison(deck, db, analysis, profile_name, db_path)

    console.print()
    db.close()


def _print_profile_comparison(deck, db, analysis, profile_name: str, db_path: str):
    """Print the profile comparison section of the analyze output."""
    proj_root = Path(db_path).parent.parent
    profiles_dir = proj_root / "data" / "profiles"

    try:
        profile_path = find_profile(profile_name, profiles_dir)
        profile = load_profile(profile_path)
    except FileNotFoundError as e:
        console.print(f"\n  [yellow]⚠ {e}[/yellow]")
        return

    role_counts = count_roles_in_deck(deck, db)
    gaps = compare_to_profile(analysis, role_counts, profile)

    console.print()
    console.print(f"[bold]── Profile: {profile.name} {'─' * max(0, 40 - len(profile.name))}[/bold]")
    console.print()

    # Column widths for aligned output
    label_w = max(len(g.display_name) for g in gaps)

    summary_lines = []
    for gap in gaps:
        label = gap.display_name.ljust(label_w)
        # Format actual value: integers without decimal, floats with 1 decimal
        if gap.actual == int(gap.actual):
            actual_str = str(int(gap.actual))
        else:
            actual_str = f"{gap.actual:.2f}"
        actual_str = actual_str.rjust(5)

        if gap.status == "ok":
            icon = "[green]✓[/green]"
            msg  = f"[dim]{gap.message}[/dim]"
        elif gap.status == "low":
            icon = "[yellow]⚠[/yellow]"
            msg  = f"[yellow]{gap.message}[/yellow]"
        else:  # high
            icon = "[cyan]↑[/cyan]"
            msg  = f"[cyan]{gap.message}[/cyan]"

        console.print(f"  {label}  {actual_str}  {icon}  {msg}")
        if gap.status != "ok":
            summary_lines.append(f"{gap.display_name}: {gap.message}")

    if summary_lines:
        console.print()
        console.print("[bold yellow]Profile Gaps:[/bold yellow]")
        for line in summary_lines:
            console.print(f"  ⚠ {line}")


if __name__ == "__main__":
    main()
