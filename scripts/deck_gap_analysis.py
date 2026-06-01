#!/usr/bin/env python3
"""
deck_gap_analysis.py — Phase 6C: Role Weighting + Primary Role Classification

Answers:
  6B: "Is this deck structurally playable before I evaluate card quality?"
  6C: "How important is each role on each card — primary, secondary, or incidental?"

Produces:
  reports/deck_analysis/gap_report.md             — full diagnostic report
  reports/deck_analysis/role_counts.csv           — per-card tag data
  reports/deck_analysis/candidates.md             — collection matches for gaps
  reports/deck_analysis/structural_summary.json   — machine-readable readiness status
  reports/deck_analysis/pattern_blindspots.csv    — cards the parser doesn't understand yet
  reports/deck_analysis/weighted_role_summary.csv — per-card weighted role breakdown

Usage:
  python scripts/deck_gap_analysis.py [--deck PATH] [--db PATH]
"""

import sys
import json
import csv
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.database import Database
from mtgdeck.tags import tag_functional_from_rules, tag_mechanical, seed_tags

# ── Structural thresholds ─────────────────────────────────────────────────────
DECK_SIZE_TARGET         = 100
LAND_TARGET_MIN          = 36
LAND_TARGET_MAX          = 37
LAND_MINIMUM_FOR_EVAL    = 30   # below this, role counts are unreliable

# ── Target role ranges for Sheoldred mono-black aristocrats/reanimator ────────
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

EARLY_CURVE_TARGET = 0.40

# ── Role weight thresholds (Phase 6C) ─────────────────────────────────────────
# Derived from the confidence values stored by the functional rule engine.
# Confidence reflects how certain we are the role applies; weight reflects
# how central the role is to why you'd play this card.
#
# Thresholds are intentionally conservative: only roles at ≥ 0.88 confidence
# become "primary" automatically. Cards with all roles clustering at 0.75-0.85
# (like Archon of Cruelty) need manual overrides to identify their real purpose.
PRIMARY_THRESHOLD   = 0.88
SECONDARY_THRESHOLD = 0.70

PRIMARY_WEIGHT   = 1.00
SECONDARY_WEIGHT = 0.65
INCIDENTAL_WEIGHT = 0.35

# ── Manual role weight overrides ──────────────────────────────────────────────
# For cards where auto-classification from confidence is wrong.
# The FUNCTIONAL_RULES confidence reflects "how certain is this role" —
# NOT "how central is this role to why you play the card."
# Archon of Cruelty is the canonical example: all roles cluster at 0.75-0.85
# (all legitimately apply), but Threat is the PRIMARY reason to cast it.
#
# Keys are exact card names. Only roles the card already has can be overridden.
# Do not add roles the rule engine didn't derive — that would be misleading.
MANUAL_ROLE_WEIGHTS: dict[str, dict[str, dict]] = {
    "Archon of Cruelty": {
        # 8-mana flyer that demands an answer — everything else is ETB bonus
        "Threat":         {"priority": "primary",    "weight": PRIMARY_WEIGHT},
        "Card_Draw":      {"priority": "secondary",  "weight": SECONDARY_WEIGHT},
        "Removal":        {"priority": "secondary",  "weight": SECONDARY_WEIGHT},
        "Payoff":         {"priority": "secondary",  "weight": SECONDARY_WEIGHT},
        "Interaction":    {"priority": "secondary",  "weight": SECONDARY_WEIGHT},
        "Card_Advantage": {"priority": "incidental", "weight": INCIDENTAL_WEIGHT},
        "Engine":         {"priority": "incidental", "weight": INCIDENTAL_WEIGHT},
    },
    "Ashnod's Altar": {
        # Sacrifice outlet first, then mana engine — Enabler is the core role
        "Enabler":          {"priority": "primary", "weight": PRIMARY_WEIGHT},
        "Engine":           {"priority": "primary", "weight": PRIMARY_WEIGHT},
        "Conversion":       {"priority": "primary", "weight": PRIMARY_WEIGHT},
        "Mana_Engine":      {"priority": "primary", "weight": PRIMARY_WEIGHT},
        "Mana_Acceleration":{"priority": "secondary", "weight": SECONDARY_WEIGHT},
    },
    "Black Market": {
        # Mana engine that scales with deaths — slow, but the primary purpose IS big mana
        "Engine":            {"priority": "primary", "weight": PRIMARY_WEIGHT},
        "Mana_Engine":       {"priority": "primary", "weight": PRIMARY_WEIGHT},
        "Mana_Acceleration": {"priority": "primary", "weight": PRIMARY_WEIGHT},
        "Payoff":            {"priority": "secondary", "weight": SECONDARY_WEIGHT},
        "Conversion":        {"priority": "secondary", "weight": SECONDARY_WEIGHT},
    },
    "Gray Merchant of Asphodel": {
        # Gary is an ETB finisher — Payoff is primary, Threat is secondary
        "Finisher": {"priority": "primary",   "weight": PRIMARY_WEIGHT},
        "Payoff":   {"priority": "primary",   "weight": PRIMARY_WEIGHT},
        "Threat":   {"priority": "secondary", "weight": SECONDARY_WEIGHT},
    },
    "Skullclamp": {
        # Card draw engine — everything else is incidental to the draw loop
        "Card_Draw":      {"priority": "primary",    "weight": PRIMARY_WEIGHT},
        "Card_Advantage": {"priority": "secondary",  "weight": SECONDARY_WEIGHT},
        "Payoff":         {"priority": "secondary",  "weight": SECONDARY_WEIGHT},
        "Engine":         {"priority": "secondary",  "weight": SECONDARY_WEIGHT},
        "Conversion":     {"priority": "incidental", "weight": INCIDENTAL_WEIGHT},
    },
}

