# Deck Completion Plan

> **Status:** Cut tiers are archetype-aware.
> Primary role validation passed — all archetype-core cards have primary roles.

## Structural Gap

| Metric | Current | Target |
|--------|---------|--------|
| Deck size | 87 | 100 |
| Lands | 10 | 36–37 |
| Lands to add | 26 | — |
| Nonlands to cut | ~13 | — |

---

## Role Depth After Cuts (projected)

The deck currently has no primary-role gaps. After cutting ~13 nonlands:
- Roles where coverage is **primary-heavy** survive cuts well.
- Roles where coverage is **incidental-heavy** may actually improve (less noise).

Roles with low primary coverage — protect these:

- **Finisher**: 2 primary cards (weighted 3.9 — target 3.0–6.0)
- **Enabler**: 2 primary cards (weighted 21.5 — target 5.5–10.0)
- **Protection**: 2 primary cards (weighted 2.0 — target 2.0–4.0)

---

## Cut Priority Order

Need to free ~13 nonland slots for lands.
Listed by cut pressure. Cut from Tier 1 first.

### Tier 1 — Safest cuts (0 primary roles)

These cards contribute only secondary/incidental role depth.
The deck absorbs these cuts with minimal role impact.

| Card | CMC | Pressure | Cut cost | Net score | FDS |
|------|-----|----------|----------|-----------|-----|
| Drivnod, Carnage Dominus | 5 | 1.60 | 0.00 | 1.60 | 1.30 |
| Nyx Lotus | 4 | 1.30 | 0.00 | 1.30 | 0.65 |
| Syr Konrad, the Grim | 5 | 1.00 | 0.00 | 1.00 | 0.35 |
| Read the Bones | 3 | 1.60 | 0.75 | 0.85 | 1.30 |
| Mind Stone | 2 | 1.90 | 1.50 | 0.40 | 1.95 |
| Night's Whisper | 2 | 1.60 | 1.50 | 0.10 | 1.30 |
| Abnormal Endurance | 2 | 1.60 | 1.50 | 0.10 | 1.30 |

### Tier 2 — Viable cuts (1+ primary roles)

Only cut from here if Tier 1 is exhausted.
Each cut removes some primary-role coverage — evaluate impact before cutting.

| Card | CMC | Primary | Net score | FDS |
|------|-----|---------|-----------|-----|
| Archon of Cruelty | 8 | 1 | 7.20 | 4.30 |
| Rune-Scarred Demon | 7 | 2 | 4.30 | 3.00 |
| Butcher of Malakir | 7 | 4 | 4.00 | 4.00 |
| Overseer of the Damned | 7 | 2 | 4.00 | 2.00 |
| Grave Titan | 6 | 2 | 2.30 | 2.65 |
| Nirkana Revenant | 6 | 2 | 2.30 | 2.65 |
| Gray Merchant of Asphodel | 5 | 2 | 0.30 | 2.65 |

### Tier 3 — Do not cut (protected)

Identity-protected cards define how the deck feels.
Parser blind spots need rule fixes before evaluation.

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

## Land Recommendations

Add ~26 lands. Suggested composition:

- 15–18 basic Swamps (reliable, no downside)
- Cabal Coffers + Urborg, Tomb of Yawgmoth (big mana payoff)
- Crypt of Agadeem (already in deck)
- 4–6 utility lands: High Market (already in), Phyrexian Tower,
  Cabal Stronghold, Nykthos (devotion), Castle Locthwain
- 3–4 fetch/fixing lands for graveyard synergy or color reliability

> Land recommendations are suggestions only. Final selection should
> respect your collection, play style, and budget.