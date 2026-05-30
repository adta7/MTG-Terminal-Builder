"""
search.py — Pure card search logic for MTG Terminal.

Search functions that query the Scryfall database and return ranked results.
No UI code here — just data logic.
"""

from typing import List, Dict, Any, Optional


def search_cards(
    query: str,
    scryfall_db: Dict[str, Dict[str, Any]],
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search for cards by name using ranked matching.

    Search ranking (collects from each tier, sorts within tier):
    1. Exact name match (case-insensitive) — score 1.0
    2. Prefix match (card name starts with query) — score 0.9
    3. Contains match (query appears anywhere in name) — score 0.8
    4. Fuzzy match (difflib similarity) — score 0.7

    Args:
        query: Search string (e.g., "blood")
        scryfall_db: Scryfall card database (name -> card data)
        limit: Max number of results to return

    Returns:
        List of card dicts, ranked by match quality. Each card has 'name', 'mana_cost',
        'type_line', 'oracle_text', 'colors', etc. from Scryfall.
    """
    if not query or not query.strip():
        return []

    query = query.strip().lower()
    results = []

    # Collect all matches with scores (don't stop after first tier)

    # 1. Exact match
    for card_name, card_data in scryfall_db.items():
        if card_name.lower() == query:
            results.append((card_data, 1.0))

    # 2. Prefix match (starts with query)
    for card_name, card_data in scryfall_db.items():
        if card_name.lower().startswith(query) and card_name.lower() != query:
            results.append((card_data, 0.9))

    # 3. Contains match (query appears anywhere)
    for card_name, card_data in scryfall_db.items():
        if query in card_name.lower() and not card_name.lower().startswith(query) and card_name.lower() != query:
            results.append((card_data, 0.8))

    # 4. Fuzzy match (difflib)
    if not results:  # Only do fuzzy if we have no other matches
        import difflib

        card_names = list(scryfall_db.keys())
        close_matches = difflib.get_close_matches(
            query, [name.lower() for name in card_names], n=limit, cutoff=0.6
        )

        for match_lower in close_matches:
            for card_name in card_names:
                if card_name.lower() == match_lower:
                    results.append((scryfall_db[card_name], 0.7))
                    break

    # Sort by score (descending), then by name (ascending)
    results.sort(key=lambda x: (-x[1], x[0].get("name", "")))

    return [card for card, _ in results[:limit]]


def search_by_tag(
    tag: str,
    scryfall_db: Dict[str, Dict[str, Any]],
    tags_map: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Search cards by role/tag (requires tag data).

    Placeholder for future tag-based search.

    Args:
        tag: Tag name (e.g., "draw", "ramp", "removal")
        scryfall_db: Card database
        tags_map: Optional map of card_name -> {tag: score}

    Returns:
        List of cards with that tag, sorted by score.
    """
    if not tags_map:
        return []

    results = []
    for card_name, card_tags in tags_map.items():
        if tag.lower() in card_tags:
            if card_name in scryfall_db:
                score = card_tags[tag.lower()]
                results.append((scryfall_db[card_name], score))

    results.sort(key=lambda x: x[1], reverse=True)
    return [card for card, _ in results]
