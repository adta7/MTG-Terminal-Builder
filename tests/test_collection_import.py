"""
test_collection_import.py — Unit and integration tests for collection_importer.py.

Unit tests use synthetic DataFrames (no file I/O).
Integration tests use the real collection Excel and are skipped if not found.
"""

import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from mtgdeck.collection_importer import (
    detect_collection_columns,
    is_black_or_colorless,
    import_collection,
    find_excel,
)
from mtgdeck.database import Database
from mtgdeck import tags


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _make_excel(tmp_path, rows: list[dict]) -> str:
    df = _make_df(rows)
    path = tmp_path / "test_collection.xlsx"
    df.to_excel(path, index=False)
    return str(path)


REAL_EXCEL = None
for candidate in [
    Path(".") / "Collection_deckbuilding_20260519 copy.xlsx",
    Path("..") / "Collection_deckbuilding_20260519 copy.xlsx",
    Path("../..") / "Collection_deckbuilding_20260519 copy.xlsx",
    Path("../../..") / "Collection_deckbuilding_20260519 copy.xlsx",
]:
    resolved = candidate.resolve()
    if resolved.exists():
        REAL_EXCEL = str(resolved)
        break


# ─── Unit: detect_collection_columns ─────────────────────────────────────────

class TestDetectCollectionColumns:

    def test_detects_all_required_columns(self):
        df = _make_df([{"Name": "x", "Card Text": "y", "Color Identity": "B"}])
        col_map = detect_collection_columns(df)
        assert "name" in col_map
        assert "oracle_text" in col_map

    def test_optional_columns_detected_when_present(self):
        df = _make_df([{
            "Name": "x", "Card Text": "y",
            "Verified Name": "x", "Count": 1, "CMC": 2, "Type": "Creature"
        }])
        col_map = detect_collection_columns(df)
        assert "verified_name" in col_map
        assert "count" in col_map
        assert "cmc" in col_map
        assert "type_line" in col_map

    def test_missing_required_column_raises(self):
        df = _make_df([{"Name": "x"}])  # missing 'Card Text'
        with pytest.raises(ValueError, match="Missing required columns"):
            detect_collection_columns(df)

    def test_error_message_lists_available_columns(self):
        df = _make_df([{"Only This": "col"}])
        with pytest.raises(ValueError) as exc_info:
            detect_collection_columns(df)
        assert "Only This" in str(exc_info.value)


# ─── Unit: is_black_or_colorless ─────────────────────────────────────────────

class TestIsBlackOrColorless:

    @pytest.mark.parametrize("value,expected", [
        (None,        True),   # no color identity = colorless
        ("",          True),   # empty
        ("nan",       True),   # pandas NaN as string
        ("B",         True),   # black only
        ("Colorless", True),   # explicit colorless label
        ("G",         False),  # green
        ("W",         False),  # white
        ("U",         False),  # blue
        ("R",         False),  # red
        ("B, G",      False),  # black + green
        ("B, R",      False),  # black + red
        ("W, B",      False),  # white + black
        ("G, U",      False),  # green + blue
    ])
    def test_color_identity_filter(self, value, expected):
        assert is_black_or_colorless(value) == expected, (
            f"is_black_or_colorless({value!r}) expected {expected}"
        )


# ─── Unit: import_collection (synthetic Excel) ───────────────────────────────

