# Functional Role Report — Collection Scan

Layer 3 derivation applied to 347 black/colorless collection cards.
Rules fire when a card's mechanical tags satisfy the required set.

## Role Summary

| Role | Cards |
|------|-------|
| Engine | 50 |
| Conversion | 34 |
| Payoff | 46 |
| Fuel | 36 |
| Recursion | 36 |
| Finisher | 14 |
| Finisher_Support | 26 |
| Mana_Engine | 13 |
| Mana_Acceleration | 41 |
| Card_Draw | 47 |
| Card_Advantage | 64 |
| Enabler | 69 |
| Setup | 22 |
| Removal | 49 |
| Interaction | 44 |
| Threat | 41 |
| Protection | 5 |
| *(no functional role)* | 122 |

## Watchlist: Deck Identity Cards

### Ashnod's Altar
- **Mechanical:** Mana_Production, Sacrifice_Outlet
- **Functional:** Conversion, Enabler, Engine, Mana_Acceleration, Mana_Engine
- **Rules that fired:**
  - `Mana_Production + Sacrifice_Outlet` → **Engine** (90%)
  - `Mana_Production + Sacrifice_Outlet` → **Conversion** (90%)
  - `Mana_Production + Sacrifice_Outlet` → **Mana_Engine** (85%)
  - `Sacrifice_Outlet` → **Enabler** (80%)
  - `Mana_Production` → **Mana_Acceleration** (75%)

### Blood Artist
- **Mechanical:** Death_Trigger, Life_Drain, Life_Gain
- **Functional:** Payoff, Threat
- **Rules that fired:**
  - `Death_Trigger + Life_Drain` → **Payoff** (90%)
  - `Death_Trigger + Life_Drain` → **Threat** (75%)

### Grave Pact
- **Mechanical:** Death_Trigger, Forced_Sacrifice
- **Functional:** Engine, Interaction, Removal, Threat
- **Rules that fired:**
  - `Forced_Sacrifice` → **Removal** (85%)
  - `Forced_Sacrifice` → **Interaction** (85%)
  - `Death_Trigger + Forced_Sacrifice` → **Engine** (85%)
  - `Death_Trigger + Forced_Sacrifice` → **Threat** (80%)

### Living Death
- **Mechanical:** Mass_Reanimate
- **Functional:** Enabler, Finisher, Recursion
- **Rules that fired:**
  - `Mass_Reanimate` → **Recursion** (95%)
  - `Mass_Reanimate` → **Finisher** (70%)
  - `Mass_Reanimate` → **Enabler** (70%)

### Ghoulcaller Gisa
- **Mechanical:** Sacrifice_Outlet, Token_Generation
- **Functional:** Conversion, Enabler, Engine, Fuel, Threat
- **Rules that fired:**
  - `Sacrifice_Outlet + Token_Generation` → **Engine** (80%)
  - `Sacrifice_Outlet` → **Enabler** (80%)
  - `Sacrifice_Outlet + Token_Generation` → **Conversion** (80%)
  - `Sacrifice_Outlet + Token_Generation` → **Threat** (70%)
  - `Token_Generation` → **Fuel** (65%)

### Bolas's Citadel
- **Mechanical:** Life_Drain, Life_Payment, Sacrifice_Outlet
- **Functional:** Conversion, Enabler, Engine, Finisher
- **Rules that fired:**
  - `Sacrifice_Outlet` → **Enabler** (80%)
  - `Life_Drain + Sacrifice_Outlet` → **Finisher** (75%)
  - `Life_Payment` → **Engine** (65%)
  - `Life_Payment` → **Conversion** (65%)

### Black Market
- **Mechanical:** Death_Trigger, Mana_Production, Scales_With_Deaths, Upkeep_Trigger
- **Functional:** Conversion, Engine, Mana_Acceleration, Mana_Engine, Payoff
- **Rules that fired:**
  - `Mana_Production + Upkeep_Trigger` → **Mana_Engine** (85%)
  - `Death_Trigger + Mana_Production` → **Engine** (85%)
  - `Scales_With_Deaths` → **Payoff** (80%)
  - `Mana_Production` → **Mana_Acceleration** (75%)
  - `Mana_Production + Scales_With_Deaths` → **Conversion** (75%)

### Sheoldred, Whispering One
- **Mechanical:** Evasion, Forced_Sacrifice, Reanimation, Upkeep_Trigger
- **Functional:** Enabler, Engine, Interaction, Recursion, Removal, Threat
- **Rules that fired:**
  - `Reanimation` → **Recursion** (95%)
  - `Forced_Sacrifice` → **Removal** (85%)
  - `Forced_Sacrifice` → **Interaction** (85%)
  - `Forced_Sacrifice + Upkeep_Trigger` → **Threat** (85%)
  - `Reanimation + Upkeep_Trigger` → **Engine** (85%)

### Phyrexian Arena
- **Mechanical:** Draw_Effect, Life_Payment, Upkeep_Trigger
- **Functional:** Card_Advantage, Card_Draw, Conversion, Engine, Payoff
- **Rules that fired:**
  - `Draw_Effect + Upkeep_Trigger` → **Card_Draw** (90%)
  - `Draw_Effect + Upkeep_Trigger` → **Card_Advantage** (90%)
  - `Draw_Effect + Upkeep_Trigger` → **Engine** (85%)
  - `Draw_Effect + Life_Payment` → **Conversion** (85%)
  - `Draw_Effect + Upkeep_Trigger` → **Payoff** (80%)

### Crypt Ghast
- **Mechanical:** Extort, Mana_Multiplier
- **Functional:** Finisher_Support, Mana_Acceleration, Mana_Engine, Payoff
- **Rules that fired:**
  - `Mana_Multiplier` → **Mana_Acceleration** (90%)
  - `Mana_Multiplier` → **Mana_Engine** (90%)
  - `Mana_Multiplier` → **Finisher_Support** (80%)
  - `Extort` → **Payoff** (70%)

### Viscera Seer
- **Mechanical:** Sacrifice_Outlet
- **Functional:** Enabler
- **Rules that fired:**
  - `Sacrifice_Outlet` → **Enabler** (80%)

### Nirkana Revenant
- **Mechanical:** Mana_Multiplier
- **Functional:** Finisher_Support, Mana_Acceleration, Mana_Engine
- **Rules that fired:**
  - `Mana_Multiplier` → **Mana_Acceleration** (90%)
  - `Mana_Multiplier` → **Mana_Engine** (90%)
  - `Mana_Multiplier` → **Finisher_Support** (80%)

### Yawgmoth, Thran Physician
- **Mechanical:** Draw_Effect, Life_Payment, Sacrifice_Outlet
- **Functional:** Card_Advantage, Card_Draw, Conversion, Enabler, Engine
- **Rules that fired:**
  - `Draw_Effect + Sacrifice_Outlet` → **Engine** (90%)
  - `Draw_Effect + Sacrifice_Outlet` → **Conversion** (90%)
  - `Draw_Effect` → **Card_Draw** (85%)
  - `Draw_Effect` → **Card_Advantage** (80%)
  - `Sacrifice_Outlet` → **Enabler** (80%)

### Diabolic Tutor
- **Mechanical:** Tutor_Effect
- **Functional:** Card_Advantage, Enabler, Finisher_Support, Setup
- **Rules that fired:**
  - `Tutor_Effect` → **Card_Advantage** (90%)
  - `Tutor_Effect` → **Setup** (90%)
  - `Tutor_Effect` → **Enabler** (80%)
  - `Tutor_Effect` → **Finisher_Support** (65%)

## Functional Roles Detail

### Engine (50 cards)

