#!/usr/bin/env python3
"""
analyze_gaps.py — Analyze scanner output and create pattern backlog.

Phase 1B: Determine which patterns to add and in what priority order.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from mtgdeck.database import Database
from mtgdeck import tags
from mtgdeck.layer2_scanner import Layer2Scanner
from fixtures.sample_cards import load_sample_cards, SAMPLE_CARDS


def analyze_gaps():
    """Analyze gaps and create pattern backlog."""
    # Setup database
    db = Database(":memory:")
    db.init_db()
    tags.seed_tags(db)
    load_sample_cards(db)

    scanner = Layer2Scanner(db)

    print("\n")
    print("╔" + "="*70 + "╗")
    print("║" + " "*70 + "║")
    print("║" + "  PHASE 1B: GAP ANALYSIS & PATTERN BACKLOG".center(70) + "║")
    print("║" + " "*70 + "║")
    print("╚" + "="*70 + "╝")

    # Get baseline data
    gaps = scanner.scan_coverage_gaps(scope="all")
    phrases = scanner.scan_unmatched_phrases(scope="all", min_frequency=1)

    print(f"\nBaseline: {len(gaps)} untagged cards out of {len(SAMPLE_CARDS)}")
    print(f"Phrase clusters: {len(phrases)}")

    # Analyze gaps for specific patterns
    print("\n" + "="*70)
    print("PATTERN ANALYSIS")
    print("="*70)

    pattern_backlog = []

    # 1. Tutor/Search patterns
    tutor_cards = [g for g in gaps if "tutor" in g.card_name.lower() or "demonic" in g.card_name.lower()]
    if tutor_cards or any("search your library" in p.phrase for p in phrases):
        pattern_backlog.append({
            "name": "Tutor_Effect",
            "regex": r'search.*library.*card',
            "priority": 1,
            "examples": [c.name for c in SAMPLE_CARDS if "tutor" in c.oracle_text.lower() or "search" in c.oracle_text.lower()][:2],
            "reason": "Found in Demonic Tutor, Entomb (search-based effects)"
        })

    # 2. Upkeep triggers
    upkeep_cards = [c for c in SAMPLE_CARDS if "beginning of your upkeep" in c.oracle_text.lower()]
    if upkeep_cards:
        pattern_backlog.append({
            "name": "Upkeep_Trigger",
            "regex": r'at the beginning of your upkeep',
            "priority": 2,
            "examples": [c.name for c in upkeep_cards][:2],
            "reason": "Found in Phyrexian Arena, Sheoldred (upkeep-based effects)"
        })

    # 3. Reanimation improvements
    reanimation_cards = [c for c in SAMPLE_CARDS if "graveyard" in c.oracle_text.lower() and "return" in c.oracle_text.lower()]
    pattern_backlog.append({
        "name": "Reanimation (improved)",
        "regex": r'return.*creature.*from.*graveyard|put.*creature.*from.*graveyard',
        "priority": 1,
        "examples": [c.name for c in reanimation_cards][:2],
        "reason": "Animate Dead, Living Death, Bloodghast (reanimation effects)"
    })

    # 4. ETB (Enter the Battlefield) triggers
    etb_cards = [c for c in SAMPLE_CARDS if "enters the battlefield" in c.oracle_text.lower()]
    if etb_cards:
        pattern_backlog.append({
            "name": "Enter_The_Battlefield",
            "regex": r'when .* enters the battlefield',
            "priority": 2,
            "examples": [c.name for c in etb_cards][:2],
            "reason": "Animate Dead, Grave Pact (ETB effects)"
        })

    # 5. Discard-based effects
    discard_cards = [c for c in SAMPLE_CARDS if "discard" in c.oracle_text.lower()]
    if discard_cards:
        pattern_backlog.append({
            "name": "Discard_Effect",
            "regex": r'discard',
            "priority": 3,
            "examples": [c.name for c in discard_cards][:2],
            "reason": "Necropotence, Yawgmoth's Will (discard effects)"
        })

    # Print backlog
    print("\nPATTERN BACKLOG (by priority):\n")
    for i, pattern in enumerate(sorted(pattern_backlog, key=lambda p: p["priority"]), 1):
        print(f"{i}. {pattern['name']}")
        print(f"   Regex: {pattern['regex']}")
        print(f"   Priority: {pattern['priority']}")
        print(f"   Examples: {', '.join(pattern['examples'])}")
        print(f"   Reason: {pattern['reason']}")
        print()

    # Unmatched phrase analysis
    print("="*70)
    print("TOP UNMATCHED PHRASES (need patterns)")
    print("="*70)
    print()

    for phrase in phrases[:10]:
        print(f"Family: {phrase.mechanic_family}")
        print(f"Phrase: '{phrase.phrase}'")
        print(f"Frequency: {phrase.frequency}x")
        print(f"Examples: {', '.join(phrase.example_cards)}")
        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"""
Phase 1B Analysis Complete

Total patterns to add: {len(pattern_backlog)}
Priority 1 (critical): {len([p for p in pattern_backlog if p['priority'] == 1])}
Priority 2 (important): {len([p for p in pattern_backlog if p['priority'] == 2])}
Priority 3 (nice-to-have): {len([p for p in pattern_backlog if p['priority'] == 3])}

Recommended action: Add patterns in priority order
- Start with Tutor_Effect (Demonic Tutor, Entomb)
- Then Reanimation improvements
- Then Upkeep_Trigger

Expected outcome after adding top 3:
- 10+ more cards will be tagged
- Coverage gap: 28 → ~18 untagged cards
""")

    return pattern_backlog


if __name__ == "__main__":
    backlog = analyze_gaps()