PRIORITY_GAPS = [
    "Card_Draw", "Fuel", "Mana_Acceleration", "Removal",
    "Recursion", "Engine", "Payoff", "Finisher", "Protection",
]

# ── Identity-protected cards ──────────────────────────────────────────────────
# Cards that may look inefficient but are intentionally expressive — they
# define how the deck feels to play. Do not flag for cuts without discussion.
IDENTITY_PROTECTED: set[str] = {
    "Lashwrithe",
    "Black Market",
    "Ghoulcaller Gisa",
    "Living Death",
    "Bolas's Citadel",
    "K'rrik, Son of Yawgmoth",
}

# ── Known parser blind spots ──────────────────────────────────────────────────
# Cards with 0 or missing functional roles that we KNOW should have roles.
# Status values:
#   fixed_in_6B  — pattern added in this phase; role should now be derived
#   needs_rule   — conceptually harder; rule not safe to add yet
KNOWN_BLIND_SPOTS: dict[str, dict] = {
    "Tragic Slip": {
        "expected_roles": ["Removal"],
        "suspected_gap":  "No -X/-X targeted removal pattern (fixed in 6B)",
        "status":         "fixed_in_6B",
    },
    "Dance of the Dead": {
        "expected_roles": ["Recursion"],
        "suspected_gap":  "put enchanted creature onto battlefield vs return … to battlefield (fixed in 6B)",
        "status":         "fixed_in_6B",
    },
    "Victimize": {
        "expected_roles": ["Recursion"],
        "suspected_gap":  "Graveyard context and return are in separate clauses (fixed in 6B)",
        "status":         "fixed_in_6B",
    },
    "Nyx Lotus": {
        "expected_roles": ["Mana_Acceleration"],
        "suspected_gap":  "Devotion-based mana not matched by existing Mana_Production patterns (fixed in 6B)",
        "status":         "fixed_in_6B",
    },
    "Lashwrithe": {
        "expected_roles": ["Threat", "Finisher"],
        "suspected_gap":  "Permanent_Scaling alone has no Threat/Finisher rule; scaling equipment needs its own concept",
        "status":         "needs_rule",
    },
    "Sudden Spoiling": {
        "expected_roles": ["Interaction"],
        "suspected_gap":  "Flash + split second prevention/combat blowout; no oracle pattern covers this",
        "status":         "needs_rule",
    },
    "Prowling Geistcatcher": {
        "expected_roles": ["Fuel", "Recursion"],
        "suspected_gap":  "Complex sac-trigger delayed recursion/storage; no pattern covers this",
        "status":         "needs_rule",
    },
}

DECK_PATH = "/Users/albertyan/code/mtg-pipeline-terminal/decks/bahahahah.json"
SCAN_DB   = "data/collection_scan.sqlite"
REPORTS   = Path("reports/deck_analysis")


