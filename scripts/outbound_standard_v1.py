"""Public-safe outbound SOP v1.0 control kernel.

This module is deterministic and side-effect free. It encodes the five
prospective outbound controls mirrored from the canonical warehouse registry:

- SOP_OUTBOUND_STANDARD_V1_0
- CTRL_OUTBOUND_EFFECTIVE_DATE_SEMANTICS_V1
- CTRL_BBGH_TEMPLATE_AUTHORITY_V1
- CTRL_ALLOCATION_PLAN_FIELD_BOUND_WRITER_V1
- CTRL_OUTBOUND_SINGLE_PASS_EXECUTION_BUNDLE_V1

It grants no provider access and no warehouse write authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping, Sequence


CURRENT_STATE_SAFE_EXECUTION = "CURRENT_STATE_SAFE_EXECUTION"
POSTFACTO_PHYSICAL_DELIVERY = "POSTFACTO_PHYSICAL_DELIVERY"
HISTORICAL_AS_OF_RECONSTRUCTION = "HISTORICAL_AS_OF_RECONSTRUCTION"

PARTNER_SPECIFIC_CANONICAL = "PARTNER_SPECIFIC_CANONICAL"
FAMILY_TEMPLATE_FALLBACK = "FAMILY_TEMPLATE_FALLBACK"
GENERIC_TEMPLATE_FALLBACK = "GENERIC_TEMPLATE_FALLBACK"

CLEAN_PASS = "CLEAN_PASS"
REMEDIATED_PASS = "REMEDIATED_PASS"
READ_ONLY_NO_PRODUCTION_MUTATION = "READ_ONLY_NO_PRODUCTION_MUTATION"

ALLOCATION_FIELDS = (
    "AllocationID",
    "TaskID",
    "TransactionKey",
    "ReservationID",
    "SourceIntervalID",
    "SourceEventID",
    "AllocatedQty",
    "SerialStart",
    "SerialEnd",
    "Decision",
    "SourceRankGateID",
    "CandidateSetHash",
    "AllocationRank",
    "SourceDate",
    "SourceRow",
    "RankPlanDecision",
)


class OutboundControlError(ValueError):
    """Fail-closed outbound control error."""


@dataclass(frozen=True, slots=True)
class EffectiveDateDecision:
    mode: str
    document_date: date
    execution_date: date


@dataclass(frozen=True, slots=True)
class TemplateDecision:
    template_class: str
    template_id: str


@dataclass(frozen=True, slots=True)
class SinglePassState:
    fresh_snapshot: bool
    prewrite_manifest: bool
    production_mutation_batches: int
    consolidated_readback: bool
    final_anti_replay_lock: bool
    repaired_historical_defect: bool = False


@dataclass(frozen=True, slots=True)
class OutboundCloseInputs:
    execution_mode: str
    template_class: str
    allocation_plan_pass: bool
    hold_clear: bool
    duplicate_prewrite_pass: bool
    postwrite_readback_pass: bool
    final_anti_replay_lock: bool
    repaired_historical_defect: bool = False


def resolve_effective_date_mode(
    *,
    document_date: date,
    execution_date: date,
    prior_delivery_proven: object = False,
    historical_reconstruction: object = False,
) -> EffectiveDateDecision:
    """Resolve one explicit date-semantics mode before source ranking."""

    if type(prior_delivery_proven) is not bool:
        raise OutboundControlError("PRIOR_DELIVERY_FLAG_INVALID")
    if type(historical_reconstruction) is not bool:
        raise OutboundControlError("HISTORICAL_RECONSTRUCTION_FLAG_INVALID")
    if prior_delivery_proven and historical_reconstruction:
        raise OutboundControlError("AMBIGUOUS_EFFECTIVE_DATE_MODE")

    if historical_reconstruction:
        mode = HISTORICAL_AS_OF_RECONSTRUCTION
    elif prior_delivery_proven:
        mode = POSTFACTO_PHYSICAL_DELIVERY
    else:
        mode = CURRENT_STATE_SAFE_EXECUTION

    return EffectiveDateDecision(
        mode=mode,
        document_date=document_date,
        execution_date=execution_date,
    )


def choose_template_authority(
    *,
    partner_template_id: object = None,
    family_template_id: object = None,
    generic_template_id: object = None,
) -> TemplateDecision:
    """Resolve partner -> family -> generic template authority."""

    for template_class, template_id in (
        (PARTNER_SPECIFIC_CANONICAL, partner_template_id),
        (FAMILY_TEMPLATE_FALLBACK, family_template_id),
        (GENERIC_TEMPLATE_FALLBACK, generic_template_id),
    ):
        if isinstance(template_id, str) and template_id.strip():
            return TemplateDecision(template_class, template_id.strip())

    raise OutboundControlError("BLOCK_TEMPLATE_AUTHORITY")


def bind_allocation_fields(
    live_headers: Sequence[object],
) -> Mapping[str, int]:
    """Bind allocation fields by live header identity, never by A-column offset."""

    if len(live_headers) != len(ALLOCATION_FIELDS):
        raise OutboundControlError("BLOCK_ALLOCATION_WRITER")

    if any(not isinstance(value, str) or not value for value in live_headers):
        raise OutboundControlError("BLOCK_ALLOCATION_WRITER")

    if len(set(live_headers)) != len(live_headers):
        raise OutboundControlError("BLOCK_ALLOCATION_WRITER")

    if set(live_headers) != set(ALLOCATION_FIELDS):
        raise OutboundControlError("BLOCK_ALLOCATION_WRITER")

    return {name: index for index, name in enumerate(live_headers)}


def validate_rank_plan_decision(
    *,
    formula_present: object,
    evaluated_value: object,
) -> bool:
    """Require formula-owned PASS_PLAN_RANK rather than a literal PASS."""

    if formula_present is not True:
        raise OutboundControlError("RANK_PLAN_FORMULA_REQUIRED")
    if evaluated_value != "PASS_PLAN_RANK":
        raise OutboundControlError("RANK_PLAN_NOT_PASS")
    return True


def classify_single_pass_close(state: SinglePassState) -> str:
    """Require one bounded mutation batch and one consolidated read-back."""

    for field_name in (
        "fresh_snapshot",
        "prewrite_manifest",
        "consolidated_readback",
        "final_anti_replay_lock",
        "repaired_historical_defect",
    ):
        if type(getattr(state, field_name)) is not bool:
            raise OutboundControlError(f"{field_name.upper()}_TYPE_INVALID")

    if (
        not state.fresh_snapshot
        or not state.prewrite_manifest
        or state.production_mutation_batches != 1
        or not state.consolidated_readback
        or not state.final_anti_replay_lock
    ):
        raise OutboundControlError("BLOCK_SINGLE_PASS")

    return REMEDIATED_PASS if state.repaired_historical_defect else CLEAN_PASS


def classify_outbound_close(inputs: OutboundCloseInputs) -> str:
    """Terminal SOP classification after all five generalized controls."""

    boolean_fields = (
        inputs.allocation_plan_pass,
        inputs.hold_clear,
        inputs.duplicate_prewrite_pass,
        inputs.postwrite_readback_pass,
        inputs.final_anti_replay_lock,
        inputs.repaired_historical_defect,
    )
    if any(type(value) is not bool for value in boolean_fields):
        raise OutboundControlError("OUTBOUND_BOOLEAN_TYPE_INVALID")

    if inputs.execution_mode == HISTORICAL_AS_OF_RECONSTRUCTION:
        return READ_ONLY_NO_PRODUCTION_MUTATION

    if inputs.execution_mode not in {
        CURRENT_STATE_SAFE_EXECUTION,
        POSTFACTO_PHYSICAL_DELIVERY,
    }:
        raise OutboundControlError("EXECUTION_MODE_INVALID")

    if inputs.template_class not in {
        PARTNER_SPECIFIC_CANONICAL,
        FAMILY_TEMPLATE_FALLBACK,
        GENERIC_TEMPLATE_FALLBACK,
    }:
        raise OutboundControlError("TEMPLATE_CLASS_INVALID")

    if not (
        inputs.allocation_plan_pass
        and inputs.hold_clear
        and inputs.duplicate_prewrite_pass
    ):
        raise OutboundControlError("OUTBOUND_PREWRITE_BLOCK")

    if not (
        inputs.postwrite_readback_pass
        and inputs.final_anti_replay_lock
    ):
        raise OutboundControlError("OUTBOUND_CLOSE_BLOCK")

    return REMEDIATED_PASS if inputs.repaired_historical_defect else CLEAN_PASS
