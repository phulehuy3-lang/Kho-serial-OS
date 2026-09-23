"""Pure same-year materialized-lineage replay control.

No external I/O, candidate discovery, or production mutation path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from scripts.ranked_prefix_allocation_lineage_v0_1 import (
    CANDIDATE_SET_HASH_ALGORITHM,
    CANDIDATE_SET_HASH_CONTRACT_ID,
    PASS as RANKED_PREFIX_PASS,
    AllocationSlice,
    RankedCandidate,
    evaluate_ranked_prefix_allocation,
)


MATCH = "MATCH"
HOLD = "HOLD"
NOT_REPLAYABLE = "NOT_REPLAYABLE"

HASH_MATCH = "MATCH"
HASH_MISMATCH = "MISMATCH"
HASH_NOT_COMPARABLE = "NOT_COMPARABLE"
HASH_MISSING = "MISSING"

CANDIDATE_SCOPE = "MATERIALIZED_CANDIDATE_SET_ONLY"


@dataclass(frozen=True, slots=True)
class ReplayTransaction:
    task_id: str
    document_date: date
    requested_qty: int


@dataclass(frozen=True, slots=True)
class SourceLedgerSnapshot:
    source_id: str
    source_date: date
    source_row: int
    pre_transaction_serial_start: str
    inbound_qty: int
    prior_committed_out_qty: int
    serial_lineage_verified: bool


@dataclass(frozen=True, slots=True)
class HistoricalLineageEvidence:
    candidate_scope: str
    transaction_closed: bool
    transaction_readback_pass: bool
    source_rank_lineage_verified: bool
    source_rank_readback_pass: bool
    plan_lineage_verified: bool
    candidate_count: int
    ranked_source_ids: tuple[str, ...]
    selected_source_ids: tuple[str, ...]
    allocation_quantities: tuple[int, ...]
    historical_candidate_set_hash: str | None = None
    historical_hash_algorithm: str | None = None
    historical_hash_contract_id: str | None = None


@dataclass(frozen=True, slots=True)
class MaterializedLineageReplaySnapshot:
    replay_id: str
    transaction: ReplayTransaction
    sources: tuple[SourceLedgerSnapshot, ...]
    historical: HistoricalLineageEvidence


@dataclass(frozen=True, slots=True)
class MaterializedLineageReplayComparison:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    candidate_scope: str
    hash_status: str
    cryptographic_hash_match_proven: bool
    reconstructed_available_qty: tuple[tuple[str, int], ...]
    kernel_ranked_source_ids: tuple[str, ...]
    kernel_expected_allocation: tuple[AllocationSlice, ...]
    kernel_candidate_set_hash: str | None


def _clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_id_tuple(values: object, *, nonempty: bool = True) -> bool:
    if not isinstance(values, tuple):
        return False
    if nonempty and not values:
        return False
    if any(not _clean(value) for value in values):
        return False
    return len(set(values)) == len(values)


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(char in "0123456789abcdef" for char in value)


def _replayability_blockers(
    snapshot: MaterializedLineageReplaySnapshot,
) -> tuple[str, ...]:
    tx = snapshot.transaction
    evidence = snapshot.historical
    blockers: list[str] = []

    if not _clean(snapshot.replay_id):
        blockers.append("LINEAGE_REPLAY:REPLAY_ID_MISSING")
    if not _clean(tx.task_id):
        blockers.append("LINEAGE_REPLAY:TASK_ID_MISSING")
    if type(tx.document_date) is not date:
        blockers.append("LINEAGE_REPLAY:DOCUMENT_DATE_INVALID")
    if not _positive_int(tx.requested_qty):
        blockers.append("LINEAGE_REPLAY:REQUESTED_QTY_INVALID")

    if evidence.candidate_scope != CANDIDATE_SCOPE:
        blockers.append("LINEAGE_REPLAY:CANDIDATE_SCOPE_INVALID")
    if evidence.transaction_closed is not True:
        blockers.append("LINEAGE_REPLAY:TRANSACTION_NOT_CLOSED")
    if evidence.transaction_readback_pass is not True:
        blockers.append("LINEAGE_REPLAY:TRANSACTION_READBACK_NOT_PASS")
    if evidence.source_rank_lineage_verified is not True:
        blockers.append("LINEAGE_REPLAY:SOURCE_RANK_LINEAGE_NOT_VERIFIED")
    if evidence.source_rank_readback_pass is not True:
        blockers.append("LINEAGE_REPLAY:SOURCE_RANK_READBACK_NOT_PASS")
    if evidence.plan_lineage_verified is not True:
        blockers.append("LINEAGE_REPLAY:PLAN_LINEAGE_NOT_VERIFIED")
    if not _positive_int(evidence.candidate_count):
        blockers.append("LINEAGE_REPLAY:CANDIDATE_COUNT_INVALID")

    if not _valid_id_tuple(evidence.ranked_source_ids):
        blockers.append("LINEAGE_REPLAY:RANKED_SOURCE_IDS_INVALID")
    if not _valid_id_tuple(evidence.selected_source_ids):
        blockers.append("LINEAGE_REPLAY:SELECTED_SOURCE_IDS_INVALID")

    if not isinstance(evidence.allocation_quantities, tuple):
        blockers.append("LINEAGE_REPLAY:ALLOCATION_QUANTITIES_INVALID")
    elif (
        not evidence.allocation_quantities
        or any(not _positive_int(q) for q in evidence.allocation_quantities)
    ):
        blockers.append("LINEAGE_REPLAY:ALLOCATION_QUANTITIES_INVALID")

    if (
        isinstance(evidence.selected_source_ids, tuple)
        and isinstance(evidence.allocation_quantities, tuple)
        and len(evidence.selected_source_ids)
        != len(evidence.allocation_quantities)
    ):
        blockers.append("LINEAGE_REPLAY:SELECTION_QUANTITY_LENGTH_MISMATCH")

    if (
        _positive_int(tx.requested_qty)
        and isinstance(evidence.allocation_quantities, tuple)
        and evidence.allocation_quantities
        and all(_positive_int(q) for q in evidence.allocation_quantities)
        and sum(evidence.allocation_quantities) != tx.requested_qty
    ):
        blockers.append(
            "LINEAGE_REPLAY:HISTORICAL_ALLOCATION_TOTAL_MISMATCH"
        )

    if (
        _positive_int(evidence.candidate_count)
        and isinstance(evidence.ranked_source_ids, tuple)
        and evidence.candidate_count != len(evidence.ranked_source_ids)
    ):
        blockers.append("LINEAGE_REPLAY:CANDIDATE_COUNT_MISMATCH")

    if not snapshot.sources:
        blockers.append("LINEAGE_REPLAY:SOURCES_EMPTY")

    source_ids = tuple(source.source_id for source in snapshot.sources)
    if not _valid_id_tuple(source_ids):
        blockers.append("LINEAGE_REPLAY:SOURCE_IDS_INVALID")

    if (
        _positive_int(evidence.candidate_count)
        and evidence.candidate_count != len(snapshot.sources)
    ):
        blockers.append("LINEAGE_REPLAY:SOURCE_SNAPSHOT_COUNT_MISMATCH")

    if (
        _valid_id_tuple(evidence.ranked_source_ids)
        and _valid_id_tuple(source_ids)
        and set(evidence.ranked_source_ids) != set(source_ids)
    ):
        blockers.append("LINEAGE_REPLAY:RANKED_SOURCE_SET_MISMATCH")

    if (
        _valid_id_tuple(evidence.selected_source_ids)
        and _valid_id_tuple(source_ids)
        and any(
            source_id not in set(source_ids)
            for source_id in evidence.selected_source_ids
        )
    ):
        blockers.append("LINEAGE_REPLAY:SELECTED_SOURCE_NOT_IN_SET")

    if type(tx.document_date) is date:
        for source in snapshot.sources:
            label = source.source_id or "<blank>"

            if not _clean(source.source_id):
                blockers.append("LINEAGE_REPLAY:SOURCE_ID_MISSING")
            if type(source.source_date) is not date:
                blockers.append(
                    f"LINEAGE_REPLAY:SOURCE_DATE_INVALID:{label}"
                )
            else:
                if source.source_date.year != tx.document_date.year:
                    blockers.append(
                        f"LINEAGE_REPLAY:SOURCE_YEAR_MISMATCH:{label}"
                    )
                if source.source_date > tx.document_date:
                    blockers.append(
                        f"LINEAGE_REPLAY:FUTURE_SOURCE:{label}"
                    )

            if not _positive_int(source.source_row):
                blockers.append(
                    f"LINEAGE_REPLAY:SOURCE_ROW_INVALID:{label}"
                )
            if (
                not isinstance(source.pre_transaction_serial_start, str)
                or not source.pre_transaction_serial_start
                or not source.pre_transaction_serial_start.isdigit()
            ):
                blockers.append(
                    f"LINEAGE_REPLAY:SERIAL_START_INVALID:{label}"
                )
            if source.serial_lineage_verified is not True:
                blockers.append(
                    f"LINEAGE_REPLAY:SERIAL_LINEAGE_NOT_VERIFIED:{label}"
                )
            if not _positive_int(source.inbound_qty):
                blockers.append(
                    f"LINEAGE_REPLAY:INBOUND_QTY_INVALID:{label}"
                )
            if not _non_negative_int(source.prior_committed_out_qty):
                blockers.append(
                    f"LINEAGE_REPLAY:PRIOR_OUT_QTY_INVALID:{label}"
                )
            if (
                _positive_int(source.inbound_qty)
                and _non_negative_int(source.prior_committed_out_qty)
            ):
                if source.prior_committed_out_qty > source.inbound_qty:
                    blockers.append(
                        f"LINEAGE_REPLAY:PRIOR_OUT_EXCEEDS_INBOUND:{label}"
                    )
                elif (
                    source.inbound_qty - source.prior_committed_out_qty
                    <= 0
                ):
                    blockers.append(
                        f"LINEAGE_REPLAY:RECONSTRUCTED_QTY_NOT_POSITIVE:{label}"
                    )

    historical_hash = evidence.historical_candidate_set_hash
    historical_algorithm = evidence.historical_hash_algorithm

    if (
        historical_hash is not None
        and historical_algorithm == CANDIDATE_SET_HASH_ALGORITHM
        and evidence.historical_hash_contract_id
        == CANDIDATE_SET_HASH_CONTRACT_ID
        and not _is_sha256(historical_hash)
    ):
        blockers.append(
            "LINEAGE_REPLAY:COMPARABLE_HISTORICAL_HASH_INVALID"
        )

    return tuple(sorted(set(blockers)))


def _reconstructed_available(
    sources: tuple[SourceLedgerSnapshot, ...],
) -> tuple[tuple[str, int], ...]:
    return tuple(
        (
            source.source_id,
            source.inbound_qty - source.prior_committed_out_qty,
        )
        for source in sources
        if (
            _positive_int(source.inbound_qty)
            and _non_negative_int(source.prior_committed_out_qty)
            and source.prior_committed_out_qty < source.inbound_qty
        )
    )


def _reconstruct_candidates(
    sources: tuple[SourceLedgerSnapshot, ...],
) -> tuple[RankedCandidate, ...]:
    return tuple(
        RankedCandidate(
            candidate_id=source.source_id,
            source_date=source.source_date,
            source_row=source.source_row,
            serial_start=source.pre_transaction_serial_start,
            available_qty=(
                source.inbound_qty - source.prior_committed_out_qty
            ),
        )
        for source in sources
    )


def _hash_status(
    evidence: HistoricalLineageEvidence,
    kernel_hash: str | None,
) -> tuple[str, tuple[str, ...]]:
    historical_hash = evidence.historical_candidate_set_hash

    if historical_hash is None:
        return HASH_MISSING, ()

    if (
        evidence.historical_hash_algorithm != CANDIDATE_SET_HASH_ALGORITHM
        or evidence.historical_hash_contract_id
        != CANDIDATE_SET_HASH_CONTRACT_ID
    ):
        return HASH_NOT_COMPARABLE, ()

    if kernel_hash == historical_hash:
        return HASH_MATCH, ()

    return (
        HASH_MISMATCH,
        ("LINEAGE_REPLAY:CANDIDATE_SET_HASH_MISMATCH",),
    )


def replay_materialized_lineage(
    snapshot: MaterializedLineageReplaySnapshot,
) -> MaterializedLineageReplayComparison:
    """Replay one same-year historical decision from materialized lineage."""

    evidence = snapshot.historical
    reconstructed = _reconstructed_available(snapshot.sources)
    blockers = list(_replayability_blockers(snapshot))

    if blockers:
        return MaterializedLineageReplayComparison(
            status=NOT_REPLAYABLE,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            candidate_scope=evidence.candidate_scope,
            hash_status=(
                HASH_MISSING
                if evidence.historical_candidate_set_hash is None
                else HASH_NOT_COMPARABLE
            ),
            cryptographic_hash_match_proven=False,
            reconstructed_available_qty=reconstructed,
            kernel_ranked_source_ids=(),
            kernel_expected_allocation=(),
            kernel_candidate_set_hash=None,
        )

    decision = evaluate_ranked_prefix_allocation(
        task_id=snapshot.transaction.task_id,
        target_date=snapshot.transaction.document_date,
        requested_qty=snapshot.transaction.requested_qty,
        candidates=_reconstruct_candidates(snapshot.sources),
    )

    if decision.status != RANKED_PREFIX_PASS or not decision.ready:
        blockers.extend(
            f"LINEAGE_REPLAY:KERNEL:{reason}"
            for reason in decision.blocking_reasons
        )

    if decision.ranked_candidate_ids != evidence.ranked_source_ids:
        blockers.append("LINEAGE_REPLAY:RANKED_SOURCE_IDS_MISMATCH")

    selected = tuple(
        item.candidate_id for item in decision.expected_allocation
    )
    if selected != evidence.selected_source_ids:
        blockers.append("LINEAGE_REPLAY:SELECTED_SOURCE_IDS_MISMATCH")

    quantities = tuple(
        item.quantity for item in decision.expected_allocation
    )
    if quantities != evidence.allocation_quantities:
        blockers.append("LINEAGE_REPLAY:ALLOCATION_QUANTITIES_MISMATCH")

    hash_status, hash_blockers = _hash_status(
        evidence,
        decision.candidate_set_hash,
    )
    blockers.extend(hash_blockers)

    if blockers:
        return MaterializedLineageReplayComparison(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            candidate_scope=evidence.candidate_scope,
            hash_status=hash_status,
            cryptographic_hash_match_proven=(hash_status == HASH_MATCH),
            reconstructed_available_qty=reconstructed,
            kernel_ranked_source_ids=decision.ranked_candidate_ids,
            kernel_expected_allocation=decision.expected_allocation,
            kernel_candidate_set_hash=decision.candidate_set_hash,
        )

    return MaterializedLineageReplayComparison(
        status=MATCH,
        ready=True,
        blocking_reasons=(),
        candidate_scope=evidence.candidate_scope,
        hash_status=hash_status,
        cryptographic_hash_match_proven=(hash_status == HASH_MATCH),
        reconstructed_available_qty=reconstructed,
        kernel_ranked_source_ids=decision.ranked_candidate_ids,
        kernel_expected_allocation=decision.expected_allocation,
        kernel_candidate_set_hash=decision.candidate_set_hash,
    )
