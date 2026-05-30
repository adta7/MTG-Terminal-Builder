"""
profiles.py — Phase 3: Deck profile comparison.

A profile is a JSON file that defines target ranges for each role category
in a deck (ramp, draw, removal, etc.). This module:

  - Loads profiles from JSON
  - Counts how many cards in a deck fill each category (via Layer 3 tags)
  - Compares actual counts against profile targets
  - Returns structured gap reports

Usage:
    profile = load_profile("data/profiles/mono_black_reanimator.json")
    role_counts = count_roles_in_deck(deck, db)
    gaps = compare_to_profile(analysis, role_counts, profile)

Category counts come from Layer 3 functional tags and a small set of
Layer 2 mechanical tags for categories with no functional equivalent.

A card with multiple functional tags (e.g. Ashnod's Altar: Mana_Engine +
Engine) can count toward multiple categories. A card with two tags that
both map to the same category still counts as exactly 1 toward that category.
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .models import Deck, DeckAnalysis
from .database import Database


# ─── Category → Tag Mappings ──────────────────────────────────────────────────
#
# Each profile category is filled by cards that carry at least one of the
# listed functional tags (Layer 3) or mechanical tags (Layer 2).
#
# Functional tags are the primary source. Mechanical tags fill the gaps for
# categories that have no functional-layer equivalent (board_wipes, graveyard_fill).
#
# To add a new category: add it here and add a matching key to the profile JSON.

CATEGORY_FUNCTIONAL_TAGS: dict[str, frozenset] = {
    "ramp":           frozenset({"Mana_Acceleration", "Mana_Engine"}),
    # "draw" uses Card_Draw only — NOT Card_Advantage or Setup.
    # Card_Advantage includes tutors (Vampiric Tutor, Demonic Tutor) which are card
    # selection / setup tools, not draw. Tutors are card-disadvantage in the hand,
    # costing a card to find another. Only literal draw effects count toward draw targets.
    "draw":           frozenset({"Card_Draw"}),
    "removal":        frozenset({"Removal", "Interaction"}),
    "reanimation":    frozenset({"Recursion"}),
    # "graveyard_fill" uses NO functional tags — Fuel is too broad.
    # Fuel includes token generators (Repeatable_Token_Generation → Fuel), which are
    # sacrifice fuel but do NOT fill the graveyard. Self_Mill and Looting_Effect
    # (via CATEGORY_MECHANICAL_TAGS) cover the real graveyard-filling effects.
    "protection":     frozenset({"Protection"}),
    # "wincons" uses only Finisher — Payoff is too broad (Blood Artist payoffs ≠ win conditions)
    "wincons":        frozenset({"Finisher"}),
    # "sac_outlets" is handled by mechanical Sacrifice_Outlet — Engine/Conversion are too broad
}

CATEGORY_MECHANICAL_TAGS: dict[str, frozenset] = {
    "board_wipes":    frozenset({"Board_Wipe"}),
    # graveyard_fill: cards that put cards IN the graveyard.
    # Self_Mill = explicit mill effects (Stitcher's Supplier, Perpetual Timepiece).
    # Looting_Effect = draw-then-discard or discard-then-draw (fills GY by discarding).
    # Graveyard_Tutor = search library and put directly into GY (Entomb, Buried Alive).
    "graveyard_fill": frozenset({"Self_Mill", "Looting_Effect", "Graveyard_Tutor"}),
    # Sacrifice_Outlet is a precise mechanical tag — only cards that explicitly let you
    # sacrifice permanents as a cost or activated ability. Much more accurate than Engine.
    "sac_outlets":    frozenset({"Sacrifice_Outlet"}),
}

# ─── Emotional/Identity Category → Tag Mappings ───────────────────────────────
#
# Maps strategic identity categories to Layer 5 (emotional) tag names.
# These capture the deck's personality and play pattern — cards that matter
# for identity, pressure, conversion engines, and apex threats.
#
# These categories are MANUALLY maintained — the rule engine cannot reliably
# infer them from oracle text. Use `mtgdeck retag-deck` after adding manual
# emotional tags to a card.

CATEGORY_EMOTIONAL_TAGS: dict[str, frozenset] = {
    "pressure_pieces":  frozenset({"Pressure_Piece", "Table_Threat"}),
    "conversion_cards": frozenset({"Conversion_Piece"}),
    "engine_core":      frozenset({"Engine_Core"}),
    "recursive_fuel":   frozenset({"Renewable_Fuel"}),
    "apex_threats":     frozenset({"Apex_Threat"}),
    "identity_cards":   frozenset({"Identity_Card"}),
    "mana_payoffs":     frozenset({"Grand_Finisher", "Momentum_Spike"}),
}

# Human-readable display names for CLI output.
CATEGORY_DISPLAY_NAMES: dict[str, str] = {
    "lands":            "Lands",
    "ramp":             "Ramp",
    "draw":             "Draw",
    "removal":          "Removal",
    "board_wipes":      "Board Wipes",
    "reanimation":      "Reanimation",
    "sac_outlets":      "Sac Outlets",
    "protection":       "Protection",
    "graveyard_fill":   "Graveyard Fill",
    "wincons":          "Win Cons",
    "avg_mana_value":   "Avg MV",
    "token_makers":     "Token Makers",
    # Emotional / strategic identity categories
    "pressure_pieces":  "Pressure Pieces",
    "conversion_cards": "Conversion Cards",
    "engine_core":      "Engine Core",
    "recursive_fuel":   "Recursive Fuel",
    "apex_threats":     "Apex Threats",
    "identity_cards":   "Identity Cards",
    "mana_payoffs":     "Mana Payoffs",
}


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Profile:
    """A deck profile with target ranges per role category."""
    name: str
    description: str
    targets: dict[str, list[float]]   # category → [min, max]


@dataclass
class ProfileGap:
    """
    The result of comparing one profile category against the deck's actual count.

    status:
        "ok"   — actual is within [target_min, target_max]
        "low"  — actual is below target_min
        "high" — actual is above target_max

    delta:
        0.0  when ok
        negative when low  (how far below target_min)
        positive when high (how far above target_max)
    """
    category: str
    display_name: str
    actual: float
    target_min: float
    target_max: float
    status: str
    delta: float
    message: str


# ─── Profile Loading ──────────────────────────────────────────────────────────

def load_profile(path: str | Path) -> Profile:
    """
    Load a deck profile from a JSON file.

    Expected format:
        {
          "name": "Mono Black Reanimator",
          "description": "...",
          "targets": {
            "lands":   [35, 37],
            "ramp":    [10, 13],
            ...
          }
        }

    Raises:
        FileNotFoundError — if the file does not exist
        ValueError        — if the JSON is malformed or missing 'targets'
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")

    with open(path) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid profile JSON in {path.name}: {e}")

    if "targets" not in data:
        raise ValueError(f"Profile {path.name} is missing required 'targets' key")

    return Profile(
        name=data.get("name", path.stem),
        description=data.get("description", ""),
        targets=data["targets"],
    )


