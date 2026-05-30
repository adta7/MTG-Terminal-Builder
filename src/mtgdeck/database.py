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

        # Tags: tag definitions by layer (phase 2)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                layer TEXT NOT NULL,
                description TEXT
            )
        """)

        # Migrate card_tags from old flat schema if it exists
        cur.execute("PRAGMA table_info(card_tags)")
        old_columns = {row[1] for row in cur.fetchall()}
        if "role" in old_columns or "strength" in old_columns:
            cur.execute("DROP TABLE card_tags")

        # Card tags: card-to-tag relationships with confidence (phase 2)
        # confidence: 0.0-1.0 scale
        #   1.0 = mechanically certain (oracle text is explicit)
        #   0.7 = confident (well-known role)
        #   0.4 = contextual (depends on deck)
        #   0.1 = speculative
        #
        # NOTE: card_id is intentionally NOT a FK to cards(name).
        # Tags are metadata about a card by name and should work even
        # for cards not yet indexed from Scryfall. tag_id IS enforced
        # so every tag must exist in the registry before use.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS card_tags (
                card_id TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'manual',
                note TEXT,
                PRIMARY KEY (card_id, tag_id),
                FOREIGN KEY(tag_id) REFERENCES tags(id)
            )
        """)

        # Synergy edges: relationships between cards (phase 2)
        # strength: 0.0-1.0 scale
        #   1.0 = core synergy (the combo itself)
        #   0.7 = strong synergy
        #   0.5 = moderate
        #   0.3 = incidental
        #
        # NOTE: card_a/card_b are NOT FK to cards(name) — synergy data
        # can be seeded independently of Scryfall indexing.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS synergy_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_a TEXT NOT NULL,
                card_b TEXT NOT NULL,
                synergy_type TEXT NOT NULL,
                strength REAL DEFAULT 0.5,
                explanation TEXT
            )
        """)

        # Tagger runs: audit trail for tagging operations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tagger_runs (
                run_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tagger_version TEXT,
                rules_version TEXT,
                card_scope TEXT,
                notes TEXT
            )
        """)

        # Tag evidence: source of truth for why tags exist (phase 2.5)
        # Stores evidence for every tag assignment to enable debugging and observability.
        # card_tags is the cache/summary; this table explains the reasoning.
        #
        # NOTE: run_id is optional (can be NULL). When provided, it references tagger_runs,
        # but we allow NULL for ad-hoc tagging operations that don't start a formal run.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tag_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                rule_id TEXT,
                evidence_text TEXT,
                oracle_start INTEGER,
                oracle_end INTEGER,
                face_index INTEGER,
                segment_id TEXT,
                ability_kind TEXT,
                text_role TEXT,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'manual',
                run_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(tag_id) REFERENCES tags(id)
            )
        """)

        # Index for evidence queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tag_evidence_card_tag
            ON tag_evidence(card_id, tag_id)
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tag_evidence_rule_id
            ON tag_evidence(rule_id)
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

    def save_tag(self, name: str, layer: str, description: str = "") -> int:
        """
        Create a tag in the tags table. Safe to call multiple times — uses INSERT OR IGNORE.

        Args:
            name: tag name, e.g. 'Mana_Multiplier'
            layer: 'mechanical' | 'functional' | 'archetype' | 'emotional'
            description: human-readable explanation of the tag

        Returns:
            tag id
        """
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO tags (name, layer, description) VALUES (?, ?, ?)",
            (name, layer, description),
        )
        self.conn.commit()
        cur.execute("SELECT id FROM tags WHERE name = ?", (name,))
        return cur.fetchone()[0]

    def get_tag_id(self, tag_name: str) -> Optional[int]:
        """Look up a tag's id by name (case-insensitive). Returns None if not found."""
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM tags WHERE LOWER(name) = LOWER(?)", (tag_name,))
        row = cur.fetchone()
        return row[0] if row else None

    def tag_card(
        self,
        card_name: str,
        tag_name: str,
        confidence: float = 1.0,
        source: str = "manual",
        note: str = "",
    ) -> bool:
        """
        Tag a card. Returns True if successful, False if tag not found.

        Confidence scale (0.0–1.0):
            1.0 = mechanically certain (oracle text is explicit)
            0.7 = confident (well-known role, clear pattern)
            0.4 = contextual (depends on the deck)
            0.1 = speculative
        """
        tag_id = self.get_tag_id(tag_name)
        if tag_id is None:
            return False
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO card_tags (card_id, tag_id, confidence, source, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (card_name, tag_id, confidence, source, note or ""),
        )
        self.conn.commit()
        return True

    def tag_card_if_higher(
        self,
        card_name: str,
        tag_name: str,
        confidence: float = 1.0,
        source: str = "rule_engine",
        note: str = "",
    ) -> bool:
        """
        Tag a card only when the new confidence is strictly higher than the existing.

        Use this for rule-engine derived tags (functional, archetype) to ensure
        that manual tags (source='manual', confidence=1.0) are never downgraded
        by an automated inference.

        Returns True if the tag was applied or already existed, False if tag not found.
        """
        tag_id = self.get_tag_id(tag_name)
        if tag_id is None:
            return False
        cur = self.conn.cursor()
        # SQLite upsert: insert if absent, update only when new confidence is higher.
        # The CASE expression compares excluded.confidence (the incoming value)
        # against the stored confidence; if the incoming is higher, update all fields.
        cur.execute(
            """
            INSERT INTO card_tags (card_id, tag_id, confidence, source, note)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(card_id, tag_id) DO UPDATE SET
                confidence = CASE
                    WHEN excluded.confidence > card_tags.confidence
                    THEN excluded.confidence
                    ELSE card_tags.confidence
                END,
                source = CASE
                    WHEN excluded.confidence > card_tags.confidence
                    THEN excluded.source
                    ELSE card_tags.source
                END,
                note = CASE
                    WHEN excluded.confidence > card_tags.confidence
                    THEN excluded.note
                    ELSE card_tags.note
                END
            """,
            (card_name, tag_id, confidence, source, note or ""),
        )
        self.conn.commit()
        return True

    def delete_auto_tags(self, card_name: str) -> int:
        """
        Delete all automatically derived tags for a card.

        Removes tags with source 'regex' (from tag_mechanical) and 'rule_engine'
        (from tag_functional_from_rules / tag_archetype_from_rules). Manual tags
        (source='manual') are never touched.

        Use this before re-running the tagging pipeline to avoid accumulating
        stale tags from old rule versions.

        Returns:
            Number of tags deleted.
        """
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM card_tags WHERE card_id = ? AND source IN ('regex', 'rule_engine')",
            (card_name,),
        )
        self.conn.commit()
        return cur.rowcount

    def get_card_tags(self, card_name: str, layer: Optional[str] = None) -> List[dict]:
        """
        Get all tags for a card, optionally filtered by layer.

        Returns:
            List of dicts: {name, layer, confidence, source, note}
        """
        cur = self.conn.cursor()
        if layer:
            cur.execute(
                """
                SELECT t.name, t.layer, ct.confidence, ct.source, ct.note
                FROM card_tags ct
                JOIN tags t ON ct.tag_id = t.id
                WHERE LOWER(ct.card_id) = LOWER(?)
                  AND LOWER(t.layer) = LOWER(?)
                ORDER BY ct.confidence DESC
                """,
                (card_name, layer),
            )
        else:
            cur.execute(
                """
                SELECT t.name, t.layer, ct.confidence, ct.source, ct.note
                FROM card_tags ct
                JOIN tags t ON ct.tag_id = t.id
                WHERE LOWER(ct.card_id) = LOWER(?)
                ORDER BY t.layer, ct.confidence DESC
                """,
                (card_name,),
            )
        return [
            {
                "name": row["name"],
                "layer": row["layer"],
                "confidence": row["confidence"],
                "source": row["source"],
                "note": row["note"],
            }
            for row in cur.fetchall()
        ]

    def all_tags(self, layer: Optional[str] = None) -> List[dict]:
        """
        Return all tags in the system, optionally filtered by layer.

        Returns:
            List of dicts: {id, name, layer, description}
        """
        cur = self.conn.cursor()
        if layer:
            cur.execute(
                "SELECT id, name, layer, description FROM tags WHERE LOWER(layer) = LOWER(?) ORDER BY name",
                (layer,),
            )
        else:
            cur.execute("SELECT id, name, layer, description FROM tags ORDER BY layer, name")
        return [
            {"id": row["id"], "name": row["name"], "layer": row["layer"], "description": row["description"]}
            for row in cur.fetchall()
        ]

    def query_cards_by_tag(self, tag_name: str, min_confidence: float = 0.0) -> List[dict]:
        """
        Find all cards tagged with a given tag.

        Args:
            tag_name: tag to search for (case-insensitive)
            min_confidence: only return tags with confidence >= this value

        Returns:
            List of dicts: {card_name, confidence, source, note}
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT ct.card_id, ct.confidence, ct.source, ct.note
            FROM card_tags ct
            JOIN tags t ON ct.tag_id = t.id
            WHERE LOWER(t.name) = LOWER(?)
              AND ct.confidence >= ?
            ORDER BY ct.confidence DESC
            """,
            (tag_name, min_confidence),
        )
        return [
            {
                "card_name": row["card_id"],
                "confidence": row["confidence"],
                "source": row["source"],
                "note": row["note"],
            }
            for row in cur.fetchall()
        ]

    def tag_count_for_deck(
        self, card_names: List[str], layer: Optional[str] = None
    ) -> dict[str, int]:
        """
        Count how many cards in a deck have each tag.

        Args:
            card_names: list of card names in the deck (pass the main deck)
            layer: optional — filter to one layer ('functional', etc.)

        Returns:
            {tag_name: count} sorted by count desc
        """
        if not card_names:
            return {}

        placeholders = ",".join("?" * len(card_names))
        lowered = [n.lower() for n in card_names]

        cur = self.conn.cursor()
        if layer:
            cur.execute(
                f"""
                SELECT t.name, COUNT(*) as count
                FROM card_tags ct
                JOIN tags t ON ct.tag_id = t.id
                WHERE LOWER(ct.card_id) IN ({placeholders})
                  AND LOWER(t.layer) = LOWER(?)
                GROUP BY t.name
                ORDER BY count DESC
                """,
                lowered + [layer],
            )
        else:
            cur.execute(
                f"""
                SELECT t.name, COUNT(*) as count
                FROM card_tags ct
                JOIN tags t ON ct.tag_id = t.id
                WHERE LOWER(ct.card_id) IN ({placeholders})
                GROUP BY t.name
                ORDER BY t.layer, count DESC
                """,
                lowered,
            )
        return {row["name"]: row["count"] for row in cur.fetchall()}

    # ─── Synergy operations (phase 2) ─────────────────────────────────────────

    def add_synergy(
        self,
        card_a: str,
        card_b: str,
        synergy_type: str,
        strength: float = 0.5,
        explanation: str = "",
    ) -> int:
        """
        Add a synergy relationship between two cards.

        Strength scale (0.0–1.0):
            1.0 = core/critical synergy (the combo itself)
            0.7 = strong synergy
            0.5 = moderate synergy
            0.3 = incidental/weak

        Returns:
            synergy edge id
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO synergy_edges (card_a, card_b, synergy_type, strength, explanation)
            VALUES (?, ?, ?, ?, ?)
            """,
            (card_a, card_b, synergy_type, strength, explanation or ""),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_synergies(self, card_name: str, min_strength: float = 0.0) -> List[dict]:
        """
        Get all synergy relationships for a card (as either card_a or card_b).

        Returns:
            List of dicts: {other_card, synergy_type, strength, explanation}
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                CASE WHEN card_a = ? THEN card_b ELSE card_a END AS other_card,
                synergy_type, strength, explanation
            FROM synergy_edges
            WHERE (card_a = ? OR card_b = ?)
              AND strength >= ?
            ORDER BY strength DESC
            """,
            (card_name, card_name, card_name, min_strength),
        )
        return [
            {
                "other_card": row["other_card"],
                "synergy_type": row["synergy_type"],
                "strength": row["strength"],
                "explanation": row["explanation"],
            }
            for row in cur.fetchall()
        ]

    # ─── Tag Evidence (Phase 2.5) ─────────────────────────────────────────────────

    def start_tagger_run(
        self,
        run_id: str,
        tagger_version: str = "unknown",
        rules_version: str = "unknown",
        card_scope: str = "all",
        notes: str = "",
    ) -> bool:
        """
        Begin a tagger run. Call this before emitting evidence for a batch of cards.

        Returns True if successful.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO tagger_runs (run_id, timestamp, tagger_version, rules_version, card_scope, notes)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
            """,
            (run_id, tagger_version, rules_version, card_scope, notes or ""),
        )
        self.conn.commit()
        return True

    def emit_tag_evidence(
        self,
        card_name: str,
        tag_name: str,
        rule_id: str = "",
        evidence_text: str = "",
        oracle_start: Optional[int] = None,
        oracle_end: Optional[int] = None,
        face_index: Optional[int] = None,
        segment_id: str = "",
        ability_kind: str = "",
        text_role: str = "",
        confidence: float = 1.0,
        source: str = "manual",
        run_id: str = "",
    ) -> bool:
        """
        Emit evidence for a tag assignment and update card_tags.

        This is the primary method for recording WHY a tag exists.

        Args:
            card_name: Card name
            tag_name: Tag name (must exist in tags table)
            rule_id: Unique identifier for the rule that produced this tag
            evidence_text: The exact oracle text span that triggered this tag
            oracle_start: Character offset in oracle text (if known)
            oracle_end: Character offset in oracle text (if known)
            face_index: Card face index (0 for front, 1 for back, None for single-face)
            segment_id: Arbitrary segment identifier (e.g., "activated_ability_1")
            ability_kind: "activated", "triggered", "static", "replacement", or ""
            text_role: "cost", "effect", "trigger", or ""
            confidence: 0.0-1.0 scale
            source: "manual", "regex", "rule_engine"
            run_id: Tagger run ID for tracking

        Returns True if successful, False if tag not found.
        """
        tag_id = self.get_tag_id(tag_name)
        if tag_id is None:
            return False

        cur = self.conn.cursor()

        # Emit evidence
        cur.execute(
            """
            INSERT INTO tag_evidence (
                card_id, tag_id, rule_id, evidence_text,
                oracle_start, oracle_end, face_index, segment_id,
                ability_kind, text_role, confidence, source, run_id,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                card_name, tag_id, rule_id or "", evidence_text or "",
                oracle_start, oracle_end, face_index, segment_id or "",
                ability_kind or "", text_role or "", confidence, source, run_id or None,
            ),
        )

        # Update card_tags as summary cache
        # Use tag_card_if_higher to respect manual tag precedence
        self.tag_card_if_higher(
            card_name=card_name,
            tag_name=tag_name,
            confidence=confidence,
            source=source,
            note=f"rule_id={rule_id}" if rule_id else "",
        )

        self.conn.commit()
        return True

    def get_tag_evidence(self, card_name: str, tag_name: str = "") -> List[dict]:
        """
        Retrieve evidence for tags on a card.

        Args:
            card_name: Card name
            tag_name: Optional filter to specific tag

        Returns:
            List of dicts with evidence details
        """
        cur = self.conn.cursor()
        query = """
            SELECT
                te.id, te.card_id, t.name as tag_name, t.layer,
                te.rule_id, te.evidence_text, te.oracle_start, te.oracle_end,
                te.face_index, te.segment_id, te.ability_kind, te.text_role,
                te.confidence, te.source, te.run_id, te.created_at
            FROM tag_evidence te
            JOIN tags t ON te.tag_id = t.id
            WHERE LOWER(te.card_id) = LOWER(?)
        """
        params = [card_name]

        if tag_name:
            query += " AND LOWER(t.name) = LOWER(?)"
            params.append(tag_name)

        query += " ORDER BY te.created_at DESC"

        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

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
