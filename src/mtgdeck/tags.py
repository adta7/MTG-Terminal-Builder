"""
tags.py — Phase 2: Five-layer card tagging system.

Tags describe what a card does at five levels of abstraction:

  Layer 1 — Oracle Facts     (automatic from Scryfall — mana cost, type, text)
  Layer 2 — Mechanical       (what the card literally does)
  Layer 3 — Functional       (what role it performs in a deck)
  Layer 4 — Archetype        (what strategies want it)
  Layer 5 — Emotional        (strategic identity — engine, apex threat, fuel, etc.)

Confidence scale (0.0–1.0):
  1.0 = mechanically certain  (oracle text is explicit)
  0.7 = confident             (well-known role, clear pattern)
  0.4 = contextual            (depends on the deck)
  0.1 = speculative

This module:
  - Defines the built-in tag registry (TAGS dict)
  - Seeds the tags table in the database
  - Provides Python wrappers around database tag queries
  - Auto-tags cards from oracle text (mechanical layer only)
"""

import re
from typing import Optional

from .models import Card


# ─── Built-in Tag Registry ─────────────────────────────────────────────────────
#
# Format: (tag_name, layer, description)
# These are the seed tags. Users can add more via db.save_tag() directly.

TAGS: list[tuple[str, str, str]] = [

    # ── Layer 2: Mechanical ──────────────────────────────────────────────────
    # What the card literally does. Derived from oracle text.

    ("Draw_Effect",       "mechanical", "Card draws one or more cards."),
    ("Life_Drain",        "mechanical", "Causes opponents to lose life, typically paired with life gain."),
    ("Life_Gain",         "mechanical", "Causes the controller to gain life."),
    ("Sacrifice_Outlet",  "mechanical", "Allows sacrificing creatures or permanents as a cost or activated ability."),
    ("Token_Generation",  "mechanical", "Creates creature or other tokens."),
    ("Reanimation",       "mechanical", "Returns cards from graveyard to the battlefield."),
    ("Recursion_To_Hand", "mechanical", "Returns cards from graveyard to hand."),
    ("Mana_Multiplier",   "mechanical", "Doubles, multiplies, or scales mana production beyond normal."),
    ("Mana_Production",   "mechanical", "Produces mana (artifacts, creatures, enchantments — not lands)."),
    ("Tutor_Effect",      "mechanical", "Searches library for a specific card."),
    ("Board_Wipe",        "mechanical", "Destroys or exiles most or all creatures/permanents."),
    ("Graveyard_Hate",    "mechanical", "Removes or disrupts cards in graveyards."),
    ("Discard_Effect",    "mechanical", "Forces opponents (or self) to discard cards."),
    ("Self_Mill",         "mechanical", "Puts cards from library into graveyard."),
    ("Cost_Reduction",    "mechanical", "Reduces mana costs of spells or abilities."),
    ("Counter_Spell",     "mechanical", "Counters spells or abilities."),
    ("Death_Trigger",     "mechanical", "Has an ability that triggers when creatures die."),
    ("ETB_Trigger",       "mechanical", "Has an ability that triggers when it or another permanent enters the battlefield."),
    ("Targeted_Removal",  "mechanical", "Destroys or exiles a specific targeted permanent."),
    ("Bounce_Effect",     "mechanical", "Returns permanents to their owner's hand."),
    ("Damage_Effect",     "mechanical", "Deals direct damage to creatures, players, or planeswalkers."),
    ("Protection_Effect", "mechanical", "Grants hexproof, shroud, indestructible, or similar protection."),

    # ── Layer 3: Functional ──────────────────────────────────────────────────
    # What role the card plays in a deck. One card can have multiple functional tags.

    ("Mana_Acceleration", "functional", "Produces more mana than a normal land drop, helping cast spells faster."),
    ("Mana_Engine",       "functional", "Provides repeatable or scaling mana — doubles, scales with board, etc."),
    ("Card_Advantage",    "functional", "Generates card advantage — draws cards, tutors, replaces itself."),
    ("Removal",           "functional", "Eliminates threats — spot removal or board wipes."),
    ("Protection",        "functional", "Shields key cards or the board state from removal."),
    ("Threat",            "functional", "Is itself a threat that demands an answer."),
    ("Finisher",          "functional", "Can directly close out the game when conditions are met."),
    ("Finisher_Support",  "functional", "Enables or powers up finishers without being one itself."),
    ("Engine",            "functional", "Enables the deck's core plan repeatedly."),
    ("Fuel",              "functional", "Provides expendable resources — tokens, creatures, mana — for the engine."),
    ("Payoff",            "functional", "Rewards executing the deck's plan with damage, life, cards, or mana."),
    ("Enabler",           "functional", "Enables key combos, synergies, or plans without being the payoff."),
    ("Recursion",         "functional", "Returns things from the graveyard to hand or battlefield."),
    ("Interaction",       "functional", "Disrupts opponents — counters, removal, stax effects."),
    ("Setup",             "functional", "Sets up future turns — tutors, fetches, digs for pieces."),
    ("Conversion",        "functional", "Converts one resource into another (creatures → mana, life → cards, etc.)."),

    # ── Layer 4: Archetype ───────────────────────────────────────────────────
    # What strategies specifically want this card.

    ("Aristocrats",    "archetype", "Sacrifice-based strategies that exploit creature deaths for value."),
    ("Reanimator",     "archetype", "Strategies that reanimate large creatures from the graveyard."),
    ("Big_Mana",       "archetype", "Strategies that generate large mana pools for X-spells or massive threats."),
    ("Voltron",        "archetype", "Commander damage strategies that buff a single creature."),
    ("Lifegain",       "archetype", "Strategies built around gaining and leveraging life totals."),
    ("Spellslinger",   "archetype", "Strategies that reward casting many instants and sorceries."),
    ("Control",        "archetype", "Reactive strategies that counter and remove threats until winning late."),
    ("Stax",           "archetype", "Resource denial strategies that lock opponents out."),
    ("Tokens",         "archetype", "Strategies that flood the board with tokens."),
    ("Graveyard",      "archetype", "Strategies that use the graveyard as a resource."),
    ("Devotion",       "archetype", "Strategies that benefit from many colored mana symbols on permanents."),
    ("Blink",          "archetype", "Strategies that exploit enters-the-battlefield triggers repeatedly."),
    ("Sacrifice",      "archetype", "Strategies centered on sacrificing permanents for value."),
    ("Discard",        "archetype", "Strategies built around discarding and reanimating or profiting."),
    ("Mill",           "archetype", "Strategies that win by emptying an opponent's library."),

    # ── Layer 5: Emotional / Play-Pattern ────────────────────────────────────
    # Strategic identity — how the card feels to play and what it represents in the deck.

    ("Engine_Core",       "emotional", "A card the deck is built to enable, protect, and repeat."),
    ("Renewable_Fuel",    "emotional", "Provides repeatable bodies or resources — hard to exhaust."),
    ("Apex_Threat",       "emotional", "Demands an immediate answer or the game often ends."),
    ("Conversion_Piece",  "emotional", "Converts one type of resource into another at high efficiency."),
    ("Pressure_Piece",    "emotional", "Applies constant upward pressure on opponents every turn."),
    ("Resilience_Piece",  "emotional", "Difficult to permanently answer — returns, regenerates, or replaces itself."),
    ("Identity_Card",     "emotional", "Strongly represents the deck's personality and strategy."),
    ("Table_Threat",      "emotional", "Draws attention and reactions from other players at the table."),
    ("Comeback_Card",     "emotional", "Helps stabilize or take back momentum when behind."),
    ("Grand_Finisher",    "emotional", "Ends the game outright when it resolves — no delay."),
    ("Momentum_Spike",    "emotional", "Creates a breakout turn that pulls the deck far ahead."),
]