- **Archon of Cruelty** via `Draw_Effect + Forced_Sacrifice` | also: Card_Advantage, Card_Draw, Interaction, Payoff, Removal, Threat
- **Ashnod's Altar** via `Mana_Production + Sacrifice_Outlet` | also: Conversion, Enabler, Mana_Acceleration, Mana_Engine
- **Black Market** via `Death_Trigger + Mana_Production` | also: Conversion, Mana_Acceleration, Mana_Engine, Payoff
- **Blighted Blackthorn** via `Life_Payment` | also: Card_Advantage, Card_Draw, Conversion, Payoff, Threat
- **Bolas's Citadel** via `Life_Payment` | also: Conversion, Enabler, Finisher
- **Braids, Arisen Nightmare** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Interaction, Payoff, Removal, Threat
- **Butcher of Malakir** via `Death_Trigger + Forced_Sacrifice` | also: Interaction, Removal, Threat
- **Ceremonial Knife** via `Repeatable_Token_Generation` | also: Fuel
- **Chainer, Dementia Master** via `Life_Payment` | also: Conversion
- **Crypt of Agadeem** via `Mana_Production + Scales_With_Deaths` | also: Conversion, Mana_Acceleration, Mana_Engine, Payoff
- **Drivnod, Carnage Dominus** via `Trigger_Doubler` | also: Enabler
- **Erebos, Bleak-Hearted** via `Draw_Effect + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Payoff
- **Foreboding Statue // Forsaken Thresher** via `Mana_Production + Upkeep_Trigger` | also: Mana_Acceleration, Mana_Engine
- **Ghoulcaller Gisa** via `Sacrifice_Outlet + Token_Generation` | also: Conversion, Enabler, Fuel, Threat
- **Ghoulish Procession** via `Repeatable_Token_Generation` | also: Conversion, Fuel, Payoff
- **Grave Pact** via `Death_Trigger + Forced_Sacrifice` | also: Interaction, Removal, Threat
- **Grim Haruspex** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Payoff
- **Hell's Caretaker** via `Reanimation + Sacrifice_Outlet` | also: Enabler, Recursion
- **Ifnir Deadlands** via `Life_Payment` | also: Conversion
- **Indulgent Tormentor** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Interaction, Payoff, Removal, Threat
- **Jadar, Ghoulcaller of Nephalia** via `Repeatable_Token_Generation` | also: Fuel
- **K'rrik, Son of Yawgmoth** via `Life_Payment` | also: Conversion
- **Liliana, the Last Hope** via `Repeatable_Token_Generation` | also: Enabler, Finisher_Support, Fuel, Recursion, Setup
- **Midnight Reaper** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Payoff
- **Morbid Opportunist** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Payoff
- **Moseo, Vein's New Dean** via `Reanimation + Upkeep_Trigger` | also: Enabler, Fuel, Payoff, Recursion, Threat
- **Ob Nixilis of the Black Oath** via `Draw_Effect + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Finisher, Fuel, Threat
- **Open the Graves** via `Repeatable_Token_Generation` | also: Conversion, Fuel, Payoff
- **Ophiomancer** via `Repeatable_Token_Generation` | also: Fuel
- **Pawn of Ulamog** via `Mana_Production + Sacrifice_Outlet` | also: Conversion, Enabler, Fuel, Mana_Acceleration, Mana_Engine, Payoff, Threat
- **Phyrexian Arena** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Conversion, Payoff
- **Phyrexian Reclamation** via `Life_Payment` | also: Conversion, Recursion
- **Pitiless Plunderer** via `Repeatable_Token_Generation` | also: Conversion, Fuel, Payoff
- **Plumb the Forbidden** via `Life_Payment` | also: Card_Advantage, Card_Draw, Conversion
- **Priest of Forgotten Gods** via `Mana_Production + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Mana_Acceleration, Mana_Engine
- **Sheoldred, Whispering One** via `Reanimation + Upkeep_Trigger` | also: Enabler, Interaction, Recursion, Removal, Threat
- **Sinister Gnarlbark** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Payoff
- **Skullclamp** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Payoff
- **Smothering Abomination** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Payoff
- **Songs of the Damned** via `Mana_Production + Scales_With_Deaths` | also: Conversion, Mana_Acceleration, Mana_Engine, Payoff
- **Staff of Compleation** via `Life_Payment` | also: Card_Advantage, Card_Draw, Conversion, Interaction, Mana_Acceleration, Removal
- **Taborax, Hope's Demise** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Payoff, Threat
- **The Black Gate** via `Life_Payment` | also: Conversion
- **Toxic Deluge** via `Life_Payment` | also: Conversion, Interaction, Removal
- **Treasure** via `Mana_Production + Sacrifice_Outlet` | also: Conversion, Enabler, Mana_Acceleration, Mana_Engine
- **Vampiric Rites** via `Draw_Effect + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler
- **Vraska, Betrayal's Sting** via `Mana_Production + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Finisher, Mana_Acceleration, Mana_Engine
- **Whisper, Blood Liturgist** via `Reanimation + Sacrifice_Outlet` | also: Enabler, Recursion
- **Woe Strider** via `Sacrifice_Outlet + Token_Generation` | also: Conversion, Enabler, Fuel, Threat
- **Yawgmoth, Thran Physician** via `Draw_Effect + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler

### Conversion (34 cards)

- **Ashnod's Altar** via `Mana_Production + Sacrifice_Outlet` | also: Enabler, Engine, Mana_Acceleration, Mana_Engine
- **Black Market** via `Mana_Production + Scales_With_Deaths` | also: Engine, Mana_Acceleration, Mana_Engine, Payoff
- **Blight Mound** via `Death_Trigger + Token_Generation` | also: Fuel, Payoff
- **Blighted Blackthorn** via `Draw_Effect + Life_Payment` | also: Card_Advantage, Card_Draw, Engine, Payoff, Threat
- **Bolas's Citadel** via `Life_Payment` | also: Enabler, Engine, Finisher
- **Chainer, Dementia Master** via `Life_Payment` | also: Engine
- **Crypt of Agadeem** via `Mana_Production + Scales_With_Deaths` | also: Engine, Mana_Acceleration, Mana_Engine, Payoff
- **Erebos, Bleak-Hearted** via `Draw_Effect + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Enabler, Engine, Payoff
- **Ghoulcaller Gisa** via `Sacrifice_Outlet + Token_Generation` | also: Enabler, Engine, Fuel, Threat
- **Ghoulish Procession** via `Death_Trigger + Token_Generation` | also: Engine, Fuel, Payoff
- **Grim Haruspex** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Engine, Payoff
- **Ifnir Deadlands** via `Life_Payment` | also: Engine
- **K'rrik, Son of Yawgmoth** via `Life_Payment` | also: Engine
- **Midnight Reaper** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Engine, Payoff
- **Morbid Opportunist** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Engine, Payoff
- **Ob Nixilis of the Black Oath** via `Draw_Effect + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Enabler, Engine, Finisher, Fuel, Threat
- **Open the Graves** via `Death_Trigger + Token_Generation` | also: Engine, Fuel, Payoff
- **Pawn of Ulamog** via `Mana_Production + Sacrifice_Outlet` | also: Enabler, Engine, Fuel, Mana_Acceleration, Mana_Engine, Payoff, Threat
- **Phyrexian Arena** via `Draw_Effect + Life_Payment` | also: Card_Advantage, Card_Draw, Engine, Payoff
- **Phyrexian Reclamation** via `Life_Payment + Recursion_To_Hand` | also: Engine, Recursion
- **Pitiless Plunderer** via `Death_Trigger + Token_Generation` | also: Engine, Fuel, Payoff
- **Plumb the Forbidden** via `Draw_Effect + Life_Payment` | also: Card_Advantage, Card_Draw, Engine
- **Priest of Forgotten Gods** via `Mana_Production + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Enabler, Engine, Mana_Acceleration, Mana_Engine
- **Skullclamp** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Engine, Payoff
- **Songs of the Damned** via `Mana_Production + Scales_With_Deaths` | also: Engine, Mana_Acceleration, Mana_Engine, Payoff
- **Staff of Compleation** via `Life_Payment + Mana_Production` | also: Card_Advantage, Card_Draw, Engine, Interaction, Mana_Acceleration, Removal
- **Taborax, Hope's Demise** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Engine, Payoff, Threat
- **The Black Gate** via `Life_Payment` | also: Engine
- **Toxic Deluge** via `Life_Payment` | also: Engine, Interaction, Removal
- **Treasure** via `Mana_Production + Sacrifice_Outlet` | also: Enabler, Engine, Mana_Acceleration, Mana_Engine
- **Vampiric Rites** via `Draw_Effect + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Enabler, Engine
- **Vraska, Betrayal's Sting** via `Mana_Production + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Enabler, Engine, Finisher, Mana_Acceleration, Mana_Engine
- **Woe Strider** via `Sacrifice_Outlet + Token_Generation` | also: Enabler, Engine, Fuel, Threat
- **Yawgmoth, Thran Physician** via `Draw_Effect + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Enabler, Engine

### Payoff (46 cards)

- **Accursed Marauder** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Removal, Threat
- **Archon of Cruelty** via `ETB_Trigger + Life_Drain` | also: Card_Advantage, Card_Draw, Engine, Interaction, Removal, Threat
- **Black Market** via `Scales_With_Deaths` | also: Conversion, Engine, Mana_Acceleration, Mana_Engine
- **Blight Mound** via `Death_Trigger + Life_Gain` | also: Conversion, Fuel
- **Blighted Blackthorn** via `ETB_Trigger + Life_Drain` | also: Card_Advantage, Card_Draw, Conversion, Engine, Threat
- **Blood Artist** via `Death_Trigger + Life_Drain` | also: Threat
- **Bloodgift Demon** via `Life_Drain + Upkeep_Trigger` | also: Threat
- **Braids, Arisen Nightmare** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Engine, Interaction, Removal, Threat
- **Crypt Ghast** via `Extort` | also: Finisher_Support, Mana_Acceleration, Mana_Engine
- **Crypt of Agadeem** via `Scales_With_Deaths` | also: Conversion, Engine, Mana_Acceleration, Mana_Engine
- **Dawnhand Eulogist** via `ETB_Trigger + Life_Drain` | also: Enabler, Finisher_Support, Fuel, Setup, Threat
- **Defiling Daemogoth** via `Combat_Trigger + Life_Drain` | also: Finisher, Threat
- **Erebos, Bleak-Hearted** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine
- **Falkenrath Noble** via `Death_Trigger + Life_Drain` | also: Threat
- **Fleshbag Marauder** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Removal, Threat
- **Ghoulish Procession** via `Death_Trigger + Token_Generation` | also: Conversion, Engine, Fuel
- **Grave Titan** via `Combat_Trigger + Token_Generation` | also: Fuel, Threat
- **Grave Venerations** via `Death_Trigger + Life_Drain` | also: Threat
- **Gray Merchant of Asphodel** via `Devotion_Effect + Life_Drain` | also: Finisher, Threat
- **Grim Haruspex** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Engine
- **Indulgent Tormentor** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Engine, Interaction, Removal, Threat
- **Merchant of Venom** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Removal, Threat
- **Merciless Executioner** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Removal, Threat
- **Midnight Reaper** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Engine
- **Morbid Opportunist** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Engine
- **Moseo, Vein's New Dean** via `Combat_Trigger + Token_Generation` | also: Enabler, Engine, Fuel, Recursion, Threat
- **Open the Graves** via `Death_Trigger + Token_Generation` | also: Conversion, Engine, Fuel
- **Palace Siege** via `Life_Drain + Upkeep_Trigger` | also: Recursion
- **Pawn of Ulamog** via `Death_Trigger + Token_Generation` | also: Conversion, Enabler, Engine, Fuel, Mana_Acceleration, Mana_Engine, Threat
- **Phyrexian Arena** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Conversion, Engine
- **Pitiless Plunderer** via `Death_Trigger + Token_Generation` | also: Conversion, Engine, Fuel
- **Plaguecrafter** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Removal, Threat
- **Pontiff of Blight** via `Extort`
- **Rogue's Gloves** via `Combat_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw
- **Sinister Gnarlbark** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Engine
- **Skullclamp** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Engine
- **Skymarch Bloodletter** via `ETB_Trigger + Life_Drain` | also: Threat
- **Smothering Abomination** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Engine
- **Sneering Shadewriter** via `ETB_Trigger + Life_Drain` | also: Threat
- **Songs of the Damned** via `Scales_With_Deaths` | also: Conversion, Engine, Mana_Acceleration, Mana_Engine
- **Stensian Sanguinist // Exsanguinate** via `Combat_Trigger + Life_Drain` | also: Finisher, Threat
- **Strength-Testing Hammer** via `Combat_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw
- **Taborax, Hope's Demise** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Card_Draw, Conversion, Engine, Threat
- **Vampire Sovereign** via `ETB_Trigger + Life_Drain` | also: Threat
- **Vraan, Executioner Thane** via `Death_Trigger + Life_Drain` | also: Threat
- **Zulaport Cutthroat** via `Death_Trigger + Life_Drain` | also: Threat

### Fuel (36 cards)

- **Abnormal Endurance** via `Return_Self_From_Graveyard` | also: Recursion
- **Blight Mound** via `Token_Generation` | also: Conversion, Payoff
- **Blood Servitor** via `Token_Generation`
- **Blood Speaker** via `Return_Self_From_Graveyard` | also: Card_Advantage, Enabler, Finisher_Support, Recursion, Setup
- **Bloodghast** via `Return_Self_From_Graveyard` | also: Enabler, Recursion
- **Ceremonial Knife** via `Repeatable_Token_Generation` | also: Engine
- **Concession Stand** via `Token_Generation`
- **Dawnhand Eulogist** via `Self_Mill` | also: Enabler, Finisher_Support, Payoff, Setup, Threat
- **Deadly Dispute** via `Token_Generation` | also: Card_Advantage, Card_Draw
- **Evernight Shade** via `Undying_Persist`
- **Ghoulcaller Gisa** via `Token_Generation` | also: Conversion, Enabler, Engine, Threat
- **Ghoulish Procession** via `Repeatable_Token_Generation` | also: Conversion, Engine, Payoff
- **Grave Titan** via `Token_Generation` | also: Payoff, Threat
- **Incarnation Technique** via `Self_Mill` | also: Enabler, Finisher_Support, Recursion, Setup
- **Jadar, Ghoulcaller of Nephalia** via `Repeatable_Token_Generation` | also: Engine
- **Kalitas, Traitor of Ghet** via `Token_Generation`
- **Liliana, the Last Hope** via `Repeatable_Token_Generation` | also: Enabler, Engine, Finisher_Support, Recursion, Setup
- **Malakir Rebirth // Malakir Mire** via `Return_Self_From_Graveyard` | also: Recursion
- **Moseo, Vein's New Dean** via `Token_Generation` | also: Enabler, Engine, Payoff, Recursion, Threat
- **Nether Traitor** via `Return_Self_From_Graveyard` | also: Enabler, Recursion
- **Ob Nixilis of the Black Oath** via `Token_Generation` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine, Finisher, Threat
- **Open the Graves** via `Repeatable_Token_Generation` | also: Conversion, Engine, Payoff
- **Ophiomancer** via `Repeatable_Token_Generation` | also: Engine
- **Pawn of Ulamog** via `Token_Generation` | also: Conversion, Enabler, Engine, Mana_Acceleration, Mana_Engine, Payoff, Threat
- **Pitiless Plunderer** via `Repeatable_Token_Generation` | also: Conversion, Engine, Payoff
- **Puppeteer Clique** via `Undying_Persist`
- **Reassembling Skeleton** via `Return_Self_From_Graveyard` | also: Enabler, Recursion
- **Rise of the Dread Marn** via `Token_Generation`
- **Scarblade Scout** via `Self_Mill` | also: Enabler, Finisher_Support, Setup
- **Skirsdag High Priest** via `Token_Generation`
- **Stalactite Dagger** via `Token_Generation`
- **Stitcher's Supplier** via `Self_Mill` | also: Enabler, Finisher_Support, Setup
- **Tenacious Dead** via `Return_Self_From_Graveyard` | also: Recursion
- **The Superlatorium** via `Token_Generation`
- **Vile Rebirth** via `Token_Generation` | also: Interaction, Removal
- **Woe Strider** via `Token_Generation` | also: Conversion, Enabler, Engine, Threat

### Recursion (36 cards)

- **Abnormal Endurance** via `Return_Self_From_Graveyard` | also: Fuel
- **Animate Dead** via `Reanimation` | also: Enabler
- **Blood Speaker** via `Recursion_To_Hand` | also: Card_Advantage, Enabler, Finisher_Support, Fuel, Setup
- **Bloodghast** via `Reanimation` | also: Enabler, Fuel
- **Chthonian Nightmare** via `Reanimation` | also: Enabler
- **Doomed Necromancer** via `Reanimation` | also: Enabler
- **Dread Return** via `Reanimation` | also: Enabler
- **Dross Skullbomb** via `Recursion_To_Hand` | also: Card_Advantage, Card_Draw
- **Gisa, Glorious Resurrector** via `Mass_Reanimate` | also: Enabler, Finisher
- **Gravedig** via `Recursion_To_Hand`
- **Gravedigger** via `Recursion_To_Hand`
- **Gravewaker** via `Reanimation` | also: Enabler
- **Grim Discovery** via `Recursion_To_Hand`
- **Hell's Caretaker** via `Reanimation` | also: Enabler, Engine
- **Incarnation Technique** via `Reanimation` | also: Enabler, Finisher_Support, Fuel, Setup
- **Infernal Offering** via `Reanimation` | also: Enabler
- **Liliana, Death Wielder** via `Reanimation` | also: Enabler, Interaction, Removal
- **Liliana, the Last Hope** via `Recursion_To_Hand` | also: Enabler, Engine, Finisher_Support, Fuel, Setup
- **Liliana, the Necromancer** via `Recursion_To_Hand`
- **Living Death** via `Mass_Reanimate` | also: Enabler, Finisher
- **Malakir Rebirth // Malakir Mire** via `Return_Self_From_Graveyard` | also: Fuel
- **Moseo, Vein's New Dean** via `Reanimation` | also: Enabler, Engine, Fuel, Payoff, Threat
- **Nether Traitor** via `Reanimation` | also: Enabler, Fuel
- **Oversold Cemetery** via `Recursion_To_Hand`
- **Palace Siege** via `Recursion_To_Hand` | also: Payoff
- **Persist** via `Reanimation` | also: Enabler
- **Phyrexian Reclamation** via `Recursion_To_Hand` | also: Conversion, Engine
- **Profane Command** via `Reanimation` | also: Enabler, Finisher, Threat
- **Reassembling Skeleton** via `Reanimation` | also: Enabler, Fuel
- **Rise of the Dark Realms** via `Mass_Reanimate` | also: Enabler, Finisher
- **Sheoldred, Whispering One** via `Reanimation` | also: Enabler, Engine, Interaction, Removal, Threat
- **Stitch Together** via `Reanimation` | also: Enabler
- **Tenacious Dead** via `Return_Self_From_Graveyard` | also: Fuel
- **Veinwitch Coven** via `Recursion_To_Hand`
- **Wake the Dead** via `Reanimation` | also: Enabler, Finisher
- **Whisper, Blood Liturgist** via `Reanimation` | also: Enabler, Engine

### Finisher (14 cards)

- **Bolas's Citadel** via `Life_Drain + Sacrifice_Outlet` | also: Conversion, Enabler, Engine
- **Bubbling Cauldron** via `Life_Drain + Sacrifice_Outlet` | also: Enabler
- **Defiling Daemogoth** via `Life_Drain + X_Spell_Effect` | also: Payoff, Threat
- **Exsanguinate** via `Life_Drain + X_Spell_Effect`
- **Gisa, Glorious Resurrector** via `Mass_Reanimate` | also: Enabler, Recursion
- **Gnawing Zombie** via `Life_Drain + Sacrifice_Outlet` | also: Enabler
- **Gray Merchant of Asphodel** via `Life_Drain + X_Spell_Effect` | also: Payoff, Threat
- **Living Death** via `Mass_Reanimate` | also: Enabler, Recursion
- **Ob Nixilis of the Black Oath** via `Life_Drain + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine, Fuel, Threat
- **Profane Command** via `Life_Drain + X_Spell_Effect` | also: Enabler, Recursion, Threat
- **Rise of the Dark Realms** via `Mass_Reanimate` | also: Enabler, Recursion
- **Stensian Sanguinist // Exsanguinate** via `Life_Drain + X_Spell_Effect` | also: Payoff, Threat
- **Vraska, Betrayal's Sting** via `Life_Drain + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine, Mana_Acceleration, Mana_Engine
- **Wake the Dead** via `Mass_Reanimate` | also: Enabler, Recursion

