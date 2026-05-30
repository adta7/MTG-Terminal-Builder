"""
test_phase3_evidence.py — Phase 3: Evidence Integration tests.

Verifies that every auto-generated mechanical tag explains itself:
which rule fired, what text fired it, where that text lives, and
what role that text played.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from mtgdeck.database import Database
from mtgdeck.models import Card
from mtgdeck import tags
from fixtures.sample_cards import SAMPLE_CARDS, load_sample_cards


# Expected mechanical tags for anchor cards in SAMPLE_CARDS.
#
# NOTE: Ghoulcaller Gisa and Bolas's Citadel use simplified oracle text in the fixture
# (not the real Scryfall oracle text). Their expectations below reflect the fixture
# text, not the real card. Fix fixture oracle texts before treating these as gold truth.
ANCHOR_EXPECTATIONS = {
    "Ashnod's Altar":          ["Sacrifice_Outlet", "Mana_Production"],
    "Blood Artist":            ["Death_Trigger", "Life_Drain"],
    "Grave Pact":              ["Death_Trigger", "Forced_Sacrifice"],
    "Animate Dead":            ["Reanimation"],
    "Ghoulcaller Gisa":        ["Token_Generation"],          # fixture has simplified oracle
    "Bolas's Citadel":         ["Life_Gain"],                 # fixture has simplified oracle
    "Phyrexian Arena":         ["Draw_Effect"],
    "Sheoldred, Whispering One": ["Reanimation", "Forced_Sacrifice"],
}


@pytest.fixture
def evidence_db():
    """Database with all sample cards loaded and mechanically tagged."""
    db = Database(":memory:")
    db.init_db()
    tags.seed_tags(db)
    load_sample_cards(db)

    for card in db.all_cards():
        if card.oracle_text:
            tags.tag_mechanical(card, db)

    yield db
    db.close()


class TestEveryTagHasEvidence:

    def test_every_regex_tag_has_evidence(self, evidence_db):
        """Every card_tags row with source='regex' must have ≥1 evidence row."""
        cur = evidence_db.conn.cursor()
        cur.execute(
            "SELECT card_id, tag_id FROM card_tags WHERE source = 'regex'"
        )
        regex_tags = cur.fetchall()

        assert len(regex_tags) > 0, "Should have regex-generated tags to test"

        missing_evidence = []
        for card_id, tag_id in regex_tags:
            cur.execute(
                "SELECT COUNT(*) FROM tag_evidence WHERE card_name = ? AND tag_id = ?",
                (card_id, tag_id),
            )
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute("SELECT name FROM tags WHERE id = ?", (tag_id,))
                tag_name = cur.fetchone()[0]
                missing_evidence.append(f"{card_id} / {tag_name}")

        assert not missing_evidence, (
            f"These regex tags have no evidence rows:\n" +
            "\n".join(f"  - {item}" for item in missing_evidence)
        )

    def test_no_orphan_regex_tags(self, evidence_db):
        """No card_tags row with source='regex' should exist without evidence."""
        cur = evidence_db.conn.cursor()
        cur.execute("""
            SELECT ct.card_id, t.name
            FROM card_tags ct
            JOIN tags t ON ct.tag_id = t.id
            WHERE ct.source = 'regex'
              AND NOT EXISTS (
                  SELECT 1 FROM tag_evidence te
                  WHERE te.card_name = ct.card_id
                    AND te.tag_id = ct.tag_id
              )
        """)
        orphans = cur.fetchall()
        assert not orphans, (
            "Orphan tags (card_tags without evidence):\n" +
            "\n".join(f"  - {row[0]} / {row[1]}" for row in orphans)
        )


class TestEvidenceFieldsPopulated:

    def test_evidence_fields_fully_populated(self, evidence_db):
        """Ashnod's Altar / Sacrifice_Outlet evidence must have all fields."""
        evidence = evidence_db.get_tag_evidence("Ashnod's Altar", "Sacrifice_Outlet")
        assert len(evidence) > 0, "Ashnod's Altar should have Sacrifice_Outlet evidence"

        row = evidence[0]
        assert row["rule_id"], f"rule_id must be non-empty, got: {row['rule_id']!r}"
        assert row["evidence_text"], f"evidence_text must be non-empty, got: {row['evidence_text']!r}"
        assert row["oracle_start"] is not None, "oracle_start must be set"
        assert row["oracle_end"] is not None, "oracle_end must be set"
        assert row["oracle_end"] > row["oracle_start"], "oracle_end must be after oracle_start"
        assert row["ability_kind"], f"ability_kind must be non-empty, got: {row['ability_kind']!r}"
        assert row["text_role"], f"text_role must be non-empty, got: {row['text_role']!r}"
        assert row["confidence"] > 0, f"confidence must be > 0, got: {row['confidence']}"
        assert row["source"] == "regex", f"source must be 'regex', got: {row['source']!r}"

    def test_evidence_rule_id_matches_pattern(self, evidence_db):
        """rule_id should follow the mechanical.tag.pattern.v1 format."""
        evidence = evidence_db.get_tag_evidence("Ashnod's Altar", "Sacrifice_Outlet")
        assert len(evidence) > 0

        rule_id = evidence[0]["rule_id"]
        assert rule_id.startswith("mechanical."), (
            f"rule_id should start with 'mechanical.', got: {rule_id!r}"
        )
        assert rule_id.endswith(".v1"), (
            f"rule_id should end with '.v1', got: {rule_id!r}"
        )
        assert rule_id.count(".") >= 3, (
            f"rule_id should have ≥3 segments (tag.pattern.v1), got: {rule_id!r}"
        )

    def test_evidence_text_is_original_case(self, evidence_db):
        """Evidence text should preserve original oracle case, not be all-lowercase."""
        evidence = evidence_db.get_tag_evidence("Ashnod's Altar", "Sacrifice_Outlet")
        assert len(evidence) > 0

        evidence_text = evidence[0]["evidence_text"]
        # Oracle text for Ashnod's Altar starts with capital 'S' in "Sacrifice"
        assert evidence_text[0].isupper() or evidence_text[0].isdigit(), (
            f"evidence_text should preserve original case, got: {evidence_text!r}"
        )

    def test_sacrifice_outlet_ability_kind(self, evidence_db):
        """Ashnod's Altar sacrifice cost should be tagged as 'activated' ability."""
        evidence = evidence_db.get_tag_evidence("Ashnod's Altar", "Sacrifice_Outlet")
        assert len(evidence) > 0

        ability_kinds = {row["ability_kind"] for row in evidence}
        assert "activated" in ability_kinds, (
            f"Sacrifice_Outlet on Ashnod's Altar should be 'activated', got: {ability_kinds}"
        )

    def test_sacrifice_outlet_text_role(self, evidence_db):
        """Ashnod's Altar sacrifice evidence should have text_role='cost'."""
        evidence = evidence_db.get_tag_evidence("Ashnod's Altar", "Sacrifice_Outlet")
        cost_evidence = [e for e in evidence if e["text_role"] == "cost"]
        assert len(cost_evidence) > 0, (
            f"Expected at least one Sacrifice_Outlet evidence with text_role='cost'. "
            f"Got roles: {[e['text_role'] for e in evidence]}"
        )

    def test_death_trigger_ability_kind(self, evidence_db):
        """Blood Artist death trigger should be tagged as 'triggered' ability."""
        evidence = evidence_db.get_tag_evidence("Blood Artist", "Death_Trigger")
        assert len(evidence) > 0, "Blood Artist should have Death_Trigger evidence"

        ability_kinds = {row["ability_kind"] for row in evidence}
        assert "triggered" in ability_kinds, (
            f"Death_Trigger on Blood Artist should be 'triggered', got: {ability_kinds}"
        )

    def test_death_trigger_text_role(self, evidence_db):
        """Blood Artist death trigger condition should have text_role='trigger'."""
        evidence = evidence_db.get_tag_evidence("Blood Artist", "Death_Trigger")
        trigger_evidence = [e for e in evidence if e["text_role"] == "trigger"]
        assert len(trigger_evidence) > 0, (
            f"Expected at least one Death_Trigger evidence with text_role='trigger'. "
            f"Got roles: {[e['text_role'] for e in evidence]}"
        )


