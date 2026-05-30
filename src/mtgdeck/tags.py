"""
tags.py — Phase 2: Five-layer card tagging system.

Tags describe what a card does at five levels of abstraction:

  Layer 1 — Oracle Facts     (automatic from Scryfall — mana cost, type, text)
  Layer 2 — Mechanical       (what the card literally does)
  Layer 3 — Functional       (what role it performs in a deck)
  Layer 4 — Archetype        (what strategies want it)
  Layer 5 — Emotional        (strategic identity — engine, apex threat, fuel, etc.)

Confidence scale (0.0–1.0):
  1.0 = mechanically certain  (oracle text is explicit)
  0.7 = confident             (well-known role, clear pattern)
  0.4 = contextual            (depends on the deck)
  0.1 = speculative

This module:
  - Defines the built-in tag registry (TAGS dict)
  - Seeds the tags table in the database
  - Provides Python wrappers around database tag queries
  - Auto-tags cards from oracle text (mechanical layer only)
"""

import re
from typing import Optional

from .models import Card
from .oracle_preprocessor import preprocess_oracle, search_text as _preprocess_search


# ─── Built-in Tag Registry ─────────────────────────────────────────────────────
#
# Format: (tag_name, layer, description)
# These are the seed tags. Users can add more via db.save_tag() directly.

TAGS: list[tuple[str, str, str]] = [

    # ── Layer 2: Mechanical ──────────────────────────────────────────────────
    # What the card literally does. Derived from oracle text.

    ("Draw_Effect",       "mechanical", "Card draws one or more cards."),
    ("Life_Drain",        "mechanical", "Causes opponents to lose life, typically paired with life gain."),
    ("Life_Gain",         "mechanical", "Causes the controller to gain life."),
    ("Sacrifice_Outlet",  "mechanical", "Allows sacrificing creatures or permanents as a cost or activated ability."),
    ("Forced_Sacrifice",  "mechanical", "Forces opponents (or all players) to sacrifice permanents."),
    ("Token_Generation",          "mechanical", "Creates creature or other tokens."),
    ("Repeatable_Token_Generation","mechanical", "Creates tokens repeatedly — each upkeep, each turn, or on a recurring trigger."),
    ("Reanimation",       "mechanical", "Returns cards from graveyard to the battlefield."),
    ("Mass_Reanimate",    "mechanical", "Returns multiple creatures from graveyards simultaneously — a board-state reset."),
    ("Recursion_To_Hand",         "mechanical", "Returns cards from graveyard to hand."),
    ("Return_Self_From_Graveyard","mechanical", "This card returns itself from the graveyard without external help."),
    ("Mana_Multiplier",   "mechanical", "Doubles, multiplies, or scales mana production beyond normal."),
    ("Mana_Production",   "mechanical", "Produces mana (artifacts, creatures, enchantments — not lands)."),
    ("Tutor_Effect",      "mechanical", "Searches library for a specific card."),
    ("Board_Wipe",        "mechanical", "Destroys or exiles most or all creatures/permanents."),
    ("Graveyard_Hate",    "mechanical", "Removes or disrupts cards in graveyards."),
    ("Discard_Effect",    "mechanical", "Forces opponents (or self) to discard cards."),
    ("Self_Mill",         "mechanical", "Puts cards from library into graveyard."),
    ("Cost_Reduction",    "mechanical", "Reduces mana costs of spells or abilities."),
    ("Life_Payment",      "mechanical", "Uses life as a cost or substitute resource — converts life into mana, cards, or effects."),
    ("Counter_Spell",     "mechanical", "Counters spells or abilities."),
    ("Death_Trigger",      "mechanical", "Has an ability that triggers when ANY creature dies — global death payoff (Blood Artist, Grave Pact)."),
    ("Self_Death_Trigger", "mechanical", "Triggers when THIS card itself dies — distinct from global death payoffs like Blood Artist."),
    ("Scales_With_Deaths", "mechanical", "Power scales with how many creatures have died — counters, mana, or damage accumulate over the game."),
    ("Permanent_Scaling",  "mechanical", "Power scales with the number of permanents, lands, or symbols on the battlefield — grows with board state."),
    ("ETB_Trigger",       "mechanical", "Has an ability that triggers when it or another permanent enters the battlefield."),
    ("Upkeep_Trigger",    "mechanical", "Has an ability that triggers at the beginning of an upkeep step — recurring value each turn."),
    ("Trigger_Doubler",   "mechanical", "Causes triggered abilities to fire an additional time — doubles the output of any engine."),
    ("Targeted_Removal",  "mechanical", "Destroys or exiles a specific targeted permanent."),
    ("Bounce_Effect",     "mechanical", "Returns permanents to their owner's hand."),
    ("Damage_Effect",     "mechanical", "Deals direct damage to creatures, players, or planeswalkers."),
    ("Protection_Effect", "mechanical", "Grants hexproof, shroud, indestructible, or similar protection."),
    ("Evasion",           "mechanical", "Can damage players or squeeze through blockers — flying, menace, fear, shadow, or similar."),
    ("Lifelink",          "mechanical", "Combat damage causes life gain — sustains through damage and enables life-based payoffs."),
    ("Deathtouch",        "mechanical", "Any amount of damage it deals is lethal — makes it a removal threat in combat."),
    ("Looting_Effect",    "mechanical", "Draws cards then discards cards (or vice versa) — cycles hand while filling the graveyard."),
    ("Combat_Trigger",    "mechanical", "Has an ability that triggers when it or another creature attacks or deals combat damage."),
    ("Search_For_Land",   "mechanical", "Searches the library for a land card — provides ramp or mana fixing."),
    ("Graveyard_Tutor",   "mechanical", "Searches the library and puts cards directly into the graveyard — Entomb, Buried Alive, Unmarked Grave."),
    ("Undying_Persist",   "mechanical", "Returns from graveyard with a +1/+1 or -1/-1 counter — inherently recurs, hard to permanently answer."),
    ("Extort",            "mechanical", "Drains life from all opponents whenever you cast a spell — scales with spell count in multiplayer."),
    ("Devotion_Effect",   "mechanical", "Scales with devotion — counts colored mana symbols among permanents you control."),
    ("X_Spell_Effect",    "mechanical", "Effect scales with X mana spent — bigger payoff with more mana investment."),

    # ── Layer 3: Functional ──────────────────────────────────────────────────
    # What role the card plays in a deck. One card can have multiple functional tags.

    ("Mana_Acceleration", "functional", "Produces more mana than a normal land drop, helping cast spells faster."),
    ("Mana_Engine",       "functional", "Provides repeatable or scaling mana — doubles, scales with board, etc."),
    ("Card_Draw",         "functional", "Literally draws cards — increases cards in hand or cards seen. Not tutors."),
    ("Card_Advantage",    "functional", "Generates card advantage — draws cards, tutors, replaces itself."),
    ("Removal",           "functional", "Eliminates threats — spot removal or board wipes."),
    ("Protection",        "functional", "Shields key cards or the board state from removal."),
    ("Threat",            "functional", "Is itself a threat that demands an answer."),
    ("Finisher",          "functional", "Can directly close out the game when conditions are met."),
    ("Finisher_Support",  "functional", "Enables or powers up finishers without being one itself."),
    ("Engine",            "functional", "Enables the deck's core plan repeatedly."),
    ("Fuel",              "functional", "Provides expendable resources — tokens, creatures, mana — for the engine."),
    ("Payoff",            "functional", "Rewards executing the deck's plan with damage, life, cards, or mana."),
    ("Enabler",           "functional", "Enables key combos, synergies, or plans without being the payoff."),
    ("Recursion",         "functional", "Returns things from the graveyard to hand or battlefield."),
    ("Interaction",       "functional", "Disrupts opponents — counters, removal, stax effects."),
    ("Setup",             "functional", "Sets up future turns — tutors, fetches, digs for pieces."),
    ("Conversion",        "functional", "Converts one resource into another (creatures → mana, life → cards, etc.)."),

    # ── Layer 4: Archetype ───────────────────────────────────────────────────
    # What strategies specifically want this card.

    ("Aristocrats",    "archetype", "Sacrifice-based strategies that exploit creature deaths for value."),
    ("Reanimator",     "archetype", "Strategies that reanimate large creatures from the graveyard."),
    ("Big_Mana",       "archetype", "Strategies that generate large mana pools for X-spells or massive threats."),
    ("Voltron",        "archetype", "Commander damage strategies that buff a single creature."),
    ("Lifegain",       "archetype", "Strategies built around gaining and leveraging life totals."),
    ("Spellslinger",   "archetype", "Strategies that reward casting many instants and sorceries."),
    ("Control",        "archetype", "Reactive strategies that counter and remove threats until winning late."),
    ("Stax",           "archetype", "Resource denial strategies that lock opponents out."),
    ("Tokens",         "archetype", "Strategies that flood the board with tokens."),
    ("Graveyard",      "archetype", "Strategies that use the graveyard as a resource."),
    ("Devotion",       "archetype", "Strategies that benefit from many colored mana symbols on permanents."),
    ("Blink",          "archetype", "Strategies that exploit enters-the-battlefield triggers repeatedly."),
    ("Sacrifice",      "archetype", "Strategies centered on sacrificing permanents for value."),
    ("Discard",        "archetype", "Strategies built around discarding and reanimating or profiting."),
    ("Mill",           "archetype", "Strategies that win by emptying an opponent's library."),

    # ── Layer 5: Emotional / Play-Pattern ────────────────────────────────────
    # Strategic identity — how the card feels to play and what it represents in the deck.

    ("Engine_Core",       "emotional", "A card the deck is built to enable, protect, and repeat."),
    ("Renewable_Fuel",    "emotional", "Provides repeatable bodies or resources — hard to exhaust."),
    ("Apex_Threat",       "emotional", "Demands an immediate answer or the game often ends."),
    ("Conversion_Piece",  "emotional", "Converts one type of resource into another at high efficiency."),
    ("Pressure_Piece",    "emotional", "Applies constant upward pressure on opponents every turn."),
    ("Resilience_Piece",  "emotional", "Difficult to permanently answer — returns, regenerates, or replaces itself."),
    ("Identity_Card",     "emotional", "Strongly represents the deck's personality and strategy."),
    ("Table_Threat",      "emotional", "Draws attention and reactions from other players at the table."),
    ("Comeback_Card",     "emotional", "Helps stabilize or take back momentum when behind."),
    ("Grand_Finisher",    "emotional", "Ends the game outright when it resolves — no delay."),
    ("Momentum_Spike",    "emotional", "Creates a breakout turn that pulls the deck far ahead."),
    ("Efficient_Staple",  "emotional", "Low-cost, high-efficiency card that consistently earns its slot."),
    ("Cheap_Enabler",     "emotional", "Low-cost enabler that keeps the engine running at minimal tempo cost."),
]