### Finisher_Support (26 cards)

- **Blood Speaker** via `Tutor_Effect` | also: Card_Advantage, Enabler, Fuel, Recursion, Setup
- **Bogbrew Witch** via `Tutor_Effect` | also: Card_Advantage, Enabler, Setup
- **Bubbling Muck** via `Mana_Multiplier` | also: Mana_Acceleration, Mana_Engine
- **Buried Alive** via `Tutor_Effect` | also: Card_Advantage, Enabler, Setup
- **Burnished Hart** via `Tutor_Effect` | also: Card_Advantage, Enabler, Mana_Acceleration, Setup
- **Crypt Ghast** via `Mana_Multiplier` | also: Mana_Acceleration, Mana_Engine, Payoff
- **Dawnhand Eulogist** via `Self_Mill` | also: Enabler, Fuel, Payoff, Setup, Threat
- **Diabolic Intent** via `Tutor_Effect` | also: Card_Advantage, Enabler, Setup
- **Diabolic Tutor** via `Tutor_Effect` | also: Card_Advantage, Enabler, Setup
- **Evolving Wilds** via `Tutor_Effect` | also: Card_Advantage, Enabler, Mana_Acceleration, Setup
- **Fabled Passage** via `Tutor_Effect` | also: Card_Advantage, Enabler, Mana_Acceleration, Setup
- **Grim Servant** via `Tutor_Effect` | also: Card_Advantage, Enabler, Setup
- **Incarnation Technique** via `Self_Mill` | also: Enabler, Fuel, Recursion, Setup
- **Insatiable Avarice** via `Tutor_Effect` | also: Card_Advantage, Enabler, Setup
- **Liliana of the Dark Realms** via `Tutor_Effect` | also: Card_Advantage, Enabler, Mana_Acceleration, Setup
- **Liliana, the Last Hope** via `Self_Mill` | also: Enabler, Engine, Fuel, Recursion, Setup
- **Magus of the Coffers** via `Mana_Production + Permanent_Scaling` | also: Mana_Acceleration, Mana_Engine
- **Myriad Landscape** via `Tutor_Effect` | also: Card_Advantage, Enabler, Mana_Acceleration, Setup
- **Nirkana Revenant** via `Mana_Multiplier` | also: Mana_Acceleration, Mana_Engine
- **Park Map** via `Tutor_Effect` | also: Card_Advantage, Enabler, Mana_Acceleration, Setup
- **Profane Tutor** via `Tutor_Effect` | also: Card_Advantage, Enabler, Setup
- **Riveteers Overlook** via `Tutor_Effect` | also: Card_Advantage, Enabler, Mana_Acceleration, Setup
- **Rune-Scarred Demon** via `Tutor_Effect` | also: Card_Advantage, Enabler, Setup
- **Scarblade Scout** via `Self_Mill` | also: Enabler, Fuel, Setup
- **Stitcher's Supplier** via `Self_Mill` | also: Enabler, Fuel, Setup
- **Terramorphic Expanse** via `Tutor_Effect` | also: Card_Advantage, Enabler, Mana_Acceleration, Setup

