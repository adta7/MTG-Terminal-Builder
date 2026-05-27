"""
analyzer.py — Phase 1: Static deck analysis.

Pure functions for computing deck statistics:
- Card counts and mana curve
- Type breakdown
- Color identity
- Land count
- Average mana value
- No AI, no suggestions — just facts.
"""

from collections import defaultdict
from .models import Deck, DeckAnalysis
from .database import Database


def analyze_deck(deck: Deck, db: Database) -> DeckAnalysis:
    """
    Analyze a deck's structure and composition.

    Returns:
        DeckAnalysis object with all computed statistics
    """
    # Count cards by type
    total_cards = deck.main_deck_count()
    land_count = 0
    spell_permanent_count = 0  # creatures, enchantments, artifacts, planeswalkers
    spell_nonpermanent_count = 0  # instants, sorceries
    mana_curve = defaultdict(int)  # cmc → count
    type_counts = defaultdict(int)  # type → count
    colors_set = set()

    for card_entry in deck.cards:
        card = db.card_by_name(card_entry.name)
        if not card:
            continue

        count = card_entry.count

        # Categorize: Land vs Spell, and Permanent vs NonPermanent
        if "Land" in card.type_line:
            land_count += count
            type_counts["Land"] += count
        elif "Instant" in card.type_line:
            spell_nonpermanent_count += count
            type_counts["Instant"] += count
        elif "Sorcery" in card.type_line:
            spell_nonpermanent_count += count
            type_counts["Sorcery"] += count
        else:
            # Everything else that's not Land/Instant/Sorcery is a permanent
            spell_permanent_count += count
            # Determine primary type for type breakdown
            primary_type = _extract_primary_type(card.type_line)
            type_counts[primary_type] += count

        # Build mana curve (spells only, not lands)
        if "Land" not in card.type_line:
            cmc = min(card.cmc, 7)  # Bucket 7+ as "7"
            mana_curve[cmc] += count

        # Track colors
        colors_set.update(card.color_identity)

    # Compute average mana value (spells only, not lands)
    spell_count = spell_permanent_count + spell_nonpermanent_count
    avg_mv = 0.0
    if spell_count > 0:
        total_mv = sum(
            db.card_by_name(c.name).cmc * c.count
            for c in deck.cards
            if db.card_by_name(c.name) and "Land" not in db.card_by_name(c.name).type_line
        )
        avg_mv = total_mv / spell_count

    # Format mana curve as dict (0-7+)
    curve_formatted = {}
    for i in range(8):
        if i in mana_curve:
            curve_formatted[i] = mana_curve[i]

    # Warnings
    warnings = []
    if total_cards != 100:
        warnings.append(f"Deck has {total_cards} cards (expected 100)")
    if not deck.commander:
        warnings.append("No commander specified")
    if land_count < 33:
        warnings.append(f"Only {land_count} lands (typically 35-37)")
    if land_count > 40:
        warnings.append(f"Too many lands: {land_count} (typically 35-37)")

    return DeckAnalysis(
        deck_name=deck.name,
        total_cards=total_cards,
        land_count=land_count,
        spell_permanent_count=spell_permanent_count,
        spell_nonpermanent_count=spell_nonpermanent_count,
        avg_mana_value=avg_mv,
        mana_curve=curve_formatted,
        type_counts=dict(type_counts),
        color_identity=sorted(colors_set),
        warnings=warnings,
    )


def filter_deck(deck: Deck, db: Database, query: str) -> list:
    """
    Filter deck cards by query.

    Syntax:
      type:creature         — cards containing "creature" in type line
      text:draw             — cards containing "draw" in oracle text
      cmc:3                 — exactly 3 mana cost
      cmc:>=4               — 4 or more
      cmc:<2                — less than 2
      color:b               — contains black in color identity
      color:colorless       — colorless
      color:multicolor      — more than one color
      keyword:flying        — has flying keyword
      name:bolt             — card name contains "bolt"

    Returns:
        List of (card_entry, card_obj) tuples matching the query
    """
    results = []

    for card_entry in deck.cards:
        card = db.card_by_name(card_entry.name)
        if not card:
            continue

        if _matches_query(card, query):
            results.append((card_entry, card))

    return results


def _matches_query(card, query: str) -> bool:
    """Check if a card matches a filter query."""
    query = query.strip().lower()

    # Handle field:value syntax
    if ":" in query:
        field, value = query.split(":", 1)
        field = field.strip().lower()
        value = value.strip().lower()

        if field == "type":
            return value in card.type_line.lower()

        if field == "text":
            return value in card.oracle_text.lower()

        if field == "cmc":
            return _matches_cmc(card.cmc, value)

        if field == "color":
            return _matches_color(card.color_identity, value)

        if field == "keyword":
            return any(value in kw.lower() for kw in card.keywords)

        if field == "name":
            return value in card.name.lower()

    # Default: search card name
    return query in card.name.lower()


def _matches_cmc(cmc: int, condition: str) -> bool:
    """Check if CMC matches condition (3, >=4, <2, etc.)."""
    if condition.startswith(">="):
        return cmc >= int(condition[2:])
    if condition.startswith("<="):
        return cmc <= int(condition[2:])
    if condition.startswith(">"):
        return cmc > int(condition[1:])
    if condition.startswith("<"):
        return cmc < int(condition[1:])
    return cmc == int(condition)


def _matches_color(color_identity: list, condition: str) -> bool:
    """Check if card matches color condition."""
    if condition == "colorless":
        return len(color_identity) == 0
    if condition == "multicolor":
        return len(color_identity) > 1
    # Single color: check if color is in identity
    return condition.upper() in color_identity


def _extract_primary_type(type_line: str) -> str:
    """
    Extract the primary type from a card's type line.

    Examples:
      "Creature — Vampire" → "Creature"
      "Legendary Creature — Vampire" → "Creature"
      "Artifact Creature — Golem" → "Creature"
      "Enchantment — Aura" → "Enchantment"
      "Planeswalker — Jace" → "Planeswalker"
    """
    main_part = type_line.split("—")[0].strip()  # Get before the dash

    # Check for primary types in order of specificity
    for primary_type in ["Planeswalker", "Creature", "Enchantment", "Artifact"]:
        if primary_type in main_part:
            return primary_type

    return "Other"