# ─── Reminder Text Stripping ──────────────────────────────────────────────────
#
# Oracle text sometimes embeds keyword reminder text in parentheses, e.g.:
#   "Undying (When this creature dies, if it had no +1/+1 counters on it...)"
#   "Extort (Whenever you cast a spell, you may pay...)"
#   Treasure token reminder: "(It's an artifact with '{T}, Sacrifice this artifact:
#     Add one mana of any color.')"
#
# We strip these parenthetical blocks before pattern matching to avoid false
# positives — especially Mana_Production firing on Treasure token reminder text.
# The core ability text (before the paren) still matches the keyword patterns.

def _strip_reminder_text(text: str) -> str:
    """
    Remove parenthetical reminder text from oracle text before pattern matching.

    Parenthetical reminders are informational only and should not influence
    mechanical tagging. Examples:
      "Flying (This creature can block creatures with flying.)" → "Flying "
      "(It's an artifact with '{T}, Sacrifice this artifact: Add one mana of any color.')" → " "

    Handles nested parens at depth 1 (MTG oracle text never goes deeper).
    """
    return re.sub(r'\([^)]*\)', '', text)


# ─── Oracle Text Auto-Tag Patterns (mechanical layer only) ────────────────────
#
# Each entry: (tag_name, regex_pattern, confidence, rule_id)
# rule_id uniquely identifies the pattern for evidence tracing.
# Patterns are applied to REMINDER-TEXT-STRIPPED lowercased oracle text.
# Keep these precise to avoid false positives.

