# Deck Completion Simulation

> **This is a structural path to completion, not a final decklist.**
> The model shows where it is confident, where it is uncertain, and where
> human judgment is required before any card is removed.

---

## Starting State

| Metric | Current | Target |
|--------|---------|--------|
| Total cards | 87 | 100 |
| Lands | 10 | 36–37 |
| Nonlands | 77 | ~64 |

---

## What Needs to Happen

1. Cut **13 nonlands** to open land slots.
2. Add **26 lands** to reach a functional mana base.
3. (Optional) Fill remaining card slots from collection, if any remain after cuts.

---

## Cut Path (model confidence breakdown)

Total cuts needed: **13**

### Phase 1 — Model-confident cuts (2 of 13)

The model is **high-confidence** on these. No primary roles. Clear structural pressure.
Cutting these first is the lowest-risk path.

| Card | CMC | Net score | Model confidence |
|------|-----|-----------|-----------------|
| Drivnod, Carnage Dominus | 5 | 1.60 | high |
| Nyx Lotus | 4 | 1.30 | high |

Cuts freed: **2**.  Remaining: **11**.

### Phase 2 — Borderline cuts (1 available, use if needed)

The model is **medium-confidence** on these. No primary roles, but some curve or
scarcity cost. Consider cutting these if Phase 1 alone is not enough.

| Card | CMC | Net score | Model confidence | Caution |
|------|-----|-----------|-----------------|---------|
| Read the Bones | 3 | 0.85 | medium | Has secondary Card_Draw — check draw count after cut. |

If all Phase 2 cuts are made: freed 3. Remaining: **10**.

### Phase 3 — Near-zero review (do NOT cut without explicit decision)

Net score is nearly zero — the model has almost no preference.
These should only be cut after evaluating whether their role is covered elsewhere.

| Card | CMC | Net score | Model confidence |
|------|-----|-----------|-----------------|
| Night's Whisper | 2 | 0.10 | low |
| Abnormal Endurance | 2 | 0.10 | low |

### Phase 3D — Needs role review (halt before cutting)

These cards have 0 primary roles but high functional density.
The model may be misclassifying them. Resolve primary-role status before cutting.

| Card | CMC | FDS | Net score |
|------|-----|-----|-----------|
| Mind Stone | 2 | 1.95 | 0.40 |

### Phase 4 — Human-required cuts (10 still needed)

After Phases 1–2, the model cannot confidently suggest the remaining cuts.
These must come from **Tier 2** (cards with primary roles, CMC ≥ 5).
Each cut removes primary-role coverage. Evaluate impact before deciding.

| Card | CMC | Primary roles | Net score | Model confidence | Impact |
|------|-----|---------------|-----------|-----------------|--------|
| Archon of Cruelty | 8 | 1 | 7.20 | medium | loses: Threat |
| Rune-Scarred Demon | 7 | 2 | 4.30 | medium | loses: Card_Advantage, Setup |
| Butcher of Malakir | 7 | 4 | 4.00 | medium | loses: Engine, Interaction, Removal, Threat |
| Overseer of the Damned | 7 | 2 | 4.00 | medium | loses: Interaction, Removal |
| Grave Titan | 6 | 2 | 2.30 | low | loses: Fuel, Threat |
| Nirkana Revenant | 6 | 2 | 2.30 | low | loses: Mana_Acceleration, Mana_Engine |
| Gray Merchant of Asphodel | 5 | 2 | 0.30 | low | loses: Finisher, Payoff |

---

## Cards Not Under Consideration

These cards are protected from the cut model and require explicit human approval.

| Card | Reason |
|------|--------|
| Black Market | identity_protected |
| Bolas's Citadel | identity_protected |
| Ghoulcaller Gisa | identity_protected |
| K'rrik, Son of Yawgmoth | identity_protected |
| Lashwrithe | blind_spot |
| Living Death | identity_protected |
| Prowling Geistcatcher | blind_spot |
| Sudden Spoiling | blind_spot |

---

## Land Addition Summary

After making the cuts above, add **26 lands**.
The model does not select specific lands — that is the player's decision.
Suggested composition (for reference only):

- 15–18 basic Swamps (reliable, no setup required)
- Cabal Coffers + Urborg, Tomb of Yawgmoth (if not already in list)
- 4–6 utility lands: Phyrexian Tower, Cabal Stronghold, Nykthos, Castle Locthwain
- 3–4 fetch/graveyard-synergy lands

> The player should finalize the land package based on collection, budget, and play style.

---

## Summary

| Stage | Cards | Model confidence |
|-------|-------|-----------------|
| Phase 1 — strong cuts | 2 | high |
| Phase 2 — borderline cuts | 1 | medium |
| Phase 3 — near-zero review | 2 | low (human decision) |
| Phase 3D — needs role review | 1 | low (halt before cutting) |
| Phase 4 — Tier 2 (primary-role cuts) | 10 | low (human required) |
| **Total cuts needed** | **13** | — |
| **Lands to add** | **26** | player decision |