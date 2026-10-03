"""Pure SERIAL_TEXT identity validation and numeric interval projection.

No external I/O, provider access, Production locator or mutation path.
Lexical serial identity is preserved; integer projection is comparison-only.
"""

from __future__ import annotations

from dataclasses import dataclass

from scripts.serial_interval_integrity_v0_1 import SerialInterval


def _valid_serial_text(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and all("0" <= character <= "9" for character in value)
    )


@dataclass(frozen=True, slots=True)
class SerialTextInterval:
    """One inclusive serial interval with preserved lexical identity."""

    start_text: object
    end_text: object

    def __post_init__(self) -> None:
        if not _valid_serial_text(self.start_text):
            raise TypeError("serial start must be native non-blank ASCII digit text")
        if not _valid_serial_text(self.end_text):
            raise TypeError("serial end must be native non-blank ASCII digit text")
        if int(self.start_text) > int(self.end_text):
            raise ValueError("numeric serial start must be <= numeric serial end")

    @property
    def identity(self) -> tuple[str, str]:
        """Return exact lexical identities without normalization."""

        return (self.start_text, self.end_text)

    @property
    def numeric_interval(self) -> SerialInterval:
        """Project to Control 04 numeric semantics without rewriting identity."""

        return SerialInterval(int(self.start_text), int(self.end_text))

    @property
    def quantity(self) -> int:
        """Return inclusive numeric cardinality."""

        return self.numeric_interval.quantity


def serial_text_range_quantity_matches(
    interval: SerialTextInterval,
    declared_quantity: object,
) -> bool:
    """Compare declared quantity to numeric projection without coercion."""

    if type(declared_quantity) is not int:
        raise TypeError("declared quantity must be a native integer")
    if declared_quantity < 0:
        raise ValueError("declared quantity must be non-negative")
    return interval.quantity == declared_quantity
