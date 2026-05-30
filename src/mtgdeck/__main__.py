"""
__main__.py — Entry point for MTG deckbuilding companion.

Run with: python -m mtgdeck
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import mtgdeck
sys.path.insert(0, str(Path(__file__).parent.parent))

from mtgdeck.database import Database
from mtgdeck.scryfall import (
    find_scryfall_json,
    download_scryfall_bulk,
    index_cards_into_db,
)
from mtgdeck.analyzer import analyze_deck
from mtgdeck.profiles import (
    count_roles_in_deck,
    compare_to_profile,
    find_profile,
    load_profile,
    CATEGORY_DISPLAY_NAMES,
)
from mtgdeck.recommender import suggest, cuts
from rich.console import Console

console = Console()


def get_db_path() -> str:
    """Get path to the cards database."""
    proj_root = Path(__file__).parent.parent.parent
    return str(proj_root / "data" / "cards.sqlite")


def _parse_flag(argv: list[str], flag: str) -> str | None:
    """Return the value after --flag, or None if flag absent or missing value."""
    if flag in argv:
        idx = argv.index(flag)
        if idx + 1 < len(argv):
            return argv[idx + 1]
    return None


def main():
    """Main entry point."""
    # Check for 'setup' command
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup()
        return

    # Check if database exists
    db_path = get_db_path()
    if not Path(db_path).exists():
        print("\n  Database not found. Run:")
        print(f"    python -m mtgdeck setup\n")
        print("  to initialize the database.\n")
        sys.exit(1)

    args = sys.argv[1:]
    cmd  = args[0] if args else None

    # ── analyze ──────────────────────────────────────────────────────────────
    if cmd == "analyze":
        if len(args) < 2:
            print("\n  Usage: python -m mtgdeck analyze <deck_name> [--profile <name>]\n")
            sys.exit(1)
        run_analyzer(db_path, args[1], profile_name=_parse_flag(sys.argv, "--profile"))
        return

    # ── suggest ──────────────────────────────────────────────────────────────
    if cmd == "suggest":
        if len(args) < 2:
            print("\n  Usage: python -m mtgdeck suggest <deck_name> --role <role> [--profile <name>] [--top <n>]\n")
            sys.exit(1)
        role = _parse_flag(sys.argv, "--role")
        if not role:
            print("\n  --role is required for suggest.\n")
            print("  Functional roles: ramp, draw, removal, board_wipes, reanimation,")
            print("                    sac_outlets, protection, graveyard_fill, wincons")
            print("  Identity roles:   pressure_pieces, conversion_cards, engine_core,")
            print("                    recursive_fuel, apex_threats, identity_cards, mana_payoffs\n")
            sys.exit(1)
        top_n = 10
        raw_top = _parse_flag(sys.argv, "--top")
        if raw_top:
            try:
                top_n = int(raw_top)
            except ValueError:
                pass
        run_suggest(db_path, args[1], role=role,
                    profile_name=_parse_flag(sys.argv, "--profile"), top_n=top_n)
        return

    # ── cuts ─────────────────────────────────────────────────────────────────
    if cmd == "cuts":
        if len(args) < 2:
            print("\n  Usage: python -m mtgdeck cuts <deck_name> [--count <n>] [--profile <name>] [--include-lands]\n")
            sys.exit(1)
        count = 5
        raw_count = _parse_flag(sys.argv, "--count")
        if raw_count:
            try:
                count = int(raw_count)
            except ValueError:
                pass
        run_cuts(db_path, args[1], count=count,
                 profile_name=_parse_flag(sys.argv, "--profile"),
                 include_lands="--include-lands" in sys.argv)
        return

    # ── inspect-card ─────────────────────────────────────────────────────────
    if cmd == "inspect-card":
        if len(args) < 2:
            print("\n  Usage: python -m mtgdeck inspect-card \"<card name>\"\n")
            sys.exit(1)
        run_inspect_card(db_path, " ".join(args[1:]))
        return

    # ── role-members ─────────────────────────────────────────────────────────
    if cmd == "role-members":
        if len(args) < 2:
            print("\n  Usage: python -m mtgdeck role-members <role> [--deck <deck_name>]\n")
            sys.exit(1)
        run_role_members(db_path, args[1], deck_name=_parse_flag(sys.argv, "--deck"))
        return

    # ── explain-cut ──────────────────────────────────────────────────────────
    if cmd == "explain-cut":
        if len(args) < 3:
            print("\n  Usage: python -m mtgdeck explain-cut <deck_name> \"<card name>\" [--profile <name>]\n")
            sys.exit(1)
        run_explain_cut(db_path, args[1], " ".join(args[2:]).split("--")[0].strip(),
                        profile_name=_parse_flag(sys.argv, "--profile"))
        return

    # ── retag-deck ───────────────────────────────────────────────────────────
    if cmd == "retag-deck":
        if len(args) < 2:
            print("\n  Usage: python -m mtgdeck retag-deck <deck_name>\n")
            sys.exit(1)
        run_retag_deck(db_path, args[1])
        return

    # ── tag-card ─────────────────────────────────────────────────────────────
    if cmd == "tag-card":
        if len(args) < 3:
            print("\n  Usage: python -m mtgdeck tag-card \"<card name>\" <tag_name> [--confidence 0.9] [--note \"reason\"]\n")
            print("  Layers are inferred from the tag name (mechanical/functional/archetype/emotional).")
            print("  Source is always 'manual'. Manual tags are never overwritten by retag-deck.\n")
            sys.exit(1)
        # card name may be multiple words before the tag
        # Convention: tag-card "Card Name" TagName
        card_name_arg = args[1]
        tag_name_arg  = args[2]
        raw_conf = _parse_flag(sys.argv, "--confidence")
        note = _parse_flag(sys.argv, "--note") or ""
        confidence = 1.0
        if raw_conf:
            try:
                confidence = float(raw_conf)
            except ValueError:
                pass
        run_tag_card(db_path, card_name_arg, tag_name_arg, confidence, note)
        return

    # Load the old mtg.py for now (until we fully refactor the UI)
    print("  Loading application...\n")
    import mtg
    mtg.main()


def _load_deck(db_path: str, deck_name: str):
    """
    Locate and load a deck by name from the decks/ folder.

    Returns (deck, deck_file_path) or prints an error and exits.
    """
    import json
    import glob
    from mtgdeck.models import Deck, DeckCard

    proj_root = Path(db_path).parent.parent
    decks_dir = proj_root / "decks"
    deck_files = glob.glob(str(decks_dir / "*.json"))

    for f in deck_files:
        with open(f) as fh:
            data = json.load(fh)
        if data.get("name", "").lower() == deck_name.lower():
            cards = [DeckCard(name=c["name"], count=c["count"]) for c in data.get("cards", [])]
            sideboard = [DeckCard(name=c["name"], count=c["count"]) for c in data.get("sideboard", [])]
            deck = Deck(
                name=data["name"],
                cards=cards,
                sideboard=sideboard,
                commander=data.get("commander"),
                created=data.get("created", ""),
                edited=data.get("edited", ""),
            )
            return deck, f

    console.print(f"\n  ✗ Deck '{deck_name}' not found\n")
    sys.exit(1)


def _load_profile(db_path: str, profile_name: str):
    """Load a profile by name. Returns None if not found (with warning printed)."""
    proj_root = Path(db_path).parent.parent
    profiles_dir = proj_root / "data" / "profiles"
    try:
        profile_path = find_profile(profile_name, profiles_dir)
        return load_profile(profile_path)
    except FileNotFoundError as e:
        console.print(f"\n  [yellow]⚠ {e}[/yellow]\n")
        return None


def setup():
    """Initialize the database by downloading and indexing Scryfall data."""
    print("\n  MTG Deckbuilding Companion — Setup\n")
    print("  This will build a database from Scryfall card data.")
    print("  It's a one-time operation (~1-2 minutes).\n")

    try:
        # Find or download Scryfall JSON
        proj_root = Path(__file__).parent.parent.parent
        json_dir = proj_root

        try:
            json_path = find_scryfall_json(str(json_dir))
            print(f"  Found Scryfall JSON: {json_path}\n")
        except FileNotFoundError:
            print("  No local Scryfall JSON found.\n")
            print("  Download from: https://scryfall.com/docs/api/bulk-data")
            print("  (Look for 'Default Cards' and download the .json file)\n")
            print("  Then place it in this directory and run:")
            print("    python -m mtgdeck setup\n")
            sys.exit(1)

        # Initialize database and index cards
        db_path = get_db_path()
        db = Database(db_path)
        db.init_db()
        db.connect()

        count = index_cards_into_db(json_path, db)
        db.close()

        print(f"\n  ✓ Setup complete! Database ready at: {db_path}\n")
        print(f"  Run: python -m mtgdeck\n")

    except Exception as e:
        print(f"\n  ✗ Setup failed: {e}\n")
        sys.exit(1)


def run_analyzer(db_path: str, deck_name: str, profile_name: str | None = None):
    """Phase 1: Analyze a deck."""
    deck, _ = _load_deck(db_path, deck_name)
    db = Database(db_path)
    db.connect()

    analysis = analyze_deck(deck, db)

    # Print results
    console.print()
    console.print(f"[bold cyan]{analysis.deck_name}[/bold cyan]")
    if deck.commander:
        console.print(f"[dim]Commander: {deck.commander}[/dim]")

    console.print()
    console.print(f"Cards: {analysis.total_cards}/100")
    console.print(f"Lands: {analysis.land_count} | Spell Permanents: {analysis.spell_permanent_count} | Spell NonPermanents: {analysis.spell_nonpermanent_count}")
    console.print(f"Avg Mana Value: {analysis.avg_mana_value:.2f}")
    console.print(f"Color Identity: {', '.join(analysis.color_identity) or 'None'}")

    # Mana curve
    console.print()
    console.print("[bold]Mana Curve:[/bold]")
    for cmc in range(8):
        count = analysis.mana_curve.get(cmc, 0)
        bar = "█" * min(count, 30)
        console.print(f"  {cmc}: {count:2d} {bar}")

    # Type breakdown
    if analysis.type_counts:
        console.print()
        console.print("[bold]Type Breakdown:[/bold]")
        for type_name in sorted(analysis.type_counts.keys()):
            count = analysis.type_counts[type_name]
            console.print(f"  {type_name}: {count}")

    # Warnings
    if analysis.warnings:
        console.print()
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in analysis.warnings:
            console.print(f"  ⚠ {warning}")

    # Phase 3: Profile comparison (only when --profile is given)
    if profile_name:
        _print_profile_comparison(deck, db, analysis, profile_name, db_path)

    console.print()
    db.close()


def _print_profile_comparison(deck, db, analysis, profile_name: str, db_path: str):
    """Print the profile comparison section of the analyze output."""
    proj_root = Path(db_path).parent.parent
    profiles_dir = proj_root / "data" / "profiles"

    try:
        profile_path = find_profile(profile_name, profiles_dir)
        profile = load_profile(profile_path)
    except FileNotFoundError as e:
        console.print(f"\n  [yellow]⚠ {e}[/yellow]")
        return

    role_counts = count_roles_in_deck(deck, db)
    gaps = compare_to_profile(analysis, role_counts, profile)

    console.print()
    console.print(f"[bold]── Profile: {profile.name} {'─' * max(0, 40 - len(profile.name))}[/bold]")
    console.print()

    # Column widths for aligned output
    label_w = max(len(g.display_name) for g in gaps)

    summary_lines = []
    for gap in gaps:
        label = gap.display_name.ljust(label_w)
        # Format actual value: integers without decimal, floats with 1 decimal
        if gap.actual == int(gap.actual):
            actual_str = str(int(gap.actual))
        else:
            actual_str = f"{gap.actual:.2f}"
        actual_str = actual_str.rjust(5)

        if gap.status == "ok":
            icon = "[green]✓[/green]"
            msg  = f"[dim]{gap.message}[/dim]"
        elif gap.status == "low":
            icon = "[yellow]⚠[/yellow]"
            msg  = f"[yellow]{gap.message}[/yellow]"
        else:  # high
            icon = "[cyan]↑[/cyan]"
            msg  = f"[cyan]{gap.message}[/cyan]"

        console.print(f"  {label}  {actual_str}  {icon}  {msg}")
        if gap.status != "ok":
            summary_lines.append(f"{gap.display_name}: {gap.message}")

    if summary_lines:
        console.print()
        console.print("[bold yellow]Profile Gaps:[/bold yellow]")
        for line in summary_lines:
            console.print(f"  ⚠ {line}")


def run_suggest(
    db_path: str,
    deck_name: str,
    role: str,
    profile_name: str | None = None,
    top_n: int = 10,
):
    """Phase 4: Suggest cards to add for a given role."""
    deck, _ = _load_deck(db_path, deck_name)
    db = Database(db_path)
    db.connect()

    from mtgdeck.analyzer import analyze_deck
    analysis = analyze_deck(deck, db)

    # Load profile if given
    profile = None
    if profile_name:
        profile = _load_profile(db_path, profile_name)

    # Check if the requested role is already above profile target before suggesting
    if profile:
        from mtgdeck.profiles import count_roles_in_deck, compare_to_profile
        role_counts_check = count_roles_in_deck(deck, db)
        gap_check = compare_to_profile(analysis, role_counts_check, profile)
        for gap in gap_check:
            if gap.category == role and gap.status == "high":
                console.print()
                console.print(f"[bold cyan]{deck.name}[/bold cyan] — suggest [bold]{role}[/bold]")
                console.print(f"[dim]Profile: {profile.name}[/dim]")
                console.print()
                console.print(f"  [yellow]⚠  {role.capitalize()} is already above profile target.[/yellow]")
                console.print(f"  [dim]Target: {int(gap.target_min)}–{int(gap.target_max)}   Current: {int(gap.actual)}[/dim]")
                console.print()
                console.print("  [dim]No additions recommended. Address a category that is short instead.[/dim]")
                console.print()
                db.close()
                return

    # Run suggest — also gather diagnostic counts before filtering
    from mtgdeck.recommender import _find_candidates_for_role
    from mtgdeck.profiles import CATEGORY_FUNCTIONAL_TAGS, CATEGORY_MECHANICAL_TAGS, CATEGORY_EMOTIONAL_TAGS
    deck_names_lower = {c.name.lower() for c in deck.cards}
    all_role_tags = (
        CATEGORY_FUNCTIONAL_TAGS.get(role, frozenset())
        | CATEGORY_MECHANICAL_TAGS.get(role, frozenset())
        | CATEGORY_EMOTIONAL_TAGS.get(role, frozenset())
    )
    tagged_in_db   = sum(1 for tag in all_role_tags
                         for _ in db.query_cards_by_tag(tag))
    in_deck_count  = sum(1 for tag in all_role_tags
                         for entry in db.query_cards_by_tag(tag)
                         if entry["card_name"].lower() in deck_names_lower)

    results = suggest(deck, db, analysis, role=role, profile=profile, top_n=top_n)
    all_candidates = _find_candidates_for_role(role, db, deck)
    candidates_before_score_filter = len(all_candidates)

    db.close()

    console.print()
    console.print(f"[bold cyan]{deck.name}[/bold cyan] — suggest [bold]{role}[/bold]")
    if profile:
        console.print(f"[dim]Profile: {profile.name}[/dim]")
    console.print(f"[dim]Showing from tagged cards only. {len(results)} result(s).[/dim]")
    console.print()

    if not results:
        console.print(f"  [yellow]No candidates found for role '{role}'.[/yellow]")
        console.print()
        console.print(f"  [bold]Diagnostic breakdown:[/bold]")
        console.print(f"  [dim]Tagged '{role}' cards in database : {tagged_in_db}[/dim]")
        console.print(f"  [dim]Already in deck                  : {in_deck_count}[/dim]")
        console.print(f"  [dim]Candidates outside deck           : {candidates_before_score_filter}[/dim]")
        console.print(f"  [dim]Scored above 0 and returned       : {len(results)}[/dim]")
        console.print()
        if tagged_in_db == 0:
            console.print(f"  [yellow]No cards are tagged for '{role}' in the database.[/yellow]")
            console.print(f"  [dim]Run: python -m mtgdeck retag-deck {deck.name}[/dim]")
            console.print(f"  [dim]Or manually tag cards: python -m mtgdeck inspect-card \"<name>\"[/dim]")
        elif candidates_before_score_filter == 0:
            console.print(f"  [yellow]All tagged '{role}' cards are already in the deck.[/yellow]")
        else:
            console.print(f"  [yellow]{candidates_before_score_filter} candidate(s) found but all scored 0.[/yellow]")
            console.print(f"  [dim]This usually means the candidates have no tags matching '{role}'[/dim]")
            console.print(f"  [dim]in the current scoring context. Run 'inspect-card' to debug.[/dim]")
        console.print()
        return

    for i, suggestion in enumerate(results, 1):
        s = suggestion.score
        console.print(
            f"  [bold]{i}. {suggestion.card_name}[/bold]"
            f"  [dim]CMC {suggestion.mana_value}[/dim]"
            f"  [cyan]{s.total_score:.0f}/100[/cyan]"
        )
        for reason in s.reasons:
            console.print(f"     [dim]• {reason}[/dim]")
        console.print()


def run_cuts(
    db_path: str,
    deck_name: str,
    count: int = 5,
    profile_name: str | None = None,
    include_lands: bool = False,
):
    """Phase 4: Suggest cuts from the deck."""
    deck, _ = _load_deck(db_path, deck_name)
    db = Database(db_path)
    db.connect()

    from mtgdeck.analyzer import analyze_deck
    analysis = analyze_deck(deck, db)

    profile = None
    if profile_name:
        profile = _load_profile(db_path, profile_name)

    # Land analysis (always shown when --include-lands or profile is active)
    _print_land_analysis(analysis, profile)

    # Run cuts — basic lands are always skipped inside cuts()
    results = cuts(deck, db, analysis, profile=profile, count=count, include_lands=include_lands)

    db.close()

    console.print()
    console.print(f"[bold cyan]{deck.name}[/bold cyan] — cut candidates")
    if profile:
        console.print(f"[dim]Profile: {profile.name}[/dim]")
    land_note = " (non-basic lands included)" if include_lands else " (lands excluded)"
    console.print(f"[dim]Scoring spells and{land_note}. Commander and basic lands excluded.[/dim]")
    console.print()

    if not results:
        console.print("  [dim]No cut candidates found.[/dim]")
        console.print()
        return

    for i, candidate in enumerate(results, 1):
        console.print(
            f"  [bold]{i}. {candidate.card_name}[/bold]"
            f"  [dim]CMC {candidate.mana_value}[/dim]"
            f"  cut score: [yellow]{candidate.cut_score:.0f}[/yellow]"
            f"  keep score: [dim]{candidate.keep_score:.0f}[/dim]"
        )
        for reason in candidate.reasons:
            console.print(f"     [dim]• {reason}[/dim]")
        console.print()


def _print_land_analysis(analysis, profile):
    """Print a land count summary and recommendation when a profile is loaded."""
    if not profile:
        return
    land_target = profile.targets.get("lands")
    if not land_target:
        return
    t_min, t_max = float(land_target[0]), float(land_target[1])
    actual = analysis.land_count
    console.print()
    console.print("[bold]── Land Analysis ──────────────────────────────────────[/bold]")
    if actual < t_min:
        deficit = int(t_min - actual)
        console.print(
            f"  Lands: {actual}  [yellow]⚠ short by {deficit}[/yellow]"
            f"  [dim](target {int(t_min)}–{int(t_max)})[/dim]"
        )
        console.print(f"  [dim]Add {deficit} more land(s) before cutting spells.[/dim]")
    elif actual > t_max:
        excess = int(actual - t_max)
        console.print(
            f"  Lands: {actual}  [cyan]↑ over by {excess}[/cyan]"
            f"  [dim](target {int(t_min)}–{int(t_max)})[/dim]"
        )
        console.print(f"  [dim]Consider cutting {excess} land(s). Prefer non-basics with low utility.[/dim]")
        console.print(f"  [dim]Run with --include-lands to see non-basic land cut candidates.[/dim]")
    else:
        console.print(
            f"  Lands: {actual}  [green]✓[/green]"
            f"  [dim](target {int(t_min)}–{int(t_max)})[/dim]"
        )


def run_inspect_card(db_path: str, card_name: str):
    """
    Audit command: show all tags for a card and which profile roles they map to.

    Usage: python -m mtgdeck inspect-card "Phyrexian Arena"
    """
    from mtgdeck.profiles import (
        CATEGORY_FUNCTIONAL_TAGS,
        CATEGORY_MECHANICAL_TAGS,
        CATEGORY_EMOTIONAL_TAGS,
        CATEGORY_DISPLAY_NAMES,
    )

    db = Database(db_path)
    db.connect()

    card = db.card_by_name(card_name)
    all_tags = db.get_card_tags(card_name)
    db.close()

    console.print()
    if card:
        console.print(f"[bold cyan]{card.name}[/bold cyan]")
        console.print(f"[dim]{card.type_line}  •  CMC {card.cmc}[/dim]")
        if card.oracle_text:
            console.print(f"[dim]{card.oracle_text[:120]}{'…' if len(card.oracle_text) > 120 else ''}[/dim]")
    else:
        console.print(f"[bold yellow]{card_name}[/bold yellow] [dim](not found in card table)[/dim]")
    console.print()

    if not all_tags:
        console.print("  [yellow]No tags found.[/yellow]")
        console.print("  [dim]Run: python -m mtgdeck retag-deck <deck_name>[/dim]")
        console.print()
        return

    # Group tags by layer
    by_layer: dict[str, list[dict]] = {}
    for t in all_tags:
        by_layer.setdefault(t["layer"], []).append(t)
    layer_order = ["mechanical", "functional", "archetype", "emotional"]

    # Build reverse map: tag_name → profile categories it fills
    all_cat_maps = list(CATEGORY_FUNCTIONAL_TAGS.items()) + \
                   list(CATEGORY_MECHANICAL_TAGS.items()) + \
                   list(CATEGORY_EMOTIONAL_TAGS.items())
    tag_to_cats: dict[str, list[str]] = {}
    for cat, tag_set in all_cat_maps:
        for t in tag_set:
            tag_to_cats.setdefault(t, []).append(cat)

    console.print("[bold]Tags by layer:[/bold]")
    for layer in layer_order:
        tags_in_layer = by_layer.get(layer, [])
        if not tags_in_layer:
            continue
        console.print(f"\n  [bold]{layer.capitalize()}[/bold]")
        for t in tags_in_layer:
            cats = tag_to_cats.get(t["name"], [])
            cat_str = " → " + ", ".join(cats) if cats else ""
            src_str = f"[dim]{t['source']}[/dim]" if t["source"] != "manual" else "[green]manual[/green]"
            console.print(
                f"    [cyan]{t['name']}[/cyan]"
                f"  conf={t['confidence']:.2f}"
                f"  {src_str}"
                f"[dim]{cat_str}[/dim]"
            )

    # Show which profile categories this card fills
    tag_names = {t["name"] for t in all_tags}
    filled: list[str] = []
    not_filled: list[str] = []
    for cat, tag_set in all_cat_maps:
        if tag_names & tag_set:
            filled.append(cat)

    console.print()
    console.print("[bold]Profile categories filled:[/bold]")
    if filled:
        for cat in sorted(set(filled)):
            display = CATEGORY_DISPLAY_NAMES.get(cat, cat)
            console.print(f"  [green]✓[/green] {display} [dim]({cat})[/dim]")
    else:
        console.print("  [yellow]None — this card fills no profile categories.[/yellow]")
        console.print("  [dim]Consider adding an emotional tag (Pressure_Piece, Identity_Card, etc.)[/dim]")
    console.print()


def run_role_members(db_path: str, role: str, deck_name: str | None = None):
    """
    Audit command: list all cards tagged for a given profile role.

    Usage: python -m mtgdeck role-members draw [--deck <deck_name>]
    """
    from mtgdeck.profiles import (
        CATEGORY_FUNCTIONAL_TAGS,
        CATEGORY_MECHANICAL_TAGS,
        CATEGORY_EMOTIONAL_TAGS,
    )

    db = Database(db_path)
    db.connect()

    # Collect all tags that map to this role
    role_tags = (
        CATEGORY_FUNCTIONAL_TAGS.get(role, frozenset())
        | CATEGORY_MECHANICAL_TAGS.get(role, frozenset())
        | CATEGORY_EMOTIONAL_TAGS.get(role, frozenset())
    )

    if not role_tags:
        console.print(f"\n  [yellow]Unknown role '{role}'.[/yellow]")
        console.print(f"  [dim]Valid roles: ramp, draw, removal, board_wipes, reanimation,")
        console.print(f"  sac_outlets, protection, graveyard_fill, wincons,")
        console.print(f"  pressure_pieces, conversion_cards, engine_core,")
        console.print(f"  recursive_fuel, apex_threats, identity_cards, mana_payoffs[/dim]")
        db.close()
        return

    # Load deck card names if filtering
    deck_names: set[str] = set()
    if deck_name:
        deck, _ = _load_deck(db_path, deck_name)
        deck_names = {c.name.lower() for c in deck.cards}

    # Gather cards with any matching tag
    found: dict[str, dict] = {}  # card_name → best tag info
    for tag_name in role_tags:
        for entry in db.query_cards_by_tag(tag_name):
            name = entry["card_name"]
            if name not in found or entry["confidence"] > found[name]["confidence"]:
                found[name] = {"tag": tag_name, "confidence": entry["confidence"]}

    db.close()

    console.print()
    console.print(f"[bold]Cards mapped to role: [cyan]{role}[/cyan][/bold]")
    console.print(f"[dim]Tags searched: {', '.join(sorted(role_tags))}[/dim]")
    if deck_name:
        console.print(f"[dim]Deck filter: {deck_name}[/dim]")
    console.print()

    in_deck = {n: v for n, v in found.items() if n.lower() in deck_names}
    outside = {n: v for n, v in found.items() if n.lower() not in deck_names}

    if deck_name and in_deck:
        console.print(f"[bold]In deck ({len(in_deck)}):[/bold]")
        for name in sorted(in_deck):
            v = in_deck[name]
            console.print(f"  [green]•[/green] {name}  [dim]via {v['tag']} conf={v['confidence']:.2f}[/dim]")
        console.print()

    if deck_name:
        label = f"Outside deck ({len(outside)})"
    else:
        label = f"All tagged ({len(found)})"

    if outside or not deck_name:
        cards_to_show = sorted(outside if deck_name else found)
        console.print(f"[bold]{label}:[/bold]")
        for name in cards_to_show:
            v = (outside if deck_name else found)[name]
            console.print(f"  [dim]•[/dim] {name}  [dim]via {v['tag']} conf={v['confidence']:.2f}[/dim]")

    if not found:
        console.print(f"  [yellow]No cards found for role '{role}'.[/yellow]")
        console.print(f"  [dim]Try: python -m mtgdeck retag-deck <deck_name>[/dim]")
    console.print()


def run_explain_cut(
    db_path: str,
    deck_name: str,
    card_name: str,
    profile_name: str | None = None,
):
    """
    Audit command: show the exact keep/cut math for a specific card.

    Usage: python -m mtgdeck explain-cut sheoldred "Lashwrithe" [--profile mono_black_reanimator]
    """
    from mtgdeck.analyzer import analyze_deck
    from mtgdeck.recommender import _score_as_cut, build_context
    from mtgdeck.scoring import ScoringContext

    deck, _ = _load_deck(db_path, deck_name)
    db = Database(db_path)
    db.connect()

    analysis = analyze_deck(deck, db)
    profile = _load_profile(db_path, profile_name) if profile_name else None

    card = db.card_by_name(card_name)
    cmc = card.cmc if card else 0

    func_tags = db.get_card_tags(card_name, layer="functional")
    mech_tags = db.get_card_tags(card_name, layer="mechanical")
    arch_tags = db.get_card_tags(card_name, layer="archetype")
    id_tags   = db.get_card_tags(card_name, layer="emotional")
    all_tags  = db.get_card_tags(card_name)

    context = build_context(deck, db, analysis, profile, target_role=None)
    db.close()

    candidate = _score_as_cut(
        card_name, cmc, func_tags, mech_tags, arch_tags, id_tags, all_tags, context
    )

    console.print()
    console.print(f"[bold cyan]explain-cut[/bold cyan]: {card_name}")
    console.print(f"[dim]Deck: {deck.name}[/dim]")
    if profile:
        console.print(f"[dim]Profile: {profile.name}[/dim]")
    console.print()
    console.print(f"  keep score : [green]{candidate.keep_score:.1f}[/green]  (higher = safer to keep)")
    console.print(f"  cut score  : [yellow]{candidate.cut_score:.1f}[/yellow]  (higher = stronger cut suggestion)")
    console.print()
    console.print("[bold]Scoring breakdown:[/bold]")
    console.print(f"  [dim]Base score: 50.0[/dim]")
    for reason in candidate.reasons:
        console.print(f"  • {reason}")
    console.print()

    # Show profile gaps for context
    if profile and context.role_gaps:
        console.print("[bold]Active profile gaps (for reference):[/bold]")
        for cat, status in sorted(context.role_gaps.items()):
            icon = {"low": "[yellow]⚠[/yellow]", "ok": "[green]✓[/green]", "high": "[cyan]↑[/cyan]"}.get(status, "")
            console.print(f"  {icon} {cat}: {status}")
        console.print()


def run_retag_deck(db_path: str, deck_name: str):
    """
    Maintenance command: re-run tagging rules for all cards in a deck.

    Deletes stale auto-generated tags (regex, rule_engine) and re-runs the
    full tagging pipeline using current rules. Manual tags are preserved.

    This is needed after:
    - Adding new tag types to the TAGS list (e.g. Card_Draw, Efficient_Staple)
    - Removing a broken rule (e.g. Life_Payment → Mana_Acceleration)
    - Changing oracle text pattern matching (e.g. reminder text stripping)

    Usage: python -m mtgdeck retag-deck sheoldred
    """
    from mtgdeck.tags import seed_tags, tag_mechanical, tag_functional_from_rules, tag_archetype_from_rules

    deck, _ = _load_deck(db_path, deck_name)
    db = Database(db_path)
    db.connect()

    console.print()
    console.print(f"[bold cyan]Retagging deck:[/bold cyan] {deck.name}")
    console.print(f"[dim]{len(deck.cards)} cards to process[/dim]")
    console.print()

    # Step 1: Ensure all current tags exist in the tags table
    added = seed_tags(db)
    if added > 0:
        console.print(f"  [dim]Seeded {added} new tag type(s) into tags table[/dim]")

    # Step 2: Delete and re-run auto tags for each card
    changed: list[str] = []
    skipped: list[str] = []

    for card_entry in deck.cards:
        name = card_entry.name
        card = db.card_by_name(name)
        if not card:
            skipped.append(name)
            continue

        old_tags = {t["name"] for t in db.get_card_tags(name, layer="mechanical")} | \
                   {t["name"] for t in db.get_card_tags(name, layer="functional")} | \
                   {t["name"] for t in db.get_card_tags(name, layer="archetype")}

        deleted = db.delete_auto_tags(name)
        tag_mechanical(card, db)
        tag_functional_from_rules(name, db)
        tag_archetype_from_rules(name, db)

        new_tags = {t["name"] for t in db.get_card_tags(name, layer="mechanical")} | \
                   {t["name"] for t in db.get_card_tags(name, layer="functional")} | \
                   {t["name"] for t in db.get_card_tags(name, layer="archetype")}

        if old_tags != new_tags:
            added_tags   = new_tags - old_tags
            removed_tags = old_tags - new_tags
            changed.append(name)
            console.print(f"  [bold]{name}[/bold]")
            if removed_tags:
                console.print(f"    [red]− {', '.join(sorted(removed_tags))}[/red]")
            if added_tags:
                console.print(f"    [green]+ {', '.join(sorted(added_tags))}[/green]")

    db.close()

    console.print()
    if skipped:
        console.print(f"  [yellow]⚠ {len(skipped)} card(s) not in Scryfall DB:[/yellow] {', '.join(skipped[:5])}")
    console.print(f"  [green]✓[/green] {len(deck.cards) - len(skipped)} cards processed, {len(changed)} changed")
    console.print()


def run_tag_card(
    db_path: str,
    card_name: str,
    tag_name: str,
    confidence: float = 1.0,
    note: str = "",
):
    """
    Manually tag a card. Tags with source='manual' are never overwritten by retag-deck.

    Usage: python -m mtgdeck tag-card "Lashwrithe" Pressure_Piece
           python -m mtgdeck tag-card "Lashwrithe" Identity_Card --confidence 0.9 --note "symbolic mono-black card"
    """
    db = Database(db_path)
    db.connect()

    # Validate the card exists
    card = db.card_by_name(card_name)
    if not card:
        console.print(f"\n  [yellow]⚠ '{card_name}' not found in Scryfall data.[/yellow]")
        console.print(f"  [dim]Tag will still be written (card may be a token or proxy).[/dim]\n")

    # Validate the tag exists in the tags table
    tag_id = db.get_tag_id(tag_name)
    if tag_id is None:
        # Show available tags
        all_tags = db.all_tags()
        names = sorted(t["name"] for t in all_tags)
        console.print(f"\n  [red]✗ Unknown tag '{tag_name}'.[/red]")
        console.print(f"  [dim]Available tags ({len(names)}): {', '.join(names[:20])}{'…' if len(names) > 20 else ''}[/dim]\n")
        db.close()
        sys.exit(1)

    # Get tag layer for display
    tag_info = next((t for t in db.all_tags() if t["name"] == tag_name), None)
    layer = tag_info["layer"] if tag_info else "unknown"

    # Write as manual tag — INSERT OR REPLACE (always overwrites, manual beats rule_engine)
    success = db.tag_card(card_name, tag_name, confidence, source="manual", note=note)
    db.close()

    console.print()
    if success:
        console.print(f"  [green]✓[/green] Tagged: [bold]{card_name}[/bold] ← {tag_name} [{layer}] conf={confidence:.2f}")
        if note:
            console.print(f"  [dim]Note: {note}[/dim]")
        console.print(f"  [dim]Run 'inspect-card \"{card_name}\"' to see all tags.[/dim]")
    else:
        console.print(f"  [red]✗ Failed to tag '{card_name}'.[/red]")
    console.print()


if __name__ == "__main__":
    main()
