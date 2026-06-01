"""
test_interactive_cut_review.py — Tests for Phase 9 CLI helper functions.

Tests the pure functions: level_to_weight, weight_to_label.
No DB, no file system, no user input.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from interactive_cut_review import level_to_weight, weight_to_label, PILLAR_WEIGHTS, CURVE_WEIGHTS


class TestLevelToWeight:

    # Valid pillar inputs
    def test_low(self):
        assert level_to_weight("low") == 0.5

    def test_medium(self):
        assert level_to_weight("medium") == 1.0

    def test_high(self):
        assert level_to_weight("high") == 1.5

    def test_very_high(self):
        assert level_to_weight("very_high") == 2.0

    # Blank = keep default
    def test_blank_returns_none(self):
        assert level_to_weight("") is None

    def test_whitespace_returns_none(self):
        assert level_to_weight("   ") is None

    # Case insensitive
    def test_uppercase_accepted(self):
        assert level_to_weight("HIGH") == 1.5

    def test_mixed_case_accepted(self):
        assert level_to_weight("Medium") == 1.0

    # Curve weights (different scale)
    def test_curve_low_is_zero(self):
        assert level_to_weight("low", is_curve=True) == 0.0

    def test_curve_medium(self):
        assert level_to_weight("medium", is_curve=True) == 0.5

    def test_curve_high(self):
        assert level_to_weight("high", is_curve=True) == 1.0

    def test_curve_very_high(self):
        assert level_to_weight("very_high", is_curve=True) == 1.5

    # Invalid input raises ValueError
    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            level_to_weight("super_high")

    def test_number_raises(self):
        with pytest.raises(ValueError):
            level_to_weight("1.5")

    def test_typo_raises(self):
        with pytest.raises(ValueError):
            level_to_weight("hight")


class TestWeightToLabel:

    def test_pillar_low(self):
        assert weight_to_label(0.5) == "low"

    def test_pillar_medium(self):
        assert weight_to_label(1.0) == "medium"

    def test_pillar_high(self):
        assert weight_to_label(1.5) == "high"

    def test_pillar_very_high(self):
        assert weight_to_label(2.0) == "very_high"

    def test_curve_low(self):
        assert weight_to_label(0.0, is_curve=True) == "low"

    def test_curve_medium(self):
        assert weight_to_label(0.5, is_curve=True) == "medium"

    def test_unknown_weight_returns_string(self):
        """Unknown weight values fall back to numeric string."""
        assert weight_to_label(0.7) == "0.7"

    def test_roundtrip_pillar(self):
        """Every pillar level should survive a label → weight → label roundtrip."""
        for label in PILLAR_WEIGHTS:
            w = level_to_weight(label)
            assert weight_to_label(w) == label

    def test_roundtrip_curve(self):
        for label in CURVE_WEIGHTS:
            w = level_to_weight(label, is_curve=True)
            assert weight_to_label(w, is_curve=True) == label


class TestWeightScales:
    """Verify the two weight scales are correct and distinct."""

    def test_pillar_weights_cover_expected_range(self):
        vals = list(PILLAR_WEIGHTS.values())
        assert min(vals) == 0.5
        assert max(vals) == 2.0

    def test_curve_weights_cover_expected_range(self):
        vals = list(CURVE_WEIGHTS.values())
        assert min(vals) == 0.0
        assert max(vals) == 1.5

    def test_curve_max_lower_than_pillar_max(self):
        """Curve scale tops out lower to prevent curve pressure from dominating."""
        assert max(CURVE_WEIGHTS.values()) < max(PILLAR_WEIGHTS.values())

    def test_all_pillar_levels_distinct(self):
        vals = list(PILLAR_WEIGHTS.values())
        assert len(vals) == len(set(vals))

    def test_all_curve_levels_distinct(self):
        vals = list(CURVE_WEIGHTS.values())
        assert len(vals) == len(set(vals))