# ─── Oracle Text Auto-Tag Patterns (mechanical layer only) ────────────────────
#
# Each entry: (tag_name, regex_pattern, confidence)
# Patterns are applied to card.oracle_text (lowercased).
# Keep these precise to avoid false positives.

_MECHANICAL_PATTERNS: list[tuple[str, str, float]] = [

    # Draw effects
    ("Draw_Effect",       r"draw (?:a card|(?:\w+ )?cards)", 1.0),

    # Life drain / gain
    ("Life_Drain",        r"each opponent loses \w+ life", 0.9),
    ("Life_Drain",        r"target (?:player|opponent) loses \w+ life", 0.9),
    ("Life_Gain",         r"you gain \w+ life", 0.9),
    ("Life_Gain",         r"gain \w+ life", 0.8),

    # Sacrifice outlets
    ("Sacrifice_Outlet",  r"sacrifice (?:a|another|any number of) (?:creature|permanent)", 1.0),
    ("Sacrifice_Outlet",  r"sacrifice .{1,20}: add", 1.0),

    # Token generation
    ("Token_Generation",  r"create (?:a |an )?\d+/\d+ .{1,40}token", 0.9),
    ("Token_Generation",  r"create (?:\w+ )?\w+ creature tokens?", 0.9),

    # Reanimation (to battlefield)
    # Pattern 1: "Return target creature card from a graveyard to the battlefield"
    ("Reanimation",       r"return .{1,80}graveyard to the battlefield", 1.0),
    # Pattern 2: Aura-based reanimate (Animate Dead, Dance of the Dead)
    # "Return enchanted creature card to the battlefield"
    ("Reanimation",       r"return enchanted creature card to the battlefield", 0.95),

    # Recursion (to hand)
    ("Recursion_To_Hand", r"return .{1,40}graveyard to (?:its owner's|your) hand", 0.9),

    # Mana doublers / multipliers
    ("Mana_Multiplier",   r"add an amount of mana equal to", 0.95),
    ("Mana_Multiplier",   r"for each swamp you control, add", 0.95),
    ("Mana_Multiplier",   r"doubles the mana", 0.95),
    ("Mana_Multiplier",   r"add that much mana of any (?:one )?(?:type|color)", 0.85),

    # Mana production (non-land permanents)
    ("Mana_Production",   r"add \{[wubrgc]\}", 0.9),
    ("Mana_Production",   r"add (?:one|two|three) mana", 0.9),

    # Tutors
    ("Tutor_Effect",      r"search your library for (?:a |an |any |up to )", 1.0),

    # Board wipes
    ("Board_Wipe",        r"destroy all (?:creatures|permanents|artifacts|enchantments|nonland)", 1.0),
    ("Board_Wipe",        r"exile all (?:creatures|permanents|nonland)", 1.0),

    # Graveyard hate
    ("Graveyard_Hate",    r"exile (?:all cards in|target card from|each card from) (?:\w+ )?graveyard", 0.9),

    # Discard
    ("Discard_Effect",    r"(?:each player|target player|each opponent) discards", 0.9),

    # Self-mill
    ("Self_Mill",         r"put the top \w+ cards? of your library into your graveyard", 0.9),
    ("Self_Mill",         r"mill \w+ cards?", 0.8),

    # Cost reduction
    ("Cost_Reduction",    r"costs? \{[0-9]\} less", 0.85),
    ("Cost_Reduction",    r"costs? \w+ less to cast", 0.85),

    # Counters
    ("Counter_Spell",     r"counter target (?:spell|ability)", 1.0),
    ("Counter_Spell",     r"counter target (?:instant|sorcery|creature|artifact|enchantment) spell", 1.0),

    # Death triggers — matches "whenever [anything] creature(s) dies/die"
    # Covers: "whenever a creature dies", "whenever another creature dies",
    #         "whenever Blood Artist or another creature dies", etc.
    ("Death_Trigger",     r"whenever .{1,40}creature(?:s)? (?:you control )?(?:dies|die)", 0.9),

    # ETB triggers
    ("ETB_Trigger",       r"when (?:this|it|.{1,20}) enters the battlefield", 0.8),

    # Targeted removal
    ("Targeted_Removal",  r"destroy target (?:creature|permanent|artifact|enchantment|planeswalker)", 1.0),
    ("Targeted_Removal",  r"exile target (?:creature|permanent|artifact|enchantment|planeswalker)", 1.0),

    # Damage
    ("Damage_Effect",     r"deals? \w+ damage to (?:any target|target creature|each creature|each player|each opponent)", 0.9),

    # Bounce
    ("Bounce_Effect",     r"return target .{1,30} to (?:its owner's|their owner's) hand", 0.9),

    # Protection
    ("Protection_Effect", r"(?:has|have|gains?) hexproof", 0.9),
    ("Protection_Effect", r"(?:has|have|gains?) indestructible", 0.9),
    ("Protection_Effect", r"(?:has|have|gains?) shroud", 0.9),
]


