from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
import unittest
from unittest.mock import patch

from scripts.ranked_prefix_allocation_lineage_v0_1 import (
    ALLOCATION_PLAN_HASH_CONTRACT_ID,
    CANDIDATE_SET_HASH_CONTRACT_ID,
    HOLD,
    PASS,
    AllocationSlice,
    RankedCandidate,
    build_allocation_plan,
    build_source_rank_lineage,
    compute_allocation_plan_hash,
    evaluate_ranked_prefix_allocation,
    validate_allocation_plan_lineage,
    validate_source_rank_lineage,
    verify_ranked_prefix_allocation,
)


TARGET = date(2026, 2, 15)


def candidate(
    candidate_id: str,
    *,
    source_date: date = TARGET,
    source_row: int = 1,
    serial_start: str = "00100",
    available_qty: int = 60,
) -> RankedCandidate:
    return RankedCandidate(
        candidate_id=candidate_id,
        source_date=source_date,
        source_row=source_row,
        serial_start=serial_start,
        available_qty=available_qty,
    )


def evaluate(
    candidates,
    *,
    requested_qty: int = 100,
):
    return evaluate_ranked_prefix_allocation(
        task_id="TASK-SYNTH-A",
        target_date=TARGET,
        requested_qty=requested_qty,
        candidates=candidates,
    )


class RankedPrefixDecisionTests(unittest.TestCase):
    def test_ranked_prefix_spans_sources(self) -> None:
        decision = evaluate(
            (
                candidate("A", available_qty=60),
                candidate(
                    "B",
                    source_row=2,
                    serial_start="00200",
                    available_qty=60,
                ),
            )
        )
        self.assertEqual(decision.status, PASS)
        self.assertEqual(
            decision.expected_allocation,
            (
                AllocationSlice("A", 1, 60),
                AllocationSlice("B", 2, 40),
            ),
        )

    def test_final_source_may_be_partially_consumed(self) -> None:
        decision = evaluate(
            (
                candidate("A", available_qty=100),
                candidate(
                    "B",
                    source_row=2,
                    serial_start="00200",
                    available_qty=100,
                ),
            ),
            requested_qty=125,
        )
        self.assertEqual(decision.expected_allocation[-1].quantity, 25)

    def test_input_order_does_not_change_rank_or_hash(self) -> None:
        a = candidate("A", available_qty=60)
        b = candidate(
            "B",
            source_row=2,
            serial_start="00200",
            available_qty=60,
        )
        first = evaluate((a, b))
        second = evaluate((b, a))
        self.assertEqual(first.ranked_candidate_ids, second.ranked_candidate_ids)
        self.assertEqual(first.candidate_set_hash, second.candidate_set_hash)

    def test_candidate_hash_contract_id_is_versioned(self) -> None:
        self.assertEqual(
            CANDIDATE_SET_HASH_CONTRACT_ID,
            "RANKED_PREFIX_CANDIDATE_SET_HASH_V1",
        )

    def test_candidate_hash_v1_golden_vector(self) -> None:
        decision = evaluate_ranked_prefix_allocation(
            task_id="TASK-HASH-A",
            target_date=date(2026, 2, 15),
            requested_qty=100,
            candidates=(
                RankedCandidate(
                    "SRC-A",
                    date(2026, 2, 14),
                    1,
                    "00100",
                    60,
                ),
                RankedCandidate(
                    "SRC-B",
                    date(2026, 2, 13),
                    2,
                    "00200",
                    60,
                ),
            ),
        )
        self.assertEqual(
            decision.candidate_set_hash,
            "37184de82ede28fdddc86dcc23dd7f89"
            "b3de35f67ba79ce7665e28cd0a761718",
        )

    def test_nearest_prior_date_ranks_first(self) -> None:
        newer = candidate(
            "NEWER",
            source_date=date(2026, 2, 14),
            source_row=2,
        )
        older = candidate(
            "OLDER",
            source_date=date(2026, 2, 13),
            source_row=1,
            serial_start="00050",
        )
        decision = evaluate((older, newer))
        self.assertEqual(decision.ranked_candidate_ids, ("NEWER", "OLDER"))

    def test_future_candidate_fails_closed(self) -> None:
        decision = evaluate(
            (candidate("FUTURE", source_date=date(2026, 2, 16)),)
        )
        self.assertEqual(decision.status, HOLD)
        self.assertIn(
            "RANKED_PREFIX:FUTURE_SOURCE:FUTURE",
            decision.blocking_reasons,
        )

    def test_duplicate_candidate_id_fails(self) -> None:
        decision = evaluate(
            (
                candidate("DUP"),
                candidate("DUP", source_row=2, serial_start="00200"),
            )
        )
        self.assertTrue(
            any(
                reason.startswith("RANKED_PREFIX:DUPLICATE_CANDIDATE_ID")
                for reason in decision.blocking_reasons
            )
        )

    def test_ambiguous_rank_key_fails(self) -> None:
        decision = evaluate(
            (
                candidate("A", serial_start="00010"),
                candidate("B", serial_start="10"),
            )
        )
        self.assertTrue(
            any(
                reason.startswith("RANKED_PREFIX:AMBIGUOUS_RANK_KEY")
                for reason in decision.blocking_reasons
            )
        )

    def test_malformed_serial_fails(self) -> None:
        decision = evaluate((candidate("A", serial_start="12A"),))
        self.assertIn(
            "RANKED_PREFIX:SERIAL_START_INVALID:A",
            decision.blocking_reasons,
        )

    def test_boolean_quantity_fails(self) -> None:
        decision = evaluate(
            (candidate("A", available_qty=True),)  # type: ignore[arg-type]
        )
        self.assertIn(
            "RANKED_PREFIX:AVAILABLE_QTY_INVALID:A",
            decision.blocking_reasons,
        )

    def test_datetime_source_date_fails(self) -> None:
        decision = evaluate(
            (
                candidate(
                    "A",
                    source_date=datetime(2026, 2, 15, 8, 0),
                ),
            )
        )
        self.assertIn(
            "RANKED_PREFIX:SOURCE_DATE_INVALID:A",
            decision.blocking_reasons,
        )

    def test_insufficient_quantity_holds_but_preserves_hash_and_rank(self) -> None:
        decision = evaluate(
            (
                candidate("A", available_qty=40),
                candidate(
                    "B",
                    source_row=2,
                    serial_start="00200",
                    available_qty=40,
                ),
            ),
            requested_qty=100,
        )
        self.assertEqual(decision.status, HOLD)
        self.assertIn(
            "RANKED_PREFIX:INSUFFICIENT_QTY",
            decision.blocking_reasons,
        )
        self.assertIsNotNone(decision.candidate_set_hash)
        self.assertEqual(decision.ranked_candidate_ids, ("A", "B"))


