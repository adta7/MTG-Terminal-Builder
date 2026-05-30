"""
oracle_preprocessor.py — Oracle text preprocessing and segmentation.

Phase 2.5: Foundation for pattern matching and evidence collection.

Goal: Transform raw oracle text into a queryable structure while preserving
evidence spans (character offsets) for traceability.

Responsibilities:
- Separate main rules text from reminder text
- Split card faces (MDFC, DFC)
- Segment abilities (activated, triggered, static, replacement)
- Preserve character offsets for evidence links
- Detect ability kind heuristically when possible
"""

import re
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class AbilitySegment:
    """A single ability or effect within oracle text."""
    text: str
    start: int  # Character offset in original oracle text
    end: int    # Character offset (exclusive)
    ability_kind: str  # "activated", "triggered", "static", "replacement", "other"
    face_index: int = 0  # 0 for front, 1 for back


@dataclass
class OraclePreprocessed:
    """Result of preprocessing oracle text."""
    card_name: str
    original_oracle: str
    normalized_oracle: str  # Lowercase for pattern matching
    main_text: str  # Rules text without reminder
    reminder_text: str  # Parenthetical reminder text
    faces: List[str]  # Card faces (single-face cards have length 1)
    segments: List[AbilitySegment]  # Individual abilities


def preprocess_oracle(card_name: str, oracle_text: str, face_index: int = 0) -> OraclePreprocessed:
    """
    Preprocess raw oracle text into a structured, queryable format.

    Args:
        card_name: Card name (for debugging)
        oracle_text: Raw oracle text from Scryfall
        face_index: 0 for front face, 1 for back face (for MDFC/DFC)

    Returns:
        OraclePreprocessed structure with segments and evidence spans
    """
    if not oracle_text:
        return OraclePreprocessed(
            card_name=card_name,
            original_oracle="",
            normalized_oracle="",
            main_text="",
            reminder_text="",
            faces=[""],
            segments=[],
        )

    # Normalize for pattern matching (preserve original for evidence spans)
    normalized = oracle_text.lower()

    # Separate reminder text (parenthetical) from main text
    main_text, reminder_text = _split_reminder_text(oracle_text)

    # Split by card faces if MDFC/DFC
    faces = _split_faces(oracle_text)

    # Segment abilities from main text
    segments = _segment_abilities(main_text, face_index)

    return OraclePreprocessed(
        card_name=card_name,
        original_oracle=oracle_text,
        normalized_oracle=normalized,
        main_text=main_text,
        reminder_text=reminder_text,
        faces=faces,
        segments=segments,
    )


def _split_reminder_text(oracle_text: str) -> tuple[str, str]:
    """
    Separate main rules text from reminder text (parenthetical).

    MTG uses parentheses for reminder text that explains keywords.

    Example:
        "Flying (This creature can't be blocked except by flying creatures.)"
        -> ("Flying", "(This creature can't be blocked except by flying creatures.)")

    Returns:
        (main_text, reminder_text)
    """
    # Find all parenthetical sections
    # Reminder text is always at the end of an ability
    main_parts = []
    reminder_parts = []
    current_pos = 0

    # Pattern: ability text, possibly ending with reminder in parens
    lines = oracle_text.split("\n")
    processed_lines = []

    for line in lines:
        # Extract content before the first paren, and everything in parens
        main_part = line
        reminder_part = ""

        # Find the last opening paren (reminder text is typically at the end)
        paren_match = re.search(r"\s*\(([^)]*)\)\s*$", line)
        if paren_match:
            main_part = line[:paren_match.start()].strip()
            reminder_part = paren_match.group(0).strip()

        processed_lines.append(main_part)
        if reminder_part:
            reminder_parts.append(reminder_part)

    main_text = "\n".join(processed_lines).strip()
    reminder_text = "\n".join(reminder_parts)

    return main_text, reminder_text


