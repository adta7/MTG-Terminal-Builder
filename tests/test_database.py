"""
test_database.py — Tests for database operations.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.database import Database
from mtgdeck.models import Card, Deck, DeckCard


def test_database_creation():
    """Test database initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init_db()
        db.connect()

        # Check that tables were created
        cur = db.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}

        assert "cards" in tables
        assert "decks" in tables
        assert "deck_cards" in tables

        db.close()


def test_insert_and_lookup_card():
    """Test inserting and looking up a card."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        db.init_db()
        db.connect()

        card = Card(
            name="Lightning Bolt",
            mana_cost="{R}",
            cmc=1,
            type_line="Instant",
            oracle_text="Lightning Bolt deals 3 damage to any target.",
            colors=["R"],
            color_identity=["R"],
        )

        db.insert_card(card)
        found = db.card_by_name("Lightning Bolt")

        assert found is not None
        assert found.name == "Lightning Bolt"
        assert found.cmc == 1

        db.close()
