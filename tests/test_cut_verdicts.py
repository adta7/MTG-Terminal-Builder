"""
test_cut_verdicts.py — Tests for cut verdict bands and model confidence.

Pure functions — no database, no fixtures needed.
These lock in the decision logic so UI or preference changes
can't silently corrupt the cut ranking.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from deck_gap_analysis import (
    cut_verdict, model_confidence,
    CUT_VERDICT_STRONG, CUT_VERDICT_BORDERLINE, CUT_VERDICT_NEAR_ZERO,
    CUT_VERDICT_ROLE_REVIEW, CUT_VERDICT_SKIP,
    ROLE_REVIEW_FDS_THRESHOLD,
)


class TestCutVerdictBands:
    """Each verdict band has a clear threshold — test the boundaries."""

    def test_strong_cut_high_net(self):
        """net >= 1.0, 0 primary, fds below threshold → strong."""
        assert cut_verdict(1.60, 0, 1.30) == CUT_VERDICT_STRONG

    def test_strong_cut_at_exact_threshold(self):
        assert cut_verdict(1.0, 0, 0.5) == CUT_VERDICT_STRONG

    def test_borderline_cut(self):
        """0.25 <= net < 1.0 → borderline."""
        assert cut_verdict(0.85, 0, 1.30) == CUT_VERDICT_BORDERLINE

    def test_borderline_lower_bound(self):
        assert cut_verdict(0.25, 0, 0.5) == CUT_VERDICT_BORDERLINE

    def test_near_zero(self):
        """0 < net < 0.25 → near_zero_review."""
        assert cut_verdict(0.10, 0, 1.30) == CUT_VERDICT_NEAR_ZERO

    def test_skip_at_zero(self):
        assert cut_verdict(0.0, 0, 0.5) == CUT_VERDICT_SKIP

    def test_skip_negative(self):
        """Negative net (cost > pressure) → do not cut."""
        assert cut_verdict(-1.2, 0, 0.5) == CUT_VERDICT_SKIP

    def test_skip_large_negative(self):
        """Gray Merchant under preferences: adj net -1.20."""
        assert cut_verdict(-1.20, 0, 0.5) == CUT_VERDICT_SKIP


class TestNeedsRoleReview:
    """needs_role_review takes priority over net-based bands when fds > threshold."""

    def test_high_net_flagged_as_review_when_fds_over_threshold(self):
        """Drivnod before threshold tuning had this issue — fds 1.30 is now below 1.5."""
        fds_above = ROLE_REVIEW_FDS_THRESHOLD + 0.1
        assert cut_verdict(1.60, 0, fds_above) == CUT_VERDICT_ROLE_REVIEW

    def test_borderline_net_flagged_as_review(self):
        fds_above = ROLE_REVIEW_FDS_THRESHOLD + 0.5
        assert cut_verdict(0.85, 0, fds_above) == CUT_VERDICT_ROLE_REVIEW

    def test_near_zero_flagged_as_review(self):
        fds_above = ROLE_REVIEW_FDS_THRESHOLD + 0.01
        assert cut_verdict(0.10, 0, fds_above) == CUT_VERDICT_ROLE_REVIEW

    def test_fds_at_exact_threshold_does_not_trigger(self):
        """FDS exactly at threshold should NOT trigger role review."""
        assert cut_verdict(1.60, 0, ROLE_REVIEW_FDS_THRESHOLD) == CUT_VERDICT_STRONG

    def test_fds_below_threshold_not_role_review(self):
        """FDS 1.30 < 1.5 threshold → normal band (Drivnod correct behavior)."""
        assert cut_verdict(1.60, 0, 1.30) == CUT_VERDICT_STRONG

    def test_primary_count_greater_than_zero_never_role_review(self):
        """Cards with primary roles are never flagged needs_role_review (they are Tier 2)."""
        fds_above = ROLE_REVIEW_FDS_THRESHOLD + 0.5
        assert cut_verdict(1.60, 1, fds_above) != CUT_VERDICT_ROLE_REVIEW
        assert cut_verdict(1.60, 3, fds_above) != CUT_VERDICT_ROLE_REVIEW


class TestCurrentDeckVerdicts:
    """
    Expected verdicts for the actual Sheoldred deck cards.
    These values were validated in Phase 6G and must not regress.
    """

    def test_drivnod_strong_cut(self):
        """Drivnod: net 1.60, fds 1.30 (< 1.5 threshold) → strong."""
        assert cut_verdict(1.60, 0, 1.30) == CUT_VERDICT_STRONG

    def test_nyx_lotus_strong_cut(self):
        """Nyx Lotus: net 1.30, fds 0.65 → strong."""
        assert cut_verdict(1.30, 0, 0.65) == CUT_VERDICT_STRONG

    def test_read_the_bones_borderline(self):
        """Read the Bones: net 0.85, fds 1.30 (< 1.5) → borderline."""
        assert cut_verdict(0.85, 0, 1.30) == CUT_VERDICT_BORDERLINE

    def test_night_whisper_near_zero(self):
        """Night's Whisper: net 0.10, fds 1.30 (< 1.5) → near_zero."""
        assert cut_verdict(0.10, 0, 1.30) == CUT_VERDICT_NEAR_ZERO

    def test_mind_stone_needs_role_review(self):
        """Mind Stone: net 0.40, fds 1.95 (> 1.5) → needs_role_review."""
        assert cut_verdict(0.40, 0, 1.95) == CUT_VERDICT_ROLE_REVIEW


class TestModelConfidence:

    def test_high_confidence_no_primary(self):
        """net >= 1.0 and 0 primary → high."""
        assert model_confidence(1.5, CUT_VERDICT_STRONG, 0) == "high"

    def test_high_confidence_not_awarded_with_primary(self):
        """Even net >= 1.0, with primary roles → medium (not high)."""
        assert model_confidence(1.5, CUT_VERDICT_STRONG, 1) == "medium"

    def test_medium_confidence_borderline(self):
        assert model_confidence(0.5, CUT_VERDICT_BORDERLINE, 0) == "medium"

    def test_medium_confidence_near_zero(self):
        """net 0.10 is >= 0.25? No — near zero → low."""
        assert model_confidence(0.10, CUT_VERDICT_NEAR_ZERO, 0) == "low"

    def test_low_confidence_role_review(self):
        """needs_role_review always returns low regardless of net."""
        assert model_confidence(1.6, CUT_VERDICT_ROLE_REVIEW, 0) == "low"

    def test_low_confidence_skip(self):
        assert model_confidence(-1.0, CUT_VERDICT_SKIP, 0) == "low"
