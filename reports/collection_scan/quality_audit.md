# Phase 4C: Tag Quality Audit

**Date:** 2026-05-30
**Scope:** 11 priority mechanical tags across 347 black/colorless collection cards

---

## Summary

| Tag | Cards | Quality | Notes |
|-----|-------|---------|-------|
| Sacrifice_Outlet | 21 | ✓ Clean | ability_kind=activated/cost correct on all |
| Death_Trigger | 21 | ✓ Clean | triggered/trigger correct on all 21 |
| Self_Death_Trigger | 14 | ⚠ 2 FP | Abnormal Endurance, Malakir Rebirth (grant effect) |
| Reanimation | 19 | ✓ Clean | accurate destination (battlefield) on all |
| Mass_Reanimate | 4 | ✓ Fixed | was 8: removed 4 hand-return false positives |
| Life_Payment | 13 | ✓ Clean | cost/draw patterns cover correct cards |
| Token_Generation | 23 | ✓ Clean | variety of token patterns all accurate |
| Mana_Multiplier | 3+2 | ✓ Narrow | only true doublers tagged |
| Draw_Effect | 47 | ✓ Broad | all 47 are genuine draw effects |
| Tutor_Effect | 17 | ⚠ Overlap | 3 land-fetch cards have both Tutor_Effect + Search_For_Land |
| Forced_Sacrifice | 14 | ✓ Clean | triggered/effect correct on all |

---

## False Positives Found and Fixed

### Mass_Reanimate — 4 removed (pattern fix applied)

Pattern 2 was `return .* target creature cards? from` without checking
destination. Four cards returned to HAND not battlefield:

- Macabre Waltz — "return ... to your hand"
- Lethal Protection — "return ... to your hand"
- Grave Venerations — single-target reanimate to battlefield (should be Reanimation)
- Witch of the Moors — "return ... to your hand"

**Fix:** Pattern now requires "battlefield" within 60 chars after the match.
Remaining 4 Mass_Reanimate cards: Living Death, Wake the Dead,
Rise of the Dark Realms, Gisa, Glorious Resurrector — all correct.

---

## Known Acceptable False Positives (Not Fixed)

### Self_Death_Trigger — 2 cards, confidence 0.85

**Abnormal Endurance** and **Malakir Rebirth // Malakir Mire** grant
"when this creature dies" to another creature. The pattern fires on the
granted ability text in the oracle.

These cards are death-adjacent (they rescue creatures from death) so the
signal is semantically related. Acceptable at 0.85 confidence. Would
require parsing quoted/granted ability text to fully exclude, which is
not worth the complexity at this stage.

### Tutor_Effect + Search_For_Land overlap — 3 cards

**Evolving Wilds**, **Fabled Passage**, **Myriad Landscape** receive both
Tutor_Effect and Search_For_Land. This is technically correct — they ARE
library searches. The overlap is informative (both tags present), not
misleading.

---

## Quality Observations

**What is semantically trustworthy:**
- Death_Trigger, Forced_Sacrifice, Sacrifice_Outlet — very clean
- Life_Payment — correct cards, correct ability_kind
- Token_Generation — wide variety, all accurate
- Reanimation — all 19 correctly return to battlefield

**What to watch:**
- ability_kind="other" on sorceries/instants is expected and honest
- text_role="unknown" on non-activated/triggered abilities is correct
- Mana_Multiplier is narrow (3 cards) but accurate — only true doublers

---

## No New Patterns Needed

After this quality pass, the remaining untagged cards fall into:

| Category | Cards |
|----------|-------|
| Basic utility/colorless lands | ~7 |
| Counter/+1+1 mechanics | ~4 |
| Low-relevance text (tapped lands, etc.) | ~3 |
| Other niche mechanics | ~50 |

None of these are high-priority for a sacrifice-recursion-drain engine.
The tagger now correctly understands the cards that define this deck's identity.

---

## What's Next: Layer 3 (Functional Roles)

Layer 2 is now semantically trustworthy for the engine cards.
The next meaningful step is Layer 3: derive functional roles from
mechanical tag combinations.

Key rules to add:
- Sacrifice_Outlet + Mana_Production → Mana_Engine
- Death_Trigger + Life_Drain → Aristocrats_Payoff
- Mass_Reanimate → Board_Reset
- Token_Generation + Death_Trigger → Fodder_Engine
- Reanimation + Self_Death_Trigger → Recursive_Value
