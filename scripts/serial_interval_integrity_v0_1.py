"""Pure serial-interval integrity controls.

No external I/O and no production mutation path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class SerialInterval:
    """Inclusive numeric serial interval."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if not isinstance(self.start, int) or isinstance(self.start, bool):
            raise TypeError("serial interval start must be a native integer")
        if not isinstance(self.end, int) or isinstance(self.end, bool):
            raise TypeError("serial interval end must be a native integer")
        if self.start < 0 or self.end < 0:
            raise ValueError("serial bounds must be non-negative")
        if self.start > self.end:
            raise ValueError("serial interval start must be <= end")

    @property
    def quantity(self) -> int:
        """Return inclusive interval cardinality."""

        return self.end - self.start + 1


def intervals_overlap(left: SerialInterval, right: SerialInterval) -> bool:
    """Return True when two inclusive intervals share at least one value."""

    return not (left.end < right.start or right.end < left.start)


def find_overlaps(
    intervals: Sequence[SerialInterval],
) -> tuple[tuple[int, int], ...]:
    """Return all overlapping input-index pairs in deterministic order."""

    overlaps: list[tuple[int, int]] = []
    for left_index in range(len(intervals)):
        for right_index in range(left_index + 1, len(intervals)):
            if intervals_overlap(intervals[left_index], intervals[right_index]):
                overlaps.append((left_index, right_index))
    return tuple(overlaps)


def serial_range_quantity_matches(
    interval: SerialInterval,
    declared_quantity: int,
) -> bool:
    """Return True only for an exact inclusive cardinality match."""

    if not isinstance(declared_quantity, int) or isinstance(
        declared_quantity, bool
    ):
        raise TypeError("declared quantity must be a native integer")
    if declared_quantity < 0:
        raise ValueError("declared quantity must be non-negative")
    return interval.quantity == declared_quantity
