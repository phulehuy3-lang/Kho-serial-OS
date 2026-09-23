"""Adversarial synthetic composition tests for the formula pair caller."""

import unittest

from scripts.formula_gate_preview_v0_1 import (
    SCENARIO_ID,
    evaluate_formula_gate_preview,
)
from scripts.required_gate_set_preflight_v0_1 import MaterializedGateEvidence


def record(gate_id, value=True, **changes):
    data = dict(
        gate_id=gate_id,
        scenario_id=SCENARIO_ID,
        task_id="task",
        scope_id="scope",
        capture_marker="capture",
        value=value,
    )
    data.update(changes)
    return MaterializedGateEvidence(**data)


def preview(evidence, hold_conflict=False):
    return evaluate_formula_gate_preview("task", "scope", "capture", evidence, hold_conflict)


class FormulaGatePreviewTests(unittest.TestCase):
    def setUp(self):
        self.valid = (record("formula_health"), record("formula_semantics"))

    def test_complete_preview_is_never_write_authority(self):
        result = preview(self.valid)
        self.assertEqual(result.status, "READY_FOR_PREVIEW")
        self.assertTrue(result.ready)
        self.assertFalse(result.production_write_authorized)

    def test_missing_extra_duplicate_hold(self):
        for evidence, reason in (
            (self.valid[:1], "EVIDENCE_MISSING"),
            (self.valid + (record("other"),), "EVIDENCE_EXTRA"),
            (self.valid + self.valid[:1], "EVIDENCE_DUPLICATE"),
        ):
            with self.subTest(reason=reason):
                result = preview(evidence)
                self.assertEqual(result.status, "HOLD")
                self.assertIn(reason, result.blocking_reasons)

    def test_binding_and_marker_mismatch_hold(self):
        for change, reason in (
            ({"task_id": "other"}, "BINDING_MISMATCH"),
            ({"scope_id": "other"}, "BINDING_MISMATCH"),
            ({"scenario_id": "other"}, "BINDING_MISMATCH"),
            ({"capture_marker": "other"}, "MARKER_MISMATCH"),
        ):
            with self.subTest(change=change):
                result = preview((self.valid[0], record("formula_semantics", **change)))
                self.assertIn(reason, result.blocking_reasons)
                self.assertFalse(result.ready)

    def test_fail_unknown_and_hold_conflict(self):
        for value, reason in ((False, "formula_semantics:FAIL"), (None, "formula_semantics:UNKNOWN")):
            with self.subTest(value=value):
                result = preview((self.valid[0], record("formula_semantics", value)))
                self.assertIn(reason, result.blocking_reasons)
        self.assertIn("hold_conflict:UNKNOWN", preview(self.valid, None).blocking_reasons)
        self.assertIn("hold_conflict:PRESENT", preview(self.valid, True).blocking_reasons)

    def test_invalid_value_and_context_hold(self):
        self.assertIn("VALUE_INVALID", preview((self.valid[0], record("formula_semantics", 1))).blocking_reasons)
        result = evaluate_formula_gate_preview("", "scope", "capture", self.valid, False)
        self.assertIn("SCENARIO_INVALID", result.blocking_reasons)


if __name__ == "__main__":
    unittest.main()
