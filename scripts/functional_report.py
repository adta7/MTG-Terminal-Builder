#!/usr/bin/env python3
"""
functional_report.py — Run Layer 3 functional derivation on the collection and report.

Usage:
  python scripts/functional_report.py

Output:
  reports/collection_scan/functional_roles.md
  reports/collection_scan/functional_roles.csv

This is a read-report script. It writes functional tags to collection_scan.sqlite
but does not touch the production database.
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.database import Database
from mtgdeck.tags import tag_functional_from_rules, FUNCTIONAL_RULES, seed_tags

SCAN_DB = "data/collection_scan.sqlite"
REPORTS_DIR = Path("reports/collection_scan")

# ── Watchlist: cards whose functional role most matters for the deck identity ──
WATCHLIST = [
    "Ashnod's Altar",
    "Blood Artist",
    "Grave Pact",
    "Living Death",
    "Ghoulcaller Gisa",
    "Bolas's Citadel",
    "Black Market",
    "Sheoldred, Whispering One",
    "Phyrexian Arena",
    "Crypt Ghast",
    "Viscera Seer",
    "Nirkana Revenant",
    "Yawgmoth, Thran Physician",
    "Diabolic Tutor",
]

# ── Deck-relevant functional buckets (display order) ─────────────────────────
BUCKET_ORDER = [
    "Engine",
    "Conversion",
    "Payoff",
    "Fuel",
    "Recursion",
    "Finisher",
    "Finisher_Support",
    "Mana_Engine",
    "Mana_Acceleration",
    "Card_Draw",
    "Card_Advantage",
    "Enabler",
    "Setup",
    "Removal",
    "Interaction",
    "Threat",
    "Protection",
]


def _mech_tags(db, card_name: str) -> set[str]:
    return {t["name"] for t in db.get_card_tags(card_name, layer="mechanical")}


def _func_tags(db, card_name: str) -> set[str]:
    return {t["name"] for t in db.get_card_tags(card_name, layer="functional")}


def _firing_rules(mech: set[str]) -> list[tuple[str, float, str]]:
    """Return (functional_tag, confidence, required_tags_str) for each firing rule."""
    # Group by functional_tag, keep highest confidence
    best: dict[str, tuple[float, str]] = {}
    for required, ftag, conf in FUNCTIONAL_RULES:
        if required.issubset(mech):
            if conf > best.get(ftag, (0, ""))[0]:
                best[ftag] = (conf, " + ".join(sorted(required)))
    return sorted(
        [(ftag, conf, req) for ftag, (conf, req) in best.items()],
        key=lambda x: -x[1],
    )


def run_functional_derivation(db) -> dict[str, list[str]]:
    """Run Layer 3 on all collection cards. Return {card_name: [functional_tags]}."""
    results = {}
    cards = list(db.collection_cards())
    print(f"Running Layer 3 derivation on {len(cards)} collection cards...")
    for card in cards:
        applied = tag_functional_from_rules(card.name, db)
        results[card.name] = applied
    print(f"  Done. Cards with functional tags: {sum(1 for v in results.values() if v)}/{len(cards)}")
    return results


def generate_reports(db) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    all_cards = sorted(db.collection_cards(), key=lambda c: c.name)

    # Collect per-card data
    card_data = []
    for card in all_cards:
        mech = _mech_tags(db, card.name)
        func = _func_tags(db, card.name)
        rules = _firing_rules(mech)
        card_data.append({
            "name": card.name,
            "mech": mech,
            "func": func,
            "rules": rules,
        })

    # Bucket → cards
    buckets: dict[str, list[dict]] = defaultdict(list)
    for c in card_data:
        for ftag in c["func"]:
            buckets[ftag].append(c)

    untagged_func = [c for c in card_data if not c["func"]]

    # ── Write CSV ─────────────────────────────────────────────────────────────
    with open(REPORTS_DIR / "functional_roles.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["card_name", "mechanical_tags", "functional_tags",
                    "top_rule_required", "top_confidence"])
        for c in card_data:
            mech_str = ", ".join(sorted(c["mech"]))
            func_str = ", ".join(sorted(c["func"]))
            top = c["rules"][0] if c["rules"] else ("", 0, "")
            w.writerow([c["name"], mech_str, func_str, top[2], f"{top[1]:.2f}"])

    # ── Write Markdown ────────────────────────────────────────────────────────
    lines = [
        "# Functional Role Report — Collection Scan",
        "",
        "Layer 3 derivation applied to 347 black/colorless collection cards.",
        "Rules fire when a card's mechanical tags satisfy the required set.",
        "",
    ]

    # Summary table
    lines += ["## Role Summary", ""]
    lines.append(f"| Role | Cards |")
    lines.append(f"|------|-------|")
    for bucket in BUCKET_ORDER:
        if bucket in buckets:
            lines.append(f"| {bucket} | {len(buckets[bucket])} |")
    lines.append(f"| *(no functional role)* | {len(untagged_func)} |")
    lines.append("")

    # ── Watchlist section ────────────────────────────────────────────────────
    lines += ["## Watchlist: Deck Identity Cards", ""]
    for name in WATCHLIST:
        card = next((c for c in card_data if c["name"] == name), None)
        if card is None:
            lines.append(f"### {name} — NOT IN COLLECTION")
            lines.append("")
            continue

        func_str = ", ".join(sorted(card["func"])) or "*(none)*"
        mech_str = ", ".join(sorted(card["mech"])) or "*(none)*"
        lines.append(f"### {name}")
        lines.append(f"- **Mechanical:** {mech_str}")
        lines.append(f"- **Functional:** {func_str}")
        if card["rules"]:
            lines.append(f"- **Rules that fired:**")
            for ftag, conf, req in card["rules"][:5]:
                lines.append(f"  - `{req}` → **{ftag}** ({conf:.0%})")
        lines.append("")

    # ── Per-bucket detail ────────────────────────────────────────────────────
    lines += ["## Functional Roles Detail", ""]
    for bucket in BUCKET_ORDER:
        if bucket not in buckets:
            continue
        cards_in = sorted(buckets[bucket], key=lambda c: c["name"])
        lines.append(f"### {bucket} ({len(cards_in)} cards)")
        lines.append("")
        for c in cards_in:
            # Find the specific rule that fired for this bucket
            rule_for_bucket = next(
                (r for r in c["rules"] if r[0] == bucket), None
            )
            rule_str = f" via `{rule_for_bucket[2]}`" if rule_for_bucket else ""
            func_others = sorted(c["func"] - {bucket})
            others_str = f" | also: {', '.join(func_others)}" if func_others else ""
            lines.append(f"- **{c['name']}**{rule_str}{others_str}")
        lines.append("")

    # ── Cards with no functional role ─────────────────────────────────────────
    if untagged_func:
        lines.append(f"## No Functional Role ({len(untagged_func)} cards)")
        lines.append("")
        lines.append("These have no mechanical tags, or only tags not yet covered by functional rules.")
        lines.append("")
        for c in untagged_func[:30]:
            mech_str = ", ".join(sorted(c["mech"])) or "*(no mechanical tags)*"
            lines.append(f"- {c['name']} [{mech_str}]")
        if len(untagged_func) > 30:
            lines.append(f"- ... and {len(untagged_func) - 30} more")
        lines.append("")

    (REPORTS_DIR / "functional_roles.md").write_text("\n".join(lines))


def print_summary(db) -> None:
    all_cards = list(db.collection_cards())
    card_data = [
        {
            "name": c.name,
            "func": _func_tags(db, c.name),
            "mech": _mech_tags(db, c.name),
        }
        for c in all_cards
    ]

    with_func = sum(1 for c in card_data if c["func"])
    print(f"\n{'='*60}")
    print("  FUNCTIONAL ROLE SUMMARY")
    print(f"{'='*60}")
    print(f"  Cards with functional tags: {with_func}/{len(all_cards)}")

    buckets: dict[str, int] = defaultdict(int)
    for c in card_data:
        for f in c["func"]:
            buckets[f] += 1

    print(f"\n{'─'*60}")
    print("ROLE COUNTS")
    print(f"{'─'*60}")
    for bucket in BUCKET_ORDER:
        if bucket in buckets:
            bar = "█" * min(buckets[bucket], 40)
            print(f"  {bucket:<22} {buckets[bucket]:>4}  {bar}")

    print(f"\n{'─'*60}")
    print("WATCHLIST")
    print(f"{'─'*60}")
    for name in WATCHLIST:
        card = next((c for c in card_data if c["name"] == name), None)
        if card is None:
            print(f"  — {name:<35} NOT IN COLLECTION")
            continue
        func_str = ", ".join(sorted(card["func"])) or "*(none)*"
        mech_str = ", ".join(sorted(card["mech"]))
        print(f"  ✓ {name:<35} [{func_str}]")
        print(f"      mech: {mech_str}")

    print(f"\n{'─'*60}")
    print("REPORTS WRITTEN")
    print(f"{'─'*60}")
    for f in sorted(REPORTS_DIR.glob("*.md")) + sorted(REPORTS_DIR.glob("*.csv")):
        print(f"  {f}")
    print()


def main():
    db = Database(SCAN_DB)
    db.connect()

    # Ensure tags are seeded (safe to call multiple times)
    seed_tags(db)

    run_functional_derivation(db)
    generate_reports(db)
    print_summary(db)

    db.close()


if __name__ == "__main__":
    main()
