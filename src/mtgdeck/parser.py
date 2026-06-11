"""
parser.py — Decklist parsing and card list handling.

Supports multiple formats:
- Plain text: "4 Lightning Bolt"
- Moxfield/Archidekt: "4x Card Name"
- Arena: Section headers + card lists
- MTGO: "SB: 4 Counterspell"
- Archidekt inline tags: "1x Card (set) [Role,Tags]"
"""

import re
from typing import Optional

from .models import DeckCard

# Matches section header lines from Moxfield, Arena, Archidekt, MTGO exports.
_SECTION_RE = re.compile(
    r"^(commander|deck|sideboard|maybeboard|companion|mainboard|main|"
    r"attractions|stickers|schemes|planes)"
    r"(\s*:|\s+\(\d+\))?$",
    re.IGNORECASE,
)
_SKIP_SECTIONS = {"maybeboard", "companion", "attractions", "stickers", "schemes", "planes"}


def _clean_card_name(raw: str) -> Optional[str]:
    """
    Strip metadata from a raw card name string:
      (set_code)        e.g. (m19), (soc), (2x2), (hob)
      [tags]            e.g. [Protection], [Maybeboard{noDeck}{noPrice},Draw]
      trailing number   e.g. trailing collector number like 196 in "Swamp (hob) 196"
    Returns the cleaned card name, or None if the result is empty.
    """
    name = raw
    name = re.sub(r"\s*\([a-z0-9]{2,6}\)\s*", " ", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\[[^\]]*\]\s*", " ", name)
    name = re.sub(r"\s+\d+\s*$", "", name)
    return name.strip() or None


def _inline_tag_section(raw_name: str) -> str:
    """
    Return the lowercase content of the first [...] tag in the name string,
    or an empty string if no tag is present.
    Used to detect Archidekt inline maybeboard/sideboard markers.
    """
    m = re.search(r"\[([^\]]+)\]", raw_name)
    return m.group(1).lower() if m else ""


def parse_card_list(lines: list[str]) -> tuple[list[DeckCard], list[DeckCard], Optional[str]]:
    """
    Parse a card list from common export formats.

    Supports:
      4 Lightning Bolt                          plain text → main
      4x Lightning Bolt                         Moxfield / Archidekt (x suffix) → main
      1x Animate Dead (soc) [Recursion]         Archidekt — set code and tag stripped → main
      1x Cabal Ritual (tor) [Sideboard,Ramp]    Archidekt inline sideboard tag → sideboard
      1x Bolas's Citadel (war) [Maybeboard...]  Archidekt maybeboard — skipped entirely
      26x Swamp (hob) 196                       set code + collector number stripped → main
      SB: 4 Counterspell                        MTGO sideboard prefix → sideboard
      # comment / // comment                    skipped
      Sideboard (15)                            section header — cards below → sideboard
      Maybeboard                                section header — cards below skipped
      Commander (1) / Deck (98)                 section header — cards below → main

    Returns:
        (main_cards, sideboard_cards, commander_name_or_none)
    """
    main = []
    sideboard = []
    commander = None
    current_section = "main"  # "main", "sideboard", or "skip"

    for raw in lines:
        line = raw.strip()

        # Blank lines and comment lines
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        # MTGO sideboard prefix "SB: 4 Card Name" → route to sideboard
        mtgo_sb = re.match(r"^SB:\s*(.+)", line, re.IGNORECASE)
        if mtgo_sb:
            name = _clean_card_name(mtgo_sb.group(1).strip())
            if name:
                sideboard.append(DeckCard(name=name, count=1))
            continue

        # Section header detection (Moxfield / Arena / MTGO style)
        m = _SECTION_RE.match(line)
        if m:
            key = m.group(1).lower()
            if key == "sideboard":
                current_section = "sideboard"
            elif key in _SKIP_SECTIONS:
                current_section = "skip"
            else:
                current_section = "main"
            continue

        if current_section == "skip":
            continue

        # Split count prefix. Handles "4", "4x", "4X".
        parts = line.split(" ", 1)
        count_str = parts[0].rstrip("xX")
        if len(parts) == 2 and count_str.isdigit():
            count = int(count_str)
            name_raw = parts[1].strip()
        else:
            count = 1
            name_raw = line

        # Archidekt inline tag routing.
        # [Maybeboard{noDeck}...] → skip.
        # [Sideboard,...] → sideboard.
        # [Commander{top}] → main deck + mark as commander.
        tag = _inline_tag_section(name_raw)
        if "maybeboard" in tag:
            continue
        is_inline_sb = "sideboard" in tag and "commander" not in tag
        is_commander = "commander" in tag

        # Strip set codes, remaining tags, and trailing collector numbers.
        name = _clean_card_name(name_raw)
        if not name:
            continue

        if is_inline_sb or current_section == "sideboard":
            sideboard.append(DeckCard(name=name, count=count))
        else:
            main.append(DeckCard(name=name, count=count))
            if is_commander and commander is None:
                commander = name

    return main, sideboard, commander


def merge_cards(existing: list[DeckCard], new: list[DeckCard]) -> list[DeckCard]:
    """Merge two card lists, combining counts for duplicates (case-insensitive)."""
    index = {c.name.lower(): c for c in existing}
    for card in new:
        key = card.name.lower()
        if key in index:
            index[key].count += card.count
        else:
            existing.append(card)
            index[key] = card
    return existing
