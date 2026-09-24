"""Pure implementation of ALLOCATION_NEAREST_PRIOR_V1_0.

No external I/O. No production write path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


SERIAL_START_MAX_DIGITS = 4096


@dataclass(frozen=True, slots=True)
class SourceLot:
    source_id: str
    source_date: date
    source_row: int
    serial_start: str


def _serial_key(serial_start: object) -> tuple[int, str]:
    """Return a numeric-order key without converting the serial to int.

    Serial identifiers remain text so leading zeroes are preserved. Only
    non-empty ASCII decimal text up to the explicit safety bound is accepted.
    """

    if type(serial_start) is not str or not serial_start:
        raise ValueError("serial_start must be non-empty ASCII decimal text")
    if len(serial_start) > SERIAL_START_MAX_DIGITS:
        raise ValueError(
            f"serial_start exceeds maximum length of {SERIAL_START_MAX_DIGITS} digits"
        )
    if any(char < "0" or char > "9" for char in serial_start):
        raise ValueError("serial_start must be non-empty ASCII decimal text")

    significant = serial_start.lstrip("0") or "0"
    return (len(significant), significant)


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
