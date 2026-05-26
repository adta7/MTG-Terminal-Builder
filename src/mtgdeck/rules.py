"""
rules.py — Deterministic Commander legality validation.

Checks:
- 100 card deck size (including commander)
- Exactly 1 commander
- No duplicate cards (except basic lands)
- All cards legal in Commander format
- Color identity within commander's color identity
"""

from typing import List

from .models import Card, Deck
from .database import Database


def validate_commander_deck(deck: Deck, db: Database) -> List[str]:
    """
    Validate a deck against Commander rules.

    Returns:
        List of violation messages (empty if valid)
    """
    violations = []

    # Check deck size
    total = deck.main_deck_count()
    if total != 100:
        violations.append(f"Deck has {total} cards, must be 100 (including commander)")

    # Check commander
    if not deck.commander:
        violations.append("No commander specified")
    else:
        commander_card = db.card_by_name(deck.commander)
        if not commander_card:
            violations.append(f"Commander '{deck.commander}' not found in database")
        elif not is_card_legal_in_format(commander_card, "commander"):
            violations.append(f"Commander '{deck.commander}' is not legal in Commander")

        # Check color identity
        if commander_card:
            commander_colors = set(commander_card.color_identity)
            for card in deck.cards:
                card_obj = db.card_by_name(card.name)
                if card_obj:
                    card_colors = set(card_obj.color_identity)
                    if not card_colors.issubset(commander_colors):
                        diff = card_colors - commander_colors
                        violations.append(
                            f"'{card.name}' has color identity {diff} "
                            f"outside commander's {commander_colors}"
                        )

    # Check for duplicates (except basic lands)
    seen = {}
    for card in deck.cards:
        card_obj = db.card_by_name(card.name)
        if card_obj and card_obj.is_basic_land():
            continue  # Basic lands unlimited
        key = card.name.lower()
        if key in seen:
            violations.append(
                f"'{card.name}' appears {seen[key] + card.count} times "
                f"(max 1 in Commander, except basic lands)"
            )
        else:
            seen[key] = card.count

    # Check legality
    for card in deck.cards:
        card_obj = db.card_by_name(card.name)
        if card_obj and not is_card_legal_in_format(card_obj, "commander"):
            violations.append(f"'{card.name}' is not legal in Commander format")

    return violations


def is_card_legal_in_format(card: Card, format_name: str) -> bool:
    """Check if a card is legal in a given format."""
    key = f"legality_{format_name}".lower()
    legality = card.legalities.get(format_name, "legal")
    return legality in ("legal", "restricted")


def get_color_identity(card: Card) -> set[str]:
    """Extract color identity from a card."""
    return set(card.color_identity)
