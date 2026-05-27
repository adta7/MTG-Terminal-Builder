#!/usr/bin/env python3
"""
scripts/tag_deck.py — Stage 2: Tag all cards from the Sheoldred deck.

Tags each card across:
  Layer 2 — Mechanical  (auto-tagged from oracle text via regex)
  Layer 3 — Functional  (manually assigned — what role it plays)
  Layer 4 — Archetype   (manually assigned — what strategies want it)
  Layer 5 — Emotional   (manually assigned — strategic identity)

Also seeds synergy edges between key card pairs.

Run from project root:
    python scripts/tag_deck.py

Safe to re-run — uses INSERT OR REPLACE throughout.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mtgdeck.database import Database
from mtgdeck import tags as tag_module

DB_PATH = Path(__file__).parent.parent / "data" / "cards.sqlite"

# ─── Layer 3: Functional Tags ─────────────────────────────────────────────────
# What role does each card perform in this deck?
# A card can have multiple functional tags.

FUNCTIONAL: dict[str, list[str]] = {
    "Abnormal Endurance":               ["Protection", "Enabler"],
    "Accursed Marauder":                ["Removal", "Interaction"],
    "Animate Dead":                     ["Recursion"],
    "Arcane Signet":                    ["Mana_Acceleration"],
    "Archon of Cruelty":                ["Threat", "Payoff"],
    "Ashnod's Altar":                   ["Mana_Engine", "Engine", "Conversion"],
    "Black Market":                     ["Mana_Engine", "Conversion"],
    "Blood Artist":                     ["Payoff"],
    "Bloodghast":                       ["Fuel", "Enabler"],
    "Bojuka Bog":                       ["Interaction"],
    "Braids, Arisen Nightmare":         ["Engine", "Payoff"],
    "Buried Alive":                     ["Setup", "Enabler"],
    "Carrion Feeder":                   ["Enabler"],
    "Chthonian Nightmare":              ["Recursion", "Engine"],
    "Crypt Ghast":                      ["Mana_Engine", "Mana_Acceleration"],
    "Crypt of Agadeem":                 ["Mana_Acceleration"],
    "Damnation":                        ["Removal"],
    "Dance of the Dead":                ["Recursion"],
    "Dark Ritual":                      ["Mana_Acceleration"],
    "Deadly Dispute":                   ["Card_Advantage", "Enabler"],
    "Disciple of Bolas":                ["Card_Advantage", "Conversion"],
    "Doomed Necromancer":               ["Recursion"],
    "Dread Return":                     ["Recursion"],
    "Drivnod, Carnage Dominus":         ["Engine"],
    "Emergence Zone":                   ["Enabler", "Setup"],
    "Erebos, Bleak-Hearted":            ["Card_Advantage", "Removal"],
    "Fabled Passage":                   ["Setup"],
    "Feed the Swarm":                   ["Removal"],
    "Ghoulcaller Gisa":                 ["Engine", "Threat", "Conversion"],
    "Ghoulish Procession":              ["Fuel"],
    "Grave Pact":                       ["Engine", "Interaction"],
    "Grave Titan":                      ["Threat", "Fuel"],
    "Gray Merchant of Asphodel":        ["Finisher", "Payoff"],
    "High Market":                      ["Enabler"],
    "Insatiable Avarice":               ["Setup", "Card_Advantage"],
    "Jadar, Ghoulcaller of Nephalia":   ["Fuel"],
    "Jet Medallion":                    ["Mana_Acceleration"],
    "K'rrik, Son of Yawgmoth":         ["Mana_Acceleration", "Engine"],
    "Lashwrithe":                       ["Threat"],
    "Living Death":                     ["Recursion", "Finisher"],
    "Malakir Rebirth // Malakir Mire":  ["Protection", "Recursion"],
    "Malicious Affliction":             ["Removal"],
    "Morbid Opportunist":               ["Card_Advantage"],
    "Mortuary Mire":                    ["Recursion"],
    "Myriad Landscape":                 ["Mana_Acceleration"],
    "Nether Traitor":                   ["Fuel"],
    "Night's Whisper":                  ["Card_Advantage"],
    "Ophiomancer":                      ["Fuel"],
    "Overseer of the Damned":           ["Threat", "Removal"],
    "Oversold Cemetery":                ["Recursion"],
    "Pawn of Ulamog":                   ["Conversion", "Fuel"],
    "Phyrexian Arena":                  ["Card_Advantage"],
    "Phyrexian Reclamation":            ["Recursion"],
    "Pitiless Plunderer":               ["Conversion", "Fuel"],
    "Plaguecrafter":                    ["Interaction", "Removal"],
    "Priest of Forgotten Gods":         ["Engine", "Conversion"],
    "Read the Bones":                   ["Card_Advantage"],
    "Reassembling Skeleton":            ["Fuel"],
    "Sheoldred, Whispering One":        ["Engine", "Threat", "Recursion"],
    "Skullclamp":                       ["Card_Advantage", "Conversion"],
    "Sol Ring":                         ["Mana_Acceleration"],
    "Stensian Sanguinist // Exsanguinate": ["Finisher"],
    "Stitcher's Supplier":              ["Enabler", "Setup"],
    "Sudden Spoiling":                  ["Interaction", "Protection"],
    "Swiftfoot Boots":                  ["Protection"],
    "Syr Konrad, the Grim":             ["Payoff", "Threat"],
    "Toxic Deluge":                     ["Removal"],
    "Victimize":                        ["Recursion"],
    "Viscera Seer":                     ["Enabler"],
    "Wake the Dead":                    ["Recursion"],
    "Woe Strider":                      ["Enabler", "Fuel"],
    "Yahenni, Undying Partisan":        ["Enabler", "Protection"],
    "Yawgmoth, Thran Physician":        ["Engine", "Card_Advantage", "Removal"],
    "Zulaport Cutthroat":               ["Payoff"],
}


# ─── Layer 4: Archetype Tags ──────────────────────────────────────────────────
# What strategies specifically want this card?

ARCHETYPE: dict[str, list[str]] = {
    "Abnormal Endurance":               ["Aristocrats", "Sacrifice"],
    "Accursed Marauder":                ["Aristocrats", "Sacrifice"],
    "Animate Dead":                     ["Reanimator", "Graveyard", "Aristocrats"],
    "Arcane Signet":                    ["Aristocrats", "Reanimator"],
    "Archon of Cruelty":                ["Reanimator"],
    "Ashnod's Altar":                   ["Aristocrats", "Sacrifice", "Reanimator"],
    "Black Market":                     ["Aristocrats", "Big_Mana"],
    "Blood Artist":                     ["Aristocrats", "Sacrifice"],
    "Bloodghast":                       ["Aristocrats", "Graveyard", "Sacrifice"],
    "Bojuka Bog":                       ["Graveyard", "Control"],
    "Braids, Arisen Nightmare":         ["Sacrifice", "Control"],
    "Buried Alive":                     ["Reanimator", "Graveyard"],
    "Carrion Feeder":                   ["Aristocrats", "Sacrifice"],
    "Chthonian Nightmare":              ["Reanimator", "Graveyard", "Aristocrats"],
    "Crypt Ghast":                      ["Big_Mana", "Devotion"],
    "Crypt of Agadeem":                 ["Big_Mana", "Graveyard", "Devotion"],
    "Damnation":                        ["Control", "Aristocrats"],
    "Dance of the Dead":                ["Reanimator", "Graveyard", "Aristocrats"],
    "Dark Ritual":                      ["Big_Mana", "Reanimator"],
    "Deadly Dispute":                   ["Aristocrats", "Sacrifice"],
    "Disciple of Bolas":                ["Aristocrats", "Sacrifice"],
    "Doomed Necromancer":               ["Reanimator", "Graveyard"],
    "Dread Return":                     ["Reanimator", "Graveyard", "Aristocrats"],
    "Drivnod, Carnage Dominus":         ["Aristocrats", "Sacrifice", "Graveyard"],
    "Erebos, Bleak-Hearted":            ["Aristocrats", "Graveyard", "Control"],
    "Feed the Swarm":                   ["Control", "Aristocrats"],
    "Ghoulcaller Gisa":                 ["Tokens", "Aristocrats", "Sacrifice"],
    "Ghoulish Procession":              ["Aristocrats", "Tokens", "Sacrifice"],
    "Grave Pact":                       ["Aristocrats", "Sacrifice", "Control"],
    "Grave Titan":                      ["Tokens", "Aristocrats", "Reanimator"],
    "Gray Merchant of Asphodel":        ["Devotion", "Big_Mana", "Lifegain"],
    "High Market":                      ["Aristocrats", "Sacrifice"],
    "Insatiable Avarice":               ["Reanimator"],
    "Jadar, Ghoulcaller of Nephalia":   ["Aristocrats", "Tokens", "Sacrifice"],
    "Jet Medallion":                    ["Big_Mana"],
    "K'rrik, Son of Yawgmoth":         ["Big_Mana"],
    "Lashwrithe":                       ["Voltron"],
    "Living Death":                     ["Reanimator", "Graveyard"],
    "Malakir Rebirth // Malakir Mire":  ["Reanimator", "Aristocrats"],
    "Malicious Affliction":             ["Control"],
    "Morbid Opportunist":               ["Aristocrats", "Sacrifice"],
    "Nether Traitor":                   ["Aristocrats", "Graveyard", "Sacrifice"],
    "Night's Whisper":                  ["Control"],
    "Ophiomancer":                      ["Aristocrats", "Tokens", "Sacrifice"],
    "Overseer of the Damned":           ["Reanimator", "Tokens"],
    "Oversold Cemetery":                ["Graveyard", "Aristocrats"],
    "Pawn of Ulamog":                   ["Aristocrats", "Sacrifice"],
    "Phyrexian Arena":                  ["Control"],
    "Phyrexian Reclamation":            ["Graveyard", "Aristocrats", "Reanimator"],
    "Pitiless Plunderer":               ["Aristocrats", "Sacrifice"],
    "Plaguecrafter":                    ["Aristocrats", "Sacrifice", "Control"],
    "Priest of Forgotten Gods":         ["Aristocrats", "Sacrifice"],
    "Read the Bones":                   ["Control"],
    "Reassembling Skeleton":            ["Aristocrats", "Sacrifice", "Graveyard"],
    "Sheoldred, Whispering One":        ["Reanimator", "Control"],
    "Skullclamp":                       ["Aristocrats", "Sacrifice", "Tokens"],
    "Sol Ring":                         ["Aristocrats", "Reanimator"],
    "Stensian Sanguinist // Exsanguinate": ["Big_Mana", "Lifegain"],
    "Stitcher's Supplier":              ["Graveyard", "Reanimator"],
    "Sudden Spoiling":                  ["Control"],
    "Swiftfoot Boots":                  ["Reanimator", "Voltron"],
    "Syr Konrad, the Grim":             ["Aristocrats", "Graveyard"],
    "Toxic Deluge":                     ["Control", "Aristocrats"],
    "Victimize":                        ["Reanimator", "Graveyard", "Aristocrats"],
    "Viscera Seer":                     ["Aristocrats", "Sacrifice"],
    "Wake the Dead":                    ["Reanimator", "Graveyard", "Aristocrats"],
    "Woe Strider":                      ["Aristocrats", "Sacrifice", "Graveyard"],
    "Yahenni, Undying Partisan":        ["Aristocrats", "Sacrifice"],
    "Yawgmoth, Thran Physician":        ["Aristocrats", "Graveyard", "Control"],
    "Zulaport Cutthroat":               ["Aristocrats", "Sacrifice"],
}


# ─── Layer 5: Emotional / Play-Pattern Tags ───────────────────────────────────
# What is this card's strategic identity in THIS deck?
# These are subjective and specific to Sheoldred aristocrats/reanimator.

EMOTIONAL: dict[str, list[str]] = {
    # The core machines — deck is built around enabling these
    "Ashnod's Altar":               ["Engine_Core", "Conversion_Piece"],
    "Yawgmoth, Thran Physician":    ["Engine_Core", "Apex_Threat", "Identity_Card", "Table_Threat"],
    "Sheoldred, Whispering One":    ["Engine_Core", "Apex_Threat", "Identity_Card", "Table_Threat"],
    "Crypt Ghast":                  ["Engine_Core", "Conversion_Piece", "Identity_Card"],
    "Grave Pact":                   ["Engine_Core", "Pressure_Piece"],
    "Skullclamp":                   ["Engine_Core", "Conversion_Piece"],
    "Priest of Forgotten Gods":     ["Engine_Core", "Conversion_Piece"],
    "Black Market":                 ["Engine_Core", "Conversion_Piece", "Momentum_Spike"],

    # Renewable fuel — bodies that keep coming back
    "Reassembling Skeleton":        ["Renewable_Fuel", "Resilience_Piece"],
    "Bloodghast":                   ["Renewable_Fuel", "Resilience_Piece"],
    "Ophiomancer":                  ["Renewable_Fuel"],
    "Jadar, Ghoulcaller of Nephalia": ["Renewable_Fuel"],
    "Nether Traitor":               ["Renewable_Fuel", "Resilience_Piece"],
    "Woe Strider":                  ["Renewable_Fuel"],
    "Ghoulish Procession":          ["Renewable_Fuel"],

    # Apex threats — must be answered or the game usually ends
    "Archon of Cruelty":            ["Apex_Threat", "Table_Threat"],
    "Grave Titan":                  ["Apex_Threat", "Table_Threat"],
    "K'rrik, Son of Yawgmoth":     ["Apex_Threat", "Table_Threat", "Momentum_Spike"],
    "Drivnod, Carnage Dominus":     ["Apex_Threat", "Pressure_Piece"],

    # Pressure pieces — apply constant pressure every turn
    "Blood Artist":                 ["Pressure_Piece"],
    "Zulaport Cutthroat":           ["Pressure_Piece"],
    "Syr Konrad, the Grim":         ["Pressure_Piece"],
    "Braids, Arisen Nightmare":     ["Pressure_Piece"],

    # Conversion pieces — turn one resource into another
    "Pitiless Plunderer":           ["Conversion_Piece"],
    "Pawn of Ulamog":               ["Conversion_Piece"],
    "Ghoulcaller Gisa":             ["Conversion_Piece", "Identity_Card"],
    "Disciple of Bolas":            ["Conversion_Piece"],

    # Grand finishers — ends the game outright when they resolve
    "Stensian Sanguinist // Exsanguinate": ["Grand_Finisher"],
    "Gray Merchant of Asphodel":    ["Grand_Finisher"],
    "Living Death":                 ["Grand_Finisher", "Comeback_Card"],
    "Dread Return":                 ["Momentum_Spike"],

    # Comeback cards — help stabilize from behind
    "Wake the Dead":                ["Comeback_Card", "Momentum_Spike"],
    "Damnation":                    ["Comeback_Card"],
    "Toxic Deluge":                 ["Comeback_Card"],

    # Resilience pieces — hard to permanently remove
    "Yahenni, Undying Partisan":    ["Resilience_Piece"],
    "Erebos, Bleak-Hearted":        ["Resilience_Piece"],

    # Identity cards — strongly represent the deck's character
    "Ghoulcaller Gisa":             ["Identity_Card"],
}


# ─── Synergy Edges ────────────────────────────────────────────────────────────
# Key card combinations. Format: (card_a, card_b, type, strength, explanation)
# strength 0.0–1.0: 1.0=combo, 0.9=core, 0.7=strong, 0.5=moderate, 0.3=incidental

SYNERGIES: list[tuple[str, str, str, float, str]] = [

    # ── Core Combos ────────────────────────────────────────────────────────────
    ("Ashnod's Altar", "Reassembling Skeleton",
     "Sacrifice_Loop", 1.0,
     "Sac skeleton for {C}{C}, return for {1}{B}. Net +{C} each loop. Infinite colorless mana."),

    ("Yawgmoth, Thran Physician", "Reassembling Skeleton",
     "Draw_Engine", 0.95,
     "Pay 1 life + sac skeleton to draw a card and put -1/-1 counter elsewhere. Return skeleton for {1}{B}. Near-infinite draw."),

    ("Yawgmoth, Thran Physician", "Nether Traitor",
     "Infinite_Draw", 0.95,
     "Two creatures: sac one to Yawgmoth (draw + counter), Traitor returns when another creature dies. Loops with a third body."),

    # ── Mana → Finisher ────────────────────────────────────────────────────────
    ("Crypt Ghast", "Stensian Sanguinist // Exsanguinate",
     "Big_Mana_Finisher", 0.95,
     "Crypt Ghast doubles all Swamp mana. Dump into Exsanguinate to drain all opponents for lethal."),

    ("Black Market", "Stensian Sanguinist // Exsanguinate",
     "Big_Mana_Finisher", 0.85,
     "Black Market accumulates {B} charge counters each time a creature dies. Convert into Exsanguinate for lethal."),

    ("K'rrik, Son of Yawgmoth", "Stensian Sanguinist // Exsanguinate",
     "Life_To_Mana_Finisher", 0.8,
     "K'rrik lets you pay life instead of {B}. Spend life to cast Exsanguinate, then drain opponents for the life back and more."),

    # ── Death Trigger Chains ───────────────────────────────────────────────────
    ("Ashnod's Altar", "Blood Artist",
     "Death_Drain_Chain", 0.9,
     "Every creature you sacrifice triggers Blood Artist — opponent loses 1, you gain 1."),

    ("Ashnod's Altar", "Zulaport Cutthroat",
     "Death_Drain_Chain", 0.9,
     "Every sacrifice triggers Zulaport — each opponent loses 1, you gain 1."),

    ("Grave Pact", "Ashnod's Altar",
     "Forced_Sacrifice_Control", 0.9,
     "Sacrifice your creatures freely; Grave Pact forces each opponent to sacrifice their best creature too."),

    ("Drivnod, Carnage Dominus", "Blood Artist",
     "Double_Death_Trigger", 0.9,
     "Drivnod doubles triggered abilities from creature deaths. Blood Artist fires twice per creature that dies."),

    ("Drivnod, Carnage Dominus", "Zulaport Cutthroat",
     "Double_Death_Trigger", 0.9,
     "Drivnod doubles triggered abilities. Zulaport fires twice per death — massive drain."),

    ("Drivnod, Carnage Dominus", "Syr Konrad, the Grim",
     "Double_Death_Trigger", 0.85,
     "Drivnod doubles Syr Konrad's death trigger. Each creature death deals 2 damage to each opponent."),

    # ── Graveyard Setup → Reanimate ────────────────────────────────────────────
    ("Buried Alive", "Sheoldred, Whispering One",
     "Setup_Reanimate", 0.95,
     "Buried Alive puts 3 creatures into graveyard. Sheoldred reanimates one each upkeep for free."),

    ("Buried Alive", "Animate Dead",
     "Setup_Instant_Reanimate", 0.9,
     "Bury a huge creature, immediately reanimate it with Animate Dead on the same turn."),

    ("Buried Alive", "Living Death",
     "Setup_Mass_Reanimate", 0.9,
     "Fill graveyard with Buried Alive, then Living Death puts the whole board back at once."),

    ("Stitcher's Supplier", "Sheoldred, Whispering One",
     "Mill_Reanimate", 0.8,
     "Supplier mills 3 on ETB and again on death. Sheoldred turns that into free reanimates each upkeep."),

    # ── Token Generation → Value ───────────────────────────────────────────────
    ("Ghoulcaller Gisa", "Skullclamp",
     "Token_Draw_Engine", 0.9,
     "Gisa creates 2/2 zombie tokens. Equip Skullclamp to a 2/2 (now 1/2), let it die, draw 2. Repeatable draw engine."),

    ("Ophiomancer", "Ashnod's Altar",
     "Renewable_Token_Mana", 0.85,
     "Ophiomancer creates a 1/1 deathtouch snake each upkeep. Sacrifice to Altar for {C}{C}. Renewable colorless mana."),

    ("Jadar, Ghoulcaller of Nephalia", "Skullclamp",
     "Decayed_Token_Draw", 0.8,
     "Jadar creates a zombie with decayed each turn. Clamp it before it attacks — draw 2 for free."),

    ("Jadar, Ghoulcaller of Nephalia", "Ashnod's Altar",
     "Decayed_Token_Mana", 0.75,
     "Sacrifice the decayed zombie to Altar for {C}{C} rather than losing it to the attack trigger."),

    # ── Pawn / Plunderer Chains ────────────────────────────────────────────────
    ("Pawn of Ulamog", "Ashnod's Altar",
     "Spawn_Mana_Chain", 0.8,
     "Creature dies → Pawn creates Eldrazi Spawn → sacrifice Spawn to Altar for another {C}. Converts deaths to mana."),

    ("Pitiless Plunderer", "Ashnod's Altar",
     "Treasure_Mana_Chain", 0.8,
     "Creature dies → Plunderer creates Treasure → tap Treasure for {C} (or sac to Altar). Extra mana from every death."),

    # ── Priest of Forgotten Gods Engine ───────────────────────────────────────
    ("Priest of Forgotten Gods", "Reassembling Skeleton",
     "Recurring_Sac_Engine", 0.85,
     "Tap Priest + sac 2 creatures (including skeleton): opponents lose 2, you add {B}{B} and draw. Skeleton returns. Repeatable."),

    ("Priest of Forgotten Gods", "Bloodghast",
     "Recurring_Sac_Engine", 0.75,
     "Bloodghast recurs via land drops. Use it as fuel for Priest's engine repeatedly."),

    # ── Sheoldred Commander Synergies ──────────────────────────────────────────
    ("Sheoldred, Whispering One", "Viscera Seer",
     "Reanimate_Scry_Loop", 0.8,
     "Sheoldred reanimates a creature each upkeep. Viscera Seer lets you scry 1 by sacrificing it before each reanimate decision."),

    ("Sheoldred, Whispering One", "Grave Pact",
     "Forced_Opponent_Sacrifice", 0.85,
     "Sheoldred forces opponents to sacrifice each upkeep. Grave Pact doubles this when you sacrifice your own creatures too."),
]


# ─── Runner ───────────────────────────────────────────────────────────────────

def main():
    db = Database(DB_PATH)
    db.init_db()

    # Seed tags
    print("Seeding tag registry...")
    tag_module.seed_tags(db)
    print(f"  {len(db.all_tags())} tags in registry\n")

    # Deck cards (non-land, non-basic)
    deck_cards = list(FUNCTIONAL.keys())

    # ── Step 1: Auto-tag mechanical layer from oracle text ─────────────────────
    print("Auto-tagging mechanical layer from oracle text...")
    mech_total = 0
    not_found = []
    for card_name in deck_cards:
        card = db.card_by_name(card_name)
        if card:
            applied = tag_module.tag_mechanical(card, db)
            if applied:
                mech_total += len(applied)
        else:
            not_found.append(card_name)

    print(f"  {mech_total} mechanical tags applied")
    if not_found:
        print(f"  NOT FOUND in DB: {not_found}")
    print()

    # ── Step 2: Apply functional tags ─────────────────────────────────────────
    print("Applying functional tags (Layer 3)...")
    func_total = 0
    for card_name, tags_list in FUNCTIONAL.items():
        for tag_name in tags_list:
            ok = db.tag_card(card_name, tag_name, confidence=1.0, source="manual")
            if ok:
                func_total += 1
            else:
                print(f"  WARNING: tag '{tag_name}' not found in registry (card: {card_name})")
    print(f"  {func_total} functional tags applied\n")

    # ── Step 3: Apply archetype tags ──────────────────────────────────────────
    print("Applying archetype tags (Layer 4)...")
    arch_total = 0
    for card_name, tags_list in ARCHETYPE.items():
        for tag_name in tags_list:
            ok = db.tag_card(card_name, tag_name, confidence=1.0, source="manual")
            if ok:
                arch_total += 1
            else:
                print(f"  WARNING: tag '{tag_name}' not found in registry (card: {card_name})")
    print(f"  {arch_total} archetype tags applied\n")

    # ── Step 4: Apply emotional tags ──────────────────────────────────────────
    print("Applying emotional tags (Layer 5)...")
    emot_total = 0
    for card_name, tags_list in EMOTIONAL.items():
        for tag_name in tags_list:
            ok = db.tag_card(card_name, tag_name, confidence=1.0, source="manual")
            if ok:
                emot_total += 1
            else:
                print(f"  WARNING: tag '{tag_name}' not found in registry (card: {card_name})")
    print(f"  {emot_total} emotional tags applied\n")

    # ── Step 5: Add synergy edges ─────────────────────────────────────────────
    print("Adding synergy edges...")
    for card_a, card_b, syn_type, strength, explanation in SYNERGIES:
        tag_module.add_synergy(card_a, card_b, syn_type, db, strength, explanation)
    print(f"  {len(SYNERGIES)} synergy edges added\n")

    # ── Step 6: Print deck diagnostic ────────────────────────────────────────
    print("=" * 60)
    print("DECK DIAGNOSTIC — Sheoldred, Whispering One")
    print("=" * 60)

    # Functional role counts
    print("\n── Functional Roles ──────────────────────────────────────")
    func_counts = tag_module.tag_count_for_deck(deck_cards, db, layer="functional")
    for tag, count in sorted(func_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"  {tag:<22} {count:2d}  {bar}")

    # Emotional identity counts
    print("\n── Emotional Identity ────────────────────────────────────")
    emot_counts = tag_module.tag_count_for_deck(deck_cards, db, layer="emotional")
    for tag, count in sorted(emot_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"  {tag:<22} {count:2d}  {bar}")

    # Archetype affinity counts
    print("\n── Archetype Affinity ────────────────────────────────────")
    arch_counts = tag_module.tag_count_for_deck(deck_cards, db, layer="archetype")
    for tag, count in sorted(arch_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"  {tag:<22} {count:2d}  {bar}")

    print()
    db.close()


if __name__ == "__main__":
    main()
