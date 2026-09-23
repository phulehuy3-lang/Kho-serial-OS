from __future__ import annotations

import unittest

from scripts.hold_lifecycle_v0_1 import (
    BLOCK_APPROVAL,
    BLOCK_DATE,
    BLOCK_EVIDENCE,
    BLOCK_EXECUTION_NOT_READY,
    BLOCK_OVERLAP,
    BLOCK_PAYLOAD,
    BLOCK_STATE_MISMATCH,
    BLOCK_STOCK_YEAR,
    HOLD,
    PASS,
    PASS_RELEASE_READBACK,
    PASS_RELEASE_READY,
    PASS_TRANSITION_INTENT,
    HoldRecord,
    HoldReleaseReadback,
    HoldTransitionIntent,
    IntervalHoldState,
    blocking_overlapping_interval_holds,
    evaluate_hold_release_readback,
    evaluate_hold_release_readiness,
    evaluate_hold_transition_intent,
    validate_hold_record,
)


def hold(**overrides: object) -> HoldRecord:
    values = {
        "hold_id": "HOLD-SYNTH-A",
        "scope_type": "INTERVAL",
        "target_id": "INT-SYNTH-A",
        "category": "CATEGORY-A",
        "range_start": "1000",
        "range_end": "1999",
        "hold_type": "EVIDENCE_REVIEW",
        "hold_flag": True,
        "status": "ACTIVE",
        "evidence_id": "EVID-SYNTH-A",
        "reason": "Synthetic fixture",
        "created_at": "2026-02-15T08:00:00Z",
    }
    values.update(overrides)
    return HoldRecord(**values)  # type: ignore[arg-type]


def interval(**overrides: object) -> IntervalHoldState:
    values = {
        "interval_id": "INT-SYNTH-A",
        "category": "CATEGORY-A",
        "range_start": "1000",
        "range_end": "1999",
        "available_qty": 100,
        "status": "HELD",
        "hold_flag": True,
        "evidence_status": "VERIFIED_INDEPENDENT",
        "source_date_text": "15/02/2026",
        "source_year": 2026,
        "source_year_status": "YEAR_VERIFIED",
    }
    values.update(overrides)
    return IntervalHoldState(**values)  # type: ignore[arg-type]


class HoldIsolationTests(unittest.TestCase):
    def test_valid_active_pair_passes(self) -> None:
        result = validate_hold_record(hold(), interval())
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.ready)

    def test_text_boolean_fails_closed(self) -> None:
        result = validate_hold_record(hold(hold_flag="TRUE"), interval())
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "HOLD_ISOLATION:HOLDFLAG_NOT_BOOLEAN",
            result.blocking_reasons,
        )

    def test_active_interval_flag_mismatch_fails(self) -> None:
        result = validate_hold_record(hold(), interval(hold_flag=False))
        self.assertIn(
            "HOLD_ISOLATION:REGISTRY_INTERVAL_FLAG_MISMATCH",
            result.blocking_reasons,
        )

    def test_invalid_range_order_fails(self) -> None:
        result = validate_hold_record(
            hold(range_start="2000", range_end="1000"),
            interval(),
        )
        self.assertIn("HOLD_ISOLATION:RANGE_INVALID", result.blocking_reasons)


class HoldReleaseReadinessTests(unittest.TestCase):
    def test_evidence_is_first_business_gate(self) -> None:
        peer = hold(
            hold_id="HOLD-SYNTH-B",
            target_id="INT-SYNTH-B",
            range_start="1500",
            range_end="2500",
        )
        result = evaluate_hold_release_readiness(
            hold(),
            interval(
                evidence_status="UNVERIFIED",
                source_date_text="bad",
                available_qty=0,
            ),
            peers=(peer,),
        )
        self.assertEqual(result.canonical_decision, BLOCK_EVIDENCE)
        self.assertEqual(result.first_blocking_gate, "EVIDENCE")

    def test_exact_date_rejects_extra_text(self) -> None:
        result = evaluate_hold_release_readiness(
            hold(),
            interval(source_date_text="15/02/2026 extra"),
        )
        self.assertEqual(result.canonical_decision, BLOCK_DATE)

    def test_source_year_mismatch_fails_date_gate(self) -> None:
        result = evaluate_hold_release_readiness(
            hold(),
            interval(source_date_text="31/12/2025", source_year=2026),
        )
        self.assertEqual(result.canonical_decision, BLOCK_DATE)

    def test_active_overlap_blocks(self) -> None:
        peer = hold(
            hold_id="HOLD-SYNTH-B",
            target_id="INT-SYNTH-B",
            range_start="1500",
            range_end="2500",
        )
        result = evaluate_hold_release_readiness(
            hold(), interval(), peers=(peer,)
        )
        self.assertEqual(result.canonical_decision, BLOCK_OVERLAP)
        self.assertEqual(result.active_overlap_peer_ids, ("HOLD-SYNTH-B",))

    def test_released_false_overlap_does_not_block(self) -> None:
        peer = hold(
            hold_id="HOLD-SYNTH-B",
            target_id="INT-SYNTH-B",
            range_start="1500",
            range_end="2500",
            status="RELEASED",
            hold_flag=False,
        )
        result = evaluate_hold_release_readiness(
            hold(), interval(), peers=(peer,)
        )
        self.assertEqual(result.canonical_decision, PASS_RELEASE_READY)

    def test_invalid_peer_range_fails_closed(self) -> None:
        peer = hold(
            hold_id="HOLD-SYNTH-B",
            target_id="INT-SYNTH-B",
            range_start="BAD",
            range_end="2500",
        )
        self.assertEqual(
            blocking_overlapping_interval_holds(hold(), (peer,)),
            ("HOLD-SYNTH-B",),
        )

    def test_zero_stock_blocks(self) -> None:
        result = evaluate_hold_release_readiness(
            hold(), interval(available_qty=0)
        )
        self.assertEqual(result.canonical_decision, BLOCK_STOCK_YEAR)

    def test_bool_stock_is_invalid(self) -> None:
        result = evaluate_hold_release_readiness(
            hold(), interval(available_qty=True)
        )
        self.assertEqual(result.canonical_decision, BLOCK_STOCK_YEAR)

    def test_clean_target_reaches_release_ready(self) -> None:
        result = evaluate_hold_release_readiness(hold(), interval())
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.ready)
        self.assertEqual(result.canonical_decision, PASS_RELEASE_READY)

    def test_released_target_is_not_released_again(self) -> None:
        result = evaluate_hold_release_readiness(
            hold(status="RELEASED", hold_flag=False),
            interval(hold_flag=False),
        )
        self.assertEqual(result.canonical_decision, BLOCK_STATE_MISMATCH)


