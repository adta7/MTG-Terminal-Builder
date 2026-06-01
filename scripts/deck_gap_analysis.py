#!/usr/bin/env python3
"""
deck_gap_analysis.py — Phase 6E: Primary Role Correction / Archetype Role Overrides

Answers:
  6B: "Is this deck structurally playable before I evaluate card quality?"
  6C: "How important is each role on each card — primary, secondary, or incidental?"
  6D: "How do weighted targets compare to raw counts? What's the completion plan?"
  6E: "Are archetype-core cards correctly classified as primary role holders?"
  6F: "What does cutting each card cost the deck? (cut_cost / role scarcity / curve)"
  6G: "Cut verdict bands — strong / borderline / near-zero / needs_role_review"
  7:  "Deck completion simulation — structural path to 100 cards"
  8:  "Preference-weighted cut review — player identity pillars guide Tier 2 ranking"

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

# ── Weighted target ranges (Phase 6D) ─────────────────────────────────────────
# These are separate from the raw TARGETS because weighted totals use a
# different scale. A deck with 14 Engine cards at 0.65 avg weight ≈ 9.1 weighted
# — which is inside the weighted ideal range even if raw looks inflated.
#
# Rough calibration: weighted ideal ≈ raw ideal × expected avg weight per role.
# Engine cards average ~0.65 (many secondary hits) → raw ideal 10-16 → weighted ~6.5-10.4.
# Recursion cards average ~0.90 (mostly primary) → raw ideal 6-9 → weighted ~5.4-8.1.
#
# Numbers are intentionally approximate. The value is in seeing which roles have
# deep primary coverage vs thin incidental coverage.
WEIGHTED_TARGETS: dict[str, tuple[float, float]] = {
    "Mana_Acceleration": (8.0, 12.0),
    "Mana_Engine":       (2.0,  5.0),
    "Card_Draw":         (7.0, 11.0),
    "Removal":           (8.0, 12.0),
    "Engine":            (8.0, 14.0),
    "Payoff":            (5.0,  9.0),
    "Fuel":              (4.0,  7.0),
    "Recursion":         (6.0, 10.0),
    "Conversion":        (4.0,  7.0),
    "Finisher":          (3.0,  6.0),
    "Enabler":           (5.5, 10.0),
    "Interaction":       (5.0,  8.0),
    "Threat":            (5.0,  9.0),
    "Setup":             (3.5,  6.5),
    "Protection":        (2.0,  4.0),
}

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

# ── Primary role overrides (Phase 6E) ────────────────────────────────────────
# For cards where the rule-engine confidence is correct (the role IS present),
# but the confidence value clusters at 0.80-0.85 — just below the 0.88 primary
# threshold — even though in this archetype the role IS primary.
#
# MANUAL_ROLE_WEIGHTS handles cases where the auto-classification is *wrong*
# (e.g., Archon of Cruelty where Threat should be primary but isn't).
# PRIMARY_ROLE_OVERRIDES handles archetype-specific promotion: the role is real,
# the deck cares about it primarily, and the threshold fails to capture that.
#
# Rule: only promote roles the card already has (from the rule engine).
# Do not add new roles here — that bypasses honest gap tracking.
#
# Archetype context: mono-black recursive midrange aristocrats.
#   - death triggers = primary engine
#   - forced sacrifice effects = primary removal / interaction
#   - death → token = primary fuel
#   - free sacrifice outlets = primary enabler
PRIMARY_ROLE_OVERRIDES: dict[str, list[str]] = {
    # Engine/control pillar — every opponent creature death forces a sacrifice.
    # This is what makes the aristocrats plan oppressive, not just value-generating.
    "Grave Pact":         ["Engine", "Removal", "Interaction"],
    "Butcher of Malakir": ["Engine", "Removal", "Interaction", "Threat"],

    # Death → Treasure. With constant creature deaths this is a primary mana engine.
    "Pitiless Plunderer": ["Engine", "Payoff", "Fuel"],

    # 6/6 deathtouch + immediate Zombie tokens. Primary threat that doubles as fuel.
    "Grave Titan":        ["Threat", "Fuel"],

    # Death → Zombie token. Pure primary fuel in a deck built on creature deaths.
    "Ghoulish Procession": ["Fuel"],

    # ETB forced sacrifice = primary removal spell. Brings value via discard too.
    "Plaguecrafter":      ["Removal", "Interaction"],

    # Smaller Plaguecrafter analogue — ETB forced sacrifice is primary removal.
    "Accursed Marauder":  ["Removal", "Interaction"],

    # Free sacrifice outlet — in aristocrats, Enabler is the PRIMARY function.
    "Woe Strider":        ["Enabler"],

    # Upkeep token generators — in aristocrats, these are dedicated fuel sources.
    # A 1/1 deathtouch snake / 2/2 zombie every upkeep is primary Fuel, not incidental.
    "Ophiomancer":                    ["Fuel"],
    "Jadar, Ghoulcaller of Nephalia": ["Fuel"],

    # Instant-speed card draw / conversion — the sacrifice is a cost, not coincidence.
    # These are played for the draw; they smooth early turns and refuel mid-combo.
    "Deadly Dispute":     ["Card_Draw"],
    "Plumb the Forbidden":["Card_Draw", "Conversion"],
    "Disciple of Bolas":  ["Card_Draw"],

    # Aristocrats payoff: pings each opponent on any death/graveyard event.
    # The functional rule (Death_Trigger + Damage_Effect → Payoff 0.85) gives Payoff,
    # but at secondary confidence. Promote to primary — he IS the payoff card.
    "Syr Konrad, the Grim": ["Payoff"],
}

# ── Cut cost constants (Phase 6F) ────────────────────────────────────────────
# Cut pressure asks "why might we remove this card?"
# Cut cost asks "what does the deck lose by removing it?"
# net_cut_score = cut_pressure - cut_cost. Only cards with net > 0 appear in tiers.

EARLY_CURVE_PROTECTION: dict[int, float] = {
    1: 2.0,   # CMC 1: near-irreplaceable early efficiency
    2: 1.5,   # CMC 2: valuable curve piece; losing one hurts early game
    3: 0.75,  # CMC 3: moderate protection
}

SCARCITY_PENALTY: dict[str, float] = {
    "W_CRITICAL":      3.0,   # role is dangerously thin — very high cost to cut from it
    "W_LOW":           2.0,   # role is below target — cutting from it hurts
    "W_OK":            0.0,   # role is healthy — no scarcity penalty
    "W_SLIGHTLY_HIGH": 0.0,   # over-target — removing one card is fine
    "W_HIGH":          0.0,   # well over-target — removing is encouraged
}

# ── Cut verdict bands (Phase 6G) ──────────────────────────────────────────────
# Do not present all positive-net cards as equally safe cuts.
# Bands reflect confidence in the cut recommendation.
CUT_VERDICT_STRONG     = "strong_cut_candidate"   # net >= 1.0
CUT_VERDICT_BORDERLINE = "borderline_cut_candidate" # 0.25 <= net < 1.0
CUT_VERDICT_NEAR_ZERO  = "near_zero_review"        # 0 < net < 0.25
CUT_VERDICT_ROLE_REVIEW = "needs_role_review"      # 0 primary roles but fds > 1.0 — may be misclassified
CUT_VERDICT_SKIP       = "do_not_cut_by_model"     # net <= 0

# FDS threshold above which a 0-primary card is suspicious enough to flag for role review
# rather than being presented as a safe cut.
# 1.0 caught too many false positives (pure draw spells like Read the Bones have FDS 1.30
# from Card_Draw + Card_Advantage — both are essentially the same function).
# 1.5 targets genuinely ambiguous cards: Mind Stone (1.95, mana rock or draw?),
# Abnormal Endurance (1.55, protection or fuel?).
ROLE_REVIEW_FDS_THRESHOLD = 1.5

# ── Primary role validation (Phase 6E) ───────────────────────────────────────
# Cards that must NOT appear in Tier 1 cut pressure after overrides are applied.
# A failure here means PRIMARY_ROLE_OVERRIDES is incomplete or wrong.
PRIMARY_ROLE_VALIDATION: dict[str, str] = {
    "Grave Pact":         "Primary engine/control pillar in aristocrats",
    "Pitiless Plunderer": "Core engine/conversion — death → Treasure is primary",
    "Grave Titan":        "Primary threat + fuel generator",
    "Butcher of Malakir": "Primary threat/oppression — flying 5/4 + forced sac",
    "Ghoulish Procession":"Primary fuel — death → token is its entire purpose",
    "Plaguecrafter":      "Primary removal — ETB forced sacrifice",
    "Accursed Marauder":  "Primary removal — ETB forced sacrifice",
    "Woe Strider":        "Primary enabler — free sacrifice outlet",
    "Ophiomancer":        "Primary fuel — snake token every upkeep",
    "Jadar, Ghoulcaller of Nephalia": "Primary fuel — zombie token on sacrifice turns",
    "Deadly Dispute":     "Primary card draw — instant-speed draw 2 with sacrifice cost",
    "Plumb the Forbidden":"Primary card draw + conversion — sacrifice X to draw X at instant speed",
    "Disciple of Bolas":  "Primary card draw — ETB sacrifice to draw X",
    "Syr Konrad, the Grim": "Primary payoff — pings each opponent on every creature death/graveyard event",
}

# ── Preference profile (Phase 8) ──────────────────────────────────────────────
# Maps each deck identity pillar to a weight.
# 0.0 = don't care / 1.0 = moderate preserve / 2.0 = strong preserve.
# "lower_curve_aggressively" adds to cut_pressure instead of cut_cost.
#
# These weights reflect the known deck philosophy (from CLAUDE.md and prior sessions):
#   - sacrifice engines, recursion, and reanimation ARE the deck's identity
#   - big black creatures and apex threats are desirable but not untouchable
#   - mana scaling is secondary to the core engine/recursion plan
DEFAULT_PREFERENCES: dict[str, float] = {
    "preserve_big_mythic_threats":  0.8,   # apex threats valued but not sacrosanct
    "preserve_sacrifice_control":   1.5,   # edict/forced-sac effects = core identity
    "preserve_draw_consistency":    1.0,   # draw smoothing is important early
    "preserve_mana_explosion":      0.8,   # mana scaling is good but secondary
    "preserve_token_fuel_density":  1.2,   # token generators = renewable fuel
    "preserve_recursion_density":   1.5,   # recursion IS the deck — protect it
    "lower_curve_aggressively":     0.5,   # mild curve pressure (not aggressive)
}

# Maps functional roles to preference categories.
# A card's primary roles are checked here to determine how much extra cut_cost
# is added by the player's preference weights.
ROLE_PREFERENCE_MAP: dict[str, str] = {
    "Threat":            "preserve_big_mythic_threats",
    "Finisher":          "preserve_big_mythic_threats",
    "Finisher_Support":  "preserve_big_mythic_threats",
    "Removal":           "preserve_sacrifice_control",
    "Interaction":       "preserve_sacrifice_control",
    "Protection":        "preserve_sacrifice_control",
    "Card_Draw":         "preserve_draw_consistency",
    "Card_Advantage":    "preserve_draw_consistency",
    "Setup":             "preserve_draw_consistency",
    "Mana_Acceleration": "preserve_mana_explosion",
    "Mana_Engine":       "preserve_mana_explosion",
    "Conversion":        "preserve_mana_explosion",
    "Fuel":              "preserve_token_fuel_density",
    "Payoff":            "preserve_token_fuel_density",
    "Recursion":         "preserve_recursion_density",
    "Enabler":           "preserve_recursion_density",
    "Engine":            "preserve_sacrifice_control",  # engines in this deck are edict-based
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

    # Apply manual weight overrides — only for roles the rule engine already derived.
    for role, override in MANUAL_ROLE_WEIGHTS.get(card_name, {}).items():
        if role in result:
            result[role].update(override)

    # Apply archetype-specific primary role promotions.
    # Promotes existing roles to primary without changing other attributes.
    for role in PRIMARY_ROLE_OVERRIDES.get(card_name, []):
        if role in result:
            result[role]["priority"] = "primary"
            result[role]["weight"]   = PRIMARY_WEIGHT

    return result


def functional_density_score(weighted_roles: dict[str, dict]) -> float:
    """
    Sum of role weights for a card. Measures functional density, not card power.

    A card with one primary job (Blood Artist, score 1.65) can be more essential
    than a card with many secondary jobs. Do not use this to rank cards by quality.
    Use it to compare cards with similar roles or to identify incidental-heavy cards
    that add to raw counts without adding meaningful role depth.
    """
    return sum(v["weight"] for v in weighted_roles.values())


def weighted_gap_status(weighted_total: float, targets: tuple[float, float]) -> str:
    lo, hi = targets
    if weighted_total < lo * 0.75:  return "W_CRITICAL"
    if weighted_total < lo:          return "W_LOW"
    if weighted_total > hi * 1.25:   return "W_HIGH"
    if weighted_total > hi:          return "W_SLIGHTLY_HIGH"
    return "W_OK"


def model_confidence(net: float, verdict: str, primary_count: int) -> str:
    """
    How confident the model is in a cut recommendation.

      high   — net >= 1.0, 0 primary roles, not flagged for role review
      medium — net >= 0.25, or Tier 2 card with clear structural pressure
      low    — near-zero net, needs_role_review, or Tier 2 with high primary density
    """
    if verdict == CUT_VERDICT_ROLE_REVIEW:
        return "low"
    if net >= 1.0 and primary_count == 0:
        return "high"
    if net >= 0.25:
        return "medium"
    return "low"


def cut_verdict(net: float, primary_count: int, fds: float) -> str:
    """
    Assign a cut verdict band to a card.

    needs_role_review takes priority over net-based bands: if a card has 0 primary
    roles but high FDS, the system may be misclassifying it — do not present it as a
    safe cut until the role review is resolved.
    """
    if primary_count == 0 and fds > ROLE_REVIEW_FDS_THRESHOLD:
        return CUT_VERDICT_ROLE_REVIEW
    if net >= 1.0:
        return CUT_VERDICT_STRONG
    if net >= 0.25:
        return CUT_VERDICT_BORDERLINE
    if net > 0:
        return CUT_VERDICT_NEAR_ZERO
    return CUT_VERDICT_SKIP


def compute_role_priority_breakdown(
    deck_infos: list,
    weighted_by_card: dict,
) -> dict[str, dict]:
    """
    For each role in TARGETS, compute the primary/secondary/incidental card counts
    and the weighted total.

    Returns:
        {role: {"raw": int, "weighted": float, "primary": int,
                "secondary": int, "incidental": int, "w_status": str}}
    """
    breakdown: dict[str, dict] = {}
    for role in TARGETS:
        raw        = 0
        weighted   = 0.0
        primary    = 0
        secondary  = 0
        incidental = 0
        for c in deck_infos:
            wr = weighted_by_card.get(c["name"], {})
            if role in wr:
                raw += 1
                info = wr[role]
                weighted += info["weight"]
                if info["priority"] == "primary":
                    primary += 1
                elif info["priority"] == "secondary":
                    secondary += 1
                else:
                    incidental += 1
        breakdown[role] = {
            "raw":        raw,
            "weighted":   weighted,
            "primary":    primary,
            "secondary":  secondary,
            "incidental": incidental,
            "w_status":   weighted_gap_status(weighted, WEIGHTED_TARGETS[role]),
        }
    return breakdown


def compute_cut_pressure(
    deck_infos: list,
    weighted_by_card: dict,
    commander: str = "",
    role_breakdown: dict | None = None,
) -> list[dict]:
    """
    Rank nonland cards by net_cut_score = cut_pressure - cut_cost.

    cut_pressure: why the deck wants to remove this card.
      - +2 per CMC above 5 (structural pressure from land needs)
      - +1 if no primary roles
      - +0.3 per secondary role

    cut_cost: what the deck loses by removing this card.
      - +EARLY_CURVE_PROTECTION[cmc] for CMC 1-3
      - +SCARCITY_PENALTY[w_status] × role_weight for each scarce role

    Only cards with net_cut_score > 0 appear in Tier 1 or Tier 2.
    Identity-protected and unresolved blind-spot cards go to Tier 3.
    """
    # Only unresolved blind spots (needs_rule) are protected — fixed blind spots
    # (fixed_in_6B) are now properly tagged and evaluated like any other card.
    unresolved_blind_spot_names = {
        k.lower() for k, v in KNOWN_BLIND_SPOTS.items()
        if v.get("status") == "needs_rule"
    }
    identity_names = {k.lower() for k in IDENTITY_PROTECTED}

    tier1 = []   # safest: 0 primary roles, positive cut pressure
    tier2 = []   # viable: 1+ primary roles, positive cut pressure (CMC ≥ 5)
    tier3 = []   # protected: identity or unresolved blind spot

    commander_lower = commander.lower()

    for c in deck_infos:
        if is_land(c):
            continue
        name_lower = c["name"].lower()
        if commander_lower and name_lower == commander_lower:
            continue   # never recommend cutting the commander
        wr         = weighted_by_card.get(c["name"], {})
        primary_count   = sum(1 for v in wr.values() if v["priority"] == "primary")
        secondary_count = sum(1 for v in wr.values() if v["priority"] == "secondary")
        fds             = functional_density_score(wr)

        if name_lower in unresolved_blind_spot_names or name_lower in identity_names:
            reason = "blind_spot" if name_lower in unresolved_blind_spot_names else "identity_protected"
            tier3.append({
                "name": c["name"], "cmc": c["cmc"],
                "primary": primary_count, "fds": fds,
                "reason": reason,
            })
            continue

        pressure = 0.0
        pressure += max(0, c["cmc"] - 5) * 2.0
        pressure += 1.0 if primary_count == 0 else 0.0
        pressure += secondary_count * 0.3

        # cut_cost: what the deck loses by removing this card
        cut_cost = EARLY_CURVE_PROTECTION.get(c["cmc"], 0.0)

        if role_breakdown:
            for role, info in wr.items():
                w_status = role_breakdown.get(role, {}).get("w_status", "W_OK")
                scarcity = SCARCITY_PENALTY.get(w_status, 0.0)
                # Weight the penalty by how much this card contributes to the role
                cut_cost += scarcity * info["weight"]

        net        = pressure - cut_cost
        verdict    = cut_verdict(net, primary_count, fds)
        confidence = model_confidence(net, verdict, primary_count)

        entry = {
            "name": c["name"], "cmc": c["cmc"],
            "primary": primary_count, "secondary": secondary_count,
            "fds": fds, "pressure": pressure, "cut_cost": cut_cost,
            "net": net, "verdict": verdict, "confidence": confidence,
        }
        if primary_count == 0 and net > 0:
            tier1.append(entry)
        elif primary_count > 0 and net > 0 and c["cmc"] >= 5:
            # Tier 2 confidence: structural pressure drives the recommendation,
            # but primary roles make it costlier. Net > 4 = medium; lower = low.
            t2_confidence = "medium" if net >= 4.0 else "low"
            tier2.append({**entry, "confidence": t2_confidence})

    tier1.sort(key=lambda x: (-x["net"], -x["cmc"]))
    tier2.sort(key=lambda x: (-x["net"], -x["cmc"]))

    return tier1, tier2, tier3


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
    print(f"  Phase 8: Preference-Weighted Cut Review")
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

    # Phase 6D: priority breakdown and cut pressure
    role_breakdown = compute_role_priority_breakdown(deck_infos, weighted_by_card)
    cut_tier1, cut_tier2, cut_tier3 = compute_cut_pressure(
        deck_infos, weighted_by_card, commander, role_breakdown
    )

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

    # ── Primary role breakdown ────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("ROLE PRIORITY BREAKDOWN  (Phase 6D weighted targets)")
    print(f"{'─'*60}")
    print(f"  {'Role':<22} {'Primary':>7} {'Sec':>5} {'Inc':>5}  {'Wtd Total':>9}  {'Wtd Target':>12}  W-Status")
    print(f"  {'─'*22} {'─'*7} {'─'*5} {'─'*5}  {'─'*9}  {'─'*12}  {'─'*14}")
    for role in TARGETS:
        bd = role_breakdown[role]
        wt_lo, wt_hi = WEIGHTED_TARGETS[role]
        print(
            f"  {role:<22} {bd['primary']:>7} {bd['secondary']:>5} {bd['incidental']:>5}"
            f"  {bd['weighted']:>9.1f}  {wt_lo:.1f}–{wt_hi:<9.1f}  {bd['w_status']}"
        )

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

    # ── Completion planner ────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("COMPLETION PLANNER (Phase 6F — cut cost aware)")
    print(f"{'─'*60}")
    print(f"  Add {structural['lands_needed']} lands.  Cut {structural['nonland_cuts_needed']} nonlands.")
    print()
    print("  Tier 1 — Candidate cuts (0 primary roles) — split by verdict band:")
    print(f"  {'Card':<35} {'CMC':>3}  {'net':>5}  Verdict")
    if cut_tier1:
        # Group by verdict band
        bands = {
            CUT_VERDICT_STRONG:     ("  A. Strong cut candidates (net ≥ 1.0):",     []),
            CUT_VERDICT_BORDERLINE: ("  B. Borderline cut candidates (0.25-1.0):", []),
            CUT_VERDICT_NEAR_ZERO:  ("  C. Near-zero review (0-0.25):",             []),
            CUT_VERDICT_ROLE_REVIEW:("  D. Needs role review (high FDS, 0 primary):",[]),
        }
        for item in cut_tier1:
            v = item["verdict"]
            if v in bands:
                bands[v][1].append(item)
        for verdict_key, (label, items) in bands.items():
            if items:
                print(f"\n{label}")
                for item in items:
                    print(f"    {item['name']:<35} {item['cmc']:>3}  {item['net']:>5.2f}  [pressure={item['pressure']:.2f} cost={item['cut_cost']:.2f} fds={item['fds']:.2f}]")
    else:
        print("    None. (All 0-role cards are blind spots or identity-protected.)")
    print()
    print("  Tier 2 — Viable cuts (1+ primary roles, only if Tier 1 exhausted):")
    if cut_tier2:
        for item in cut_tier2[:6]:
            print(f"    {item['name']:<35} {item['cmc']:>3}  primary={item['primary']}  net={item['net']:.2f}  fds={item['fds']:.2f}")
    else:
        print("    None.")
    print()
    print("  Tier 3 — Do not cut (protected):")
    for item in cut_tier3:
        print(f"    [{item['reason']}]  {item['name']}")

    # ── Primary role validation (Phase 6E) ───────────────────────────────────
    tier1_names = {item["name"].lower() for item in cut_tier1}
    print(f"\n{'─'*60}")
    print("PRIMARY ROLE VALIDATION (Phase 6E)")
    print(f"{'─'*60}")
    print("  Checks that archetype-core cards are NOT in Tier 1 cut pressure.")
    all_pass = True
    for card_name, reason in PRIMARY_ROLE_VALIDATION.items():
        wr = weighted_by_card.get(card_name, {})
        primary_roles = [r for r, v in wr.items() if v["priority"] == "primary"]
        in_tier1 = card_name.lower() in tier1_names
        if in_tier1 or not primary_roles:
            print(f"  ✗ {card_name:<35}  NO primary roles — still misclassified")
            all_pass = False
        else:
            print(f"  ✓ {card_name:<35}  primary: {', '.join(sorted(primary_roles))}")
    if all_pass:
        print("\n  All validation checks passed. Cut tiers are archetype-aware.")
    else:
        print("\n  ⚠ Some cards still misclassified. Expand PRIMARY_ROLE_OVERRIDES.")

    # ── Write reports ─────────────────────────────────────────────────────────
    _write_structural_json(structural)
    _write_blindspots_csv()
    _write_gap_report(
        deck_name, commander, deck_infos, lands, nonlands,
        avg_cmc, early_pct, role_status, gaps, excess,
        candidates_by_role, cmc_bucket, structural, cuts, weighted_role_totals,
        role_breakdown,
    )
    _write_role_csv(deck_infos)
    _write_candidates_md(candidates_by_role)
    _write_weighted_summary_csv(deck_infos, weighted_by_card)
    _write_weighted_role_targets_csv(role_breakdown)
    _write_primary_role_summary_csv(role_breakdown)
    _write_completion_plan_md(structural, cut_tier1, cut_tier2, cut_tier3, role_breakdown, all_pass)
    _write_deck_completion_simulation_md(
        structural, cut_tier1, cut_tier2, cut_tier3, weighted_by_card, role_breakdown
    )
    # Phase 8: preference-weighted cut review for the human-required Tier 2 cuts
    sim_confident = sum(
        1 for c in cut_tier1
        if c["verdict"] in (CUT_VERDICT_STRONG, CUT_VERDICT_BORDERLINE)
    )
    cuts_still_needed = max(0, structural["nonland_cuts_needed"] - sim_confident)
    tier2_adjusted = compute_preference_adjusted_cuts(
        cut_tier2, weighted_by_card, DEFAULT_PREFERENCES
    )
    _write_preference_cut_review(tier2_adjusted, DEFAULT_PREFERENCES, cuts_still_needed)

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
    weighted_totals, role_breakdown,
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
        "- **Raw** = cards with this role (any priority)",
        "- **Primary** = cards where this is a primary role (weight 1.0)",
        "- **Weighted** = sum of weights (primary=1.0, secondary=0.65, incidental=0.35)",
        "- **W-Status** = weighted total vs weighted target range",
        "",
        "| Role | Raw | Primary | Weighted | Ideal (raw) | W-Target | Status | W-Status |",
        "|------|-----|---------|----------|-------------|----------|--------|----------|",
    ]
    for role, (count, (lo, id_lo, id_hi, hi), status) in sorted(
        role_status.items(),
        key=lambda x: ["CRITICAL", "LOW", "OK", "SLIGHTLY HIGH", "HIGH"].index(x[1][2])
    ):
        w   = weighted_totals.get(role, 0.0)
        bd  = role_breakdown.get(role, {})
        pri = bd.get("primary", 0)
        wt_lo, wt_hi = WEIGHTED_TARGETS.get(role, (0, 0))
        w_status = bd.get("w_status", "—")
        lines.append(
            f"| {role} | {count} | {pri} | {w:.1f} | {id_lo}–{id_hi} "
            f"| {wt_lo:.1f}–{wt_hi:.1f} | {status} | {w_status} |"
        )

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
            score = functional_density_score(weighted)
            w.writerow([
                c["name"], c["cmc"], "yes" if is_land(c) else "no",
                "; ".join(primary),
                "; ".join(secondary),
                "; ".join(incidental),
                f"{score:.2f}",
                len(c["func"]),
            ])


def _write_deck_completion_simulation_md(
    structural: dict,
    tier1: list, tier2: list, tier3: list,
    weighted_by_card: dict,
    role_breakdown: dict,
) -> None:
    """
    Structural path from the current 87-card incomplete deck to a complete 100-card deck.

    The simulation shows what the model IS confident about, what it is uncertain about,
    and where human judgment is required. It is not a final decklist.
    """
    cuts_needed   = structural["nonland_cuts_needed"]
    lands_needed  = structural["lands_needed"]

    # Split tier1 into verdict bands for the simulation
    strong     = [c for c in tier1 if c["verdict"] == CUT_VERDICT_STRONG]
    borderline = [c for c in tier1 if c["verdict"] == CUT_VERDICT_BORDERLINE]
    near_zero  = [c for c in tier1 if c["verdict"] == CUT_VERDICT_NEAR_ZERO]
    role_review = [c for c in tier1 if c["verdict"] == CUT_VERDICT_ROLE_REVIEW]

    confident_cuts    = len(strong)
    borderline_cuts   = len(borderline)
    human_needed      = cuts_needed - confident_cuts  # minimum human decision cuts
    human_if_border   = cuts_needed - confident_cuts - borderline_cuts

    lines = [
        "# Deck Completion Simulation",
        "",
        "> **This is a structural path to completion, not a final decklist.**",
        "> The model shows where it is confident, where it is uncertain, and where",
        "> human judgment is required before any card is removed.",
        ">",
        f"> **Model limit:** This model can suggest {confident_cuts + borderline_cuts} of "
        f"{cuts_needed} needed cuts with medium-or-higher confidence.",
        f"> The remaining {cuts_needed - confident_cuts - borderline_cuts} cuts require "
        f"player preference input.",
        "",
        "---",
        "",
        "## Starting State",
        "",
        f"| Metric | Current | Target |",
        f"|--------|---------|--------|",
        f"| Total cards | {structural['deck_size']} | {structural['deck_size_target']} |",
        f"| Lands | {structural['land_count']} | {structural['land_target_min']}–{structural['land_target_max']} |",
        f"| Nonlands | {structural['nonland_count']} | ~{structural['deck_size_target'] - structural['land_target_min']} |",
        "",
        "---",
        "",
        "## What Needs to Happen",
        "",
        f"1. Cut **{cuts_needed} nonlands** to open land slots.",
        f"2. Add **{lands_needed} lands** to reach a functional mana base.",
        f"3. (Optional) Fill remaining card slots from collection, if any remain after cuts.",
        "",
        "---",
        "",
        "## Cut Path (model confidence breakdown)",
        "",
        f"Total cuts needed: **{cuts_needed}**",
        "",
    ]

    # Phase 1: strong cuts
    lines += [
        f"### Phase 1 — Model-confident cuts ({confident_cuts} of {cuts_needed})",
        "",
        "The model is **high-confidence** on these. No primary roles. Clear structural pressure.",
        "Cutting these first is the lowest-risk path.",
        "",
    ]
    if strong:
        lines.append("| Card | CMC | Net score | Model confidence |")
        lines.append("|------|-----|-----------|-----------------|")
        for item in strong:
            lines.append(
                f"| {item['name']} | {item['cmc']} "
                f"| {item['net']:.2f} | {item['confidence']} |"
            )
    else:
        lines.append("None. (No strong cut candidates — proceed directly to Phase 2.)")

    remaining_after_1 = cuts_needed - confident_cuts
    lines += [
        "",
        f"Cuts freed: **{confident_cuts}**.  Remaining: **{remaining_after_1}**.",
        "",
    ]

    # Phase 2: borderline cuts (optional)
    lines += [
        f"### Phase 2 — Borderline cuts ({borderline_cuts} available, use if needed)",
        "",
        "The model is **medium-confidence** on these. No primary roles, but some curve or",
        "scarcity cost. Consider cutting these if Phase 1 alone is not enough.",
        "",
    ]
    if borderline:
        lines.append("| Card | CMC | Net score | Model confidence | Caution |")
        lines.append("|------|-----|-----------|-----------------|---------|")
        for item in borderline:
            caution = "Has secondary Card_Draw — check draw count after cut." if "Card_Draw" in {
                r for r, v in weighted_by_card.get(item["name"], {}).items()
            } else "—"
            lines.append(
                f"| {item['name']} | {item['cmc']} "
                f"| {item['net']:.2f} | {item['confidence']} | {caution} |"
            )
    else:
        lines.append("None.")

    remaining_after_2 = max(0, remaining_after_1 - borderline_cuts)
    lines += [
        "",
        f"If all Phase 2 cuts are made: freed {confident_cuts + borderline_cuts}. "
        f"Remaining: **{remaining_after_2}**.",
        "",
    ]

    # Phase 3: near-zero review
    lines += [
        f"### Phase 3 — Near-zero review (do NOT cut without explicit decision)",
        "",
        "Net score is nearly zero — the model has almost no preference.",
        "These should only be cut after evaluating whether their role is covered elsewhere.",
        "",
    ]
    if near_zero:
        lines.append("| Card | CMC | Net score | Model confidence |")
        lines.append("|------|-----|-----------|-----------------|")
        for item in near_zero:
            lines.append(
                f"| {item['name']} | {item['cmc']} "
                f"| {item['net']:.2f} | {item['confidence']} |"
            )
    else:
        lines.append("None.")
    lines.append("")

    # Phase 4: role review cards
    if role_review:
        lines += [
            "### Phase 3D — Needs role review (halt before cutting)",
            "",
            "These cards have 0 primary roles but high functional density.",
            "The model may be misclassifying them. Resolve primary-role status before cutting.",
            "",
            "| Card | CMC | FDS | Net score |",
            "|------|-----|-----|-----------|",
        ]
        for item in role_review:
            lines.append(
                f"| {item['name']} | {item['cmc']} "
                f"| {item['fds']:.2f} | {item['net']:.2f} |"
            )
        lines.append("")

    # Phase 5: human-required Tier 2 cuts
    if remaining_after_2 > 0:
        lines += [
            f"### Phase 4 — Human-required cuts ({remaining_after_2} still needed)",
            "",
            "After Phases 1–2, the model cannot confidently suggest the remaining cuts.",
            "These must come from **Tier 2** (cards with primary roles, CMC ≥ 5).",
            "Each cut removes primary-role coverage. Evaluate impact before deciding.",
            "",
        ]
        if tier2:
            lines.append("| Card | CMC | Primary roles | Net score | Model confidence | Impact |")
            lines.append("|------|-----|---------------|-----------|-----------------|--------|")
            for item in tier2[:10]:
                wr = weighted_by_card.get(item["name"], {})
                primary_roles = sorted(r for r, v in wr.items() if v["priority"] == "primary")
                impact = ", ".join(primary_roles)
                lines.append(
                    f"| {item['name']} | {item['cmc']} "
                    f"| {len(primary_roles)} | {item['net']:.2f} | {item['confidence']} "
                    f"| loses: {impact or '—'} |"
                )
        lines.append("")

    # Protected cards summary
    lines += [
        "---",
        "",
        "## Cards Not Under Consideration",
        "",
        "These cards are protected from the cut model and require explicit human approval.",
        "",
        "| Card | Reason |",
        "|------|--------|",
    ]
    for item in tier3:
        lines.append(f"| {item['name']} | {item['reason']} |")

    # Land additions
    lines += [
        "",
        "---",
        "",
        "## Land Addition Summary",
        "",
        f"After making the cuts above, add **{lands_needed} lands**.",
        "The model does not select specific lands — that is the player's decision.",
        "Suggested composition (for reference only):",
        "",
        "- 15–18 basic Swamps (reliable, no setup required)",
        "- Cabal Coffers + Urborg, Tomb of Yawgmoth (if not already in list)",
        "- 4–6 utility lands: Phyrexian Tower, Cabal Stronghold, Nykthos, Castle Locthwain",
        "- 3–4 fetch/graveyard-synergy lands",
        "",
        "> The player should finalize the land package based on collection, budget, and play style.",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Stage | Cards | Model confidence |",
        f"|-------|-------|-----------------|",
        f"| Phase 1 — strong cuts | {confident_cuts} | high |",
        f"| Phase 2 — borderline cuts | {borderline_cuts} | medium |",
        f"| Phase 3 — near-zero review | {len(near_zero)} | low (human decision) |",
        f"| Phase 3D — needs role review | {len(role_review)} | low (halt before cutting) |",
        f"| Phase 4 — Tier 2 (primary-role cuts) | {remaining_after_2} | low (human required) |",
        f"| **Total cuts needed** | **{cuts_needed}** | — |",
        f"| **Lands to add** | **{lands_needed}** | player decision |",
    ]

    # Add machine-readable simulation status header
    simulation_status = {
        "complete_confident_path_available": (confident_cuts + borderline_cuts >= cuts_needed),
        "medium_or_higher_confidence_cuts_available": confident_cuts + borderline_cuts,
        "high_confidence_cuts": confident_cuts,
        "medium_confidence_cuts": borderline_cuts,
        "human_required_cuts": remaining_after_2,
        "near_zero_review_count": len(near_zero),
        "needs_role_review_count": len(role_review),
        "total_cuts_needed": cuts_needed,
        "lands_to_add": lands_needed,
        "warning": (
            "This model cannot complete the final deck without player preference input. "
            f"Only {confident_cuts + borderline_cuts} of {cuts_needed} needed cuts can be "
            "suggested with medium-or-higher confidence. The remaining "
            f"{remaining_after_2} require explicit human decisions about which primary roles "
            "to reduce."
        ),
    }
    (REPORTS / "deck_completion_simulation.json").write_text(
        json.dumps(simulation_status, indent=2)
    )
    (REPORTS / "deck_completion_simulation.md").write_text("\n".join(lines))


def compute_preference_adjusted_cuts(
    tier2: list,
    weighted_by_card: dict,
    preferences: dict | None = None,
) -> list[dict]:
    """
    Re-rank Tier 2 cuts using player preference weights.

    preference_adjusted_cut_cost = base_cut_cost + sum(pref_weight × role_weight)
      where pref_weight is the player's weight for each primary role's preference category.

    lower_curve_aggressively adds to cut_pressure, not cut_cost:
      lower_curve_boost = lower_curve_weight × max(0, cmc - 4)

    Returns a new list sorted by preference_adjusted_net (DESC).
    """
    if preferences is None:
        preferences = DEFAULT_PREFERENCES

    lower_curve = preferences.get("lower_curve_aggressively", 0.0)
    adjusted = []

    for item in tier2:
        wr = weighted_by_card.get(item["name"], {})

        # Preference cost: sum over primary roles that match a preference category
        pref_cost = 0.0
        pref_categories_hit: list[str] = []
        for role, info in wr.items():
            if info["priority"] == "primary":
                category = ROLE_PREFERENCE_MAP.get(role)
                if category and category != "lower_curve_aggressively":
                    weight = preferences.get(category, 0.0)
                    pref_cost += weight * PRIMARY_WEIGHT
                    if category not in pref_categories_hit:
                        pref_categories_hit.append(category)

        # Lower curve preference adds pressure for high CMC
        curve_boost = lower_curve * max(0, item["cmc"] - 4)

        adj_pressure = item["pressure"] + curve_boost
        adj_cost     = item["cut_cost"] + pref_cost
        adj_net      = adj_pressure - adj_cost

        primary_roles = sorted(r for r, v in wr.items() if v["priority"] == "primary")

        adjusted.append({
            **item,
            "preference_adjusted_pressure": adj_pressure,
            "preference_adjusted_cut_cost": adj_cost,
            "preference_adjusted_net":      adj_net,
            "preference_categories_hit":    pref_categories_hit,
            "primary_roles":                primary_roles,
        })

    adjusted.sort(key=lambda x: -x["preference_adjusted_net"])
    return adjusted


def _write_preference_cut_review(
    tier2_adjusted: list,
    preferences: dict,
    cuts_still_needed: int,
) -> None:
    """Write preference-weighted Tier 2 cut review as MD and JSON."""

    # Classify each card by adjusted net vs cuts needed
    prefer_avoid  = [c for c in tier2_adjusted if c["preference_adjusted_net"] <= 0]
    consider      = [c for c in tier2_adjusted if 0 < c["preference_adjusted_net"] <= 3]
    cut_if_needed = [c for c in tier2_adjusted if c["preference_adjusted_net"] > 3]

    # MD report
    lines = [
        "# Preference-Weighted Cut Review",
        "",
        "> Tier 2 cuts ranked by preference-adjusted net score.",
        "> Cards scoring high here are under both structural pressure AND align with",
        "> a pillar the player has *not* marked as high-priority to preserve.",
        "",
        "---",
        "",
        "## Active Preference Profile",
        "",
        "| Preference | Weight | Meaning |",
        "|-----------|--------|---------|",
    ]
    pref_labels = {
        "preserve_big_mythic_threats":  "Apex threats / finishers",
        "preserve_sacrifice_control":   "Edict effects / sacrifice engines",
        "preserve_draw_consistency":    "Card draw / hand smoothing",
        "preserve_mana_explosion":      "Mana scaling / acceleration",
        "preserve_token_fuel_density":  "Token generation / fuel supply",
        "preserve_recursion_density":   "Graveyard recursion",
        "lower_curve_aggressively":     "Curve pressure (adds to cut pressure for CMC>4)",
    }
    for pref, weight in preferences.items():
        lines.append(f"| {pref} | {weight:.1f} | {pref_labels.get(pref, '')} |")

    lines += [
        "",
        "---",
        "",
        f"## Tier 2 Re-Ranked (preference-adjusted, {cuts_still_needed} still needed)",
        "",
        "### Avoid cutting (preference-adjusted net ≤ 0)",
        "",
        "Your preferences protect these. Do not cut without reconsidering your weights.",
        "",
    ]
    if prefer_avoid:
        lines.append("| Card | CMC | Adj net | Protected by |")
        lines.append("|------|-----|---------|--------------|")
        for c in prefer_avoid:
            cats = ", ".join(c["preference_categories_hit"]) or "—"
            lines.append(
                f"| {c['name']} | {c['cmc']} "
                f"| {c['preference_adjusted_net']:.2f} | {cats} |"
            )
    else:
        lines.append("None — all Tier 2 cards are under positive cut pressure even with preferences.")

    lines += [
        "",
        "### Consider carefully (adj net 0–3)",
        "",
        "Cutting these removes preferred roles. Evaluate specific impact before deciding.",
        "",
    ]
    if consider:
        lines.append("| Card | CMC | Adj net | Primary roles lost | Preference categories |")
        lines.append("|------|-----|---------|---------------------|----------------------|")
        for c in consider:
            lost = ", ".join(c["primary_roles"])
            cats = ", ".join(c["preference_categories_hit"]) or "—"
            lines.append(
                f"| {c['name']} | {c['cmc']} "
                f"| {c['preference_adjusted_net']:.2f} | {lost} | {cats} |"
            )
    else:
        lines.append("None.")

    lines += [
        "",
        "### Cut if needed (adj net > 3)",
        "",
        "These have structural cut pressure that outweighs your preference protection.",
        "Cutting from here first preserves your preferred pillars.",
        "",
    ]
    if cut_if_needed:
        lines.append("| Card | CMC | Base net | Adj net | Lower curve boost |")
        lines.append("|------|-----|----------|---------|-------------------|")
        for c in cut_if_needed:
            boost = c["preference_adjusted_pressure"] - c["pressure"]
            lines.append(
                f"| {c['name']} | {c['cmc']} "
                f"| {c['net']:.2f} | {c['preference_adjusted_net']:.2f} | +{boost:.2f} |"
            )
    else:
        lines.append("None — all remaining Tier 2 cuts are blocked by preferences.")

    lines += [
        "",
        "---",
        "",
        "## How to Use This Report",
        "",
        "1. Cut all **'cut if needed'** cards first to stay within preferred pillars.",
        "2. If still short, move to **'consider carefully'** — review each impact.",
        "3. **'Avoid cutting'** should only be touched after adjusting preference weights.",
        "4. Return to `deck_gap_analysis.py → DEFAULT_PREFERENCES` to tune weights.",
    ]

    (REPORTS / "preference_cut_review.md").write_text("\n".join(lines))

    # JSON report
    pref_json = {
        "preferences": preferences,
        "cuts_still_needed": cuts_still_needed,
        "tier2_ranked": [
            {
                "name": c["name"],
                "cmc": c["cmc"],
                "base_net": round(c["net"], 2),
                "preference_adjusted_net": round(c["preference_adjusted_net"], 2),
                "primary_roles": c["primary_roles"],
                "preference_categories_hit": c["preference_categories_hit"],
                "model_confidence": c.get("confidence", "low"),
            }
            for c in tier2_adjusted
        ],
    }
    (REPORTS / "preference_cut_review.json").write_text(
        json.dumps(pref_json, indent=2)
    )


def _write_weighted_role_targets_csv(role_breakdown: dict) -> None:
    """
    Write per-role weighted breakdown with weighted target comparison.

    Columns: role, raw_count, weighted_total, primary_count, secondary_count,
             incidental_count, weighted_target_lo, weighted_target_hi, w_status
    """
    with open(REPORTS / "weighted_role_targets.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "role", "raw_count", "weighted_total",
            "primary_count", "secondary_count", "incidental_count",
            "weighted_target_lo", "weighted_target_hi", "w_status",
        ])
        for role in TARGETS:
            bd = role_breakdown[role]
            wt_lo, wt_hi = WEIGHTED_TARGETS[role]
            w.writerow([
                role, bd["raw"], f"{bd['weighted']:.2f}",
                bd["primary"], bd["secondary"], bd["incidental"],
                wt_lo, wt_hi, bd["w_status"],
            ])


def _write_primary_role_summary_csv(role_breakdown: dict) -> None:
    """
    Write a clean primary-role summary. Easier to read than the full targets CSV.

    Columns: role, primary_count, secondary_count, incidental_count,
             weighted_total, w_status
    """
    with open(REPORTS / "primary_role_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "role", "primary_count", "secondary_count", "incidental_count",
            "weighted_total", "w_status",
        ])
        for role in sorted(TARGETS):
            bd = role_breakdown[role]
            w.writerow([
                role, bd["primary"], bd["secondary"], bd["incidental"],
                f"{bd['weighted']:.2f}", bd["w_status"],
            ])


def _write_completion_plan_md(
    structural: dict,
    tier1: list, tier2: list, tier3: list,
    role_breakdown: dict,
    validation_passed: bool = False,
) -> None:
    """
    Write a deck completion plan: how many lands to add, which nonlands are
    cut candidates (and in what order), preserving primary-role density.
    """
    lands_needed = structural["lands_needed"]
    cuts_needed  = structural["nonland_cuts_needed"]

    if validation_passed:
        status_block = [
            "> **Status:** Cut tiers are archetype-aware.",
            "> Primary role validation passed — all archetype-core cards have primary roles.",
            "",
        ]
    else:
        status_block = [
            "> ⚠ **WARNING: Cut tiers are experimental.**",
            "> Cards with 0 primary roles may indicate missing primary-role classification,",
            "> not true cut safety. Do not make final cuts from this list until",
            "> primary-role validation passes (run `PRIMARY_ROLE_VALIDATION` checks).",
            "",
        ]

    lines = [
        "# Deck Completion Plan",
        "",
        *status_block,
        "## Structural Gap",
        "",
        f"| Metric | Current | Target |",
        f"|--------|---------|--------|",
        f"| Deck size | {structural['deck_size']} | {structural['deck_size_target']} |",
        f"| Lands | {structural['land_count']} | {structural['land_target_min']}–{structural['land_target_max']} |",
        f"| Lands to add | {lands_needed} | — |",
        f"| Nonlands to cut | ~{cuts_needed} | — |",
        "",
        "---",
        "",
        "## Role Depth After Cuts (projected)",
        "",
        "The deck currently has no primary-role gaps. After cutting ~" + str(cuts_needed) + " nonlands:",
        "- Roles where coverage is **primary-heavy** survive cuts well.",
        "- Roles where coverage is **incidental-heavy** may actually improve (less noise).",
        "",
        "Roles with low primary coverage — protect these:",
        "",
    ]

    low_primary = [
        (role, bd) for role, bd in role_breakdown.items()
        if bd["primary"] <= 2 and bd["raw"] > 0
    ]
    low_primary.sort(key=lambda x: x[1]["primary"])
    for role, bd in low_primary:
        lines.append(
            f"- **{role}**: {bd['primary']} primary cards"
            f" (weighted {bd['weighted']:.1f} — target {WEIGHTED_TARGETS[role][0]:.1f}–{WEIGHTED_TARGETS[role][1]:.1f})"
        )

    lines += [
        "",
        "---",
        "",
        "## Cut Priority Order",
        "",
        f"Need to free ~{cuts_needed} nonland slots for lands.",
        "Listed by verdict band, then net score. Strong cuts first.",
        "",
        "### Tier 1 — Candidate cuts (0 primary roles)",
        "",
        "Split into verdict bands. `net = cut_pressure − cut_cost`.",
        "High net = confident cut. Near-zero = evaluate carefully.",
        "Cards in **D (needs_role_review)** may be misclassified —",
        "do not cut until primary-role status is confirmed.",
        "",
    ]

    if tier1:
        verdict_bands = [
            (CUT_VERDICT_STRONG,      "#### A. Strong cut candidates (net ≥ 1.0)"),
            (CUT_VERDICT_BORDERLINE,  "#### B. Borderline cut candidates (0.25–1.0)"),
            (CUT_VERDICT_NEAR_ZERO,   "#### C. Near-zero review (0–0.25)"),
            (CUT_VERDICT_ROLE_REVIEW, "#### D. Needs role review (high FDS, 0 primary)"),
        ]
        by_verdict: dict[str, list] = {v: [] for v, _ in verdict_bands}
        for item in tier1:
            v = item.get("verdict", CUT_VERDICT_NEAR_ZERO)
            if v in by_verdict:
                by_verdict[v].append(item)
        for verdict_key, heading in verdict_bands:
            items = by_verdict[verdict_key]
            if items:
                lines += ["", heading, ""]
                lines.append("| Card | CMC | Pressure | Cut cost | Net | FDS |")
                lines.append("|------|-----|----------|----------|-----|-----|")
                for item in items:
                    lines.append(
                        f"| {item['name']} | {item['cmc']} "
                        f"| {item['pressure']:.2f} | {item['cut_cost']:.2f} "
                        f"| {item['net']:.2f} | {item['fds']:.2f} |"
                    )
    else:
        lines.append("None. (All 0-role cards are in the protected lists.)")

    lines += [
        "",
        "### Tier 2 — Viable cuts (1+ primary roles)",
        "",
        "Only cut from here if Tier 1 is exhausted.",
        "Each cut removes some primary-role coverage — evaluate impact before cutting.",
        "",
    ]

    if tier2:
        lines.append("| Card | CMC | Primary | Net score | FDS |")
        lines.append("|------|-----|---------|-----------|-----|")
        for item in tier2[:10]:
            lines.append(
                f"| {item['name']} | {item['cmc']} "
                f"| {item['primary']} | {item['net']:.2f} | {item['fds']:.2f} |"
            )
    else:
        lines.append("None.")

    lines += [
        "",
        "### Tier 3 — Do not cut (protected)",
        "",
        "Identity-protected cards define how the deck feels.",
        "Parser blind spots need rule fixes before evaluation.",
        "",
    ]

    if tier3:
        lines.append("| Card | Reason |")
        lines.append("|------|--------|")
        for item in tier3:
            lines.append(f"| {item['name']} | {item['reason']} |")
    else:
        lines.append("None.")

    lines += [
        "",
        "---",
        "",
        "## Land Recommendations",
        "",
        "Add ~" + str(lands_needed) + " lands. Suggested composition:",
        "",
        "- 15–18 basic Swamps (reliable, no downside)",
        "- Cabal Coffers + Urborg, Tomb of Yawgmoth (big mana payoff)",
        "- Crypt of Agadeem (already in deck)",
        "- 4–6 utility lands: High Market (already in), Phyrexian Tower,",
        "  Cabal Stronghold, Nykthos (devotion), Castle Locthwain",
        "- 3–4 fetch/fixing lands for graveyard synergy or color reliability",
        "",
        "> Land recommendations are suggestions only. Final selection should",
        "> respect your collection, play style, and budget.",
    ]

    (REPORTS / "completion_plan.md").write_text("\n".join(lines))


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