# ── Data helpers ──────────────────────────────────────────────────────────────

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
        "name":   card.name,
        "cmc":    card.cmc or 0,
        "type":   card.type_line or "",
        "oracle": (card.oracle_text or "")[:100],
        "mech":   mech,
        "func":   func,
    }


def is_land(card_info_dict: dict) -> bool:
    return "Land" in card_info_dict.get("type", "")


def gap_status(count: int, targets: tuple) -> str:
    lo, ideal_lo, ideal_hi, hi = targets
    if count < lo:          return "CRITICAL"
    if count < ideal_lo:    return "LOW"
    if count > hi:          return "HIGH"
    if count > ideal_hi:    return "SLIGHTLY HIGH"
    return "OK"


# ── Structural validation ─────────────────────────────────────────────────────

def compute_structural_status(total_cards: int, land_count: int) -> dict:
    """
    Compute structural readiness for a Commander deck.

    A deck is not ready for final role evaluation if it has fewer than
    100 cards or fewer than LAND_MINIMUM_FOR_EVAL lands.
    """
    nonland_count = total_cards - land_count
    lands_needed  = max(0, LAND_TARGET_MIN - land_count)
    # After adding lands, how many nonlands will need to be cut to hit exactly 100?
    nonland_cuts  = max(0, nonland_count - (DECK_SIZE_TARGET - LAND_TARGET_MIN))

    is_ready = (total_cards >= DECK_SIZE_TARGET and land_count >= LAND_MINIMUM_FOR_EVAL)

    reasons = []
    if total_cards < DECK_SIZE_TARGET:
        reasons.append("deck_below_100_cards")
    if land_count < LAND_MINIMUM_FOR_EVAL:
        reasons.append("land_count_below_minimum")

    return {
        "deck_size":           total_cards,
        "deck_size_target":    DECK_SIZE_TARGET,
        "land_count":          land_count,
        "land_target_min":     LAND_TARGET_MIN,
        "land_target_max":     LAND_TARGET_MAX,
        "lands_needed":        lands_needed,
        "nonland_count":       nonland_count,
        "nonland_cuts_needed": nonland_cuts,
        "deck_readiness":      "ready_for_evaluation" if is_ready else "not_ready_for_final_evaluation",
        "role_counts_are_final": is_ready,
        "reasons":             reasons,
    }


# ── Cut candidate classification ──────────────────────────────────────────────

def classify_cut_candidates(deck_infos: list, role_status: dict) -> dict:
    """
    Classify nonland cards into 4 cut candidate categories.

    A. Unknown / unclassified  — 0 roles, no known blind-spot explanation
    B. Structural cut pressure — high CMC with over-represented roles
    C. Parser blind spots      — 0 roles but KNOWN gap; do not cut
    D. Identity-protected      — intentionally expressive; do not cut without discussion
    """
    blind_spot_names  = {k.lower() for k in KNOWN_BLIND_SPOTS}
    identity_names    = {k.lower() for k in IDENTITY_PROTECTED}

    A_unknown    = []
    B_structural = []
    C_blind_spots = []
    D_identity   = []

    for c in deck_infos:
        if is_land(c):
            continue
        name_lower = c["name"].lower()
        func_count = len(c["func"])

        # C before A: a 0-role card that IS a blind spot is C, not A
        if func_count == 0 and name_lower in blind_spot_names:
            C_blind_spots.append(c)
            continue

        # D: identity-protected regardless of role count
        if name_lower in identity_names:
            D_identity.append(c)
            continue

        # A: truly unknown (0 roles, not a blind spot, not identity-protected)
        if func_count == 0:
            A_unknown.append(c)
            continue

        # B: structural cut pressure
        # CMC 6+ with at least one over-represented role
        if c["cmc"] >= 6:
            over_roles = [
                r for r in c["func"]
                if role_status.get(r, (0, None, "OK"))[2] in ("HIGH", "SLIGHTLY HIGH")
            ]
            if over_roles:
                B_structural.append({"card": c, "over_roles": over_roles})

    B_structural.sort(key=lambda x: -x["card"]["cmc"])

    return {
        "A_unknown":    A_unknown,
        "B_structural": B_structural,
        "C_blind_spots": C_blind_spots,
        "D_identity":   D_identity,
    }


