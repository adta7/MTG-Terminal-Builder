#!/usr/bin/env python3
"""Test script to debug getch() key reading."""

from ui import getch

print("Testing getch() key reading")
print("Press keys to test (q to quit):")
print("- Arrow keys (should print UP/DOWN/LEFT/RIGHT)")
print("- ESC (should print ESC)")
print("- Regular keys (should print the character)")
print()

while True:
    try:
        key = getch()
        print(f"Got: {repr(key)}")
        if key == 'q':
            break
    except KeyboardInterrupt:
        print("\nInterrupted")
        break
