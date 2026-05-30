#!/usr/bin/env python3
"""Test script for the interactive card search view."""

from mtg import get_scryfall_db
from search_view import run_card_search_view

if __name__ == "__main__":
    print("Loading Scryfall database...")
    db = get_scryfall_db()
    print(f"✓ Loaded {len(db)} cards\n")

    print("Starting card search view...")
    print("(Press any key to begin)\n")
    input()

    result = run_card_search_view(db)

    if result:
        print(f"\nSelected card: {result.get('name', 'Unknown')}")
    else:
        print("\nSearch cancelled.")