# ── Role weighting (Phase 6C) ─────────────────────────────────────────────────

def compute_weighted_roles(card_name: str, db) -> dict[str, dict]:
    """
    Compute weighted roles for a single card.

    Weight is derived from the confidence stored by the functional rule engine,
    then adjusted by MANUAL_ROLE_WEIGHTS for cards where auto-classification
    doesn't reflect the card's real purpose.

    Returns:
        {role_name: {"priority": "primary"|"secondary"|"incidental",
                     "weight": float, "confidence": float}}
    """
    func_tags = db.get_card_tags(card_name, layer="functional")
    result: dict[str, dict] = {}

    for tag in func_tags:
        role = tag["name"]
        conf = tag["confidence"]
        if conf >= PRIMARY_THRESHOLD:
            priority, weight = "primary", PRIMARY_WEIGHT
        elif conf >= SECONDARY_THRESHOLD:
            priority, weight = "secondary", SECONDARY_WEIGHT
        else:
            priority, weight = "incidental", INCIDENTAL_WEIGHT
        result[role] = {"priority": priority, "weight": weight, "confidence": conf}

    # Apply manual overrides — only for roles the rule engine already derived.
    # We never ADD roles here; that would bypass the honest gap-tracking.
    for role, override in MANUAL_ROLE_WEIGHTS.get(card_name, {}).items():
        if role in result:
            result[role].update(override)

    return result


def total_weighted_score(weighted_roles: dict[str, dict]) -> float:
    return sum(v["weight"] for v in weighted_roles.values())


# ── Collection candidate search ───────────────────────────────────────────────

def find_candidates(db, role: str, deck_names: set[str], limit: int = 8) -> list[dict]:
    """Find collection cards with the given functional role NOT in the deck."""
    placeholders = ",".join(["?" for _ in deck_names])
    cur = db.conn.cursor()
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
    for card_name, conf in rows[:limit * 2]:
        c = db.card_by_name(card_name)
        if c:
            func = {t["name"] for t in db.get_card_tags(card_name, layer="functional")}
            mech = {t["name"] for t in db.get_card_tags(card_name, layer="mechanical")}
            results.append({
                "name": card_name,
                "cmc":  c.cmc or 0,
                "type": c.type_line or "",
                "conf": conf,
                "func": func,
                "mech": mech,
            })
    results.sort(key=lambda x: (-x["conf"], x["cmc"]))
    return results[:limit]


# ── Main analysis ─────────────────────────────────────────────────────────────