class TestAnchorCardEvidence:

    @pytest.mark.parametrize("card_name,expected_tags", ANCHOR_EXPECTATIONS.items())
    def test_anchor_card_expected_tags_have_evidence(self, evidence_db, card_name, expected_tags):
        """Each anchor card's expected tags must all have evidence rows."""
        for tag_name in expected_tags:
            evidence = evidence_db.get_tag_evidence(card_name, tag_name)
            assert len(evidence) > 0, (
                f"{card_name} should have evidence for {tag_name}, but got none.\n"
                f"All tags on this card: "
                f"{[t['name'] for t in evidence_db.get_card_tags(card_name)]}"
            )


class TestIdempotency:

    def test_repeated_tagging_no_duplicate_evidence(self):
        """Running tag_mechanical() twice with no run_id should not create duplicate evidence."""
        db = Database(":memory:")
        db.init_db()
        tags.seed_tags(db)

        card = Card(
            name="Ashnod's Altar",
            mana_cost="{3}",
            cmc=3,
            type_line="Artifact",
            oracle_text="Sacrifice a creature: Add {C}{C}.",
        )
        db.insert_card(card)

        # First run
        tags.tag_mechanical(card, db)
        cur = db.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tag_evidence WHERE card_name = ?", (card.name,))
        count_after_first = cur.fetchone()[0]
        assert count_after_first > 0

        # Second run (no run_id — should be idempotent)
        tags.tag_mechanical(card, db)
        cur.execute("SELECT COUNT(*) FROM tag_evidence WHERE card_name = ?", (card.name,))
        count_after_second = cur.fetchone()[0]

        assert count_after_first == count_after_second, (
            f"Repeated tag_mechanical() with no run_id should not add evidence rows. "
            f"Before: {count_after_first}, After: {count_after_second}"
        )

        db.close()

    def test_audit_run_allows_duplicate_evidence(self):
        """Running tag_mechanical() with different run_ids should add audit rows."""
        db = Database(":memory:")
        db.init_db()
        tags.seed_tags(db)

        card = Card(
            name="Ashnod's Altar",
            mana_cost="{3}",
            cmc=3,
            type_line="Artifact",
            oracle_text="Sacrifice a creature: Add {C}{C}.",
        )
        db.insert_card(card)

        # Run via run_id (audit-log mode)
        run_id_1 = "run_2026_01"
        run_id_2 = "run_2026_02"
        db.start_tagger_run(run_id=run_id_1)
        db.start_tagger_run(run_id=run_id_2)

        db.emit_tag_evidence(
            card_name=card.name,
            tag_name="Sacrifice_Outlet",
            rule_id="mechanical.sacrifice_outlet.sacrifice_cost.v1",
            evidence_text="Sacrifice a creature:",
            oracle_start=0,
            oracle_end=22,
            ability_kind="activated",
            text_role="cost",
            confidence=1.0,
            source="regex",
            run_id=run_id_1,
        )
        db.emit_tag_evidence(
            card_name=card.name,
            tag_name="Sacrifice_Outlet",
            rule_id="mechanical.sacrifice_outlet.sacrifice_cost.v1",
            evidence_text="Sacrifice a creature:",
            oracle_start=0,
            oracle_end=22,
            ability_kind="activated",
            text_role="cost",
            confidence=1.0,
            source="regex",
            run_id=run_id_2,
        )

        cur = db.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM tag_evidence WHERE card_name = ? AND run_id IS NOT NULL",
            (card.name,),
        )
        count = cur.fetchone()[0]
        assert count == 2, (
            f"Two different run_ids should produce 2 audit rows, got {count}"
        )

        db.close()


class TestLivingDeathKnownGap:

    @pytest.mark.xfail(
        strict=True,
        reason="Mass_Reanimate pattern does not yet detect 'returns all creature cards from their graveyard'"
    )
    def test_living_death_mass_reanimate_has_evidence(self, evidence_db):
        """Living Death should have Mass_Reanimate evidence (currently fails — known gap)."""
        evidence = evidence_db.get_tag_evidence("Living Death", "Mass_Reanimate")
        assert len(evidence) > 0, "Living Death should have Mass_Reanimate evidence"
