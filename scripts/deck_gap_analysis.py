#!/usr/bin/env python3
"""
deck_gap_analysis.py — Compare current deck against functional role targets.

Usage:
  python scripts/deck_gap_analysis.py [--deck PATH] [--db PATH]

Output:
  reports/deck_analysis/gap_report.md
  reports/deck_analysis/role_counts.csv
  reports/deck_analysis/candidates.md

Goal: answer "what does my deck need more or less of?" using functional roles
and the known collection. Does NOT make final cuts — diagnostic only.
"""

import sys
import json
import csv
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.database import Database
from mtgdeck.tags import tag_functional_from_rules, seed_tags

# ── Target role ranges for Sheoldred mono-black aristocrats/reanimator ────────
# Based on 99-card Commander (87 known + ~12 lands/utility to fill).
# Ranges are (min, ideal_min, ideal_max, max).
TARGETS = {
    "Mana_Acceleration": (10, 11, 14, 16),
    "Mana_Engine":        (1,  2,  4,  6),
    "Card_Draw":          (8,  9,  12, 15),
    "Removal":            (8,  9,  12, 14),
    "Engine":             (8,  10, 16, 20),
    "Payoff":             (5,  6,  10, 13),
    "Fuel":               (4,  5,  8,  11),
    "Recursion":          (5,  6,  9,  12),
    "Conversion":         (4,  5,  8,  11),
    "Finisher":           (3,  3,  6,  8),
    "Enabler":            (6,  7,  12, 16),
    "Interaction":        (5,  6,  9,  12),
    "Threat":             (5,  6,  10, 14),
    "Setup":              (3,  4,  7,  9),
    "Protection":         (2,  2,  4,  6),
}

# ── Deck CMC profile targets ──────────────────────────────────────────────────
# In a 99-card Commander deck, most spells should be ≤4 CMC with some at 5+.
EARLY_CURVE_TARGET = 0.40   # at least 40% of nonland cards should be CMC ≤ 3

# ── Priority tags for recommendations ─────────────────────────────────────────
# Ordered by what matters most for this deck's "hand feels sad" problem.
PRIORITY_GAPS = [
    "Card_Draw",
    "Fuel",
    "Mana_Acceleration",
    "Removal",
    "Recursion",
    "Engine",
    "Payoff",
    "Finisher",
    "Protection",
]

DECK_PATH = "/Users/albertyan/code/mtg-pipeline-terminal/decks/bahahahah.json"
SCAN_DB   = "data/collection_scan.sqlite"
REPORTS   = Path("reports/deck_analysis")


def load_deck(deck_path: str) -> list[dict]:
    with open(deck_path) as f:
        data = json.load(f)
    return data


def card_info(db, card_name: str) -> dict:
    card = db.card_by_name(card_name)
    if not card:
        return {"name": card_name, "mech": [], "func": [], "cmc": 0, "type": ""}
    mech = {t["name"] for t in db.get_card_tags(card.name, layer="mechanical")}
    func = {t["name"] for t in db.get_card_tags(card.name, layer="functional")}
    return {
        "name": card.name,
        "cmc": card.cmc or 0,
        "type": card.type_line or "",
        "oracle": (card.oracle_text or "")[:100],
        "mech": mech,
        "func": func,
    }


def is_land(card_info_dict: dict) -> bool:
    return "Land" in card_info_dict.get("type", "")


def gap_status(count: int, targets: tuple) -> str:
    lo, ideal_lo, ideal_hi, hi = targets
    if count < lo:
        return "CRITICAL"
    if count < ideal_lo:
        return "LOW"
    if count > hi:
        return "HIGH"
    if count > ideal_hi:
        return "SLIGHTLY HIGH"
    return "OK"