_MECHANICAL_PATTERNS: list[tuple[str, str, float, str]] = [

    # Draw effects
    ("Draw_Effect",       r"draw (?:a card|(?:\w+ )?cards)", 1.0,
        "mechanical.draw_effect.draw_cards.v1"),

    # Life drain / gain
    ("Life_Drain",        r"each opponent loses \w+ life", 0.9,
        "mechanical.life_drain.each_opponent_loses.v1"),
    ("Life_Drain",        r"target (?:player|opponent) loses \w+ life", 0.9,
        "mechanical.life_drain.target_loses.v1"),
    # Compound clause: "sacrifices a permanent, discards a card, and loses 3 life" — Archon of Cruelty
    ("Life_Drain",        r"and loses? \d+ life", 0.85,
        "mechanical.life_drain.compound_loses.v1"),
    ("Life_Gain",         r"you gain \w+ life", 0.9,
        "mechanical.life_gain.you_gain.v1"),
    ("Life_Gain",         r"gain \w+ life", 0.8,
        "mechanical.life_gain.gain_life.v1"),
    # "you gain life equal to the life lost this way" — Exsanguinate, drain spells
    ("Life_Gain",         r"you gain life equal to", 0.85,
        "mechanical.life_gain.gain_equal_to.v1"),
    # "you gain that much life" — Extort reminder text, Consuming Aberration variants
    ("Life_Gain",         r"you gain that much life", 0.85,
        "mechanical.life_gain.gain_that_much.v1"),

    # Sacrifice outlets — card has an activated ability whose cost includes sacrificing.
    # Requires the colon that separates cost from effect in activated abilities:
    #   "Sacrifice a creature: Scry 1"        → outlet ✓
    #   "Sacrifice a creature: Add {C}{C}."   → outlet ✓ (also caught by second pattern)
    # This intentionally excludes:
    #   "As an additional cost to cast this spell, sacrifice a creature." (Victimize)
    #   "When [name] enters, sacrifice another creature." (Disciple of Bolas)
    # Those are casting costs / ETB triggers, not repeatable outlets.
    ("Sacrifice_Outlet",  r"sacrifice (?:a|another|any number of) (?:\w+ )*(?:creature|permanent)\s*:", 1.0,
        "mechanical.sacrifice_outlet.sacrifice_cost.v1"),
    ("Sacrifice_Outlet",  r"sacrifice .{1,20}: add", 1.0,
        "mechanical.sacrifice_outlet.sacrifice_for_mana.v1"),

    # Forced sacrifice (OPPONENTS are forced to sacrifice)
    # Covers: Sheoldred, Grave Pact, Plaguecrafter, Braids, Butcher of Malakir
    # "may sacrifice" (Braids) is still a forced choice — same archetype signal.
    ("Forced_Sacrifice",  r"(?:that player|each player|each other player|target opponent|each opponent) (?:may )?sacrifice(?:s)? (?:a |an |another |all )?(?:\w+ )?(?:creature|permanent|planeswalker)", 1.0,
        "mechanical.forced_sacrifice.opponent_sacrifices.v1"),

    # Token generation
    # "create a 2/2 black Zombie" — standard format with optional article
    ("Token_Generation",           r"create (?:a |an )?\d+/\d+ .{1,40}token", 0.9,
        "mechanical.token_generation.create_pt_token.v1"),
    # "create two 2/2 black Zombie" — number word before the P/T (Grave Titan, etc.)
    ("Token_Generation",           r"create \w+ \d+/\d+ .{1,40}token", 0.9,
        "mechanical.token_generation.create_count_pt_token.v1"),
    # "create X creature tokens" — generic token count
    ("Token_Generation",           r"create (?:\w+ )?creature tokens?", 0.85,
        "mechanical.token_generation.create_creature_token.v1"),
    # Artifact tokens: Treasure, Food, Blood, Clue, Gold, Ichor, Map
    # "create a Treasure token" — Pitiless Plunderer, Deadly Dispute, etc.
    ("Token_Generation",           r"create (?:a |an |two |three )?(?:treasure|food|blood|clue|gold|ichor|map) token", 0.9,
        "mechanical.token_generation.create_artifact_token.v1"),
    # "investigate" keyword — always creates a Clue token (reminder text is stripped)
    ("Token_Generation",           r"\binvestigate\b", 0.85,
        "mechanical.token_generation.investigate.v1"),

    # Repeatable token generation — creates tokens on a recurring trigger
    # "at the beginning of your upkeep/turn/end step" or "each player's upkeep"
    ("Repeatable_Token_Generation", r"at the beginning of (?:your|each|each player's) (?:upkeep|turn|end step).{1,80}create", 0.95,
        "mechanical.repeatable_token.upkeep_create.v1"),
    # Whenever-based repeatable tokens — triggered on a recurring event on a permanent
    ("Repeatable_Token_Generation", r"whenever .{1,60}create a .{1,30}token", 0.85,
        "mechanical.repeatable_token.whenever_create.v1"),

    # Reanimation (to battlefield) — single target
    # Pattern 1: "Return target creature card from a graveyard to the battlefield"
    ("Reanimation",       r"return .{1,80}graveyard to the battlefield", 1.0,
        "mechanical.reanimation.graveyard_to_battlefield.v1"),
    # Pattern 2: Aura-based reanimate (Animate Dead, Dance of the Dead)
    ("Reanimation",       r"return enchanted creature card to the battlefield", 0.95,
        "mechanical.reanimation.aura_enchanted_card.v1"),

    # Mass reanimation — returns many creatures at once
    # Living Death: "puts all cards they exiled this way onto the battlefield"
    ("Mass_Reanimate",    r"put(?:s)? all .{0,40}cards?.{1,50}onto the battlefield", 0.95,
        "mechanical.mass_reanimate.all_cards_to_battlefield.v1"),
    # Wake the Dead: "Return X target creature cards from your graveyard to the battlefield"
    ("Mass_Reanimate",    r"return (?:up to )?\w+ target creature cards? from", 0.95,
        "mechanical.mass_reanimate.multiple_target_creatures.v1"),

    # Recursion (to hand)
    ("Recursion_To_Hand",          r"return .{1,40}graveyard to (?:its owner's|your) hand", 0.9,
        "mechanical.recursion_to_hand.graveyard_to_hand.v1"),

    # Self-recursion — card returns itself from graveyard
    # Modern Scryfall oracle standardizes self-recursion as "return this card from your graveyard"
    # Covers: Reassembling Skeleton, Bloodghast, Nether Traitor, and similar.
    ("Return_Self_From_Graveyard", r"return this card from your graveyard to", 0.95,
        "mechanical.return_self.this_card_from_graveyard.v1"),
    # Older/grant wording — "when this creature dies, return it to the battlefield" (Abnormal Endurance)
    ("Return_Self_From_Graveyard", r"when this creature dies.{1,60}return it to the battlefield", 0.9,
        "mechanical.return_self.dies_return_to_battlefield.v1"),

    # Mana doublers / multipliers
    ("Mana_Multiplier",   r"add an amount of mana equal to", 0.95,
        "mechanical.mana_multiplier.add_amount_equal_to.v1"),
    ("Mana_Multiplier",   r"for each swamp you control, add", 0.95,
        "mechanical.mana_multiplier.per_swamp_add.v1"),
    ("Mana_Multiplier",   r"doubles the mana", 0.95,
        "mechanical.mana_multiplier.doubles_mana.v1"),
    ("Mana_Multiplier",   r"add that much mana of any (?:one )?(?:type|color)", 0.85,
        "mechanical.mana_multiplier.add_that_much.v1"),
    # "Whenever you tap a Swamp for mana, add an additional {B}" — Crypt Ghast, Magus of the Coffers style
    # Also catches "adds an additional {B}" (Bubbling Muck uses third-person "adds")
    ("Mana_Multiplier",   r"adds? an additional \{[wubrgcx]\}", 0.9,
        "mechanical.mana_multiplier.add_additional_symbol.v1"),
    # "Whenever you tap a land for mana, add one mana of any type" — general tap doublers
    ("Mana_Multiplier",   r"whenever you tap .{1,30}for mana, add", 0.9,
        "mechanical.mana_multiplier.tap_for_mana_add.v1"),
    # "its controller adds one mana of that color" — Gauntlet of Power-style ability-text doubling
    # (the parenthetical "This effect doubles the mana..." is stripped as reminder text)
    ("Mana_Multiplier",   r"adds one mana of that color", 0.85,
        "mechanical.mana_multiplier.adds_one_mana.v1"),

    # Mana production (non-land permanents)
    ("Mana_Production",   r"add \{[wubrgc]\}", 0.9,
        "mechanical.mana_production.add_color_symbol.v1"),
    ("Mana_Production",   r"add (?:one|two|three) mana", 0.9,
        "mechanical.mana_production.add_word_mana.v1"),

    # Tutors
    ("Tutor_Effect",      r"search your library for (?:a |an |any |up to )", 1.0,
        "mechanical.tutor_effect.search_library_for.v1"),

    # Board wipes
    ("Board_Wipe",        r"destroy all (?:creatures|permanents|artifacts|enchantments|nonland)", 1.0,
        "mechanical.board_wipe.destroy_all.v1"),
    ("Board_Wipe",        r"exile all (?:creatures|permanents|nonland)", 1.0,
        "mechanical.board_wipe.exile_all.v1"),
    # Stat-based board wipe — "all creatures get -X/-X" (Toxic Deluge, Mutilate, etc.)
    ("Board_Wipe",        r"all creatures get -\w+/-\w+", 0.95,
        "mechanical.board_wipe.minus_stats.v1"),

    # Graveyard hate
    ("Graveyard_Hate",    r"exile (?:all cards in|target card from|each card from) (?:\w+ )?graveyard", 0.9,
        "mechanical.graveyard_hate.exile_graveyard.v1"),

    # Discard
    ("Discard_Effect",    r"(?:each player|target player|each opponent) discards", 0.9,
        "mechanical.discard_effect.player_discards.v1"),
    # "each player who can't [sacrifice] discards a card" — Plaguecrafter, Fleshbag Marauder
    ("Discard_Effect",    r"each player who can't discards", 0.85,
        "mechanical.discard_effect.cant_sacrifice_discards.v1"),
    # "that player discards a card" — Braids conditional discard
    ("Discard_Effect",    r"that player discards", 0.85,
        "mechanical.discard_effect.that_player_discards.v1"),

    # Self-mill
    ("Self_Mill",         r"put the top \w+ cards? of your library into your graveyard", 0.9,
        "mechanical.self_mill.top_library_to_graveyard.v1"),
    ("Self_Mill",         r"mill \w+ cards?", 0.8,
        "mechanical.self_mill.mill_keyword.v1"),

    # Cost reduction
    ("Cost_Reduction",    r"costs? \{[0-9]\} less", 0.85,
        "mechanical.cost_reduction.mana_symbol_less.v1"),
    ("Cost_Reduction",    r"costs? \w+ less to cast", 0.85,
        "mechanical.cost_reduction.word_less_to_cast.v1"),

    # Life payment — life used as a cost or resource substitute
    # "pay X life" as an additional cost (Toxic Deluge, Ad Nauseam)
    ("Life_Payment",      r"as an additional cost.{1,40}pay \w+ life", 0.95,
        "mechanical.life_payment.additional_cost_life.v1"),
    # "pay 2 life rather than pay that mana" — K'rrik, Phyrexian mana cards
    ("Life_Payment",      r"pay \d+ life rather than", 0.95,
        "mechanical.life_payment.pay_life_rather_than.v1"),
    # "Pay 3 life:" or "{T}, Pay 1 life:" — life as activated ability cost.
    # Covers Chainer, Dementia Master; Ifnir Deadlands; and similar.
    # Placed AFTER pay_life_rather_than to avoid double-triggering on those cards,
    # though evidence idempotency handles duplicates safely.
    ("Life_Payment",      r"pay \d+ life", 0.9,
        "mechanical.life_payment.pay_n_life_cost.v1"),
    # "you draw a card and you lose 1 life" — Phyrexian Arena style (life drain as card cost)
    ("Life_Payment",      r"draw a card and (?:you )?(?:lose|pay) \d+ life", 0.85,
        "mechanical.life_payment.draw_and_lose_life.v1"),

    # Counters
    ("Counter_Spell",     r"counter target (?:spell|ability)", 1.0,
        "mechanical.counter_spell.counter_target.v1"),
    ("Counter_Spell",     r"counter target (?:instant|sorcery|creature|artifact|enchantment) spell", 1.0,
        "mechanical.counter_spell.counter_type_spell.v1"),

    # Permanent scaling — power scales with how many permanents/lands/symbols are on the battlefield
    # "for each Swamp you control" — Lashwrithe, Nightmare, Crypt Ghast extort
    ("Permanent_Scaling",  r"for each swamp you control", 0.9,
        "mechanical.permanent_scaling.per_swamp.v1"),
    # "for each [type] you control" — generic scaling (devotion, tribal, etc.)
    ("Permanent_Scaling",  r"for each (?:land|creature|artifact|enchantment|permanent) you control", 0.85,
        "mechanical.permanent_scaling.per_permanent_type.v1"),
    # "equal to the number of [something] you control"
    ("Permanent_Scaling",  r"equal to the number of .{1,30}you control", 0.85,
        "mechanical.permanent_scaling.equal_to_count.v1"),

    # Scales with deaths — accumulates power over time as creatures die (counters, mana, damage)
    # "whenever a creature dies, put a counter" — Black Market, Dread Presence, etc.
    ("Scales_With_Deaths", r"whenever .{1,30}creature.{1,20}dies?, (?:put|place) .{1,20}counter", 0.9,
        "mechanical.scales_with_deaths.dies_put_counter.v1"),
    # "for each [color] creature card in your graveyard" — Crypt of Agadeem and similar
    ("Scales_With_Deaths", r"for each (?:\w+ )?creature card in (?:your|their|all) graveyard", 0.85,
        "mechanical.scales_with_deaths.per_graveyard_creature.v1"),

    # Death triggers — matches "whenever [anything] creature(s) dies/die"
    # Covers: "whenever a creature dies", "whenever another creature dies",
    #         "whenever Blood Artist or another creature dies", etc.
    ("Death_Trigger",     r"whenever .{1,40}creature(?:s)? (?:you control )?(?:dies|die)", 0.9,
        "mechanical.death_trigger.whenever_creature_dies.v1"),

    # Self-death trigger — this card itself has a trigger when IT dies.
    # Distinct from Death_Trigger (which fires when ANY creature dies).
    # Covers: Bile-Vial Boggart, Festering Newt, Golgari Thug, Tattered Mummy, etc.
    # Note: confidence 0.85 because granted abilities ("gains 'when this creature dies'")
    # can also match; they are less common but not excluded by stripping.
    ("Self_Death_Trigger", r"when this (?:creature|permanent) dies", 0.85,
        "mechanical.self_death_trigger.when_this_dies.v1"),

    # Trigger doublers — makes other triggered abilities fire again. Major engine amplifier.
    ("Trigger_Doubler",   r"triggers? an additional time", 0.95,
        "mechanical.trigger_doubler.additional_time.v1"),
    ("Trigger_Doubler",   r"triggers? twice", 0.95,
        "mechanical.trigger_doubler.triggers_twice.v1"),
    ("Trigger_Doubler",   r"each of those triggered abilities triggers an additional time", 0.95,
        "mechanical.trigger_doubler.each_ability_additional.v1"),

    # Upkeep / main-phase / end-step triggers — fires every turn, strong recurring value signal.
    # Covers: "at the beginning of your upkeep", "each opponent's upkeep",
    #         "each other player's upkeep" (Braids), "your first main phase", "your end step".
    ("Upkeep_Trigger",    r"at the beginning of (?:your|each|each player's|each other player's|each opponent's) (?:upkeep|precombat main phase|first main phase|end step)", 0.95,
        "mechanical.upkeep_trigger.at_beginning.v1"),

    # ETB triggers
    # Pattern 1: classic wording — "when [name] enters the battlefield"
    ("ETB_Trigger",       r"when (?:this|it|.{1,20}) enters the battlefield", 0.8,
        "mechanical.etb_trigger.when_enters_classic.v1"),
    # Pattern 2: modern Oracle wording (post-2022) — "when/whenever this creature enters[, / or attacks]"
    ("ETB_Trigger",       r"when(?:ever)? (?:this|.{1,30}) enters(?:,| or)", 0.8,
        "mechanical.etb_trigger.when_enters_modern.v1"),

    # Targeted removal
    # Allow optional qualifier before the permanent type: "nonblack", "tapped", "nonartifact", etc.
    ("Targeted_Removal",  r"destroy target (?:\w+ )?(?:creature|permanent|artifact|enchantment|planeswalker)", 1.0,
        "mechanical.targeted_removal.destroy_target.v1"),
    ("Targeted_Removal",  r"exile target (?:\w+ )?(?:creature|permanent|artifact|enchantment|planeswalker)", 1.0,
        "mechanical.targeted_removal.exile_target.v1"),

    # Damage
    ("Damage_Effect",     r"deals? \w+ damage to (?:any target|target creature|each creature|each player|each opponent)", 0.9,
        "mechanical.damage_effect.deals_damage.v1"),

    # Bounce
    ("Bounce_Effect",     r"return target .{1,30} to (?:its owner's|their owner's) hand", 0.9,
        "mechanical.bounce_effect.return_to_hand.v1"),

    # Protection
    ("Protection_Effect", r"(?:has|have|gains?) hexproof", 0.9,
        "mechanical.protection.hexproof.v1"),
    ("Protection_Effect", r"(?:has|have|gains?) indestructible", 0.9,
        "mechanical.protection.indestructible.v1"),
    ("Protection_Effect", r"(?:has|have|gains?) shroud", 0.9,
        "mechanical.protection.shroud.v1"),

    # Evasion — can push damage past blockers
    # Hard keywords: flying, menace, fear, shadow, intimidate
    ("Evasion",           r"\bflying\b", 1.0,
        "mechanical.evasion.flying.v1"),
    ("Evasion",           r"\bmenace\b", 1.0,
        "mechanical.evasion.menace.v1"),
    ("Evasion",           r"\bfear\b", 0.9,
        "mechanical.evasion.fear.v1"),
    ("Evasion",           r"\bshadow\b", 0.9,
        "mechanical.evasion.shadow.v1"),
    ("Evasion",           r"\bintimidate\b", 0.95,
        "mechanical.evasion.intimidate.v1"),
    # Landwalk — unblockable when defending player controls that land type
    ("Evasion",           r"\b(?:swamp|forest|island|mountain|plains|land)walk\b", 0.9,
        "mechanical.evasion.landwalk.v1"),
    # "can't be blocked" / "is unblockable" — two oracle wordings for unblockability
    ("Evasion",           r"can't be blocked", 0.95,
        "mechanical.evasion.cant_be_blocked.v1"),
    ("Evasion",           r"\bunblockable\b", 0.95,
        "mechanical.evasion.unblockable.v1"),

    # Lifelink — combat damage as life gain
    ("Lifelink",          r"\blifelink\b", 1.0,
        "mechanical.lifelink.keyword.v1"),
    ("Lifelink",          r"gains? lifelink", 0.9,
        "mechanical.lifelink.gains.v1"),

    # Deathtouch — lethal damage regardless of toughness
    ("Deathtouch",        r"\bdeathtouch\b", 1.0,
        "mechanical.deathtouch.keyword.v1"),
    ("Deathtouch",        r"gains? deathtouch", 0.9,
        "mechanical.deathtouch.gains.v1"),

    # Looting — draw-then-discard or discard-then-draw
    # "draw two cards, then discard two cards" — Faithless Looting, Careful Study
    ("Looting_Effect",    r"draw .{1,30},? then discard", 0.9,
        "mechanical.looting.draw_then_discard.v1"),
    # "discard a card, then draw two cards" — Thrill of Possibility, Wild Guess
    ("Looting_Effect",    r"discard .{1,30},? then draw", 0.9,
        "mechanical.looting.discard_then_draw.v1"),

    # Combat triggers — fires when something attacks or deals combat damage
    # "whenever [X] attacks" — attack trigger
    ("Combat_Trigger",    r"whenever .{1,40} attacks?[,\.]", 0.85,
        "mechanical.combat_trigger.whenever_attacks.v1"),
    # "whenever [X] deals combat damage to" — combat damage trigger
    ("Combat_Trigger",    r"whenever .{1,40} deals? combat damage to", 0.9,
        "mechanical.combat_trigger.deals_combat_damage.v1"),

    # Land search — ramp via fetching lands from the library
    # "search your library for a basic land card" / "a land card" / "a Swamp"
    ("Search_For_Land",   r"search your library for (?:a |an |up to (?:\w+ )?)?(?:basic )?(?:land|swamp|forest|island|plains|mountain)", 0.95,
        "mechanical.search_for_land.search_library_land.v1"),

    # Graveyard tutors — search library and PUT cards directly into the graveyard.
    # Covers: Entomb, Buried Alive, Unmarked Grave, Jarad's Orders (partial).
    # Deliberately distinct from Search_For_Land / Tutor_Effect (which goes to hand).
    ("Graveyard_Tutor",   r"search your library for .{0,60}?put (?:it|them|that card) into your graveyard", 0.95,
        "mechanical.graveyard_tutor.search_put_to_graveyard.v1"),

    # Undying / Persist — returns after dying with a counter change
    ("Undying_Persist",   r"\bundying\b", 1.0,
        "mechanical.undying_persist.undying.v1"),
    ("Undying_Persist",   r"\bpersist\b", 1.0,
        "mechanical.undying_persist.persist.v1"),

    # Extort — drains life on every spell cast
    ("Extort",            r"\bextort\b", 1.0,
        "mechanical.extort.keyword.v1"),

    # Devotion effects — power scales with colored mana symbols among permanents
    # "your devotion to black" — Gary, Erebos, Nykthos
    ("Devotion_Effect",   r"(?:your|each player's) devotion to (?:\w+|any color)", 0.95,
        "mechanical.devotion.devotion_to_color.v1"),

    # X-spell scaling — effect scales with X mana spent (Exsanguinate, Torment of Hailfire, etc.)
    # Life-drain X: "each opponent loses X life"
    ("X_Spell_Effect",    r"each opponent loses x life", 0.95,
        "mechanical.x_spell.each_opponent_loses_x.v1"),
    # Targeted X: "target player loses X life"
    ("X_Spell_Effect",    r"target player loses x life", 0.90,
        "mechanical.x_spell.target_loses_x.v1"),
    # Damage X: "deals X damage to each opponent / any target"
    ("X_Spell_Effect",    r"deals? x damage", 0.90,
        "mechanical.x_spell.deals_x_damage.v1"),
    # Repeated effect: "repeat the following process X times" (Torment of Hailfire)
    ("X_Spell_Effect",    r"repeat the following process x times", 0.95,
        "mechanical.x_spell.repeat_x_times.v1"),
]


