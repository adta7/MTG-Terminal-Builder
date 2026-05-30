"""
test_oracle_preprocessor.py — Tests for oracle text preprocessing.

Verify that oracle text is correctly segmented and searchable.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mtgdeck.oracle_preprocessor import (
    preprocess_oracle,
    _split_reminder_text,
    _detect_ability_kind,
    search_text,
)


class TestReminderTextSeparation:
    """Test separation of main text from reminder text."""

    def test_simple_keyword_with_reminder(self):
        """Flying keyword with reminder text should split correctly."""
        oracle = "Flying (This creature can't be blocked except by flying creatures.)"
        main, reminder = _split_reminder_text(oracle)

        assert main == "Flying"
        assert "can't be blocked" in reminder

    def test_multiple_abilities_with_reminders(self):
        """Multiple abilities with reminders should all separate."""
        oracle = "Flying (This creature can't be blocked except by flying creatures.)\nDeathtouch (Any amount of damage this deals to a creature is enough to make it be destroyed.)"
        main, reminder = _split_reminder_text(oracle)

        assert "Flying" in main
        assert "Deathtouch" in main
        assert "can't be blocked" in reminder
        assert "enough to make it" in reminder

    def test_activated_ability_no_reminder(self):
        """Activated abilities without reminder text should remain intact."""
        oracle = "Sacrifice a creature: Add {C}{C}."
        main, reminder = _split_reminder_text(oracle)

        assert main == oracle
        assert reminder == ""

    def test_triggered_ability_with_reminder(self):
        """Triggered ability with reminder should split correctly."""
        oracle = "Whenever a creature dies, you gain 1 life. (A creature leaves the battlefield when it dies.)"
        main, reminder = _split_reminder_text(oracle)

        assert "Whenever a creature dies" in main
        assert "A creature leaves the battlefield" in reminder


class TestAbilityDetection:
    """Test detection of ability kinds."""

    def test_activated_ability_detected(self):
        """Activated ability with colon should be detected."""
        text = "Sacrifice a creature: Add {C}{C}."
        kind = _detect_ability_kind(text)
        assert kind == "activated"

    def test_triggered_ability_detected(self):
        """Triggered ability starting with 'When' or 'Whenever' should be detected."""
        text1 = "When Ashnod's Altar enters the battlefield, draw a card."
        text2 = "Whenever a creature dies, you gain 1 life."

        assert _detect_ability_kind(text1) == "triggered"
        assert _detect_ability_kind(text2) == "triggered"

    def test_at_trigger_detected(self):
        """Triggered ability starting with 'At' should be detected."""
        text = "At the beginning of your upkeep, sacrifice Braids."
        kind = _detect_ability_kind(text)
        assert kind == "triggered"

    def test_replacement_effect_detected(self):
        """Replacement effect with 'instead' should be detected."""
        text = "Instead of paying this spell's mana cost, you may pay 1 life."
        kind = _detect_ability_kind(text)
        assert kind == "replacement"

    def test_static_ability_detected(self):
        """Static ability with keywords should be detected."""
        text = "Creatures you control have flying."
        kind = _detect_ability_kind(text)
        assert kind == "static"

    def test_keyword_static_detected(self):
        """Simple keyword (flying, lifelink) should be detected as static."""
        assert _detect_ability_kind("Flying") == "static"
        assert _detect_ability_kind("Lifelink") == "static"
        assert _detect_ability_kind("Deathtouch") == "static"


class TestOraclePreprocessing:
    """Test full oracle text preprocessing."""

    def test_ashnod_altar_preprocessing(self):
        """Ashnod's Altar should preprocess correctly."""
        oracle = "Sacrifice a creature: Add {C}{C}."
        result = preprocess_oracle("Ashnod's Altar", oracle)

        assert result.card_name == "Ashnod's Altar"
        assert result.original_oracle == oracle
        assert result.main_text == oracle  # No reminder text
        assert len(result.segments) > 0
        assert result.segments[0].ability_kind == "activated"

    def test_blood_artist_preprocessing(self):
        """Blood Artist with multiple abilities should preprocess correctly."""
        oracle = "Lifelink\nWhenever Blood Artist or another creature dies, target opponent loses 1 life and you gain 1 life."
        result = preprocess_oracle("Blood Artist", oracle)

        assert "Lifelink" in result.main_text
        assert "Whenever" in result.main_text
        assert len(result.segments) == 2  # Two lines = two segments

    def test_normalized_oracle_lowercase(self):
        """Normalized oracle should be lowercase for pattern matching."""
        oracle = "Flying (This creature can't be blocked except by flying creatures.)"
        result = preprocess_oracle("Test Card", oracle)

        assert result.normalized_oracle == oracle.lower()

    def test_empty_oracle_text(self):
        """Empty oracle text should not crash."""
        result = preprocess_oracle("Blank Card", "")

        assert result.card_name == "Blank Card"
        assert result.original_oracle == ""
        assert len(result.segments) == 0

    def test_multi_line_oracle(self):
        """Multi-line oracle text should split into segments."""
        oracle = "Flying\nDeathtouch\nWhenever a creature dies, you gain 1 life."
        result = preprocess_oracle("Test", oracle)

        assert len(result.segments) == 3
        assert result.segments[0].text == "Flying"
        assert result.segments[1].text == "Deathtouch"
        assert "Whenever" in result.segments[2].text