### Mana_Engine (13 cards)

- **Ashnod's Altar** via `Mana_Production + Sacrifice_Outlet` | also: Conversion, Enabler, Engine, Mana_Acceleration
- **Black Market** via `Mana_Production + Upkeep_Trigger` | also: Conversion, Engine, Mana_Acceleration, Payoff
- **Bubbling Muck** via `Mana_Multiplier` | also: Finisher_Support, Mana_Acceleration
- **Crypt Ghast** via `Mana_Multiplier` | also: Finisher_Support, Mana_Acceleration, Payoff
- **Crypt of Agadeem** via `Mana_Production + Scales_With_Deaths` | also: Conversion, Engine, Mana_Acceleration, Payoff
- **Foreboding Statue // Forsaken Thresher** via `Mana_Production + Upkeep_Trigger` | also: Engine, Mana_Acceleration
- **Magus of the Coffers** via `Mana_Production + Permanent_Scaling` | also: Finisher_Support, Mana_Acceleration
- **Nirkana Revenant** via `Mana_Multiplier` | also: Finisher_Support, Mana_Acceleration
- **Pawn of Ulamog** via `Mana_Production + Sacrifice_Outlet` | also: Conversion, Enabler, Engine, Fuel, Mana_Acceleration, Payoff, Threat
- **Priest of Forgotten Gods** via `Mana_Production + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine, Mana_Acceleration
- **Songs of the Damned** via `Mana_Production + Scales_With_Deaths` | also: Conversion, Engine, Mana_Acceleration, Payoff
- **Treasure** via `Mana_Production + Sacrifice_Outlet` | also: Conversion, Enabler, Engine, Mana_Acceleration
- **Vraska, Betrayal's Sting** via `Mana_Production + Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine, Finisher, Mana_Acceleration

### Mana_Acceleration (41 cards)

- **Arcane Signet** via `Mana_Production`
- **Ashnod's Altar** via `Mana_Production` | also: Conversion, Enabler, Engine, Mana_Engine
- **Black Market** via `Mana_Production` | also: Conversion, Engine, Mana_Engine, Payoff
- **Bubbling Muck** via `Mana_Multiplier` | also: Finisher_Support, Mana_Engine
- **Burnished Hart** via `Search_For_Land` | also: Card_Advantage, Enabler, Finisher_Support, Setup
- **Cabal Ritual** via `Mana_Production`
- **Charcoal Diamond** via `Mana_Production`
- **Commander's Sphere** via `Mana_Production` | also: Card_Advantage, Card_Draw
- **Crypt Ghast** via `Mana_Multiplier` | also: Finisher_Support, Mana_Engine, Payoff
- **Crypt of Agadeem** via `Mana_Production` | also: Conversion, Engine, Mana_Engine, Payoff
- **Dark Ritual** via `Mana_Production`
- **Dungeon Map** via `Mana_Production`
- **Evolving Wilds** via `Search_For_Land` | also: Card_Advantage, Enabler, Finisher_Support, Setup
- **Fabled Passage** via `Search_For_Land` | also: Card_Advantage, Enabler, Finisher_Support, Setup
- **Firdoch Core** via `Mana_Production`
- **Foraging Wickermaw** via `Mana_Production`
- **Foreboding Statue // Forsaken Thresher** via `Mana_Production` | also: Engine, Mana_Engine
- **Honored Heirloom** via `Mana_Production` | also: Interaction, Removal
- **Jet Medallion** via `Cost_Reduction` | also: Enabler
- **Liliana of the Dark Realms** via `Search_For_Land` | also: Card_Advantage, Enabler, Finisher_Support, Setup
- **Magus of the Coffers** via `Mana_Production` | also: Finisher_Support, Mana_Engine
- **Mind Stone** via `Mana_Production` | also: Card_Advantage, Card_Draw
- **Myriad Landscape** via `Search_For_Land` | also: Card_Advantage, Enabler, Finisher_Support, Setup
- **Nirkana Revenant** via `Mana_Multiplier` | also: Finisher_Support, Mana_Engine
- **Page, Loose Leaf** via `Mana_Production`
- **Park Map** via `Search_For_Land` | also: Card_Advantage, Enabler, Finisher_Support, Setup
- **Pawn of Ulamog** via `Mana_Production` | also: Conversion, Enabler, Engine, Fuel, Mana_Engine, Payoff, Threat
- **Potioner's Trove** via `Mana_Production`
- **Priest of Forgotten Gods** via `Mana_Production` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine, Mana_Engine
- **Quest for the Necropolis** via `Cost_Reduction` | also: Enabler
- **Riveteers Overlook** via `Search_For_Land` | also: Card_Advantage, Enabler, Finisher_Support, Setup
- **Sol Ring** via `Mana_Production`
- **Songs of the Damned** via `Mana_Production` | also: Conversion, Engine, Mana_Engine, Payoff
- **Staff of Compleation** via `Mana_Production` | also: Card_Advantage, Card_Draw, Conversion, Engine, Interaction, Removal
- **Terramorphic Expanse** via `Search_For_Land` | also: Card_Advantage, Enabler, Finisher_Support, Setup
- **The Darkness Crystal** via `Cost_Reduction` | also: Enabler
- **Treasure** via `Mana_Production` | also: Conversion, Enabler, Engine, Mana_Engine
- **Unstable Obelisk** via `Mana_Production` | also: Interaction, Removal
- **Vraska, Betrayal's Sting** via `Mana_Production` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine, Finisher, Mana_Engine
- **Wickersmith's Tools** via `Mana_Production`
- **Worn Powerstone** via `Mana_Production`

