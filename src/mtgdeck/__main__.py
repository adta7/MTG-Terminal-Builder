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

    # Load the old mtg.py for now (until we fully refactor the UI)
    print("  Loading application...\n")
    import mtg
    mtg.main()


def setup():
    """Initialize the database by downloading and indexing Scryfall data."""
    print("\n  MTG Deckbuilding Companion — Setup\n")
    print("  This will download the latest Scryfall card data and build the database.")
    print("  It's a one-time operation (~1-2 minutes).\n")

    try:
        # Find or download Scryfall JSON
        proj_root = Path(__file__).parent.parent.parent
        json_dir = proj_root

        try:
            json_path = find_scryfall_json(str(json_dir))
            print(f"  Found Scryfall JSON: {json_path}\n")
        except FileNotFoundError:
            print("  No local Scryfall JSON found. Downloading...\n")
            json_path = download_scryfall_bulk(str(json_dir / "oracle-cards-latest.json"))

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


if __name__ == "__main__":
    main()
