"""
test_phase6_patterns.py — Regression tests for Phase 6B/6G oracle text pattern fixes.

Each test:
  1. Creates a synthetic Card with the real oracle text
  2. Inserts it into an in-memory DB
  3. Runs tag_mechanical + tag_functional_from_rules
  4. Asserts the expected functional tags are present

These tests ensure the pattern fixes never silently regress.
Uses in-memory SQLite — no collection_scan.sqlite dependency.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.database import Database
from mtgdeck.models import Card
from mtgdeck import tags


@pytest.fixture
def db():
    database = Database(":memory:")
    database.init_db()
    tags.seed_tags(database)
    yield database
    database.close()


def _tag_and_get_functional(db, name: str, oracle_text: str, type_line: str = "Instant") -> set:
    card = Card(name=name, mana_cost="{B}", cmc=1, type_line=type_line, oracle_text=oracle_text)
    db.insert_card(card)
    tags.tag_mechanical(card, db)
    tags.tag_functional_from_rules(name, db)
    return {t["name"] for t in db.get_card_tags(name, layer="functional")}


def _tag_and_get_mechanical(db, name: str, oracle_text: str, type_line: str = "Instant") -> set:
    card = Card(name=name, mana_cost="{B}", cmc=1, type_line=type_line, oracle_text=oracle_text)
    db.insert_card(card)
    tags.tag_mechanical(card, db)
    return {t["name"] for t in db.get_card_tags(name, layer="mechanical")}


# ── Phase 6B fixes ─────────────────────────────────────────────────────────────

class TestTragicSlip:
    """Pattern: 'target creature gets -X/-X until end of turn' → Targeted_Removal."""

    ORACLE = (
        "Target creature gets -1/-1 until end of turn.\n"
        "Morbid — That creature gets -13/-13 until end of turn instead "
        "if a creature died this turn."
    )

    def test_targeted_removal_mechanical(self, db):
        mech = _tag_and_get_mechanical(db, "Tragic Slip", self.ORACLE)
        assert "Targeted_Removal" in mech, f"Expected Targeted_Removal, got: {mech}"

    def test_removal_functional(self, db):
        func = _tag_and_get_functional(db, "Tragic Slip", self.ORACLE)
        assert "Removal" in func, f"Expected Removal, got: {func}"

    def test_interaction_functional(self, db):
        func = _tag_and_get_functional(db, "Tragic Slip", self.ORACLE)
        assert "Interaction" in func


class TestDanceOfTheDead:
    """Pattern: 'put enchanted creature card onto the battlefield' → Reanimation."""

    ORACLE = (
        "Enchant creature card in a graveyard\n"
        "When this Aura enters, if it's on the battlefield, it loses "
        "\"enchant creature card in a graveyard\" and gains "
        "\"enchant creature put onto the battlefield with this Aura.\" "
        "Put enchanted creature card onto the battlefield tapped under "
        "your control and attach this Aura to it. When this Aura leaves "
        "the battlefield, that creature's controller sacrifices it.\n"
        "Enchanted creature gets +1/+1 and doesn't untap during its "
        "controller's untap step."
    )

    def test_reanimation_mechanical(self, db):
        mech = _tag_and_get_mechanical(db, "Dance of the Dead", self.ORACLE, type_line="Enchantment — Aura")
        assert "Reanimation" in mech, f"Expected Reanimation, got: {mech}"

    def test_recursion_functional(self, db):
        func = _tag_and_get_functional(db, "Dance of the Dead", self.ORACLE, type_line="Enchantment — Aura")
        assert "Recursion" in func, f"Expected Recursion, got: {func}"


class TestVictimize:
    """Pattern: 'return the chosen cards to the battlefield' → Reanimation."""

    ORACLE = (
        "Choose two target creature cards in your graveyard. "
        "Sacrifice a creature. If you do, return the chosen cards "
        "to the battlefield tapped."
    )

    def test_reanimation_mechanical(self, db):
        mech = _tag_and_get_mechanical(db, "Victimize", self.ORACLE, type_line="Sorcery")
        assert "Reanimation" in mech, f"Expected Reanimation, got: {mech}"

    def test_recursion_functional(self, db):
        func = _tag_and_get_functional(db, "Victimize", self.ORACLE, type_line="Sorcery")
        assert "Recursion" in func, f"Expected Recursion, got: {func}"


class TestNyxLotus:
    """Pattern: 'add an amount of mana' → Mana_Production → Mana_Acceleration."""

    ORACLE = (
        "Nyx Lotus enters tapped.\n"
        "{T}: Choose a color. Add an amount of mana of that color equal "
        "to your devotion to that color."
    )

    def test_mana_production_mechanical(self, db):
        mech = _tag_and_get_mechanical(db, "Nyx Lotus", self.ORACLE, type_line="Legendary Artifact")
        assert "Mana_Production" in mech, f"Expected Mana_Production, got: {mech}"

    def test_mana_acceleration_functional(self, db):
        func = _tag_and_get_functional(db, "Nyx Lotus", self.ORACLE, type_line="Legendary Artifact")
        assert "Mana_Acceleration" in func, f"Expected Mana_Acceleration, got: {func}"


# ── Phase 6G fixes ─────────────────────────────────────────────────────────────

class TestSyrKonrad:
    """Rule: Death_Trigger + Damage_Effect → Payoff (Phase 6G functional rule)."""

    ORACLE = (
        "Whenever another creature dies, or a creature card is put into "
        "a graveyard from anywhere other than the battlefield, or a "
        "creature card leaves your graveyard, Syr Konrad, the Grim "
        "deals 1 damage to each opponent."
    )

    def test_death_trigger_mechanical(self, db):
        mech = _tag_and_get_mechanical(db, "Syr Konrad", self.ORACLE, type_line="Legendary Creature")
        assert "Death_Trigger" in mech

    def test_damage_effect_mechanical(self, db):
        mech = _tag_and_get_mechanical(db, "Syr Konrad", self.ORACLE, type_line="Legendary Creature")
        assert "Damage_Effect" in mech

    def test_payoff_functional(self, db):
        func = _tag_and_get_functional(db, "Syr Konrad", self.ORACLE, type_line="Legendary Creature")
        assert "Payoff" in func, f"Expected Payoff, got: {func}"


# ── No regressions on existing patterns ────────────────────────────────────────

class TestExistingPatternsSafe:
    """Sanity check: existing patterns still fire after Phase 6B/6G additions."""

    def test_blood_artist_death_trigger(self, db):
        oracle = "Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life."
        func = _tag_and_get_functional(db, "Blood Artist Test", oracle, type_line="Creature")
        assert "Payoff" in func

    def test_ashnods_altar_sacrifice_outlet(self, db):
        oracle = "Sacrifice a creature: Add {C}{C}."
        mech = _tag_and_get_mechanical(db, "Ashnods Test", oracle, type_line="Artifact")
        assert "Sacrifice_Outlet" in mech

    def test_animate_dead_reanimation(self, db):
        oracle = "Return target creature card from a graveyard to the battlefield."
        mech = _tag_and_get_mechanical(db, "Animate Dead Test", oracle, type_line="Enchantment")
        assert "Reanimation" in mech

    def test_no_false_positive_for_amount_of_mana_on_land(self, db):
        """'add an amount of mana' on a LAND should not get Mana_Production tag."""
        oracle = "{T}: Add an amount of mana of any color equal to your devotion to any color."
        mech = _tag_and_get_mechanical(
            db, "Devotion Land Test", oracle, type_line="Basic Land — Swamp"
        )
        # Land exclusion: basic lands should not get Mana_Production
        # (the tag_mechanical code has a guard for lands)
        assert "Mana_Production" not in mech, (
            "Lands should not get Mana_Production unless they produce scaling mana"
        )
