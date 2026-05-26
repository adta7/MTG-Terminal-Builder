"""
scryfall.py — Download and index Scryfall card data.

Handles:
- Finding local Scryfall JSON (oracle-cards-*.json)
- Downloading from Scryfall if needed
- Normalizing card data (handling DFCs, extracting fields)
- Indexing into database
"""

import json
import urllib.request
import os
from pathlib import Path
from typing import Optional, List

from .models import Card
from .database import Database


def find_scryfall_json(search_dir: Optional[str] = None) -> str:
    """
    Locate the Scryfall oracle cards JSON file.

    Searches for files matching patterns:
      - oracle-cards*.json
      - *.json (if no oracle-cards found, takes first *.json)

    Args:
        search_dir: Directory to search (default: current dir)

    Returns:
        Path to the JSON file

    Raises:
        FileNotFoundError: If no suitable JSON found
    """
    search_dir = search_dir or "."
    files = list(Path(search_dir).glob("oracle-cards*.json"))

    if files:
        return str(files[0])

    files = list(Path(search_dir).glob("*.json"))
    if files:
        return str(files[0])

    raise FileNotFoundError(
        f"No Scryfall JSON found in {search_dir}. "
        "Expected: oracle-cards-*.json or *.json"
    )


def download_scryfall_bulk(output_path: str = "oracle-cards-latest.json") -> str:
    """
    Download the latest Scryfall bulk data JSON.

    Args:
        output_path: Where to save the file

    Returns:
        Path to downloaded file

    Raises:
        urllib.error.URLError: If download fails
    """
    url = "https://data.scryfall.io/oracle-cards/oracle-cards.json"
    print(f"\n  Downloading Scryfall data (~165MB)...")
    print(f"  This may take a minute...\n")

    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"\n  ✓ Downloaded to {output_path}\n")
        return output_path
    except Exception as e:
        print(f"\n  ✗ Download failed: {e}\n")
        raise


def normalize_card(raw_card: dict) -> Optional[Card]:
    """
    Convert a Scryfall card object to our Card model.

    Handles:
    - Double-faced cards (merge faces with " // ")
    - Missing fields (use defaults)
    - Color/legality extraction

    Returns:
        Card object, or None if card is invalid
    """
    name = raw_card.get("name")
    if not name:
        return None

    # For double-faced cards, merge relevant fields
    mana_cost = raw_card.get("mana_cost", "")
    type_line = raw_card.get("type_line", "")
    oracle_text = raw_card.get("oracle_text", "")
    power = raw_card.get("power")
    toughness = raw_card.get("toughness")
    loyalty = raw_card.get("loyalty")

    if "card_faces" in raw_card:
        faces = raw_card["card_faces"]
        if len(faces) >= 2:
            # Merge both faces
            mana_cost = " // ".join(f.get("mana_cost", "") for f in faces if f.get("mana_cost"))
            type_line = " // ".join(f.get("type_line", "") for f in faces if f.get("type_line"))
            oracle_text = "\n\n".join(f.get("oracle_text", "") for f in faces if f.get("oracle_text"))
            # Use first face's P/T/loyalty
            if faces[0]:
                power = faces[0].get("power")
                toughness = faces[0].get("toughness")
                loyalty = faces[0].get("loyalty")

    cmc = raw_card.get("cmc", 0)
    colors = raw_card.get("colors", [])
    color_identity = raw_card.get("color_identity", [])
    keywords = raw_card.get("keywords", [])
    rarity = raw_card.get("rarity", "")
    set_name = raw_card.get("set_name", "")
    scryfall_uri = raw_card.get("scryfall_uri", "")
    legalities = raw_card.get("legalities", {})

    return Card(
        name=name,
        mana_cost=mana_cost,
        cmc=int(cmc) if cmc else 0,
        type_line=type_line,
        oracle_text=oracle_text,
        power=power,
        toughness=toughness,
        loyalty=loyalty,
        colors=colors,
        color_identity=color_identity,
        keywords=keywords,
        rarity=rarity,
        set_name=set_name,
        scryfall_uri=scryfall_uri,
        legalities=legalities,
    )


def load_json_cards(json_path: str) -> List[dict]:
    """Load all cards from Scryfall JSON file."""
    print(f"  Loading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    return cards


def index_cards_into_db(json_path: str, db: Database) -> int:
    """
    Load cards from JSON and insert into database.

    Returns:
        Number of cards indexed
    """
    raw_cards = load_json_cards(json_path)
    cards = []

    print(f"  Normalizing {len(raw_cards)} cards...")
    for raw in raw_cards:
        card = normalize_card(raw)
        if card:
            cards.append(card)

    print(f"  Inserting {len(cards)} cards into database...")
    db.insert_cards_bulk(cards)
    print(f"  ✓ Indexed {len(cards)} cards")

    return len(cards)
