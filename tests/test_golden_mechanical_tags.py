"""
test_golden_mechanical_tags.py — Golden test set for mechanical tagging.

These tests verify that known cards have correct tags according to the
golden test set defined in mechanical_tags.yaml.

This file is the regression test suite that ensures Layer 2 (mechanical tags)
remains reliable as we evolve the patterns and rules.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import yaml
from mtgdeck.database import Database
from mtgdeck import tags


@pytest.fixture
def db():
    """Fresh in-memory database with schema and seed tags."""
    database = Database(":memory:")
    database.init_db()
    tags.seed_tags(database)
    yield database
    database.close()


@pytest.fixture
def golden_set():
    """Load golden test set from YAML."""
    yaml_path = Path(__file__).parent / "golden" / "mechanical_tags.yaml"
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return data


def test_golden_set_loaded(golden_set):
    """Verify golden set loads correctly."""
    assert golden_set is not None
    assert len(golden_set) > 0


class TestGoldenMechanicalTags:
    """Regression tests against golden set expectations."""

    @pytest.mark.parametrize("card_name,expectations", [
        pytest.param(name, expectations, id=name)
        for name, expectations in (
            yaml.safe_load(open(Path(__file__).parent / "golden" / "mechanical_tags.yaml"))
            or {}
        ).items()
    ])
    def test_golden_card_tags(self, db, card_name, expectations, golden_set):
        """
        Verify each golden card has expected tags and no unwanted tags.

        This parametrized test runs once per card in the golden set.
        Golden tests only run if the card exists in the database.
        """
        # Check if card exists in database
        card = db.card_by_name(card_name)
        if not card:
            pytest.skip(f"Card not in database: {card_name}")

        must_have = set(expectations.get("must_have", []))
        must_not_have = set(expectations.get("must_not_have", []))

        tags_result = db.get_card_tags(card_name)
        actual_tags = {t["name"] for t in tags_result}

        # Verify must_have
        missing = must_have - actual_tags
        assert not missing, (
            f"{card_name}: Missing expected tags: {missing}\n"
            f"Has: {actual_tags}"
        )

        # Verify must_not_have
        unwanted = must_not_have & actual_tags
        assert not unwanted, (
            f"{card_name}: Has unexpected tags: {unwanted}\n"
            f"Has: {actual_tags}"
        )


class TestGoldenCardsByFamily:
    """Tests grouped by mechanic family."""

    def test_sacrifice_outlets(self, db, golden_set):
        """Verify sacrifice outlet cards are tagged correctly."""
        cards = ["Ashnod's Altar", "Viscera Seer"]
        found = 0
        for card in cards:
            if card in golden_set and db.card_by_name(card):
                tags_result = db.get_card_tags(card)
                actual = {t["name"] for t in tags_result}
                must_have = set(golden_set[card].get("must_have", []))
                assert must_have.issubset(actual), f"{card} missing: {must_have - actual}"
                found += 1
        if found == 0:
            pytest.skip("No sacrifice outlet cards in database")

    def test_death_triggers(self, db, golden_set):
        """Verify death trigger cards are tagged correctly."""
        cards = ["Blood Artist", "Grave Pact"]
        found = 0
        for card in cards:
            if card in golden_set and db.card_by_name(card):
                tags_result = db.get_card_tags(card)
                actual = {t["name"] for t in tags_result}
                must_have = set(golden_set[card].get("must_have", []))
                assert must_have.issubset(actual), f"{card} missing: {must_have - actual}"
                found += 1
        if found == 0:
            pytest.skip("No death trigger cards in database")

    def test_reanimation(self, db, golden_set):
        """Verify reanimation cards are tagged correctly."""
        cards = ["Animate Dead", "Living Death"]
        found = 0
        for card in cards:
            if card in golden_set and db.card_by_name(card):
                tags_result = db.get_card_tags(card)
                actual = {t["name"] for t in tags_result}
                must_have = set(golden_set[card].get("must_have", []))
                assert must_have.issubset(actual), f"{card} missing: {must_have - actual}"
                found += 1
        if found == 0:
            pytest.skip("No reanimation cards in database")


class TestGoldenExpectations:
    """Tests for specific cards with manual verification."""

    def test_ashnods_altar_is_not_death_trigger(self, db):
        """Ashnod's Altar should NOT be tagged as Death_Trigger."""
        card = db.card_by_name("Ashnod's Altar")
        if not card:
            pytest.skip("Card not in database")
        tags_result = db.get_card_tags("Ashnod's Altar")
        actual = {t["name"] for t in tags_result}
        assert "Death_Trigger" not in actual

    def test_blood_artist_is_death_trigger(self, db):
        """Blood Artist SHOULD be tagged as Death_Trigger."""
        card = db.card_by_name("Blood Artist")
        if not card:
            pytest.skip("Card not in database")
        tags_result = db.get_card_tags("Blood Artist")
        actual = {t["name"] for t in tags_result}
        assert "Death_Trigger" in actual

    def test_grave_pact_is_not_sacrifice_outlet(self, db):
        """Grave Pact should NOT be tagged as Sacrifice_Outlet."""
        card = db.card_by_name("Grave Pact")
        if not card:
            pytest.skip("Card not in database")
        tags_result = db.get_card_tags("Grave Pact")
        actual = {t["name"] for t in tags_result}
        assert "Sacrifice_Outlet" not in actual

    def test_sheoldred_has_reanimation(self, db):
        """Sheoldred SHOULD have Reanimation tag."""
        card = db.card_by_name("Sheoldred, Whispering One")
        if not card:
            pytest.skip("Card not in database")
        tags_result = db.get_card_tags("Sheoldred, Whispering One")
        actual = {t["name"] for t in tags_result}
        assert "Reanimation" in actual


class TestGoldenSetIntegrity:
    """Tests to verify the golden set itself is well-formed."""

    def test_golden_set_has_both_expectations(self, golden_set):
        """Every card should have both must_have and must_not_have."""
        for card_name, expectations in golden_set.items():
            assert "must_have" in expectations, f"{card_name} missing must_have"
            assert "must_not_have" in expectations, f"{card_name} missing must_not_have"
            assert len(expectations["must_have"]) > 0, f"{card_name} has empty must_have"
            assert len(expectations["must_not_have"]) > 0, f"{card_name} has empty must_not_have"

    def test_no_overlap_in_expectations(self, golden_set):
        """A tag should not appear in both must_have and must_not_have."""
        for card_name, expectations in golden_set.items():
            must_have = set(expectations.get("must_have", []))
            must_not_have = set(expectations.get("must_not_have", []))
            overlap = must_have & must_not_have
            assert not overlap, (
                f"{card_name}: Tags appear in both must_have and must_not_have: {overlap}"
            )
