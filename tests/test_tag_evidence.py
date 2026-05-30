"""
test_tag_evidence.py — Tests for evidence-based tag tracking.

Phase 2.5: Foundation observability.

The goal is to ensure every tag assignment is traceable:
- Which rule produced it?
- What was the triggering text?
- What ability kind does it come from?
- What text role (cost/effect/trigger)?
- How confident are we?

This vertical slice tests Ashnod's Altar end-to-end.
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
    """In-memory database with schema and seed tags."""
    database = Database(":memory:")
    database.init_db()
    tags.seed_tags(database)
    yield database
    database.close()


class TestTagEvidenceVerticalSlice:
    """Vertical slice: Ashnod's Altar with evidence tracking."""

    def test_ashnod_altar_sacrifice_outlet_with_evidence(self, db):
        """
        Ashnod's Altar has "Sacrifice a creature:" as the cost.

        This should emit a Sacrifice_Outlet tag with:
        - rule_id: "activated_sacrifice_cost_001"
        - ability_kind: "activated"
        - text_role: "cost"
        - evidence_text: "Sacrifice a creature:"
        - confidence: "high" (0.95)
        """
        # Emit the evidence
        result = db.emit_tag_evidence(
            card_name="Ashnod's Altar",
            tag_name="Sacrifice_Outlet",
            rule_id="activated_sacrifice_cost_001",
            evidence_text="Sacrifice a creature:",
            ability_kind="activated",
            text_role="cost",
            confidence=0.95,
            source="regex",
        )

        assert result is True, "emit_tag_evidence should succeed"

        # Verify tag was added to card_tags
        tags = db.get_card_tags("Ashnod's Altar")
        tag_names = {t['name'] for t in tags}
        assert 'Sacrifice_Outlet' in tag_names, "Sacrifice_Outlet should be in card_tags"

        # Find and verify the Sacrifice_Outlet tag
        sac_outlet_tag = next((t for t in tags if t['name'] == 'Sacrifice_Outlet'), None)
        assert sac_outlet_tag is not None
        assert sac_outlet_tag['confidence'] == 0.95
        assert sac_outlet_tag['source'] == 'regex'

        # Verify evidence was recorded
        evidence_list = db.get_tag_evidence("Ashnod's Altar", "Sacrifice_Outlet")
        assert len(evidence_list) > 0, "Evidence should be recorded"

        evidence = evidence_list[0]
        assert evidence['rule_id'] == "activated_sacrifice_cost_001"
        assert evidence['evidence_text'] == "Sacrifice a creature:"
        assert evidence['ability_kind'] == "activated"
        assert evidence['text_role'] == "cost"
        assert evidence['confidence'] == 0.95
        assert evidence['source'] == 'regex'

    def test_ashnod_altar_mana_production_with_evidence(self, db):
        """
        Ashnod's Altar has "Add {C}{C}." as the effect.

        This should emit a Mana_Production tag with:
        - rule_id: "activated_mana_effect_001"
        - ability_kind: "activated"
        - text_role: "effect"
        - evidence_text: "Add {C}{C}."
        - confidence: 0.95
        """
        result = db.emit_tag_evidence(
            card_name="Ashnod's Altar",
            tag_name="Mana_Production",
            rule_id="activated_mana_effect_001",
            evidence_text="Add {C}{C}.",
            ability_kind="activated",
            text_role="effect",
            confidence=0.95,
            source="regex",
        )

        assert result is True

        tags = db.get_card_tags("Ashnod's Altar")
        tag_names = {t['name'] for t in tags}
        assert 'Mana_Production' in tag_names

        evidence_list = db.get_tag_evidence("Ashnod's Altar", "Mana_Production")
        assert len(evidence_list) > 0

        evidence = evidence_list[0]
        assert evidence['rule_id'] == "activated_mana_effect_001"
        assert evidence['evidence_text'] == "Add {C}{C}."
        assert evidence['ability_kind'] == "activated"
        assert evidence['text_role'] == "effect"

    def test_ashnod_altar_must_have_and_must_not_have(self, db):
        """
        Golden test: Ashnod's Altar verification.

        must_have:
        - Sacrifice_Outlet
        - Mana_Production

        must_not_have:
        - Death_Trigger (no death trigger)
        - Token_Generation (no token generation)
        - Reanimation (no reanimation)
        """
        # Tags are pre-seeded, no need to create them

        # Emit the positive tags
        db.emit_tag_evidence(
            card_name="Ashnod's Altar",
            tag_name="Sacrifice_Outlet",
            rule_id="activated_sacrifice_cost_001",
            evidence_text="Sacrifice a creature:",
            ability_kind="activated",
            text_role="cost",
            confidence=0.95,
            source="regex",
        )

        db.emit_tag_evidence(
            card_name="Ashnod's Altar",
            tag_name="Mana_Production",
            rule_id="activated_mana_effect_001",
            evidence_text="Add {C}{C}.",
            ability_kind="activated",
            text_role="effect",
            confidence=0.95,
            source="regex",
        )

        # Get all tags
        tags = db.get_card_tags("Ashnod's Altar")
        tag_names = {t['name'] for t in tags}

        # Verify must_have
        assert 'Sacrifice_Outlet' in tag_names, "must_have: Sacrifice_Outlet"
        assert 'Mana_Production' in tag_names, "must_have: Mana_Production"

        # Verify must_not_have (these tags should NOT be present)
        assert 'Death_Trigger' not in tag_names, "must_not_have: Death_Trigger"
        assert 'Token_Generation' not in tag_names, "must_not_have: Token_Generation"
        assert 'Reanimation' not in tag_names, "must_not_have: Reanimation"

    def test_evidence_queryable_by_rule_id(self, db):
        """Evidence should be queryable by rule_id for auditing."""
        db.emit_tag_evidence(
            card_name="Ashnod's Altar",
            tag_name="Sacrifice_Outlet",
            rule_id="activated_sacrifice_cost_001",
            evidence_text="Sacrifice a creature:",
            ability_kind="activated",
            text_role="cost",
            confidence=0.95,
            source="regex",
        )

        # Query all evidence for this card
        all_evidence = db.get_tag_evidence("Ashnod's Altar")
        assert len(all_evidence) > 0

        # Check rule_id is queryable
        rule_ids = {e['rule_id'] for e in all_evidence}
        assert "activated_sacrifice_cost_001" in rule_ids

    def test_tagger_run_tracking(self, db):
        """Tagger runs should be tracked for audit trail."""
        run_id = "run_2026_05_30_test_ashnod"

        # Start a tagger run
        result = db.start_tagger_run(
            run_id=run_id,
            tagger_version="2.9.0",
            rules_version="mechanical_v35",
            card_scope="deck_pool",
            notes="Testing Ashnod's Altar evidence"
        )
        assert result is True

        # Emit evidence with run_id
        db.emit_tag_evidence(
            card_name="Ashnod's Altar",
            tag_name="Sacrifice_Outlet",
            rule_id="activated_sacrifice_cost_001",
            evidence_text="Sacrifice a creature:",
            ability_kind="activated",
            text_role="cost",
            confidence=0.95,
            source="regex",
            run_id=run_id,
        )

        # Verify run_id is stored in evidence
        evidence = db.get_tag_evidence("Ashnod's Altar")
        assert evidence[0]['run_id'] == run_id

    def test_backward_compatibility_old_tag_queries(self, db):
        """
        Old code that uses get_card_tags should still work.

        The evidence system should not break existing queries.
        """
        # Emit evidence the new way
        db.emit_tag_evidence(
            card_name="Ashnod's Altar",
            tag_name="Sacrifice_Outlet",
            rule_id="activated_sacrifice_cost_001",
            evidence_text="Sacrifice a creature:",
            confidence=0.95,
            source="regex",
        )

        # Old code queries card_tags the same way
        tags = db.get_card_tags("Ashnod's Altar")
        assert len(tags) > 0
        assert tags[0]['name'] == 'Sacrifice_Outlet'
        assert tags[0]['confidence'] == 0.95
