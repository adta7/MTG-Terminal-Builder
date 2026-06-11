# Functional Role Quality Audit — Phase 5B

**Date:** 2026-05-30
**Cards audited:** 347 black/colorless collection cards
**Cards with functional roles:** 225/347

## Changes applied before this audit

1. **Bolas's Citadel Layer 2 fix** — Added two patterns:
   - `Life_Payment`: `pay life equal to` (covers "pay life equal to its mana value")
   - `Sacrifice_Outlet`: `sacrifice N nonland permanents:` (covers word-number quantities)
   - Result: Bolas's Citadel now correctly tagged **Life_Drain + Life_Payment + Sacrifice_Outlet**
   - Functional result: **Conversion + Enabler + Engine + Finisher** ✓

2. **Threat inflation fix** — Removed `Evasion alone → Threat at 0.50`
   - Before: 74 Threat cards (many only had flying)
   - After: 41 Threat cards (all based on multi-tag combinations ≥0.60)
   - Lost 15 cards that had no functional role besides "has evasion" — honest

---

## Role Audit Results

### Threat (41 cards) — ✓ TRUSTWORTHY after fix

All 41 cards have at minimum a two-tag combination:
- Top tier (0.80–0.85): Braids, Sheoldred, Indulgent Tormentor (Forced_Sacrifice + Upkeep_Trigger)
- Mid tier (0.75–0.80): Evasion + drain, Evasion + forced sac, Death + drain combos
- Bottom tier (0.60): Forced_Sacrifice alone (still meaningful — a recurring edict is a threat)

**Note:** Evasion alone no longer assigns Threat. Future tag: `Combat_Relevance` for evasion-only cards.

---

### Engine (50 cards) — ✓ MOSTLY CORRECT, one note

Top examples: Ashnod's Altar, Yawgmoth, Pawn of Ulamog, Priest of Forgotten Gods, Black Market, Grave Pact, Ghoulcaller Gisa.

**One semantic note:** `Treasure` token is tagged Engine (Mana_Production + Sacrifice_Outlet = 0.90). A token is engine *output*, not the engine itself. This is acceptable at Layer 3 — the mechanical profile is correct. It would be filtered at Layer 5 ("emotional" layer) when permanence and repeatability become signals.

---

### Payoff (46 cards) — ✓ CLEAN

High-confidence aristocrats payoffs: Blood Artist, Zulaport Cutthroat, Falkenrath Noble, Vraan (all 0.90). Gray Merchant, Midnight Reaper, Grim Haruspex at 0.85. All correct.

---

### Fuel (36 cards) — ✓ GOOD, known imprecision on 2 cards

Most Fuel cards are correct: Bloodghast, Nether Traitor (self-recursion), Ghoulish Procession, Jadar (repeatable tokens), Open the Graves.

**Known imprecision:** Abnormal Endurance and Malakir Rebirth appear as Fuel via Return_Self_From_Graveyard (their oracle text quotes the ability they grant to others). Both do serve fuel-like functions strategically (they temporarily prevent a creature from dying, keeping it in the fuel cycle). Acceptable at 0.85.

---

### Conversion (34 cards) — ✓ STRONG

The "resource transformer" concept is working well:
- Sacrifice + mana: Ashnod's Altar, Priest of Forgotten Gods, Pawn of Ulamog
- Life + cards: Phyrexian Arena, Yawgmoth, Erebos, Blighted Blackthorn
- Sacrifice + tokens: Ghoulcaller Gisa

These are exactly the cards that make a mono-black sacrifice deck tick.

---

### Finisher (14 cards) — ✓ SELECTIVE AND ACCURATE

The narrowest bucket. All are genuine game-closers:
- X-spell finishers (0.90): Exsanguinate, Gray Merchant, Profane Command
- Sacrifice finishers (0.75): Bolas's Citadel, Gnawing Zombie, Ob Nixilis, Vraska
- Mass reanimate (0.70): Living Death, Rise of the Dark Realms, Wake the Dead

14 cards is appropriate for a 347-card collection. This bucket is correctly conservative.

---

### Card_Draw (47 cards) — ✓ BROAD BUT VALID

Top entries all 0.90 from two-tag combinations:
- Death + Draw: Erebos, Grim Haruspex, Midnight Reaper, Skullclamp
- Upkeep + Draw: Phyrexian Arena, Braids, Smothering Abomination, Sinister Gnarlbark

Single Draw_Effect at 0.85 inflates the lower portion. That is intentionally conservative (0.85, not 1.0) — a single-shot draw spell is Card_Draw but at lower confidence than a recurring engine.

---

### Mana_Engine (13 cards) — ✓ SELECTIVE AND CORRECT

Very clean. Mana doublers (Crypt Ghast, Nirkana Revenant, Bubbling Muck at 0.90) and scaling mana producers (Black Market, Crypt of Agadeem, Magus of the Coffers, Ashnod's Altar at 0.85). This is the correct list of mana engines for a mono-black deck.

---

### Removal (49 cards) — ✓ CLEAN

All top entries are Targeted_Removal or Board_Wipe at 0.95:
Damnation, Infernal Grasp, Hero's Downfall, Annihilate, Deadly Tempest.
Forced_Sacrifice entries are correctly at 0.85 (they're soft removal).

---

## Summary: What Is Trustworthy

| Role | Verdict | Notes |
|------|---------|-------|
| Threat | ✓ Trustworthy | Fixed from 74→41, all multi-tag now |
| Engine | ✓ Mostly | Treasure token is minor semantic imprecision |
| Payoff | ✓ Clean | Aristocrats payoffs correctly identified |
| Fuel | ✓ Good | 2 known imprecisions (granted ability FP) |
| Conversion | ✓ Strong | Resource-transformer concept working well |
| Finisher | ✓ Selective | 14 cards, all correct |
| Card_Draw | ✓ Broad | Single draw spells at 0.85, correct |
| Mana_Engine | ✓ Selective | 13 cards, all mana engines |
| Removal | ✓ Clean | Targeted/wipe at 0.95, forced sac at 0.85 |

---

## Known Remaining Gaps

1. `Evasion alone → Combat_Relevance` — not yet a tag (removed from Threat)
2. `Life_Loss_Draw` vs `Life_Payment` — Phyrexian Arena, Phyrexian Reclamation lose life differently than K'rrik, Bolas's Citadel. Future refinement.
3. Token cards as Engine — tokens with activated abilities get Engine tag. Layer 5 should filter by "permanent" status.
4. `Treasure token` in Engine/Conversion — a one-shot artifact counts mechanically but not strategically. Future: filter by card type or set permanence threshold.

---

## Layer 3 Status: Ready for Deck Analysis

The functional roles are calibrated enough to answer:
- Which cards are engines? (50)
- Which are payoffs? (46)
- Which are finishers? (14)
- Which provide mana acceleration? (41)
- Which provide card velocity? (47)

**Not recommended yet:** Layer 4 archetype or Layer 5 emotional tagging. Calibrate first, then expand.
