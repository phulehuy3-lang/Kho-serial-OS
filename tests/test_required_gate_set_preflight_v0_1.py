from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.fail_closed_release_gates_v0_1 import evaluate_release_gates
from scripts.required_gate_set_preflight_v0_1 import (
    CONTRACT_ID,
    MaterializedGateEvidence,
    RequiredGateScenario,
    assess_required_gate_set,
)


SCENARIO = RequiredGateScenario(
    contract_id=CONTRACT_ID,
    scenario_id="SYNTHETIC-A",
    task_id="TASK-A",
    scope_id="SCOPE-A",
    required_gate_ids=("formula_health", "formula_semantics"),
    expected_capture_marker="CAPTURE-A",
)


def record(gate_id: str, value: bool | None = True) -> MaterializedGateEvidence:
    return MaterializedGateEvidence(
        gate_id=gate_id,
        scenario_id=SCENARIO.scenario_id,
        task_id=SCENARIO.task_id,
        scope_id=SCENARIO.scope_id,
        capture_marker=SCENARIO.expected_capture_marker,
        value=value,
    )


class RequiredGateSetPreflightTests(unittest.TestCase):
    def assess(self, *records, scenario=SCENARIO):
        return assess_required_gate_set(scenario, tuple(records))

    def test_complete_map_passes_and_control_07_aggregates(self) -> None:
        result = self.assess(record("formula_health"), record("formula_semantics"))
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.ready)
        self.assertEqual(
            result.validated_gate_map,
            {"formula_health": True, "formula_semantics": True},
        )
        with self.assertRaises(TypeError):
            result.validated_gate_map["formula_semantics"] = False
        decision = evaluate_release_gates(result.validated_gate_map, False)
        self.assertEqual(decision.status, "READY_FOR_RELEASE")
        self.assertEqual(
            evaluate_release_gates(result.validated_gate_map, None).status,
            "HOLD",
        )

    def test_declared_missing_gate_blocks_previous_omission_path(self) -> None:
        self.assertEqual(
            evaluate_release_gates({"formula_health": True}, False).status,
            "READY_FOR_RELEASE",
        )
        result = self.assess(record("formula_health"))
        self.assertEqual(result.blocking_reasons, ("EVIDENCE_MISSING",))
        self.assertIsNone(result.validated_gate_map)

    def test_empty_extra_and_duplicate_evidence(self) -> None:
        self.assertIn("EVIDENCE_MISSING", self.assess().blocking_reasons)
        self.assertEqual(
            self.assess(record("formula_health"), record("formula_semantics"), record("extra")).blocking_reasons,
            ("EVIDENCE_EXTRA",),
        )
        self.assertEqual(
            self.assess(record("formula_health"), record("formula_health"), record("formula_semantics")).blocking_reasons,
            ("EVIDENCE_DUPLICATE",),
        )

    def test_context_and_capture_binding(self) -> None:
        for field in ("scenario_id", "task_id", "scope_id"):
            with self.subTest(field=field):
                wrong = replace(record("formula_semantics"), **{field: "OTHER"})
                self.assertIn(
                    "BINDING_MISMATCH",
                    self.assess(record("formula_health"), wrong).blocking_reasons,
                )
        stale = replace(record("formula_semantics"), capture_marker="CAPTURE-OLD")
        self.assertEqual(
            self.assess(record("formula_health"), stale).blocking_reasons,
            ("MARKER_MISMATCH",),
        )

    def test_non_native_values_and_unknown_forwarding(self) -> None:
        for invalid in ("PASS", 1):
            with self.subTest(invalid=invalid):
                self.assertEqual(
                    self.assess(record("formula_health"), record("formula_semantics", invalid)).blocking_reasons,
                    ("VALUE_INVALID",),
                )
        for value, blocker in ((False, "formula_semantics:FAIL"), (None, "formula_semantics:UNKNOWN")):
            with self.subTest(value=value):
                result = self.assess(record("formula_health"), record("formula_semantics", value))
                self.assertTrue(result.ready)
                self.assertIn(
                    blocker,
                    evaluate_release_gates(result.validated_gate_map, False).blocking_gates,
                )

    def test_invalid_scenario_is_hold(self) -> None:
        for scenario in (
            replace(SCENARIO, contract_id="UNKNOWN"),
            replace(SCENARIO, required_gate_ids=()),
            replace(SCENARIO, required_gate_ids=("formula_health", "formula_health")),
            replace(SCENARIO, required_gate_ids=(" formula_health",)),
            replace(SCENARIO, task_id=""),
        ):
            with self.subTest(scenario=scenario):
                result = self.assess(record("formula_health"), record("formula_semantics"), scenario=scenario)
                self.assertIn("SCENARIO_INVALID", result.blocking_reasons)
                self.assertIsNone(result.validated_gate_map)

    def test_input_order_does_not_change_result(self) -> None:
        first = self.assess(record("formula_health"), record("formula_semantics"))
        second = self.assess(record("formula_semantics"), record("formula_health"))
        self.assertEqual(first, second)

    def test_multiple_reasons_are_sorted(self) -> None:
        result = self.assess(record("formula_health"), replace(record("extra", "PASS"), task_id="OTHER"))
        self.assertEqual(
            result.blocking_reasons,
            ("BINDING_MISMATCH", "EVIDENCE_EXTRA", "EVIDENCE_MISSING", "VALUE_INVALID"),
        )


if __name__ == "__main__":
    unittest.main()
