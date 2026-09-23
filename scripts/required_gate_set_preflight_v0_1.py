"""Pure, scoped completeness check before fail-closed gate aggregation.

The caller supplies the authoritative required set and capture marker. A PASS
proves only exact coverage and binding of already-materialized evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


CONTRACT_ID = "REQUIRED_GATE_SET_PREFLIGHT_V1"
PASS = "PASS"
HOLD = "HOLD"


@dataclass(frozen=True, slots=True)
class RequiredGateScenario:
    contract_id: str
    scenario_id: str
    task_id: str
    scope_id: str
    required_gate_ids: tuple[str, ...]
    expected_capture_marker: str


@dataclass(frozen=True, slots=True)
class MaterializedGateEvidence:
    gate_id: str
    scenario_id: str
    task_id: str
    scope_id: str
    capture_marker: str
    value: bool | None


@dataclass(frozen=True, slots=True)
class GateSetPreflightResult:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    validated_gate_map: Mapping[str, bool | None] | None


def _valid_id(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
    )


def assess_required_gate_set(
    scenario: RequiredGateScenario,
    evidence: tuple[MaterializedGateEvidence, ...],
) -> GateSetPreflightResult:
    """Return a complete gate map only for matching scenario-bound records.

    False and None values are structurally valid and must be assessed by
    Control 07 after a PASS. No external evidence is discovered here.
    """

    blockers: set[str] = set()
    if not isinstance(scenario, RequiredGateScenario):
        blockers.add("SCENARIO_INVALID")
        required: tuple[str, ...] = ()
    else:
        required = scenario.required_gate_ids
        if (
            scenario.contract_id != CONTRACT_ID
            or any(
                not _valid_id(value)
                for value in (
                    scenario.scenario_id,
                    scenario.task_id,
                    scenario.scope_id,
                    scenario.expected_capture_marker,
                )
            )
            or type(required) is not tuple
            or not required
            or any(not _valid_id(gate_id) for gate_id in required)
            or len(set(required)) != len(required)
        ):
            blockers.add("SCENARIO_INVALID")

    if type(evidence) is not tuple:
        blockers.add("EVIDENCE_MISSING")
        records: tuple[MaterializedGateEvidence, ...] = ()
    else:
        records = evidence
        if not records:
            blockers.add("EVIDENCE_MISSING")

    gate_ids: list[str] = []
    values: dict[str, bool | None] = {}
    for record in records:
        if not isinstance(record, MaterializedGateEvidence):
            blockers.add("BINDING_MISMATCH")
            continue
        if not _valid_id(record.gate_id):
            blockers.add("BINDING_MISMATCH")
        else:
            gate_ids.append(record.gate_id)
            values[record.gate_id] = record.value
        if not all(
            _valid_id(value)
            for value in (
                record.scenario_id,
                record.task_id,
                record.scope_id,
                record.capture_marker,
            )
        ):
            blockers.add("BINDING_MISMATCH")
        if isinstance(scenario, RequiredGateScenario):
            if (
                record.scenario_id != scenario.scenario_id
                or record.task_id != scenario.task_id
                or record.scope_id != scenario.scope_id
            ):
                blockers.add("BINDING_MISMATCH")
            if record.capture_marker != scenario.expected_capture_marker:
                blockers.add("MARKER_MISMATCH")
        if record.value is not None and type(record.value) is not bool:
            blockers.add("VALUE_INVALID")

    if len(set(gate_ids)) != len(gate_ids):
        blockers.add("EVIDENCE_DUPLICATE")
    if "SCENARIO_INVALID" not in blockers:
        if set(required) - set(gate_ids):
            blockers.add("EVIDENCE_MISSING")
        if set(gate_ids) - set(required):
            blockers.add("EVIDENCE_EXTRA")

    if blockers:
        return GateSetPreflightResult(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(blockers)),
            validated_gate_map=None,
        )
    return GateSetPreflightResult(
        status=PASS,
        ready=True,
        blocking_reasons=(),
        validated_gate_map=MappingProxyType(
            {gate_id: values[gate_id] for gate_id in sorted(required)}
        ),
    )
