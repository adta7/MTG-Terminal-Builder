"""
test_analyzer.py — Tests for deck analysis.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.models import Card, Deck, DeckCard
from mtgdeck.analyzer import analyze_deck, filter_deck, _matches_cmc, _matches_color


def test_matches_cmc():
    """Test CMC matching logic."""
    assert _matches_cmc(3, "3") == True
    assert _matches_cmc(3, ">=3") == True
    assert _matches_cmc(3, ">=4") == False
    assert _matches_cmc(3, "<4") == True
    assert _matches_cmc(0, "0") == True   # Fixed: "colorless" is not a CMC condition


def test_matches_color():
    """Test color matching logic."""
    assert _matches_color(["U"], "u") == True
    assert _matches_color(["U", "B"], "multicolor") == True
    assert _matches_color([], "colorless") == True
    assert _matches_color(["U"], "colorless") == False


def test_analyze_simple_deck():
    """Test analyzing a simple deck."""
    deck = Deck(
        name="Test Deck",
        cards=[
            DeckCard(name="Island", count=30),
            DeckCard(name="Plains", count=25),
            DeckCard(name="Counterspell", count=20),  # Would need cmc in DB
            DeckCard(name="Lightning Bolt", count=25),
        ],
        commander=None,
    )

    # This test is limited because we don't have a real DB
    # But we can at least verify the structure
    assert deck.main_deck_count() == 100


def test_deck_card_filtering():
    """Test that filtering works structurally."""
    deck = Deck(
        name="Test",
        cards=[
            DeckCard(name="Island", count=10),
            DeckCard(name="Lightning Bolt", count=5),
        ],
    )

    # Just verify the deck structure is correct
    assert len(deck.cards) == 2
    assert deck.main_deck_count() == 15