### Card_Draw (47 cards)

- **Annihilate** via `Draw_Effect` | also: Card_Advantage, Interaction, Removal
- **Archon of Cruelty** via `Draw_Effect` | also: Card_Advantage, Engine, Interaction, Payoff, Removal, Threat
- **Blighted Blackthorn** via `Draw_Effect` | also: Card_Advantage, Conversion, Engine, Payoff, Threat
- **Blood Divination** via `Draw_Effect` | also: Card_Advantage
- **Braids, Arisen Nightmare** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Engine, Interaction, Payoff, Removal, Threat
- **Commander's Sphere** via `Draw_Effect` | also: Card_Advantage, Mana_Acceleration
- **Deadly Dispute** via `Draw_Effect` | also: Card_Advantage, Fuel
- **Decree of Pain** via `Draw_Effect` | also: Card_Advantage, Interaction, Removal
- **Disciple of Bolas** via `Draw_Effect` | also: Card_Advantage
- **Dregs of Sorrow** via `Draw_Effect` | also: Card_Advantage
- **Dross Skullbomb** via `Draw_Effect` | also: Card_Advantage, Recursion
- **Dusk Urchins** via `Draw_Effect` | also: Card_Advantage
- **Erebos, Bleak-Hearted** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Conversion, Enabler, Engine, Payoff
- **Eventide's Shadow** via `Draw_Effect` | also: Card_Advantage
- **Eviscerator's Insight** via `Draw_Effect` | also: Card_Advantage
- **Grim Haruspex** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Conversion, Engine, Payoff
- **Hoarder's Greed** via `Draw_Effect` | also: Card_Advantage
- **Indulgent Tormentor** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Engine, Interaction, Payoff, Removal, Threat
- **Infectious Inquiry** via `Draw_Effect` | also: Card_Advantage
- **Massacre Girl, Known Killer** via `Draw_Effect` | also: Card_Advantage
- **Midnight Reaper** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Conversion, Engine, Payoff
- **Mind Stone** via `Draw_Effect` | also: Card_Advantage, Mana_Acceleration
- **Morbid Opportunist** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Conversion, Engine, Payoff
- **Night's Whisper** via `Draw_Effect` | also: Card_Advantage
- **Ob Nixilis of the Black Oath** via `Draw_Effect` | also: Card_Advantage, Conversion, Enabler, Engine, Finisher, Fuel, Threat
- **Oft-Nabbed Goat** via `Draw_Effect` | also: Card_Advantage
- **Painful Truths** via `Draw_Effect` | also: Card_Advantage
- **Phyrexian Arena** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Conversion, Engine, Payoff
- **Phyrexian Gargantua** via `Draw_Effect` | also: Card_Advantage
- **Plumb the Forbidden** via `Draw_Effect` | also: Card_Advantage, Conversion, Engine
- **Priest of Forgotten Gods** via `Draw_Effect` | also: Card_Advantage, Conversion, Enabler, Engine, Mana_Acceleration, Mana_Engine
- **Promise of Power** via `Draw_Effect` | also: Card_Advantage
- **Read the Bones** via `Draw_Effect` | also: Card_Advantage
- **Rogue's Gloves** via `Draw_Effect` | also: Card_Advantage, Payoff
- **Sinister Gnarlbark** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Engine, Payoff
- **Skeletal Scrying** via `Draw_Effect` | also: Card_Advantage
- **Skullclamp** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Conversion, Engine, Payoff
- **Smothering Abomination** via `Draw_Effect + Upkeep_Trigger` | also: Card_Advantage, Engine, Payoff
- **Staff of Compleation** via `Draw_Effect` | also: Card_Advantage, Conversion, Engine, Interaction, Mana_Acceleration, Removal
- **Strength-Testing Hammer** via `Draw_Effect` | also: Card_Advantage, Payoff
- **Syphon Mind** via `Draw_Effect` | also: Card_Advantage
- **Taborax, Hope's Demise** via `Death_Trigger + Draw_Effect` | also: Card_Advantage, Conversion, Engine, Payoff, Threat
- **The Dross Pits** via `Draw_Effect` | also: Card_Advantage
- **Vampiric Rites** via `Draw_Effect` | also: Card_Advantage, Conversion, Enabler, Engine
- **Village Rites** via `Draw_Effect` | also: Card_Advantage
- **Vraska, Betrayal's Sting** via `Draw_Effect` | also: Card_Advantage, Conversion, Enabler, Engine, Finisher, Mana_Acceleration, Mana_Engine
- **Yawgmoth, Thran Physician** via `Draw_Effect` | also: Card_Advantage, Conversion, Enabler, Engine

### Card_Advantage (64 cards)

