"""
test_tags.py — Tests for the Phase 2 five-layer tagging system.

All tests use an in-memory SQLite database so they run fast
and leave no files behind.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mtgdeck.database import Database
from mtgdeck.models import Card
from mtgdeck import tags


@pytest.fixture
def db():
    """Fresh in-memory database with schema and seed tags."""
    database = Database(":memory:")
    database.init_db()
    tags.seed_tags(database)
    yield database
    database.close()


def _make_card(name: str, oracle_text: str = "") -> Card:
    """Helper to build a minimal Card for testing."""
    return Card(
        name=name,
        mana_cost="",
        cmc=0,
        type_line="Creature",
        oracle_text=oracle_text,
    )


# ─── seed_tags ────────────────────────────────────────────────────────────────

class TestSeedTags:

    def test_all_four_layers_present(self, db):
        """Tags should exist across all four defined layers."""
        all_tags = db.all_tags()
        layers = {t["layer"] for t in all_tags}
        assert "mechanical" in layers
        assert "functional" in layers
        assert "archetype" in layers
        assert "emotional" in layers

    def test_minimum_tag_count(self, db):
        """Should seed at least 30 tags total."""
        assert len(db.all_tags()) >= 30

    def test_mechanical_layer_minimum(self, db):
        """Mechanical layer should have at least 10 tags."""
        assert len(db.all_tags("mechanical")) >= 10

    def test_functional_layer_minimum(self, db):
        """Functional layer should have at least 8 tags."""
        assert len(db.all_tags("functional")) >= 8

    def test_emotional_layer_minimum(self, db):
        """Emotional layer should have key strategic identity tags."""
        emotional_names = {t["name"] for t in db.all_tags("emotional")}
        assert "Engine_Core" in emotional_names
        assert "Apex_Threat" in emotional_names
        assert "Renewable_Fuel" in emotional_names

    def test_seed_is_idempotent(self, db):
        """Calling seed_tags twice should not duplicate tags."""
        count_before = len(db.all_tags())
        tags.seed_tags(db)
        count_after = len(db.all_tags())
        assert count_before == count_after

    def test_each_tag_has_description(self, db):
        """Every seeded tag should have a non-empty description."""
        for tag in db.all_tags():
            assert tag["description"], f"Tag '{tag['name']}' has no description"


# ─── tag_card / get_card_tags ─────────────────────────────────────────────────

class TestTagCard:

    def test_tag_and_retrieve(self, db):
        """Tag a card and retrieve it back."""
        success = db.tag_card("Crypt Ghast", "Engine_Core", confidence=1.0, source="manual")
        assert success is True

        result = tags.get_card_tags("Crypt Ghast", db)
        assert len(result) == 1
        assert result[0]["name"] == "Engine_Core"
        assert result[0]["confidence"] == 1.0
        assert result[0]["source"] == "manual"

    def test_tag_unknown_tag_returns_false(self, db):
        """Tagging with a nonexistent tag name should return False."""
        success = db.tag_card("Sol Ring", "Not_A_Real_Tag")
        assert success is False

    def test_multiple_tags_on_one_card(self, db):
        """A card can have tags from different layers."""
        db.tag_card("Ashnod's Altar", "Sacrifice_Outlet", 1.0)
        db.tag_card("Ashnod's Altar", "Mana_Production", 1.0)
        db.tag_card("Ashnod's Altar", "Engine_Core", 1.0)

        result = tags.get_card_tags("Ashnod's Altar", db)
        tag_names = {t["name"] for t in result}
        assert "Sacrifice_Outlet" in tag_names
        assert "Mana_Production" in tag_names
        assert "Engine_Core" in tag_names

    def test_filter_by_layer(self, db):
        """get_card_tags should filter correctly by layer."""
        db.tag_card("Blood Artist", "Death_Trigger", 1.0)
        db.tag_card("Blood Artist", "Payoff", 1.0)
        db.tag_card("Blood Artist", "Engine_Core", 0.8)

        mech = tags.get_card_tags("Blood Artist", db, layer="mechanical")
        func = tags.get_card_tags("Blood Artist", db, layer="functional")
        emot = tags.get_card_tags("Blood Artist", db, layer="emotional")

        assert all(t["layer"] == "mechanical" for t in mech)
        assert all(t["layer"] == "functional" for t in func)
        assert all(t["layer"] == "emotional" for t in emot)
        assert len(mech) == 1   # Death_Trigger
        assert len(func) == 1   # Payoff
        assert len(emot) == 1   # Engine_Core

    def test_empty_layer_returns_empty_list(self, db):
        """Filtering by layer with no matches returns empty list, not error."""
        db.tag_card("Basic Card", "Draw_Effect", 1.0)
        result = tags.get_card_tags("Basic Card", db, layer="emotional")
        assert result == []

    def test_case_insensitive_card_lookup(self, db):
        """get_card_tags should work regardless of card name casing."""
        db.tag_card("Sol Ring", "Mana_Acceleration", 1.0)
        result = tags.get_card_tags("sol ring", db)
        assert len(result) == 1

    def test_confidence_stored_correctly(self, db):
        """Confidence values are stored and returned as floats."""
        db.tag_card("Reassembling Skeleton", "Renewable_Fuel", confidence=0.95)
        result = tags.get_card_tags("Reassembling Skeleton", db)
        assert abs(result[0]["confidence"] - 0.95) < 0.001

    def test_replace_tag_updates_confidence(self, db):
        """Tagging same card+tag twice should update, not duplicate."""
        db.tag_card("Swamp", "Mana_Production", 0.5)
        db.tag_card("Swamp", "Mana_Production", 0.9)

        result = tags.get_card_tags("Swamp", db)
        mana_tags = [t for t in result if t["name"] == "Mana_Production"]
        assert len(mana_tags) == 1
        assert abs(mana_tags[0]["confidence"] - 0.9) < 0.001


# ─── get_tag_names ────────────────────────────────────────────────────────────

class TestGetTagNames:

    def test_returns_list_of_strings(self, db):
        db.tag_card("Sol Ring", "Engine_Core", 1.0)
        names = tags.get_tag_names("Sol Ring", db)
        assert isinstance(names, list)
        assert "Engine_Core" in names

    def test_membership_check(self, db):
        db.tag_card("Crypt Ghast", "Mana_Engine", 1.0)
        names = tags.get_tag_names("Crypt Ghast", db)
        assert "Mana_Engine" in names
        assert "Apex_Threat" not in names


# ─── query_cards_by_tag ───────────────────────────────────────────────────────

class TestQueryCardsByTag:

    def test_finds_tagged_cards(self, db):
        db.tag_card("Blood Artist", "Death_Trigger", 1.0)
        db.tag_card("Zulaport Cutthroat", "Death_Trigger", 1.0)
        db.tag_card("Llanowar Elves", "Mana_Acceleration", 1.0)

        result = tags.query_cards_by_tag("Death_Trigger", db)
        names = {r["card_name"] for r in result}
        assert "Blood Artist" in names
        assert "Zulaport Cutthroat" in names
        assert "Llanowar Elves" not in names

    def test_returns_empty_for_untagged(self, db):
        result = tags.query_cards_by_tag("Board_Wipe", db)
        assert result == []

    def test_min_confidence_filters(self, db):
        db.tag_card("Card A", "Finisher", confidence=0.9)
        db.tag_card("Card B", "Finisher", confidence=0.3)

        high = tags.query_cards_by_tag("Finisher", db, min_confidence=0.5)
        all_results = tags.query_cards_by_tag("Finisher", db, min_confidence=0.0)

        high_names = {r["card_name"] for r in high}
        all_names = {r["card_name"] for r in all_results}

        assert "Card A" in high_names
        assert "Card B" not in high_names
        assert "Card B" in all_names


# ─── tag_mechanical (auto-tagger) ─────────────────────────────────────────────

class TestTagMechanical:

    def test_draw_effect_detected(self, db):
        card = _make_card("Divination", "Draw two cards.")
        applied = tags.tag_mechanical(card, db)
        assert "Draw_Effect" in applied

    def test_death_trigger_detected(self, db):
        card = _make_card("Blood Artist",
                          "Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.")
        applied = tags.tag_mechanical(card, db)
        assert "Death_Trigger" in applied

    def test_sacrifice_outlet_detected(self, db):
        card = _make_card("Ashnod's Altar",
                          "Sacrifice a creature: Add {C}{C}.")
        applied = tags.tag_mechanical(card, db)
        assert "Sacrifice_Outlet" in applied

    def test_board_wipe_detected(self, db):
        card = _make_card("Damnation",
                          "Destroy all creatures. They can't be regenerated.")
        applied = tags.tag_mechanical(card, db)
        assert "Board_Wipe" in applied

    def test_reanimation_detected(self, db):
        card = _make_card("Animate Dead",
                          "Return target creature card from a graveyard to the battlefield under your control.")
        applied = tags.tag_mechanical(card, db)
        assert "Reanimation" in applied

    def test_tutor_detected(self, db):
        card = _make_card("Vampiric Tutor",
                          "Search your library for a card, then shuffle your library and put that card on top.")
        applied = tags.tag_mechanical(card, db)
        assert "Tutor_Effect" in applied

    def test_life_drain_detected(self, db):
        card = _make_card("Exsanguinate",
                          "Each opponent loses X life. You gain life equal to the life lost this way.")
        applied = tags.tag_mechanical(card, db)
        assert "Life_Drain" in applied

    def test_no_false_positives_on_empty_text(self, db):
        """Card with no oracle text should get no mechanical tags."""
        card = _make_card("Blank Card", "")
        applied = tags.tag_mechanical(card, db)
        assert applied == []

    def test_auto_tag_stores_in_db(self, db):
        """Auto-tagged cards should be retrievable from the database."""
        card = _make_card("Divination", "Draw two cards.")
        tags.tag_mechanical(card, db)
        stored = tags.get_tag_names(card.name, db, layer="mechanical")
        assert "Draw_Effect" in stored

    def test_auto_tag_source_is_regex(self, db):
        """Auto-tagged cards should have source='regex', not 'manual'."""
        card = _make_card("Divination", "Draw two cards.")
        tags.tag_mechanical(card, db)
        result = tags.get_card_tags(card.name, db, layer="mechanical")
        draw_tag = next(t for t in result if t["name"] == "Draw_Effect")
        assert draw_tag["source"] == "regex"

    def test_multiple_patterns_on_one_card(self, db):
        """Cards with multiple effects should get multiple tags."""
        card = _make_card("Blood Artist",
                          "Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.")
        applied = tags.tag_mechanical(card, db)
        assert "Death_Trigger" in applied
        assert "Life_Drain" in applied
        assert "Life_Gain" in applied


# ─── synergy edges ────────────────────────────────────────────────────────────

class TestSynergy:

    def test_add_and_retrieve_synergy(self, db):
        edge_id = tags.add_synergy(
            "Ashnod's Altar",
            "Reassembling Skeleton",
            "Sacrifice_Loop",
            db,
            strength=1.0,
            explanation="Skeleton recurs for 2 mana, altar produces 2 — infinite loop.",
        )
        assert isinstance(edge_id, int)

        synergies = tags.get_synergies("Ashnod's Altar", db)
        assert len(synergies) == 1
        assert synergies[0]["other_card"] == "Reassembling Skeleton"
        assert synergies[0]["synergy_type"] == "Sacrifice_Loop"
        assert synergies[0]["strength"] == 1.0

    def test_synergy_bidirectional(self, db):
        """get_synergies should return edge regardless of which card you query."""
        tags.add_synergy(
            "Crypt Ghast",
            "Exsanguinate",
            "Big_Mana_Finisher",
            db,
            strength=0.9,
        )
        from_a = tags.get_synergies("Crypt Ghast", db)
        from_b = tags.get_synergies("Exsanguinate", db)

        assert len(from_a) == 1
        assert len(from_b) == 1
        assert from_a[0]["other_card"] == "Exsanguinate"
        assert from_b[0]["other_card"] == "Crypt Ghast"

    def test_min_strength_filter(self, db):
        tags.add_synergy("Card A", "Card B", "Strong_Synergy", db, strength=0.9)
        tags.add_synergy("Card A", "Card C", "Weak_Synergy",   db, strength=0.2)

        strong = tags.get_synergies("Card A", db, min_strength=0.5)
        all_s  = tags.get_synergies("Card A", db, min_strength=0.0)

        assert len(strong) == 1
        assert strong[0]["other_card"] == "Card B"
        assert len(all_s) == 2

    def test_strength_is_zero_to_one(self, db):
        """Strength values should be stored as 0.0-1.0 floats."""
        tags.add_synergy("X", "Y", "Test", db, strength=0.75)
        result = tags.get_synergies("X", db)
        assert 0.0 <= result[0]["strength"] <= 1.0


# ─── tag_count_for_deck ───────────────────────────────────────────────────────

class TestTagCountForDeck:

    def test_counts_deck_tags(self, db):
        db.tag_card("Card A", "Mana_Acceleration", 1.0)
        db.tag_card("Card B", "Mana_Acceleration", 1.0)
        db.tag_card("Card C", "Removal", 1.0)

        counts = tags.tag_count_for_deck(["Card A", "Card B", "Card C"], db)
        assert counts.get("Mana_Acceleration") == 2
        assert counts.get("Removal") == 1

    def test_layer_filter(self, db):
        db.tag_card("Card A", "Mana_Acceleration", 1.0)   # functional
        db.tag_card("Card A", "Engine_Core", 1.0)         # emotional

        func_counts = tags.tag_count_for_deck(["Card A"], db, layer="functional")
        emot_counts = tags.tag_count_for_deck(["Card A"], db, layer="emotional")

        assert "Mana_Acceleration" in func_counts
        assert "Engine_Core" not in func_counts
        assert "Engine_Core" in emot_counts
        assert "Mana_Acceleration" not in emot_counts

    def test_empty_deck_returns_empty(self, db):
        result = tags.tag_count_for_deck([], db)
        assert result == {}

    def test_untagged_cards_not_counted(self, db):
        """Cards with no tags should not appear in the count."""
        result = tags.tag_count_for_deck(["Untagged Card Name"], db)
        assert result == {}