def find_candidates(db, role: str, deck_names: set[str], limit: int = 8) -> list[dict]:
    """Find collection cards with the given functional role NOT in the deck."""
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT ct.card_name, ct.confidence
        FROM card_tags ct
        JOIN tags t ON ct.tag_id = t.id
        WHERE t.name = ? AND t.layer = 'functional'
          AND LOWER(ct.card_name) NOT IN ({placeholders})
        ORDER BY ct.confidence DESC
        """,
        [role] + list(deck_names),
    )
    # Rebuild with placeholders properly
    placeholders = ",".join(["?" for _ in deck_names])
    cur.execute(
        f"""
        SELECT ct.card_name, ct.confidence
        FROM card_tags ct
        JOIN tags t ON ct.tag_id = t.id
        WHERE t.name = ? AND t.layer = 'functional'
          AND LOWER(ct.card_name) NOT IN ({placeholders})
        ORDER BY ct.confidence DESC
        """,
        [role] + [n.lower() for n in deck_names],
    )
    rows = cur.fetchall()
    results = []
    for card_name, conf in rows[:limit*2]:
        c = db.card_by_name(card_name)
        if c:
            func = {t["name"] for t in db.get_card_tags(card_name, layer="functional")}
            mech = {t["name"] for t in db.get_card_tags(card_name, layer="mechanical")}
            results.append({
                "name": card_name,
                "cmc": c.cmc or 0,
                "type": c.type_line or "",
                "conf": conf,
                "func": func,
                "mech": mech,
            })
    # Sort by confidence, then CMC (prefer lower CMC)
    results.sort(key=lambda x: (-x["conf"], x["cmc"]))
    return results[:limit]


def run_analysis(deck_path: str, db_path: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)

    deck = load_deck(deck_path)
    deck_cards_raw = deck.get("cards", [])
    deck_name = deck.get("name", "Unknown")
    commander = deck.get("commander", "Sheoldred, Whispering One")

    print(f"\n{'='*60}")
    print(f"  DECK GAP ANALYSIS — {deck_name.upper()}")
    print(f"  Commander: {commander}")
    print(f"  Cards in list: {len(deck_cards_raw)} / 99")
    print(f"{'='*60}")

    db = Database(db_path)
    db.connect()
    seed_tags(db)

    # Ensure all deck cards have functional tags derived
    deck_names_normalized = set()
    deck_infos = []

    for entry in deck_cards_raw:
        raw_name = entry["name"].strip()
        # Normalize case
        c = db.card_by_name(raw_name)
        actual_name = c.name if c else raw_name
        deck_names_normalized.add(actual_name.lower())
        if c:
            tag_functional_from_rules(actual_name, db)
        deck_infos.append(card_info(db, actual_name))

    # Separate lands from nonlands
    lands = [c for c in deck_infos if is_land(c)]
    nonlands = [c for c in deck_infos if not is_land(c)]
    cmc_values = [c["cmc"] for c in nonlands if c["cmc"] > 0]
    avg_cmc = sum(cmc_values) / len(cmc_values) if cmc_values else 0
    early_count = sum(1 for c in cmc_values if c <= 3)
    early_pct = early_count / len(nonlands) if nonlands else 0

    # Role counts
    role_counts: Counter = Counter()
    cards_by_role: dict[str, list[str]] = defaultdict(list)
    for c in deck_infos:
        for role in c["func"]:
            role_counts[role] += 1
            cards_by_role[role].append(c["name"])

    # Role status
    role_status = {}
    for role, targets in TARGETS.items():
        count = role_counts.get(role, 0)
        status = gap_status(count, targets)
        role_status[role] = (count, targets, status)

    gaps = {r: v for r, v in role_status.items() if v[2] in ("CRITICAL", "LOW")}
    excess = {r: v for r, v in role_status.items() if v[2] in ("HIGH", "SLIGHTLY HIGH")}

    # ── Print to terminal ─────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("DECK COMPOSITION")
    print(f"{'─'*60}")
    print(f"  Total cards:    {len(deck_cards_raw)} / 99 (need {99 - len(deck_cards_raw)} more)")
    print(f"  Lands:          {len(lands)}")
    print(f"  Nonland spells: {len(nonlands)}")
    print(f"  Average CMC:    {avg_cmc:.2f}")
    print(f"  CMC ≤ 3:        {early_count}/{len(nonlands)} ({early_pct:.0%})  target: ≥40%")
    if early_pct < EARLY_CURVE_TARGET:
        print(f"  ⚠  Curve is heavy — consider more low-CMC cards")

    print(f"\n{'─'*60}")
    print("ROLE COUNTS  (target ranges in parentheses)")
    print(f"{'─'*60}")
    for role in TARGETS:
        count, targets, status = role_status[role]
        lo, id_lo, id_hi, hi = targets
        icon = "⚠ " if status in ("CRITICAL", "LOW") else ("→ " if status in ("HIGH", "SLIGHTLY HIGH") else "✓ ")
        bar = "█" * count
        print(f"  {icon}{role:<22} {count:>3}  (ideal {id_lo}–{id_hi})  {bar}")

    print(f"\n{'─'*60}")
    print("GAPS (roles below target)")
    print(f"{'─'*60}")
    if not gaps:
        print("  None found.")
    for role, (count, (lo, id_lo, id_hi, hi), status) in gaps.items():
        need = id_lo - count
        print(f"  {status:<10} {role:<22} have {count}, need {id_lo}–{id_hi}  (add ~{need})")

    print(f"\n{'─'*60}")
    print("EXCESS (roles above target)")
    print(f"{'─'*60}")
    if not excess:
        print("  None found.")
    for role, (count, (lo, id_lo, id_hi, hi), status) in excess.items():
        over = count - id_hi
        print(f"  {status:<14} {role:<22} have {count}, ideal ≤{id_hi}  (could cut ~{over})")

    # ── Collection candidates for gaps ────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("COLLECTION CANDIDATES FOR GAPS")
    print(f"{'─'*60}")

    candidates_by_role = {}
    for role in PRIORITY_GAPS:
        if role in gaps or role_counts.get(role, 0) < TARGETS[role][1]:
            cands = find_candidates(db, role, deck_names_normalized)
            if cands:
                candidates_by_role[role] = cands
                count = role_counts.get(role, 0)
                ideal_lo = TARGETS[role][1]
                print(f"\n  {role} (have {count}, ideal ≥{ideal_lo}):")
                for c in cands[:5]:
                    func_str = ", ".join(sorted(c["func"] - {role}))
                    print(f"    CMC {c['cmc']}  {c['name']:<35} also: {func_str}")

    # ── CMC breakdown ─────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("MANA CURVE (nonland cards)")
    print(f"{'─'*60}")
    cmc_bucket: Counter = Counter()
    for c in deck_infos:
        if not is_land(c):
            bucket = min(c["cmc"], 7)
            cmc_bucket[bucket] += 1
    for cost in range(8):
        label = f"CMC {cost}" if cost < 7 else "CMC 7+"
        count = cmc_bucket.get(cost, 0)
        bar = "█" * count
        print(f"  {label:<8} {count:>3}  {bar}")

    # ── Write reports ─────────────────────────────────────────────────────────
    _write_gap_report(deck_name, commander, deck_infos, lands, nonlands,
                      avg_cmc, early_pct, role_status, gaps, excess,
                      candidates_by_role, cmc_bucket)
    _write_role_csv(deck_infos)
    _write_candidates_md(candidates_by_role)

    print(f"\n{'─'*60}")
    print("REPORTS WRITTEN")
    print(f"{'─'*60}")
    for f in sorted(REPORTS.glob("*")):
        print(f"  {f}")
    print()

    db.close()


def _write_gap_report(name, commander, all_cards, lands, nonlands, avg_cmc,
                      early_pct, role_status, gaps, excess, candidates, cmc_bucket):
    lines = [
        f"# Deck Gap Analysis — {name}",
        f"\n**Commander:** {commander}",
        f"**Cards in list:** {len(all_cards)} / 99",
        f"**Average CMC (nonland):** {avg_cmc:.2f}",
        f"**CMC ≤ 3:** {sum(1 for c in nonlands if c['cmc'] <= 3)}/{len(nonlands)} ({early_pct:.0%})",
        "",
        "---",
        "",
        "## Role Counts vs Targets",
        "",
        "| Role | Have | Ideal | Status |",
        "|------|------|-------|--------|",
    ]
    for role, (count, (lo, id_lo, id_hi, hi), status) in sorted(
        role_status.items(), key=lambda x: ["CRITICAL","LOW","OK","SLIGHTLY HIGH","HIGH"].index(x[1][2])
    ):
        lines.append(f"| {role} | {count} | {id_lo}–{id_hi} | {status} |")

    lines += ["", "---", "", "## Gaps to Fill", ""]
    if not gaps:
        lines.append("No critical or low roles found.")
    for role, (count, (_, id_lo, id_hi, _h), status) in gaps.items():
        lines.append(f"### {role} ({status}: have {count}, ideal {id_lo}–{id_hi})")
        if role in candidates:
            lines.append("")
            lines.append("**Collection candidates:**")
            for c in candidates[role][:6]:
                other_func = ", ".join(sorted(c["func"] - {role}))
                lines.append(f"- **{c['name']}** (CMC {c['cmc']}) — also: {other_func or '—'}")
        lines.append("")

    lines += ["", "---", "", "## Mana Curve", ""]
    for cost in range(8):
        label = f"CMC {cost}" if cost < 7 else "CMC 7+"
        count = cmc_bucket.get(cost, 0)
        bar = "█" * count
        lines.append(f"- {label}: {count}  {bar}")

    (REPORTS / "gap_report.md").write_text("\n".join(lines))


def _write_role_csv(deck_infos):
    with open(REPORTS / "role_counts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["card_name", "cmc", "type", "mechanical_tags", "functional_tags"])
        for c in sorted(deck_infos, key=lambda x: x["name"]):
            w.writerow([
                c["name"], c["cmc"], c["type"],
                ", ".join(sorted(c["mech"])),
                ", ".join(sorted(c["func"])),
            ])


def _write_candidates_md(candidates_by_role):
    lines = ["# Collection Candidates for Deck Gaps", ""]
    for role, cands in candidates_by_role.items():
        lines.append(f"## {role}")
        lines.append("")
        for c in cands:
            other_func = ", ".join(sorted(c["func"] - {role}))
            mech_str = ", ".join(sorted(c["mech"]))
            lines.append(f"### {c['name']} (CMC {c['cmc']})")
            lines.append(f"- Functional: {', '.join(sorted(c['func']))}")
            lines.append(f"- Mechanical: {mech_str}")
            lines.append("")
    (REPORTS / "candidates.md").write_text("\n".join(lines))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", default=DECK_PATH)
    parser.add_argument("--db", default=SCAN_DB)
    args = parser.parse_args()
    run_analysis(args.deck, args.db)


if __name__ == "__main__":
    main()
