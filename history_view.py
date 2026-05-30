"""
history_view.py — Interactive view of search history with replay capability.

Shows past search queries and lets users replay them or review results.
"""

import shutil
from typing import Dict, Any, List

from ui import BreadcrumbPath, clear_screen, getch, SessionState, restore_terminal
from renderers import render_dual_panel, render_single_panel
from search_view import run_card_search_view


def run_history_view(scryfall_db: Dict[str, Any], session_state: SessionState) -> None:
    """Display and replay search history.

    Users:
    - ↑↓ arrow keys to navigate history entries
    - Enter to replay the selected search
    - q or ESC to return to menu

    Args:
        scryfall_db: Scryfall card database for replayed searches
        session_state: Session state containing search history
    """
    try:
        breadcrumb = BreadcrumbPath("MTG Pipeline", "Search History")
        width = shutil.get_terminal_size().columns
        height = shutil.get_terminal_size().lines

        selected_index = 0

        while True:
            clear_screen()

            # Breadcrumb
            breadcrumb_str = f"[dim cyan]{breadcrumb.render()}[/dim cyan]"
            print(breadcrumb_str)
            print()

            # Get history (newest first)
            history = session_state.get_history()

            if not history:
                print("[yellow]No search history yet.[/yellow]")
                print("Search for cards to build history.")
                print()
                print("Press q to return to menu.")
                key = getch()
                if key == 'q' or key == 'ESC':
                    return

            else:
                # Display in dual-panel or single-panel depending on terminal width
                use_dual_panel = width >= 100

                # Left panel: search queries with result counts
                history_items = [
                    f"{entry.query} ({len(entry.results)} results)"
                    for entry in history
                ]

                # Right panel: top results from selected search
                if selected_index < len(history):
                    selected_entry = history[selected_index]
                    result_lines = []
                    for i, card in enumerate(selected_entry.results[:5], 1):
                        card_name = card.get("name", "Unknown")
                        result_lines.append(f"{i}. {card_name}")
                    if not result_lines:
                        result_lines = ["(No results)"]
                else:
                    result_lines = ["(No entry selected)"]

                status_line = "↑↓ navigate · Enter replay · q quit"

                if use_dual_panel:
                    output = render_dual_panel(
                        left_title=f"Search History ({len(history)})",
                        left_items=history_items,
                        left_selected=selected_index,
                        right_title="Top Results",
                        right_lines=result_lines,
                        breadcrumb_str="",
                        status_str=f"[dim]{status_line}[/dim]",
                        width=width,
                        height=height,
                    )
                else:
                    output = render_single_panel(
                        title=f"Search History ({len(history)})",
                        items=history_items,
                        selected=selected_index,
                        breadcrumb_str="",
                        status_str=f"[dim]{status_line}[/dim]",
                        width=width,
                        height=height,
                    )

                print(output)

                # Get user input
                key = getch()

                if key == 'UP':
                    selected_index = (selected_index - 1) % len(history)

                elif key == 'DOWN':
                    selected_index = (selected_index + 1) % len(history)

                elif key == '\r':  # Enter
                    # Replay the selected search
                    if selected_index < len(history):
                        entry = history[selected_index]
                        run_card_search_view(scryfall_db, session_state, prefill_query=entry.query)
                        # After returning from search, stay in history view
                        selected_index = 0  # Reset selection to top

                elif key == 'q' or key == 'ESC':
                    return

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n\nError in history view: {e}")
        import traceback
        traceback.print_exc()
    finally:
        restore_terminal()
