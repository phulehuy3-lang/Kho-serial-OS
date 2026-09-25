"""Synthetic non-production canary for V3 required-check enforcement.

This file must never be merged. It intentionally aliases a write-capable
pathlib method so Trusted Public Boundary V3 fails while the pre-V3 checks
remain otherwise satisfied.
"""

from pathlib import Path


writer = Path("synthetic-v3-canary.txt").write_text


def canary() -> None:
    writer("synthetic")
