"""Pure source-derived reconciliation and formula-health controls.

No external I/O and no production mutation path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class FormulaAnchorSnapshot:
    """Minimal evidence required to judge one formula anchor."""

    name: str
    formula_present: bool
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("formula anchor name must be a non-empty string")
        if not isinstance(self.formula_present, bool):
            raise TypeError("formula_present must be a native boolean")
        if self.error_code is not None and not isinstance(
            self.error_code, str
        ):
            raise TypeError("error_code must be text or None")


def _valid_metric_keys(metrics: Mapping[object, object]) -> bool:
    return all(
        isinstance(key, str) and bool(key.strip())
        for key in metrics
    )


def exact_source_derived_reconciliation(
    source_metrics: Mapping[object, object],
    derived_metrics: Mapping[object, object],
) -> bool:
    """Return True only for exact normalized source/derived parity."""

    if not _valid_metric_keys(source_metrics):
        return False
    if not _valid_metric_keys(derived_metrics):
        return False

    if set(source_metrics) != set(derived_metrics):
        return False

    for key, source_value in source_metrics.items():
        derived_value = derived_metrics[key]

        if type(source_value) is not type(derived_value):
            return False
        if source_value != derived_value:
            return False

    return True


def formula_anchor_healthy(anchor: FormulaAnchorSnapshot) -> bool:
    """Return True only when a formula exists and no error is reported."""

    if anchor.formula_present is not True:
        return False
    if anchor.error_code is None:
        return True
    return not anchor.error_code.strip()


def formula_anchors_healthy(
    anchors: Sequence[FormulaAnchorSnapshot],
) -> bool:
    """Return True only for a non-empty, unique, all-healthy anchor set."""

    if not anchors:
        return False

    names = tuple(anchor.name.strip() for anchor in anchors)
    if len(set(names)) != len(names):
        return False

    return all(formula_anchor_healthy(anchor) for anchor in anchors)
