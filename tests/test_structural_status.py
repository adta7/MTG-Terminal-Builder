"""
test_structural_status.py — Tests for compute_structural_status().

Pure function — no database, no fixtures needed.
Tests different deck shapes to verify the readiness calculation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from deck_gap_analysis import (
    compute_structural_status,
    DECK_SIZE_TARGET,
    LAND_TARGET_MIN,
    LAND_TARGET_MAX,
    LAND_MINIMUM_FOR_EVAL,
)


class TestCurrentDeckState:
    """The actual Sheoldred deck: 87 cards, 10 lands."""

    def test_not_ready(self):
        status = compute_structural_status(87, 10)
        assert status["deck_readiness"] == "not_ready_for_final_evaluation"

    def test_role_counts_not_final(self):
        status = compute_structural_status(87, 10)
        assert status["role_counts_are_final"] is False

    def test_both_reasons_present(self):
        status = compute_structural_status(87, 10)
        assert "deck_below_100_cards" in status["reasons"]
        assert "land_count_below_minimum" in status["reasons"]

    def test_lands_needed(self):
        status = compute_structural_status(87, 10)
        assert status["lands_needed"] == LAND_TARGET_MIN - 10  # 26

    def test_nonland_cuts_needed(self):
        status = compute_structural_status(87, 10)
        # 77 nonlands - (100 - 36) target nonlands = 77 - 64 = 13
        assert status["nonland_cuts_needed"] == 13

    def test_nonland_count(self):
        status = compute_structural_status(87, 10)
        assert status["nonland_count"] == 77


class TestCompleteDecks:
    """Decks that should pass all structural checks."""

    def test_complete_deck_minimum_lands(self):
        """100 cards, exactly 36 lands — minimum passing configuration."""
        status = compute_structural_status(100, 36)
        assert status["deck_readiness"] == "ready_for_evaluation"
        assert status["role_counts_are_final"] is True
        assert status["reasons"] == []

    def test_complete_deck_max_lands(self):
        """100 cards, 37 lands — also passes."""
        status = compute_structural_status(100, 37)
        assert status["deck_readiness"] == "ready_for_evaluation"
        assert status["role_counts_are_final"] is True

    def test_complete_deck_heavy_lands(self):
        """100 cards, 40 lands — structurally complete even if land-heavy."""
        status = compute_structural_status(100, 40)
        assert status["deck_readiness"] == "ready_for_evaluation"


class TestLandCountProblems:
    """Decks with 100 cards but not enough lands."""

    def test_100_cards_25_lands_fails(self):
        """100 cards but only 25 lands — fails land check."""
        status = compute_structural_status(100, 25)
        assert status["deck_readiness"] == "not_ready_for_final_evaluation"
        assert "land_count_below_minimum" in status["reasons"]
        assert "deck_below_100_cards" not in status["reasons"]

    def test_100_cards_30_lands_passes(self):
        """100 cards, exactly LAND_MINIMUM_FOR_EVAL lands — just passes."""
        status = compute_structural_status(100, LAND_MINIMUM_FOR_EVAL)
        assert status["deck_readiness"] == "ready_for_evaluation"


class TestSizeProblems:
    """Decks short on cards but with enough lands."""

    def test_90_cards_36_lands(self):
        """Deck with enough lands but below 100 cards."""
        status = compute_structural_status(90, 36)
        assert status["deck_readiness"] == "not_ready_for_final_evaluation"
        assert "deck_below_100_cards" in status["reasons"]
        assert "land_count_below_minimum" not in status["reasons"]


class TestMathInvariants:
    """Verify structural math stays consistent."""

    def test_lands_needed_never_negative(self):
        """Decks with excess lands should show 0 needed, not negative."""
        status = compute_structural_status(100, 40)
        assert status["lands_needed"] == 0

    def test_nonland_cuts_needed_never_negative(self):
        """Decks already within target should show 0 cuts needed."""
        status = compute_structural_status(100, 36)
        assert status["nonland_cuts_needed"] == 0

    def test_deck_size_target_correct(self):
        status = compute_structural_status(87, 10)
        assert status["deck_size_target"] == DECK_SIZE_TARGET
        assert status["land_target_min"] == LAND_TARGET_MIN
        assert status["land_target_max"] == LAND_TARGET_MAX
