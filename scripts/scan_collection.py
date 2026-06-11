#!/usr/bin/env python3
"""
scan_collection.py — Import black/colorless collection cards and run the mechanical tagger.

Usage:
  python scripts/scan_collection.py [--excel PATH]

Output:
  data/collection_scan.sqlite
  reports/collection_scan/summary.md
  reports/collection_scan/untagged_cards.csv
  reports/collection_scan/unmatched_phrases.csv
  reports/collection_scan/anchor_validation.md

This is a MEASUREMENT script. It does not modify the production database.
It does not add new patterns. It scans and reports only.
"""

import sys
import argparse
import csv
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.database import Database
from mtgdeck.tags import seed_tags, tag_mechanical
from mtgdeck.layer2_scanner import Layer2Scanner
from mtgdeck.collection_importer import import_collection, find_excel

# ─── Anchor cards that define this deck's strategic identity ──────────────────
# These should be understood by the tagger. Missing tags here are high-priority gaps.
ANCHOR_CARDS = [
    ("Ashnod's Altar",          ["Sacrifice_Outlet", "Mana_Production"]),
    ("Viscera Seer",             ["Sacrifice_Outlet"]),
    ("Blood Artist",             ["Death_Trigger", "Life_Drain"]),
    ("Grave Pact",               ["Death_Trigger", "Forced_Sacrifice"]),
    ("Living Death",             ["Mass_Reanimate"]),
    ("Animate Dead",             ["Reanimation"]),
    ("Sheoldred, Whispering One",["Reanimation", "Forced_Sacrifice"]),
    ("Ghoulcaller Gisa",         ["Sacrifice_Outlet", "Token_Generation"]),
    ("Bolas's Citadel",          ["Life_Drain"]),
    ("Phyrexian Arena",          ["Draw_Effect"]),
    ("Black Market",             ["Scales_With_Deaths", "Mana_Production"]),
    ("Crypt Ghast",              ["Mana_Multiplier"]),
    ("Necropotence",             ["Life_Payment"]),
    ("Demonic Tutor",            ["Tutor_Effect"]),
    ("Bitterblossom",            ["Repeatable_Token_Generation"]),
]


def _pct(n: int, total: int) -> str:
    return f"{100*n//total}%" if total else "0%"


