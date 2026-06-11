"""
test_scoring.py — Unit tests for Phase 4 card scoring.

All tests are pure — no database required.
The scoring module takes pre-fetched tag lists and a ScoringContext;
we construct minimal fake inputs here.

Covers:
  - _categories_filled: functional and mechanical tag mapping
  - _compute_role_match: target role present / absent, confidence scaling
  - _compute_profile_gap: low/ok/high gaps, multi-category, clamping
  - _compute_archetype_fit: overlap counting, cap at 15
  - _compute_identity_score: max across tags, empty
  - _compute_mv_modifier: sensitive / tolerant / neutral roles
  - score_card: end-to-end, clamping to [0, 100], reasons populated
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mtgdeck.scoring import (
    ScoringContext,
    ScoreBreakdown,
    IDENTITY_SCORES,
    MV_SENSITIVE_ROLES,
    MV_TOLERANT_ROLES,
    _categories_filled,
    _compute_role_match,
    _compute_profile_gap,
    _compute_archetype_fit,
    _compute_identity_score,
    _compute_mv_modifier,
    score_card,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _ctx(
    deck_archetype_tags=frozenset(),
    role_gaps=None,
    avg_mana_value=3.0,
    target_role=None,
    profile_name=None,
) -> ScoringContext:
    return ScoringContext(
        deck_archetype_tags=frozenset(deck_archetype_tags),
        role_gaps=role_gaps or {},
        avg_mana_value=avg_mana_value,
        target_role=target_role,
        profile_name=profile_name,
    )


def _tag(name: str, layer: str = "functional", confidence: float = 1.0) -> dict:
    return {"name": name, "layer": layer, "confidence": confidence, "source": "test", "note": ""}


# ─── _categories_filled ───────────────────────────────────────────────────────

class TestCategoriesFilled:

    def test_functional_tag_fills_ramp(self):
        assert "ramp" in _categories_filled({"Mana_Acceleration"}, set())

    def test_functional_tag_fills_draw(self):
        assert "draw" in _categories_filled({"Card_Draw"}, set())

    def test_mechanical_tag_fills_board_wipes(self):
        assert "board_wipes" in _categories_filled(set(), {"Board_Wipe"})

    def test_mechanical_tag_fills_sac_outlets(self):
        assert "sac_outlets" in _categories_filled(set(), {"Sacrifice_Outlet"})

    def test_mechanical_tag_fills_graveyard_fill(self):
        assert "graveyard_fill" in _categories_filled(set(), {"Self_Mill"})

    def test_functional_fills_multiple_categories(self):
        """Mana_Acceleration → ramp; Card_Draw → draw."""
        filled = _categories_filled({"Mana_Acceleration", "Card_Draw"}, set())
        assert "ramp" in filled
        assert "draw" in filled

    def test_no_tags_fills_nothing(self):
        assert _categories_filled(set(), set()) == set()

    def test_unrecognised_tags_fill_nothing(self):
        assert _categories_filled({"NotATag"}, {"AlsoNotATag"}) == set()

    def test_two_functional_tags_same_category_count_once(self):
        """Mana_Acceleration and Mana_Engine both map to ramp → only 1 category."""
        filled = _categories_filled({"Mana_Acceleration", "Mana_Engine"}, set())
        # ramp appears once, not twice
        assert filled.count("ramp") == 1 if isinstance(filled, list) else "ramp" in filled
        assert len([c for c in filled if c == "ramp"]) == 1

    def test_functional_fill_reanimation(self):
        assert "reanimation" in _categories_filled({"Recursion"}, set())

    def test_functional_fill_wincons(self):
        assert "wincons" in _categories_filled({"Finisher"}, set())

    def test_functional_fill_protection(self):
        assert "protection" in _categories_filled({"Protection"}, set())


# ─── _compute_role_match ──────────────────────────────────────────────────────

class TestComputeRoleMatch:

    def test_functional_tag_matches_target_role(self):
        func_tags = [_tag("Card_Draw", layer="functional", confidence=1.0)]
        ctx = _ctx(target_role="draw")
        reasons = []
        score = _compute_role_match(func_tags, [], {"Card_Draw"}, set(), ctx, reasons)
        assert score == pytest.approx(40.0)
        assert any("draw" in r for r in reasons)

    def test_mechanical_tag_matches_target_role(self):
        """Board_Wipe (mechanical) maps to board_wipes category."""
        mech_tags = [_tag("Board_Wipe", layer="mechanical", confidence=1.0)]
        ctx = _ctx(target_role="board_wipes")
        reasons = []
        score = _compute_role_match([], mech_tags, set(), {"Board_Wipe"}, ctx, reasons)
        assert score == pytest.approx(40.0)

    def test_confidence_scales_role_match(self):
        """A tag with confidence=0.7 gives 40 × 0.7 = 28."""
        func_tags = [_tag("Recursion", confidence=0.7)]
        ctx = _ctx(target_role="reanimation")
        reasons = []
        score = _compute_role_match(func_tags, [], {"Recursion"}, set(), ctx, reasons)
        assert score == pytest.approx(28.0)

    def test_no_matching_tag_returns_zero(self):
        func_tags = [_tag("Finisher", confidence=1.0)]
        ctx = _ctx(target_role="draw")
        reasons = []
        score = _compute_role_match(func_tags, [], {"Finisher"}, set(), ctx, reasons)
        assert score == 0.0
        assert any("Does not match" in r for r in reasons)

    def test_no_target_role_scores_by_categories_filled(self):
        """Without a target role, 1 category filled → 8 points."""
        ctx = _ctx(target_role=None)
        reasons = []
        score = _compute_role_match(
            [_tag("Card_Draw")], [], {"Card_Draw"}, set(), ctx, reasons
        )
        assert score == pytest.approx(8.0)

    def test_no_target_role_multiple_categories_cap_at_40(self):
        """6 categories × 8 = 48 but caps at 40."""
        func_names = {"Card_Advantage", "Mana_Acceleration", "Recursion", "Removal", "Finisher", "Protection"}
        ctx = _ctx(target_role=None)
        reasons = []
        func_tags = [_tag(n) for n in func_names]
        score = _compute_role_match(func_tags, [], func_names, set(), ctx, reasons)
        assert score == pytest.approx(40.0)

    def test_no_target_role_no_categories_is_zero(self):
        ctx = _ctx(target_role=None)
        reasons = []
        score = _compute_role_match([], [], set(), set(), ctx, reasons)
        assert score == 0.0

    def test_best_confidence_tag_wins(self):
        """Two tags both map to the same role; score uses max confidence.
        Uses ramp (Mana_Acceleration + Mana_Engine) since ramp has two functional tags.
        """
        func_tags = [
            _tag("Mana_Acceleration", confidence=0.5),
            _tag("Mana_Engine", confidence=0.9),
        ]
        func_names = {"Mana_Acceleration", "Mana_Engine"}
        ctx = _ctx(target_role="ramp")
        reasons = []
        score = _compute_role_match(func_tags, [], func_names, set(), ctx, reasons)
        assert score == pytest.approx(40 * 0.9)


# ─── _compute_profile_gap ─────────────────────────────────────────────────────

class TestComputeProfileGap:

    def test_low_gap_gives_15_points(self):
        ctx = _ctx(role_gaps={"draw": "low"})
        reasons = []
        score = _compute_profile_gap({"Card_Draw"}, set(), ctx, reasons)
        assert score == pytest.approx(15.0)

    def test_ok_gap_gives_5_points(self):
        ctx = _ctx(role_gaps={"draw": "ok"})
        reasons = []
        score = _compute_profile_gap({"Card_Draw"}, set(), ctx, reasons)
        assert score == pytest.approx(5.0)

    def test_high_gap_gives_minus_5_clamped_to_zero(self):
        """Over-supplied category → -5, but clamped to 0 minimum."""
        ctx = _ctx(role_gaps={"draw": "high"})
        reasons = []
        score = _compute_profile_gap({"Card_Draw"}, set(), ctx, reasons)
        assert score == 0.0

    def test_multiple_low_gaps_capped_at_30(self):
        """4 low-gap categories × 15 = 60, capped at 30."""
        ctx = _ctx(role_gaps={
            "draw": "low",
            "ramp": "low",
            "reanimation": "low",
            "removal": "low",
        })
        func_names = {"Card_Advantage", "Mana_Acceleration", "Recursion", "Removal"}
        reasons = []
        score = _compute_profile_gap(func_names, set(), ctx, reasons)
        assert score == pytest.approx(30.0)

    def test_mixed_gaps_partially_offset(self):
        """1 low (+15), 1 high (-5) → net 10, still within [0, 30]."""
        ctx = _ctx(role_gaps={"draw": "low", "ramp": "high"})
        func_names = {"Card_Draw", "Mana_Acceleration"}
        reasons = []
        score = _compute_profile_gap(func_names, set(), ctx, reasons)
        assert score == pytest.approx(10.0)

    def test_no_profile_no_gap_data_treats_as_ok(self):
        """Without profile, role_gaps is empty → every category treated as ok → 5."""
        ctx = _ctx(role_gaps={})
        reasons = []
        score = _compute_profile_gap({"Card_Draw"}, set(), ctx, reasons)
        assert score == pytest.approx(5.0)

    def test_empty_tags_returns_zero(self):
        ctx = _ctx(role_gaps={"draw": "low"})
        reasons = []
        score = _compute_profile_gap(set(), set(), ctx, reasons)
        assert score == 0.0


# ─── _compute_archetype_fit ───────────────────────────────────────────────────

class TestComputeArchetypeFit:

    def test_single_overlap_scores_3(self):
        ctx = _ctx(deck_archetype_tags=frozenset({"Reanimator"}))
        reasons = []
        score = _compute_archetype_fit({"Reanimator"}, ctx, reasons)
        assert score == pytest.approx(3.0)

    def test_three_overlaps_score_9(self):
        ctx = _ctx(deck_archetype_tags=frozenset({"Reanimator", "Graveyard", "Aristocrats"}))
        reasons = []
        score = _compute_archetype_fit({"Reanimator", "Graveyard", "Aristocrats"}, ctx, reasons)
        assert score == pytest.approx(9.0)

    def test_five_overlaps_capped_at_15(self):
        archetypes = frozenset({"Reanimator", "Graveyard", "Aristocrats", "Sacrifice", "Big_Mana"})
        ctx = _ctx(deck_archetype_tags=archetypes)
        reasons = []
        score = _compute_archetype_fit(archetypes, ctx, reasons)
        assert score == pytest.approx(15.0)

    def test_six_overlaps_still_capped_at_15(self):
        archetypes = frozenset({"Reanimator", "Graveyard", "Aristocrats", "Sacrifice", "Big_Mana", "Control"})
        ctx = _ctx(deck_archetype_tags=archetypes)
        reasons = []
        score = _compute_archetype_fit(archetypes, ctx, reasons)
        assert score == pytest.approx(15.0)

    def test_no_overlap_scores_zero(self):
        ctx = _ctx(deck_archetype_tags=frozenset({"Reanimator"}))
        reasons = []
        score = _compute_archetype_fit({"Tokens"}, ctx, reasons)
        assert score == 0.0

    def test_partial_overlap_scores_partial(self):
        ctx = _ctx(deck_archetype_tags=frozenset({"Reanimator", "Graveyard"}))
        reasons = []
        score = _compute_archetype_fit({"Reanimator", "Tokens"}, ctx, reasons)
        assert score == pytest.approx(3.0)

    def test_empty_deck_archetypes_always_zero(self):
        ctx = _ctx(deck_archetype_tags=frozenset())
        reasons = []
        score = _compute_archetype_fit({"Reanimator"}, ctx, reasons)
        assert score == 0.0


# ─── _compute_identity_score ──────────────────────────────────────────────────

class TestComputeIdentityScore:

    def test_engine_core_returns_10(self):
        reasons = []
        score = _compute_identity_score({"Engine_Core"}, reasons)
        assert score == pytest.approx(10.0)

    def test_grand_finisher_returns_10(self):
        reasons = []
        score = _compute_identity_score({"Grand_Finisher"}, reasons)
        assert score == pytest.approx(10.0)

    def test_apex_threat_returns_8(self):
        reasons = []
        score = _compute_identity_score({"Apex_Threat"}, reasons)
        assert score == pytest.approx(8.0)

    def test_takes_max_when_multiple_tags(self):
        """Apex_Threat(8) + Identity_Card(5) → max = 8."""
        reasons = []
        score = _compute_identity_score({"Apex_Threat", "Identity_Card"}, reasons)
        assert score == pytest.approx(8.0)

    def test_no_identity_tags_returns_zero(self):
        reasons = []
        score = _compute_identity_score(set(), reasons)
        assert score == 0.0

    def test_unknown_identity_tag_returns_zero(self):
        reasons = []
        score = _compute_identity_score({"UnknownTag"}, reasons)
        assert score == 0.0

    def test_reason_added_for_best_tag(self):
        reasons = []
        _compute_identity_score({"Engine_Core"}, reasons)
        assert any("Engine_Core" in r for r in reasons)

    def test_all_identity_tags_covered(self):
        """Every key in IDENTITY_SCORES maps to a positive value."""
        for tag_name, expected_score in IDENTITY_SCORES.items():
            reasons = []
            score = _compute_identity_score({tag_name}, reasons)
            assert score == pytest.approx(expected_score), f"Wrong score for {tag_name}"


# ─── _compute_mv_modifier ─────────────────────────────────────────────────────

class TestComputeMvModifier:

    # Sensitive roles
    def test_sensitive_role_cmc_1_gives_plus_5(self):
        reasons = []
        assert _compute_mv_modifier(1, "draw", reasons) == pytest.approx(5.0)

    def test_sensitive_role_cmc_2_gives_plus_3(self):
        reasons = []
        assert _compute_mv_modifier(2, "ramp", reasons) == pytest.approx(3.0)

    def test_sensitive_role_cmc_3_gives_plus_1(self):
        reasons = []
        assert _compute_mv_modifier(3, "removal", reasons) == pytest.approx(1.0)

    def test_sensitive_role_cmc_4_gives_minus_1(self):
        reasons = []
        assert _compute_mv_modifier(4, "draw", reasons) == pytest.approx(-1.0)

    def test_sensitive_role_cmc_5_gives_minus_3(self):
        reasons = []
        assert _compute_mv_modifier(5, "draw", reasons) == pytest.approx(-3.0)

    def test_sensitive_role_cmc_6_gives_minus_5(self):
        reasons = []
        assert _compute_mv_modifier(6, "ramp", reasons) == pytest.approx(-5.0)

    def test_sensitive_role_cmc_0_gives_plus_5(self):
        reasons = []
        assert _compute_mv_modifier(0, "sac_outlets", reasons) == pytest.approx(5.0)

    # Tolerant roles
    def test_tolerant_role_cmc_2_gives_plus_2(self):
        reasons = []
        assert _compute_mv_modifier(2, "reanimation", reasons) == pytest.approx(2.0)

    def test_tolerant_role_cmc_7_gives_zero(self):
        reasons = []
        assert _compute_mv_modifier(7, "wincons", reasons) == pytest.approx(0.0)

    def test_tolerant_role_cmc_5_gives_zero(self):
        reasons = []
        assert _compute_mv_modifier(5, "reanimation", reasons) == pytest.approx(0.0)

    # Neutral / no role
    def test_no_role_cmc_2_gives_plus_2(self):
        reasons = []
        assert _compute_mv_modifier(2, None, reasons) == pytest.approx(2.0)

    def test_no_role_cmc_4_gives_zero(self):
        reasons = []
        assert _compute_mv_modifier(4, None, reasons) == pytest.approx(0.0)

    def test_no_role_cmc_7_gives_minus_2(self):
        reasons = []
        assert _compute_mv_modifier(7, None, reasons) == pytest.approx(-2.0)

    def test_all_mv_sensitive_roles_are_tested(self):
        """All roles in MV_SENSITIVE_ROLES produce a non-zero modifier for CMC 1."""
        for role in MV_SENSITIVE_ROLES:
            reasons = []
            mod = _compute_mv_modifier(1, role, reasons)
            assert mod > 0, f"Expected positive modifier for sensitive role {role} at CMC 1"

    def test_all_mv_tolerant_roles_permit_high_cmc(self):
        """Tolerant roles produce 0 modifier for CMC 7 — no penalty for bombs."""
        for role in MV_TOLERANT_ROLES:
            reasons = []
            mod = _compute_mv_modifier(7, role, reasons)
            assert mod == pytest.approx(0.0), f"Expected 0 for tolerant role {role} at CMC 7"


# ─── score_card (end-to-end) ──────────────────────────────────────────────────

class TestScoreCard:

    def _simple_draw_card(self):
        """Tags for a CMC-2 draw card with Reanimator archetype and Engine_Core identity."""
        func_tags     = [_tag("Card_Draw", confidence=1.0)]
        mech_tags     = [_tag("Draw_Effect", layer="mechanical", confidence=1.0)]
        archetype_tags = [_tag("Reanimator", layer="archetype", confidence=0.8)]
        identity_tags  = [_tag("Engine_Core", layer="emotional", confidence=0.9)]
        return func_tags, mech_tags, archetype_tags, identity_tags

    def test_returns_score_breakdown(self):
        func, mech, arch, ident = self._simple_draw_card()
        ctx = _ctx(
            deck_archetype_tags=frozenset({"Reanimator"}),
            role_gaps={"draw": "low"},
            target_role="draw",
        )
        result = score_card("Necropotence", 3, func, mech, arch, ident, ctx)
        assert isinstance(result, ScoreBreakdown)
        assert result.card_name == "Necropotence"

    def test_total_score_is_sum_of_components(self):
        func, mech, arch, ident = self._simple_draw_card()
        ctx = _ctx(
            deck_archetype_tags=frozenset({"Reanimator"}),
            role_gaps={"draw": "low"},
            target_role="draw",
        )
        result = score_card("Necropotence", 3, func, mech, arch, ident, ctx)
        expected = (
            result.role_match_score
            + result.profile_gap_score
            + result.archetype_fit_score
            + result.identity_score
            + result.mana_value_modifier
        )
        assert result.total_score == pytest.approx(min(100.0, max(0.0, expected)))

    def test_total_score_never_exceeds_100(self):
        """Give the card every bonus possible — total must stay ≤ 100."""
        func_tags = [_tag("Card_Advantage", confidence=1.0), _tag("Mana_Acceleration", confidence=1.0)]
        mech_tags = [_tag("Board_Wipe", layer="mechanical", confidence=1.0)]
        archetype_tags = [_tag(a, layer="archetype") for a in ["Reanimator", "Graveyard", "Aristocrats", "Sacrifice", "Big_Mana"]]
        identity_tags  = [_tag("Engine_Core", layer="emotional", confidence=1.0)]
        ctx = _ctx(
            deck_archetype_tags=frozenset({"Reanimator", "Graveyard", "Aristocrats", "Sacrifice", "Big_Mana"}),
            role_gaps={"draw": "low", "ramp": "low", "board_wipes": "low"},
            target_role="draw",
        )
        result = score_card("Omnipotent Card", 0, func_tags, mech_tags, archetype_tags, identity_tags, ctx)
        assert result.total_score <= 100.0

    def test_total_score_never_below_zero(self):
        """Give the card every penalty — total must stay ≥ 0."""
        ctx = _ctx(
            deck_archetype_tags=frozenset({"Reanimator"}),
            role_gaps={"draw": "high", "ramp": "high"},
            target_role="draw",
        )
        # Card has no draw tags → role_match=0, no arch overlap, no identity, CMC 8 penalized
        result = score_card("Bad Card", 8, [], [], [_tag("Tokens", layer="archetype")], [], ctx)
        assert result.total_score >= 0.0

    def test_reasons_list_is_populated(self):
        func, mech, arch, ident = self._simple_draw_card()
        ctx = _ctx(target_role="draw", role_gaps={"draw": "low"})
        result = score_card("Test", 2, func, mech, arch, ident, ctx)
        assert len(result.reasons) > 0
        assert all(isinstance(r, str) for r in result.reasons)

    def test_high_confidence_beats_low_confidence(self):
        """Same role, higher confidence → higher score."""
        ctx = _ctx(target_role="draw", role_gaps={})
        high = score_card("High", 2,
            [_tag("Card_Draw", confidence=1.0)], [], [], [], ctx)
        low = score_card("Low", 2,
            [_tag("Card_Draw", confidence=0.4)], [], [], [], ctx)
        assert high.role_match_score > low.role_match_score

    def test_lower_cmc_beats_higher_in_sensitive_role(self):
        """CMC 2 draw card scores better than CMC 5 draw card."""
        ctx = _ctx(target_role="draw")
        cheap = score_card("Cheap", 2, [_tag("Card_Advantage", confidence=1.0)], [], [], [], ctx)
        pricey = score_card("Pricey", 5, [_tag("Card_Advantage", confidence=1.0)], [], [], [], ctx)
        assert cheap.total_score > pricey.total_score
