"""
pinned_view.py — View and manage pinned cards.
"""

from typing import Dict, Any

from ui import BreadcrumbPath, clear_screen, getch, SessionState
from renderers import render_card_preview


def run_pinned_cards_view(session_state: SessionState) -> None:
    """Display and manage pinned cards from the session.

    Args:
        session_state: Session state containing pinned cards
    """
    breadcrumb = BreadcrumbPath("MTG Pipeline", "Pinned Cards")

    while True:
        clear_screen()

        # Breadcrumb
        breadcrumb_str = f"[dim cyan]{breadcrumb.render()}[/dim cyan]"
        print(breadcrumb_str)
        print()

        # Get pinned cards
        pinned = sorted(session_state.pinned_cards)

        if not pinned:
            print("[yellow]No pinned cards yet.[/yellow]")
            print("Pin cards from the search view by pressing 'p'.")
            print()
            print("Press q to return to menu.")
            key = getch()
            if key == 'q' or key == 'ESC':
                return

        else:
            # Display pinned cards
            print(f"[bold cyan]Pinned Cards ({len(pinned)})[/bold cyan]")
            print("[dim cyan]" + "─" * 40 + "[/dim cyan]")
            print()

            for i, card_name in enumerate(pinned, 1):
                print(f"  {i}. {card_name}")

            print()
            print("[dim]q to return to menu[/dim]")

            key = getch()
            if key == 'q' or key == 'ESC':
                return