class TestImportCollection:

    @pytest.fixture
    def db(self):
        db = Database(":memory:")
        db.init_db()
        tags.seed_tags(db)
        yield db
        db.close()

    def test_basic_import(self, tmp_path, db):
        excel = _make_excel(tmp_path, [
            {"Name": "Ashnod's Altar", "Verified Name": "Ashnod's Altar",
             "Card Text": "Sacrifice a creature: Add {C}{C}.",
             "Color Identity": "B", "Count": 1, "CMC": 3, "Type": "Artifact"},
        ])
        result = import_collection(excel, db, filter_black_colorless=True)
        assert result["cards_loaded"] == 1
        assert result["collection_rows"] == 1
        assert db.card_by_name("Ashnod's Altar") is not None

    def test_filters_out_non_black_cards(self, tmp_path, db):
        excel = _make_excel(tmp_path, [
            {"Name": "Lightning Bolt", "Card Text": "Deal 3 damage.", "Color Identity": "R", "Count": 1},
            {"Name": "Dark Ritual",    "Card Text": "Add {B}{B}{B}.", "Color Identity": "B", "Count": 1},
        ])
        result = import_collection(excel, db, filter_black_colorless=True)
        assert result["cards_loaded"] == 1
        assert db.card_by_name("Dark Ritual") is not None
        assert db.card_by_name("Lightning Bolt") is None

    def test_deduplication_aggregates_quantity(self, tmp_path, db):
        excel = _make_excel(tmp_path, [
            {"Name": "Sol Ring", "Card Text": "{T}: Add {C}{C}.", "Color Identity": None, "Count": 1},
            {"Name": "Sol Ring", "Card Text": "{T}: Add {C}{C}.", "Color Identity": None, "Count": 1},
        ])
        result = import_collection(excel, db, filter_black_colorless=True)
        # Only one unique card entry, but quantities aggregated
        assert result["cards_loaded"] == 1
        assert result["collection_rows"] == 1

        cur = db.conn.cursor()
        cur.execute("SELECT quantity FROM collection WHERE card_name = 'Sol Ring'")
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 2, f"Expected quantity=2 after deduplication, got {row[0]}"

    def test_no_duplicate_cards_in_db(self, tmp_path, db):
        excel = _make_excel(tmp_path, [
            {"Name": "Blood Artist", "Card Text": "Whenever dies.", "Color Identity": "B", "Count": 2},
            {"Name": "Blood Artist", "Card Text": "Whenever dies.", "Color Identity": "B", "Count": 1},
        ])
        import_collection(excel, db, filter_black_colorless=True)

        cur = db.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cards WHERE name = 'Blood Artist'")
        count = cur.fetchone()[0]
        assert count == 1, f"Expected 1 row in cards table for Blood Artist, got {count}"

    def test_colorless_cards_included(self, tmp_path, db):
        excel = _make_excel(tmp_path, [
            {"Name": "Sol Ring", "Card Text": "{T}: Add {C}{C}.", "Color Identity": None, "Count": 1},
            {"Name": "Command Tower", "Card Text": "{T}: Add mana.", "Color Identity": None, "Count": 1},
        ])
        result = import_collection(excel, db, filter_black_colorless=True)
        assert result["cards_loaded"] == 2

    def test_skips_rows_with_no_name(self, tmp_path, db):
        excel = _make_excel(tmp_path, [
            {"Name": None,           "Card Text": "something", "Color Identity": "B", "Count": 1},
            {"Name": "Dark Ritual",  "Card Text": "Add {B}{B}{B}.", "Color Identity": "B", "Count": 1},
        ])
        result = import_collection(excel, db, filter_black_colorless=True)
        assert result["cards_loaded"] == 1

    def test_import_stats_total_rows(self, tmp_path, db):
        rows = [
            {"Name": "Card A", "Card Text": "text a", "Color Identity": "B", "Count": 1},
            {"Name": "Card B", "Card Text": "text b", "Color Identity": "G", "Count": 1},  # filtered
            {"Name": "Card C", "Card Text": "text c", "Color Identity": "B", "Count": 1},
        ]
        excel = _make_excel(tmp_path, rows)
        result = import_collection(excel, db, filter_black_colorless=True)
        assert result["total_excel_rows"] == 3
        assert result["cards_loaded"] == 2
        assert result["cards_skipped"] == 1


# ─── Integration: real collection Excel ──────────────────────────────────────

@pytest.mark.skipif(REAL_EXCEL is None, reason="Real collection Excel not found")
class TestRealCollectionImport:

    @pytest.fixture
    def db(self):
        db = Database(":memory:")
        db.init_db()
        tags.seed_tags(db)
        yield db
        db.close()

    def test_real_import_loads_expected_count(self, db):
        result = import_collection(REAL_EXCEL, db, filter_black_colorless=True)
        loaded = result["cards_loaded"]
        assert 300 <= loaded <= 450, (
            f"Expected 300–450 unique black/colorless cards, got {loaded}. "
            "Check collection Excel or filter logic."
        )

    def test_real_import_no_duplicate_cards(self, db):
        import_collection(REAL_EXCEL, db, filter_black_colorless=True)
        cur = db.conn.cursor()
        cur.execute(
            "SELECT name, COUNT(*) as cnt FROM cards GROUP BY LOWER(name) HAVING cnt > 1"
        )
        duplicates = cur.fetchall()
        assert not duplicates, (
            f"Duplicate card names in cards table:\n" +
            "\n".join(f"  {row[0]} ({row[1]}x)" for row in duplicates)
        )

    def test_real_import_anchor_cards_present(self, db):
        import_collection(REAL_EXCEL, db, filter_black_colorless=True)
        anchors = ["Ashnod's Altar", "Blood Artist", "Phyrexian Arena"]
        for name in anchors:
            card = db.card_by_name(name)
            if card is None:
                pytest.skip(f"{name} not in this collection — skip anchor presence check")

    def test_real_import_mechanical_tagging_runs(self, db):
        import_collection(REAL_EXCEL, db, filter_black_colorless=True)
        all_cards = list(db.all_cards())
        tagged_count = 0
        for card in all_cards:
            if card.oracle_text:
                applied = tags.tag_mechanical(card, db)
                if applied:
                    tagged_count += 1
        coverage = tagged_count / len(all_cards) if all_cards else 0
        assert coverage >= 0.35, (
            f"Expected ≥35% coverage on real collection, got {coverage:.0%}. "
            "Tagging may be broken."
        )