def run_analysis(deck_path: str, db_path: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)

    deck          = load_deck(deck_path)
    deck_cards_raw = deck.get("cards", [])
    deck_name     = deck.get("name", "Unknown")
    commander     = deck.get("commander", "Sheoldred, Whispering One")

    print(f"\n{'='*60}")
    print(f"  DECK GAP ANALYSIS — {deck_name.upper()}")
    print(f"  Commander: {commander}")
    print(f"  Phase 6C: Role Weighting + Primary Role Classification")
    print(f"{'='*60}")

    db = Database(db_path)
    db.connect()
    seed_tags(db)

    deck_names_normalized = set()
    deck_infos = []

    for entry in deck_cards_raw:
        raw_name   = entry["name"].strip()
        c          = db.card_by_name(raw_name)
        actual_name = c.name if c else raw_name
        deck_names_normalized.add(actual_name.lower())
        if c:
            tag_mechanical(c, db)                   # re-apply patterns (picks up new 6B rules)
            tag_functional_from_rules(actual_name, db)
        deck_infos.append(card_info(db, actual_name))

    lands    = [c for c in deck_infos if is_land(c)]
    nonlands = [c for c in deck_infos if not is_land(c)]
    cmc_values   = [c["cmc"] for c in nonlands if c["cmc"] > 0]
    avg_cmc      = sum(cmc_values) / len(cmc_values) if cmc_values else 0
    early_count  = sum(1 for v in cmc_values if v <= 3)
    early_pct    = early_count / len(nonlands) if nonlands else 0

    structural = compute_structural_status(len(deck_cards_raw), len(lands))

    # Compute weighted roles for each card (Phase 6C)
    weighted_by_card: dict[str, dict] = {}
    for c in deck_infos:
        weighted_by_card[c["name"]] = compute_weighted_roles(c["name"], db)

    # Weighted deck-level counts: sum of weights for each role across all cards
    weighted_role_totals: dict[str, float] = defaultdict(float)
    for card_weighted in weighted_by_card.values():
        for role, info in card_weighted.items():
            weighted_role_totals[role] += info["weight"]

    # ── Print structural status ───────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("STRUCTURAL STATUS")
    print(f"{'─'*60}")

    if structural["deck_readiness"] == "not_ready_for_final_evaluation":
        print("  ⚠  NOT READY FOR FINAL ROLE EVALUATION")
        for r in structural["reasons"]:
            print(f"     reason: {r}")
        print("  Role counts below are DIAGNOSTIC ONLY.")
    else:
        print("  ✓  STRUCTURALLY COMPLETE — role evaluation is meaningful")

    print(f"\n  Deck size:         {structural['deck_size']} / {DECK_SIZE_TARGET}"
          f"  (need {DECK_SIZE_TARGET - structural['deck_size']} more)")
    print(f"  Lands:             {structural['land_count']}"
          f"  (target {LAND_TARGET_MIN}–{LAND_TARGET_MAX}, need {structural['lands_needed']} more)")
    print(f"  Nonlands:          {structural['nonland_count']}"
          f"  (will need ~{structural['nonland_cuts_needed']} cuts after adding lands)")

    # Role counts
    role_counts: Counter = Counter()
    cards_by_role: dict[str, list[str]] = defaultdict(list)
    for c in deck_infos:
        for role in c["func"]:
            role_counts[role] += 1
            cards_by_role[role].append(c["name"])

    role_status = {}
    for role, targets in TARGETS.items():
        count  = role_counts.get(role, 0)
        status = gap_status(count, targets)
        role_status[role] = (count, targets, status)

    gaps   = {r: v for r, v in role_status.items() if v[2] in ("CRITICAL", "LOW")}
    excess = {r: v for r, v in role_status.items() if v[2] in ("HIGH", "SLIGHTLY HIGH")}

    # ── Print role counts ─────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    label = "ROLE COUNTS (diagnostic only — deck not structurally complete)" \
        if not structural["role_counts_are_final"] else \
        "ROLE COUNTS"
    print(label)
    print(f"{'─'*60}")
    print(f"  {'Role':<22} {'Raw':>4}  {'Weighted':>8}  {'Ideal range':<12}  Status")
    print(f"  {'─'*22} {'─'*4}  {'─'*8}  {'─'*12}  {'─'*14}")
    for role in TARGETS:
        count, targets, status = role_status[role]
        lo, id_lo, id_hi, hi = targets
        w_total = weighted_role_totals.get(role, 0.0)
        icon = "⚠ " if status in ("CRITICAL", "LOW") else ("→ " if status in ("HIGH", "SLIGHTLY HIGH") else "✓ ")
        print(f"  {icon}{role:<22} {count:>4}  {w_total:>8.1f}  {id_lo}–{id_hi:<10}  {status}")

    # ── Print gaps ────────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("GAPS (roles below target)")
    print(f"{'─'*60}")
    if not gaps:
        print("  None found.")
    for role, (count, (lo, id_lo, id_hi, hi), status) in gaps.items():
        need = id_lo - count
        print(f"  {status:<10} {role:<22} have {count}, need {id_lo}–{id_hi}  (add ~{need})")

    # ── Print excess ──────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("EXCESS (roles above target)")
    print(f"{'─'*60}")
    if not excess:
        print("  None found.")
    for role, (count, (lo, id_lo, id_hi, hi), status) in excess.items():
        over = count - id_hi
        print(f"  {status:<14} {role:<22} have {count}, ideal ≤{id_hi}  (could cut ~{over})")

    # ── Collection candidates ─────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("COLLECTION CANDIDATES FOR GAPS")
    print(f"{'─'*60}")

    candidates_by_role = {}
    for role in PRIORITY_GAPS:
        if role in gaps or role_counts.get(role, 0) < TARGETS[role][1]:
            cands = find_candidates(db, role, deck_names_normalized)
            if cands:
                candidates_by_role[role] = cands
                count    = role_counts.get(role, 0)
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
        bar   = "█" * count
        print(f"  {label:<8} {count:>3}  {bar}")

    # ── Cut candidate classification ──────────────────────────────────────────
    cuts = classify_cut_candidates(deck_infos, role_status)

    print(f"\n{'─'*60}")
    print("CUT CANDIDATE CLASSIFICATION")
    print(f"{'─'*60}")

    print("\n  A. Unknown / Unclassified (0 roles, no blind-spot explanation):")
    if cuts["A_unknown"]:
        for c in cuts["A_unknown"]:
            print(f"     CMC {c['cmc']}  {c['name']}")
    else:
        print("     None.")

    print("\n  B. Structural Cut Pressure (high CMC + over-represented role):")
    if cuts["B_structural"]:
        for item in cuts["B_structural"]:
            c = item["card"]
            print(f"     CMC {c['cmc']}  {c['name']:<35}  over-roles: {', '.join(item['over_roles'])}")
    else:
        print("     None.")

    print("\n  C. Parser Blind Spots (DO NOT CUT based on current role score):")
    if cuts["C_blind_spots"]:
        for c in cuts["C_blind_spots"]:
            spot = KNOWN_BLIND_SPOTS.get(c["name"], {})
            expected = ", ".join(spot.get("expected_roles", ["?"]))
            print(f"     {c['name']:<35}  expected: {expected}  ({spot.get('status', '?')})")
    else:
        print("     None.")

    print("\n  D. Identity-Protected (intentionally expressive — discuss before cutting):")
    if cuts["D_identity"]:
        for c in cuts["D_identity"]:
            print(f"     CMC {c['cmc']}  {c['name']}")
    else:
        print("     None.")

    # ── Blind-spot validation output ──────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("BLIND SPOT VALIDATION (Phase 6B pattern fixes)")
    print(f"{'─'*60}")
    for card_name, spot in KNOWN_BLIND_SPOTS.items():
        c = db.card_by_name(card_name)
        if not c:
            print(f"  {card_name}: NOT IN DB")
            continue
        func_tags = {t["name"] for t in db.get_card_tags(card_name, layer="functional")}
        expected  = set(spot["expected_roles"])
        found     = expected & func_tags
        missing   = expected - func_tags
        status    = spot["status"]
        if status == "fixed_in_6B":
            mark = "✓" if not missing else "✗"
            print(f"  {mark} {card_name:<30}  expected {expected}  got {func_tags & (expected | {'Interaction', 'Removal', 'Recursion', 'Mana_Acceleration'})}")
        else:
            print(f"  ·  {card_name:<30}  [{status}] — still 0 roles by design, in blind spots list")

    # ── Write reports ─────────────────────────────────────────────────────────
    _write_structural_json(structural)
    _write_blindspots_csv()
    _write_gap_report(
        deck_name, commander, deck_infos, lands, nonlands,
        avg_cmc, early_pct, role_status, gaps, excess,
        candidates_by_role, cmc_bucket, structural, cuts, weighted_role_totals,
    )
    _write_role_csv(deck_infos)
    _write_candidates_md(candidates_by_role)
    _write_weighted_summary_csv(deck_infos, weighted_by_card)

    print(f"\n{'─'*60}")
    print("REPORTS WRITTEN")
    print(f"{'─'*60}")
    for f in sorted(REPORTS.glob("*")):
        print(f"  {f}")
    print()

    db.close()


