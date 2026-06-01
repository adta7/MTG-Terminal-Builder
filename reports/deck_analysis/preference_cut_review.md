# Preference-Weighted Cut Review

> Tier 2 cuts ranked by preference-adjusted net score.
> Cards scoring high here are under both structural pressure AND align with
> a pillar the player has *not* marked as high-priority to preserve.

---

## Active Preference Profile

| Preference | Weight | Meaning |
|-----------|--------|---------|
| preserve_big_mythic_threats | 0.8 | Apex threats / finishers |
| preserve_sacrifice_control | 1.5 | Edict effects / sacrifice engines |
| preserve_draw_consistency | 1.0 | Card draw / hand smoothing |
| preserve_mana_explosion | 0.8 | Mana scaling / acceleration |
| preserve_token_fuel_density | 1.2 | Token generation / fuel supply |
| preserve_recursion_density | 1.5 | Graveyard recursion |
| lower_curve_aggressively | 0.5 | Curve pressure (adds to cut pressure for CMC>4) |

---

## Tier 2 Re-Ranked (preference-adjusted, 10 still needed)

### Avoid cutting (preference-adjusted net ≤ 0)

Your preferences protect these. Do not cut without reconsidering your weights.

| Card | CMC | Adj net | Protected by |
|------|-----|---------|--------------|
| Gray Merchant of Asphodel | 5 | -1.20 | preserve_big_mythic_threats, preserve_token_fuel_density |

### Consider carefully (adj net 0–3)

Cutting these removes preferred roles. Evaluate specific impact before deciding.

| Card | CMC | Adj net | Primary roles lost | Preference categories |
|------|-----|---------|---------------------|----------------------|
| Overseer of the Damned | 7 | 2.50 | Interaction, Removal | preserve_sacrifice_control |
| Nirkana Revenant | 6 | 1.70 | Mana_Acceleration, Mana_Engine | preserve_mana_explosion |
| Grave Titan | 6 | 1.30 | Fuel, Threat | preserve_big_mythic_threats, preserve_token_fuel_density |
| Butcher of Malakir | 7 | 0.20 | Engine, Interaction, Removal, Threat | preserve_sacrifice_control, preserve_big_mythic_threats |

### Cut if needed (adj net > 3)

These have structural cut pressure that outweighs your preference protection.
Cutting from here first preserves your preferred pillars.

| Card | CMC | Base net | Adj net | Lower curve boost |
|------|-----|----------|---------|-------------------|
| Archon of Cruelty | 8 | 7.20 | 8.40 | +2.00 |
| Rune-Scarred Demon | 7 | 4.30 | 3.80 | +1.50 |

---

## How to Use This Report

1. Cut all **'cut if needed'** cards first to stay within preferred pillars.
2. If still short, move to **'consider carefully'** — review each impact.
3. **'Avoid cutting'** should only be touched after adjusting preference weights.
4. Return to `deck_gap_analysis.py → DEFAULT_PREFERENCES` to tune weights.