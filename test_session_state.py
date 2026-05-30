"""
test_session_state.py — Unit tests for SessionState.

Tests pin/unpin, history cap and dedup, and ordering.
"""

from datetime import datetime
from ui import SessionState, SearchHistoryEntry


def test_pin_card_stores_full_dict():
    state = SessionState()
    card = {"id": "abc123", "name": "Lightning Bolt", "mana_cost": "{R}"}

    state.pin_card(card)

    assert state.is_pinned(card)
    pinned = state.get_pinned_cards()
    assert len(pinned) == 1
    assert pinned[0]["name"] == "Lightning Bolt"


def test_pin_card_with_oracle_id():
    state = SessionState()
    card = {"oracle_id": "xyz789", "name": "Counterspell", "mana_cost": "{UU}"}

    state.pin_card(card)

    assert state.is_pinned(card)
    pinned = state.get_pinned_cards()
    assert len(pinned) == 1
    assert pinned[0]["name"] == "Counterspell"


def test_pin_card_fallback_to_name():
    state = SessionState()
    card = {"name": "Black Lotus"}

    state.pin_card(card)

    assert state.is_pinned(card)
    pinned = state.get_pinned_cards()
    assert len(pinned) == 1
    assert pinned[0]["name"] == "Black Lotus"


def test_unpin_card_by_id():
    state = SessionState()
    card = {"id": "abc123", "name": "Lightning Bolt"}

    state.pin_card(card)
    assert state.is_pinned(card)

    state.unpin_card("abc123")
    assert not state.is_pinned(card)


def test_unpin_card_by_name():
    state = SessionState()
    card = {"name": "Black Lotus"}

    state.pin_card(card)
    assert state.is_pinned(card)

    state.unpin_card("Black Lotus")
    assert not state.is_pinned(card)


def test_is_pinned_multiple_cards():
    state = SessionState()
    card1 = {"id": "1", "name": "Card A"}
    card2 = {"id": "2", "name": "Card B"}

    state.pin_card(card1)

    assert state.is_pinned(card1)
    assert not state.is_pinned(card2)


def test_get_pinned_cards_insertion_order():
    state = SessionState()
    card1 = {"id": "1", "name": "First"}
    card2 = {"id": "2", "name": "Second"}
    card3 = {"id": "3", "name": "Third"}

    state.pin_card(card1)
    state.pin_card(card2)
    state.pin_card(card3)

    pinned = state.get_pinned_cards()
    assert [c["name"] for c in pinned] == ["First", "Second", "Third"]


def test_add_search_history_records_entry():
    state = SessionState()
    cards = [{"name": "Card1"}, {"name": "Card2"}]

    state.add_search_history("test query", cards)

    history = state.get_history()
    assert len(history) == 1
    assert history[0].query == "test query"
    assert len(history[0].results) == 2


def test_add_search_history_caps_results_at_10():
    state = SessionState()
    cards = [{"name": f"Card{i}"} for i in range(20)]

    state.add_search_history("big search", cards)

    history = state.get_history()
    assert len(history[0].results) == 10


def test_add_search_history_deduplicates_consecutive():
    state = SessionState()
    cards1 = [{"name": "Result1"}]
    cards2 = [{"name": "Result2"}]

    state.add_search_history("query", cards1)
    state.add_search_history("query", cards2)  # Same query

    history = state.get_history()
    assert len(history) == 1
    # Should be replaced, so we get the second result
    assert history[0].results[0]["name"] == "Result2"


def test_add_search_history_allows_different_queries():
    state = SessionState()

    state.add_search_history("query1", [{"name": "R1"}])
    state.add_search_history("query2", [{"name": "R2"}])
    state.add_search_history("query1", [{"name": "R1b"}])  # Different from query2

    history = state.get_history()
    assert len(history) == 3


def test_add_search_history_caps_at_max_entries():
    state = SessionState()

    for i in range(60):
        state.add_search_history(f"query{i}", [{"name": f"Result{i}"}], max_entries=50)

    history = state.get_history()
    assert len(history) == 50


def test_get_history_returns_newest_first():
    state = SessionState()

    state.add_search_history("first", [])
    state.add_search_history("second", [])
    state.add_search_history("third", [])

    history = state.get_history()
    assert [e.query for e in history] == ["third", "second", "first"]


def test_pinned_cards_and_history_independent():
    state = SessionState()

    state.pin_card({"id": "1", "name": "Pinned Card"})
    state.add_search_history("query", [{"name": "Search Result"}])

    assert len(state.get_pinned_cards()) == 1
    assert len(state.get_history()) == 1

    state.unpin_card("1")

    assert len(state.get_pinned_cards()) == 0
    assert len(state.get_history()) == 1


if __name__ == "__main__":
    # Run all tests
    test_pin_card_stores_full_dict()
    test_pin_card_with_oracle_id()
    test_pin_card_fallback_to_name()
    test_unpin_card_by_id()
    test_unpin_card_by_name()
    test_is_pinned_multiple_cards()
    test_get_pinned_cards_insertion_order()
    test_add_search_history_records_entry()
    test_add_search_history_caps_results_at_10()
    test_add_search_history_deduplicates_consecutive()
    test_add_search_history_allows_different_queries()
    test_add_search_history_caps_at_max_entries()
    test_get_history_returns_newest_first()
    test_pinned_cards_and_history_independent()
    print("✓ All tests passed!")
