"""Synthetic non-production canary for Trusted Public Boundary V3 enforcement.

This file must never be merged. It exists only on the canary branch to prove
that V3 detects a simple alias of a write-capable pathlib method while V1/V2
remain otherwise satisfied.
"""

from pathlib import Path


writer = Path("synthetic-canary.txt").write_text


def canary() -> None:
    writer("synthetic")
