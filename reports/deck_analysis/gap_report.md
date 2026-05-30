# Deck Gap Analysis — Bahahahah

**Commander:** Sheoldred, Whispering One  
**Date:** 2026-05-30  
**Phase:** 6B — Structural Deck Diagnostics

---

## Structural Status

**`NOT READY FOR FINAL ROLE EVALUATION`**

| Metric | Current | Target |
|--------|---------|--------|
| Deck size | 87 | 100 |
| Lands | 10 | 36–37 |
| Nonlands | 77 | ~64 |
| Lands needed | 26 | — |
| Nonland cuts after adding lands | ~13 | — |

> **Note:** Role counts below are DIAGNOSTIC ONLY.
> They are inflated because the deck has too many nonlands relative to lands.
> Do not treat them as final until the deck reaches 100 cards with 36+ lands.

Reasons:

- `deck_below_100_cards`
- `land_count_below_minimum`

---

## Role Counts vs Targets
(Diagnostic only)

| Role | Have | Ideal | Status |
|------|------|-------|--------|
| Finisher | 5 | 3–6 | OK |
| Setup | 6 | 4–7 | OK |
| Protection | 2 | 2–4 | OK |
| Mana_Acceleration | 16 | 11–14 | SLIGHTLY HIGH |
| Card_Draw | 14 | 9–12 | SLIGHTLY HIGH |
| Mana_Engine | 7 | 2–4 | HIGH |
| Removal | 15 | 9–12 | HIGH |
| Engine | 28 | 10–16 | HIGH |
| Payoff | 20 | 6–10 | HIGH |
| Fuel | 15 | 5–8 | HIGH |
| Recursion | 16 | 6–9 | HIGH |
| Conversion | 20 | 5–8 | HIGH |
| Enabler | 32 | 7–12 | HIGH |
| Interaction | 14 | 6–9 | HIGH |
| Threat | 16 | 6–10 | HIGH |

---

## Gaps to Fill

No critical or low roles found.

---

## Mana Curve (nonland spells)

- CMC 0: 0  
- CMC 1: 9  █████████
- CMC 2: 27  ███████████████████████████
- CMC 3: 15  ███████████████
- CMC 4: 11  ███████████
- CMC 5: 6  ██████
- CMC 6: 3  ███
- CMC 7+: 6  ██████

---

## Cut Candidate Classification

Cards are sorted into four categories. A 0-role card is never a cut candidate
until it has passed through the blind-spot check.

### A. Unknown / Unclassified

Cards with 0 functional roles and no known explanation.
These are candidates for either a cut or a new rule.

None.

### B. Structural Cut Pressure

Cards that may need to be cut because the deck needs lands — not because they are bad.
Logic: CMC 6+ and at least one over-represented role.

| Card | CMC | Over-represented roles |
|------|-----|------------------------|
| Archon of Cruelty | 8 | Engine, Threat, Interaction, Removal, Payoff, Card_Draw |
| Butcher of Malakir | 7 | Threat, Engine, Interaction, Removal |
| Overseer of the Damned | 7 | Interaction, Removal |
| Rune-Scarred Demon | 7 | Enabler |
| Sheoldred, Whispering One | 7 | Engine, Recursion, Enabler, Threat, Interaction, Removal |
| Grave Titan | 6 | Payoff, Threat, Fuel |
| Nirkana Revenant | 6 | Mana_Engine, Mana_Acceleration |

### C. Parser Blind Spots

**DO NOT cut based on current role score.**
The system does not understand these cards yet.

| Card | Expected roles | Gap | Status |
|------|----------------|-----|--------|
| Lashwrithe | Threat, Finisher | Permanent_Scaling alone has no Threat/Finisher rule; scaling equipment needs its own concept | needs_rule |
| Prowling Geistcatcher | Fuel, Recursion | Complex sac-trigger delayed recursion/storage; no pattern covers this | needs_rule |
| Sudden Spoiling | Interaction | Flash + split second prevention/combat blowout; no oracle pattern covers this | needs_rule |

### D. Identity-Protected Cards

Cards that may look inefficient but are intentionally expressive.
They define how the deck feels to play. Do not cut without discussion.

| Card | CMC | Functional tags |
|------|-----|-----------------|
| Black Market | 5 | Conversion, Engine, Mana_Acceleration, Mana_Engine, Payoff |
| Bolas's Citadel | 6 | Conversion, Enabler, Engine, Finisher |
| Ghoulcaller Gisa | 5 | Conversion, Enabler, Engine, Fuel, Threat |
| K'rrik, Son of Yawgmoth | 7 | Conversion, Engine |
| Living Death | 5 | Enabler, Finisher, Recursion |

---

## Parser Blind Spots (full list)

Cards the system does not fully understand.
Fixed in this phase are tagged `fixed_in_6B`. Still-open gaps are `needs_rule`.

| Card | Expected role | Suspected gap | Status |
|------|---------------|---------------|--------|
| Tragic Slip | Removal | No -X/-X targeted removal pattern (fixed in 6B) | `fixed_in_6B` |
| Dance of the Dead | Recursion | put enchanted creature onto battlefield vs return … to battlefield (fixed in 6B) | `fixed_in_6B` |
| Victimize | Recursion | Graveyard context and return are in separate clauses (fixed in 6B) | `fixed_in_6B` |
| Nyx Lotus | Mana_Acceleration | Devotion-based mana not matched by existing Mana_Production patterns (fixed in 6B) | `fixed_in_6B` |
| Lashwrithe | Threat, Finisher | Permanent_Scaling alone has no Threat/Finisher rule; scaling equipment needs its own concept | `needs_rule` |
| Sudden Spoiling | Interaction | Flash + split second prevention/combat blowout; no oracle pattern covers this | `needs_rule` |
| Prowling Geistcatcher | Fuel, Recursion | Complex sac-trigger delayed recursion/storage; no pattern covers this | `needs_rule` |