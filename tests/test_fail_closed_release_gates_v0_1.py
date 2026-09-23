from __future__ import annotations

import unittest

from scripts.fail_closed_release_gates_v0_1 import (
    HOLD,
    READY_FOR_RELEASE,
    evaluate_release_gates,
)


class FailClosedReleaseGateTests(unittest.TestCase):
    def test_all_applicable_gates_pass_without_hold_conflict(self) -> None:
        decision = evaluate_release_gates(
            {
                "formula_health": True,
                "interval_integrity": True,
                "source_readback": True,
                "source_derived_reconciliation": True,
            },
            hold_conflict=False,
        )
        self.assertEqual(decision.status, READY_FOR_RELEASE)
        self.assertTrue(decision.ready)
        self.assertEqual(decision.blocking_gates, ())

    def test_failed_gate_forces_hold(self) -> None:
        decision = evaluate_release_gates(
            {
                "source_readback": True,
                "interval_integrity": False,
            },
            hold_conflict=False,
        )
        self.assertEqual(decision.status, HOLD)
        self.assertFalse(decision.ready)
        self.assertEqual(
            decision.blocking_gates,
            ("interval_integrity:FAIL",),
        )

    def test_unknown_gate_evidence_forces_hold(self) -> None:
        decision = evaluate_release_gates(
            {
                "source_readback": True,
                "source_derived_reconciliation": None,
            },
            hold_conflict=False,
        )
        self.assertEqual(decision.status, HOLD)
        self.assertEqual(
            decision.blocking_gates,
            ("source_derived_reconciliation:UNKNOWN",),
        )

    def test_present_hold_conflict_forces_hold(self) -> None:
        decision = evaluate_release_gates(
            {"source_readback": True},
            hold_conflict=True,
        )
        self.assertEqual(decision.status, HOLD)
        self.assertEqual(
            decision.blocking_gates,
            ("hold_conflict:PRESENT",),
        )

    def test_unknown_hold_state_forces_hold(self) -> None:
        decision = evaluate_release_gates(
            {"source_readback": True},
            hold_conflict=None,
        )
        self.assertEqual(decision.status, HOLD)
        self.assertEqual(
            decision.blocking_gates,
            ("hold_conflict:UNKNOWN",),
        )

    def test_empty_gate_evidence_fails_closed(self) -> None:
        decision = evaluate_release_gates(
            {},
            hold_conflict=False,
        )
        self.assertEqual(decision.status, HOLD)
        self.assertEqual(
            decision.blocking_gates,
            ("gate_evidence:EMPTY",),
        )

    def test_multiple_blockers_are_deterministic(self) -> None:
        decision = evaluate_release_gates(
            {
                "z_gate": False,
                "a_gate": None,
                "m_gate": True,
            },
            hold_conflict=True,
        )
        self.assertEqual(
            decision.blocking_gates,
            (
                "a_gate:UNKNOWN",
                "z_gate:FAIL",
                "hold_conflict:PRESENT",
            ),
        )

    def test_text_pass_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            evaluate_release_gates(
                {"source_readback": "PASS"},  # type: ignore[arg-type]
                hold_conflict=False,
            )

    def test_integer_one_is_not_accepted_as_true(self) -> None:
        with self.assertRaises(TypeError):
            evaluate_release_gates(
                {"source_readback": 1},  # type: ignore[arg-type]
                hold_conflict=False,
            )

    def test_integer_hold_conflict_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            evaluate_release_gates(
                {"source_readback": True},
                hold_conflict=0,  # type: ignore[arg-type]
            )

    def test_blank_gate_name_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_release_gates(
                {"   ": True},
                hold_conflict=False,
            )

    def test_ready_requires_nonempty_gate_evidence(self) -> None:
        decision = evaluate_release_gates(
            {},
            hold_conflict=None,
        )
        self.assertFalse(decision.ready)
        self.assertEqual(
            decision.blocking_gates,
            ("gate_evidence:EMPTY", "hold_conflict:UNKNOWN"),
        )


if __name__ == "__main__":
    unittest.main()
