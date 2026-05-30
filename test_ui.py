#!/usr/bin/env python3
"""Quick demo of the new interactive menu."""

from ui import ask_choice_interactive, BreadcrumbPath

if __name__ == "__main__":
    print("Testing interactive menu...")
    print()

    # Test 1: Simple menu
    breadcrumb = BreadcrumbPath("MTG Pipeline", "Demo")
    options = ["View Deck", "Analyze Deck", "Add Cards", "Remove Cards"]

    result = ask_choice_interactive(
        "Choose an action",
        options,
        breadcrumb=breadcrumb,
        cancellable=True
    )

    if result is not None:
        print(f"\nYou selected: {options[result]} (index {result})")
    else:
        print("\nYou cancelled.")