class TestTextSearch:
    """Test pattern searching in preprocessed text."""

    def test_search_in_main_text(self):
        """Should find pattern in main text."""
        oracle = "Sacrifice a creature: Add {C}{C}."
        result = preprocess_oracle("Test", oracle)

        matches = search_text(result, r"Sacrifice a creature", search_in="main")
        assert len(matches) > 0

    def test_search_excludes_reminder_text(self):
        """Search in 'main' should not match reminder text."""
        oracle = "Flying (This creature can't be blocked except by flying creatures.)"
        result = preprocess_oracle("Test", oracle)

        # "blocked" is in reminder text, not main
        matches = search_text(result, r"blocked", search_in="main")
        assert len(matches) == 0

    def test_search_in_reminder(self):
        """Should find pattern in reminder text."""
        oracle = "Flying (This creature can't be blocked except by flying creatures.)"
        result = preprocess_oracle("Test", oracle)

        matches = search_text(result, r"blocked", search_in="reminder")
        assert len(matches) > 0

    def test_search_in_normalized(self):
        """Should find pattern in normalized (lowercased) text."""
        oracle = "Sacrifice A CREATURE: Add {C}{C}."
        result = preprocess_oracle("Test", oracle)

        matches = search_text(result, r"sacrifice a creature", search_in="normalized")
        assert len(matches) > 0

    def test_search_returns_spans(self):
        """Search should return correct character spans."""
        oracle = "Sacrifice a creature: Add {C}{C}."
        result = preprocess_oracle("Test", oracle)

        matches = search_text(result, r"Add \{C\}\{C\}", search_in="main")
        assert len(matches) > 0

        # Check the span points to the right text
        for start, end in matches:
            span_text = oracle[start:end]
            assert "{C}{C}" in span_text


class TestSegmentAbilityKind:
    """Test that segments have correct ability kinds."""

    def test_activated_segment(self):
        """Activated ability segment should have correct kind."""
        oracle = "Sacrifice a creature: Add {C}{C}."
        result = preprocess_oracle("Test", oracle)

        assert len(result.segments) > 0
        assert result.segments[0].ability_kind == "activated"

    def test_triggered_segment(self):
        """Triggered ability segment should have correct kind."""
        oracle = "Whenever a creature dies, you gain 1 life."
        result = preprocess_oracle("Test", oracle)

        assert len(result.segments) > 0
        assert result.segments[0].ability_kind == "triggered"

    def test_mixed_ability_kinds(self):
        """Card with mixed ability kinds should segment correctly."""
        oracle = "Flying\nSacrifice a creature: Add {C}{C}.\nWhenever a creature dies, gain 1 life."
        result = preprocess_oracle("Test", oracle)

        assert len(result.segments) == 3
        assert result.segments[0].ability_kind == "static"  # Flying
        assert result.segments[1].ability_kind == "activated"
        assert result.segments[2].ability_kind == "triggered"
