"""
test_report_outputs.py — Integration tests for report file generation.

Runs deck_gap_analysis.py once (module-scope fixture) and verifies:
  - All expected report files are written
  - JSON files parse successfully
  - Required JSON keys are present
  - Key invariants hold (e.g., current deck is not ready)

Depends on: data/collection_scan.sqlite and decks/bahahahah.json being present.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"
REPORTS_DIR  = PROJECT_ROOT / "reports" / "deck_analysis"


@pytest.fixture(scope="module")
def analysis_run():
    """Run the full analysis once. Fail fast if the script exits non-zero."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "deck_gap_analysis.py")],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, (
        f"deck_gap_analysis.py exited {result.returncode}:\n{result.stderr[-2000:]}"
    )
    return result


EXPECTED_REPORTS = [
    "gap_report.md",
    "role_counts.csv",
    "weighted_role_summary.csv",
    "weighted_role_targets.csv",
    "primary_role_summary.csv",
    "completion_plan.md",
    "deck_completion_simulation.md",
    "deck_completion_simulation.json",
    "preference_cut_review.md",
    "preference_cut_review.json",
    "structural_summary.json",
    "pattern_blindspots.csv",
    "candidates.md",
]


class TestReportFilesExist:
    @pytest.mark.parametrize("filename", EXPECTED_REPORTS)
    def test_report_file_written(self, analysis_run, filename):
        path = REPORTS_DIR / filename
        assert path.exists(), f"Expected report not found: reports/deck_analysis/{filename}"
        assert path.stat().st_size > 0, f"Report is empty: {filename}"


class TestSimulationJSON:

    def test_parses_as_valid_json(self, analysis_run):
        with open(REPORTS_DIR / "deck_completion_simulation.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_required_keys_present(self, analysis_run):
        with open(REPORTS_DIR / "deck_completion_simulation.json") as f:
            data = json.load(f)
        required = [
            "complete_confident_path_available",
            "medium_or_higher_confidence_cuts_available",
            "high_confidence_cuts",
            "medium_confidence_cuts",
            "human_required_cuts",
            "total_cuts_needed",
            "lands_to_add",
            "warning",
        ]
        for key in required:
            assert key in data, f"Missing key in deck_completion_simulation.json: '{key}'"

    def test_current_deck_cannot_be_completed_by_model(self, analysis_run):
        """87-card / 10-land deck always needs human input for remaining cuts."""
        with open(REPORTS_DIR / "deck_completion_simulation.json") as f:
            data = json.load(f)
        assert data["complete_confident_path_available"] is False

    def test_human_required_cuts_positive(self, analysis_run):
        with open(REPORTS_DIR / "deck_completion_simulation.json") as f:
            data = json.load(f)
        assert data["human_required_cuts"] > 0

    def test_cuts_add_up(self, analysis_run):
        """confident + human_required should approximately equal total_cuts_needed."""
        with open(REPORTS_DIR / "deck_completion_simulation.json") as f:
            data = json.load(f)
        confident   = data["medium_or_higher_confidence_cuts_available"]
        human       = data["human_required_cuts"]
        total       = data["total_cuts_needed"]
        # near-zero and role-review cards are in tier1 but not in confident or human
        assert confident + human <= total
        assert confident >= data["high_confidence_cuts"]

    def test_renamed_field_present(self, analysis_run):
        """Verify the Phase 7A rename landed correctly."""
        with open(REPORTS_DIR / "deck_completion_simulation.json") as f:
            data = json.load(f)
        assert "medium_or_higher_confidence_cuts_available" in data
        assert "confident_cuts_available" not in data, (
            "Old field name 'confident_cuts_available' should have been renamed"
        )


class TestPreferenceJSON:

    def test_parses_as_valid_json(self, analysis_run):
        with open(REPORTS_DIR / "preference_cut_review.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_required_keys_present(self, analysis_run):
        with open(REPORTS_DIR / "preference_cut_review.json") as f:
            data = json.load(f)
        for key in ["preference_profile_name", "preferences", "cuts_still_needed", "tier2_ranked"]:
            assert key in data, f"Missing key in preference_cut_review.json: '{key}'"

    def test_profile_name_correct(self, analysis_run):
        with open(REPORTS_DIR / "preference_cut_review.json") as f:
            data = json.load(f)
        assert data["preference_profile_name"] == "sheoldred_recursive_sacrifice_midrange"

    def test_tier2_ranked_is_list(self, analysis_run):
        with open(REPORTS_DIR / "preference_cut_review.json") as f:
            data = json.load(f)
        assert isinstance(data["tier2_ranked"], list)
        assert len(data["tier2_ranked"]) > 0

    def test_tier2_entries_have_required_fields(self, analysis_run):
        with open(REPORTS_DIR / "preference_cut_review.json") as f:
            data = json.load(f)
        required = ["name", "cmc", "base_net", "preference_adjusted_net", "primary_roles"]
        for entry in data["tier2_ranked"]:
            for field in required:
                assert field in entry, f"tier2_ranked entry missing field '{field}': {entry}"


class TestStructuralJSON:

    def test_parses_as_valid_json(self, analysis_run):
        with open(REPORTS_DIR / "structural_summary.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_required_keys_present(self, analysis_run):
        with open(REPORTS_DIR / "structural_summary.json") as f:
            data = json.load(f)
        for key in ["deck_readiness", "role_counts_are_final", "reasons",
                    "lands_needed", "nonland_cuts_needed"]:
            assert key in data, f"Missing key in structural_summary.json: '{key}'"

    def test_current_deck_not_ready(self, analysis_run):
        with open(REPORTS_DIR / "structural_summary.json") as f:
            data = json.load(f)
        assert data["deck_readiness"] == "not_ready_for_final_evaluation"
        assert data["role_counts_are_final"] is False


class TestValidationPasses:
    """The primary role validation should print 'All validation checks passed'."""

    def test_all_validation_checks_pass(self, analysis_run):
        assert "All validation checks passed" in analysis_run.stdout, (
            "Primary role validation failed — check PRIMARY_ROLE_OVERRIDES and "
            "PRIMARY_ROLE_VALIDATION in deck_gap_analysis.py"
        )
