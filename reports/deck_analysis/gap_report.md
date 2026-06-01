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

## Role Counts vs Targets *(Diagnostic only)*

- **Raw** = cards with this role (any priority)
- **Primary** = cards where this is a primary role (weight 1.0)
- **Weighted** = sum of weights (primary=1.0, secondary=0.65, incidental=0.35)
- **W-Status** = weighted total vs weighted target range

| Role | Raw | Primary | Weighted | Ideal (raw) | W-Target | Status | W-Status |
|------|-----|---------|----------|-------------|----------|--------|----------|
| Finisher | 5 | 2 | 3.9 | 3–6 | 3.0–6.0 | OK | W_OK |
| Setup | 6 | 5 | 5.7 | 4–7 | 3.5–6.5 | OK | W_OK |
| Protection | 2 | 2 | 2.0 | 2–4 | 2.0–4.0 | OK | W_OK |
| Mana_Acceleration | 16 | 3 | 11.2 | 11–14 | 8.0–12.0 | SLIGHTLY HIGH | W_OK |
| Card_Draw | 14 | 5 | 10.9 | 9–12 | 7.0–11.0 | SLIGHTLY HIGH | W_OK |
| Mana_Engine | 7 | 4 | 6.0 | 2–4 | 2.0–5.0 | HIGH | W_SLIGHTLY_HIGH |
| Removal | 15 | 7 | 11.9 | 9–12 | 8.0–12.0 | HIGH | W_OK |
| Engine | 28 | 6 | 18.2 | 10–16 | 8.0–14.0 | HIGH | W_HIGH |
| Payoff | 20 | 4 | 14.4 | 6–10 | 5.0–9.0 | HIGH | W_HIGH |
| Fuel | 15 | 0 | 8.0 | 5–8 | 4.0–7.0 | HIGH | W_SLIGHTLY_HIGH |
| Recursion | 16 | 14 | 15.3 | 6–9 | 6.0–10.0 | HIGH | W_HIGH |
| Conversion | 20 | 5 | 12.3 | 5–8 | 4.0–7.0 | HIGH | W_HIGH |
| Enabler | 32 | 1 | 21.1 | 7–12 | 5.5–10.0 | HIGH | W_HIGH |
| Interaction | 14 | 5 | 10.9 | 6–9 | 5.0–8.0 | HIGH | W_HIGH |
| Threat | 16 | 1 | 10.8 | 6–10 | 5.0–9.0 | HIGH | W_SLIGHTLY_HIGH |

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
| Archon of Cruelty | 8 | Removal, Engine, Interaction, Threat, Payoff, Card_Draw |
| Butcher of Malakir | 7 | Interaction, Removal, Engine, Threat |
| Overseer of the Damned | 7 | Interaction, Removal |
| Rune-Scarred Demon | 7 | Enabler |
| Sheoldred, Whispering One | 7 | Removal, Engine, Enabler, Interaction, Threat, Recursion |
| Grave Titan | 6 | Threat, Payoff, Fuel |
| Nirkana Revenant | 6 | Mana_Acceleration, Mana_Engine |

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