"""
pinned_view.py — Interactive view and management of pinned cards.

Displays pinned cards in a dual-panel layout with full card previews.
"""

import shutil
from typing import Optional

from ui import BreadcrumbPath, clear_screen, getch, SessionState, restore_terminal
from renderers import render_card_preview, render_dual_panel, render_single_panel


def run_pinned_cards_view(session_state: SessionState) -> None:
    """Display and manage pinned cards from the session.

    Users:
    - ↑↓ arrow keys to navigate pinned cards
    - u to unpin selected card
    - q or ESC to return to menu

    Args:
        session_state: Session state containing pinned cards
    """
    try:
        breadcrumb = BreadcrumbPath("MTG Pipeline", "Pinned Cards")
        width = shutil.get_terminal_size().columns
        height = shutil.get_terminal_size().lines

        selected_index = 0

        while True:
            clear_screen()

            # Breadcrumb
            breadcrumb_str = f"[dim cyan]{breadcrumb.render()}[/dim cyan]"
            print(breadcrumb_str)
            print()

            # Get pinned cards
            pinned = session_state.get_pinned_cards()

            if not pinned:
                print("[yellow]No pinned cards yet.[/yellow]")
                print("Pin cards from the search view by pressing 'p'.")
                print()
                print("Press q to return to menu.")
                key = getch()
                if key == 'q' or key == 'ESC':
                    return

            else:
                # Display in dual-panel or single-panel depending on terminal width
                use_dual_panel = width >= 100

                # Extract card names with ★ prefix (all are pinned)
                card_names = [f"★ {c.get('name', 'Unknown')}" for c in pinned]

                # Get preview of selected card
                if selected_index < len(pinned):
                    selected_card = pinned[selected_index]
                    preview_lines = render_card_preview(selected_card, width=30)
                else:
                    preview_lines = ["(No card selected)"]

                status_line = "↑↓ navigate · u unpin · q quit"

                if use_dual_panel:
                    output = render_dual_panel(
                        left_title=f"Pinned Cards ({len(pinned)})",
                        left_items=card_names,
                        left_selected=selected_index,
                        right_title="Preview",
                        right_lines=preview_lines,
                        breadcrumb_str="",
                        status_str=f"[dim]{status_line}[/dim]",
                        width=width,
                        height=height,
                    )
                else:
                    output = render_single_panel(
                        title=f"Pinned Cards ({len(pinned)})",
                        items=card_names,
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
                    selected_index = (selected_index - 1) % len(pinned)

                elif key == 'DOWN':
                    selected_index = (selected_index + 1) % len(pinned)

                elif key == 'u':
                    # Unpin selected card
                    if selected_index < len(pinned):
                        card_to_unpin = pinned[selected_index]
                        card_key = card_to_unpin.get("id") or card_to_unpin.get("oracle_id") or card_to_unpin.get("name", "Unknown")
                        session_state.unpin_card(card_key)
                        # Adjust selection if we just removed the last card
                        if selected_index >= len(session_state.get_pinned_cards()):
                            selected_index = max(0, selected_index - 1)

                elif key == 'q' or key == 'ESC':
                    return

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n\nError in pinned view: {e}")
        import traceback
        traceback.print_exc()
    finally:
        restore_terminal()
