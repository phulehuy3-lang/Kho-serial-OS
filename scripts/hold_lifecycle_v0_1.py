"""Pure HOLD lifecycle control.

The module is side-effect-free. It validates state and readiness only and
never mutates external or production data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from scripts.serial_interval_integrity_v0_1 import SerialInterval, intervals_overlap


PASS = "PASS"
HOLD = "HOLD"

BLOCK_EVIDENCE = "BLOCK_EVIDENCE"
BLOCK_DATE = "BLOCK_DATE"
BLOCK_OVERLAP = "BLOCK_OVERLAP"
BLOCK_STOCK_YEAR = "BLOCK_STOCK_YEAR"
BLOCK_STATE_MISMATCH = "BLOCK_STATE_MISMATCH"
PASS_RELEASE_READY = "PASS_RELEASE_READY"

BLOCK_NO_READY = "BLOCK_NO_READY"
BLOCK_TX_GATE = "BLOCK_TX_GATE"
BLOCK_APPROVAL = "BLOCK_APPROVAL"
BLOCK_PAYLOAD = "BLOCK_PAYLOAD"
BLOCK_EXECUTION_NOT_READY = "BLOCK_EXECUTION_NOT_READY"
BLOCK_SAFE_STATE = "BLOCK_SAFE_STATE"
PASS_TRANSITION_INTENT = "PASS_TRANSITION_INTENT"

PASS_RELEASE_READBACK = "PASS_RELEASE_READBACK"

_ALLOWED_STATES = {"ACTIVE", "RELEASED", "REVERSED", "CANCELLED"}


@dataclass(frozen=True, slots=True)
class HoldRecord:
    hold_id: str
    scope_type: str
    target_id: str
    category: str
    range_start: str | None
    range_end: str | None
    hold_type: str
    hold_flag: bool | None
    status: str
    evidence_id: str | None
    reason: str
    created_at: str


@dataclass(frozen=True, slots=True)
class IntervalHoldState:
    interval_id: str
    category: str
    range_start: str
    range_end: str
    available_qty: int
    status: str
    hold_flag: bool | None
    evidence_status: str | None
    source_date_text: str | None
    source_year: int | None
    source_year_status: str | None


@dataclass(frozen=True, slots=True)
class HoldIsolationDecision:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HoldReleaseReadiness:
    status: str
    ready: bool
    canonical_decision: str
    first_blocking_gate: str | None
    blocking_reasons: tuple[str, ...]
    active_overlap_peer_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HoldTransitionIntent:
    release_decision: str
    transaction_gate_decision: str | None
    approval_status: str | None
    expected_payload_hash: str | None
    actual_payload_hash: str | None
    execution_ready: bool | None
    last_safe_state: str | None


@dataclass(frozen=True, slots=True)
class HoldTransitionIntentDecision:
    status: str
    ready: bool
    canonical_decision: str
    blocking_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HoldReleaseReadback:
    registry_hold_flag: bool | None
    registry_status: str | None
    interval_hold_flag: bool | None
    quarantine_contains_target: bool | None
    eligible_contains_target: bool | None
    lookup_reports_hold: bool | None
    ranking_contains_target: bool | None
    inventory_total_before: int | None
    inventory_total_after: int | None
    rollback_proof_pass: bool | None


@dataclass(frozen=True, slots=True)
class HoldReadbackDecision:
    status: str
    ready: bool
    canonical_decision: str
    blocking_reasons: tuple[str, ...]


def _clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def _strict_bool(value: object) -> bool:
    return isinstance(value, bool)


def _range_key(value: str | None) -> int | None:
    if not isinstance(value, str) or not value or not value.isdigit():
        return None
    return int(value)


def _parse_exact_dd_mm_yyyy(value: str | None) -> datetime | None:
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        parsed = datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return None
    return parsed if parsed.strftime("%d/%m/%Y") == value else None


def _ranges_overlap(
    left_start: str | None,
    left_end: str | None,
    right_start: str | None,
    right_end: str | None,
) -> bool | None:
    """Delegate inclusive overlap semantics to the canonical interval control."""

    ls = _range_key(left_start)
    le = _range_key(left_end)
    rs = _range_key(right_start)
    re = _range_key(right_end)
    if None in {ls, le, rs, re}:
        return None

    assert ls is not None and le is not None
    assert rs is not None and re is not None

    try:
        left = SerialInterval(ls, le)
        right = SerialInterval(rs, re)
    except (TypeError, ValueError):
        return None

    return intervals_overlap(left, right)


def validate_hold_record(
    record: HoldRecord,
    interval: IntervalHoldState | None = None,
) -> HoldIsolationDecision:
    blockers: list[str] = []

    for code, value in (
        ("HOLD_ID_MISSING", record.hold_id),
        ("SCOPE_TYPE_MISSING", record.scope_type),
        ("TARGET_ID_MISSING", record.target_id),
        ("HOLD_TYPE_MISSING", record.hold_type),
        ("EVIDENCE_ID_MISSING", record.evidence_id),
        ("REASON_MISSING", record.reason),
        ("CREATED_AT_MISSING", record.created_at),
    ):
        if not _clean(value):
            blockers.append(f"HOLD_ISOLATION:{code}")

    if record.status not in _ALLOWED_STATES:
        blockers.append("HOLD_ISOLATION:STATUS_INVALID")
    if not _strict_bool(record.hold_flag):
        blockers.append("HOLD_ISOLATION:HOLDFLAG_NOT_BOOLEAN")
    if record.status == "ACTIVE" and record.hold_flag is not True:
        blockers.append("HOLD_ISOLATION:ACTIVE_REQUIRES_TRUE_HOLDFLAG")
    if record.status == "RELEASED" and record.hold_flag is not False:
        blockers.append("HOLD_ISOLATION:RELEASED_REQUIRES_FALSE_HOLDFLAG")

    if record.scope_type == "INTERVAL":
        if _range_key(record.range_start) is None:
            blockers.append("HOLD_ISOLATION:RANGE_START_INVALID")
        if _range_key(record.range_end) is None:
            blockers.append("HOLD_ISOLATION:RANGE_END_INVALID")
        if _ranges_overlap(
            record.range_start,
            record.range_end,
            record.range_start,
            record.range_end,
        ) is None:
            blockers.append("HOLD_ISOLATION:RANGE_INVALID")

        if interval is None:
            blockers.append("HOLD_ISOLATION:INTERVAL_STATE_MISSING")
        else:
            if interval.interval_id != record.target_id:
                blockers.append("HOLD_ISOLATION:TARGET_INTERVAL_MISMATCH")
            if interval.category != record.category:
                blockers.append("HOLD_ISOLATION:CATEGORY_MISMATCH")
            if not _strict_bool(interval.hold_flag):
                blockers.append("HOLD_ISOLATION:INTERVAL_HOLDFLAG_NOT_BOOLEAN")
            elif record.status == "ACTIVE" and interval.hold_flag is not True:
                blockers.append("HOLD_ISOLATION:REGISTRY_INTERVAL_FLAG_MISMATCH")
            elif record.status == "RELEASED" and interval.hold_flag is not False:
                blockers.append("HOLD_ISOLATION:REGISTRY_INTERVAL_FLAG_MISMATCH")

    if blockers:
        return HoldIsolationDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
        )
    return HoldIsolationDecision(status=PASS, ready=True, blocking_reasons=())


def _peer_id(peer: HoldRecord) -> str:
    return _clean(peer.hold_id) or "<MISSING_HOLD_ID>"


def blocking_overlapping_interval_holds(
    target: HoldRecord,
    peers: Iterable[HoldRecord],
) -> tuple[str, ...]:
    if target.scope_type != "INTERVAL":
        return ()

    blockers: list[str] = []
    for peer in peers:
        if peer.hold_id == target.hold_id:
            continue
        if peer.scope_type != "INTERVAL":
            continue
        if peer.category != target.category:
            continue

        overlap = _ranges_overlap(
            target.range_start,
            target.range_end,
            peer.range_start,
            peer.range_end,
        )
        if overlap is None:
            blockers.append(_peer_id(peer))
            continue
        if not overlap:
            continue
        if peer.status == "ACTIVE":
            blockers.append(_peer_id(peer))
            continue
        if peer.status not in _ALLOWED_STATES:
            blockers.append(_peer_id(peer))
            continue
        if not _strict_bool(peer.hold_flag):
            blockers.append(_peer_id(peer))
            continue
        if peer.hold_flag is True:
            blockers.append(_peer_id(peer))

    return tuple(sorted(set(blockers)))


def evaluate_hold_release_readiness(
    record: HoldRecord,
    interval: IntervalHoldState,
    peers: Iterable[HoldRecord] = (),
) -> HoldReleaseReadiness:
    isolation = validate_hold_record(record, interval)
    if not isolation.ready:
        return HoldReleaseReadiness(
            status=HOLD,
            ready=False,
            canonical_decision=BLOCK_STATE_MISMATCH,
            first_blocking_gate="STATE",
            blocking_reasons=isolation.blocking_reasons,
            active_overlap_peer_ids=(),
        )

    if (
        record.scope_type != "INTERVAL"
        or record.status != "ACTIVE"
        or record.hold_flag is not True
    ):
        return HoldReleaseReadiness(
            status=HOLD,
            ready=False,
            canonical_decision=BLOCK_STATE_MISMATCH,
            first_blocking_gate="STATE",
            blocking_reasons=("HOLD_RELEASE:TARGET_NOT_ACTIVE_INTERVAL",),
            active_overlap_peer_ids=(),
        )

    if interval.evidence_status != "VERIFIED_INDEPENDENT":
        return HoldReleaseReadiness(
            status=HOLD,
            ready=False,
            canonical_decision=BLOCK_EVIDENCE,
            first_blocking_gate="EVIDENCE",
            blocking_reasons=("HOLD_RELEASE:EVIDENCE_NOT_VERIFIED_INDEPENDENT",),
            active_overlap_peer_ids=(),
        )

    source_date = _parse_exact_dd_mm_yyyy(interval.source_date_text)
    if (
        source_date is None
        or not isinstance(interval.source_year, int)
        or isinstance(interval.source_year, bool)
        or source_date.year != interval.source_year
    ):
        return HoldReleaseReadiness(
            status=HOLD,
            ready=False,
            canonical_decision=BLOCK_DATE,
            first_blocking_gate="EXACT_SOURCE_DATE",
            blocking_reasons=("HOLD_RELEASE:SOURCE_DATE_INVALID_OR_YEAR_MISMATCH",),
            active_overlap_peer_ids=(),
        )

    overlap_peers = blocking_overlapping_interval_holds(record, peers)
    if overlap_peers:
        return HoldReleaseReadiness(
            status=HOLD,
            ready=False,
            canonical_decision=BLOCK_OVERLAP,
            first_blocking_gate="ACTIVE_OVERLAP",
            blocking_reasons=("HOLD_RELEASE:BLOCKING_OVERLAP_PRESENT",),
            active_overlap_peer_ids=overlap_peers,
        )

    if (
        not isinstance(interval.available_qty, int)
        or isinstance(interval.available_qty, bool)
        or interval.available_qty <= 0
        or interval.source_year_status != "YEAR_VERIFIED"
    ):
        return HoldReleaseReadiness(
            status=HOLD,
            ready=False,
            canonical_decision=BLOCK_STOCK_YEAR,
            first_blocking_gate="STOCK_YEAR",
            blocking_reasons=("HOLD_RELEASE:STOCK_OR_YEAR_NOT_READY",),
            active_overlap_peer_ids=(),
        )

    return HoldReleaseReadiness(
        status=PASS,
        ready=True,
        canonical_decision=PASS_RELEASE_READY,
        first_blocking_gate=None,
        blocking_reasons=(),
        active_overlap_peer_ids=(),
    )


def evaluate_hold_transition_intent(
    intent: HoldTransitionIntent,
) -> HoldTransitionIntentDecision:
    if intent.release_decision != PASS_RELEASE_READY:
        return HoldTransitionIntentDecision(
            HOLD, False, BLOCK_NO_READY,
            ("HOLD_TRANSITION:TARGET_NOT_RELEASE_READY",),
        )
    if intent.transaction_gate_decision != PASS_RELEASE_READY:
        return HoldTransitionIntentDecision(
            HOLD, False, BLOCK_TX_GATE,
            ("HOLD_TRANSITION:TRANSACTION_GATE_NOT_RELEASE_READY",),
        )
    if intent.approval_status != "APPROVED":
        return HoldTransitionIntentDecision(
            HOLD, False, BLOCK_APPROVAL,
            ("HOLD_TRANSITION:APPROVAL_NOT_APPROVED",),
        )
    if (
        not _clean(intent.expected_payload_hash)
        or not _clean(intent.actual_payload_hash)
        or intent.expected_payload_hash != intent.actual_payload_hash
    ):
        return HoldTransitionIntentDecision(
            HOLD, False, BLOCK_PAYLOAD,
            ("HOLD_TRANSITION:PAYLOAD_HASH_MISMATCH",),
        )
    if intent.execution_ready is not True:
        return HoldTransitionIntentDecision(
            HOLD, False, BLOCK_EXECUTION_NOT_READY,
            ("HOLD_TRANSITION:EXECUTION_READY_NOT_TRUE",),
        )
    if intent.last_safe_state != "GATE_EVALUATED":
        return HoldTransitionIntentDecision(
            HOLD, False, BLOCK_SAFE_STATE,
            ("HOLD_TRANSITION:LAST_SAFE_STATE_INVALID",),
        )
    return HoldTransitionIntentDecision(
        PASS, True, PASS_TRANSITION_INTENT, (),
    )


def evaluate_hold_release_readback(
    snapshot: HoldReleaseReadback,
) -> HoldReadbackDecision:
    blockers: list[str] = []

    bool_fields = {
        "REGISTRY_HOLDFLAG": snapshot.registry_hold_flag,
        "INTERVAL_HOLDFLAG": snapshot.interval_hold_flag,
        "QUARANTINE_CONTAINS_TARGET": snapshot.quarantine_contains_target,
        "ELIGIBLE_CONTAINS_TARGET": snapshot.eligible_contains_target,
        "LOOKUP_REPORTS_HOLD": snapshot.lookup_reports_hold,
        "RANKING_CONTAINS_TARGET": snapshot.ranking_contains_target,
        "ROLLBACK_PROOF": snapshot.rollback_proof_pass,
    }
    for name, value in bool_fields.items():
        if not _strict_bool(value):
            blockers.append(f"HOLD_READBACK:{name}_UNKNOWN_OR_INVALID")

    if snapshot.registry_hold_flag is not False:
        blockers.append("HOLD_READBACK:REGISTRY_HOLDFLAG_NOT_FALSE")
    if snapshot.registry_status != "RELEASED":
        blockers.append("HOLD_READBACK:REGISTRY_STATUS_NOT_RELEASED")
    if snapshot.interval_hold_flag is not False:
        blockers.append("HOLD_READBACK:INTERVAL_HOLDFLAG_NOT_FALSE")
    if snapshot.quarantine_contains_target is not False:
        blockers.append("HOLD_READBACK:TARGET_STILL_IN_QUARANTINE")
    if snapshot.eligible_contains_target is not True:
        blockers.append("HOLD_READBACK:TARGET_NOT_ELIGIBLE")
    if snapshot.lookup_reports_hold is not False:
        blockers.append("HOLD_READBACK:LOOKUP_STILL_REPORTS_HOLD")
    if snapshot.ranking_contains_target is not True:
        blockers.append("HOLD_READBACK:RANKING_DOES_NOT_SEE_TARGET")

    if (
        not isinstance(snapshot.inventory_total_before, int)
        or isinstance(snapshot.inventory_total_before, bool)
        or not isinstance(snapshot.inventory_total_after, int)
        or isinstance(snapshot.inventory_total_after, bool)
        or snapshot.inventory_total_before != snapshot.inventory_total_after
    ):
        blockers.append("HOLD_READBACK:INVENTORY_TOTAL_CHANGED_OR_UNKNOWN")
    if snapshot.rollback_proof_pass is not True:
        blockers.append("HOLD_READBACK:ROLLBACK_PROOF_NOT_PASS")

    if blockers:
        return HoldReadbackDecision(
            status=HOLD,
            ready=False,
            canonical_decision=HOLD,
            blocking_reasons=tuple(sorted(set(blockers))),
        )
    return HoldReadbackDecision(
        status=PASS,
        ready=True,
        canonical_decision=PASS_RELEASE_READBACK,
        blocking_reasons=(),
    )
