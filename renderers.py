"""
renderers.py — Pure rendering functions for MTG Terminal.

All rendering functions return strings or lists of strings.
They do not print directly — that's the caller's job.
This makes them testable and reusable.
"""

import textwrap
from typing import List, Dict, Any, Optional


def render_card_preview(
    card: Dict[str, Any],
    width: int = 40,
) -> List[str]:
    """Render card preview (compact format for right panel).

    Returns a list of strings, one per line. Caller handles printing/clearing.

    Args:
        card: Card dict from Scryfall
        width: Max line width (default 40 chars for side panel)

    Returns:
        List of formatted strings ready to print.
    """
    lines = []

    # Card name (bold in caller's code)
    name = card.get("name", "Unknown")
    lines.append(name)

    # Mana cost and value
    mana = card.get("mana_cost", "")
    cmc = card.get("cmc", 0)
    if mana or cmc:
        mana_str = f"{mana} (CMC: {int(cmc)})" if cmc else mana
        lines.append(mana_str.strip())

    # Type line
    type_line = card.get("type_line", "")
    if type_line:
        lines.append(type_line)

    lines.append("")  # Blank line

    # Oracle text (wrapped)
    oracle = card.get("oracle_text", "")
    if oracle:
        wrapped = textwrap.wrap(oracle, width=width - 1)
        lines.extend(wrapped)
    else:
        lines.append("(no text)")

    lines.append("")  # Blank line

    # Color identity
    colors = card.get("colors", [])
    color_id = card.get("color_identity", [])
    if color_id:
        color_map = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green"}
        color_names = [color_map.get(c, c) for c in color_id]
        lines.append(f"Color ID: {', '.join(color_names)}")

    # Rarity
    rarity = card.get("rarity", "")
    if rarity:
        lines.append(f"Rarity: {rarity.capitalize()}")

    # Set name
    set_name = card.get("set_name", "")
    if set_name:
        lines.append(f"Set: {set_name}")

    # Power/Toughness or Loyalty
    power = card.get("power", "")
    toughness = card.get("toughness", "")
    loyalty = card.get("loyalty", "")

    if power and toughness:
        lines.append(f"P/T: {power}/{toughness}")
    elif loyalty:
        lines.append(f"Loyalty: {loyalty}")

    return lines


def render_dual_panel(
    left_title: str,
    left_items: List[str],
    left_selected: int,
    right_title: str,
    right_lines: List[str],
    breadcrumb_str: str = "",
    status_str: str = "",
    width: int = 100,
    height: int = 20,
) -> str:
    """Render two-panel layout side-by-side.

    Args:
        left_title: Title for left panel
        left_items: List of item names (one per line, selectable)
        left_selected: Index of selected item (0-based)
        right_title: Title for right panel
        right_lines: List of strings to display on right (pre-formatted)
        breadcrumb_str: Optional breadcrumb text (already formatted)
        status_str: Optional status line (already formatted)
        width: Total terminal width
        height: Total terminal height

    Returns:
        Complete screen as a single string, ready to print.
    """
    # Calculate panel widths
    # Format: [left panel (30%)] | [right panel (rest)]
    left_width = max(20, width // 3)  # At least 20 chars for names
    separator = " │ "
    right_width = max(30, width - left_width - len(separator))

    output = []

    # Breadcrumb at top
    if breadcrumb_str:
        output.append(breadcrumb_str)
        output.append("")

    # Panel headers
    left_header = f"┌ {left_title}".ljust(left_width)
    right_header = f"┌ {right_title}"
    header_line = left_header + separator + right_header
    output.append(header_line[:width])

    # Calculate content height (account for headers, status, spacing)
    content_height = max(5, height - 4)  # Leave room for headers, blank lines, status

    # Render content rows
    for row in range(content_height):
        # Left panel: list item
        left_line = ""
        if row < len(left_items):
            item = left_items[row]
            # Highlight selected item
            if row == left_selected:
                item_str = f"> {item}"
            else:
                item_str = f"  {item}"
            left_line = item_str[: left_width - 1].ljust(left_width - 1)
        else:
            left_line = " " * (left_width - 1)

        # Right panel: preview content
        right_line = ""
        if row < len(right_lines):
            right_line = right_lines[row][: right_width - 1]

        # Combine
        line = left_line + " │ " + right_line.ljust(right_width - 1)
        output.append(line[: width - 1])

    # Bottom separator
    output.append("└" + "─" * (width - 2) + "┘")

    # Status line
    if status_str:
        output.append(status_str)

    return "\n".join(output)


def render_single_panel(
    title: str,
    items: List[str],
    selected: int,
    breadcrumb_str: str = "",
    status_str: str = "",
    width: int = 80,
    height: int = 20,
) -> str:
    """Fallback: render single-panel list (for narrow terminals).

    Args:
        title: Panel title
        items: List of selectable items
        selected: Index of selected item
        breadcrumb_str: Optional breadcrumb
        status_str: Optional status line
        width: Terminal width
        height: Terminal height

    Returns:
        Complete screen as a single string.
    """
    output = []

    if breadcrumb_str:
        output.append(breadcrumb_str)
        output.append("")

    # Header
    output.append(f"┌ {title}".ljust(width - 1))

    # Content
    content_height = max(3, height - 4)
    for i, item in enumerate(items[:content_height]):
        if i == selected:
            line = f"> {item}"
        else:
            line = f"  {item}"
        output.append(line[: width - 1].ljust(width - 1))

    # Filler
    for _ in range(content_height - len(items)):
        output.append(" " * (width - 1))

    # Bottom
    output.append("└" + "─" * (width - 2) + "┘")

    if status_str:
        output.append(status_str)

    return "\n".join(output)