- **Annihilate** via `Draw_Effect` | also: Card_Draw, Interaction, Removal
- **Archon of Cruelty** via `Draw_Effect` | also: Card_Draw, Engine, Interaction, Payoff, Removal, Threat
- **Blighted Blackthorn** via `Draw_Effect` | also: Card_Draw, Conversion, Engine, Payoff, Threat
- **Blood Divination** via `Draw_Effect` | also: Card_Draw
- **Blood Speaker** via `Tutor_Effect` | also: Enabler, Finisher_Support, Fuel, Recursion, Setup
- **Bogbrew Witch** via `Tutor_Effect` | also: Enabler, Finisher_Support, Setup
- **Braids, Arisen Nightmare** via `Draw_Effect + Upkeep_Trigger` | also: Card_Draw, Engine, Interaction, Payoff, Removal, Threat
- **Buried Alive** via `Tutor_Effect` | also: Enabler, Finisher_Support, Setup
- **Burnished Hart** via `Tutor_Effect` | also: Enabler, Finisher_Support, Mana_Acceleration, Setup
- **Commander's Sphere** via `Draw_Effect` | also: Card_Draw, Mana_Acceleration
- **Deadly Dispute** via `Draw_Effect` | also: Card_Draw, Fuel
- **Decree of Pain** via `Draw_Effect` | also: Card_Draw, Interaction, Removal
- **Diabolic Intent** via `Tutor_Effect` | also: Enabler, Finisher_Support, Setup
- **Diabolic Tutor** via `Tutor_Effect` | also: Enabler, Finisher_Support, Setup
- **Disciple of Bolas** via `Draw_Effect` | also: Card_Draw
- **Dregs of Sorrow** via `Draw_Effect` | also: Card_Draw
- **Dross Skullbomb** via `Draw_Effect` | also: Card_Draw, Recursion
- **Dusk Urchins** via `Draw_Effect` | also: Card_Draw
- **Erebos, Bleak-Hearted** via `Death_Trigger + Draw_Effect` | also: Card_Draw, Conversion, Enabler, Engine, Payoff
- **Eventide's Shadow** via `Draw_Effect` | also: Card_Draw
- **Eviscerator's Insight** via `Draw_Effect` | also: Card_Draw
- **Evolving Wilds** via `Tutor_Effect` | also: Enabler, Finisher_Support, Mana_Acceleration, Setup
- **Fabled Passage** via `Tutor_Effect` | also: Enabler, Finisher_Support, Mana_Acceleration, Setup
- **Grim Haruspex** via `Death_Trigger + Draw_Effect` | also: Card_Draw, Conversion, Engine, Payoff
- **Grim Servant** via `Tutor_Effect` | also: Enabler, Finisher_Support, Setup
- **Hoarder's Greed** via `Draw_Effect` | also: Card_Draw
- **Indulgent Tormentor** via `Draw_Effect + Upkeep_Trigger` | also: Card_Draw, Engine, Interaction, Payoff, Removal, Threat
- **Infectious Inquiry** via `Draw_Effect` | also: Card_Draw
- **Insatiable Avarice** via `Tutor_Effect` | also: Enabler, Finisher_Support, Setup
- **Liliana of the Dark Realms** via `Tutor_Effect` | also: Enabler, Finisher_Support, Mana_Acceleration, Setup
- **Massacre Girl, Known Killer** via `Draw_Effect` | also: Card_Draw
- **Midnight Reaper** via `Death_Trigger + Draw_Effect` | also: Card_Draw, Conversion, Engine, Payoff
- **Mind Stone** via `Draw_Effect` | also: Card_Draw, Mana_Acceleration
- **Morbid Opportunist** via `Death_Trigger + Draw_Effect` | also: Card_Draw, Conversion, Engine, Payoff
- **Myriad Landscape** via `Tutor_Effect` | also: Enabler, Finisher_Support, Mana_Acceleration, Setup
- **Night's Whisper** via `Draw_Effect` | also: Card_Draw
- **Ob Nixilis of the Black Oath** via `Draw_Effect` | also: Card_Draw, Conversion, Enabler, Engine, Finisher, Fuel, Threat
- **Oft-Nabbed Goat** via `Draw_Effect` | also: Card_Draw
- **Painful Truths** via `Draw_Effect` | also: Card_Draw
- **Park Map** via `Tutor_Effect` | also: Enabler, Finisher_Support, Mana_Acceleration, Setup
- **Phyrexian Arena** via `Draw_Effect + Upkeep_Trigger` | also: Card_Draw, Conversion, Engine, Payoff
- **Phyrexian Gargantua** via `Draw_Effect` | also: Card_Draw
- **Plumb the Forbidden** via `Draw_Effect` | also: Card_Draw, Conversion, Engine
- **Priest of Forgotten Gods** via `Draw_Effect` | also: Card_Draw, Conversion, Enabler, Engine, Mana_Acceleration, Mana_Engine
- **Profane Tutor** via `Tutor_Effect` | also: Enabler, Finisher_Support, Setup
- **Promise of Power** via `Draw_Effect` | also: Card_Draw
- **Read the Bones** via `Draw_Effect` | also: Card_Draw
- **Riveteers Overlook** via `Tutor_Effect` | also: Enabler, Finisher_Support, Mana_Acceleration, Setup
- **Rogue's Gloves** via `Draw_Effect` | also: Card_Draw, Payoff
- **Rune-Scarred Demon** via `Tutor_Effect` | also: Enabler, Finisher_Support, Setup
- **Sinister Gnarlbark** via `Draw_Effect + Upkeep_Trigger` | also: Card_Draw, Engine, Payoff
- **Skeletal Scrying** via `Draw_Effect` | also: Card_Draw
- **Skullclamp** via `Death_Trigger + Draw_Effect` | also: Card_Draw, Conversion, Engine, Payoff
- **Smothering Abomination** via `Draw_Effect + Upkeep_Trigger` | also: Card_Draw, Engine, Payoff
- **Staff of Compleation** via `Draw_Effect` | also: Card_Draw, Conversion, Engine, Interaction, Mana_Acceleration, Removal
- **Strength-Testing Hammer** via `Draw_Effect` | also: Card_Draw, Payoff
- **Syphon Mind** via `Draw_Effect` | also: Card_Draw
- **Taborax, Hope's Demise** via `Death_Trigger + Draw_Effect` | also: Card_Draw, Conversion, Engine, Payoff, Threat
- **Terramorphic Expanse** via `Tutor_Effect` | also: Enabler, Finisher_Support, Mana_Acceleration, Setup
- **The Dross Pits** via `Draw_Effect` | also: Card_Draw
- **Vampiric Rites** via `Draw_Effect` | also: Card_Draw, Conversion, Enabler, Engine
- **Village Rites** via `Draw_Effect` | also: Card_Draw
- **Vraska, Betrayal's Sting** via `Draw_Effect` | also: Card_Draw, Conversion, Enabler, Engine, Finisher, Mana_Acceleration, Mana_Engine
- **Yawgmoth, Thran Physician** via `Draw_Effect` | also: Card_Draw, Conversion, Enabler, Engine

### Enabler (69 cards)

- **Animate Dead** via `Reanimation` | also: Recursion
- **Ashnod's Altar** via `Sacrifice_Outlet` | also: Conversion, Engine, Mana_Acceleration, Mana_Engine
- **Blood Bairn** via `Sacrifice_Outlet`
- **Blood Speaker** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Fuel, Recursion, Setup
- **Bloodghast** via `Reanimation` | also: Fuel, Recursion
- **Bogbrew Witch** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Setup
- **Bolas's Citadel** via `Sacrifice_Outlet` | also: Conversion, Engine, Finisher
- **Bubbling Cauldron** via `Sacrifice_Outlet` | also: Finisher
- **Buried Alive** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Setup
- **Burnished Hart** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Mana_Acceleration, Setup
- **Carrion Feeder** via `Sacrifice_Outlet`
- **Chthonian Nightmare** via `Reanimation` | also: Recursion
- **Dawnhand Eulogist** via `Self_Mill` | also: Finisher_Support, Fuel, Payoff, Setup, Threat
- **Diabolic Intent** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Setup
- **Diabolic Tutor** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Setup
- **Doomed Necromancer** via `Reanimation` | also: Recursion
- **Dread Return** via `Reanimation` | also: Recursion
- **Drivnod, Carnage Dominus** via `Trigger_Doubler` | also: Engine
- **Erebos, Bleak-Hearted** via `Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Engine, Payoff
- **Evolving Wilds** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Mana_Acceleration, Setup
- **Fabled Passage** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Mana_Acceleration, Setup
- **Flesh Carver** via `Sacrifice_Outlet`
- **Ghoulcaller Gisa** via `Sacrifice_Outlet` | also: Conversion, Engine, Fuel, Threat
- **Gisa, Glorious Resurrector** via `Mass_Reanimate` | also: Finisher, Recursion
- **Gnawing Zombie** via `Sacrifice_Outlet` | also: Finisher
- **Gravewaker** via `Reanimation` | also: Recursion
- **Grim Servant** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Setup
- **Hell's Caretaker** via `Sacrifice_Outlet` | also: Engine, Recursion
- **High Market** via `Sacrifice_Outlet`
- **Incarnation Technique** via `Self_Mill` | also: Finisher_Support, Fuel, Recursion, Setup
- **Infernal Offering** via `Reanimation` | also: Recursion
- **Insatiable Avarice** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Setup
- **Jet Medallion** via `Cost_Reduction` | also: Mana_Acceleration
- **Liliana of the Dark Realms** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Mana_Acceleration, Setup
- **Liliana, Death Wielder** via `Reanimation` | also: Interaction, Recursion, Removal
- **Liliana, the Last Hope** via `Self_Mill` | also: Engine, Finisher_Support, Fuel, Recursion, Setup
- **Living Death** via `Mass_Reanimate` | also: Finisher, Recursion
- **Moseo, Vein's New Dean** via `Reanimation` | also: Engine, Fuel, Payoff, Recursion, Threat
- **Myriad Landscape** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Mana_Acceleration, Setup
- **Nether Traitor** via `Reanimation` | also: Fuel, Recursion
- **Ob Nixilis of the Black Oath** via `Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Engine, Finisher, Fuel, Threat
- **Park Map** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Mana_Acceleration, Setup
- **Pawn of Ulamog** via `Sacrifice_Outlet` | also: Conversion, Engine, Fuel, Mana_Acceleration, Mana_Engine, Payoff, Threat
- **Persist** via `Reanimation` | also: Recursion
- **Phyrexian Ghoul** via `Sacrifice_Outlet`
- **Priest of Forgotten Gods** via `Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Engine, Mana_Acceleration, Mana_Engine
- **Profane Command** via `Reanimation` | also: Finisher, Recursion, Threat
- **Profane Tutor** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Setup
- **Quest for the Necropolis** via `Cost_Reduction` | also: Mana_Acceleration
- **Reassembling Skeleton** via `Reanimation` | also: Fuel, Recursion
- **Rise of the Dark Realms** via `Mass_Reanimate` | also: Finisher, Recursion
- **Riveteers Overlook** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Mana_Acceleration, Setup
- **Rune-Scarred Demon** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Setup
- **Scarblade Scout** via `Self_Mill` | also: Finisher_Support, Fuel, Setup
- **Sheoldred, Whispering One** via `Reanimation` | also: Engine, Interaction, Recursion, Removal, Threat
- **Stitch Together** via `Reanimation` | also: Recursion
- **Stitcher's Supplier** via `Self_Mill` | also: Finisher_Support, Fuel, Setup
- **Terramorphic Expanse** via `Tutor_Effect` | also: Card_Advantage, Finisher_Support, Mana_Acceleration, Setup
- **The Darkness Crystal** via `Cost_Reduction` | also: Mana_Acceleration
- **Treasure** via `Sacrifice_Outlet` | also: Conversion, Engine, Mana_Acceleration, Mana_Engine
- **Vampire Warlord** via `Sacrifice_Outlet`
- **Vampiric Rites** via `Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Engine
- **Viscera Seer** via `Sacrifice_Outlet`
- **Vraska, Betrayal's Sting** via `Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Engine, Finisher, Mana_Acceleration, Mana_Engine
- **Wake the Dead** via `Reanimation` | also: Finisher, Recursion
- **Whisper, Blood Liturgist** via `Sacrifice_Outlet` | also: Engine, Recursion
- **Woe Strider** via `Sacrifice_Outlet` | also: Conversion, Engine, Fuel, Threat
- **Yahenni, Undying Partisan** via `Sacrifice_Outlet` | also: Protection
- **Yawgmoth, Thran Physician** via `Sacrifice_Outlet` | also: Card_Advantage, Card_Draw, Conversion, Engine