def run_scan(excel_path: str, scan_db_path: str, reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n{'='*60}")
    print("  COLLECTION SCAN — BLACK/COLORLESS")
    print(f"  {timestamp}")
    print(f"{'='*60}\n")

    # ── Step 1: Fresh database ────────────────────────────────────────────────
    print("→ Creating fresh scan database...")
    scan_db = Path(scan_db_path)
    if scan_db.exists():
        scan_db.unlink()
    db = Database(scan_db_path)
    db.init_db()
    seed_tags(db)
    print(f"  OK: {scan_db_path}")

    # ── Step 2: Import collection ─────────────────────────────────────────────
    print(f"\n→ Importing from: {excel_path}")
    result = import_collection(excel_path, db, filter_black_colorless=True)
    print(f"  Loaded:  {result['cards_loaded']} unique black/colorless cards")
    print(f"  Skipped: {result['cards_skipped']} (other colors or missing data)")
    print(f"  Excel rows: {result['total_excel_rows']}")

    # ── Step 3: Run mechanical tagger ─────────────────────────────────────────
    print("\n→ Running mechanical tagger...")
    all_cards = list(db.all_cards())
    tagged_cards = 0
    untagged_cards = []

    for card in all_cards:
        if card.oracle_text:
            applied = tag_mechanical(card, db)
            if applied:
                tagged_cards += 1
            else:
                untagged_cards.append(card)
        else:
            untagged_cards.append(card)

    total = len(all_cards)
    print(f"  Tagged:   {tagged_cards}/{total}  ({_pct(tagged_cards, total)})")
    print(f"  Untagged: {total - tagged_cards}/{total}  ({_pct(total-tagged_cards, total)})")

    # ── Step 4: Scanner ───────────────────────────────────────────────────────
    print("\n→ Running scanner...")
    scanner = Layer2Scanner(db)
    gaps = scanner.scan_coverage_gaps(scope="all")
    phrases = scanner.scan_unmatched_phrases(scope="all", min_frequency=2)
    print(f"  Coverage gaps: {len(gaps)} cards")
    print(f"  Unmatched phrase clusters: {len(phrases)}")

    # ── Step 5: Tag distribution ──────────────────────────────────────────────
    cur = db.conn.cursor()
    cur.execute("""
        SELECT t.name, COUNT(ct.card_name) as cnt
        FROM tags t
        LEFT JOIN card_tags ct ON ct.tag_id = t.id
        WHERE t.layer = 'mechanical'
        GROUP BY t.id
        HAVING cnt > 0
        ORDER BY cnt DESC
    """)
    tag_dist = cur.fetchall()

    # ── Step 6: Anchor card validation ───────────────────────────────────────
    anchor_results = []
    for card_name, expected_tags in ANCHOR_CARDS:
        card_tags = db.get_card_tags(card_name)
        actual_tags = {t["name"] for t in card_tags}
        hits = [t for t in expected_tags if t in actual_tags]
        misses = [t for t in expected_tags if t not in actual_tags]
        in_collection = db.card_by_name(card_name) is not None
        anchor_results.append({
            "card": card_name,
            "in_collection": in_collection,
            "expected": expected_tags,
            "actual": sorted(actual_tags),
            "hits": hits,
            "misses": misses,
            "ok": len(misses) == 0 and in_collection,
        })

    # ── Step 7: Write reports ─────────────────────────────────────────────────
    _write_summary(reports_dir, timestamp, result, tagged_cards, total, tag_dist, anchor_results, gaps)
    _write_untagged_csv(reports_dir, gaps)
    _write_phrases_csv(reports_dir, phrases)
    _write_anchor_report(reports_dir, timestamp, anchor_results)

    # ── Print summary to terminal ─────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("TAG COVERAGE (top 20)")
    print(f"{'─'*60}")
    for tag_name, cnt in tag_dist[:20]:
        bar = "█" * min(cnt, 40)
        print(f"  {tag_name:<30} {cnt:>4}  {bar}")

    print(f"\n{'─'*60}")
    print("ANCHOR CARD VALIDATION")
    print(f"{'─'*60}")
    for r in anchor_results:
        status = "✓" if r["ok"] else ("✗" if r["in_collection"] else "—")
        tags_str = ", ".join(r["actual"][:4]) + ("…" if len(r["actual"]) > 4 else "")
        miss_str = f"  MISSING: {r['misses']}" if r["misses"] else ""
        print(f"  {status} {r['card']:<35} [{tags_str}]{miss_str}")

    print(f"\n{'─'*60}")
    print("TOP UNMATCHED PHRASE CLUSTERS")
    print(f"{'─'*60}")
    for p in phrases[:12]:
        examples = ", ".join(p.example_cards[:2])
        print(f"  ({p.frequency}x) {p.phrase!r:<50} [{p.mechanic_family}]  eg: {examples}")

    print(f"\n{'─'*60}")
    print("REPORTS WRITTEN")
    print(f"{'─'*60}")
    for f in sorted(reports_dir.glob("*")):
        print(f"  {f}")
    print()


def _write_summary(reports_dir, timestamp, import_result, tagged, total, tag_dist, anchors, gaps):
    anchor_ok = sum(1 for r in anchors if r["ok"])
    anchor_in = sum(1 for r in anchors if r["in_collection"])
    anchor_total = len(anchors)

    lines = [
        "# Collection Scan — Summary",
        f"\n**Run:** {timestamp}",
        f"\n## Import",
        f"- Cards loaded: {import_result['cards_loaded']} unique black/colorless",
        f"- Cards skipped: {import_result['cards_skipped']} (other colors or empty)",
        f"- Excel rows: {import_result['total_excel_rows']}",
        f"\n## Coverage",
        f"- Tagged: {tagged}/{total} ({_pct(tagged, total)})",
        f"- Untagged: {total-tagged}/{total} ({_pct(total-tagged, total)})",
        f"- Coverage gaps (zero-tag cards): {len(gaps)}",
        f"\n## Anchor Cards",
        f"- {anchor_ok}/{anchor_in} owned anchors fully tagged  ({anchor_in}/{anchor_total} anchors in collection)",
        f"\n## Mechanical Tag Distribution",
    ]
    for tag_name, cnt in tag_dist:
        lines.append(f"- {tag_name}: {cnt}")

    lines += [
        f"\n## What to do next",
        "1. Review `untagged_cards.csv` — cards with taggable text but no tags",
        "2. Review `unmatched_phrases.csv` — recurring phrases with no pattern (pattern backlog)",
        "3. Review `anchor_validation.md` — key identity cards, verify correctness",
        "4. Pick top 3–5 unmatched phrases and add patterns (Phase 4B)",
    ]

    (reports_dir / "summary.md").write_text("\n".join(lines))


def _write_untagged_csv(reports_dir, gaps):
    with open(reports_dir / "untagged_cards.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["card_name", "has_taggable_verbs", "oracle_snippet"])
        for g in gaps:
            snippet = (g.oracle_text or "")[:120].replace("\n", " ")
            w.writerow([g.card_name, g.has_taggable_verbs, snippet])


def _write_phrases_csv(reports_dir, phrases):
    with open(reports_dir / "unmatched_phrases.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frequency", "mechanic_family", "phrase", "example_cards"])
        for p in phrases:
            w.writerow([p.frequency, p.mechanic_family, p.phrase, "; ".join(p.example_cards)])


def _write_anchor_report(reports_dir, timestamp, anchor_results):
    lines = [
        "# Anchor Card Validation",
        f"\n**Run:** {timestamp}",
        "\nCards that define the deck's strategic identity. Missing tags here are high-priority gaps.",
        "",
    ]
    for r in anchor_results:
        status = "✓ OK" if r["ok"] else ("✗ GAP" if r["in_collection"] else "— NOT IN COLLECTION")
        lines.append(f"\n## {r['card']} — {status}")
        lines.append(f"- Expected: {r['expected']}")
        lines.append(f"- Actual: {r['actual']}")
        if r["misses"]:
            lines.append(f"- **Missing tags: {r['misses']}**")
        if not r["in_collection"]:
            lines.append("- *Card not in collection — add it to validate.*")

    (reports_dir / "anchor_validation.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Scan black/colorless collection cards.")
    parser.add_argument("--excel", help="Path to collection Excel file")
    parser.add_argument("--db", default="data/collection_scan.sqlite", help="Output SQLite path")
    parser.add_argument("--reports", default="reports/collection_scan", help="Reports output dir")
    args = parser.parse_args()

    excel_path = find_excel(args.excel)
    run_scan(
        excel_path=str(excel_path),
        scan_db_path=args.db,
        reports_dir=Path(args.reports),
    )


if __name__ == "__main__":
    main()