# ─── Functional Inference Rules (Layer 3) ────────────────────────────────────
#
# Each entry: (frozenset_of_required_mechanical_tags, functional_tag, confidence)
#
# A rule fires when ALL mechanical tags in the required set are present on a card.
# When multiple rules fire for the same functional tag, the highest confidence wins.
# Confidence semantics:
#   0.90+ = near-certain (strong mechanical evidence)
#   0.70–0.89 = probable (good but indirect evidence)
#   0.50–0.69 = plausible (weak evidence — single-tag rules for broad tags)

FUNCTIONAL_RULES: list[tuple[frozenset, str, float]] = [

    # ── Mana_Acceleration ────────────────────────────────────────────────────
    # Any card that produces more mana than it costs (rocks, ramp, doublers, reducers)
    # NOTE: Life_Payment alone does NOT imply mana acceleration. Phyrexian Arena pays
    # life for cards, not mana. K'rrik pays life instead of mana — but K'rrik has both
    # Life_Payment AND Mana_Production, which is caught by the Mana_Engine rules below.
    (frozenset({"Mana_Production"}),                                "Mana_Acceleration", 0.75),
    (frozenset({"Mana_Multiplier"}),                                "Mana_Acceleration", 0.90),
    (frozenset({"Search_For_Land"}),                                "Mana_Acceleration", 0.80),
    (frozenset({"Cost_Reduction"}),                                 "Mana_Acceleration", 0.65),

    # ── Mana_Engine ──────────────────────────────────────────────────────────
    # Repeating, scaling, or amplifying mana production — more than basic ramp
    (frozenset({"Mana_Multiplier"}),                                "Mana_Engine",       0.90),
    (frozenset({"Mana_Production", "Upkeep_Trigger"}),              "Mana_Engine",       0.85),
    (frozenset({"Mana_Production", "Scales_With_Deaths"}),          "Mana_Engine",       0.85),
    (frozenset({"Mana_Production", "Permanent_Scaling"}),           "Mana_Engine",       0.85),
    (frozenset({"Mana_Production", "Sacrifice_Outlet"}),            "Mana_Engine",       0.85),
    (frozenset({"Mana_Production", "Death_Trigger"}),               "Mana_Engine",       0.80),

    # ── Card_Draw ────────────────────────────────────────────────────────────
    # Literally draws cards — narrows Card_Advantage to genuine draw effects only.
    # Tutors do NOT get Card_Draw — they get Setup instead.
    # This is the tag the "draw" profile category uses.
    (frozenset({"Draw_Effect"}),                                    "Card_Draw",         0.85),
    (frozenset({"Draw_Effect", "Death_Trigger"}),                   "Card_Draw",         0.90),
    (frozenset({"Draw_Effect", "Upkeep_Trigger"}),                  "Card_Draw",         0.90),
    (frozenset({"Draw_Effect", "ETB_Trigger"}),                     "Card_Draw",         0.85),
    (frozenset({"Draw_Effect", "Combat_Trigger"}),                  "Card_Draw",         0.85),
    (frozenset({"Draw_Effect", "Forced_Sacrifice"}),                "Card_Draw",         0.85),

    # ── Card_Advantage ───────────────────────────────────────────────────────
    # Generates card advantage — draws, tutors, or replaces itself.
    # Broader than Card_Draw: includes tutors, looting, and repeatable draw.
    # Does NOT map to the "draw" profile category (use Card_Draw for that).
    (frozenset({"Draw_Effect"}),                                    "Card_Advantage",    0.80),
    (frozenset({"Tutor_Effect"}),                                   "Card_Advantage",    0.90),
    (frozenset({"Looting_Effect"}),                                 "Card_Advantage",    0.65),
    (frozenset({"Draw_Effect", "Death_Trigger"}),                   "Card_Advantage",    0.85),
    (frozenset({"Draw_Effect", "Upkeep_Trigger"}),                  "Card_Advantage",    0.90),
    (frozenset({"Draw_Effect", "ETB_Trigger"}),                     "Card_Advantage",    0.80),
    (frozenset({"Draw_Effect", "Combat_Trigger"}),                  "Card_Advantage",    0.80),

    # ── Removal ──────────────────────────────────────────────────────────────
    # Eliminates threats — spot removal, board wipes, or disruptive sacrifice
    (frozenset({"Targeted_Removal"}),                               "Removal",           0.95),
    (frozenset({"Board_Wipe"}),                                     "Removal",           0.95),
    (frozenset({"Forced_Sacrifice"}),                               "Removal",           0.85),
    (frozenset({"Counter_Spell"}),                                  "Removal",           0.85),
    (frozenset({"Bounce_Effect"}),                                  "Removal",           0.65),
    (frozenset({"Discard_Effect"}),                                 "Removal",           0.60),
    (frozenset({"Graveyard_Hate"}),                                 "Removal",           0.70),
    (frozenset({"Damage_Effect"}),                                  "Removal",           0.55),

    # ── Interaction ──────────────────────────────────────────────────────────
    # Disrupts opponents — broader than removal, includes counters and discard
    (frozenset({"Counter_Spell"}),                                  "Interaction",       0.95),
    (frozenset({"Targeted_Removal"}),                               "Interaction",       0.90),
    (frozenset({"Forced_Sacrifice"}),                               "Interaction",       0.85),
    (frozenset({"Discard_Effect"}),                                 "Interaction",       0.80),
    (frozenset({"Board_Wipe"}),                                     "Interaction",       0.80),
    (frozenset({"Bounce_Effect"}),                                  "Interaction",       0.75),
    (frozenset({"Graveyard_Hate"}),                                 "Interaction",       0.80),

    # ── Protection ───────────────────────────────────────────────────────────
    # Shields key cards or the board state from removal
    (frozenset({"Protection_Effect"}),                              "Protection",        0.90),
    (frozenset({"Counter_Spell"}),                                  "Protection",        0.75),

    # ── Threat ───────────────────────────────────────────────────────────────
    # Is itself a threat that demands an immediate answer
    (frozenset({"Forced_Sacrifice", "Upkeep_Trigger"}),             "Threat",            0.85),
    (frozenset({"Forced_Sacrifice", "ETB_Trigger"}),                "Threat",            0.80),
    (frozenset({"Forced_Sacrifice", "Death_Trigger"}),              "Threat",            0.80),
    (frozenset({"Evasion", "Combat_Trigger"}),                      "Threat",            0.80),
    (frozenset({"Evasion", "Life_Drain"}),                          "Threat",            0.75),
    (frozenset({"Evasion", "Forced_Sacrifice"}),                    "Threat",            0.80),
    (frozenset({"Life_Drain", "ETB_Trigger"}),                      "Threat",            0.70),
    (frozenset({"Death_Trigger", "Life_Drain"}),                    "Threat",            0.75),
    (frozenset({"Deathtouch", "Combat_Trigger"}),                   "Threat",            0.70),
    (frozenset({"Combat_Trigger", "Token_Generation"}),             "Threat",            0.70),
    (frozenset({"Sacrifice_Outlet", "Token_Generation"}),           "Threat",            0.70),
    (frozenset({"Evasion", "Lifelink"}),                            "Threat",            0.70),
    (frozenset({"Forced_Sacrifice"}),                               "Threat",            0.60),
    (frozenset({"Evasion"}),                                        "Threat",            0.50),

    # ── Finisher ─────────────────────────────────────────────────────────────
    # Can directly close out the game when conditions are met
    (frozenset({"X_Spell_Effect", "Life_Drain"}),                   "Finisher",          0.90),
    (frozenset({"Life_Drain", "Permanent_Scaling"}),                "Finisher",          0.85),
    (frozenset({"Life_Drain", "Devotion_Effect"}),                  "Finisher",          0.85),
    (frozenset({"Life_Drain", "Scales_With_Deaths"}),               "Finisher",          0.80),
    (frozenset({"Board_Wipe", "Mass_Reanimate"}),                   "Finisher",          0.85),
    (frozenset({"Mass_Reanimate"}),                                 "Finisher",          0.70),
    (frozenset({"Damage_Effect", "Permanent_Scaling"}),             "Finisher",          0.75),
    (frozenset({"Life_Drain", "Sacrifice_Outlet"}),                 "Finisher",          0.75),

    # ── Finisher_Support ─────────────────────────────────────────────────────
    # Powers up or enables finishers without being one itself
    (frozenset({"Mana_Multiplier"}),                                "Finisher_Support",  0.80),
    (frozenset({"Mana_Production", "Permanent_Scaling"}),           "Finisher_Support",  0.75),
    (frozenset({"Tutor_Effect"}),                                   "Finisher_Support",  0.65),
    (frozenset({"Self_Mill"}),                                      "Finisher_Support",  0.55),

    # ── Engine ───────────────────────────────────────────────────────────────
    # Enables the deck's core plan repeatedly — combines two meaningful abilities
    (frozenset({"Sacrifice_Outlet", "Mana_Production"}),            "Engine",            0.90),
    (frozenset({"Sacrifice_Outlet", "Draw_Effect"}),                "Engine",            0.90),
    (frozenset({"Death_Trigger", "Mana_Production"}),               "Engine",            0.85),
    (frozenset({"Death_Trigger", "Draw_Effect"}),                   "Engine",            0.85),
    (frozenset({"Upkeep_Trigger", "Mana_Production"}),              "Engine",            0.85),
    (frozenset({"Upkeep_Trigger", "Draw_Effect"}),                  "Engine",            0.85),
    (frozenset({"Scales_With_Deaths", "Mana_Production"}),          "Engine",            0.85),
    (frozenset({"Repeatable_Token_Generation"}),                    "Engine",            0.75),
    (frozenset({"Trigger_Doubler"}),                                "Engine",            0.80),
    (frozenset({"Death_Trigger", "Forced_Sacrifice"}),              "Engine",            0.85),
    (frozenset({"Sacrifice_Outlet", "Token_Generation"}),           "Engine",            0.80),
    (frozenset({"Sacrifice_Outlet", "Reanimation"}),                "Engine",            0.80),
    (frozenset({"Reanimation", "Upkeep_Trigger"}),                  "Engine",            0.85),
    (frozenset({"Forced_Sacrifice", "Draw_Effect"}),                "Engine",            0.75),
    (frozenset({"Life_Payment"}),                                   "Engine",            0.65),

    # ── Fuel ─────────────────────────────────────────────────────────────────
    # Provides expendable resources (tokens, recurring bodies, self-mill) for the engine
    (frozenset({"Return_Self_From_Graveyard"}),                     "Fuel",              0.85),
    (frozenset({"Repeatable_Token_Generation"}),                    "Fuel",              0.85),
    (frozenset({"Token_Generation"}),                               "Fuel",              0.65),
    (frozenset({"Undying_Persist"}),                                "Fuel",              0.80),
    (frozenset({"Self_Mill"}),                                      "Fuel",              0.60),

    # ── Payoff ───────────────────────────────────────────────────────────────
    # Rewards executing the plan with damage, life, cards, or mana
    (frozenset({"Death_Trigger", "Life_Drain"}),                    "Payoff",            0.90),
    (frozenset({"Death_Trigger", "Life_Gain"}),                     "Payoff",            0.85),
    (frozenset({"Death_Trigger", "Draw_Effect"}),                   "Payoff",            0.85),
    (frozenset({"Death_Trigger", "Mana_Production"}),               "Payoff",            0.75),
    (frozenset({"Death_Trigger", "Token_Generation"}),              "Payoff",            0.80),
    (frozenset({"Scales_With_Deaths"}),                             "Payoff",            0.80),
    (frozenset({"ETB_Trigger", "Life_Drain"}),                      "Payoff",            0.80),
    (frozenset({"ETB_Trigger", "Forced_Sacrifice"}),                "Payoff",            0.75),
    (frozenset({"Combat_Trigger", "Draw_Effect"}),                  "Payoff",            0.75),
    (frozenset({"Combat_Trigger", "Token_Generation"}),             "Payoff",            0.80),
    (frozenset({"Combat_Trigger", "Life_Drain"}),                   "Payoff",            0.80),
    (frozenset({"Devotion_Effect", "Life_Drain"}),                  "Payoff",            0.85),
    (frozenset({"Upkeep_Trigger", "Draw_Effect"}),                  "Payoff",            0.80),
    (frozenset({"Upkeep_Trigger", "Life_Drain"}),                   "Payoff",            0.80),
    (frozenset({"Forced_Sacrifice", "Draw_Effect"}),                "Payoff",            0.75),
    (frozenset({"Extort"}),                                         "Payoff",            0.70),

    # ── Enabler ──────────────────────────────────────────────────────────────
    # Enables key combos, synergies, or plans without being the payoff itself
    (frozenset({"Sacrifice_Outlet"}),                               "Enabler",           0.80),
    (frozenset({"Tutor_Effect"}),                                   "Enabler",           0.80),
    (frozenset({"Self_Mill"}),                                      "Enabler",           0.70),
    (frozenset({"Looting_Effect"}),                                 "Enabler",           0.65),
    (frozenset({"Reanimation"}),                                    "Enabler",           0.70),
    (frozenset({"Cost_Reduction"}),                                 "Enabler",           0.75),
    (frozenset({"Trigger_Doubler"}),                                "Enabler",           0.80),
    (frozenset({"Mass_Reanimate"}),                                 "Enabler",           0.70),

    # ── Recursion ────────────────────────────────────────────────────────────
    # Returns things from the graveyard to hand or battlefield
    (frozenset({"Reanimation"}),                                    "Recursion",         0.95),
    (frozenset({"Mass_Reanimate"}),                                 "Recursion",         0.95),
    (frozenset({"Recursion_To_Hand"}),                              "Recursion",         0.90),
    (frozenset({"Return_Self_From_Graveyard"}),                     "Recursion",         0.85),

    # ── Setup ────────────────────────────────────────────────────────────────
    # Sets up future turns — tutors, self-mill, looting
    (frozenset({"Tutor_Effect"}),                                   "Setup",             0.90),
    (frozenset({"Graveyard_Tutor"}),                                "Setup",             0.90),
    (frozenset({"Self_Mill"}),                                      "Setup",             0.75),
    (frozenset({"Looting_Effect"}),                                 "Setup",             0.70),
    (frozenset({"Search_For_Land"}),                                "Setup",             0.65),

    # ── Conversion ───────────────────────────────────────────────────────────
    # Converts one resource into another (creatures→mana, life→cards, etc.)
    (frozenset({"Sacrifice_Outlet", "Mana_Production"}),            "Conversion",        0.90),
    (frozenset({"Sacrifice_Outlet", "Draw_Effect"}),                "Conversion",        0.90),
    (frozenset({"Life_Payment", "Mana_Production"}),                "Conversion",        0.85),
    (frozenset({"Life_Payment", "Draw_Effect"}),                    "Conversion",        0.85),
    (frozenset({"Life_Payment", "Recursion_To_Hand"}),              "Conversion",        0.80),
    (frozenset({"Sacrifice_Outlet", "Token_Generation"}),           "Conversion",        0.80),
    (frozenset({"Death_Trigger", "Draw_Effect"}),                   "Conversion",        0.65),
    (frozenset({"Death_Trigger", "Mana_Production"}),               "Conversion",        0.70),
    (frozenset({"Death_Trigger", "Token_Generation"}),              "Conversion",        0.65),
    (frozenset({"Scales_With_Deaths", "Mana_Production"}),          "Conversion",        0.75),
    (frozenset({"Looting_Effect"}),                                 "Conversion",        0.65),
    (frozenset({"Life_Payment"}),                                   "Conversion",        0.65),
]