# ─── Role Counting ────────────────────────────────────────────────────────────

def count_roles_in_deck(deck: Deck, db: Database) -> dict[str, int]:
    """
    Count how many cards in the deck fill each profile category.

    Checks three tag layers:
      - Functional (Layer 3): ramp, draw, removal, reanimation, protection, wincons
      - Mechanical (Layer 2): board_wipes, graveyard_fill, sac_outlets
      - Emotional (Layer 5): pressure_pieces, conversion_cards, engine_core,
                             recursive_fuel, apex_threats, identity_cards, mana_payoffs

    A card contributes at most 1 count per category, even if multiple of
    its tags map to the same category. Cards with no tags are silently skipped.

    Returns:
        dict mapping category → count of cards filling that role
    """
    role_counts: dict[str, int] = defaultdict(int)

    for card_entry in deck.cards:
        func_tags = {
            t["name"]
            for t in db.get_card_tags(card_entry.name, layer="functional")
        }
        mech_tags = {
            t["name"]
            for t in db.get_card_tags(card_entry.name, layer="mechanical")
        }
        emotional_tags = {
            t["name"]
            for t in db.get_card_tags(card_entry.name, layer="emotional")
        }

        # Collect unique categories this card contributes to.
        # Using a set ensures each category is counted at most once per card,
        # even if the card has two tags that both map to the same category.
        contributed: set[str] = set()

        for category, tag_set in CATEGORY_FUNCTIONAL_TAGS.items():
            if func_tags & tag_set:
                contributed.add(category)

        for category, tag_set in CATEGORY_MECHANICAL_TAGS.items():
            if mech_tags & tag_set:
                contributed.add(category)

        for category, tag_set in CATEGORY_EMOTIONAL_TAGS.items():
            if emotional_tags & tag_set:
                contributed.add(category)

        for category in contributed:
            role_counts[category] += card_entry.count

    return dict(role_counts)


