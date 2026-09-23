"""Pure ranked-prefix allocation and lineage controls.

No external I/O and no production mutation path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from typing import Iterable, Sequence

from scripts.allocation_nearest_prior import (
    SourceLot,
    eligible_sources_nearest_prior,
)


PASS = "PASS"
HOLD = "HOLD"
CANDIDATE_SET_HASH_ALGORITHM = "SHA256_CANONICAL_JSON_V1"
CANDIDATE_SET_HASH_CONTRACT_ID = "RANKED_PREFIX_CANDIDATE_SET_HASH_V1"
ALLOCATION_PLAN_HASH_ALGORITHM = "SHA256_CANONICAL_JSON_V1"
ALLOCATION_PLAN_HASH_CONTRACT_ID = "RANKED_PREFIX_ALLOCATION_PLAN_HASH_V1"
_ALLOWED_PLAN_STATES = {"PLANNED", "COMMITTED"}


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    candidate_id: str
    source_date: date
    source_row: int
    serial_start: str
    available_qty: int


@dataclass(frozen=True, slots=True)
class AllocationSlice:
    candidate_id: str
    allocation_rank: int
    quantity: int


@dataclass(frozen=True, slots=True)
class RankedPrefixDecision:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    candidate_set_hash: str | None
    ranked_candidate_ids: tuple[str, ...]
    expected_allocation: tuple[AllocationSlice, ...]


@dataclass(frozen=True, slots=True)
class SourceRankLineage:
    task_id: str
    source_rank_gate_id: str
    candidate_set_hash: str
    ranked_candidate_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AllocationPlanRow:
    task_id: str
    source_rank_gate_id: str
    candidate_set_hash: str
    allocation_rank: int
    candidate_id: str
    planned_quantity: int
    state: str = "PLANNED"


@dataclass(frozen=True, slots=True)
class ValidationDecision:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]


def _clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _serial_key(serial_start: object) -> int | None:
    if not isinstance(serial_start, str):
        return None
    if not serial_start or not serial_start.isdigit():
        return None
    return int(serial_start)


def _candidate_blockers(
    candidate: RankedCandidate,
    target_date: date,
) -> tuple[str, ...]:
    blockers: list[str] = []
    label = candidate.candidate_id or "<blank>"

    if not _clean(candidate.candidate_id):
        blockers.append("RANKED_PREFIX:CANDIDATE_ID_MISSING")
    if type(candidate.source_date) is not date:
        blockers.append(f"RANKED_PREFIX:SOURCE_DATE_INVALID:{label}")
    elif candidate.source_date > target_date:
        blockers.append(f"RANKED_PREFIX:FUTURE_SOURCE:{label}")
    if not _positive_int(candidate.source_row):
        blockers.append(f"RANKED_PREFIX:SOURCE_ROW_INVALID:{label}")
    if _serial_key(candidate.serial_start) is None:
        blockers.append(f"RANKED_PREFIX:SERIAL_START_INVALID:{label}")
    if not _positive_int(candidate.available_qty):
        blockers.append(f"RANKED_PREFIX:AVAILABLE_QTY_INVALID:{label}")

    return tuple(blockers)


def _duplicate_id_blockers(
    candidates: Sequence[RankedCandidate],
) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for candidate in candidates:
        if candidate.candidate_id in seen:
            duplicates.add(candidate.candidate_id)
        seen.add(candidate.candidate_id)
    return tuple(
        f"RANKED_PREFIX:DUPLICATE_CANDIDATE_ID:{candidate_id}"
        for candidate_id in sorted(duplicates)
    )


def _ambiguous_rank_blockers(
    candidates: Sequence[RankedCandidate],
) -> tuple[str, ...]:
    keys: dict[tuple[int, int, int], list[str]] = {}
    for candidate in candidates:
        serial_key = _serial_key(candidate.serial_start)
        if type(candidate.source_date) is not date or serial_key is None:
            continue
        if not _positive_int(candidate.source_row):
            continue
        key = (
            -candidate.source_date.toordinal(),
            candidate.source_row,
            serial_key,
        )
        keys.setdefault(key, []).append(candidate.candidate_id)

    blockers: list[str] = []
    for ids in keys.values():
        if len(ids) > 1:
            blockers.append(
                "RANKED_PREFIX:AMBIGUOUS_RANK_KEY:"
                + ",".join(sorted(ids))
            )
    return tuple(sorted(blockers))


def _canonical_rank_candidates(
    candidates: Sequence[RankedCandidate],
    target_date: date,
) -> tuple[RankedCandidate, ...]:
    """Rank via the canonical public NEAREST-PRIOR implementation."""

    lots = tuple(
        SourceLot(
            source_id=candidate.candidate_id,
            source_date=candidate.source_date,
            source_row=candidate.source_row,
            serial_start=candidate.serial_start,
        )
        for candidate in candidates
    )
    ranked_lots = eligible_sources_nearest_prior(lots, target_date)
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    return tuple(by_id[lot.source_id] for lot in ranked_lots)


def _candidate_hash_payload(
    *,
    task_id: str,
    target_date: date,
    requested_qty: int,
    ranked_candidates: Sequence[RankedCandidate],
) -> dict[str, object]:
    return {
        "task_id": task_id,
        "target_date": target_date.isoformat(),
        "requested_qty": requested_qty,
        "candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "source_date": candidate.source_date.isoformat(),
                "source_row": candidate.source_row,
                "serial_start": candidate.serial_start,
                "available_qty": candidate.available_qty,
            }
            for candidate in ranked_candidates
        ],
    }


def compute_candidate_set_hash(
    *,
    task_id: str,
    target_date: date,
    requested_qty: int,
    ranked_candidates: Sequence[RankedCandidate],
) -> str:
    payload = _candidate_hash_payload(
        task_id=task_id,
        target_date=target_date,
        requested_qty=requested_qty,
        ranked_candidates=ranked_candidates,
    )
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_expected_allocation(
    requested_qty: int,
    ranked_candidates: Sequence[RankedCandidate],
) -> tuple[AllocationSlice, ...]:
    remaining = requested_qty
    result: list[AllocationSlice] = []

    for candidate in ranked_candidates:
        if remaining == 0:
            break
        quantity = min(candidate.available_qty, remaining)
        result.append(
            AllocationSlice(
                candidate_id=candidate.candidate_id,
                allocation_rank=len(result) + 1,
                quantity=quantity,
            )
        )
        remaining -= quantity

    return tuple(result)


def evaluate_ranked_prefix_allocation(
    *,
    task_id: str,
    target_date: date,
    requested_qty: int,
    candidates: Iterable[RankedCandidate],
) -> RankedPrefixDecision:
    """Validate, rank, hash, and build the expected ranked-prefix allocation."""

    materialized = tuple(candidates)
    blockers: list[str] = []

    if not _clean(task_id):
        blockers.append("RANKED_PREFIX:TASK_ID_MISSING")
    if type(target_date) is not date:
        blockers.append("RANKED_PREFIX:TARGET_DATE_INVALID")
    if not _positive_int(requested_qty):
        blockers.append("RANKED_PREFIX:REQUESTED_QTY_INVALID")
    if not materialized:
        blockers.append("RANKED_PREFIX:CANDIDATES_EMPTY")

    if type(target_date) is date:
        for candidate in materialized:
            blockers.extend(_candidate_blockers(candidate, target_date))

    blockers.extend(_duplicate_id_blockers(materialized))
    blockers.extend(_ambiguous_rank_blockers(materialized))

    if blockers:
        return RankedPrefixDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            candidate_set_hash=None,
            ranked_candidate_ids=(),
            expected_allocation=(),
        )

    ranked = _canonical_rank_candidates(materialized, target_date)

    if len(ranked) != len(materialized):
        return RankedPrefixDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=("RANKED_PREFIX:CANONICAL_SET_CHANGED",),
            candidate_set_hash=None,
            ranked_candidate_ids=(),
            expected_allocation=(),
        )

    candidate_hash = compute_candidate_set_hash(
        task_id=task_id,
        target_date=target_date,
        requested_qty=requested_qty,
        ranked_candidates=ranked,
    )

    if sum(candidate.available_qty for candidate in ranked) < requested_qty:
        return RankedPrefixDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=("RANKED_PREFIX:INSUFFICIENT_QTY",),
            candidate_set_hash=candidate_hash,
            ranked_candidate_ids=tuple(
                candidate.candidate_id for candidate in ranked
            ),
            expected_allocation=(),
        )

    allocation = _build_expected_allocation(requested_qty, ranked)
    return RankedPrefixDecision(
        status=PASS,
        ready=True,
        blocking_reasons=(),
        candidate_set_hash=candidate_hash,
        ranked_candidate_ids=tuple(
            candidate.candidate_id for candidate in ranked
        ),
        expected_allocation=allocation,
    )


def verify_ranked_prefix_allocation(
    *,
    task_id: str,
    target_date: date,
    requested_qty: int,
    candidates: Iterable[RankedCandidate],
    proposed_allocation: Sequence[AllocationSlice],
) -> ValidationDecision:
    """Independently recompute ranked-prefix allocation.

    This function deliberately does not call evaluate_ranked_prefix_allocation,
    _canonical_rank_candidates, eligible_sources_nearest_prior, or
    _build_expected_allocation.
    """

    materialized = tuple(candidates)
    blockers: list[str] = []

    if not isinstance(task_id, str) or not task_id.strip():
        blockers.append("RANKED_PREFIX:TASK_ID_MISSING")
    if type(target_date) is not date:
        blockers.append("RANKED_PREFIX:TARGET_DATE_INVALID")
    if not isinstance(requested_qty, int) or isinstance(requested_qty, bool) or requested_qty <= 0:
        blockers.append("RANKED_PREFIX:REQUESTED_QTY_INVALID")
    if not materialized:
        blockers.append("RANKED_PREFIX:CANDIDATES_EMPTY")

    seen: set[str] = set()
    rank_keys: dict[tuple[int, int, int], list[str]] = {}

    if type(target_date) is date:
        for candidate in materialized:
            label = candidate.candidate_id or "<blank>"
            if not isinstance(candidate.candidate_id, str) or not candidate.candidate_id.strip():
                blockers.append("RANKED_PREFIX:CANDIDATE_ID_MISSING")
            if candidate.candidate_id in seen:
                blockers.append(
                    f"RANKED_PREFIX:DUPLICATE_CANDIDATE_ID:{candidate.candidate_id}"
                )
            seen.add(candidate.candidate_id)

            if type(candidate.source_date) is not date:
                blockers.append(f"RANKED_PREFIX:SOURCE_DATE_INVALID:{label}")
                continue
            if candidate.source_date > target_date:
                blockers.append(f"RANKED_PREFIX:FUTURE_SOURCE:{label}")

            if (
                not isinstance(candidate.source_row, int)
                or isinstance(candidate.source_row, bool)
                or candidate.source_row <= 0
            ):
                blockers.append(f"RANKED_PREFIX:SOURCE_ROW_INVALID:{label}")

            if (
                not isinstance(candidate.serial_start, str)
                or not candidate.serial_start
                or not candidate.serial_start.isdigit()
            ):
                blockers.append(f"RANKED_PREFIX:SERIAL_START_INVALID:{label}")
                serial_key = None
            else:
                serial_key = int(candidate.serial_start)

            if (
                not isinstance(candidate.available_qty, int)
                or isinstance(candidate.available_qty, bool)
                or candidate.available_qty <= 0
            ):
                blockers.append(f"RANKED_PREFIX:AVAILABLE_QTY_INVALID:{label}")

            if (
                serial_key is not None
                and isinstance(candidate.source_row, int)
                and not isinstance(candidate.source_row, bool)
                and candidate.source_row > 0
            ):
                key = (
                    -candidate.source_date.toordinal(),
                    candidate.source_row,
                    serial_key,
                )
                rank_keys.setdefault(key, []).append(candidate.candidate_id)

    for ids in rank_keys.values():
        if len(ids) > 1:
            blockers.append(
                "RANKED_PREFIX:AMBIGUOUS_RANK_KEY:"
                + ",".join(sorted(ids))
            )

    if blockers:
        return ValidationDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
        )

    ranked = sorted(
        materialized,
        key=lambda candidate: (
            -candidate.source_date.toordinal(),
            candidate.source_row,
            int(candidate.serial_start),
        ),
    )

    if sum(candidate.available_qty for candidate in ranked) < requested_qty:
        return ValidationDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=("RANKED_PREFIX:INSUFFICIENT_QTY",),
        )

    remaining = requested_qty
    expected: list[AllocationSlice] = []
    for candidate in ranked:
        if remaining == 0:
            break
        quantity = min(candidate.available_qty, remaining)
        expected.append(
            AllocationSlice(
                candidate_id=candidate.candidate_id,
                allocation_rank=len(expected) + 1,
                quantity=quantity,
            )
        )
        remaining -= quantity

    if tuple(proposed_allocation) != tuple(expected):
        return ValidationDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=("RANKED_PREFIX:INDEPENDENT_VERIFIER_FAIL",),
        )

    return ValidationDecision(status=PASS, ready=True, blocking_reasons=())


def build_source_rank_lineage(
    *,
    task_id: str,
    decision: RankedPrefixDecision,
    source_rank_gate_id: str,
) -> SourceRankLineage:
    if not decision.ready or decision.candidate_set_hash is None:
        raise ValueError("source-rank lineage requires a PASS decision")
    if not _clean(task_id):
        raise ValueError("task_id must be non-empty")
    if not _clean(source_rank_gate_id):
        raise ValueError("source_rank_gate_id must be non-empty")

    return SourceRankLineage(
        task_id=task_id,
        source_rank_gate_id=source_rank_gate_id,
        candidate_set_hash=decision.candidate_set_hash,
        ranked_candidate_ids=decision.ranked_candidate_ids,
    )


def validate_source_rank_lineage(
    *,
    task_id: str,
    decision: RankedPrefixDecision,
    lineage: SourceRankLineage,
) -> ValidationDecision:
    blockers: list[str] = []

    if not decision.ready or decision.candidate_set_hash is None:
        blockers.append("RANKED_PREFIX:SOURCE_RANK_NOT_PASS")
    else:
        if lineage.task_id != task_id:
            blockers.append("RANKED_PREFIX:LINEAGE_TASK_MISMATCH")
        if not _clean(lineage.source_rank_gate_id):
            blockers.append("RANKED_PREFIX:LINEAGE_GATE_ID_MISSING")
        if lineage.candidate_set_hash != decision.candidate_set_hash:
            blockers.append("RANKED_PREFIX:CANDIDATE_HASH_MISMATCH")
        if lineage.ranked_candidate_ids != decision.ranked_candidate_ids:
            blockers.append("RANKED_PREFIX:RANKED_LINEAGE_MISMATCH")

    if blockers:
        return ValidationDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
        )
    return ValidationDecision(status=PASS, ready=True, blocking_reasons=())


def build_allocation_plan(
    *,
    task_id: str,
    decision: RankedPrefixDecision,
    source_rank_gate_id: str,
    state: str = "PLANNED",
) -> tuple[AllocationPlanRow, ...]:
    if not decision.ready or decision.candidate_set_hash is None:
        raise ValueError("allocation plan requires a PASS decision")
    if not _clean(task_id):
        raise ValueError("task_id must be non-empty")
    if not _clean(source_rank_gate_id):
        raise ValueError("source_rank_gate_id must be non-empty")
    if state not in _ALLOWED_PLAN_STATES:
        raise ValueError(f"unsupported allocation state: {state!r}")

    return tuple(
        AllocationPlanRow(
            task_id=task_id,
            source_rank_gate_id=source_rank_gate_id,
            candidate_set_hash=decision.candidate_set_hash,
            allocation_rank=item.allocation_rank,
            candidate_id=item.candidate_id,
            planned_quantity=item.quantity,
            state=state,
        )
        for item in decision.expected_allocation
    )


def validate_allocation_plan_lineage(
    *,
    task_id: str,
    decision: RankedPrefixDecision,
    lineage: SourceRankLineage,
    plan_rows: Sequence[AllocationPlanRow],
) -> ValidationDecision:
    blockers = list(
        validate_source_rank_lineage(
            task_id=task_id,
            decision=decision,
            lineage=lineage,
        ).blocking_reasons
    )

    if not plan_rows:
        blockers.append("RANKED_PREFIX:ALLOCATION_PLAN_EMPTY")

    expected = decision.expected_allocation if decision.ready else ()
    if len(plan_rows) != len(expected):
        blockers.append("RANKED_PREFIX:ALLOCATION_PLAN_LENGTH_MISMATCH")

    for index, row in enumerate(plan_rows):
        if row.task_id != task_id:
            blockers.append("RANKED_PREFIX:PLAN_TASK_MISMATCH")
        if row.source_rank_gate_id != lineage.source_rank_gate_id:
            blockers.append("RANKED_PREFIX:PLAN_GATE_MISMATCH")
        if row.candidate_set_hash != lineage.candidate_set_hash:
            blockers.append("RANKED_PREFIX:PLAN_CANDIDATE_HASH_MISMATCH")
        if row.allocation_rank != index + 1:
            blockers.append("RANKED_PREFIX:PLAN_RANK_SEQUENCE_INVALID")
        if row.state not in _ALLOWED_PLAN_STATES:
            blockers.append("RANKED_PREFIX:PLAN_STATE_INVALID")
        if not _positive_int(row.planned_quantity):
            blockers.append("RANKED_PREFIX:PLAN_QTY_INVALID")

        if index < len(expected):
            expected_row = expected[index]
            if row.candidate_id != expected_row.candidate_id:
                blockers.append("RANKED_PREFIX:PLAN_CANDIDATE_RANK_MISMATCH")
            if row.planned_quantity != expected_row.quantity:
                blockers.append("RANKED_PREFIX:PLAN_QTY_MISMATCH")

    if blockers:
        return ValidationDecision(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
        )
    return ValidationDecision(status=PASS, ready=True, blocking_reasons=())


def compute_allocation_plan_hash(
    *,
    task_id: str,
    decision: RankedPrefixDecision,
    lineage: SourceRankLineage,
    plan_rows: Sequence[AllocationPlanRow],
) -> str:
    """Hash only a lineage-valid allocation plan.

    The hash is suitable for binding downstream dry-run contracts to the exact
    validated plan. Invalid plans raise instead of producing a trusted hash.
    """

    validation = validate_allocation_plan_lineage(
        task_id=task_id,
        decision=decision,
        lineage=lineage,
        plan_rows=plan_rows,
    )
    if not validation.ready:
        raise ValueError(
            "allocation plan hash requires PASS lineage validation: "
            + ",".join(validation.blocking_reasons)
        )

    payload = {
        "task_id": task_id,
        "source_rank_gate_id": lineage.source_rank_gate_id,
        "candidate_set_hash": lineage.candidate_set_hash,
        "rows": [
            {
                "allocation_rank": row.allocation_rank,
                "candidate_id": row.candidate_id,
                "planned_quantity": row.planned_quantity,
                "state": row.state,
            }
            for row in plan_rows
        ],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
