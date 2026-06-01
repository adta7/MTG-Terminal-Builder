#!/usr/bin/env python3
"""
interactive_cut_review.py — Phase 9: Minimal Interactive Cut Review CLI

Asks the user seven preference questions, then generates a preference-weighted
cut review without editing DEFAULT_PREFERENCES manually.

Usage:
  python scripts/interactive_cut_review.py [--deck PATH] [--db PATH]

Output (overwrites existing):
  reports/deck_analysis/preference_cut_review.md
  reports/deck_analysis/preference_cut_review.json

This script is a review tool, not an optimizer.
It helps the user see tradeoffs; it does not decide for them.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from deck_gap_analysis import (
    DECK_PATH, SCAN_DB,
    DEFAULT_PREFERENCES, PREFERENCE_PROFILE_NAME,
    load_analysis_data,
    compute_preference_adjusted_cuts,
    _write_preference_cut_review,
    CUT_VERDICT_STRONG, CUT_VERDICT_BORDERLINE, CUT_VERDICT_NEAR_ZERO,
    CUT_VERDICT_ROLE_REVIEW, CUT_VERDICT_SKIP,
)


# ── Weight conversion ─────────────────────────────────────────────────────────
# Standard pillars: low/medium/high/very_high → weight
PILLAR_WEIGHTS: dict[str, float] = {
    "low":       0.5,
    "medium":    1.0,
    "high":      1.5,
    "very_high": 2.0,
}

# Curve pressure has a smaller scale so it doesn't explode at high CMC
CURVE_WEIGHTS: dict[str, float] = {
    "low":       0.0,
    "medium":    0.5,
    "high":      1.0,
    "very_high": 1.5,
}


def level_to_weight(level: str, is_curve: bool = False) -> float | None:
    """
    Convert a preference level string to a numeric weight.

    Returns None for blank input (signals "keep current default").
    Raises ValueError for unrecognized input.
    """
    level = level.strip().lower()
    if level == "":
        return None
    weights = CURVE_WEIGHTS if is_curve else PILLAR_WEIGHTS
    if level not in weights:
        valid = " / ".join(weights)
        raise ValueError(f"Invalid level '{level}'. Valid: {valid}")
    return weights[level]


def weight_to_label(weight: float, is_curve: bool = False) -> str:
    """Reverse-lookup the level label for a numeric weight."""
    weights = CURVE_WEIGHTS if is_curve else PILLAR_WEIGHTS
    for label, w in weights.items():
        if abs(w - weight) < 0.001:
            return label
    return f"{weight:.1f}"


# ── Preference question definitions ──────────────────────────────────────────
PREFERENCE_QUESTIONS = [
    {
        "key":         "preserve_big_mythic_threats",
        "label":       "Preserve big mythic threats",
        "description": "Apex threats, finishers — Grave Titan, Archon of Cruelty, Butcher of Malakir",
        "is_curve":    False,
    },
    {
        "key":         "preserve_sacrifice_control",
        "label":       "Preserve sacrifice/control effects",
        "description": "Edict effects, forced sacrifice, engine pillars — Grave Pact, Overseer of the Damned",
        "is_curve":    False,
    },
    {
        "key":         "preserve_draw_consistency",
        "label":       "Preserve draw consistency",
        "description": "Card draw and early hand smoothing — Night's Whisper, Read the Bones, Rune-Scarred Demon",
        "is_curve":    False,
    },
    {
        "key":         "preserve_mana_explosion",
        "label":       "Preserve mana scaling",
        "description": "Mana doublers and scaling — Nirkana Revenant, Black Market, Crypt Ghast",
        "is_curve":    False,
    },
    {
        "key":         "preserve_token_fuel_density",
        "label":       "Preserve token/fuel density",
        "description": "Token generation and recurring bodies — Grave Titan, Ghoulish Procession",
        "is_curve":    False,
    },
    {
        "key":         "preserve_recursion_density",
        "label":       "Preserve recursion density",
        "description": "Graveyard recursion — Animate Dead, Victimize, Oversold Cemetery",
        "is_curve":    False,
    },
    {
        "key":         "lower_curve_aggressively",
        "label":       "Lower curve aggressively",
        "description": "Adds cut pressure to high-CMC cards (CMC > 4). Higher = more pressure on expensive cards.",
        "is_curve":    True,
    },
]


def ask_preference(question: dict, current_default: float) -> float:
    """Prompt the user for one preference level. Returns the chosen weight."""
    is_curve    = question.get("is_curve", False)
    current_lbl = weight_to_label(current_default, is_curve)
    valid_opts  = " / ".join(CURVE_WEIGHTS if is_curve else PILLAR_WEIGHTS)

    print(f"\n  {question['label']}")
    print(f"  {question['description']}")
    print(f"  Default: {current_default:.1f} ({current_lbl})")
    print(f"  Options: {valid_opts}  (blank = keep default)")
    print("  > ", end="", flush=True)

    while True:
        answer = input().strip()
        try:
            result = level_to_weight(answer, is_curve)
            return result if result is not None else current_default
        except ValueError as e:
            print(f"  {e}")
            print("  > ", end="", flush=True)


def build_preferences_interactive(defaults: dict) -> tuple[dict, bool]:
    """
    Walk through all preference questions and collect user answers.

    Returns (preferences_dict, changed) where changed is True if any
    preference differed from the default.
    """
    preferences = dict(defaults)
    changed     = False

    print("\n" + "─" * 60)
    print("PREFERENCE SELECTION")
    print("─" * 60)
    print("  Rate each identity pillar. Higher weight = more protected from cuts.")
    print("  Press Enter to keep the current default for any pillar.")

    for question in PREFERENCE_QUESTIONS:
        key         = question["key"]
        current_val = defaults[key]
        new_val     = ask_preference(question, current_val)
        preferences[key] = new_val
        if abs(new_val - current_val) > 0.001:
            changed = True

    return preferences, changed


def print_summary(tier2_adjusted: list, cuts_still_needed: int) -> None:
    """Print a short terminal summary after generating the report."""
    cut_if_needed = [c for c in tier2_adjusted if c["preference_adjusted_net"] > 3]
    consider      = [c for c in tier2_adjusted if 0 < c["preference_adjusted_net"] <= 3]
    avoid         = [c for c in tier2_adjusted if c["preference_adjusted_net"] <= 0]

    print()
    print("─" * 60)
    print("PREFERENCE-ADJUSTED TIER 2 SUMMARY")
    print("─" * 60)
    print(f"  Cuts still needed after Tier 1: {cuts_still_needed}")
    print()

    if cut_if_needed:
        print("  Cut if needed (adj net > 3):")
        for c in cut_if_needed:
            print(f"    CMC {c['cmc']}  {c['name']:<35}  adj net={c['preference_adjusted_net']:.2f}")
    else:
        print("  Cut if needed: none — preferences protect all Tier 2 cards.")

    print()
    if consider:
        print("  Consider carefully (adj net 0–3):")
        for c in consider:
            print(f"    CMC {c['cmc']}  {c['name']:<35}  adj net={c['preference_adjusted_net']:.2f}")
    if avoid:
        print("  Avoid cutting (adj net ≤ 0 — strongly protected):")
        for c in avoid:
            cats = ", ".join(c.get("preference_categories_hit", []))
            print(f"    CMC {c['cmc']}  {c['name']:<35}  adj net={c['preference_adjusted_net']:.2f}  [{cats}]")


def main(deck_path: str = DECK_PATH, db_path: str = SCAN_DB) -> None:
    print()
    print("=" * 60)
    print("  MTG DECK PREFERENCE CUT REVIEW")
    print(f"  Profile: {PREFERENCE_PROFILE_NAME}")
    print("=" * 60)

    print("\nLoading deck data… ", end="", flush=True)
    data = load_analysis_data(deck_path, db_path)
    print("done.")

    structural  = data["structural"]
    cut_tier2   = data["cut_tier2"]
    weighted_by_card = data["weighted_by_card"]

    sim_confident = sum(
        1 for c in data["cut_tier1"]
        if c["verdict"] in (CUT_VERDICT_STRONG, CUT_VERDICT_BORDERLINE)
    )
    cuts_still_needed = max(0, structural["nonland_cuts_needed"] - sim_confident)

    print()
    print(f"  Deck: {data['deck_name']}")
    print(f"  Commander: {data['commander']}")
    print(f"  Cards: {structural['deck_size']} / {structural['deck_size_target']}")
    print(f"  Cuts needed: {structural['nonland_cuts_needed']}  "
          f"(model-confident: {sim_confident}, human-required: {cuts_still_needed})")

    preferences, changed = build_preferences_interactive(DEFAULT_PREFERENCES)

    # Echo the chosen profile
    print()
    print("─" * 60)
    print("SELECTED PREFERENCE PROFILE")
    print("─" * 60)
    for q in PREFERENCE_QUESTIONS:
        key = q["key"]
        val = preferences[key]
        lbl = weight_to_label(val, q.get("is_curve", False))
        marker = "  *" if abs(val - DEFAULT_PREFERENCES[key]) > 0.001 else "   "
        print(f"{marker} {q['label']:<40} {val:.1f}  ({lbl})")
    if changed:
        print()
        print("  (* = changed from default)")

    # Run preference review
    tier2_adjusted = compute_preference_adjusted_cuts(
        cut_tier2, weighted_by_card, preferences
    )
    _write_preference_cut_review(tier2_adjusted, preferences, cuts_still_needed)

    print_summary(tier2_adjusted, cuts_still_needed)

    print()
    print("─" * 60)
    print("REPORTS WRITTEN")
    print("─" * 60)
    from deck_gap_analysis import REPORTS
    for f in ["preference_cut_review.md", "preference_cut_review.json"]:
        print(f"  {REPORTS / f}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive preference-weighted cut review.")
    parser.add_argument("--deck", default=DECK_PATH)
    parser.add_argument("--db",   default=SCAN_DB)
    args = parser.parse_args()
    main(args.deck, args.db)
