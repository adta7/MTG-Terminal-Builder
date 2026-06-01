# Deck Completion Plan

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

- **Fuel**: 0 primary cards (weighted 8.0 — target 4.0–7.0)
- **Enabler**: 1 primary cards (weighted 21.1 — target 5.5–10.0)
- **Threat**: 1 primary cards (weighted 10.8 — target 5.0–9.0)
- **Finisher**: 2 primary cards (weighted 3.9 — target 3.0–6.0)
- **Protection**: 2 primary cards (weighted 2.0 — target 2.0–4.0)

---

## Cut Priority Order

Need to free ~13 nonland slots for lands.
Listed by cut pressure. Cut from Tier 1 first.

### Tier 1 — Safest cuts (0 primary roles)

These cards contribute only secondary/incidental role depth.
The deck absorbs these cuts with minimal role impact.

| Card | CMC | Functional density | Cut pressure |
|------|-----|--------------------|--------------|
| Butcher of Malakir | 7 | 2.60 | 6.2 |
| Grave Titan | 6 | 1.65 | 3.6 |
| Grave Pact | 4 | 2.60 | 2.2 |
| Plaguecrafter | 3 | 2.60 | 2.2 |
| Woe Strider | 3 | 2.95 | 2.2 |
| Accursed Marauder | 2 | 2.60 | 2.2 |
| Pitiless Plunderer | 4 | 2.30 | 1.9 |
| Ghoulish Procession | 2 | 2.30 | 1.9 |
| Mind Stone | 2 | 1.95 | 1.9 |
| Plumb the Forbidden | 2 | 2.30 | 1.9 |
| Drivnod, Carnage Dominus | 5 | 1.30 | 1.6 |
| Disciple of Bolas | 4 | 1.30 | 1.6 |
| Ophiomancer | 3 | 1.30 | 1.6 |
| Read the Bones | 3 | 1.30 | 1.6 |
| Deadly Dispute | 2 | 1.65 | 1.6 |
| Jadar, Ghoulcaller of Nephalia | 2 | 1.30 | 1.6 |
| Night's Whisper | 2 | 1.30 | 1.6 |
| Abnormal Endurance | 2 | 1.30 | 1.6 |
| Stitcher's Supplier | 1 | 2.00 | 1.6 |
| Nyx Lotus | 4 | 0.65 | 1.3 |
| Arcane Signet | 2 | 0.65 | 1.3 |
| Cabal Ritual | 2 | 0.65 | 1.3 |
| Jet Medallion | 2 | 1.00 | 1.3 |
| Carrion Feeder | 1 | 0.65 | 1.3 |
| Dark Ritual | 1 | 0.65 | 1.3 |
| Sol Ring | 1 | 0.65 | 1.3 |
| Viscera Seer | 1 | 0.65 | 1.3 |
| Syr Konrad, the Grim | 5 | 0.35 | 1.0 |

### Tier 2 — Viable cuts (1+ primary roles)

Only cut from here if Tier 1 is exhausted.
Each cut removes some primary-role coverage — evaluate impact before cutting.

| Card | CMC | Primary roles | Functional density |
|------|-----|---------------|--------------------|
| Archon of Cruelty | 8 | 1 | 4.30 |
| Rune-Scarred Demon | 7 | 2 | 3.00 |

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