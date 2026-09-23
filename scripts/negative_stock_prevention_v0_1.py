"""Pure negative-stock prevention controls.

No external I/O and no production mutation path.
"""

from __future__ import annotations


def _validate_quantity(name: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be a native integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def remaining_stock(available: int, requested: int) -> int:
    """Return remaining stock after a proposed issue.

    Inputs are validated as native non-negative integers. A negative result is
    a blocking state; exact depletion to zero is valid.
    """

    available_value = _validate_quantity("available", available)
    requested_value = _validate_quantity("requested", requested)
    return available_value - requested_value


def issue_would_create_negative_stock(
    available: int,
    requested: int,
) -> bool:
    """Return True when a proposed issue would make stock negative."""

    return remaining_stock(available, requested) < 0
