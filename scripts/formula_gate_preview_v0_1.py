"""Synthetic formula pair preview; no operational release authority."""

from __future__ import annotations

from dataclasses import dataclass

from scripts.fail_closed_release_gates_v0_1 import evaluate_release_gates
from scripts.required_gate_set_preflight_v0_1 import (
    CONTRACT_ID,
    MaterializedGateEvidence,
    RequiredGateScenario,
    assess_required_gate_set,
)


SCENARIO_ID = "SYNTHETIC_FORMULA_PAIR"
REQUIRED_GATES = ("formula_health", "formula_semantics")


@dataclass(frozen=True, slots=True)
class FormulaGatePreviewDecision:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    production_write_authorized: bool = False


def evaluate_formula_gate_preview(
    task_id: str,
    scope_id: str,
    expected_capture_marker: str,
    evidence: tuple[MaterializedGateEvidence, ...],
    hold_conflict: bool | None,
) -> FormulaGatePreviewDecision:
    """Require independent formula health and semantics in a synthetic scope."""

    scenario = RequiredGateScenario(
        contract_id=CONTRACT_ID,
        scenario_id=SCENARIO_ID,
        task_id=task_id,
        scope_id=scope_id,
        required_gate_ids=REQUIRED_GATES,
        expected_capture_marker=expected_capture_marker,
    )
    preflight = assess_required_gate_set(scenario, evidence)
    if not preflight.ready:
        return FormulaGatePreviewDecision(
            status="HOLD",
            ready=False,
            blocking_reasons=preflight.blocking_reasons,
        )
    decision = evaluate_release_gates(preflight.validated_gate_map, hold_conflict)
    return FormulaGatePreviewDecision(
        status="READY_FOR_PREVIEW" if decision.ready else "HOLD",
        ready=decision.ready,
        blocking_reasons=decision.blocking_gates,
    )
