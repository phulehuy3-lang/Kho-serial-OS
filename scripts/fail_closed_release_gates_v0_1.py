"""Pure fail-closed release-gate aggregation.

No external I/O and no production mutation path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


READY_FOR_RELEASE = "READY_FOR_RELEASE"
HOLD = "HOLD"


@dataclass(frozen=True, slots=True)
class ReleaseDecision:
    """Deterministic fail-closed release decision."""

    status: str
    ready: bool
    blocking_gates: tuple[str, ...]


def _validate_gate_name(name: object) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("gate name must be a non-empty string")
    return name


def _validate_tristate(name: str, value: object) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a native boolean or None")
    return value


def evaluate_release_gates(
    applicable_gates: Mapping[str, bool | None],
    hold_conflict: bool | None,
) -> ReleaseDecision:
    """Aggregate already-scoped gate evidence into READY_FOR_RELEASE or HOLD.

    Empty evidence, FAIL, UNKNOWN, present HOLD conflict, and unknown HOLD
    state all fail closed.
    """

    blockers: list[str] = []

    if not applicable_gates:
        blockers.append("gate_evidence:EMPTY")

    validated_names: list[str] = []
    for raw_name in applicable_gates:
        validated_names.append(_validate_gate_name(raw_name))

    for gate_name in sorted(validated_names):
        result = _validate_tristate(
            f"gate {gate_name!r}",
            applicable_gates[gate_name],
        )

        if result is None:
            blockers.append(f"{gate_name}:UNKNOWN")
        elif result is False:
            blockers.append(f"{gate_name}:FAIL")

    hold_value = _validate_tristate("hold_conflict", hold_conflict)
    if hold_value is None:
        blockers.append("hold_conflict:UNKNOWN")
    elif hold_value is True:
        blockers.append("hold_conflict:PRESENT")

    if blockers:
        return ReleaseDecision(
            status=HOLD,
            ready=False,
            blocking_gates=tuple(blockers),
        )

    return ReleaseDecision(
        status=READY_FOR_RELEASE,
        ready=True,
        blocking_gates=(),
    )
