"""Pure implementation of ALLOCATION_NEAREST_PRIOR_V1_0.

No external I/O. No production write path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True, slots=True)
class SourceLot:
    source_id: str
    source_date: date
    source_row: int
    serial_start: str


def _serial_key(serial_start: str) -> int:
    if not isinstance(serial_start, str) or not serial_start or not serial_start.isdigit():
        raise ValueError("serial_start must be non-empty numeric text")
    return int(serial_start)


def _validate_source(source: SourceLot) -> None:
    if not source.source_id.strip():
        raise ValueError("source_id must be non-empty")
    if not isinstance(source.source_row, int) or isinstance(source.source_row, bool) or source.source_row <= 0:
        raise ValueError("source_row must be a positive integer")
    _serial_key(source.serial_start)


def eligible_sources_nearest_prior(
    sources: Iterable[SourceLot],
    target_date: date,
) -> tuple[SourceLot, ...]:
    """Return eligible sources in canonical deterministic order.

    Order: SOURCE_DATE_DESC | SOURCE_ROW_ASC | SERIAL_START_ASC.
    Sources after target_date are excluded.
    """

    materialized = tuple(sources)
    for source in materialized:
        _validate_source(source)

    eligible = [source for source in materialized if source.source_date <= target_date]
    eligible.sort(
        key=lambda source: (
            -source.source_date.toordinal(),
            source.source_row,
            _serial_key(source.serial_start),
        )
    )
    return tuple(eligible)