### Setup (22 cards)

- **Blood Speaker** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Fuel, Recursion
- **Bogbrew Witch** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support
- **Buried Alive** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support
- **Burnished Hart** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Mana_Acceleration
- **Dawnhand Eulogist** via `Self_Mill` | also: Enabler, Finisher_Support, Fuel, Payoff, Threat
- **Diabolic Intent** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support
- **Diabolic Tutor** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support
- **Evolving Wilds** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Mana_Acceleration
- **Fabled Passage** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Mana_Acceleration
- **Grim Servant** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support
- **Incarnation Technique** via `Self_Mill` | also: Enabler, Finisher_Support, Fuel, Recursion
- **Insatiable Avarice** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support
- **Liliana of the Dark Realms** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Mana_Acceleration
- **Liliana, the Last Hope** via `Self_Mill` | also: Enabler, Engine, Finisher_Support, Fuel, Recursion
- **Myriad Landscape** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Mana_Acceleration
- **Park Map** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Mana_Acceleration
- **Profane Tutor** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support
- **Riveteers Overlook** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Mana_Acceleration
- **Rune-Scarred Demon** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support
- **Scarblade Scout** via `Self_Mill` | also: Enabler, Finisher_Support, Fuel
- **Stitcher's Supplier** via `Self_Mill` | also: Enabler, Finisher_Support, Fuel
- **Terramorphic Expanse** via `Tutor_Effect` | also: Card_Advantage, Enabler, Finisher_Support, Mana_Acceleration

### Removal (49 cards)

- **Accursed Marauder** via `Forced_Sacrifice` | also: Interaction, Payoff, Threat
- **Annihilate** via `Targeted_Removal` | also: Card_Advantage, Card_Draw, Interaction
- **Archon of Cruelty** via `Forced_Sacrifice` | also: Card_Advantage, Card_Draw, Engine, Interaction, Payoff, Threat
- **Braids, Arisen Nightmare** via `Forced_Sacrifice` | also: Card_Advantage, Card_Draw, Engine, Interaction, Payoff, Threat
- **Butcher of Malakir** via `Forced_Sacrifice` | also: Engine, Interaction, Threat
- **Damnation** via `Board_Wipe` | also: Interaction
- **Dawnhand Dissident** via `Graveyard_Hate` | also: Interaction
- **Deadly Tempest** via `Board_Wipe` | also: Interaction
- **Decree of Pain** via `Board_Wipe` | also: Card_Advantage, Card_Draw, Interaction
- **Demon of Wailing Agonies** via `Forced_Sacrifice` | also: Interaction, Threat
- **Explosive Apparatus** via `Damage_Effect`
- **Feed the Swarm** via `Targeted_Removal` | also: Interaction
- **Final Act** via `Board_Wipe` | also: Interaction
- **Fleshbag Marauder** via `Forced_Sacrifice` | also: Interaction, Payoff, Threat
- **Grave Pact** via `Forced_Sacrifice` | also: Engine, Interaction, Threat
- **Havoc Demon** via `Board_Wipe` | also: Interaction
- **Hero's Downfall** via `Targeted_Removal` | also: Interaction
- **Honored Heirloom** via `Graveyard_Hate` | also: Interaction, Mana_Acceleration
- **Indulgent Tormentor** via `Forced_Sacrifice` | also: Card_Advantage, Card_Draw, Engine, Interaction, Payoff, Threat
- **Infernal Grasp** via `Targeted_Removal` | also: Interaction
- **Kalitas, Bloodchief of Ghet** via `Targeted_Removal` | also: Interaction
- **Lethal Protection** via `Targeted_Removal` | also: Interaction
- **Lich's Caress** via `Targeted_Removal` | also: Interaction
- **Liliana's Reaver** via `Discard_Effect` | also: Interaction, Threat
- **Liliana, Death Wielder** via `Targeted_Removal` | also: Enabler, Interaction, Recursion
- **Malicious Affliction** via `Targeted_Removal` | also: Interaction
- **Merchant of Venom** via `Forced_Sacrifice` | also: Interaction, Payoff, Threat
- **Merciless Executioner** via `Forced_Sacrifice` | also: Interaction, Payoff, Threat
- **Meteor Golem** via `Targeted_Removal` | also: Interaction
- **Mudbutton Cursetosser** via `Targeted_Removal` | also: Interaction
- **Murder** via `Targeted_Removal` | also: Interaction
- **Murderous Rider // Swift End** via `Targeted_Removal` | also: Interaction
- **Mutilate** via `Board_Wipe` | also: Interaction
- **Necromantic Selection** via `Board_Wipe` | also: Interaction
- **Overseer of the Damned** via `Targeted_Removal` | also: Interaction
- **Pestilence Demon** via `Damage_Effect`
- **Plaguecrafter** via `Forced_Sacrifice` | also: Interaction, Payoff, Threat
- **Ravenous Chupacabra** via `Targeted_Removal` | also: Interaction
- **Requiting Hex** via `Targeted_Removal` | also: Interaction
- **Sheoldred, Whispering One** via `Forced_Sacrifice` | also: Enabler, Engine, Interaction, Recursion, Threat
- **Skeleton Archer** via `Damage_Effect`
- **Staff of Compleation** via `Targeted_Removal` | also: Card_Advantage, Card_Draw, Conversion, Engine, Interaction, Mana_Acceleration
- **Syr Konrad, the Grim** via `Damage_Effect`
- **Tendrils of Corruption** via `Damage_Effect`
- **Toxic Deluge** via `Board_Wipe` | also: Conversion, Engine, Interaction
- **Unstable Obelisk** via `Targeted_Removal` | also: Interaction, Mana_Acceleration
- **Vile Rebirth** via `Targeted_Removal` | also: Fuel, Interaction
- **Witch of the Moors** via `Forced_Sacrifice` | also: Interaction, Threat
- **Woebringer Demon** via `Forced_Sacrifice` | also: Interaction, Threat

### Interaction (44 cards)