# ── Report writers ────────────────────────────────────────────────────────────

def _write_structural_json(status: dict) -> None:
    (REPORTS / "structural_summary.json").write_text(
        json.dumps(status, indent=2)
    )


def _write_blindspots_csv() -> None:
    with open(REPORTS / "pattern_blindspots.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["card_name", "expected_role", "suspected_gap", "status"])
        for card, info in KNOWN_BLIND_SPOTS.items():
            for role in info["expected_roles"]:
                w.writerow([card, role, info["suspected_gap"], info["status"]])


def _write_gap_report(
    name, commander, all_cards, lands, nonlands, avg_cmc, early_pct,
    role_status, gaps, excess, candidates, cmc_bucket, structural, cuts,
    weighted_totals,
):
    readiness_label = (
        "NOT READY FOR FINAL ROLE EVALUATION"
        if not structural["role_counts_are_final"]
        else "STRUCTURALLY COMPLETE"
    )
    reasons_str = "\n".join(f"- `{r}`" for r in structural["reasons"]) or "- none"

    lines = [
        f"# Deck Gap Analysis — {name}",
        "",
        f"**Commander:** {commander}  ",
        f"**Date:** 2026-05-30  ",
        f"**Phase:** 6B — Structural Deck Diagnostics",
        "",
        "---",
        "",
        "## Structural Status",
        "",
        f"**`{readiness_label}`**",
        "",
        "| Metric | Current | Target |",
        "|--------|---------|--------|",
        f"| Deck size | {structural['deck_size']} | {DECK_SIZE_TARGET} |",
        f"| Lands | {structural['land_count']} | {LAND_TARGET_MIN}–{LAND_TARGET_MAX} |",
        f"| Nonlands | {structural['nonland_count']} | ~{DECK_SIZE_TARGET - LAND_TARGET_MIN} |",
        f"| Lands needed | {structural['lands_needed']} | — |",
        f"| Nonland cuts after adding lands | ~{structural['nonland_cuts_needed']} | — |",
        "",
    ]

    if not structural["role_counts_are_final"]:
        lines += [
            "> **Note:** Role counts below are DIAGNOSTIC ONLY.",
            "> They are inflated because the deck has too many nonlands relative to lands.",
            "> Do not treat them as final until the deck reaches 100 cards with 36+ lands.",
            "",
            "Reasons:",
            "",
            reasons_str,
            "",
        ]

    diag_note = " *(Diagnostic only)*" if not structural["role_counts_are_final"] else ""
    lines += [
        "---",
        "",
        f"## Role Counts vs Targets{diag_note}",
        "",
        "Raw count = how many deck cards have this role (any priority).  ",
        "Weighted = sum of role weights (primary=1.0, secondary=0.65, incidental=0.35).  ",
        "Weighted is a more honest picture of role depth.",
        "",
        "| Role | Raw | Weighted | Ideal | Status |",
        "|------|-----|----------|-------|--------|",
    ]
    for role, (count, (lo, id_lo, id_hi, hi), status) in sorted(
        role_status.items(),
        key=lambda x: ["CRITICAL", "LOW", "OK", "SLIGHTLY HIGH", "HIGH"].index(x[1][2])
    ):
        w = weighted_totals.get(role, 0.0)
        lines.append(f"| {role} | {count} | {w:.1f} | {id_lo}–{id_hi} | {status} |")

    # Gaps
    lines += ["", "---", "", "## Gaps to Fill", ""]
    if not gaps:
        lines.append("No critical or low roles found.")
    else:
        for role, (count, (_, id_lo, id_hi, _h), status) in gaps.items():
            lines.append(f"### {role} ({status}: have {count}, ideal {id_lo}–{id_hi})")
            if role in candidates:
                lines.append("")
                lines.append("**Collection candidates:**")
                for c in candidates[role][:6]:
                    other_func = ", ".join(sorted(c["func"] - {role}))
                    lines.append(f"- **{c['name']}** (CMC {c['cmc']}) — also: {other_func or '—'}")
            lines.append("")

    # Curve
    lines += ["", "---", "", "## Mana Curve (nonland spells)", ""]
    for cost in range(8):
        label = f"CMC {cost}" if cost < 7 else "CMC 7+"
        count = cmc_bucket.get(cost, 0)
        bar   = "█" * count
        lines.append(f"- {label}: {count}  {bar}")

    # Cut candidates
    lines += [
        "", "---", "", "## Cut Candidate Classification", "",
        "Cards are sorted into four categories. A 0-role card is never a cut candidate",
        "until it has passed through the blind-spot check.",
        "",
    ]

    lines.append("### A. Unknown / Unclassified")
    lines.append("")
    lines.append("Cards with 0 functional roles and no known explanation.")
    lines.append("These are candidates for either a cut or a new rule.")
    lines.append("")
    if cuts["A_unknown"]:
        lines.append("| Card | CMC |")
        lines.append("|------|-----|")
        for c in cuts["A_unknown"]:
            lines.append(f"| {c['name']} | {c['cmc']} |")
    else:
        lines.append("None.")
    lines.append("")

    lines.append("### B. Structural Cut Pressure")
    lines.append("")
    lines.append("Cards that may need to be cut because the deck needs lands — not because they are bad.")
    lines.append("Logic: CMC 6+ and at least one over-represented role.")
    lines.append("")
    if cuts["B_structural"]:
        lines.append("| Card | CMC | Over-represented roles |")
        lines.append("|------|-----|------------------------|")
        for item in cuts["B_structural"]:
            c = item["card"]
            lines.append(f"| {c['name']} | {c['cmc']} | {', '.join(item['over_roles'])} |")
    else:
        lines.append("None.")
    lines.append("")

    lines.append("### C. Parser Blind Spots")
    lines.append("")
    lines.append("**DO NOT cut based on current role score.**")
    lines.append("The system does not understand these cards yet.")
    lines.append("")
    if cuts["C_blind_spots"]:
        lines.append("| Card | Expected roles | Gap | Status |")
        lines.append("|------|----------------|-----|--------|")
        for c in cuts["C_blind_spots"]:
            spot = KNOWN_BLIND_SPOTS.get(c["name"], {})
            expected = ", ".join(spot.get("expected_roles", ["?"]))
            lines.append(f"| {c['name']} | {expected} | {spot.get('suspected_gap', '?')} | {spot.get('status', '?')} |")
    else:
        lines.append("None. (All previously known blind spots have been fixed.)")
    lines.append("")

    lines.append("### D. Identity-Protected Cards")
    lines.append("")
    lines.append("Cards that may look inefficient but are intentionally expressive.")
    lines.append("They define how the deck feels to play. Do not cut without discussion.")
    lines.append("")
    if cuts["D_identity"]:
        lines.append("| Card | CMC | Functional tags |")
        lines.append("|------|-----|-----------------|")
        for c in cuts["D_identity"]:
            func_str = ", ".join(sorted(c["func"])) or "*(parser blind spot)*"
            lines.append(f"| {c['name']} | {c['cmc']} | {func_str} |")
    else:
        lines.append("None.")
    lines.append("")

    # Parser blind spots appendix
    lines += [
        "---", "",
        "## Parser Blind Spots (full list)", "",
        "Cards the system does not fully understand.",
        "Fixed in this phase are tagged `fixed_in_6B`. Still-open gaps are `needs_rule`.",
        "",
        "| Card | Expected role | Suspected gap | Status |",
        "|------|---------------|---------------|--------|",
    ]
    for card, info in KNOWN_BLIND_SPOTS.items():
        expected = ", ".join(info["expected_roles"])
        lines.append(f"| {card} | {expected} | {info['suspected_gap']} | `{info['status']}` |")

    (REPORTS / "gap_report.md").write_text("\n".join(lines))


def _write_weighted_summary_csv(deck_infos: list, weighted_by_card: dict) -> None:
    """
    Write per-card weighted role breakdown.

    Columns:
      card_name, mana_value, primary_roles, secondary_roles, incidental_roles,
      total_weighted_score, raw_role_count

    total_weighted_score = sum(weight for each role). Lets you rank cards by
    functional density rather than raw role count.
    """
    with open(REPORTS / "weighted_role_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "card_name", "mana_value", "is_land",
            "primary_roles", "secondary_roles", "incidental_roles",
            "total_weighted_score", "raw_role_count",
        ])
        for c in sorted(deck_infos, key=lambda x: x["name"]):
            weighted = weighted_by_card.get(c["name"], {})
            primary   = sorted(r for r, v in weighted.items() if v["priority"] == "primary")
            secondary = sorted(r for r, v in weighted.items() if v["priority"] == "secondary")
            incidental = sorted(r for r, v in weighted.items() if v["priority"] == "incidental")
            score = total_weighted_score(weighted)
            w.writerow([
                c["name"], c["cmc"], "yes" if is_land(c) else "no",
                "; ".join(primary),
                "; ".join(secondary),
                "; ".join(incidental),
                f"{score:.2f}",
                len(c["func"]),
            ])


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
            mech_str   = ", ".join(sorted(c["mech"]))
            lines.append(f"### {c['name']} (CMC {c['cmc']})")
            lines.append(f"- Functional: {', '.join(sorted(c['func']))}")
            lines.append(f"- Mechanical: {mech_str}")
            lines.append("")
    (REPORTS / "candidates.md").write_text("\n".join(lines))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", default=DECK_PATH)
    parser.add_argument("--db",   default=SCAN_DB)
    args = parser.parse_args()
    run_analysis(args.deck, args.db)


if __name__ == "__main__":
    main()
