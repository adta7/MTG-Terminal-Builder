"""
ui.py — Centralized UI helpers for MTG Terminal

Provides clean rendering, screen management, and interactive components
for the terminal UI.
"""

import os
import sys
import shutil
import tty
import termios
import select
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


# ─── Menu Items ──────────────────────────────────────────────────────────────

@dataclass
class MenuItem:
    """A menu item with key, label, and optional description."""

    key: str
    label: str
    description: str = ""
    enabled: bool = True

    def __str__(self) -> str:
        return self.label


# ─── Session State ───────────────────────────────────────────────────────────

@dataclass
class SearchHistoryEntry:
    """A single search history entry."""

    query: str
    timestamp: datetime
    results: List[Dict[str, Any]]  # snapshot of top N results


@dataclass
class SessionState:
    """Shared session state across the app (in-memory, not persisted yet)."""

    pinned_cards: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Pinned cards, keyed by stable card ID: {id: card_dict}."""

    recent_searches: List[str] = field(default_factory=list)
    """Recent search queries (for future search history)."""

    active_deck: Optional[str] = None
    """Currently active deck name (if any)."""

    history: List[SearchHistoryEntry] = field(default_factory=list)
    """Search history entries (session-local, not persisted)."""

    def _card_key(self, card_data: Dict[str, Any]) -> str:
        return card_data.get("id") or card_data.get("oracle_id") or card_data.get("name", "Unknown")

    def pin_card(self, card_data: Dict[str, Any]):
        """Add a card to pinned dict with full card data."""
        key = self._card_key(card_data)
        self.pinned_cards[key] = card_data

    def unpin_card(self, card_key: str):
        """Remove a card from pinned dict by key."""
        self.pinned_cards.pop(card_key, None)

    def is_pinned(self, card_data: Dict[str, Any]) -> bool:
        """Check if a card is pinned."""
        key = self._card_key(card_data)
        return key in self.pinned_cards

    def get_pinned_cards(self) -> List[Dict[str, Any]]:
        """Return list of pinned cards in insertion order."""
        return list(self.pinned_cards.values())

    def add_search_history(self, query: str, results: List[Dict[str, Any]], max_entries: int = 50):
        """Record a search in history, capped at max_entries. Dedup consecutive identical queries."""
        entry = SearchHistoryEntry(query=query, timestamp=datetime.now(), results=results[:10])
        # Deduplicate consecutive identical queries
        if self.history and self.history[-1].query == query:
            self.history[-1] = entry
        else:
            self.history.append(entry)
        self.history = self.history[-max_entries:]

    def get_history(self) -> List[SearchHistoryEntry]:
        """Return search history in reverse order (newest first)."""
        return list(reversed(self.history))

    def add_recent_search(self, query: str):
        """Add to recent searches (max 10)."""
        if query in self.recent_searches:
            self.recent_searches.remove(query)
        self.recent_searches.insert(0, query)
        if len(self.recent_searches) > 10:
            self.recent_searches = self.recent_searches[:10]

# ─── Screen State ─────────────────────────────────────────────────────────────

class BreadcrumbPath:
    """Manages navigation breadcrumb context."""

    def __init__(self, *path):
        self.path = list(path)

    def push(self, label: str):
        """Add a breadcrumb level."""
        self.path.append(label)

    def pop(self):
        """Remove the last breadcrumb level."""
        if self.path:
            self.path.pop()

    def render(self) -> str:
        """Return formatted breadcrumb string."""
        if not self.path:
            return ""
        return " > ".join(self.path)

    def copy(self) -> "BreadcrumbPath":
        """Return a copy of this breadcrumb."""
        return BreadcrumbPath(*self.path)


# ─── Screen Rendering ─────────────────────────────────────────────────────────

def term_width() -> int:
    """Get current terminal width."""
    return shutil.get_terminal_size().columns


def term_height() -> int:
    """Get current terminal height."""
    return shutil.get_terminal_size().lines


def clear_screen():
    """Clear the terminal screen cleanly."""
    os.system("clear" if os.name != "nt" else "cls")


def restore_terminal():
    """Restore terminal to normal (non-raw) state.

    Call this if the terminal gets stuck in raw mode due to an error.
    Uses 'stty sane' which is the universal terminal restoration command.
    """
    try:
        import subprocess
        subprocess.run(["stty", "sane"], check=False)
    except Exception:
        pass  # Silently ignore errors during restoration


def render_breadcrumb(path: BreadcrumbPath) -> str:
    """Render breadcrumb as a styled string."""
    breadcrumb_text = path.render()
    if breadcrumb_text:
        return f"[dim cyan]{breadcrumb_text}[/dim cyan]"
    return ""


def render_status_line(keys: List[str]) -> str:
    """Render a status line with available keybindings.

    Args:
        keys: List of keybind descriptions, e.g. ["↑↓ Navigate", "Space Select"]

    Returns:
        Formatted status line string.
    """
    return " | ".join(keys)


def render_screen(
    header: Optional[str] = None,
    body: Optional[str] = None,
    footer: Optional[str] = None,
    breadcrumb: Optional[BreadcrumbPath] = None,
):
    """Clear screen and render a full page layout.

    Args:
        header: Title/header text (optional, rendered as bold cyan)
        body: Main content (rich markup supported)
        footer: Footer/status line (optional, rendered as dim)
        breadcrumb: BreadcrumbPath object (optional, rendered at top)
    """
    clear_screen()

    # Render breadcrumb if provided
    if breadcrumb and breadcrumb.path:
        console.print(render_breadcrumb(breadcrumb))
        console.print()

    # Render header
    if header:
        console.print(f"[bold cyan]{header}[/bold cyan]")
        console.print("[dim cyan]" + "─" * min(term_width() - 2, 78) + "[/dim cyan]")
        console.print()

    # Render body
    if body:
        console.print(body)

    # Render footer with padding
    if footer:
        console.print()
        console.print(f"[dim]{footer}[/dim]")


# ─── Interactive Menu ────────────────────────────────────────────────────────

def getch() -> str:
    """Read a single keypress in raw mode.

    Handles arrow keys and ESC. Returns single character or special key string.
    Uses select() to wait for first byte, then reads remaining bytes in blocking mode.
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)

        # Wait for first byte with select (10 second timeout to avoid hanging)
        if not select.select([sys.stdin], [], [], 10)[0]:
            return None

        ch = sys.stdin.buffer.read(1)
        if ch == b'\x03':
            raise KeyboardInterrupt

        if ch == b'\x1b':
            # Read the next two bytes without timeout (escape sequences complete eventually)
            ch2 = sys.stdin.buffer.read(1)
            if ch2 == b'[':
                ch3 = sys.stdin.buffer.read(1)
                if ch3 == b'A':
                    return 'UP'
                if ch3 == b'B':
                    return 'DOWN'
                if ch3 == b'C':
                    return 'RIGHT'
                if ch3 == b'D':
                    return 'LEFT'
            return 'ESC'

        return ch.decode('utf-8', errors='replace')

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def ask_choice_interactive(
    title: str,
    options: List,  # Can be strings or MenuItem objects
    labels: Optional[List[str]] = None,
    breadcrumb: Optional[BreadcrumbPath] = None,
    cancellable: bool = True,
) -> Optional:
    """Display an interactive menu with arrow key navigation + number select.

    Supports both string options and MenuItem objects.

    Supports:
    - Arrow keys (↑/↓) to move selection
    - Enter to confirm selection
    - Number keys (1-N) to quick-select an option
    - ESC or q to cancel (if cancellable=True)

    Args:
        title: Menu title
        options: List of option values (strings or MenuItem objects)
        labels: Optional list of display labels (for string options only)
        breadcrumb: Optional BreadcrumbPath for context
        cancellable: If True, ESC returns None; if False, ESC beeps and re-prompts

    Returns:
        For MenuItem objects: the MenuItem object that was selected, or None if cancelled
        For string options: the 0-based index of selected option, or None if cancelled
    """
    if not options:
        return None

    # Determine if we're using MenuItem objects or strings
    use_menu_items = options and isinstance(options[0], MenuItem)

    if not use_menu_items and labels is None:
        labels = options

    selected_index = 0

    while True:
        # Clear and render the menu
        clear_screen()

        # Breadcrumb
        if breadcrumb and breadcrumb.path:
            console.print(render_breadcrumb(breadcrumb))
            console.print()

        # Header
        console.print(f"[bold cyan]{title}[/bold cyan]")
        console.print("[dim cyan]" + "─" * min(term_width() - 2, 78) + "[/dim cyan]")
        console.print()

        # Options with highlight
        for i, opt in enumerate(options):
            # Get the label to display
            if use_menu_items:
                menu_item = opt
                display_label = menu_item.label
                is_enabled = menu_item.enabled
            else:
                display_label = labels[i] if labels else opt
                is_enabled = True

            # Skip disabled items when rendering
            if not is_enabled:
                console.print(f"  {i+1}  [dim]{display_label}[/dim]")
            elif i == selected_index:
                # Highlight selected option
                console.print(f"[reverse]> {i+1}  {display_label}[/reverse]")
            else:
                console.print(f"  {i+1}  {display_label}")

        console.print()

        # Show description of selected item if available
        if use_menu_items and selected_index < len(options):
            menu_item = options[selected_index]
            if menu_item.description:
                console.print(f"[dim]{menu_item.description}[/dim]")
                console.print()

        # Status line
        status = render_status_line([
            "[bold cyan]↑↓[/bold cyan] Navigate",
            "[bold cyan]Enter[/bold cyan] Select",
            "[bold cyan]1-9[/bold cyan] Quick",
            "[dim cyan]q/ESC[/dim cyan] Back" if cancellable else "",
        ])
        # Filter out empty strings
        status = " | ".join([s for s in status.split(" | ") if s])
        console.print(f"[dim]{status}[/dim]")

        # Wait for keypress
        key = getch()

        # Handle keys
        if key == 'UP':
            # Move up, skip disabled items
            selected_index = (selected_index - 1) % len(options)
            while use_menu_items and not options[selected_index].enabled:
                selected_index = (selected_index - 1) % len(options)

        elif key == 'DOWN':
            # Move down, skip disabled items
            selected_index = (selected_index + 1) % len(options)
            while use_menu_items and not options[selected_index].enabled:
                selected_index = (selected_index + 1) % len(options)

        elif key == '\r':  # Enter (not spacebar for menus)
            # Check if selected item is enabled
            if use_menu_items and not options[selected_index].enabled:
                sys.stdout.write('\a')  # Beep
                sys.stdout.flush()
            else:
                # Return the selected item
                if use_menu_items:
                    return options[selected_index]
                else:
                    return selected_index

        elif key == 'ESC' or key == 'q':
            if cancellable:
                return None
            # Else beep and continue
            sys.stdout.write('\a')
            sys.stdout.flush()

        elif key.isdigit():
            num = int(key)
            if 1 <= num <= len(options):
                selected_index = num - 1
                # Auto-select if enabled
                if not use_menu_items or options[selected_index].enabled:
                    if use_menu_items:
                        return options[selected_index]
                    else:
                        return selected_index
            # Invalid number, ignore