def _split_faces(oracle_text: str) -> List[str]:
    """
    Split MDFC/DFC text into front and back faces.

    Double-faced cards have oracle text in format:
        "Front side text
        ―――
        Back side text"

    Or sometimes:
        "Front side text"
        and
        "Back side text"

    For now, returns [oracle_text] for single-faced cards.
    TODO: Improve MDFC/DFC detection.
    """
    # Common separators for card faces
    separators = [r"\s*―――\s*", r"\s*//\s*", r"\s*&\s*"]

    for sep in separators:
        if re.search(sep, oracle_text):
            faces = re.split(sep, oracle_text)
            return [f.strip() for f in faces if f.strip()]

    # Single-faced card
    return [oracle_text]


def _segment_abilities(oracle_text: str, face_index: int = 0) -> List[AbilitySegment]:
    """
    Segment oracle text into individual abilities.

    Heuristics:
    - Activated abilities: "cost: effect" pattern
    - Triggered abilities: Start with "When", "Whenever", "At"
    - Static abilities: Other text (if, instead, as long as, etc.)

    Returns:
        List of AbilitySegment objects with character offsets
    """
    segments = []

    if not oracle_text:
        return segments

    # Split by common ability delimiters
    # In MTG, abilities are usually separated by newlines or bullet points
    lines = oracle_text.split("\n")
    current_offset = 0

    for line in lines:
        if not line.strip():
            current_offset += len(line) + 1  # +1 for newline
            continue

        # Detect ability kind from the line
        ability_kind = _detect_ability_kind(line)

        # Find the actual character span in the original text
        # This is a simplified approach; a full parser would be more complex
        segment = AbilitySegment(
            text=line.strip(),
            start=current_offset,
            end=current_offset + len(line),
            ability_kind=ability_kind,
            face_index=face_index,
        )
        segments.append(segment)

        current_offset += len(line) + 1  # +1 for newline

    return segments


def _detect_ability_kind(text: str) -> str:
    """
    Heuristically detect the ability kind from text.

    Returns: "activated", "triggered", "static", "replacement", or "other"
    """
    text_lower = text.lower().strip()

    # Triggered ability: starts with timing words (highest priority)
    # Use word boundaries to avoid matching "at" in "creature"
    if re.match(r"^(when|whenever|at\s)", text_lower):
        return "triggered"

    # Activated ability: contains colon (cost: effect)
    if ":" in text:
        return "activated"

    # Replacement effect: contains "instead"
    if "instead" in text_lower:
        return "replacement"

    # Static ability: typical keywords or ongoing effects
    static_indicators = [
        "flying", "lifelink", "haste", "deathtouch", "hexproof", "shroud",
        "indestructible", "unblockable", "can't be blocked", "can't attack",
        "if ", "as long as", "you may", "can't", "costs less", "must", "has"
    ]
    if any(indicator in text_lower for indicator in static_indicators):
        return "static"

    return "other"


def get_ability_segment(
    preprocessed: OraclePreprocessed,
    segment_index: int
) -> Optional[AbilitySegment]:
    """
    Get a specific ability segment by index.

    Useful for rules that want to inspect a particular ability.
    """
    if 0 <= segment_index < len(preprocessed.segments):
        return preprocessed.segments[segment_index]
    return None


def search_text(
    preprocessed: OraclePreprocessed,
    pattern: str,
    search_in: str = "main"
) -> List[tuple[int, int]]:
    """
    Search for a pattern in the preprocessed oracle text.

    Args:
        preprocessed: OraclePreprocessed result
        pattern: Regex pattern to search for
        search_in: "main", "reminder", "all", or "normalized"

    Returns:
        List of (start, end) spans where pattern matches
    """
    text_to_search = {
        "main": preprocessed.main_text,
        "reminder": preprocessed.reminder_text,
        "all": preprocessed.original_oracle,
        "normalized": preprocessed.normalized_oracle,
    }.get(search_in, preprocessed.main_text)

    matches = []
    for match in re.finditer(pattern, text_to_search, re.IGNORECASE):
        matches.append((match.start(), match.end()))

    return matches