class HoldTransitionIntentTests(unittest.TestCase):
    def intent(self, **overrides: object) -> HoldTransitionIntent:
        values = {
            "release_decision": PASS_RELEASE_READY,
            "transaction_gate_decision": PASS_RELEASE_READY,
            "approval_status": "APPROVED",
            "expected_payload_hash": "payload-a",
            "actual_payload_hash": "payload-a",
            "execution_ready": True,
            "last_safe_state": "GATE_EVALUATED",
        }
        values.update(overrides)
        return HoldTransitionIntent(**values)  # type: ignore[arg-type]

    def test_approval_blocks_before_execution(self) -> None:
        result = evaluate_hold_transition_intent(
            self.intent(approval_status="PENDING")
        )
        self.assertEqual(result.canonical_decision, BLOCK_APPROVAL)

    def test_payload_mismatch_blocks(self) -> None:
        result = evaluate_hold_transition_intent(
            self.intent(actual_payload_hash="payload-b")
        )
        self.assertEqual(result.canonical_decision, BLOCK_PAYLOAD)

    def test_execution_not_ready_blocks(self) -> None:
        result = evaluate_hold_transition_intent(
            self.intent(execution_ready=False)
        )
        self.assertEqual(
            result.canonical_decision,
            BLOCK_EXECUTION_NOT_READY,
        )

    def test_all_inputs_only_return_intent(self) -> None:
        result = evaluate_hold_transition_intent(self.intent())
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.ready)
        self.assertEqual(result.canonical_decision, PASS_TRANSITION_INTENT)


class HoldReadbackTests(unittest.TestCase):
    def readback(self, **overrides: object) -> HoldReleaseReadback:
        values = {
            "registry_hold_flag": False,
            "registry_status": "RELEASED",
            "interval_hold_flag": False,
            "quarantine_contains_target": False,
            "eligible_contains_target": True,
            "lookup_reports_hold": False,
            "ranking_contains_target": True,
            "inventory_total_before": 1000,
            "inventory_total_after": 1000,
            "rollback_proof_pass": True,
        }
        values.update(overrides)
        return HoldReleaseReadback(**values)  # type: ignore[arg-type]

    def test_full_readback_passes(self) -> None:
        result = evaluate_hold_release_readback(self.readback())
        self.assertEqual(result.status, PASS)
        self.assertEqual(result.canonical_decision, PASS_RELEASE_READBACK)

    def test_unknown_view_state_fails_closed(self) -> None:
        result = evaluate_hold_release_readback(
            self.readback(eligible_contains_target=None)
        )
        self.assertEqual(result.status, HOLD)

    def test_inventory_total_change_fails(self) -> None:
        result = evaluate_hold_release_readback(
            self.readback(inventory_total_after=999)
        )
        self.assertIn(
            "HOLD_READBACK:INVENTORY_TOTAL_CHANGED_OR_UNKNOWN",
            result.blocking_reasons,
        )

    def test_still_in_quarantine_fails(self) -> None:
        result = evaluate_hold_release_readback(
            self.readback(quarantine_contains_target=True)
        )
        self.assertIn(
            "HOLD_READBACK:TARGET_STILL_IN_QUARANTINE",
            result.blocking_reasons,
        )


if __name__ == "__main__":
    unittest.main()