# ─── Session History ─────────────────────────────────────────────────────────

@dataclass
class HistoryEntry:
    """A single entry in the session history."""

    timestamp: datetime
    title: str
    entry_type: str  # "card", "deck", "analysis", "comparison", etc.
    content: str  # Rich-formatted content
    metadata: Dict[str, Any]  # Extra data (card name, deck name, etc.)

    def short_label(self) -> str:
        """Return a short label for this history entry."""
        label = self.metadata.get("label", self.title)
        return f"[{self.entry_type}] {label}"


class SessionHistory:
    """Manages session history for referencing previous views."""

    def __init__(self):
        self.entries: List[HistoryEntry] = []

    def add(
        self,
        title: str,
        entry_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a new history entry.

        Args:
            title: Display name for this entry
            entry_type: Category (card, deck, analysis, comparison, etc.)
            content: Rich-formatted content to store
            metadata: Optional extra data
        """
        entry = HistoryEntry(
            timestamp=datetime.now(),
            title=title,
            entry_type=entry_type,
            content=content,
            metadata=metadata or {},
        )
        self.entries.append(entry)

    def list(self) -> List[HistoryEntry]:
        """Return all history entries in reverse order (most recent first)."""
        return list(reversed(self.entries))

    def export_markdown(self, filepath: str):
        """Export session history to a markdown file."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w") as f:
            f.write(f"# Session History — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for entry in self.entries:
                time_str = entry.timestamp.strftime("%H:%M:%S")
                f.write(f"## {time_str} — {entry.short_label()}\n\n")
                # Strip Rich markup for markdown export
                f.write(f"{entry.content}\n\n")
                f.write("---\n\n")

    def clear(self):
        """Clear all history."""
        self.entries = []


# ─── Global Session State ────────────────────────────────────────────────────

# These are initialized once at app start and persist across screens
_current_breadcrumb = BreadcrumbPath("MTG Pipeline")
_session_history = SessionHistory()


def get_breadcrumb() -> BreadcrumbPath:
    """Get the current breadcrumb path."""
    return _current_breadcrumb


def reset_breadcrumb():
    """Reset breadcrumb to root."""
    global _current_breadcrumb
    _current_breadcrumb = BreadcrumbPath("MTG Pipeline")


def get_session_history() -> SessionHistory:
    """Get the session history manager."""
    return _session_history
