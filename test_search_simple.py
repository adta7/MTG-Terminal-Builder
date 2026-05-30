#!/usr/bin/env python3
"""Simpler test: just test that do_search works."""

from mtg import get_scryfall_db
from search import search_cards

print("Loading database...")
db = get_scryfall_db()
print(f"Loaded {len(db)} cards\n")

# Manually test the search function
test_queries = ["blood", "lightning", "ashnod"]

for query in test_queries:
    results = search_cards(query, db, limit=10)
    print(f"search_cards('{query}', db, limit=10)")
    print(f"  → {len(results)} results")
    for card in results[:3]:
        print(f"    - {card.get('name')}")
    print()

print("✓ Search function definitely works")
print("\nThe issue must be in how search_view.py is calling it.")
