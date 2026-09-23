from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
import unittest

from scripts.materialized_lineage_replay_v0_1 import (
    CANDIDATE_SCOPE,
    HASH_MATCH,
    HASH_MISMATCH,
    HASH_MISSING,
    HASH_NOT_COMPARABLE,
    HOLD,
    MATCH,
    NOT_REPLAYABLE,
    HistoricalLineageEvidence,
    MaterializedLineageReplaySnapshot,
    ReplayTransaction,
    SourceLedgerSnapshot,
    replay_materialized_lineage,
)
from scripts.ranked_prefix_allocation_lineage_v0_1 import (
    CANDIDATE_SET_HASH_ALGORITHM,
    RankedCandidate,
    evaluate_ranked_prefix_allocation,
)


DOC_DATE = date(2026, 9, 11)


def transaction(*, requested_qty: int = 100) -> ReplayTransaction:
    return ReplayTransaction(
        task_id="TASK-REPLAY-A",
        document_date=DOC_DATE,
        requested_qty=requested_qty,
    )


def source(
    source_id: str,
    *,
    source_date: date = date(2026, 9, 10),
    source_row: int = 10,
    serial_start: str = "00100",
    inbound_qty: int = 100,
    prior_out_qty: int = 0,
    serial_lineage_verified: bool = True,
) -> SourceLedgerSnapshot:
    return SourceLedgerSnapshot(
        source_id=source_id,
        source_date=source_date,
        source_row=source_row,
        pre_transaction_serial_start=serial_start,
        inbound_qty=inbound_qty,
        prior_committed_out_qty=prior_out_qty,
        serial_lineage_verified=serial_lineage_verified,
    )


def historical(
    *,
    ranked=("SRC-A",),
    selected=("SRC-A",),
    quantities=(100,),
    candidate_count=1,
    historical_hash=None,
    historical_algorithm=None,
    **overrides,
) -> HistoricalLineageEvidence:
    values = {
        "candidate_scope": CANDIDATE_SCOPE,
        "transaction_closed": True,
        "transaction_readback_pass": True,
        "source_rank_lineage_verified": True,
        "source_rank_readback_pass": True,
        "plan_lineage_verified": True,
        "candidate_count": candidate_count,
        "ranked_source_ids": tuple(ranked),
        "selected_source_ids": tuple(selected),
        "allocation_quantities": tuple(quantities),
        "historical_candidate_set_hash": historical_hash,
        "historical_hash_algorithm": historical_algorithm,
    }
    values.update(overrides)
    return HistoricalLineageEvidence(**values)


def snapshot(
    *,
    tx=None,
    sources=None,
    evidence=None,
) -> MaterializedLineageReplaySnapshot:
    return MaterializedLineageReplaySnapshot(
        replay_id="REPLAY-A",
        transaction=transaction() if tx is None else tx,
        sources=(source("SRC-A"),) if sources is None else tuple(sources),
        historical=historical() if evidence is None else evidence,
    )


def canonical_hash(tx, sources):
    candidates = tuple(
        RankedCandidate(
            candidate_id=item.source_id,
            source_date=item.source_date,
            source_row=item.source_row,
            serial_start=item.pre_transaction_serial_start,
            available_qty=item.inbound_qty - item.prior_committed_out_qty,
        )
        for item in sources
    )
    result = evaluate_ranked_prefix_allocation(
        task_id=tx.task_id,
        target_date=tx.document_date,
        requested_qty=tx.requested_qty,
        candidates=candidates,
    )
    assert result.candidate_set_hash is not None
    return result.candidate_set_hash


