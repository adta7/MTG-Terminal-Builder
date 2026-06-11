"""
scoring.py — Phase 4: Deterministic card scoring.

Scores how well a card fits a deck based on five independent components:

  1. role_match_score  (0-40) — Does the card fill the target role?
  2. profile_gap_score (0-30) — Does the deck need more of what this card provides?
  3. archetype_fit     (0-15) — Does the card fit the deck's dominant strategies?
  4. identity_score    (0-10) — Is this a high-value strategic/identity card?
  5. mv_modifier    (-5 to +5) — Is the mana cost appropriate for the role?

All functions are pure — they take data in, return data out.
No database calls happen here; the caller (recommender.py) fetches tags
and passes them as arguments so this module is fully testable in isolation.

Usage:
    context = build_context(deck, db, analysis, profile, target_role="draw")
    breakdown = score_card(
        card_name="Necropotence",
        card_cmc=3,
        func_tags=db.get_card_tags("Necropotence", layer="functional"),
        mech_tags=db.get_card_tags("Necropotence", layer="mechanical"),
        archetype_tags=db.get_card_tags("Necropotence", layer="archetype"),
        identity_tags=db.get_card_tags("Necropotence", layer="emotional"),
        context=context,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .profiles import CATEGORY_FUNCTIONAL_TAGS, CATEGORY_MECHANICAL_TAGS, CATEGORY_EMOTIONAL_TAGS


# ─── Identity Weight Table ────────────────────────────────────────────────────
#
# Maps emotional/identity tag names to their contribution to identity_score.
# These numbers represent the strategic importance of a card's role in the deck.
# Engine_Core and Grand_Finisher are the highest — the deck is built around them.
# Cards not in this table contribute 0 to identity_score.

IDENTITY_SCORES: dict[str, float] = {
    "Engine_Core":      10.0,
    "Grand_Finisher":   10.0,
    "Apex_Threat":       8.0,
    "Conversion_Piece":  8.0,
    "Pressure_Piece":    7.0,
    "Momentum_Spike":    7.0,
    "Comeback_Card":     6.0,
    "Renewable_Fuel":    6.0,
    "Table_Threat":      5.0,
    "Resilience_Piece":  5.0,
    "Identity_Card":     5.0,
    "Efficient_Staple":  7.0,
    "Cheap_Enabler":     7.0,
}


# ─── MV Role Sensitivity ──────────────────────────────────────────────────────
#
# For sensitive roles (ramp, draw, protection, etc.) cheap cards are strongly
# preferred — paying 4 mana for a draw spell hurts. For tolerant roles
# (wincons, reanimation) a 7-drop bomb is expected and normal.

MV_SENSITIVE_ROLES: frozenset[str] = frozenset({
    "draw",
    "ramp",
    "protection",
    "sac_outlets",
    "removal",
    "board_wipes",
    "graveyard_fill",
})

MV_TOLERANT_ROLES: frozenset[str] = frozenset({
    "wincons",
    "reanimation",
})


# ─── Scoring Context ──────────────────────────────────────────────────────────

@dataclass
class ScoringContext:
    """
    Pre-computed deck state for a single suggest or cuts call.

    Build once via recommender.build_context() and reuse for every card
    in the candidate pool. This avoids querying the same deck data repeatedly.

    Attributes:
        deck_archetype_tags: archetype tag names that appear in ≥3 distinct
            deck cards. Represents the deck's dominant strategic identity.
        role_gaps: per-category gap status from the profile comparison.
            Keys are profile category names ("ramp", "draw", etc.),
            values are "low", "ok", or "high". Empty if no profile is given.
        avg_mana_value: deck average MV (spells only, not lands).
        target_role: the role being searched for in suggest(); None for cuts().
        profile_name: name of the active profile, or None.
    """
    deck_archetype_tags: frozenset
    role_gaps: dict[str, str]
    avg_mana_value: float
    target_role: str | None
    profile_name: str | None


# ─── Score Breakdown ──────────────────────────────────────────────────────────

@dataclass
class ScoreBreakdown:
    """
    Transparent breakdown of a card's total score.

    Every component is exposed so the CLI can print an explanation.
    total_score is clamped to [0, 100].

    Attributes:
        card_name: name of the scored card.
        total_score: sum of all components, clamped to [0, 100].
        role_match_score: 0-40. How well this card fills the target role.
        profile_gap_score: 0-30. How much the deck needs what this provides.
        archetype_fit_score: 0-15. Alignment with the deck's archetypes.
        identity_score: 0-10. Strategic weight of the card's identity tags.
        mana_value_modifier: -5 to +5. MV efficiency for the role.
        reasons: plain-English explanation of each scoring decision.
    """
    card_name: str
    total_score: float
    role_match_score: float
    profile_gap_score: float
    archetype_fit_score: float
    identity_score: float
    mana_value_modifier: float
    reasons: list[str] = field(default_factory=list)


# ─── Core Scoring Function ────────────────────────────────────────────────────

def score_card(
    card_name: str,
    card_cmc: int,
    func_tags: list[dict],
    mech_tags: list[dict],
    archetype_tags: list[dict],
    identity_tags: list[dict],
    context: ScoringContext,
) -> ScoreBreakdown:
    """
    Score how well a card fits the deck.

    All tag arguments are lists of dicts from db.get_card_tags():
        [{"name": str, "layer": str, "confidence": float, ...}, ...]

    Args:
        card_name:      Name of the card (for display only — not used in logic).
        card_cmc:       Converted mana cost.
        func_tags:      Layer 3 (functional) tags.
        mech_tags:      Layer 2 (mechanical) tags.
        archetype_tags: Layer 4 (archetype) tags.
        identity_tags:  Layer 5 (emotional) tags.
        context:        Pre-computed deck context from build_context().

    Returns:
        ScoreBreakdown with all components and human-readable reasons.
    """
    reasons: list[str] = []

    func_names = {t["name"] for t in func_tags}
    mech_names = {t["name"] for t in mech_tags}
    arch_names = {t["name"] for t in archetype_tags}
    id_names   = {t["name"] for t in identity_tags}

    role_match_score    = _compute_role_match(func_tags, mech_tags, func_names, mech_names, context, reasons)
    profile_gap_score   = _compute_profile_gap(func_names, mech_names, context, reasons)
    archetype_fit_score = _compute_archetype_fit(arch_names, context, reasons)
    identity_score      = _compute_identity_score(id_names, reasons)
    mana_value_modifier = _compute_mv_modifier(card_cmc, context.target_role, reasons)

    total = (
        role_match_score
        + profile_gap_score
        + archetype_fit_score
        + identity_score
        + mana_value_modifier
    )
    total = max(0.0, min(100.0, total))

    return ScoreBreakdown(
        card_name=card_name,
        total_score=total,
        role_match_score=role_match_score,
        profile_gap_score=profile_gap_score,
        archetype_fit_score=archetype_fit_score,
        identity_score=identity_score,
        mana_value_modifier=mana_value_modifier,
        reasons=reasons,
    )


# ─── Component Scorers ────────────────────────────────────────────────────────

def _compute_role_match(
    func_tags: list[dict],
    mech_tags: list[dict],
    func_names: set[str],
    mech_names: set[str],
    context: ScoringContext,
    reasons: list[str],
) -> float:
    """
    Role match score (0-40).

    If context.target_role is set:
      - Find tags that match the role's requirements (functional + mechanical).
      - Score = 40 × max_confidence_of_matching_tags.
      - If no match: 0.

    If no target_role (cut scoring context):
      - Count how many profile categories are filled.
      - Score = min(40, categories × 8).
    """
    if context.target_role:
        target = context.target_role
        func_required = CATEGORY_FUNCTIONAL_TAGS.get(target, frozenset())
        mech_required = CATEGORY_MECHANICAL_TAGS.get(target, frozenset())

        matching: list[tuple[str, float]] = []
        for t in func_tags:
            if t["name"] in func_required:
                matching.append((t["name"], t["confidence"]))
        for t in mech_tags:
            if t["name"] in mech_required:
                matching.append((t["name"], t["confidence"]))

        if not matching:
            reasons.append(f"Does not match {target} role")
            return 0.0

        max_conf = max(conf for _, conf in matching)
        best_tag = max(matching, key=lambda x: x[1])[0]
        score = 40.0 * max_conf
        reasons.append(
            f"Matches {target} role via {best_tag} (conf {max_conf:.2f})"
        )
        return score

    # No target role — count how many categories the card fills
    filled = _categories_filled(func_names, mech_names)
    score = min(40.0, len(filled) * 8.0)
    n = len(filled)
    if n:
        label = "category" if n == 1 else "categories"
        reasons.append(
            f"Fills {n} profile {label}: {', '.join(sorted(filled))}"
        )
    else:
        reasons.append("Fills no profile categories")
    return score


def _compute_profile_gap(
    func_names: set[str],
    mech_names: set[str],
    context: ScoringContext,
    reasons: list[str],
) -> float:
    """
    Profile gap score (0-30).

    Rewards filling categories where the deck is short.
    Penalizes filling categories where the deck is already over.

    Scoring:
      "low"  category → +15 (deck needs this)
      "ok"   category → +5  (deck is fine, still useful)
      "high" category → -5  (deck has too many of these)

    Clamped to [0, 30].
    """
    filled = _categories_filled(func_names, mech_names)
    if not filled:
        return 0.0

    score = 0.0
    gap_parts: list[str] = []
    for cat in filled:
        status = context.role_gaps.get(cat, "ok")
        if status == "low":
            score += 15.0
            gap_parts.append(f"{cat}(short ↑)")
        elif status == "ok":
            score += 5.0
            gap_parts.append(f"{cat}(ok)")
        elif status == "high":
            score -= 5.0
            gap_parts.append(f"{cat}(over ↓)")

    score = max(0.0, min(30.0, score))
    if gap_parts:
        reasons.append("Gap alignment: " + ", ".join(gap_parts))
    return score


def _compute_archetype_fit(
    arch_names: set[str],
    context: ScoringContext,
    reasons: list[str],
) -> float:
    """
    Archetype fit score (0-15).

    Cards that share archetype tags with the deck's dominant strategies score higher.
    Each matching archetype tag is worth 3 points, capped at 15 (5 matches).
    """
    overlap = arch_names & context.deck_archetype_tags
    score = min(15.0, len(overlap) * 3.0)
    if overlap:
        reasons.append(f"Archetype match: {', '.join(sorted(overlap))}")
    else:
        reasons.append("No archetype overlap with deck")
    return score


def _compute_identity_score(
    id_names: set[str],
    reasons: list[str],
) -> float:
    """
    Identity score (0-10).

    The card's emotional/strategic weight in the deck's identity.
    Takes the highest score across all identity tags the card has.
    Cards with no identity tags contribute 0.
    """
    scores = {name: IDENTITY_SCORES[name] for name in id_names if name in IDENTITY_SCORES}
    if not scores:
        return 0.0
    best_tag, best_score = max(scores.items(), key=lambda x: x[1])
    reasons.append(f"Identity: {best_tag} (+{best_score:.0f})")
    return best_score


def _compute_mv_modifier(
    cmc: int,
    target_role: str | None,
    reasons: list[str],
) -> float:
    """
    Mana value modifier (-5 to +5).

    For MV_SENSITIVE_ROLES (draw, ramp, protection, etc.):
      CMC ≤ 1: +5    CMC 2: +3    CMC 3: +1
      CMC 4:  -1    CMC 5:  -3   CMC 6+: -5

    For MV_TOLERANT_ROLES (wincons, reanimation):
      CMC ≤ 2: +2    CMC 3+: 0   (high CMC bombs are expected)

    For other roles or no target role:
      CMC ≤ 2: +2    CMC 3-4: 0  CMC 5-6: -1  CMC 7+: -2
    """
    if target_role in MV_SENSITIVE_ROLES:
        table = {0: 5.0, 1: 5.0, 2: 3.0, 3: 1.0, 4: -1.0, 5: -3.0}
        mod = table.get(cmc, -5.0)
        if mod != 0.0:
            sign = "+" if mod > 0 else ""
            quality = "efficient" if mod > 0 else "costly"
            reasons.append(
                f"MV {cmc} is {quality} for {target_role} ({sign}{mod:.0f})"
            )
        return mod

    if target_role in MV_TOLERANT_ROLES:
        mod = 2.0 if cmc <= 2 else 0.0
        if mod > 0:
            reasons.append(f"MV {cmc} is efficient for {target_role} (+{mod:.0f})")
        return mod

    # Neutral scaling — mild preference for lower CMC
    if cmc <= 2:
        mod = 2.0
    elif cmc <= 4:
        mod = 0.0
    elif cmc <= 6:
        mod = -1.0
    else:
        mod = -2.0

    if mod != 0.0:
        sign = "+" if mod > 0 else ""
        reasons.append(f"MV {cmc} ({sign}{mod:.0f})")
    return mod


# ─── Shared Utility ───────────────────────────────────────────────────────────

def _categories_filled(
    func_names: set[str],
    mech_names: set[str],
    emotional_names: set[str] = frozenset(),
) -> set[str]:
    """
    Return the set of profile categories this card fills, given its tag names.

    Checks functional (Layer 3), mechanical (Layer 2), and optionally emotional
    (Layer 5) tags. Uses the same category-to-tag mapping as count_roles_in_deck()
    in profiles.py so that scoring stays consistent with profile comparison.

    A card with two functional tags that both map to "ramp" still counts as 1 category.
    Pass emotional_names to include identity/strategic categories (pressure_pieces,
    engine_core, etc.) in the result.
    """
    filled: set[str] = set()
    for cat, tags in CATEGORY_FUNCTIONAL_TAGS.items():
        if func_names & tags:
            filled.add(cat)
    for cat, tags in CATEGORY_MECHANICAL_TAGS.items():
        if mech_names & tags:
            filled.add(cat)
    for cat, tags in CATEGORY_EMOTIONAL_TAGS.items():
        if emotional_names & tags:
            filled.add(cat)
    return filled