# ─── Public API ───────────────────────────────────────────────────────────────

def seed_tags(db) -> int:
    """
    Seed the tags table with the built-in tag registry.

    Safe to call on an existing database — uses INSERT OR IGNORE.
    Returns the number of tags that were newly inserted.

    Usage:
        db.connect()
        tags.seed_tags(db)
    """
    inserted = 0
    for name, layer, description in TAGS:
        tag_id = db.save_tag(name, layer, description)
        if tag_id:
            inserted += 1
    return inserted


def tag_card(
    card_name: str,
    tag_name: str,
    db,
    confidence: float = 1.0,
    source: str = "manual",
    note: str = "",
) -> bool:
    """
    Tag a card with a named tag.

    Args:
        card_name: exact card name (must exist in cards table)
        tag_name:  tag from the registry (e.g. 'Engine_Core')
        db:        open Database connection
        confidence: 0.0–1.0 (default 1.0 for manual tags)
        source:    'manual' | 'regex' | 'contextual' | 'ai'
        note:      optional human explanation

    Returns:
        True if tagged successfully, False if tag_name not found in registry.
    """
    return db.tag_card(card_name, tag_name, confidence, source, note)


def get_card_tags(card_name: str, db, layer: Optional[str] = None) -> list[dict]:
    """
    Get all tags for a card, optionally filtered by layer.

    Args:
        card_name: card name (case-insensitive)
        db:        open Database connection
        layer:     optional — 'mechanical' | 'functional' | 'archetype' | 'emotional'

    Returns:
        List of dicts: {name, layer, confidence, source, note}
        Sorted by confidence desc within each layer.
    """
    return db.get_card_tags(card_name, layer)


