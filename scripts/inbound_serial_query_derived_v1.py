"""Pure composition profile for inbound serial acceptance.

Consumes already-materialized producer outcomes only. No live I/O or mutation.
"""

from __future__ import annotations

from dataclasses import dataclass

from scripts.fail_closed_release_gates_v0_1 import (
    HOLD as RELEASE_HOLD,
    READY_FOR_RELEASE,
    evaluate_release_gates,
)
from scripts.formula_semantic_identity_v0_1 import (
    FormulaSemanticAssessment,
    HOLD as FORMULA_HOLD,
    PASS as FORMULA_PASS,
)
from scripts.required_gate_set_preflight_v0_1 import (
    CONTRACT_ID as PREFLIGHT_CONTRACT_ID,
    HOLD as PREFLIGHT_HOLD,
    PASS as PREFLIGHT_PASS,
    MaterializedGateEvidence,
    RequiredGateScenario,
    assess_required_gate_set,
)
from scripts.source_readback_v0_1 import SourceReadbackResult
from scripts.source_role_boundary_v0_1 import SourceRoleBoundaryResult


PROFILE_CONTRACT_ID = "INBOUND_SERIAL_QUERY_DERIVED_PROFILE_V1"
SCENARIO_ID = "INBOUND_SERIAL_QUERY_DERIVED_V1"
INBOUND_CONTROL_READY = "INBOUND_CONTROL_READY"
HOLD = "HOLD"

REQUIRED_GATE_IDS = (
    "source_role_boundary",
    "source_readback",
    "serial_range_quantity",
    "serial_overlap_free",
    "source_derived_reconciliation",
    "formula_health",
    "formula_semantics",
)


@dataclass(frozen=True, slots=True)
class InboundProfileContext:
    """Exact profile identity and evidence binding."""

    contract_id: object
    task_id: object
    scope_id: object
    capture_marker: object


@dataclass(frozen=True, slots=True)
class InboundProducerOutcomes:
    """Already-materialized outcomes from the seven required producers."""

    source_role_boundary: object
    source_readback: object
    serial_range_quantity: object
    serial_overlap_free: object
    source_derived_reconciliation: object
    formula_health: object
    formula_semantics: object


@dataclass(frozen=True, slots=True)
class InboundProfileResult:
    """Fail-closed result for this locked inbound scenario."""

    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    preflight_status: str
    release_status: str | None
    production_write_authorized: bool = False


def _valid_exact_text(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
    )


def _context_blockers(context: object) -> tuple[str, ...]:
    blockers: list[str] = []
    if type(context) is not InboundProfileContext:
        return ("PROFILE_CONTEXT_INVALID",)
    if context.contract_id != PROFILE_CONTRACT_ID:
        blockers.append("PROFILE_CONTRACT_INVALID")
    if not all(
        _valid_exact_text(value)
        for value in (context.task_id, context.scope_id, context.capture_marker)
    ):
        blockers.append("PROFILE_CONTEXT_INVALID")
    return tuple(sorted(set(blockers)))


def _convert_source_role(value: object) -> object:
    if value is None:
        return None
    if type(value) is not SourceRoleBoundaryResult:
        return None
    if value.production_write_authorized is not False:
        return None
    if (
        value.status == "PASS"
        and value.boundary_pass is True
        and value.blocking_reasons == ()
    ):
        return True
    if (
        value.status == "HOLD"
        and value.boundary_pass is False
        and type(value.blocking_reasons) is tuple
        and bool(value.blocking_reasons)
    ):
        return False
    return None


def _convert_source_readback(value: object) -> object:
    if value is None:
        return None
    if type(value) is not SourceReadbackResult:
        return None
    if value.production_write_authorized is not False:
        return None
    if (
        value.status == "PASS"
        and value.readback_match is True
        and value.blocking_reasons == ()
    ):
        return True
    if (
        value.status == "HOLD"
        and value.readback_match is False
        and type(value.blocking_reasons) is tuple
        and bool(value.blocking_reasons)
    ):
        return False
    return None


def _convert_formula_semantics(value: object) -> object:
    if value is None:
        return None
    if type(value) is not FormulaSemanticAssessment:
        return None
    if (
        value.status == FORMULA_PASS
        and value.ready is True
        and value.blocking_reasons == ()
    ):
        return True
    if (
        value.status == FORMULA_HOLD
        and value.ready is False
        and type(value.blocking_reasons) is tuple
        and bool(value.blocking_reasons)
    ):
        return False
    return None


