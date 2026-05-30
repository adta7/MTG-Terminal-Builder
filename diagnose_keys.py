#!/usr/bin/env python3
"""Diagnostic test to understand escape sequence timing on this system."""

import sys
import tty
import termios
import select
import time
import fcntl
import os

def test_blocking_mode():
    """Test reading escape sequences in pure blocking mode."""
    print("=" * 70)
    print("TEST 1: Pure blocking mode (no select, no non-blocking)")
    print("=" * 70)
    print("Press down arrow, up arrow, and ESC. Watch the byte sequence.")
    print()

    for attempt in range(5):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            print(f"Attempt {attempt + 1}: ", end="", flush=True)

            start = time.time()
            ch1 = sys.stdin.buffer.read(1)
            t1 = time.time() - start

            print(f"Byte1={ch1!r} (t={t1*1000:.1f}ms)", end="", flush=True)

            if ch1 == b'\x1b':
                start = time.time()
                ch2 = sys.stdin.buffer.read(1)
                t2 = time.time() - start
                print(f" → Byte2={ch2!r} (t={t2*1000:.1f}ms)", end="", flush=True)

                if ch2 == b'[':
                    start = time.time()
                    ch3 = sys.stdin.buffer.read(1)
                    t3 = time.time() - start
                    print(f" → Byte3={ch3!r} (t={t3*1000:.1f}ms)", end="", flush=True)

                    direction = {b'A': 'UP', b'B': 'DOWN', b'C': 'RIGHT', b'D': 'LEFT'}.get(ch3, 'UNKNOWN')
                    print(f" = {direction}")
                else:
                    print()
            else:
                print()

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    print()


def test_select_mode():
    """Test reading with select() timeout."""
    print("=" * 70)
    print("TEST 2: Using select() with different timeouts")
    print("=" * 70)
    print("Press down arrow, up arrow, and ESC.")
    print()

    timeouts = [0.01, 0.05, 0.1, 0.2]

    for timeout in timeouts:
        print(f"\nTimeout: {timeout*1000:.0f}ms")
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            print(f"  Press a key: ", end="", flush=True)

            start = time.time()
            ch1 = sys.stdin.buffer.read(1)
            t1 = time.time() - start

            print(f"Byte1={ch1!r} (t={t1*1000:.1f}ms)", end="", flush=True)

            if ch1 == b'\x1b':
                has_next = select.select([sys.stdin], [], [], timeout)[0]
                elapsed = (time.time() - start - t1) * 1000

                if has_next:
                    start2 = time.time()
                    ch2 = sys.stdin.buffer.read(1)
                    t2 = time.time() - start2
                    print(f" → Byte2={ch2!r} (select elapsed={elapsed:.1f}ms, read={t2*1000:.1f}ms)", end="", flush=True)

                    if ch2 == b'[':
                        has_next = select.select([sys.stdin], [], [], timeout)[0]
                        elapsed = (time.time() - start - t1 - t2) * 1000

                        if has_next:
                            start3 = time.time()
                            ch3 = sys.stdin.buffer.read(1)
                            t3 = time.time() - start3
                            print(f" → Byte3={ch3!r} (select elapsed={elapsed:.1f}ms, read={t3*1000:.1f}ms)")
                            direction = {b'A': 'UP', b'B': 'DOWN', b'C': 'RIGHT', b'D': 'LEFT'}.get(ch3, 'UNKNOWN')
                            print(f"    RESULT: {direction}")
                        else:
                            print(f" → select timeout (elapsed={elapsed:.1f}ms)")
                else:
                    print(f" → select timeout immediately")
            else:
                print()

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def test_nonblocking_mode():
    """Test with non-blocking mode and retry loop."""
    print("\n" + "=" * 70)
    print("TEST 3: Non-blocking mode with retry loop")
    print("=" * 70)
    print("Press down arrow, up arrow, and ESC.")
    print()

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)

    try:
        tty.setraw(fd)
        fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)

        for attempt in range(5):
            print(f"Attempt {attempt + 1}: ", end="", flush=True)

            # Block until first byte arrives
            select.select([sys.stdin], [], [], 10)
            start = time.time()
            ch1 = sys.stdin.buffer.read(1)
            t1 = (time.time() - start) * 1000

            if not ch1:
                print("(no input)")
                continue

            print(f"Byte1={ch1!r} (t={t1:.1f}ms)", end="", flush=True)

            if ch1 == b'\x1b':
                ch2 = None
                for retry in range(200):  # Try 200 times
                    time.sleep(0.001)  # 1ms between retries
                    ch2 = sys.stdin.buffer.read(1)
                    if ch2:
                        print(f" → Byte2={ch2!r} (retry #{retry})", end="", flush=True)
                        break

                if ch2 == b'[':
                    ch3 = None
                    for retry in range(200):
                        time.sleep(0.001)
                        ch3 = sys.stdin.buffer.read(1)
                        if ch3:
                            print(f" → Byte3={ch3!r} (retry #{retry})", end="", flush=True)
                            break

                    if ch3:
                        direction = {b'A': 'UP', b'B': 'DOWN', b'C': 'RIGHT', b'D': 'LEFT'}.get(ch3, 'UNKNOWN')
                        print(f" = {direction}")
                    else:
                        print(" (timeout waiting for byte3)")
                else:
                    print(f" (expected '[', got something else)")
            else:
                print()

    finally:
        fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


if __name__ == "__main__":
    try:
        test_blocking_mode()
        test_select_mode()
        test_nonblocking_mode()
        print("\n" + "=" * 70)
        print("Diagnostics complete.")
        print("=" * 70)
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
