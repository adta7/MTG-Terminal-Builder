# Deck Gap Analysis — Bahahahah (Sheoldred, Whispering One)

**Date:** 2026-05-30  
**Cards in list:** 87 / 99  
**Source:** Functional role derivation on collection scan DB

---

## Primary Finding: Land Shortage

The 87-card list has only **10 lands** — a complete Commander deck needs 35–38.

| Metric | Current | Target |
|--------|---------|--------|
| Total cards | 87 | 99 |
| Lands | 10 | 36–38 |
| Nonland spells | 77 | ~61 |
| Cards to add | 12 | — |
| Nonlands to cut | ~16 | — |
| Lands still needed | ~28 | — |

**The deck needs approximately 28 Swamps/utility lands and ~16 nonland cuts.**

---

## Mana Curve (77 nonland spells)

| CMC | Count |
|-----|-------|
| 1 | 9 |
| 2 | 27 |
| 3 | 15 |
| 4 | 11 |
| 5 | 6 |
| 6 | 3 |
| 7+ | 6 |

**CMC ≤ 3: 51/77 (66%)** — curve is healthy. CMC 7+ has 6 cards — 1–2 more than optimal for midrange.

---

## Functional Role Counts vs Targets

| Role | Have | Ideal | Status |
|------|------|-------|--------|
| Engine | 28 | 10–16 | HIGH |
| Enabler | 30 | 7–12 | HIGH |
| Payoff | 20 | 6–10 | HIGH |
| Conversion | 20 | 5–8 | HIGH |
| Fuel | 15 | 5–8 | HIGH |
| Recursion | 14 | 6–9 | HIGH |
| Threat | 16 | 6–10 | HIGH |
| Mana_Engine | 7 | 2–4 | HIGH |
| Card_Draw | 14 | 9–12 | SLIGHTLY HIGH |
| Removal | 13 | 9–12 | SLIGHTLY HIGH |
| Interaction | 12 | 6–9 | SLIGHTLY HIGH |
| Mana_Acceleration | 15 | 11–14 | SLIGHTLY HIGH |
| Finisher | 5 | 3–6 | OK |
| Setup | 6 | 4–7 | OK |
| Protection | 2 | 2–4 | OK |

**No functional gaps.** The deck is over-full across every role. Once ~16 nonland
spells are cut to make room for 28+ lands, role counts will normalize into range.

---

## System Blind Spots (7 cards the tagger doesn't fully understand yet)

| Card | CMC | Real role | Layer 2 gap |
|------|-----|-----------|-------------|
| Tragic Slip | 1 | Removal | No pattern for -X/-X targeted removal |
| Dance of the Dead | 2 | Recursion | "put onto battlefield" vs. "return to battlefield" |
| Victimize | 3 | Recursion | Graveyard word separated from "return to battlefield" |
| Nyx Lotus | 4 | Mana_Acceleration | Devotion-based mana not tagged as Mana_Production |
| Lashwrithe | 4 | Threat/Finisher | Permanent_Scaling alone has no functional rule |
| Sudden Spoiling | 3 | Interaction | Flash + split second effect, no pattern |
| Prowling Geistcatcher | 5 | Fuel/Recursion | Complex sac-trigger, no pattern |

These are all real cards doing real work. The system just doesn't see them yet.

---

## Cut Candidates (weakest functional profiles)

When freeing slots for lands, cut these first:

| Card | CMC | Roles | Why |
|------|-----|-------|-----|
| Overseer of the Damned | 7 | Interaction, Removal | Expensive single-use |
| Lashwrithe | 4 | *(none)* | System-blind, equipment slot |
| Nyx Lotus | 4 | *(none)* | Enters tapped, slow, inconsistent |
| Prowling Geistcatcher | 5 | *(none)* | Complex, niche |
| Syr Konrad, the Grim | 5 | Removal | Only 1 role for a 5-drop |
| K'rrik, Son of Yawgmoth | 7 | Conversion, Engine | Redundant with Sheoldred at 7 |

**Keep (highest functional value):**  
Archon of Cruelty (7 roles), Yawgmoth (5), Erebos (5), Bolas's Citadel (4), Black Market (5)

---

## "Hand Feels Sad by Turn 5" Diagnosis

1. **Incomplete land base** — test games without proper 36-land base feel wrong
2. **6 cards at CMC 7+** — drawing multiple clogs the hand early
3. **14 Recursion + 15 Fuel** — pieces that need other pieces to enable value; less action in isolation

**Fix:** Full 36-land base, cut 2–3 of the 7+ CMC cards, ensure 3–4 CMC ≤ 2 draw spells.

---

## Summary

This deck has the right strategic identity: mono-black aristocrats/reanimator with deep
sacrifice, death-trigger payoffs, recursion, and mana engines. No wrong cards, just a
draft list that needs its land base and final cuts.

**Next steps:**
1. Add ~28 lands (basic Swamps + Crypt of Agadeem, Cabal Coffers, utility lands)
2. Cut ~16 weakest nonlands (CMC 7+ excess, system-blind cards, redundant roles)
3. Finalize to 99 and playtest
