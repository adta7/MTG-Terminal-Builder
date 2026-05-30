#!/usr/bin/env python3
"""
debug_collection_card.py — Diagnose why a card is missing or mis-tagged.

Usage:
  python scripts/debug_collection_card.py "Demonic Tutor"
  python scripts/debug_collection_card.py "Bitterblossom" --excel PATH
  python scripts/debug_collection_card.py "Necropotence" --db data/collection_scan.sqlite
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.database import Database
from mtgdeck.collection_importer import find_excel, is_black_or_colorless
import pandas as pd


def debug_card(card_name: str, excel_path: str, db_path: str) -> None:
    print(f"\n{'='*60}")
    print(f"  DEBUG: {card_name!r}")
    print(f"{'='*60}")

    # ── 1. Search in Excel ────────────────────────────────────────────────────
    print("\n[1] Excel lookup")
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"  ERROR reading Excel: {e}")
        df = None

    excel_rows = []
    if df is not None:
        for col in ["Verified Name", "Name"]:
            if col in df.columns:
                matches = df[df[col].astype(str).str.lower() == card_name.lower()]
                if not matches.empty:
                    excel_rows = matches.to_dict("records")
                    break
        # Fuzzy fallback: partial match
        if not excel_rows and df is not None:
            for col in ["Verified Name", "Name"]:
                if col in df.columns:
                    partial = df[df[col].astype(str).str.lower().str.contains(
                        card_name.lower(), na=False
                    )]
                    if not partial.empty:
                        print(f"  NOTE: No exact match. Partial matches on {col!r}:")
                        for _, r in partial.iterrows():
                            print(f"    {r.get('Verified Name') or r.get('Name')!r}")
                        break

    if not excel_rows:
        print(f"  NOT FOUND in Excel (exact name: {card_name!r})")
    else:
        print(f"  Found {len(excel_rows)} row(s) in Excel:")
        for r in excel_rows:
            name = r.get("Verified Name") or r.get("Name")
            ci = r.get("Color Identity")
            count = r.get("Count", 1)
            foil = r.get("Foil")
            oracle = str(r.get("Card Text", "") or "")[:100]
            ci_pass = is_black_or_colorless(ci)
            print(f"    Name:           {name!r}")
            print(f"    Color Identity: {ci!r}  → filter passes: {ci_pass}")
            print(f"    Count/Foil:     {count} / {foil}")
            print(f"    Oracle (100ch): {oracle!r}")
            if not ci_pass:
                print(f"    ⚠  FILTERED OUT by color identity — not black/colorless")

    # ── 2. Cards table ────────────────────────────────────────────────────────
    print("\n[2] Scan DB — cards table")
    try:
        db = Database(db_path)
        db.connect()
    except Exception as e:
        print(f"  ERROR opening DB {db_path}: {e}")
        return

    card = db.card_by_name(card_name)
    if card is None:
        print(f"  NOT FOUND in cards table (name: {card_name!r})")
        # Check if close match exists
        cur = db.conn.cursor()
        cur.execute(
            "SELECT name FROM cards WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{card_name[:6]}%",),
        )
        close = [r[0] for r in cur.fetchall()[:5]]
        if close:
            print(f"  Close matches in cards: {close}")
    else:
        print(f"  FOUND: {card.name!r}")
        print(f"    type_line:    {card.type_line!r}")
        print(f"    mana_cost:    {card.mana_cost!r}")
        print(f"    oracle_text:  {(card.oracle_text or '')[:120]!r}")
        has_oracle = bool(card.oracle_text and card.oracle_text.strip())
        print(f"    oracle present: {has_oracle}")

    # ── 3. Collection table ───────────────────────────────────────────────────
    print("\n[3] Scan DB — collection table")
    cur = db.conn.cursor()
    cur.execute(
        "SELECT * FROM collection WHERE LOWER(card_name) = LOWER(?)",
        (card_name,),
    )
    col_rows = cur.fetchall()
    if not col_rows:
        print(f"  NOT FOUND in collection table")
    else:
        for r in col_rows:
            print(f"  card_name={r['card_name']!r}  quantity={r['quantity']}  foil={r['foil']}")

    # ── 4. Tags assigned ─────────────────────────────────────────────────────
    print("\n[4] Tags assigned")
    card_tags = db.get_card_tags(card_name)
    if not card_tags:
        print(f"  No tags assigned")
    else:
        for t in card_tags:
            print(f"  {t['name']:<35} confidence={t['confidence']:.2f}  source={t['source']!r}")

    # ── 5. Evidence rows ─────────────────────────────────────────────────────
    print("\n[5] Evidence rows")
    evidence = db.get_tag_evidence(card_name)
    if not evidence:
        print(f"  No evidence rows")
    else:
        for e in evidence:
            print(f"  rule_id:      {e['rule_id']!r}")
            print(f"  evidence_text:{e['evidence_text']!r}")
            print(f"  ability_kind: {e['ability_kind']!r}  text_role: {e['text_role']!r}")
            print()

    db.close()
    print(f"{'─'*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Debug a card's import and tagging state.")
    parser.add_argument("card_name", help="Card name to debug")
    parser.add_argument("--excel", help="Excel path (auto-detected if omitted)")
    parser.add_argument("--db", default="data/collection_scan.sqlite", help="Scan DB path")
    args = parser.parse_args()

    excel_path = find_excel(args.excel)
    debug_card(args.card_name, str(excel_path), args.db)


if __name__ == "__main__":
    main()
