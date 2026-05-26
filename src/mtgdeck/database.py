"""
database.py — SQLite persistence layer for MTG data.

Manages:
- Schema creation and migrations
- Card data (from Scryfall)
- Deck storage
- Collection tracking
- Role tags (phase 2)
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .models import Card, Deck, DeckCard


class Database:
    """SQLite database for MTG card and deck data."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self):
        """Open database connection."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def init_db(self):
        """Create schema and run migrations."""
        self.connect()
        cur = self.conn.cursor()

        # Cards table: Scryfall data
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                mana_cost TEXT,
                cmc INTEGER,
                type_line TEXT,
                oracle_text TEXT,
                power TEXT,
                toughness TEXT,
                loyalty TEXT,
                colors TEXT,
                color_identity TEXT,
                keywords TEXT,
                rarity TEXT,
                set_name TEXT,
                scryfall_uri TEXT,
                legality_commander TEXT,
                legality_modern TEXT,
                legality_standard TEXT,
                updated_at TIMESTAMP
            )
        """)

        # Decks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                commander_name TEXT,
                created_at TIMESTAMP,
                edited_at TIMESTAMP,
                path TEXT
            )
        """)

        # Deck cards: many-to-many
        cur.execute("""
            CREATE TABLE IF NOT EXISTS deck_cards (
                id INTEGER PRIMARY KEY,
                deck_id INTEGER NOT NULL,
                card_name TEXT NOT NULL,
                count INTEGER NOT NULL,
                is_sideboard INTEGER DEFAULT 0,
                FOREIGN KEY(deck_id) REFERENCES decks(id),
                FOREIGN KEY(card_name) REFERENCES cards(name),
                UNIQUE(deck_id, card_name, is_sideboard)
            )
        """)

        # Collection: user's owned cards
        cur.execute("""
            CREATE TABLE IF NOT EXISTS collection (
                id INTEGER PRIMARY KEY,
                card_name TEXT NOT NULL,
                quantity INTEGER,
                set_code TEXT,
                foil INTEGER,
                condition TEXT,
                UNIQUE(card_name, set_code),
                FOREIGN KEY(card_name) REFERENCES cards(name)
            )
        """)

        # Card tags: role classification (phase 2)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS card_tags (
                id INTEGER PRIMARY KEY,
                card_name TEXT NOT NULL,
                role TEXT NOT NULL,
                strength INTEGER,
                UNIQUE(card_name, role),
                FOREIGN KEY(card_name) REFERENCES cards(name)
            )
        """)

        self.conn.commit()

    # ─── Card operations ──────────────────────────────────────────────────────

    def card_by_name(self, name: str) -> Optional[Card]:
        """Lookup a card by name (case-insensitive)."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM cards WHERE LOWER(name) = LOWER(?)", (name,))
        row = cur.fetchone()
        return self._row_to_card(row) if row else None

    def cards_by_type(self, type_substr: str) -> List[Card]:
        """Find cards whose type_line contains substring."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM cards WHERE LOWER(type_line) LIKE LOWER(?)",
            (f"%{type_substr}%",),
        )
        return [self._row_to_card(row) for row in cur.fetchall()]

    def cards_by_color(self, color_identity: str) -> List[Card]:
        """Find cards matching color identity."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM cards WHERE color_identity LIKE ?",
            (f"%{color_identity}%",),
        )
        return [self._row_to_card(row) for row in cur.fetchall()]

    def all_cards(self) -> List[Card]:
        """Return all cards in database."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM cards ORDER BY name")
        return [self._row_to_card(row) for row in cur.fetchall()]

    def card_names_list(self) -> list[str]:
        """Return all card names for fuzzy matching."""
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM cards ORDER BY name")
        return [row[0] for row in cur.fetchall()]

    def insert_card(self, card: Card) -> int:
        """Insert or replace a card. Returns card id."""
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO cards (
                name, mana_cost, cmc, type_line, oracle_text,
                power, toughness, loyalty, colors, color_identity,
                keywords, rarity, set_name, scryfall_uri,
                legality_commander, legality_modern, legality_standard,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card.name,
                card.mana_cost,
                card.cmc,
                card.type_line,
                card.oracle_text,
                card.power,
                card.toughness,
                card.loyalty,
                json.dumps(card.colors),
                json.dumps(card.color_identity),
                json.dumps(card.keywords),
                card.rarity,
                card.set_name,
                card.scryfall_uri,
                card.legalities.get("commander"),
                card.legalities.get("modern"),
                card.legalities.get("standard"),
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def insert_cards_bulk(self, cards: List[Card]) -> int:
        """Insert multiple cards efficiently. Returns count."""
        cur = self.conn.cursor()
        rows = [
            (
                card.name,
                card.mana_cost,
                card.cmc,
                card.type_line,
                card.oracle_text,
                card.power,
                card.toughness,
                card.loyalty,
                json.dumps(card.colors),
                json.dumps(card.color_identity),
                json.dumps(card.keywords),
                card.rarity,
                card.set_name,
                card.scryfall_uri,
                card.legalities.get("commander"),
                card.legalities.get("modern"),
                card.legalities.get("standard"),
                datetime.now().isoformat(),
            )
            for card in cards
        ]
        cur.executemany(
            """
            INSERT OR REPLACE INTO cards (
                name, mana_cost, cmc, type_line, oracle_text,
                power, toughness, loyalty, colors, color_identity,
                keywords, rarity, set_name, scryfall_uri,
                legality_commander, legality_modern, legality_standard,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()
        return len(cards)

    def card_count(self) -> int:
        """Total cards in database."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cards")
        return cur.fetchone()[0]

    # ─── Deck operations ──────────────────────────────────────────────────────

    def save_deck(self, deck: Deck) -> int:
        """Save a deck. Returns deck id."""
        cur = self.conn.cursor()
        now = datetime.now().isoformat()

        # Insert or update deck
        cur.execute(
            """
            INSERT INTO decks (name, commander_name, created_at, edited_at, path)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET edited_at = ?
            """,
            (deck.name, deck.commander, deck.created or now, now, deck.path, now),
        )
        deck_id = cur.lastrowid

        # Clear existing deck cards
        cur.execute("DELETE FROM deck_cards WHERE deck_id = ?", (deck_id,))

        # Insert main deck cards
        for card in deck.cards:
            cur.execute(
                """
                INSERT INTO deck_cards (deck_id, card_name, count, is_sideboard)
                VALUES (?, ?, ?, 0)
                """,
                (deck_id, card.name, card.count),
            )

        # Insert sideboard cards
        for card in deck.sideboard:
            cur.execute(
                """
                INSERT INTO deck_cards (deck_id, card_name, count, is_sideboard)
                VALUES (?, ?, ?, 1)
                """,
                (deck_id, card.name, card.count),
            )

        self.conn.commit()
        return deck_id

    def load_deck(self, deck_id: int) -> Optional[Deck]:
        """Load a deck by id."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
        deck_row = cur.fetchone()
        if not deck_row:
            return None

        cur.execute(
            "SELECT card_name, count FROM deck_cards WHERE deck_id = ? AND is_sideboard = 0",
            (deck_id,),
        )
        cards = [DeckCard(name=row["card_name"], count=row["count"]) for row in cur.fetchall()]

        cur.execute(
            "SELECT card_name, count FROM deck_cards WHERE deck_id = ? AND is_sideboard = 1",
            (deck_id,),
        )
        sideboard = [DeckCard(name=row["card_name"], count=row["count"]) for row in cur.fetchall()]

        return Deck(
            name=deck_row["name"],
            cards=cards,
            sideboard=sideboard,
            commander=deck_row["commander_name"],
            created=deck_row["created_at"],
            edited=deck_row["edited_at"],
            path=deck_row["path"],
        )

    def list_decks(self) -> List[Deck]:
        """Return all decks."""
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM decks ORDER BY edited_at DESC")
        return [self.load_deck(row["id"]) for row in cur.fetchall()]

    def delete_deck(self, deck_id: int):
        """Delete a deck and all its cards."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM deck_cards WHERE deck_id = ?", (deck_id,))
        cur.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
        self.conn.commit()

    # ─── Tag operations (phase 2) ─────────────────────────────────────────────

    def save_card_tag(self, card_name: str, role: str, strength: int):
        """Save a role tag for a card."""
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO card_tags (card_name, role, strength)
            VALUES (?, ?, ?)
            """,
            (card_name, role, strength),
        )
        self.conn.commit()

    def get_card_tags(self, card_name: str) -> dict[str, int]:
        """Get all roles for a card. Returns {role: strength}."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT role, strength FROM card_tags WHERE LOWER(card_name) = LOWER(?)",
            (card_name,),
        )
        return {row["role"]: row["strength"] for row in cur.fetchall()}

    def load_all_tags(self) -> dict[str, dict[str, int]]:
        """Load all card tags. Returns {card_name: {role: strength}}."""
        cur = self.conn.cursor()
        cur.execute("SELECT card_name, role, strength FROM card_tags ORDER BY card_name")
        result = {}
        for row in cur.fetchall():
            if row["card_name"] not in result:
                result[row["card_name"]] = {}
            result[row["card_name"]][row["role"]] = row["strength"]
        return result

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _row_to_card(self, row) -> Card:
        """Convert a sqlite3.Row to a Card model."""
        return Card(
            name=row["name"],
            mana_cost=row["mana_cost"] or "",
            cmc=row["cmc"] or 0,
            type_line=row["type_line"] or "",
            oracle_text=row["oracle_text"] or "",
            power=row["power"],
            toughness=row["toughness"],
            loyalty=row["loyalty"],
            colors=json.loads(row["colors"]) if row["colors"] else [],
            color_identity=json.loads(row["color_identity"]) if row["color_identity"] else [],
            keywords=json.loads(row["keywords"]) if row["keywords"] else [],
            rarity=row["rarity"] or "",
            set_name=row["set_name"] or "",
            scryfall_uri=row["scryfall_uri"] or "",
            legalities={
                "commander": row["legality_commander"],
                "modern": row["legality_modern"],
                "standard": row["legality_standard"],
            },
        )