def _scenario(context: InboundProfileContext) -> RequiredGateScenario:
    return RequiredGateScenario(
        contract_id=PREFLIGHT_CONTRACT_ID,
        scenario_id=SCENARIO_ID,
        task_id=context.task_id,
        scope_id=context.scope_id,
        required_gate_ids=REQUIRED_GATE_IDS,
        expected_capture_marker=context.capture_marker,
    )


def materialize_inbound_gate_evidence(
    context: InboundProfileContext,
    outcomes: InboundProducerOutcomes,
) -> tuple[MaterializedGateEvidence, ...]:
    """Bind all seven producer outcomes to the locked inbound context."""

    converted = (
        ("source_role_boundary", _convert_source_role(outcomes.source_role_boundary)),
        ("source_readback", _convert_source_readback(outcomes.source_readback)),
        ("serial_range_quantity", outcomes.serial_range_quantity),
        ("serial_overlap_free", outcomes.serial_overlap_free),
        (
            "source_derived_reconciliation",
            outcomes.source_derived_reconciliation,
        ),
        ("formula_health", outcomes.formula_health),
        ("formula_semantics", _convert_formula_semantics(outcomes.formula_semantics)),
    )
    return tuple(
        MaterializedGateEvidence(
            gate_id=gate_id,
            scenario_id=SCENARIO_ID,
            task_id=context.task_id,
            scope_id=context.scope_id,
            capture_marker=context.capture_marker,
            value=value,
        )
        for gate_id, value in converted
    )


def assess_inbound_materialized_gate_evidence(
    context: InboundProfileContext,
    evidence: tuple[MaterializedGateEvidence, ...],
    hold_conflict: object,
) -> InboundProfileResult:
    """Apply Control 13 before Control 07 to already-materialized evidence."""

    context_blockers = _context_blockers(context)
    if context_blockers:
        return InboundProfileResult(
            status=HOLD,
            ready=False,
            blocking_reasons=context_blockers,
            preflight_status=PREFLIGHT_HOLD,
            release_status=None,
        )

    preflight = assess_required_gate_set(_scenario(context), evidence)
    if preflight.status != PREFLIGHT_PASS or preflight.validated_gate_map is None:
        return InboundProfileResult(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(
                f"preflight:{reason}"
                for reason in preflight.blocking_reasons
            ),
            preflight_status=preflight.status,
            release_status=None,
        )

    try:
        release = evaluate_release_gates(
            preflight.validated_gate_map,
            hold_conflict,
        )
    except (TypeError, ValueError):
        return InboundProfileResult(
            status=HOLD,
            ready=False,
            blocking_reasons=("release:INPUT_INVALID",),
            preflight_status=PREFLIGHT_PASS,
            release_status=RELEASE_HOLD,
        )

    if release.status == READY_FOR_RELEASE and release.ready is True:
        return InboundProfileResult(
            status=INBOUND_CONTROL_READY,
            ready=True,
            blocking_reasons=(),
            preflight_status=PREFLIGHT_PASS,
            release_status=READY_FOR_RELEASE,
        )

    return InboundProfileResult(
        status=HOLD,
        ready=False,
        blocking_reasons=tuple(
            f"release:{reason}"
            for reason in release.blocking_gates
        ),
        preflight_status=PREFLIGHT_PASS,
        release_status=release.status,
    )


def evaluate_inbound_profile(
    context: InboundProfileContext,
    outcomes: InboundProducerOutcomes,
    hold_conflict: object,
) -> InboundProfileResult:
    """Compose all seven locked inbound producers through Controls 13 and 07."""

    context_blockers = _context_blockers(context)
    if context_blockers:
        return InboundProfileResult(
            status=HOLD,
            ready=False,
            blocking_reasons=context_blockers,
            preflight_status=PREFLIGHT_HOLD,
            release_status=None,
        )

    if type(outcomes) is not InboundProducerOutcomes:
        return InboundProfileResult(
            status=HOLD,
            ready=False,
            blocking_reasons=("PROFILE_INPUT_INVALID",),
            preflight_status=PREFLIGHT_HOLD,
            release_status=None,
        )

    evidence = materialize_inbound_gate_evidence(context, outcomes)
    return assess_inbound_materialized_gate_evidence(
        context,
        evidence,
        hold_conflict,
    )
