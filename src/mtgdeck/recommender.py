"""
recommender.py — Phase 4: Card suggestions and cut candidates.

Two public functions:

  suggest(deck, db, analysis, role, profile, top_n)
    → list[Suggestion]

    Finds tagged cards NOT currently in the deck that fill the target role.
    Returns the top_n highest-scoring candidates.

    Note: only tagged cards appear as candidates. If a card has no tags in the
    database there is no basis for scoring it, so it is silently omitted.
    The caller should print a note like "Showing from tagged cards only."

  cuts(deck, db, analysis, profile, count, include_lands)
    → list[CutCandidate]

    Scores every card in the deck (excluding the commander and, by default,
    lands) on how worth keeping it is. Returns the lowest-scoring cards as
    cut candidates, sorted by cut_score descending.

Usage:
    profile = load_profile("data/profiles/mono_black_reanimator.json")
    suggestions = suggest(deck, db, analysis, role="draw", profile=profile)
    for s in suggestions:
        print(f"{s.card_name} — {s.score.total_score:.0f}/100")
        for reason in s.score.reasons:
            print(f"  • {reason}")
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .database import Database
from .models import Deck, DeckAnalysis
from .profiles import (
    Profile,
    compare_to_profile,
    count_roles_in_deck,
    CATEGORY_FUNCTIONAL_TAGS,
    CATEGORY_MECHANICAL_TAGS,
    CATEGORY_EMOTIONAL_TAGS,
)
from .scoring import (
    IDENTITY_SCORES,
    ScoreBreakdown,
    ScoringContext,
    _categories_filled,
    score_card,
)


# ─── Result Types ─────────────────────────────────────────────────────────────

@dataclass
class Suggestion:
    """A card recommended for adding to the deck."""
    card_name: str
    score: ScoreBreakdown
    mana_value: int


@dataclass
class CutCandidate:
    """A card recommended for cutting from the deck."""
    card_name: str
    keep_score: float   # how worth keeping: higher is better
    cut_score: float    # 100 - keep_score: higher means cut it
    reasons: list[str] = field(default_factory=list)
    mana_value: int = 0


# ─── Identity Keep Bonuses ────────────────────────────────────────────────────
#
# Higher bonuses than the suggest-side IDENTITY_SCORES because cuts should be
# conservative about removing identity cards. An Engine_Core should almost
# never appear in a cut list — make it very expensive to cut.

_IDENTITY_KEEP_BONUSES: dict[str, float] = {
    "Engine_Core":      15.0,  # The deck is built around this — never cut casually
    "Grand_Finisher":   12.0,  # Win condition; requires strong justification to cut
    "Apex_Threat":      10.0,
    "Conversion_Piece": 10.0,
    "Identity_Card":    10.0,
    "Pressure_Piece":    8.0,
    "Momentum_Spike":    8.0,
    "Renewable_Fuel":    7.0,
    "Comeback_Card":     7.0,
    "Resilience_Piece":  6.0,
    "Table_Threat":      6.0,
    "Efficient_Staple":  8.0,  # Cheap, proven, earns its slot every game
    "Cheap_Enabler":     8.0,  # Low-tempo cost to run; very efficient for the deck
}


# ─── Public API ───────────────────────────────────────────────────────────────

def build_context(
    deck: Deck,
    db: Database,
    analysis: DeckAnalysis,
    profile: Profile | None = None,
    target_role: str | None = None,
) -> ScoringContext:
    """
    Pre-compute the deck context needed for scoring.

    Call once per suggest/cuts invocation and reuse for every card.

    Computes:
      - deck_archetype_tags: archetype tags appearing in ≥3 distinct deck cards.
        Treats each unique card name as one count (not by quantity), so a 4x of
        a card only counts once toward the threshold.
      - role_gaps: per-category gap status from profile comparison.
        Empty if no profile is given.
      - avg_mana_value, target_role, profile_name from the arguments.
    """
    # Count archetype tags across unique deck card names (not by count).
    # This reflects what the deck is designed to do, not how many copies.
    arch_tag_counts: dict[str, int] = defaultdict(int)
    for card_entry in deck.cards:
        for tag in db.get_card_tags(card_entry.name, layer="archetype"):
            arch_tag_counts[tag["name"]] += 1

    # ≥3 distinct cards share an archetype → it's a deck theme
    deck_archetype_tags = frozenset(
        name for name, count in arch_tag_counts.items() if count >= 3
    )

    # Compute per-category gap status from profile
    role_gaps: dict[str, str] = {}
    if profile:
        role_counts = count_roles_in_deck(deck, db)
        gaps = compare_to_profile(analysis, role_counts, profile)
        role_gaps = {gap.category: gap.status for gap in gaps}

    return ScoringContext(
        deck_archetype_tags=deck_archetype_tags,
        role_gaps=role_gaps,
        avg_mana_value=analysis.avg_mana_value,
        target_role=target_role,
        profile_name=profile.name if profile else None,
    )


def suggest(
    deck: Deck,
    db: Database,
    analysis: DeckAnalysis,
    role: str,
    profile: Profile | None = None,
    top_n: int = 10,
) -> list[Suggestion]:
    """
    Recommend cards to add to the deck for the given role.

    Candidate pool: tagged cards not in the deck whose functional or mechanical
    tags map to the requested role. Untagged cards are not included because
    there is no basis for scoring them.

    Args:
        deck:     The current deck (used for exclusion and context).
        db:       Open database connection.
        analysis: Result of analyze_deck() for the same deck.
        role:     Profile category to fill (e.g. "draw", "ramp", "wincons").
        profile:  Optional deck profile for gap-aware scoring.
        top_n:    Maximum number of suggestions to return.

    Returns:
        Suggestions sorted by total_score descending. At most top_n results.
        Only cards with total_score > 0 are included.
    """
    context = build_context(deck, db, analysis, profile, target_role=role)
    candidates = _find_candidates_for_role(role, db, deck)

    results: list[Suggestion] = []
    for card_name in candidates:
        card = db.card_by_name(card_name)
        cmc = card.cmc if card else 0

        func_tags  = db.get_card_tags(card_name, layer="functional")
        mech_tags  = db.get_card_tags(card_name, layer="mechanical")
        arch_tags  = db.get_card_tags(card_name, layer="archetype")
        id_tags    = db.get_card_tags(card_name, layer="emotional")

        breakdown = score_card(card_name, cmc, func_tags, mech_tags, arch_tags, id_tags, context)
        if breakdown.total_score > 0:
            results.append(Suggestion(card_name=card_name, score=breakdown, mana_value=cmc))

    results.sort(key=lambda s: s.score.total_score, reverse=True)
    return results[:top_n]


def cuts(
    deck: Deck,
    db: Database,
    analysis: DeckAnalysis,
    profile: Profile | None = None,
    count: int = 5,
    include_lands: bool = False,
) -> list[CutCandidate]:
    """
    Suggest cards to cut from the deck.

    Scores every main-deck card on how worth keeping it is, then returns
    the lowest-scoring cards as cut candidates.

    The commander is always excluded — never suggest cutting the commander.
    Lands are excluded by default (include_lands=False) because land counts
    are a deliberate deck decision; use --include-lands to override.

    Args:
        deck:          The current deck.
        db:            Open database connection.
        analysis:      Result of analyze_deck() for the same deck.
        profile:       Optional deck profile for gap-aware scoring.
        count:         Number of cut candidates to return.
        include_lands: If True, lands are eligible for cuts.

    Returns:
        CutCandidates sorted by cut_score descending (highest cut_score = strongest cut).
    """
    context = build_context(deck, db, analysis, profile, target_role=None)

    candidates: list[CutCandidate] = []
    for card_entry in deck.cards:
        name = card_entry.name

        # Never suggest cutting the commander
        if deck.commander and name.lower() == deck.commander.lower():
            continue

        card = db.card_by_name(name)
        cmc = card.cmc if card else 0

        # Always skip basic lands — they are never useful as individual cut candidates.
        # Basic land count is handled separately via land analysis (compare to profile target).
        if card and "Basic" in card.type_line and "Land" in card.type_line:
            continue

        # Skip non-basic lands unless include_lands=True
        if not include_lands and card and "Land" in card.type_line:
            continue

        func_tags = db.get_card_tags(name, layer="functional")
        mech_tags = db.get_card_tags(name, layer="mechanical")
        arch_tags = db.get_card_tags(name, layer="archetype")
        id_tags   = db.get_card_tags(name, layer="emotional")
        all_tags  = db.get_card_tags(name)  # all layers — used for confidence check

        candidate = _score_as_cut(
            name, cmc, func_tags, mech_tags, arch_tags, id_tags, all_tags,
            context,
        )
        candidate.mana_value = cmc
        candidates.append(candidate)

    candidates.sort(key=lambda c: c.cut_score, reverse=True)
    return candidates[:count]


# ─── Internal Helpers ─────────────────────────────────────────────────────────

def _find_candidates_for_role(role: str, db: Database, deck: Deck) -> list[str]:
    """
    Find tagged cards not in the deck that can fill the given role.

    Searches functional (Layer 3), mechanical (Layer 2), and emotional (Layer 5)
    tags for the requested role. Only cards with at least one matching tag
    are included. Untagged cards are never candidates.

    Returns a sorted list of card names.
    """
    deck_names_lower = {c.name.lower() for c in deck.cards}

    func_role_tags      = CATEGORY_FUNCTIONAL_TAGS.get(role, frozenset())
    mech_role_tags      = CATEGORY_MECHANICAL_TAGS.get(role, frozenset())
    emotional_role_tags = CATEGORY_EMOTIONAL_TAGS.get(role, frozenset())

    candidates: set[str] = set()
    for tag_name in func_role_tags | mech_role_tags | emotional_role_tags:
        for entry in db.query_cards_by_tag(tag_name):
            if entry["card_name"].lower() not in deck_names_lower:
                candidates.add(entry["card_name"])

    return sorted(candidates)


def _score_as_cut(
    card_name: str,
    cmc: int,
    func_tags: list[dict],
    mech_tags: list[dict],
    arch_tags: list[dict],
    id_tags: list[dict],
    all_tags: list[dict],
    context: ScoringContext,
) -> CutCandidate:
    """
    Compute a keep_score for a card being evaluated as a cut candidate.

    keep_score starts at 50 (neutral) and is modified by:
      - Confidence of its tags (well-understood cards are safer to keep)
      - Gap alignment (fills a short category → keep; fills an over category → cut)
      - Identity bonuses (Engine_Core, Grand_Finisher, etc.)
      - Archetype overlap with deck strategy
      - Multi-function bonus (cards that fill ≥2 categories)
      - No-category penalty (fills nothing → likely expendable)

    cut_score = 100 - keep_score.
    Higher cut_score → stronger cut recommendation.
    """
    reasons: list[str] = []

    func_names = {t["name"] for t in func_tags}
    mech_names = {t["name"] for t in mech_tags}
    arch_names = {t["name"] for t in arch_tags}
    id_names   = {t["name"] for t in id_tags}

    keep_score = 50.0
    # All profile categories this card fills — functional, mechanical, AND emotional.
    # Passing id_names lets identity/strategic cards (Pressure_Piece, Engine_Core, etc.)
    # count toward the new emotional profile categories instead of getting "no role" penalty.
    filled = _categories_filled(func_names, mech_names, id_names)

    # 1. Confidence bonus — how well understood is this card?
    if all_tags:
        max_conf = max(t["confidence"] for t in all_tags)
        conf_bonus = (max_conf - 0.5) * 20.0
        keep_score += conf_bonus
        if conf_bonus > 0:
            reasons.append(f"Confidence {max_conf:.2f} (+{conf_bonus:.0f})")
        elif conf_bonus < 0:
            reasons.append(f"Low confidence {max_conf:.2f} ({conf_bonus:.0f})")
    else:
        # Untagged: no basis for keeping
        keep_score -= 5.0
        reasons.append("Untagged card (-5)")

    # 2. Gap alignment — reward cards filling underfilled roles
    #
    # IMPORTANT: overfill penalties are capped at -15 total, regardless of how many
    # overfilled categories the card touches. Without this cap, a multifunction card
    # (e.g. Deadly Dispute: draw + sac + treasure) gets stacked -10 × N, making the
    # most versatile cards appear as the worst cuts. That is backwards.
    low_bonus = 0.0
    high_penalty = 0.0
    gap_parts: list[str] = []
    for cat in filled:
        status = context.role_gaps.get(cat, "ok")
        if status == "low":
            low_bonus += 10.0
            gap_parts.append(f"{cat}(short ↑+10)")
        elif status == "high":
            high_penalty += 10.0
            gap_parts.append(f"{cat}(over ↓-10)")

    keep_score += low_bonus
    # Cap total overfill penalty: even if 4 categories are over, max penalty is -15.
    keep_score -= min(high_penalty, 15.0)
    if gap_parts:
        reasons.append("Gap: " + ", ".join(gap_parts))

    # 3. Identity protection — high-value identity tags protect against cuts
    for id_tag in id_names:
        bonus = _IDENTITY_KEEP_BONUSES.get(id_tag, 0.0)
        if bonus > 0.0:
            keep_score += bonus
            reasons.append(f"Identity: {id_tag} +{bonus:.0f}")

    # 4. Archetype alignment — cards that fit the deck's strategy are worth keeping
    overlap = arch_names & context.deck_archetype_tags
    arch_bonus = min(9.0, len(overlap) * 3.0)
    if arch_bonus > 0:
        keep_score += arch_bonus
        reasons.append(f"Archetype match: {', '.join(sorted(overlap))} +{arch_bonus:.0f}")

    # 5. Multi-function bonus / no-function penalty
    if len(filled) >= 2:
        keep_score += 5.0
        reasons.append(f"Multi-function ({len(filled)} categories) +5")
    elif len(filled) == 0:
        keep_score -= 5.0
        reasons.append("No profile role (-5)")

    cut_score = 100.0 - keep_score
    return CutCandidate(
        card_name=card_name,
        keep_score=keep_score,
        cut_score=cut_score,
        reasons=reasons,
    )
