from __future__ import annotations

import unittest

from scripts.inbound_universe_coverage_v0_1 import assess_coverage


class CoverageTests(unittest.TestCase):
    def check(self, **overrides):
        context = ("synthetic-target", "synthetic-registry", "synthetic-binding",
                   "synthetic-method", "synthetic-consistency", "task-a", "scope-a",
                   "ACTIVE_SERIAL_INTERVAL_UNIVERSE")
        values = dict(first_position=3, last_position=5, captured_positions=(3, 4, 5),
                      expected_context=context, captured_context=context,
                      method_accepted=True, consistency_accepted=True,
                      enumeration_terminated=True, truncated=False, limit_exceeded=False)
        values.update(overrides)
        result = assess_coverage(**values)
        self.assertIs(result.live_read_authorized, False)
        self.assertIs(result.executable_acquisition_authorized, False)
        self.assertIs(result.production_write_authorized, False)
        return result

    def test_full_domain_and_permuted_capture_are_coherent(self):
        self.assertTrue(self.check().coverage_coherent)
        self.assertTrue(self.check(captured_positions=(5, 3, 4)).coverage_coherent)

    def test_omitted_last_or_hidden_filtered_middle_row_is_blocked(self):
        for positions in ((3, 4), (3, 5)):
            with self.subTest(positions=positions):
                self.assertIn("DOMAIN_COVERAGE_MISMATCH",
                              self.check(captured_positions=positions).blocking_reasons)

    def test_duplicate_and_out_of_domain_are_blocked(self):
        for positions in ((3, 4, 4, 5), (2, 3, 4, 5), (3, 4, 6)):
            self.assertFalse(self.check(captured_positions=positions).coverage_coherent)

    def test_empty_response_does_not_prove_nonempty_domain(self):
        self.assertFalse(self.check(captured_positions=()).coverage_coherent)

    def test_authority_sealed_empty_domain_still_needs_termination(self):
        self.assertTrue(self.check(last_position=2, captured_positions=()).coverage_coherent)
        self.assertFalse(self.check(last_position=2, captured_positions=(),
                                    enumeration_terminated=False).coverage_coherent)

    def test_scope_task_and_consistency_context_drift_are_blocked(self):
        context = ("synthetic-target", "synthetic-registry", "synthetic-binding",
                   "synthetic-method", "synthetic-consistency", "task-a", "scope-a",
                   "ACTIVE_SERIAL_INTERVAL_UNIVERSE")
        for index in range(8):
            changed = list(context)
            changed[index] = "drift"
            self.assertFalse(self.check(captured_context=tuple(changed)).coverage_coherent)

    def test_unknown_and_pseudo_boolean_evidence_are_blocked(self):
        for field, valid in (("method_accepted", True), ("consistency_accepted", True),
                             ("enumeration_terminated", True), ("truncated", False),
                             ("limit_exceeded", False)):
            for value in (None, str(valid), int(valid), not valid):
                self.assertFalse(self.check(**{field: value}).coverage_coherent)

    def test_malformed_bounds_and_positions_are_blocked(self):
        for overrides in ({"first_position": True}, {"last_position": 100003},
                          {"last_position": 1}, {"captured_positions": [3, 4, 5]},
                          {"captured_positions": (3, True, 5)},
                          {"expected_context": ("",) * 8}):
            self.assertFalse(self.check(**overrides).coverage_coherent)

    def test_hold_domain_uses_the_same_contract(self):
        context = ("synthetic-target", "synthetic-registry", "synthetic-binding",
                   "synthetic-method", "synthetic-consistency", "task-a", "scope-a",
                   "ACTIVE_HOLD_INTERVAL_UNIVERSE")
        self.assertTrue(self.check(expected_context=context,
                                   captured_context=context).coverage_coherent)


if __name__ == "__main__":
    unittest.main()
