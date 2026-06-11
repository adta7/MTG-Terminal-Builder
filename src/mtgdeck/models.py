"""
models.py — Core data structures for MTG deckbuilding.

Typed dataclasses for cards, decks, and analysis results.
All other modules import from here to ensure consistency.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Card:
    """A Magic card from Scryfall."""

    name: str
    mana_cost: str
    cmc: int
    type_line: str
    oracle_text: str
    power: Optional[str] = None
    toughness: Optional[str] = None
    loyalty: Optional[str] = None
    colors: list[str] = field(default_factory=list)  # ["U", "B"]
    color_identity: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    rarity: str = ""
    set_name: str = ""
    scryfall_uri: str = ""
    legalities: dict[str, str] = field(default_factory=dict)  # format → "legal"/"banned"/etc.

    def is_basic_land(self) -> bool:
        """Check if this is a basic land (Plains, Island, etc.)."""
        basics = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}
        return self.name in basics

    def color_count(self) -> int:
        """Number of colors in this card's mana cost."""
        return len(self.colors)


@dataclass
class DeckCard:
    """A card entry in a deck (name + count)."""

    name: str
    count: int

    def __hash__(self):
        return hash((self.name.lower(), self.count))


@dataclass
class Deck:
    """A complete Magic deck."""

    name: str
    cards: list[DeckCard] = field(default_factory=list)
    sideboard: list[DeckCard] = field(default_factory=list)
    commander: Optional[str] = None
    created: str = ""  # ISO date: "2026-05-24"
    edited: str = ""
    path: Optional[str] = None  # Path to JSON file if loaded from disk

    def total_cards(self) -> int:
        """Total main deck + sideboard."""
        return sum(c.count for c in self.cards) + sum(c.count for c in self.sideboard)

    def main_deck_count(self) -> int:
        """Total cards in main deck (excluding sideboard)."""
        return sum(c.count for c in self.cards)

    def sideboard_count(self) -> int:
        """Total cards in sideboard."""
        return sum(c.count for c in self.sideboard)


@dataclass
class DeckAnalysis:
    """Results of analyzing a deck structure."""

    deck_name: str
    total_cards: int
    land_count: int
    spell_permanent_count: int  # creatures, enchantments, artifacts, planeswalkers
    spell_nonpermanent_count: int  # instants, sorceries
    avg_mana_value: float
    mana_curve: dict[int, int] = field(default_factory=dict)  # cmc → count
    type_counts: dict[str, int] = field(default_factory=dict)  # type → count
    color_identity: list[str] = field(default_factory=list)
    role_counts: dict[str, int] = field(default_factory=dict)  # role → count (phase 2)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CardScore:
    """Score for how well a card fits a deck."""

    card_name: str
    total_score: float  # 0-100
    role_match: float = 0.0
    gap_fill: float = 0.0
    synergy: float = 0.0
    mana_value: float = 0.0
    preference: float = 0.0
    reason: str = ""