def get_tag_names(card_name: str, db, layer: Optional[str] = None) -> list[str]:
    """
    Convenience: get just the tag names (not full dicts) for a card.

    Useful for simple checks: 'Engine_Core' in tags.get_tag_names('Crypt Ghast', db)
    """
    return [t["name"] for t in db.get_card_tags(card_name, layer)]


def query_cards_by_tag(tag_name: str, db, min_confidence: float = 0.0) -> list[dict]:
    """
    Find all cards tagged with a given tag.

    Args:
        tag_name:       tag to search for (case-insensitive)
        db:             open Database connection
        min_confidence: filter out tags below this confidence

    Returns:
        List of dicts: {card_name, confidence, source, note}
    """
    return db.query_cards_by_tag(tag_name, min_confidence)


def add_synergy(
    card_a: str,
    card_b: str,
    synergy_type: str,
    db,
    strength: float = 0.5,
    explanation: str = "",
) -> int:
    """
    Record a synergy relationship between two cards.

    Synergy types (descriptive strings — no fixed enum):
        'Sacrifice_Loop'        — one provides outlet, other recurs
        'Death_Trigger_Fuel'    — one dies, other profits
        'Big_Mana_Finisher'     — one makes mana, other spends it
        'Draw_Engine'           — two cards that combine for repeated draw
        etc.

    Strength scale (0.0–1.0):
        1.0 = core synergy (the combo itself)
        0.7 = strong synergy
        0.5 = moderate
        0.3 = incidental

    Returns:
        synergy edge id
    """
    return db.add_synergy(card_a, card_b, synergy_type, strength, explanation)


