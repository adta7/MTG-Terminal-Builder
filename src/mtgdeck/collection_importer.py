"""
collection_importer.py — Load a collection Excel file into the database.

Handles deduplication, quantity aggregation, color-identity filtering,
and column detection so the importer survives minor spreadsheet variations.
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from .models import Card


# Columns that MUST be present for the import to work
REQUIRED_COLUMNS = {"Name", "Card Text"}

# Logical field → preferred Excel column name
COLUMN_MAP = {
    "name":           "Name",
    "verified_name":  "Verified Name",
    "count":          "Count",
    "foil":           "Foil",
    "mana_cost":      "Mana Cost",
    "cmc":            "CMC",
    "type_line":      "Type",
    "oracle_text":    "Card Text",
    "power":          "Power",
    "toughness":      "Toughness",
    "color_identity": "Color Identity",
    "rarity":         "Rarity",
    "commander_legal": "Commander Legal",
}


def detect_collection_columns(df: pd.DataFrame) -> dict:
    """Validate columns in the DataFrame and return a logical → actual column map.

    Raises ValueError with a clear message if required columns are missing.
    """
    available = set(df.columns)
    missing = REQUIRED_COLUMNS - available
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}\n"
            f"Available columns: {sorted(available)}"
        )

    col_map = {}
    for field, preferred in COLUMN_MAP.items():
        if preferred in available:
            col_map[field] = preferred

    return col_map


def is_black_or_colorless(value) -> bool:
    """Return True if the color identity qualifies for black/colorless scan.

    Includes: colorless (None, empty, nan), exactly black (B only).
    Excludes: any card with W, U, R, or G in color identity.

    Handles Excel formats: 'B', 'B, G', None, nan, '', 'Colorless'.
    """
    if value is None:
        return True
    s = str(value).strip().lower()
    if s in ("", "nan", "none", "colorless"):
        return True

    # Extract WUBRG letters from whatever format the value takes
    ci_letters = frozenset(c for c in s.upper() if c in "WUBRG")
    return not ci_letters.intersection(frozenset("WURG"))


def import_collection(
    excel_path: str,
    db,
    filter_black_colorless: bool = True,
) -> dict:
    """Import a collection Excel file into the database.

    - Validates required columns
    - Filters to black/colorless cards if requested
    - Deduplicates by Verified Name (or Name), aggregating quantities
    - Skips rows with no oracle text (tokens, placeholder rows)
    - Inserts into `cards` table and `collection` table

    Returns:
        {
            'cards_loaded': int,       # unique cards inserted into cards table
            'cards_skipped': int,      # rows filtered out or missing data
            'collection_rows': int,    # entries written to collection table
            'total_excel_rows': int,   # raw row count from Excel
        }
    """
    df = pd.read_excel(excel_path)
    col = detect_collection_columns(df)

    name_col = col.get("verified_name") or col.get("name")
    oracle_col = col.get("oracle_text")

    # Aggregation state: name → {quantity, foil_quantity, card_data}
    seen: dict[str, dict] = {}
    cards_skipped = 0

    for _, row in df.iterrows():
        raw_name = row[name_col] if name_col else None
        if raw_name is None or (isinstance(raw_name, float)):
            cards_skipped += 1
            continue

        name = str(raw_name).strip()
        if not name or name.lower() == "nan":
            cards_skipped += 1
            continue

        # Color identity filter
        ci_val = row[col["color_identity"]] if "color_identity" in col else None
        if filter_black_colorless and not is_black_or_colorless(ci_val):
            cards_skipped += 1
            continue

        # Oracle text: skip rows with no text (token cards, placeholder rows)
        oracle_text = ""
        if oracle_col:
            raw_oracle = row[oracle_col]
            if pd.notna(raw_oracle):
                oracle_text = str(raw_oracle).strip()

        # Quantity and foil
        count = 1
        if "count" in col:
            raw_count = row[col["count"]]
            if pd.notna(raw_count):
                try:
                    count = int(raw_count)
                except (ValueError, TypeError):
                    count = 1

        is_foil = False
        if "foil" in col:
            raw_foil = row[col["foil"]]
            if pd.notna(raw_foil):
                is_foil = bool(raw_foil)

        if name not in seen:
            # First occurrence: capture card data for insertion
            mana_cost = ""
            if "mana_cost" in col and pd.notna(row[col["mana_cost"]]):
                mana_cost = str(row[col["mana_cost"]]).strip()

            cmc = 0
            if "cmc" in col and pd.notna(row[col["cmc"]]):
                try:
                    cmc = int(float(row[col["cmc"]]))
                except (ValueError, TypeError):
                    cmc = 0

            type_line = ""
            if "type_line" in col and pd.notna(row[col["type_line"]]):
                type_line = str(row[col["type_line"]]).strip()

            power = None
            if "power" in col and pd.notna(row[col["power"]]):
                power = str(row[col["power"]]).strip()

            toughness = None
            if "toughness" in col and pd.notna(row[col["toughness"]]):
                toughness = str(row[col["toughness"]]).strip()

            seen[name] = {
                "card": Card(
                    name=name,
                    mana_cost=mana_cost,
                    cmc=cmc,
                    type_line=type_line,
                    oracle_text=oracle_text,
                    power=power,
                    toughness=toughness,
                ),
                "quantity": 0,
                "foil_quantity": 0,
            }

        seen[name]["quantity"] += count
        if is_foil:
            seen[name]["foil_quantity"] += count

    # Insert into database
    cards_loaded = 0
    for name, entry in seen.items():
        db.insert_card(entry["card"])
        cards_loaded += 1
        db.upsert_collection(
            card_name=name,
            quantity=entry["quantity"],
            foil_quantity=entry["foil_quantity"],
        )

    return {
        "cards_loaded": cards_loaded,
        "cards_skipped": cards_skipped,
        "collection_rows": len(seen),
        "total_excel_rows": len(df),
    }


def find_excel(hint: Optional[str] = None) -> Path:
    """Find the collection Excel file.

    Search order:
    1. Explicitly provided hint path
    2. Current directory
    3. Parent directories (up to 4 levels up)
    """
    if hint:
        p = Path(hint)
        if p.exists():
            return p
        raise FileNotFoundError(f"Excel not found at: {hint}")

    search_roots = [Path(".")]
    parent = Path(".").resolve()
    for _ in range(4):
        parent = parent.parent
        search_roots.append(parent)

    for root in search_roots:
        matches = list(root.glob("*.xlsx"))
        if matches:
            # Prefer files with "collection" in the name
            preferred = [m for m in matches if "collection" in m.name.lower()]
            return preferred[0] if preferred else matches[0]

    raise FileNotFoundError(
        "No .xlsx collection file found.\n"
        "Pass --excel PATH or place the Excel file in or above the project directory."
    )
