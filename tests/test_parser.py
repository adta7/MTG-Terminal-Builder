"""
test_parser.py — Tests for decklist parsing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.parser import parse_card_list, _clean_card_name


def test_parse_plain_text():
    """Test parsing plain text format."""
    lines = [
        "4 Lightning Bolt",
        "2 Counterspell",
    ]
    main, sideboard, commander = parse_card_list(lines)
    assert len(main) == 2
    assert main[0].name == "Lightning Bolt"
    assert main[0].count == 4


def test_parse_with_set_codes():
    """Test parsing with set codes stripped."""
    lines = [
        "1x Animate Dead (soc)",
    ]
    main, sideboard, commander = parse_card_list(lines)
    assert len(main) == 1
    assert main[0].name == "Animate Dead"


def test_clean_card_name():
    """Test card name cleaning."""
    assert _clean_card_name("Lightning Bolt (m19)") == "Lightning Bolt"
    assert _clean_card_name("Card [Tag]") == "Card"
    assert _clean_card_name("Swamp 196") == "Swamp"