class IndependentVerifierTests(unittest.TestCase):
    def sources(self):
        return (
            candidate("A", available_qty=60),
            candidate(
                "B",
                source_row=2,
                serial_start="00200",
                available_qty=60,
            ),
        )

    def test_exact_ranked_prefix_passes(self) -> None:
        decision = evaluate(self.sources())
        verified = verify_ranked_prefix_allocation(
            task_id="TASK-SYNTH-A",
            target_date=TARGET,
            requested_qty=100,
            candidates=self.sources(),
            proposed_allocation=decision.expected_allocation,
        )
        self.assertEqual(verified.status, PASS)
        self.assertTrue(verified.ready)

    def test_skipping_higher_ranked_source_fails(self) -> None:
        verified = verify_ranked_prefix_allocation(
            task_id="TASK-SYNTH-A",
            target_date=TARGET,
            requested_qty=100,
            candidates=self.sources(),
            proposed_allocation=(
                AllocationSlice("B", 1, 60),
                AllocationSlice("A", 2, 40),
            ),
        )
        self.assertEqual(verified.status, HOLD)
        self.assertIn(
            "RANKED_PREFIX:INDEPENDENT_VERIFIER_FAIL",
            verified.blocking_reasons,
        )

    def test_verifier_does_not_use_allocator_ranking_path(self) -> None:
        proposed = (
            AllocationSlice("A", 1, 60),
            AllocationSlice("B", 2, 40),
        )
        with patch(
            "scripts.ranked_prefix_allocation_lineage_v0_1."
            "_canonical_rank_candidates",
            side_effect=AssertionError("allocator path must not be called"),
        ):
            verified = verify_ranked_prefix_allocation(
                task_id="TASK-SYNTH-A",
                target_date=TARGET,
                requested_qty=100,
                candidates=self.sources(),
                proposed_allocation=proposed,
            )
        self.assertEqual(verified.status, PASS)

    def test_verifier_rejects_insufficient_quantity(self) -> None:
        verified = verify_ranked_prefix_allocation(
            task_id="TASK-SYNTH-A",
            target_date=TARGET,
            requested_qty=200,
            candidates=self.sources(),
            proposed_allocation=(),
        )
        self.assertIn(
            "RANKED_PREFIX:INSUFFICIENT_QTY",
            verified.blocking_reasons,
        )


class LineageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sources = (
            candidate("A", available_qty=60),
            candidate(
                "B",
                source_row=2,
                serial_start="00200",
                available_qty=60,
            ),
        )
        self.decision = evaluate(self.sources)
        self.lineage = build_source_rank_lineage(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            source_rank_gate_id="GATE-SYNTH-A",
        )

    def test_exact_source_rank_lineage_passes(self) -> None:
        result = validate_source_rank_lineage(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=self.lineage,
        )
        self.assertEqual(result.status, PASS)

    def test_candidate_hash_mismatch_holds(self) -> None:
        bad = replace(self.lineage, candidate_set_hash="0" * 64)
        result = validate_source_rank_lineage(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=bad,
        )
        self.assertIn(
            "RANKED_PREFIX:CANDIDATE_HASH_MISMATCH",
            result.blocking_reasons,
        )

    def test_ranked_candidate_lineage_mismatch_holds(self) -> None:
        bad = replace(
            self.lineage,
            ranked_candidate_ids=("B", "A"),
        )
        result = validate_source_rank_lineage(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=bad,
        )
        self.assertIn(
            "RANKED_PREFIX:RANKED_LINEAGE_MISMATCH",
            result.blocking_reasons,
        )

    def test_exact_allocation_plan_lineage_passes(self) -> None:
        plan = build_allocation_plan(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            source_rank_gate_id=self.lineage.source_rank_gate_id,
        )
        result = validate_allocation_plan_lineage(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=self.lineage,
            plan_rows=plan,
        )
        self.assertEqual(result.status, PASS)

    def test_plan_rank_mismatch_holds(self) -> None:
        plan = list(
            build_allocation_plan(
                task_id="TASK-SYNTH-A",
                decision=self.decision,
                source_rank_gate_id=self.lineage.source_rank_gate_id,
            )
        )
        plan[0] = replace(plan[0], allocation_rank=2)
        result = validate_allocation_plan_lineage(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=self.lineage,
            plan_rows=plan,
        )
        self.assertIn(
            "RANKED_PREFIX:PLAN_RANK_SEQUENCE_INVALID",
            result.blocking_reasons,
        )

    def test_plan_quantity_mismatch_holds(self) -> None:
        plan = list(
            build_allocation_plan(
                task_id="TASK-SYNTH-A",
                decision=self.decision,
                source_rank_gate_id=self.lineage.source_rank_gate_id,
            )
        )
        plan[-1] = replace(plan[-1], planned_quantity=39)
        result = validate_allocation_plan_lineage(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=self.lineage,
            plan_rows=plan,
        )
        self.assertIn(
            "RANKED_PREFIX:PLAN_QTY_MISMATCH",
            result.blocking_reasons,
        )

    def test_allocation_plan_hash_is_deterministic(self) -> None:
        plan = build_allocation_plan(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            source_rank_gate_id=self.lineage.source_rank_gate_id,
        )
        first = compute_allocation_plan_hash(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=self.lineage,
            plan_rows=plan,
        )
        second = compute_allocation_plan_hash(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=self.lineage,
            plan_rows=plan,
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertTrue(all(char in "0123456789abcdef" for char in first))

    def test_allocation_plan_hash_contract_id_is_versioned(self) -> None:
        self.assertEqual(
            ALLOCATION_PLAN_HASH_CONTRACT_ID,
            "RANKED_PREFIX_ALLOCATION_PLAN_HASH_V1",
        )

    def test_allocation_plan_hash_v1_golden_vector(self) -> None:
        decision = evaluate_ranked_prefix_allocation(
            task_id="TASK-HASH-A",
            target_date=date(2026, 2, 15),
            requested_qty=100,
            candidates=(
                RankedCandidate(
                    "SRC-A",
                    date(2026, 2, 14),
                    1,
                    "00100",
                    60,
                ),
                RankedCandidate(
                    "SRC-B",
                    date(2026, 2, 13),
                    2,
                    "00200",
                    60,
                ),
            ),
        )
        lineage = build_source_rank_lineage(
            task_id="TASK-HASH-A",
            decision=decision,
            source_rank_gate_id="GATE-A",
        )
        plan = build_allocation_plan(
            task_id="TASK-HASH-A",
            decision=decision,
            source_rank_gate_id="GATE-A",
        )
        digest = compute_allocation_plan_hash(
            task_id="TASK-HASH-A",
            decision=decision,
            lineage=lineage,
            plan_rows=plan,
        )
        self.assertEqual(
            digest,
            "e36f9f6818a2290e67d1d39ca0923fd"
            "64605a4663547da62c946204a20157b63",
        )

    def test_plan_state_changes_allocation_plan_hash(self) -> None:
        planned = build_allocation_plan(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            source_rank_gate_id=self.lineage.source_rank_gate_id,
            state="PLANNED",
        )
        committed = build_allocation_plan(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            source_rank_gate_id=self.lineage.source_rank_gate_id,
            state="COMMITTED",
        )
        planned_hash = compute_allocation_plan_hash(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=self.lineage,
            plan_rows=planned,
        )
        committed_hash = compute_allocation_plan_hash(
            task_id="TASK-SYNTH-A",
            decision=self.decision,
            lineage=self.lineage,
            plan_rows=committed,
        )
        self.assertNotEqual(planned_hash, committed_hash)

    def test_invalid_plan_cannot_receive_canonical_hash(self) -> None:
        plan = list(
            build_allocation_plan(
                task_id="TASK-SYNTH-A",
                decision=self.decision,
                source_rank_gate_id=self.lineage.source_rank_gate_id,
            )
        )
        plan[-1] = replace(plan[-1], planned_quantity=39)
        with self.assertRaises(ValueError):
            compute_allocation_plan_hash(
                task_id="TASK-SYNTH-A",
                decision=self.decision,
                lineage=self.lineage,
                plan_rows=plan,
            )

    def test_invalid_plan_state_is_rejected_by_builder(self) -> None:
        with self.assertRaises(ValueError):
            build_allocation_plan(
                task_id="TASK-SYNTH-A",
                decision=self.decision,
                source_rank_gate_id=self.lineage.source_rank_gate_id,
                state="OTHER",
            )


    def test_non_ascii_digit_serial_holds_without_exception(self) -> None:
        decision = evaluate((candidate("A", serial_start="²"),))
        self.assertEqual(decision.status, HOLD)
        self.assertIn(
            "RANKED_PREFIX:SERIAL_START_INVALID:A",
            decision.blocking_reasons,
        )

    def test_overlong_serial_holds_without_integer_conversion(self) -> None:
        decision = evaluate((candidate("A", serial_start="9" * 5000),))
        self.assertEqual(decision.status, HOLD)
        self.assertIn(
            "RANKED_PREFIX:SERIAL_START_INVALID:A",
            decision.blocking_reasons,
        )

    def test_independent_verifier_holds_for_overlong_serial(self) -> None:
        result = verify_ranked_prefix_allocation(
            task_id="TASK-SYNTH-A",
            target_date=TARGET,
            requested_qty=1,
            candidates=(candidate("A", serial_start="9" * 5000, available_qty=1),),
            proposed_allocation=(),
        )
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "RANKED_PREFIX:SERIAL_START_INVALID:A",
            result.blocking_reasons,
        )


if __name__ == "__main__":
    unittest.main()