# ─── Public API ───────────────────────────────────────────────────────────────

def seed_tags(db) -> int:
    """
    Seed the tags table with the built-in tag registry.

    Safe to call on an existing database — uses INSERT OR IGNORE.
    Returns the number of tags that were newly inserted.

    Usage:
        db.connect()
        tags.seed_tags(db)
    """
    inserted = 0
    for name, layer, description in TAGS:
        tag_id = db.save_tag(name, layer, description)
        if tag_id:
            inserted += 1
    return inserted


def tag_card(
    card_name: str,
    tag_name: str,
    db,
    confidence: float = 1.0,
    source: str = "manual",
    note: str = "",
) -> bool:
    """
    Tag a card with a named tag.

    Args:
        card_name: exact card name (must exist in cards table)
        tag_name:  tag from the registry (e.g. 'Engine_Core')
        db:        open Database connection
        confidence: 0.0–1.0 (default 1.0 for manual tags)
        source:    'manual' | 'regex' | 'contextual' | 'ai'
        note:      optional human explanation

    Returns:
        True if tagged successfully, False if tag_name not found in registry.
    """
    return db.tag_card(card_name, tag_name, confidence, source, note)


def get_card_tags(card_name: str, db, layer: Optional[str] = None) -> list[dict]:
    """
    Get all tags for a card, optionally filtered by layer.

    Args:
        card_name: card name (case-insensitive)
        db:        open Database connection
        layer:     optional — 'mechanical' | 'functional' | 'archetype' | 'emotional'

    Returns:
        List of dicts: {name, layer, confidence, source, note}
        Sorted by confidence desc within each layer.
    """
    return db.get_card_tags(card_name, layer)


