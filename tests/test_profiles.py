"""
test_profiles.py — Tests for Phase 3 deck profile comparison.

Covers:
  - load_profile: valid JSON, missing file, bad JSON, missing targets key
  - compare_to_profile: ok / low / high statuses, lands, avg_mana_value
  - count_roles_in_deck: single-function card, multi-function card,
                         untagged card, deduplication within a category
  - find_profile: bare name, .json extension, not found
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from mtgdeck.database import Database
from mtgdeck.models import Card, Deck, DeckCard, DeckAnalysis
from mtgdeck import tags
from mtgdeck.profiles import (
    Profile,
    ProfileGap,
    load_profile,
    count_roles_in_deck,
    compare_to_profile,
    find_profile,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """In-memory database with schema and all seed tags."""
    database = Database(":memory:")
    database.init_db()
    tags.seed_tags(database)
    yield database
    database.close()


@pytest.fixture
def profile_dir(tmp_path):
    """Temporary directory pre-populated with two profile JSON files."""
    (tmp_path / "mono_black_reanimator.json").write_text(json.dumps({
        "name": "Mono Black Reanimator",
        "description": "Test profile.",
        "targets": {
            "lands":          [35, 37],
            "ramp":           [10, 13],
            "draw":           [10, 14],
            "removal":        [8, 11],
            "board_wipes":    [2, 4],
            "reanimation":    [9, 14],
            "sac_outlets":    [5, 8],
            "protection":     [3, 6],
            "graveyard_fill": [5, 9],
            "wincons":        [4, 7],
            "avg_mana_value": [2.8, 3.8],
        },
    }))
    (tmp_path / "generic_commander.json").write_text(json.dumps({
        "name": "Generic Commander",
        "description": "Wide baseline.",
        "targets": {
            "lands": [33, 38],
            "ramp":  [8, 14],
        },
    }))
    return tmp_path


def _make_analysis(
    land_count=35,
    avg_mana_value=3.2,
    deck_name="Test Deck",
) -> DeckAnalysis:
    """Build a minimal DeckAnalysis for comparison tests."""
    return DeckAnalysis(
        deck_name=deck_name,
        total_cards=100,
        land_count=land_count,
        spell_permanent_count=50,
        spell_nonpermanent_count=15,
        avg_mana_value=avg_mana_value,
    )


def _make_card(name: str, type_line: str = "Creature") -> Card:
    return Card(
        name=name,
        mana_cost="",
        cmc=2,
        type_line=type_line,
        oracle_text="",
    )


# ─── load_profile ─────────────────────────────────────────────────────────────

class TestLoadProfile:

    def test_loads_valid_profile(self, profile_dir):
        p = load_profile(profile_dir / "mono_black_reanimator.json")
        assert p.name == "Mono Black Reanimator"
        assert p.targets["ramp"] == [10, 13]
        assert p.targets["lands"] == [35, 37]
        assert p.targets["avg_mana_value"] == [2.8, 3.8]

    def test_loads_description(self, profile_dir):
        p = load_profile(profile_dir / "mono_black_reanimator.json")
        assert "Test profile" in p.description

    def test_missing_file_raises(self, profile_dir):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_profile(profile_dir / "doesnt_exist.json")

    def test_invalid_json_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        with pytest.raises(ValueError, match="Invalid profile JSON"):
            load_profile(bad)

    def test_missing_targets_key_raises(self, tmp_path):
        no_targets = tmp_path / "no_targets.json"
        no_targets.write_text(json.dumps({"name": "Oops"}))
        with pytest.raises(ValueError, match="missing required 'targets'"):
            load_profile(no_targets)

    def test_name_falls_back_to_stem(self, tmp_path):
        """When JSON has no 'name' key, filename stem is used."""
        p_file = tmp_path / "my_custom_profile.json"
        p_file.write_text(json.dumps({"targets": {"lands": [35, 37]}}))
        p = load_profile(p_file)
        assert p.name == "my_custom_profile"


# ─── compare_to_profile ───────────────────────────────────────────────────────

class TestCompareToProfile:

    def _simple_profile(self) -> Profile:
        return Profile(
            name="Simple",
            description="",
            targets={
                "lands":          [35, 37],
                "ramp":           [10, 13],
                "draw":           [10, 14],
                "avg_mana_value": [2.8, 3.8],
            },
        )

    def test_all_ok_returns_all_ok_status(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=3.2)
        role_counts = {"ramp": 11, "draw": 12}
        gaps = compare_to_profile(analysis, role_counts, profile)
        assert all(g.status == "ok" for g in gaps)

    def test_low_category_detected(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=3.2)
        role_counts = {"ramp": 7, "draw": 12}   # ramp below 10
        gaps = compare_to_profile(analysis, role_counts, profile)
        ramp_gap = next(g for g in gaps if g.category == "ramp")
        assert ramp_gap.status == "low"
        assert ramp_gap.actual == 7.0
        assert ramp_gap.delta < 0

    def test_high_category_detected(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=3.2)
        role_counts = {"ramp": 16, "draw": 12}   # ramp above 13
        gaps = compare_to_profile(analysis, role_counts, profile)
        ramp_gap = next(g for g in gaps if g.category == "ramp")
        assert ramp_gap.status == "high"
        assert ramp_gap.delta > 0

    def test_lands_uses_analysis_land_count(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=33, avg_mana_value=3.2)  # below 35
        role_counts = {"ramp": 11, "draw": 12}
        gaps = compare_to_profile(analysis, role_counts, profile)
        lands_gap = next(g for g in gaps if g.category == "lands")
        assert lands_gap.status == "low"
        assert lands_gap.actual == 33.0

    def test_avg_mana_value_uses_analysis_avg_mv(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=4.5)  # above 3.8
        role_counts = {"ramp": 11, "draw": 12}
        gaps = compare_to_profile(analysis, role_counts, profile)
        mv_gap = next(g for g in gaps if g.category == "avg_mana_value")
        assert mv_gap.status == "high"
        assert mv_gap.actual == pytest.approx(4.5)

    def test_missing_category_in_role_counts_treats_as_zero(self):
        """A category absent from role_counts is treated as 0 (no cards fill it)."""
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=3.2)
        gaps = compare_to_profile(analysis, {}, profile)  # empty role_counts
        ramp_gap = next(g for g in gaps if g.category == "ramp")
        assert ramp_gap.status == "low"
        assert ramp_gap.actual == 0.0

    def test_returns_one_gap_per_profile_category(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=3.2)
        gaps = compare_to_profile(analysis, {"ramp": 11, "draw": 12}, profile)
        assert len(gaps) == len(profile.targets)

    def test_gap_message_low_mentions_shortfall(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=3.2)
        role_counts = {"ramp": 7, "draw": 12}
        gaps = compare_to_profile(analysis, role_counts, profile)
        ramp_gap = next(g for g in gaps if g.category == "ramp")
        assert "short" in ramp_gap.message.lower()

    def test_gap_message_high_mentions_over(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=3.2)
        role_counts = {"ramp": 20, "draw": 12}
        gaps = compare_to_profile(analysis, role_counts, profile)
        ramp_gap = next(g for g in gaps if g.category == "ramp")
        assert "over" in ramp_gap.message.lower()

    def test_gap_display_name_populated(self):
        profile = self._simple_profile()
        analysis = _make_analysis(land_count=36, avg_mana_value=3.2)
        gaps = compare_to_profile(analysis, {"ramp": 11, "draw": 12}, profile)
        names = {g.display_name for g in gaps}
        assert "Ramp" in names
        assert "Lands" in names
        assert "Avg MV" in names


# ─── count_roles_in_deck ──────────────────────────────────────────────────────

class TestCountRolesInDeck:

    def _seed_card_with_tags(self, db, card_name: str, func_tags=(), mech_tags=()):
        """Insert a card and give it specific functional/mechanical tags."""
        card = _make_card(card_name)
        db.insert_card(card)
        for tag in func_tags:
            db.tag_card(card_name, tag, confidence=1.0, source="test")
        for tag in mech_tags:
            db.tag_card(card_name, tag, confidence=1.0, source="test")

    def _deck(self, *card_names: str) -> Deck:
        return Deck(
            name="Test",
            cards=[DeckCard(name=n, count=1) for n in card_names],
        )

    def test_single_function_card_counts_in_one_category(self, db):
        self._seed_card_with_tags(db, "Animate Dead", func_tags=["Recursion"])
        deck = self._deck("Animate Dead")
        counts = count_roles_in_deck(deck, db)
        assert counts.get("reanimation") == 1

    def test_multi_function_card_counts_in_multiple_categories(self, db):
        """Ashnod's Altar: Mana_Engine (functional→ramp) + Sacrifice_Outlet (mechanical→sac_outlets)."""
        self._seed_card_with_tags(
            db, "Ashnod's Altar",
            func_tags=["Mana_Engine"],
            mech_tags=["Sacrifice_Outlet"],
        )
        deck = self._deck("Ashnod's Altar")
        counts = count_roles_in_deck(deck, db)
        # Counts as 1 ramp (Mana_Engine) AND 1 sac_outlet (Sacrifice_Outlet mechanical)
        assert counts.get("ramp") == 1
        assert counts.get("sac_outlets") == 1

    def test_same_category_tags_do_not_double_count(self, db):
        """A card with Mana_Acceleration AND Mana_Engine should count as 1 ramp, not 2."""
        self._seed_card_with_tags(
            db, "Crypt Ghast",
            func_tags=["Mana_Acceleration", "Mana_Engine"],
        )
        deck = self._deck("Crypt Ghast")
        counts = count_roles_in_deck(deck, db)
        assert counts.get("ramp") == 1

    def test_untagged_card_contributes_nothing(self, db):
        db.insert_card(_make_card("Swamp", type_line="Basic Land"))
        deck = self._deck("Swamp")
        counts = count_roles_in_deck(deck, db)
        assert sum(counts.values()) == 0

    def test_mechanical_tag_fills_board_wipes(self, db):
        """Board_Wipe is a mechanical tag that maps to the board_wipes category."""
        self._seed_card_with_tags(
            db, "Toxic Deluge",
            mech_tags=["Board_Wipe"],
        )
        deck = self._deck("Toxic Deluge")
        counts = count_roles_in_deck(deck, db)
        assert counts.get("board_wipes") == 1

    def test_mechanical_self_mill_fills_graveyard_fill(self, db):
        self._seed_card_with_tags(
            db, "Perpetual Timepiece",
            mech_tags=["Self_Mill"],
        )
        deck = self._deck("Perpetual Timepiece")
        counts = count_roles_in_deck(deck, db)
        assert counts.get("graveyard_fill") == 1

    def test_multiple_cards_accumulate(self, db):
        for name in ["Reanimate", "Animate Dead", "Living Death"]:
            self._seed_card_with_tags(db, name, func_tags=["Recursion"])
        deck = self._deck("Reanimate", "Animate Dead", "Living Death")
        counts = count_roles_in_deck(deck, db)
        assert counts.get("reanimation") == 3

    def test_card_with_count_gt_1_multiplies(self, db):
        """In non-Commander formats a card may appear more than once — count respects it."""
        self._seed_card_with_tags(db, "Lightning Bolt", func_tags=["Removal"])
        deck = Deck(
            name="Test",
            cards=[DeckCard(name="Lightning Bolt", count=4)],
        )
        counts = count_roles_in_deck(deck, db)
        assert counts.get("removal") == 4

    def test_empty_deck_returns_empty_dict(self, db):
        deck = Deck(name="Empty", cards=[])
        counts = count_roles_in_deck(deck, db)
        assert counts == {}

    def test_unknown_card_silently_skipped(self, db):
        """Cards not in the tag DB contribute nothing and do not raise."""
        deck = self._deck("Totally Unknown Card XYZ")
        counts = count_roles_in_deck(deck, db)
        assert sum(counts.values()) == 0


# ─── find_profile ─────────────────────────────────────────────────────────────

class TestFindProfile:

    def test_finds_by_bare_name(self, profile_dir):
        path = find_profile("mono_black_reanimator", profile_dir)
        assert path.name == "mono_black_reanimator.json"

    def test_finds_by_name_with_json_extension(self, profile_dir):
        path = find_profile("mono_black_reanimator.json", profile_dir)
        assert path.name == "mono_black_reanimator.json"

    def test_finds_generic_commander(self, profile_dir):
        path = find_profile("generic_commander", profile_dir)
        assert path.name == "generic_commander.json"

    def test_not_found_raises_with_available_hint(self, profile_dir):
        with pytest.raises(FileNotFoundError, match="Available:"):
            find_profile("nonexistent_profile", profile_dir)
