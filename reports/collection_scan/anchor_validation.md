# Anchor Card Validation

**Run:** 2026-05-30 14:32

Cards that define the deck's strategic identity. Missing tags here are high-priority gaps.


## Ashnod's Altar — ✓ OK
- Expected: ['Sacrifice_Outlet', 'Mana_Production']
- Actual: ['Mana_Production', 'Sacrifice_Outlet']

## Viscera Seer — ✓ OK
- Expected: ['Sacrifice_Outlet']
- Actual: ['Sacrifice_Outlet']

## Blood Artist — ✓ OK
- Expected: ['Death_Trigger', 'Life_Drain']
- Actual: ['Death_Trigger', 'Life_Drain', 'Life_Gain']

## Grave Pact — ✓ OK
- Expected: ['Death_Trigger', 'Forced_Sacrifice']
- Actual: ['Death_Trigger', 'Forced_Sacrifice']

## Living Death — ✓ OK
- Expected: ['Mass_Reanimate']
- Actual: ['Mass_Reanimate']

## Animate Dead — ✓ OK
- Expected: ['Reanimation']
- Actual: ['ETB_Trigger', 'Reanimation']

## Sheoldred, Whispering One — ✓ OK
- Expected: ['Reanimation', 'Forced_Sacrifice']
- Actual: ['Evasion', 'Forced_Sacrifice', 'Reanimation', 'Upkeep_Trigger']

## Ghoulcaller Gisa — ✓ OK
- Expected: ['Sacrifice_Outlet', 'Token_Generation']
- Actual: ['Sacrifice_Outlet', 'Token_Generation']

## Bolas's Citadel — ✓ OK
- Expected: ['Life_Drain']
- Actual: ['Life_Drain', 'Life_Payment', 'Sacrifice_Outlet']

## Phyrexian Arena — ✓ OK
- Expected: ['Draw_Effect']
- Actual: ['Draw_Effect', 'Life_Payment', 'Upkeep_Trigger']

## Black Market — ✓ OK
- Expected: ['Scales_With_Deaths', 'Mana_Production']
- Actual: ['Death_Trigger', 'Mana_Production', 'Scales_With_Deaths', 'Upkeep_Trigger']

## Crypt Ghast — ✓ OK
- Expected: ['Mana_Multiplier']
- Actual: ['Extort', 'Mana_Multiplier']

## Necropotence — — NOT IN COLLECTION
- Expected: ['Life_Payment']
- Actual: []
- **Missing tags: ['Life_Payment']**
- *Card not in collection — add it to validate.*

## Demonic Tutor — — NOT IN COLLECTION
- Expected: ['Tutor_Effect']
- Actual: []
- **Missing tags: ['Tutor_Effect']**
- *Card not in collection — add it to validate.*

## Bitterblossom — — NOT IN COLLECTION
- Expected: ['Repeatable_Token_Generation']
- Actual: []
- **Missing tags: ['Repeatable_Token_Generation']**
- *Card not in collection — add it to validate.*