def get_tag_names(card_name: str, db, layer: Optional[str] = None) -> list[str]:
    """
    Convenience: get just the tag names (not full dicts) for a card.

    Useful for simple checks: 'Engine_Core' in tags.get_tag_names('Crypt Ghast', db)
    """
    return [t["name"] for t in db.get_card_tags(card_name, layer)]


def query_cards_by_tag(tag_name: str, db, min_confidence: float = 0.0) -> list[dict]:
    """
    Find all cards tagged with a given tag.

    Args:
        tag_name:       tag to search for (case-insensitive)
        db:             open Database connection
        min_confidence: filter out tags below this confidence

    Returns:
        List of dicts: {card_name, confidence, source, note}
    """
    return db.query_cards_by_tag(tag_name, min_confidence)


def add_synergy(
    card_a: str,
    card_b: str,
    synergy_type: str,
    db,
    strength: float = 0.5,
    explanation: str = "",
) -> int:
    """
    Record a synergy relationship between two cards.

    Synergy types (descriptive strings — no fixed enum):
        'Sacrifice_Loop'        — one provides outlet, other recurs
        'Death_Trigger_Fuel'    — one dies, other profits
        'Big_Mana_Finisher'     — one makes mana, other spends it
        'Draw_Engine'           — two cards that combine for repeated draw
        etc.

    Strength scale (0.0–1.0):
        1.0 = core synergy (the combo itself)
        0.7 = strong synergy
        0.5 = moderate
        0.3 = incidental

    Returns:
        synergy edge id
    """
    return db.add_synergy(card_a, card_b, synergy_type, strength, explanation)


def get_synergies(card_name: str, db, min_strength: float = 0.0) -> list[dict]:
    """
    Get all synergy relationships for a card.

    Returns:
        List of dicts: {other_card, synergy_type, strength, explanation}
    """
    return db.get_synergies(card_name, min_strength)


def tag_mechanical(card: Card, db) -> list[str]:
    """
    Auto-tag a card's mechanical layer using oracle text patterns.

    This handles the obvious, objectively true mechanical tags.
    Functional, archetype, and emotional tags require human judgment.

    Args:
        card: Card object with oracle_text populated
        db:   open Database connection (tags must be seeded first)

    Returns:
        List of tag names that were successfully applied.

    Usage:
        db.connect()
        seed_tags(db)
        card = db.card_by_name("Blood Artist")
        applied = tag_mechanical(card, db)
        # → ['Draw_Effect', 'Death_Trigger', ...]
    """
    oracle = (card.oracle_text or "").lower()
    applied = []

    for tag_name, pattern, confidence in _MECHANICAL_PATTERNS:
        if re.search(pattern, oracle):
            success = db.tag_card(card.name, tag_name, confidence, source="regex")
            if success:
                applied.append(tag_name)

    # Deduplicate (same tag may match multiple patterns)
    return list(dict.fromkeys(applied))


def tag_count_for_deck(card_names: list[str], db, layer: Optional[str] = None) -> dict[str, int]:
    """
    Count how many cards in a deck carry each tag.

    Args:
        card_names: list of card names (the deck's main deck)
        db:         open Database connection
        layer:      optional — filter to one layer

    Returns:
        {tag_name: count}, sorted by count desc

    Example:
        counts = tag_count_for_deck(deck_card_names, db, layer='functional')
        # → {'Mana_Acceleration': 8, 'Recursion': 6, 'Removal': 4, ...}
    """
    return db.tag_count_for_deck(card_names, layer)
