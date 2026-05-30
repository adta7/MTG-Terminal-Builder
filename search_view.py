"""
search_view.py — Interactive card search view.

Combines search logic, renderers, and keyboard input into a cohesive screen.
"""

import sys
import shutil
from typing import Optional, List, Dict, Any

from ui import BreadcrumbPath, clear_screen, getch, SessionState, restore_terminal, render_view_header, render_status_line
from search import search_cards
from renderers import render_card_preview, render_dual_panel, render_single_panel


def run_card_search_view(
    scryfall_db: Dict[str, Any],
    session_state: SessionState,
    prefill_query: str = "",
) -> Optional[Dict[str, Any]]:
    """Run the interactive card search view.

    Users:
    1. First get prompted to enter a search query (or use prefilled)
    2. Then navigate results with arrow keys
    3. Press p to toggle pin
    4. Press / to search again
    5. Press q or ESC to quit

    Args:
        scryfall_db: Scryfall card database
        session_state: Shared session state for pinned cards and recent searches
        prefill_query: Optional pre-filled search query (e.g., from history replay)

    Returns:
        None (returns control to main menu)
    """
    try:
        breadcrumb = BreadcrumbPath("MTG Pipeline", "Card Search")
        width = shutil.get_terminal_size().columns
        height = shutil.get_terminal_size().lines

        # Step 1: Get initial search query
        clear_screen()
        print(render_view_header(breadcrumb))
        print()
        prompt = f"Search for card [{prefill_query}]: " if prefill_query else "Search for card: "
        search_query = input(prompt).strip() or prefill_query

        # Step 2: Execute search
        search_results: List[Dict[str, Any]] = []
        selected_index = 0

        if search_query:
            session_state.add_recent_search(search_query)
            search_results = search_cards(search_query, scryfall_db, limit=50)
            session_state.add_search_history(search_query, search_results)

        # Step 3: Interactive navigation loop
        while True:
            # Render current state
            clear_screen()
            print(render_view_header(breadcrumb))
            print()

            # Determine layout based on terminal width
            use_dual_panel = width >= 100

            if not search_results:
                print("[yellow]No results.[/yellow]")
                print("Press / to search again, or q to quit.")
                key = getch()
                if key == '/' or key == 's':
                    # New search
                    search_query = input("Search for card: ").strip()
                    if search_query:
                        session_state.add_recent_search(search_query)
                        search_results = search_cards(search_query, scryfall_db, limit=50)
                        selected_index = 0
                elif key == 'q' or key == 'ESC':
                    return None
                continue

            # Render dual or single panel
            if use_dual_panel:
                # Dual-panel mode
                # Add ★ marker for pinned cards
                card_names = [
                    f"★ {c.get('name', 'Unknown')}" if session_state.is_pinned(c) else c.get("name", "Unknown")
                    for c in search_results
                ]

                if search_results and selected_index < len(search_results):
                    selected_card = search_results[selected_index]
                    preview_lines = render_card_preview(selected_card, width=30)
                else:
                    preview_lines = ["(No card selected)"]

                status = render_status_line("↑↓ navigate", "p pin", "/ search", "ESC back")

                output = render_dual_panel(
                    left_title=f"Search Results ({len(search_results)})",
                    left_items=card_names,
                    left_selected=selected_index if search_results else -1,
                    right_title="Preview",
                    right_lines=preview_lines,
                    breadcrumb_str="",
                    status_str=f"[dim]{status}[/dim]",
                    width=width,
                    height=height,
                )
                print(output)

            else:
                # Single-panel fallback for narrow terminals
                # Add ★ marker for pinned cards
                card_names = [
                    f"★ {c.get('name', 'Unknown')}" if session_state.is_pinned(c) else c.get("name", "Unknown")
                    for c in search_results
                ]
                status = render_status_line("↑↓ navigate", "p pin", "/ search", "ESC back")

                output = render_single_panel(
                    title=f"Search Results ({len(search_results)})",
                    items=card_names,
                    selected=selected_index if search_results else -1,
                    breadcrumb_str="",
                    status_str=f"[dim]{status}[/dim]",
                    width=width,
                    height=height,
                )
                print(output)

            # Get user input
            key = getch()

            if key == 'UP':
                if search_results:
                    selected_index = (selected_index - 1) % len(search_results)

            elif key == 'DOWN':
                if search_results:
                    selected_index = (selected_index + 1) % len(search_results)

            elif key == 'p':
                # Toggle pin on selected card
                if search_results and selected_index < len(search_results):
                    selected_card = search_results[selected_index]
                    if session_state.is_pinned(selected_card):
                        key = selected_card.get("id") or selected_card.get("oracle_id") or selected_card.get("name", "Unknown")
                        session_state.unpin_card(key)
                    else:
                        session_state.pin_card(selected_card)

            elif key == '/':
                # Start a new search
                search_query = input("Search for card: ").strip()
                if search_query:
                    session_state.add_recent_search(search_query)
                    search_results = search_cards(search_query, scryfall_db, limit=50)
                    session_state.add_search_history(search_query, search_results)
                    selected_index = 0
                else:
                    search_results = []

            elif key == 'q' or key == 'ESC':
                # Go back
                return None

        return None

    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        return None
    except Exception as e:
        print(f"\n\nError in search view: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Always restore terminal, even if something goes wrong
        restore_terminal()