- **Accursed Marauder** via `Forced_Sacrifice` | also: Payoff, Removal, Threat
- **Annihilate** via `Targeted_Removal` | also: Card_Advantage, Card_Draw, Removal
- **Archon of Cruelty** via `Forced_Sacrifice` | also: Card_Advantage, Card_Draw, Engine, Payoff, Removal, Threat
- **Braids, Arisen Nightmare** via `Forced_Sacrifice` | also: Card_Advantage, Card_Draw, Engine, Payoff, Removal, Threat
- **Butcher of Malakir** via `Forced_Sacrifice` | also: Engine, Removal, Threat
- **Damnation** via `Board_Wipe` | also: Removal
- **Dawnhand Dissident** via `Graveyard_Hate` | also: Removal
- **Deadly Tempest** via `Board_Wipe` | also: Removal
- **Decree of Pain** via `Board_Wipe` | also: Card_Advantage, Card_Draw, Removal
- **Demon of Wailing Agonies** via `Forced_Sacrifice` | also: Removal, Threat
- **Feed the Swarm** via `Targeted_Removal` | also: Removal
- **Final Act** via `Board_Wipe` | also: Removal
- **Fleshbag Marauder** via `Forced_Sacrifice` | also: Payoff, Removal, Threat
- **Grave Pact** via `Forced_Sacrifice` | also: Engine, Removal, Threat
- **Havoc Demon** via `Board_Wipe` | also: Removal
- **Hero's Downfall** via `Targeted_Removal` | also: Removal
- **Honored Heirloom** via `Graveyard_Hate` | also: Mana_Acceleration, Removal
- **Indulgent Tormentor** via `Forced_Sacrifice` | also: Card_Advantage, Card_Draw, Engine, Payoff, Removal, Threat
- **Infernal Grasp** via `Targeted_Removal` | also: Removal
- **Kalitas, Bloodchief of Ghet** via `Targeted_Removal` | also: Removal
- **Lethal Protection** via `Targeted_Removal` | also: Removal
- **Lich's Caress** via `Targeted_Removal` | also: Removal
- **Liliana's Reaver** via `Discard_Effect` | also: Removal, Threat
- **Liliana, Death Wielder** via `Targeted_Removal` | also: Enabler, Recursion, Removal
- **Malicious Affliction** via `Targeted_Removal` | also: Removal
- **Merchant of Venom** via `Forced_Sacrifice` | also: Payoff, Removal, Threat
- **Merciless Executioner** via `Forced_Sacrifice` | also: Payoff, Removal, Threat
- **Meteor Golem** via `Targeted_Removal` | also: Removal
- **Mudbutton Cursetosser** via `Targeted_Removal` | also: Removal
- **Murder** via `Targeted_Removal` | also: Removal
- **Murderous Rider // Swift End** via `Targeted_Removal` | also: Removal
- **Mutilate** via `Board_Wipe` | also: Removal
- **Necromantic Selection** via `Board_Wipe` | also: Removal
- **Overseer of the Damned** via `Targeted_Removal` | also: Removal
- **Plaguecrafter** via `Forced_Sacrifice` | also: Payoff, Removal, Threat
- **Ravenous Chupacabra** via `Targeted_Removal` | also: Removal
- **Requiting Hex** via `Targeted_Removal` | also: Removal
- **Sheoldred, Whispering One** via `Forced_Sacrifice` | also: Enabler, Engine, Recursion, Removal, Threat
- **Staff of Compleation** via `Targeted_Removal` | also: Card_Advantage, Card_Draw, Conversion, Engine, Mana_Acceleration, Removal
- **Toxic Deluge** via `Board_Wipe` | also: Conversion, Engine, Removal
- **Unstable Obelisk** via `Targeted_Removal` | also: Mana_Acceleration, Removal
- **Vile Rebirth** via `Targeted_Removal` | also: Fuel, Removal
- **Witch of the Moors** via `Forced_Sacrifice` | also: Removal, Threat
- **Woebringer Demon** via `Forced_Sacrifice` | also: Removal, Threat

### Threat (41 cards)

- **Accursed Marauder** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Payoff, Removal
- **Archon of Cruelty** via `ETB_Trigger + Forced_Sacrifice` | also: Card_Advantage, Card_Draw, Engine, Interaction, Payoff, Removal
- **Blighted Blackthorn** via `ETB_Trigger + Life_Drain` | also: Card_Advantage, Card_Draw, Conversion, Engine, Payoff
- **Blood Artist** via `Death_Trigger + Life_Drain` | also: Payoff
- **Bloodgift Demon** via `Evasion + Life_Drain` | also: Payoff
- **Braids, Arisen Nightmare** via `Forced_Sacrifice + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Engine, Interaction, Payoff, Removal
- **Butcher of Malakir** via `Death_Trigger + Forced_Sacrifice` | also: Engine, Interaction, Removal
- **Dawnhand Eulogist** via `Evasion + Life_Drain` | also: Enabler, Finisher_Support, Fuel, Payoff, Setup
- **Defiling Daemogoth** via `Combat_Trigger + Evasion` | also: Finisher, Payoff
- **Demon of Wailing Agonies** via `Combat_Trigger + Evasion` | also: Interaction, Removal
- **Drana, the Last Bloodchief** via `Combat_Trigger + Evasion`
- **Falkenrath Noble** via `Evasion + Life_Drain` | also: Payoff
- **Fleshbag Marauder** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Payoff, Removal
- **Ghoulcaller Gisa** via `Sacrifice_Outlet + Token_Generation` | also: Conversion, Enabler, Engine, Fuel
- **Grave Pact** via `Death_Trigger + Forced_Sacrifice` | also: Engine, Interaction, Removal
- **Grave Titan** via `Combat_Trigger + Deathtouch` | also: Fuel, Payoff
- **Grave Venerations** via `Death_Trigger + Life_Drain` | also: Payoff
- **Gray Merchant of Asphodel** via `ETB_Trigger + Life_Drain` | also: Finisher, Payoff
- **Indulgent Tormentor** via `Forced_Sacrifice + Upkeep_Trigger` | also: Card_Advantage, Card_Draw, Engine, Interaction, Payoff, Removal
- **Liliana's Reaver** via `Combat_Trigger + Deathtouch` | also: Interaction, Removal
- **Merchant of Venom** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Payoff, Removal
- **Merciless Executioner** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Payoff, Removal
- **Mirkwood Bats** via `Evasion + Life_Drain`
- **Moseo, Vein's New Dean** via `Combat_Trigger + Evasion` | also: Enabler, Engine, Fuel, Payoff, Recursion
- **Necropolis Regent** via `Combat_Trigger + Evasion`
- **Ob Nixilis of the Black Oath** via `Evasion + Life_Drain` | also: Card_Advantage, Card_Draw, Conversion, Enabler, Engine, Finisher, Fuel
- **Pawn of Ulamog** via `Sacrifice_Outlet + Token_Generation` | also: Conversion, Enabler, Engine, Fuel, Mana_Acceleration, Mana_Engine, Payoff
- **Plaguecrafter** via `ETB_Trigger + Forced_Sacrifice` | also: Interaction, Payoff, Removal
- **Profane Command** via `Evasion + Life_Drain` | also: Enabler, Finisher, Recursion
- **Raving Dead** via `Combat_Trigger + Deathtouch`
- **Sheoldred, Whispering One** via `Forced_Sacrifice + Upkeep_Trigger` | also: Enabler, Engine, Interaction, Recursion, Removal
- **Skymarch Bloodletter** via `Evasion + Life_Drain` | also: Payoff
- **Sneering Shadewriter** via `Evasion + Life_Drain` | also: Payoff
- **Stensian Sanguinist // Exsanguinate** via `Combat_Trigger + Deathtouch` | also: Finisher, Payoff
- **Taborax, Hope's Demise** via `Evasion + Lifelink` | also: Card_Advantage, Card_Draw, Conversion, Engine, Payoff
- **Vampire Sovereign** via `Evasion + Life_Drain` | also: Payoff
- **Vraan, Executioner Thane** via `Death_Trigger + Life_Drain` | also: Payoff
- **Witch of the Moors** via `Forced_Sacrifice + Upkeep_Trigger` | also: Interaction, Removal
- **Woe Strider** via `Sacrifice_Outlet + Token_Generation` | also: Conversion, Enabler, Engine, Fuel
- **Woebringer Demon** via `Forced_Sacrifice + Upkeep_Trigger` | also: Interaction, Removal
- **Zulaport Cutthroat** via `Death_Trigger + Life_Drain` | also: Payoff

### Protection (5 cards)

- **Arcane Lighthouse** via `Protection_Effect`
- **Masterful Flourish** via `Protection_Effect`
- **Popular Egotist** via `Protection_Effect`
- **Swiftfoot Boots** via `Protection_Effect`
- **Yahenni, Undying Partisan** via `Protection_Effect` | also: Enabler

## No Functional Role (122 cards)

These have no mechanical tags, or only tags not yet covered by functional rules.

- Aberrant Return [*(no mechanical tags)*]
- Abyssal Persecutor [Evasion]
- Accorder's Shield [*(no mechanical tags)*]
- Aether Snap [*(no mechanical tags)*]
- Archfiend of Ifnir [Evasion]
- Archfiend of the Dross [Evasion, Upkeep_Trigger]
- Arisen Gorgon [Deathtouch]
- Ashes to Ashes [*(no mechanical tags)*]
- Bad Moon [*(no mechanical tags)*]
- Barbed Bloodletter [ETB_Trigger]
- Barren Moor [*(no mechanical tags)*]
- Bile-Vial Boggart [Self_Death_Trigger]
- Black Sun's Zenith [*(no mechanical tags)*]
- Blight Rot [*(no mechanical tags)*]
- Blightbelly Rat [Self_Death_Trigger]
- Blowfly Infestation [Death_Trigger]
- Boggart Prankster [Combat_Trigger]
- Bojuka Bog [ETB_Trigger]
- Burrog Banemaker [Deathtouch]
- Carnifex Demon [Evasion]
- Child of Night [Lifelink]
- Chimil, the Inner Sun [Upkeep_Trigger]
- Command Tower [*(no mechanical tags)*]
- Contagion Clasp [ETB_Trigger]
- Corrupt [Life_Gain, Permanent_Scaling]
- Cost of Brilliance [Life_Drain]
- Costume Shop [*(no mechanical tags)*]
- Crumbling Colossus [*(no mechanical tags)*]
- Curse of Shallow Graves [*(no mechanical tags)*]
- Dance of the Dead [ETB_Trigger]
- ... and 92 more
