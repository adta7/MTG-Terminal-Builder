"""
test_recommender.py — Integration tests for Phase 4 suggestions and cuts.

Uses an in-memory database. Tests cover:
  - build_context: archetype threshold (≥3 cards), role_gaps with/without profile
  - _find_candidates_for_role: tag-based lookup, deck exclusion
  - suggest: sorted results, deck exclusion, top_n limit, zero-score exclusion
  - cuts: commander exclusion, land exclusion, include_lands, count limit, ordering
  - _score_as_cut: keep_score components (confidence, gap, identity, archetype, multi-function)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mtgdeck.database import Database
from mtgdeck.models import Card, Deck, DeckCard, DeckAnalysis
from mtgdeck import tags
from mtgdeck.profiles import Profile
from mtgdeck.recommender import (
    Suggestion,
    CutCandidate,
    build_context,
    cuts,
    suggest,
    _find_candidates_for_role,
    _score_as_cut,
)
from mtgdeck.scoring import ScoringContext


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    database = Database(":memory:")
    database.init_db()
    tags.seed_tags(database)
    yield database
    database.close()


def _make_card(
    name: str,
    cmc: int = 2,
    type_line: str = "Creature",
    oracle_text: str = "",
) -> Card:
    return Card(
        name=name,
        mana_cost="",
        cmc=cmc,
        type_line=type_line,
        oracle_text=oracle_text,
    )


def _make_deck(*card_names: str, commander: str | None = None) -> Deck:
    return Deck(
        name="Test",
        cards=[DeckCard(name=n, count=1) for n in card_names],
        commander=commander,
    )


def _make_analysis(land_count: int = 35, avg_mv: float = 3.2) -> DeckAnalysis:
    return DeckAnalysis(
        deck_name="Test",
        total_cards=100,
        land_count=land_count,
        spell_permanent_count=50,
        spell_nonpermanent_count=15,
        avg_mana_value=avg_mv,
    )


def _seed_card_with_tags(db, name: str, cmc: int = 2, func=(), mech=(), arch=(), ident=(), type_line="Creature"):
    """Insert a card into the DB and apply the given tag sets."""
    db.insert_card(_make_card(name, cmc=cmc, type_line=type_line))
    for tag in func:
        db.tag_card(name, tag, confidence=1.0, source="test")
    for tag in mech:
        db.tag_card(name, tag, confidence=1.0, source="test")
    for tag in arch:
        db.tag_card(name, tag, confidence=0.8, source="test")
    for tag in ident:
        db.tag_card(name, tag, confidence=0.9, source="test")


# ─── build_context ────────────────────────────────────────────────────────────

class TestBuildContext:

    def test_archetype_tag_in_3_cards_is_included(self, db):
        for name in ["Card A", "Card B", "Card C"]:
            _seed_card_with_tags(db, name, arch=["Reanimator"])
        deck = _make_deck("Card A", "Card B", "Card C")
        ctx = build_context(deck, db, _make_analysis())
        assert "Reanimator" in ctx.deck_archetype_tags

    def test_archetype_tag_in_2_cards_not_included(self, db):
        for name in ["Card A", "Card B"]:
            _seed_card_with_tags(db, name, arch=["Reanimator"])
        deck = _make_deck("Card A", "Card B")
        ctx = build_context(deck, db, _make_analysis())
        assert "Reanimator" not in ctx.deck_archetype_tags

    def test_multiple_archetypes_can_qualify(self, db):
        for name in ["A", "B", "C"]:
            _seed_card_with_tags(db, name, arch=["Reanimator", "Graveyard"])
        deck = _make_deck("A", "B", "C")
        ctx = build_context(deck, db, _make_analysis())
        assert "Reanimator" in ctx.deck_archetype_tags
        assert "Graveyard" in ctx.deck_archetype_tags

    def test_role_gaps_empty_without_profile(self, db):
        deck = _make_deck()
        ctx = build_context(deck, db, _make_analysis(), profile=None)
        assert ctx.role_gaps == {}

    def test_role_gaps_populated_with_profile(self, db):
        profile = Profile(
            name="Test",
            description="",
            targets={"ramp": [10, 13]},
        )
        # No ramp cards in deck → gap is "low"
        deck = _make_deck()
        ctx = build_context(deck, db, _make_analysis(), profile=profile)
        assert ctx.role_gaps.get("ramp") == "low"

    def test_target_role_propagated(self, db):
        deck = _make_deck()
        ctx = build_context(deck, db, _make_analysis(), target_role="draw")
        assert ctx.target_role == "draw"

    def test_profile_name_propagated(self, db):
        profile = Profile(name="Mono Black Reanimator", description="", targets={})
        deck = _make_deck()
        ctx = build_context(deck, db, _make_analysis(), profile=profile)
        assert ctx.profile_name == "Mono Black Reanimator"

    def test_avg_mv_from_analysis(self, db):
        deck = _make_deck()
        ctx = build_context(deck, db, _make_analysis(avg_mv=3.75))
        assert ctx.avg_mana_value == pytest.approx(3.75)


# ─── _find_candidates_for_role ────────────────────────────────────────────────

class TestFindCandidatesForRole:

    def test_finds_card_with_matching_functional_tag(self, db):
        _seed_card_with_tags(db, "Necropotence", func=["Card_Draw"])
        deck = _make_deck()
        candidates = _find_candidates_for_role("draw", db, deck)
        assert "Necropotence" in candidates

    def test_finds_card_with_matching_mechanical_tag(self, db):
        _seed_card_with_tags(db, "Toxic Deluge", mech=["Board_Wipe"])
        deck = _make_deck()
        candidates = _find_candidates_for_role("board_wipes", db, deck)
        assert "Toxic Deluge" in candidates

    def test_excludes_cards_already_in_deck(self, db):
        _seed_card_with_tags(db, "Necropotence", func=["Card_Advantage"])
        deck = _make_deck("Necropotence")
        candidates = _find_candidates_for_role("draw", db, deck)
        assert "Necropotence" not in candidates

    def test_excludes_cards_with_no_matching_tags(self, db):
        _seed_card_with_tags(db, "Lightning Bolt", func=["Removal"])
        deck = _make_deck()
        candidates = _find_candidates_for_role("draw", db, deck)
        assert "Lightning Bolt" not in candidates

    def test_returns_sorted_list(self, db):
        for name in ["Zebra Card", "Apple Card"]:
            _seed_card_with_tags(db, name, func=["Card_Advantage"])
        candidates = _find_candidates_for_role("draw", db, _make_deck())
        assert candidates == sorted(candidates)

    def test_unknown_role_returns_empty(self, db):
        candidates = _find_candidates_for_role("not_a_real_role", db, _make_deck())
        assert candidates == []

    def test_deck_exclusion_is_case_insensitive(self, db):
        _seed_card_with_tags(db, "Necropotence", func=["Card_Advantage"])
        deck = _make_deck("necropotence")  # lowercase in deck
        candidates = _find_candidates_for_role("draw", db, deck)
        assert "Necropotence" not in candidates


# ─── suggest ──────────────────────────────────────────────────────────────────

class TestSuggest:

    def test_returns_suggestions_for_role(self, db):
        _seed_card_with_tags(db, "Necropotence", cmc=3, func=["Card_Draw"])
        deck = _make_deck()
        results = suggest(deck, db, _make_analysis(), role="draw")
        names = [s.card_name for s in results]
        assert "Necropotence" in names

    def test_excludes_cards_already_in_deck(self, db):
        _seed_card_with_tags(db, "Necropotence", func=["Card_Advantage"])
        deck = _make_deck("Necropotence")
        results = suggest(deck, db, _make_analysis(), role="draw")
        assert all(s.card_name != "Necropotence" for s in results)

    def test_results_sorted_by_score_descending(self, db):
        # High confidence (1.0) card should rank above low confidence (0.4) card
        db.insert_card(_make_card("High Quality Draw", cmc=2))
        db.tag_card("High Quality Draw", "Card_Advantage", confidence=1.0, source="test")
        db.insert_card(_make_card("Low Quality Draw", cmc=2))
        db.tag_card("Low Quality Draw", "Card_Advantage", confidence=0.4, source="test")

        deck = _make_deck()
        results = suggest(deck, db, _make_analysis(), role="draw")
        scores = [s.score.total_score for s in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_limits_results(self, db):
        for i in range(5):
            _seed_card_with_tags(db, f"Draw Card {i}", cmc=2, func=["Card_Advantage"])
        deck = _make_deck()
        results = suggest(deck, db, _make_analysis(), role="draw", top_n=3)
        assert len(results) <= 3

    def test_results_are_suggestion_objects(self, db):
        _seed_card_with_tags(db, "Necropotence", func=["Card_Advantage"])
        deck = _make_deck()
        results = suggest(deck, db, _make_analysis(), role="draw")
        assert all(isinstance(s, Suggestion) for s in results)

    def test_mana_value_populated(self, db):
        _seed_card_with_tags(db, "Necropotence", cmc=3, func=["Card_Draw"])
        deck = _make_deck()
        results = suggest(deck, db, _make_analysis(), role="draw")
        nec = next(s for s in results if s.card_name == "Necropotence")
        assert nec.mana_value == 3

    def test_unknown_role_returns_empty(self, db):
        deck = _make_deck()
        results = suggest(deck, db, _make_analysis(), role="not_a_real_role")
        assert results == []

    def test_profile_gap_aware_scoring(self, db):
        """Card filling a 'low' role should score higher than when gap is 'ok'."""
        _seed_card_with_tags(db, "Draw Card", cmc=2, func=["Card_Draw"])
        deck = _make_deck()
        profile_low  = Profile("Test", "", {"draw": [10, 14]})
        profile_full = Profile("Test", "", {"draw": [0, 100]})
        analysis = _make_analysis()

        with_gap    = suggest(deck, db, analysis, role="draw", profile=profile_low)
        without_gap = suggest(deck, db, analysis, role="draw", profile=profile_full)

        low_score  = next(s.score.total_score for s in with_gap if s.card_name == "Draw Card")
        ok_score   = next(s.score.total_score for s in without_gap if s.card_name == "Draw Card")
        assert low_score > ok_score


# ─── cuts ─────────────────────────────────────────────────────────────────────

class TestCuts:

    def test_excludes_commander_from_cuts(self, db):
        _seed_card_with_tags(db, "Commander Card", cmc=4)
        _seed_card_with_tags(db, "Filler Card", cmc=5)
        deck = _make_deck("Commander Card", "Filler Card", commander="Commander Card")
        results = cuts(deck, db, _make_analysis())
        assert all(c.card_name != "Commander Card" for c in results)

    def test_excludes_lands_by_default(self, db):
        db.insert_card(_make_card("Swamp", cmc=0, type_line="Basic Land"))
        _seed_card_with_tags(db, "Creature Card", cmc=3)
        deck = _make_deck("Swamp", "Creature Card")
        results = cuts(deck, db, _make_analysis())
        assert all(c.card_name != "Swamp" for c in results)

    def test_basic_lands_always_excluded(self, db):
        """Basic lands should never appear as cut candidates, even with include_lands=True.
        They are handled by land-count analysis, not individual card scoring.
        """
        db.insert_card(_make_card("Swamp", cmc=0, type_line="Basic Land — Swamp"))
        _seed_card_with_tags(db, "Creature Card", cmc=3)
        deck = _make_deck("Swamp", "Creature Card")
        # Even with include_lands=True, basics are excluded
        results = cuts(deck, db, _make_analysis(), include_lands=True)
        assert all(c.card_name != "Swamp" for c in results)

    def test_nonbasic_lands_included_when_flag_set(self, db):
        """Non-basic utility lands should be evaluated as potential cuts when include_lands=True."""
        db.insert_card(_make_card("Cabal Coffers", cmc=0, type_line="Land"))
        deck = _make_deck("Cabal Coffers")
        results = cuts(deck, db, _make_analysis(), include_lands=True)
        names = [c.card_name for c in results]
        assert "Cabal Coffers" in names

    def test_count_limits_results(self, db):
        for i in range(8):
            _seed_card_with_tags(db, f"Card {i}", cmc=3)
        deck = _make_deck(*[f"Card {i}" for i in range(8)])
        results = cuts(deck, db, _make_analysis(), count=3)
        assert len(results) <= 3

    def test_results_sorted_by_cut_score_descending(self, db):
        for i in range(4):
            _seed_card_with_tags(db, f"Card {i}", cmc=i + 2)
        deck = _make_deck(*[f"Card {i}" for i in range(4)])
        results = cuts(deck, db, _make_analysis())
        scores = [c.cut_score for c in results]
        assert scores == sorted(scores, reverse=True)

    def test_cut_score_is_complement_of_keep_score(self, db):
        _seed_card_with_tags(db, "Test Card", cmc=3)
        deck = _make_deck("Test Card")
        results = cuts(deck, db, _make_analysis())
        for c in results:
            assert c.cut_score == pytest.approx(100.0 - c.keep_score)

    def test_returns_cut_candidate_objects(self, db):
        _seed_card_with_tags(db, "Test Card", cmc=3)
        deck = _make_deck("Test Card")
        results = cuts(deck, db, _make_analysis())
        assert all(isinstance(c, CutCandidate) for c in results)

    def test_mana_value_populated(self, db):
        _seed_card_with_tags(db, "Big Card", cmc=7)
        deck = _make_deck("Big Card")
        results = cuts(deck, db, _make_analysis())
        big = next((c for c in results if c.card_name == "Big Card"), None)
        if big:
            assert big.mana_value == 7


# ─── _score_as_cut ─────────────────────────────────────────────────────────────

class TestScoreAsCut:

    def _ctx(self, role_gaps=None, deck_archetypes=frozenset()):
        return ScoringContext(
            deck_archetype_tags=frozenset(deck_archetypes),
            role_gaps=role_gaps or {},
            avg_mana_value=3.2,
            target_role=None,
            profile_name=None,
        )

    def _tag(self, name: str, layer: str = "functional", confidence: float = 1.0):
        return {"name": name, "layer": layer, "confidence": confidence, "source": "test", "note": ""}

    def test_base_keep_score_is_50(self):
        ctx = self._ctx()
        candidate = _score_as_cut("Card", 3, [], [], [], [], [], ctx)
        # With no tags, should be near 50 - penalty
        assert candidate.keep_score < 55

    def test_high_confidence_increases_keep_score(self):
        """High confidence (1.0) → (1.0 - 0.5) × 20 = +10 bonus."""
        ctx = self._ctx()
        tag = self._tag("Card_Advantage", confidence=1.0)
        candidate = _score_as_cut("Card", 3, [tag], [], [], [], [tag], ctx)
        assert candidate.keep_score > 50

    def test_low_gap_increases_keep_score(self):
        ctx = self._ctx(role_gaps={"draw": "low"})
        func_tag = self._tag("Card_Draw", confidence=1.0)
        candidate_low  = _score_as_cut("Card", 3, [func_tag], [], [], [], [func_tag], ctx)
        ctx_none = self._ctx(role_gaps={})
        candidate_none = _score_as_cut("Card", 3, [func_tag], [], [], [], [func_tag], ctx_none)
        assert candidate_low.keep_score > candidate_none.keep_score

    def test_high_gap_decreases_keep_score(self):
        ctx = self._ctx(role_gaps={"draw": "high"})
        func_tag = self._tag("Card_Draw", confidence=1.0)
        candidate_high = _score_as_cut("Card", 3, [func_tag], [], [], [], [func_tag], ctx)
        ctx_none = self._ctx(role_gaps={})
        candidate_none = _score_as_cut("Card", 3, [func_tag], [], [], [], [func_tag], ctx_none)
        assert candidate_high.keep_score < candidate_none.keep_score

    def test_engine_core_gets_large_keep_bonus(self):
        """Engine_Core should add 12 to keep_score — prevents it from appearing in cuts."""
        ctx = self._ctx()
        id_tag = self._tag("Engine_Core", layer="emotional", confidence=1.0)
        tag = self._tag("Card_Advantage", confidence=1.0)
        candidate = _score_as_cut("Necropotence", 3, [tag], [], [], [id_tag], [tag, id_tag], ctx)
        assert candidate.keep_score > 60

    def test_archetype_overlap_increases_keep_score(self):
        ctx = self._ctx(deck_archetypes=frozenset({"Reanimator"}))
        func_tag  = self._tag("Card_Advantage", confidence=1.0)
        arch_tag  = self._tag("Reanimator", layer="archetype", confidence=0.8)
        all_tags  = [func_tag, arch_tag]
        candidate = _score_as_cut("Card", 3, [func_tag], [], [arch_tag], [], all_tags, ctx)
        ctx_no_arch = self._ctx(deck_archetypes=frozenset())
        candidate_no = _score_as_cut("Card", 3, [func_tag], [], [arch_tag], [], all_tags, ctx_no_arch)
        assert candidate.keep_score > candidate_no.keep_score

    def test_multi_function_card_gets_plus_5(self):
        """Card filling 2 categories gets +5 keep bonus."""
        ctx = self._ctx()
        func_tags = [
            self._tag("Card_Draw", confidence=1.0),
            self._tag("Mana_Acceleration", confidence=1.0),
        ]
        all_tags = func_tags
        candidate = _score_as_cut("Swiss Army Card", 2, func_tags, [], [], [], all_tags, ctx)
        # Multi-function bonus should appear in reasons
        assert any("Multi-function" in r for r in candidate.reasons)

    def test_no_category_card_gets_penalty(self):
        """Card filling no profile category gets -5 keep score penalty."""
        ctx = self._ctx()
        func_tag = self._tag("Threat")  # "Threat" is not mapped to any profile category
        all_tags = [func_tag]
        candidate = _score_as_cut("Off-plan Card", 3, [func_tag], [], [], [], all_tags, ctx)
        assert any("No profile role" in r or "no profile" in r.lower() for r in candidate.reasons)

    def test_untagged_card_gets_penalty(self):
        ctx = self._ctx()
        candidate = _score_as_cut("Untagged", 3, [], [], [], [], [], ctx)
        assert any("Untagged" in r for r in candidate.reasons)

    def test_reasons_is_non_empty(self):
        ctx = self._ctx()
        func_tag = self._tag("Card_Advantage", confidence=1.0)
        candidate = _score_as_cut("Card", 2, [func_tag], [], [], [], [func_tag], ctx)
        assert len(candidate.reasons) > 0