def get_synergies(card_name: str, db, min_strength: float = 0.0) -> list[dict]:
    """
    Get all synergy relationships for a card.

    Returns:
        List of dicts: {other_card, synergy_type, strength, explanation}
    """
    return db.get_synergies(card_name, min_strength)


def _ability_kind_for_span(segments, oracle_start: int, oracle_end: int) -> str:
    """Return ability_kind of the segment whose span contains oracle_start.

    Segments and oracle_start must be in the same coordinate space (main_text).
    """
    for seg in segments:
        if seg.start <= oracle_start < seg.end:
            return seg.ability_kind
    return "other"


def _text_role_for_span(segments, oracle_start: int, oracle_end: int, ability_kind: str) -> str:
    """Classify the syntactic role of the match span within its ability.

    Segments and oracle_start must be in the same coordinate space (main_text).

    Roles:
      cost        — the payment portion of an activated ability (before ':')
      trigger     — the condition clause of a triggered ability (before first ',')
      effect      — the resolving effect
      replacement — part of a replacement effect ("instead")
      static      — part of a static ability (ongoing condition)
      unknown     — fallback
    """
    if ability_kind == "replacement":
        return "replacement"
    if ability_kind == "static":
        return "static"

    for seg in segments:
        if seg.start <= oracle_start < seg.end:
            seg_lower = seg.text.lower()
            rel_pos = oracle_start - seg.start  # position of match within this segment

            if ability_kind == "activated":
                colon_pos = seg_lower.find(":")
                if colon_pos != -1 and rel_pos < colon_pos:
                    return "cost"
                return "effect"

            if ability_kind == "triggered":
                comma_pos = seg_lower.find(",")
                if comma_pos != -1 and rel_pos < comma_pos:
                    return "trigger"
                return "effect"

    return "unknown"


def tag_mechanical(card: Card, db) -> list[str]:
    """
    Auto-tag a card's mechanical layer using oracle text patterns.

    This handles the obvious, objectively true mechanical tags.
    Functional, archetype, and emotional tags require human judgment.

    Args:
        card: Card object with oracle_text populated
        db:   open Database connection (tags must be seeded first)

    Returns:
        List of tag names that were successfully applied.

    Usage:
        db.connect()
        seed_tags(db)
        card = db.card_by_name("Blood Artist")
        applied = tag_mechanical(card, db)
        # → ['Draw_Effect', 'Death_Trigger', ...]
    """
    # Use search_text("main") for all matching. This gives spans into preprocessed.main_text
    # (reminder text stripped, original case), which is the same coordinate space as
    # segment.start/end. A single span from the match drives evidence, ability_kind,
    # and text_role — no re-searching inside the helpers.
    oracle_raw = card.oracle_text or ""
    is_land = "Land" in (card.type_line or "")
    applied = []

    preprocessed = preprocess_oracle(card.name, oracle_raw)

    for tag_name, pattern, confidence, rule_id in _MECHANICAL_PATTERNS:
        spans = _preprocess_search(preprocessed, pattern, search_in="main")
        if not spans:
            continue

        oracle_start, oracle_end = spans[0]

        # Lands produce mana by definition — "add {B}" in a land's oracle text
        # is its basic function, not a special ability. Only tag Mana_Production
        # for lands that produce *extra* or *scaling* mana (Crypt of Agadeem,
        # Cabal Coffers). Plain utility lands (Bojuka Bog, High Market, etc.)
        # should not be tagged — they tap for one mana like any basic.
        if tag_name == "Mana_Production" and is_land:
            if not _preprocess_search(preprocessed, r"for each|for every|twice|double", search_in="main"):
                continue

        # evidence_text from main_text preserves original case
        evidence_text = preprocessed.main_text[oracle_start:oracle_end]

        ability_kind = _ability_kind_for_span(preprocessed.segments, oracle_start, oracle_end)
        text_role = _text_role_for_span(preprocessed.segments, oracle_start, oracle_end, ability_kind)

        success = db.emit_tag_evidence(
            card_name=card.name,
            tag_name=tag_name,
            rule_id=rule_id,
            evidence_text=evidence_text,
            oracle_start=oracle_start,
            oracle_end=oracle_end,
            ability_kind=ability_kind,
            text_role=text_role,
            confidence=confidence,
            source="regex",
        )
        if success:
            applied.append(tag_name)

    # Deduplicate (same tag may match multiple patterns)
    return list(dict.fromkeys(applied))


