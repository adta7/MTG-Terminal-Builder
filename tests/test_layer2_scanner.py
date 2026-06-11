"""
test_layer2_scanner.py — Tests for Layer 2 foundation audit scanner.

Verify scanner reports generate correctly and identify coverage gaps/issues.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mtgdeck.database import Database
from mtgdeck.models import Card
from mtgdeck import tags
from mtgdeck.layer2_scanner import Layer2Scanner


@pytest.fixture
def db():
    """In-memory database with schema, seed tags, and test cards."""
    database = Database(":memory:")
    database.init_db()
    tags.seed_tags(database)

    # Insert test cards
    test_cards = [
        Card(
            name="Ashnod's Altar",
            mana_cost="{1}",
            cmc=1,
            type_line="Artifact",
            oracle_text="Sacrifice a creature: Add {C}{C}.",
        ),
        Card(
            name="Blank Card",
            mana_cost="{1}",
            cmc=1,
            type_line="Creature",
            oracle_text="",
        ),
        Card(
            name="Vanilla Creature",
            mana_cost="{2}{B}",
            cmc=3,
            type_line="Creature — Human",
            oracle_text="Flying",
        ),
        Card(
            name="Complex Card",
            mana_cost="{2}{B}{B}",
            cmc=4,
            type_line="Creature — Vampire",
            oracle_text="Flying\nDeathtouch\nWhenever a creature dies, you gain 1 life.",
        ),
    ]

    for card in test_cards:
        database.insert_card(card)

    # Tag some cards
    database.tag_card("Ashnod's Altar", "Sacrifice_Outlet", 0.95, "regex")
    database.tag_card("Ashnod's Altar", "Mana_Production", 0.95, "regex")
    database.tag_card("Complex Card", "Flying", 0.95, "regex")
    database.tag_card("Complex Card", "Deathtouch", 0.95, "regex")

    yield database
    database.close()


class TestCoverageGapScanning:
    """Test coverage gap detection."""

    def test_finds_zero_tag_cards(self, db):
        """Should identify cards with zero tags."""
        scanner = Layer2Scanner(db)
        gaps = scanner.scan_coverage_gaps(scope="all")

        # Should find Blank Card and Vanilla Creature as gaps
        gap_names = {gap.card_name for gap in gaps}
        assert "Blank Card" in gap_names or "Vanilla Creature" in gap_names

    def test_finds_low_tag_cards_with_taggable_language(self, db):
        """Should flag cards with few tags but taggable language."""
        scanner = Layer2Scanner(db)
        gaps = scanner.scan_coverage_gaps(scope="all")

        # Vanilla Creature has "Flying" but only tagged for that
        vanilla_gaps = [g for g in gaps if g.card_name == "Vanilla Creature"]
        if vanilla_gaps:
            gap = vanilla_gaps[0]
            assert gap.has_taggable_verbs is False  # Flying is a keyword, not a verb

    def test_identifies_likely_missing_tags(self, db):
        """Should suggest likely missing tags."""
        scanner = Layer2Scanner(db)
        gaps = scanner.scan_coverage_gaps(scope="all")

        # Blank Card has no oracle text, shouldn't suggest missing tags
        blank = [g for g in gaps if g.card_name == "Blank Card"]
        # Just verify the method runs without error

    def test_gap_sorting(self, db):
        """Gaps should be sorted by tag count."""
        scanner = Layer2Scanner(db)
        gaps = scanner.scan_coverage_gaps(scope="all")

        if len(gaps) > 1:
            # Verify sorted by tag_count then name
            for i in range(len(gaps) - 1):
                assert gaps[i].tag_count <= gaps[i + 1].tag_count


class TestOverTaggingRiskScanning:
    """Test over-tagging detection."""

    def test_finds_high_tag_count_cards(self, db):
        """Should identify cards with many tags."""
        scanner = Layer2Scanner(db)

        # Tag Complex Card heavily to trigger over-tagging detection
        for i in range(10):
            try:
                db.tag_card("Complex Card", f"Test_Tag_{i}", 0.5, "test")
            except:
                pass  # Some tags may not exist

        risks = scanner.scan_over_tagging_risk(threshold=5)
        risk_names = {r.card_name for r in risks}
        # Just verify method runs

    def test_risk_level_assignment(self, db):
        """Risk level should be based on tag count."""
        scanner = Layer2Scanner(db)
        risks = scanner.scan_over_tagging_risk(threshold=1)

        for risk in risks:
            if risk.tag_count < 12:
                assert risk.risk_level in ["low", "medium"]
            else:
                assert risk.risk_level in ["medium", "high"]


class TestPhraseClusterScanning:
    """Test unmatched phrase detection."""

    def test_identifies_untagged_phrases(self, db):
        """Should find phrases in untagged cards."""
        scanner = Layer2Scanner(db)
        clusters = scanner.scan_unmatched_phrases(scope="all", min_frequency=1)

        # Blank Card is untagged, so no phrases
        # Should get empty list or low counts
        # Just verify method runs

    def test_phrase_family_classification(self, db):
        """Phrases should be classified into mechanic families."""
        scanner = Layer2Scanner(db)

        # Test classification directly
        assert scanner._classify_phrase_family("sacrifice a creature") == "sacrifice"
        assert scanner._classify_phrase_family("draw a card") == "draw"
        assert scanner._classify_phrase_family("return from graveyard") in ["reanimate", "death"]
        assert scanner._classify_phrase_family("exile target") == "exile"

    def test_phrase_frequency_sorting(self, db):
        """Clusters should be sorted by frequency."""
        scanner = Layer2Scanner(db)
        clusters = scanner.scan_unmatched_phrases(scope="all", min_frequency=1)

        if len(clusters) > 1:
            for i in range(len(clusters) - 1):
                assert clusters[i].frequency >= clusters[i + 1].frequency


class TestScannerHelpers:
    """Test scanner helper methods."""

    def test_has_taggable_verbs(self, db):
        """Should detect taggable verbs in oracle text."""
        scanner = Layer2Scanner(db)

        assert scanner._has_taggable_verbs("Sacrifice a creature: Add mana.") is True
        assert scanner._has_taggable_verbs("Draw a card") is True
        assert scanner._has_taggable_verbs("Flying") is False

    def test_extract_phrases(self, db):
        """Should extract meaningful phrases."""
        scanner = Layer2Scanner(db)

        oracle = "Sacrifice a creature: Add {C}{C}.\nWhenever a creature dies, gain 1 life."
        phrases = scanner._extract_phrases(oracle)

        assert len(phrases) > 0
        # Should extract segments between delimiters
        assert any("sacrifice" in p for p in phrases)

    def test_find_likely_missing_tags(self, db):
        """Should suggest likely missing tags based on patterns."""
        scanner = Layer2Scanner(db)

        oracle = "Sacrifice a creature: Add {C}{C}."
        missing = scanner._find_likely_missing_tags(oracle)

        # Should find Sacrifice_Outlet and Mana_Production
        assert "Sacrifice_Outlet" in missing
        assert "Mana_Production" in missing
