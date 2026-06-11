"""
test_phase1_bootstrap.py — Phase 1A Bootstrap testing.

Load sample cards and run scanner to identify baseline gaps.
This is the foundation for pattern addition and evidence integration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from mtgdeck.database import Database
from mtgdeck import tags
from mtgdeck.layer2_scanner import Layer2Scanner
from fixtures.sample_cards import load_sample_cards, SAMPLE_CARDS


@pytest.fixture
def bootstrap_db():
    """Database with sample cards loaded."""
    db = Database(":memory:")
    db.init_db()
    tags.seed_tags(db)

    # Load sample cards
    count = load_sample_cards(db)
    print(f"\n✓ Loaded {count} sample cards")

    yield db
    db.close()


class TestPhase1ABootstrap:
    """Phase 1A: Bootstrap with test data."""

    def test_sample_cards_loaded(self, bootstrap_db):
        """Verify sample cards loaded correctly."""
        cards = bootstrap_db.all_cards()
        assert len(cards) == len(SAMPLE_CARDS)

        card_names = {c.name for c in cards}
        sample_names = {c.name for c in SAMPLE_CARDS}
        assert card_names == sample_names

    def test_scanner_runs_on_sample_data(self, bootstrap_db):
        """Scanner should run without errors on sample data."""
        scanner = Layer2Scanner(bootstrap_db)

        # Should not crash
        gaps = scanner.scan_coverage_gaps(scope="all")
        risks = scanner.scan_over_tagging_risk(threshold=5)
        phrases = scanner.scan_unmatched_phrases(scope="all", min_frequency=1)

        assert isinstance(gaps, list)
        assert isinstance(risks, list)
        assert isinstance(phrases, list)

    def test_identifies_coverage_gaps(self, bootstrap_db):
        """Should identify cards with zero or low tags."""
        scanner = Layer2Scanner(bootstrap_db)
        gaps = scanner.scan_coverage_gaps(scope="all")

        # All sample cards start with zero tags
        assert len(gaps) > 0
        assert all(gap.tag_count == 0 for gap in gaps)

        print(f"\n✓ Coverage gaps found: {len(gaps)}")
        print(f"  Sample: {gaps[0].card_name} ({gaps[0].tag_count} tags)")

    def test_identifies_taggable_verbs(self, bootstrap_db):
        """Should identify cards with taggable language."""
        scanner = Layer2Scanner(bootstrap_db)
        gaps = scanner.scan_coverage_gaps(scope="all")

        # Many cards have taggable verbs
        taggable_gaps = [g for g in gaps if g.has_taggable_verbs]
        assert len(taggable_gaps) > 0

        print(f"\n✓ Cards with taggable verbs: {len(taggable_gaps)}")
        print(f"  Sample: {taggable_gaps[0].card_name}")
        print(f"  Likely missing: {taggable_gaps[0].missing_likely_tags}")

    def test_identifies_mechanic_families(self, bootstrap_db):
        """Should cluster oracle phrases by mechanic family."""
        scanner = Layer2Scanner(bootstrap_db)
        phrases = scanner.scan_unmatched_phrases(scope="all", min_frequency=1)

        assert len(phrases) > 0

        # Check families are detected
        families = {p.mechanic_family for p in phrases}
        print(f"\n✓ Mechanic families found: {families}")

        # Should have multiple families
        assert len(families) > 1

    def test_baseline_report(self, bootstrap_db):
        """Generate baseline report showing gaps."""
        scanner = Layer2Scanner(bootstrap_db)

        gaps = scanner.scan_coverage_gaps(scope="all")
        risks = scanner.scan_over_tagging_risk(threshold=5)
        phrases = scanner.scan_unmatched_phrases(scope="all", min_frequency=1)

        print("\n" + "="*70)
        print("PHASE 1A BASELINE REPORT")
        print("="*70)

        print(f"\nTotal cards: {len(SAMPLE_CARDS)}")
        print(f"Cards with zero tags: {len(gaps)}")
        print(f"Phrase clusters: {len(phrases)}")

        print("\nTop missing patterns (by frequency):")
        for phrase in phrases[:5]:
            print(f"  - {phrase.mechanic_family}: '{phrase.phrase}' ({phrase.frequency}x)")

        print("\nTop untagged cards:")
        for gap in gaps[:5]:
            if gap.missing_likely_tags:
                print(f"  - {gap.card_name}: should have {', '.join(gap.missing_likely_tags)}")

        print("\n✓ Baseline report generated")


class TestPhase1ACardCoverage:
    """Verify we have diversity in the test data."""

    def test_has_sacrifice_outlets(self, bootstrap_db):
        """Sample should include sacrifice outlets."""
        names = {c.name for c in bootstrap_db.all_cards()}
        sacrifice_outlets = {"Ashnod's Altar", "Viscera Seer", "Cartel Aristocrat"}
        assert sacrifice_outlets.issubset(names)

    def test_has_death_triggers(self, bootstrap_db):
        """Sample should include death triggers."""
        names = {c.name for c in bootstrap_db.all_cards()}
        death_triggers = {"Blood Artist", "Zulaport Cutthroat", "Grave Pact"}
        assert death_triggers.issubset(names)

    def test_has_reanimation(self, bootstrap_db):
        """Sample should include reanimation spells."""
        names = {c.name for c in bootstrap_db.all_cards()}
        reanimation = {"Animate Dead", "Living Death"}
        assert reanimation.issubset(names)

    def test_has_recursion(self, bootstrap_db):
        """Sample should include self-recursion cards."""
        names = {c.name for c in bootstrap_db.all_cards()}
        recursion = {"Bloodghast", "Reassembling Skeleton"}
        assert recursion.issubset(names)

    def test_has_tokens(self, bootstrap_db):
        """Sample should include token generators."""
        names = {c.name for c in bootstrap_db.all_cards()}
        tokens = {"Ghoulcaller Gisa", "Bitterblossom"}
        assert tokens.issubset(names)

    def test_has_removal(self, bootstrap_db):
        """Sample should include removal spells."""
        names = {c.name for c in bootstrap_db.all_cards()}
        removal = {"Victim of Night", "Plague Crafter"}
        assert removal.issubset(names)

    def test_has_tutors(self, bootstrap_db):
        """Sample should include tutor spells."""
        names = {c.name for c in bootstrap_db.all_cards()}
        tutors = {"Demonic Tutor", "Entomb"}
        assert tutors.issubset(names)