ARCHETYPE_RULES: list[tuple[frozenset, str, float]] = [

    # ── Aristocrats ──────────────────────────────────────────────────────────
    # Sacrifice-based strategies that profit from creature deaths.
    # High-confidence rules require the specific death-payoff combination.
    (frozenset({"Death_Trigger", "Life_Drain"}),                  "Aristocrats", 0.90),
    (frozenset({"Death_Trigger", "Life_Gain"}),                   "Aristocrats", 0.85),
    (frozenset({"Death_Trigger", "Draw_Effect"}),                 "Aristocrats", 0.80),
    (frozenset({"Death_Trigger", "Mana_Production"}),             "Aristocrats", 0.80),
    (frozenset({"Sacrifice_Outlet", "Death_Trigger"}),            "Aristocrats", 0.90),
    (frozenset({"Forced_Sacrifice", "Death_Trigger"}),            "Aristocrats", 0.85),
    (frozenset({"Token_Generation", "Death_Trigger"}),            "Aristocrats", 0.80),
    (frozenset({"Repeatable_Token_Generation", "Death_Trigger"}), "Aristocrats", 0.85),
    (frozenset({"Return_Self_From_Graveyard"}),                   "Aristocrats", 0.80),
    (frozenset({"Undying_Persist"}),                              "Aristocrats", 0.75),
    (frozenset({"Scales_With_Deaths"}),                           "Aristocrats", 0.75),
    (frozenset({"Sacrifice_Outlet"}),                             "Aristocrats", 0.65),

    # ── Sacrifice ────────────────────────────────────────────────────────────
    # Strategies centered on sacrificing permanents for value.
    # Broader than Aristocrats — no requirement for death payoffs.
    (frozenset({"Sacrifice_Outlet"}),                             "Sacrifice", 0.80),
    (frozenset({"Forced_Sacrifice"}),                             "Sacrifice", 0.75),
    (frozenset({"Sacrifice_Outlet", "Token_Generation"}),         "Sacrifice", 0.85),
    (frozenset({"Sacrifice_Outlet", "Mana_Production"}),          "Sacrifice", 0.80),

    # ── Reanimator ───────────────────────────────────────────────────────────
    # Strategies that reanimate large creatures from the graveyard.
    (frozenset({"Reanimation"}),                                  "Reanimator", 0.90),
    (frozenset({"Mass_Reanimate"}),                               "Reanimator", 0.95),
    (frozenset({"Self_Mill"}),                                    "Reanimator", 0.65),
    (frozenset({"Looting_Effect"}),                               "Reanimator", 0.60),

    # ── Graveyard ────────────────────────────────────────────────────────────
    # Any strategy that uses the graveyard as a resource.
    # Broader than Reanimator — includes self-mill, recursion, and GY interaction.
    (frozenset({"Reanimation"}),                                  "Graveyard", 0.85),
    (frozenset({"Mass_Reanimate"}),                               "Graveyard", 0.90),
    (frozenset({"Self_Mill"}),                                    "Graveyard", 0.80),
    (frozenset({"Return_Self_From_Graveyard"}),                   "Graveyard", 0.80),
    (frozenset({"Recursion_To_Hand"}),                            "Graveyard", 0.75),
    (frozenset({"Looting_Effect"}),                               "Graveyard", 0.70),
    (frozenset({"Scales_With_Deaths"}),                           "Graveyard", 0.70),
    (frozenset({"Graveyard_Hate"}),                               "Graveyard", 0.65),

    # ── Big_Mana ─────────────────────────────────────────────────────────────
    # Strategies that generate large mana pools for X-spells or massive threats.
    (frozenset({"Mana_Multiplier"}),                              "Big_Mana", 0.90),
    (frozenset({"X_Spell_Effect", "Life_Drain"}),                 "Big_Mana", 0.90),
    (frozenset({"X_Spell_Effect"}),                               "Big_Mana", 0.80),
    (frozenset({"Scales_With_Deaths", "Mana_Production"}),        "Big_Mana", 0.80),
    (frozenset({"Permanent_Scaling", "Mana_Production"}),         "Big_Mana", 0.75),
    (frozenset({"Cost_Reduction"}),                               "Big_Mana", 0.70),

    # ── Devotion ─────────────────────────────────────────────────────────────
    # Strategies that benefit from many colored mana symbols among permanents.
    (frozenset({"Devotion_Effect"}),                              "Devotion", 0.95),

    # ── Tokens ───────────────────────────────────────────────────────────────
    # Strategies that create and exploit many tokens.
    (frozenset({"Repeatable_Token_Generation"}),                  "Tokens", 0.90),
    (frozenset({"Token_Generation", "Death_Trigger"}),            "Tokens", 0.80),
    (frozenset({"Token_Generation", "Sacrifice_Outlet"}),         "Tokens", 0.75),

    # ── Lifegain ─────────────────────────────────────────────────────────────
    # Strategies built around gaining and leveraging life totals.
    # Only the genuinely life-gain-centric combinations — Extort is excluded
    # (incidental drain, not a lifegain strategy card).
    (frozenset({"Life_Drain", "Devotion_Effect"}),                "Lifegain", 0.80),
    (frozenset({"Life_Drain", "X_Spell_Effect"}),                 "Lifegain", 0.75),
    (frozenset({"Lifelink"}),                                     "Lifegain", 0.65),

    # ── Control ──────────────────────────────────────────────────────────────
    # Reactive strategies that answer threats and maintain board control.
    (frozenset({"Counter_Spell"}),                                "Control", 0.90),
    (frozenset({"Targeted_Removal"}),                             "Control", 0.75),
    (frozenset({"Board_Wipe"}),                                   "Control", 0.70),
    (frozenset({"Graveyard_Hate"}),                               "Control", 0.75),

    # ── Discard ──────────────────────────────────────────────────────────────
    # Strategies built around making opponents discard.
    # Only fires on compound signals — Discard_Effect alone is too broad.
    (frozenset({"Discard_Effect", "Upkeep_Trigger"}),             "Discard", 0.75),
    (frozenset({"Discard_Effect", "Forced_Sacrifice"}),           "Discard", 0.70),

    # ── Stax ─────────────────────────────────────────────────────────────────
    # Resource denial strategies that lock opponents out over time.
    (frozenset({"Forced_Sacrifice", "Upkeep_Trigger"}),           "Stax", 0.75),

    # ── Voltron ──────────────────────────────────────────────────────────────
    # Commander damage strategies that buff a single creature.
    # Low confidence — many equipment and buffs serve multiple strategies.
    (frozenset({"Permanent_Scaling", "Evasion"}),                 "Voltron", 0.70),
    (frozenset({"Protection_Effect"}),                            "Voltron", 0.55),
]


def tag_functional_from_rules(card_name: str, db) -> list[str]:
    """
    Derive functional tags (Layer 3) from a card's mechanical tags using FUNCTIONAL_RULES.

    Requires the card to already have mechanical tags stored in the database.
    Safe to call multiple times — uses upsert, so the best confidence always wins.

    Args:
        card_name: exact card name (must have mechanical tags in the database)
        db:        open Database connection

    Returns:
        List of functional tag names that were applied or updated.

    Usage:
        card = db.card_by_name("Blood Artist")
        tag_mechanical(card, db)           # Layer 2 first
        tag_functional_from_rules("Blood Artist", db)  # → ["Payoff", "Threat", ...]
    """
    mech_tags = {t["name"] for t in db.get_card_tags(card_name, layer="mechanical")}

    if not mech_tags:
        return []

    # Collect highest confidence for each functional tag that fires.
    # Multiple rules can fire for the same tag — keep the best one.
    best_confidence: dict[str, float] = {}
    for required, functional_tag, confidence in FUNCTIONAL_RULES:
        if required.issubset(mech_tags):
            if confidence > best_confidence.get(functional_tag, 0.0):
                best_confidence[functional_tag] = confidence

    # Apply all derived functional tags.
    # Use tag_card_if_higher so that an existing manual tag (confidence=1.0)
    # is never downgraded by a rule-engine inference (confidence < 1.0).
    applied = []
    for functional_tag, confidence in best_confidence.items():
        success = db.tag_card_if_higher(card_name, functional_tag, confidence, source="rule_engine")
        if success:
            applied.append(functional_tag)

    return applied


def tag_archetype_from_rules(card_name: str, db) -> list[str]:
    """
    Derive archetype tags (Layer 4) from a card's mechanical tags using ARCHETYPE_RULES.

    Rules use mechanical tags only (Layer 2) as input — not functional tags.
    Mechanical tags encode the exact archetype-specific signals (Death_Trigger,
    Mana_Multiplier, etc.) without the abstraction noise of functional labels.

    Safe to call multiple times — uses tag_card_if_higher so existing manual
    tags (confidence=1.0) are never downgraded by a rule-engine inference.

    Args:
        card_name: exact card name (must have mechanical tags in the database)
        db:        open Database connection

    Returns:
        List of archetype tag names that were newly applied or updated.

    Usage:
        card = db.card_by_name("Blood Artist")
        tag_mechanical(card, db)                # Layer 2 first
        tag_functional_from_rules(card_name, db) # Layer 3 second (optional before Layer 4)
        tag_archetype_from_rules(card_name, db)  # → ["Aristocrats", "Sacrifice"]
    """
    mech_tags = {t["name"] for t in db.get_card_tags(card_name, layer="mechanical")}

    if not mech_tags:
        return []

    # Collect highest confidence for each archetype tag that fires.
    best_confidence: dict[str, float] = {}
    for required, archetype_tag, confidence in ARCHETYPE_RULES:
        if required.issubset(mech_tags):
            if confidence > best_confidence.get(archetype_tag, 0.0):
                best_confidence[archetype_tag] = confidence

    # Apply derived archetype tags, never downgrading existing manual tags.
    applied = []
    for archetype_tag, confidence in best_confidence.items():
        success = db.tag_card_if_higher(card_name, archetype_tag, confidence, source="rule_engine")
        if success:
            applied.append(archetype_tag)

    return applied


def tag_count_for_deck(card_names: list[str], db, layer: Optional[str] = None) -> dict[str, int]:
    """
    Count how many cards in a deck carry each tag.

    Args:
        card_names: list of card names (the deck's main deck)
        db:         open Database connection
        layer:      optional — filter to one layer

    Returns:
        {tag_name: count}, sorted by count desc

    Example:
        counts = tag_count_for_deck(deck_card_names, db, layer='functional')
        # → {'Mana_Acceleration': 8, 'Recursion': 6, 'Removal': 4, ...}
    """
    return db.tag_count_for_deck(card_names, layer)
