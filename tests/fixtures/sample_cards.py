"""
sample_cards.py — Sample mono-black cards for testing.

These are real MTG cards used to test the scanner and tagging system.
Sourced from typical Sheoldred/mono-black reanimator strategies.
"""

from mtgdeck.models import Card

SAMPLE_CARDS = [
    # Sacrifice outlets & engines
    Card(
        name="Ashnod's Altar",
        mana_cost="{1}",
        cmc=1,
        type_line="Artifact",
        oracle_text="Sacrifice a creature: Add {C}{C}.",
    ),
    Card(
        name="Viscera Seer",
        mana_cost="{B}",
        cmc=1,
        type_line="Creature — Vampire",
        oracle_text="Sacrifice a creature: Viscera Seer gets +2/+1 until end of turn.",
    ),
    Card(
        name="Cartel Aristocrat",
        mana_cost="{W}{B}",
        cmc=2,
        type_line="Creature — Human Advisor",
        oracle_text="Sacrifice a creature: Cartel Aristocrat gains protection from any color until end of turn.",
    ),

    # Death triggers & payoffs
    Card(
        name="Blood Artist",
        mana_cost="{B}",
        cmc=1,
        type_line="Creature — Vampire",
        oracle_text="Whenever Blood Artist or another creature dies, target opponent loses 1 life and you gain 1 life.",
    ),
    Card(
        name="Zulaport Cutthroat",
        mana_cost="{B}",
        cmc=1,
        type_line="Creature — Vampire Ally",
        oracle_text="Whenever Zulaport Cutthroat or another creature you control dies, each opponent loses 1 life and you gain 1 life.",
    ),
    Card(
        name="Grave Pact",
        mana_cost="{1}{B}{B}",
        cmc=3,
        type_line="Enchantment",
        oracle_text="Whenever a creature you control dies, each opponent sacrifices a creature.",
    ),
    Card(
        name="Harvester of Souls",
        mana_cost="{2}{B}{B}",
        cmc=4,
        type_line="Creature — Horror",
        oracle_text="Whenever another creature you control dies, you may draw a card.",
    ),

    # Reanimation
    Card(
        name="Animate Dead",
        mana_cost="{1}{B}",
        cmc=2,
        type_line="Enchantment — Aura",
        oracle_text="Enchant creature card in a graveyard. When Animate Dead enters the battlefield, if it's on the battlefield, it becomes a creature with base power and toughness 2/2. If Animate Dead is in a graveyard, return target creature card from your graveyard to the battlefield tapped under your control. When Animate Dead leaves the battlefield, that creature's controller sacrifices it.",
    ),
    Card(
        name="Living Death",
        mana_cost="{2}{B}{B}",
        cmc=4,
        type_line="Sorcery",
        oracle_text="Each player exiles all creature cards from their graveyard, then sacrifices all creatures they control, then puts all cards they exiled this way onto the battlefield.",
    ),
    Card(
        name="Return of the Fallen",
        mana_cost="{2}{B}",
        cmc=3,
        type_line="Instant",
        oracle_text="Return target creature card from your graveyard to your hand.",
    ),

    # Recursion & self-return
    Card(
        name="Bloodghast",
        mana_cost="{B}{B}",
        cmc=2,
        type_line="Creature — Vampire",
        oracle_text="Bloodghast has haste as long as an opponent has more life than you. Whenever a land enters the battlefield under your control, you may return Bloodghast from your graveyard to the battlefield.",
    ),
    Card(
        name="Reassembling Skeleton",
        mana_cost="{1}{B}",
        cmc=2,
        type_line="Creature — Skeleton",
        oracle_text="{1}{B}: Return Reassembling Skeleton from your graveyard to the battlefield tapped.",
    ),
    Card(
        name="Geralf's Messenger",
        mana_cost="{1}{B}{B}",
        cmc=3,
        type_line="Creature — Zombie",
        oracle_text="Undying (When this creature dies, if it had no +1/+1 counters on it, return it to the battlefield under its owner's control with a +1/+1 counter on it.)",
    ),

    # Token generation
    Card(
        name="Ghoulcaller Gisa",
        mana_cost="{2}{B}{B}",
        cmc=4,
        type_line="Creature — Zombie Shaman",
        oracle_text="{B}, {T}, Sacrifice another creature: Create X 2/2 black Zombie creature tokens, where X is the sacrificed creature's power.",
    ),
    Card(
        name="Bitterblossom",
        mana_cost="{1}{B}",
        cmc=2,
        type_line="Enchantment",
        oracle_text="At the beginning of your end step, you create a 1/1 black Faerie creature token with flying.",
    ),
    Card(
        name="Cemetery Reaper",
        mana_cost="{1}{B}",
        cmc=2,
        type_line="Creature — Zombie",
        oracle_text="{T}: Exile target creature card from a graveyard. Create a 2/2 black Zombie token.",
    ),

    # Mana & ramp
    Card(
        name="Sol Ring",
        mana_cost="{1}",
        cmc=1,
        type_line="Artifact",
        oracle_text="{T}: Add {C}{C}.",
    ),
    Card(
        name="Dark Ritual",
        mana_cost="{B}",
        cmc=1,
        type_line="Instant",
        oracle_text="Add {B}{B}{B}.",
    ),
    Card(
        name="Cabal Coffers",
        mana_cost="",
        cmc=0,
        type_line="Land",
        oracle_text="{T}: Add {B}. {T}, Sacrifice a creature: Add {B}{B}.",
    ),

    # Card draw
    Card(
        name="Phyrexian Arena",
        mana_cost="{1}{B}",
        cmc=2,
        type_line="Enchantment",
        oracle_text="At the beginning of your upkeep, you draw a card and you lose 1 life.",
    ),
    Card(
        name="Necropotence",
        mana_cost="{B}{B}{B}",
        cmc=3,
        type_line="Enchantment",
        oracle_text="Skip your draw step. Whenever you discard a card, exile that card from your graveyard. Pay life equal to that card's mana value: Return the last card exiled this way to your hand.",
    ),

    # Removal & interaction
    Card(
        name="Victim of Night",
        mana_cost="{1}{B}",
        cmc=2,
        type_line="Instant",
        oracle_text="Destroy target non-black creature.",
    ),
    Card(
        name="Plague Crafter",
        mana_cost="{2}{B}",
        cmc=3,
        type_line="Creature — Human Shaman",
        oracle_text="When Plague Crafter enters the battlefield, each other player sacrifices a creature.",
    ),

    # Tutors
    Card(
        name="Demonic Tutor",
        mana_cost="{1}{B}",
        cmc=2,
        type_line="Instant",
        oracle_text="Search your library for a card, put that card in your hand, then shuffle.",
    ),
    Card(
        name="Entomb",
        mana_cost="{B}",
        cmc=1,
        type_line="Instant",
        oracle_text="Search your library for a card, put that card into your graveyard, then shuffle.",
    ),

    # Complex/combo cards
    Card(
        name="Bolas's Citadel",
        mana_cost="{3}{B}{B}",
        cmc=5,
        type_line="Artifact",
        oracle_text="You may look at the top card of your library at any time.\nYou may play lands and cast spells from the top of your library. If you cast a spell this way, pay life equal to its mana value rather than pay its mana cost.\n{T}, Sacrifice ten nonland permanents: Each opponent loses 10 life.",
    ),
    Card(
        name="Yawgmoth's Will",
        mana_cost="{2}{B}",
        cmc=3,
        type_line="Instant",
        oracle_text="For each card in your graveyard, you may play that card this turn without paying its mana cost.",
    ),
    Card(
        name="Sheoldred, Whispering One",
        mana_cost="{2}{B}{B}",
        cmc=4,
        type_line="Legendary Creature — Praetor",
        oracle_text="At the beginning of your upkeep, return target creature card from your graveyard to the battlefield. At the beginning of each opponent's upkeep, that player sacrifices a creature.",
    ),
]


def load_sample_cards(db):
    """Load sample cards into database. Returns count of cards inserted."""
    count = 0
    for card in SAMPLE_CARDS:
        db.insert_card(card)
        count += 1
    return count