# ─── Profile Comparison ───────────────────────────────────────────────────────

def compare_to_profile(
    analysis: DeckAnalysis,
    role_counts: dict[str, int],
    profile: Profile,
) -> list[ProfileGap]:
    """
    Compare a deck's actual role counts against a profile's target ranges.

    Returns one ProfileGap per category defined in the profile.
    Categories are evaluated in the order they appear in profile.targets.

    Special categories handled separately:
      "lands"          → uses analysis.land_count  (not role_counts)
      "avg_mana_value" → uses analysis.avg_mana_value (not role_counts)
    All other categories → pulled from role_counts dict.
    """
    gaps: list[ProfileGap] = []

    for category, bounds in profile.targets.items():
        target_min, target_max = float(bounds[0]), float(bounds[1])
        display = CATEGORY_DISPLAY_NAMES.get(
            category,
            category.replace("_", " ").title(),
        )

        # Resolve the actual value for this category.
        if category == "lands":
            actual = float(analysis.land_count)
        elif category == "avg_mana_value":
            actual = analysis.avg_mana_value
        else:
            actual = float(role_counts.get(category, 0))

        # Classify and compute delta.
        if actual < target_min:
            status = "low"
            delta = actual - target_min   # negative
            needed = _fmt(target_min - actual)
            message = f"short by {needed}  (target {_fmt(target_min)}–{_fmt(target_max)})"
        elif actual > target_max:
            status = "high"
            delta = actual - target_max   # positive
            over = _fmt(actual - target_max)
            message = f"over by {over}  (target {_fmt(target_min)}–{_fmt(target_max)})"
        else:
            status = "ok"
            delta = 0.0
            message = f"target {_fmt(target_min)}–{_fmt(target_max)}"

        gaps.append(ProfileGap(
            category=category,
            display_name=display,
            actual=actual,
            target_min=target_min,
            target_max=target_max,
            status=status,
            delta=delta,
            message=message,
        ))

    return gaps


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _fmt(val: float) -> str:
    """Format a numeric value: integers without decimal, floats with one decimal."""
    return str(int(val)) if val == int(val) else f"{val:.1f}"


def find_profile(name: str, profiles_dir: str | Path) -> Path:
    """
    Locate a profile JSON file by name.

    Accepts either a bare name ("mono_black_reanimator") or a full path.
    Searches in profiles_dir if the name is not an absolute path.

    Raises:
        FileNotFoundError — if no matching profile is found
    """
    candidate = Path(name)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    profiles_dir = Path(profiles_dir)
    # Try exact filename first, then with .json extension.
    for suffix in ["", ".json"]:
        p = profiles_dir / f"{name}{suffix}"
        if p.exists():
            return p

    available = sorted(p.stem for p in profiles_dir.glob("*.json"))
    hint = f"Available: {', '.join(available)}" if available else "No profiles found."
    raise FileNotFoundError(
        f"Profile '{name}' not found in {profiles_dir}. {hint}"
    )