class MaterializedLineageReplayTests(unittest.TestCase):
    def test_single_source_full_consume_matches(self) -> None:
        result = replay_materialized_lineage(snapshot())
        self.assertEqual(result.status, MATCH)
        self.assertTrue(result.ready)
        self.assertEqual(
            result.reconstructed_available_qty,
            (("SRC-A", 100),),
        )
        self.assertEqual(result.hash_status, HASH_MISSING)

    def test_prior_out_reconstruction_matches(self) -> None:
        sources = (
            source(
                "SRC-NEW",
                source_date=date(2026, 9, 10),
                source_row=20,
                serial_start="01000",
                inbound_qty=4000,
            ),
            source(
                "SRC-OLD",
                source_date=date(2026, 9, 7),
                source_row=10,
                serial_start="02000",
                inbound_qty=500,
                prior_out_qty=19,
            ),
        )
        evidence = historical(
            ranked=("SRC-NEW", "SRC-OLD"),
            selected=("SRC-NEW", "SRC-OLD"),
            quantities=(4000, 100),
            candidate_count=2,
        )
        result = replay_materialized_lineage(
            snapshot(
                tx=transaction(requested_qty=4100),
                sources=sources,
                evidence=evidence,
            )
        )
        self.assertEqual(result.status, MATCH)
        self.assertEqual(
            result.reconstructed_available_qty,
            (("SRC-NEW", 4000), ("SRC-OLD", 481)),
        )

    def test_unverified_serial_lineage_is_not_replayable(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                sources=(
                    source("SRC-A", serial_lineage_verified=False),
                )
            )
        )
        self.assertEqual(result.status, NOT_REPLAYABLE)
        self.assertIn(
            "LINEAGE_REPLAY:SERIAL_LINEAGE_NOT_VERIFIED:SRC-A",
            result.blocking_reasons,
        )

    def test_prior_out_exceeding_inbound_is_not_replayable(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                sources=(
                    source(
                        "SRC-A",
                        inbound_qty=100,
                        prior_out_qty=101,
                    ),
                )
            )
        )
        self.assertIn(
            "LINEAGE_REPLAY:PRIOR_OUT_EXCEEDS_INBOUND:SRC-A",
            result.blocking_reasons,
        )

    def test_zero_reconstructed_availability_is_not_replayable(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                sources=(
                    source(
                        "SRC-A",
                        inbound_qty=100,
                        prior_out_qty=100,
                    ),
                )
            )
        )
        self.assertIn(
            "LINEAGE_REPLAY:RECONSTRUCTED_QTY_NOT_POSITIVE:SRC-A",
            result.blocking_reasons,
        )

    def test_cross_year_source_is_not_replayable(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                sources=(
                    source(
                        "SRC-A",
                        source_date=date(2025, 12, 31),
                    ),
                )
            )
        )
        self.assertIn(
            "LINEAGE_REPLAY:SOURCE_YEAR_MISMATCH:SRC-A",
            result.blocking_reasons,
        )

    def test_future_same_year_source_is_not_replayable(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                sources=(
                    source(
                        "SRC-A",
                        source_date=date(2026, 9, 12),
                    ),
                )
            )
        )
        self.assertIn(
            "LINEAGE_REPLAY:FUTURE_SOURCE:SRC-A",
            result.blocking_reasons,
        )

    def test_datetime_document_date_is_rejected(self) -> None:
        bad_tx = replace(
            transaction(),
            document_date=datetime(2026, 9, 11, 8, 0),
        )
        result = replay_materialized_lineage(snapshot(tx=bad_tx))
        self.assertIn(
            "LINEAGE_REPLAY:DOCUMENT_DATE_INVALID",
            result.blocking_reasons,
        )

    def test_boolean_prior_out_is_rejected(self) -> None:
        bad = replace(
            source("SRC-A"),
            prior_committed_out_qty=True,
        )
        result = replay_materialized_lineage(snapshot(sources=(bad,)))
        self.assertIn(
            "LINEAGE_REPLAY:PRIOR_OUT_QTY_INVALID:SRC-A",
            result.blocking_reasons,
        )

    def test_candidate_scope_is_locked(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                evidence=historical(
                    candidate_scope="GLOBAL_DISCOVERY",
                )
            )
        )
        self.assertIn(
            "LINEAGE_REPLAY:CANDIDATE_SCOPE_INVALID",
            result.blocking_reasons,
        )

    def test_rank_mismatch_holds(self) -> None:
        sources = (
            source(
                "SRC-NEW",
                source_date=date(2026, 9, 10),
                source_row=20,
                serial_start="01000",
            ),
            source(
                "SRC-OLD",
                source_date=date(2026, 9, 7),
                source_row=10,
                serial_start="02000",
            ),
        )
        evidence = historical(
            ranked=("SRC-OLD", "SRC-NEW"),
            selected=("SRC-OLD",),
            quantities=(100,),
            candidate_count=2,
        )
        result = replay_materialized_lineage(
            snapshot(sources=sources, evidence=evidence)
        )
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "LINEAGE_REPLAY:RANKED_SOURCE_IDS_MISMATCH",
            result.blocking_reasons,
        )

    def test_allocation_quantity_mismatch_holds(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                evidence=historical(quantities=(99,))
            )
        )
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "LINEAGE_REPLAY:ALLOCATION_QUANTITIES_MISMATCH",
            result.blocking_reasons,
        )

    def test_comparable_candidate_hash_match_is_reported(self) -> None:
        tx = transaction()
        sources = (source("SRC-A"),)
        digest = canonical_hash(tx, sources)
        evidence = historical(
            historical_hash=digest,
            historical_algorithm=CANDIDATE_SET_HASH_ALGORITHM,
        )
        result = replay_materialized_lineage(
            snapshot(tx=tx, sources=sources, evidence=evidence)
        )
        self.assertEqual(result.status, MATCH)
        self.assertEqual(result.hash_status, HASH_MATCH)

    def test_comparable_candidate_hash_mismatch_holds(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                evidence=historical(
                    historical_hash="0" * 64,
                    historical_algorithm=CANDIDATE_SET_HASH_ALGORITHM,
                )
            )
        )
        self.assertEqual(result.status, HOLD)
        self.assertEqual(result.hash_status, HASH_MISMATCH)
        self.assertIn(
            "LINEAGE_REPLAY:CANDIDATE_SET_HASH_MISMATCH",
            result.blocking_reasons,
        )

    def test_noncomparable_hash_does_not_claim_hash_match(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                evidence=historical(
                    historical_hash="opaque-historical-hash",
                    historical_algorithm="OTHER_ALGORITHM",
                )
            )
        )
        self.assertEqual(result.status, MATCH)
        self.assertEqual(result.hash_status, HASH_NOT_COMPARABLE)

    def test_malformed_comparable_hash_is_not_replayable(self) -> None:
        result = replay_materialized_lineage(
            snapshot(
                evidence=historical(
                    historical_hash="not-a-sha256",
                    historical_algorithm=CANDIDATE_SET_HASH_ALGORITHM,
                )
            )
        )
        self.assertEqual(result.status, NOT_REPLAYABLE)
        self.assertIn(
            "LINEAGE_REPLAY:COMPARABLE_HISTORICAL_HASH_INVALID",
            result.blocking_reasons,
        )


if __name__ == "__main__":
    unittest.main()
