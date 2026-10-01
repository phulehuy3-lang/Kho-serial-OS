"""Synthetic regressions for the 28 September control-plane defects."""

import unittest

from scripts.warehouse_governance_v1_8 import (
    GateError, PROTECTED, SESSION_GATES, classify_global_session,
    composite_identity, duplicate_decision, exact_middle_split, formula_hash,
    validate_correction, validate_formula_snapshot, validate_inbound_touch_set,
    validate_postfacto_physical, validate_transition,
)


class GovernanceTests(unittest.TestCase):
    def test_boolean_gate_inputs_fail_closed(self):
        for bad in ("FALSE", "TRUE", 0, 1, None, [], {}, [False]):
            with self.subTest(value=bad):
                with self.assertRaises(GateError):
                    validate_transition("PREPARED", "PREWRITE_SEALED", manifest_readback=bad)
                with self.assertRaises(GateError):
                    validate_transition("READBACK_PASS", "CLOSED", reconciliation=bad, audit=True)
                good = dict(signed_range=("1000", "1001"), booked_range=("1000", "1001"),
                            unique_source=True, sufficient_stock=True, hold_clear=True,
                            no_prior_out=True, owner_confirmed=True, reranked=False)
                for key in ("unique_source", "sufficient_stock", "hold_clear", "no_prior_out", "owner_confirmed", "reranked"):
                    with self.subTest(key=key), self.assertRaises(GateError):
                        validate_postfacto_physical(**dict(good, **{key: bad}))

    def test_readback_transition_and_close_require_evidence(self):
        for previous, following in (("WRITTEN", "READBACK_PASS"), ("READBACK_PASS", "CLOSED")):
            with self.subTest(following=following), self.assertRaises(GateError):
                validate_transition(previous, following, reconciliation=True, audit=True)

    def test_generic_inbound_only_four_cells(self):
        self.assertTrue(validate_inbound_touch_set([("BUSINESS", c) for c in "ACDO"]))

    def test_rectangular_a_to_o_rejected(self):
        with self.assertRaisesRegex(GateError, "BLOCK_SCOPE"):
            validate_inbound_touch_set([("BUSINESS", chr(c)) for c in range(ord("A"), ord("O") + 1)])

    def test_derived_or_duplicate_target_rejected(self):
        for cells in ([('ELIGIBLE_STOCK', 'A')], [('BUSINESS', 'A')] * 2):
            with self.subTest(cells=cells), self.assertRaises(GateError):
                validate_inbound_touch_set(cells)

    def test_formula_missing_before_or_after_and_hash_drift(self):
        before = {c: f"={c}1+1" for c in PROTECTED}
        digest = formula_hash(before)
        self.assertTrue(validate_formula_snapshot(before, before.copy(), digest))
        for key in ("B", "G", "N"):
            changed = before.copy()
            changed.pop(key)
            with self.subTest(key=key), self.assertRaisesRegex(GateError, "MISSING_POSTWRITE_FORMULA"):
                validate_formula_snapshot(before, changed, digest)
        changed = before.copy()
        changed["B"] = "=B1+2"
        with self.assertRaisesRegex(GateError, "FORMULA_HASH_MISMATCH"):
            validate_formula_snapshot(before, changed, digest)
        with self.assertRaisesRegex(GateError, "STALE_PREWRITE_FORMULA_HASH"):
            validate_formula_snapshot(before, before, "0" * 64)

    def test_state_machine_and_parent_lineage(self):
        with self.assertRaises(GateError):
            validate_transition("PREPARED", "CLOSED", manifest_readback=True, reconciliation=True, audit=True)
        with self.assertRaises(GateError):
            validate_transition("CLOSED", "WRITTEN")
        with self.assertRaises(GateError):
            validate_correction("CLOSED", "")
        with self.assertRaises(GateError):
            validate_transition("PREPARED", "PREWRITE_SEALED")
        self.assertTrue(validate_transition("PREPARED", "PREWRITE_SEALED", manifest_readback=True))
        self.assertTrue(validate_correction("CLOSED", "synthetic-parent"))

    def test_document_number_reuse_and_true_duplicate(self):
        base = dict(direction="IN", partner="synthetic-vendor", document_no="SAMPLE-17",
                    document_date="2026-09-28", order="batch-one", payload_hash="hash-one")
        distinct = dict(base, order="batch-two", payload_hash="hash-two")
        self.assertNotEqual(composite_identity(base), composite_identity(distinct))
        self.assertTrue(duplicate_decision([base], distinct))
        with self.assertRaisesRegex(GateError, "TRUE_DUPLICATE"):
            duplicate_decision([base], base.copy())
        with self.assertRaises(GateError):
            composite_identity(dict(base, partner=""))

    def test_exact_middle_slice_conservation_and_identity(self):
        split = exact_middle_split("00001000", "00002999", "00001500", "00001999")
        self.assertEqual([split[k][2] for k in ("left", "out", "right")], [500, 500, 1000])
        self.assertEqual(sum(split[k][2] for k in ("left", "out", "right")), split["source_quantity"])
        self.assertEqual(split["out"][:2], ("00001500", "00001999"))
        with self.assertRaises(GateError):
            exact_middle_split("00001000", "00002999", "00002999", "00003000")

    def test_serial_text_contract_rejects_unicode_types_and_length(self):
        cases = (
            ("１２", "１３", "１２", "１２"),
            ("١٢", "١٣", "١٢", "١٢"),
            ("१२", "१३", "१२", "१२"),
            (True, "13", "12", "12"),
            ("", "13", "12", "12"),
            (12, "13", "12", "12"),
            ("1" * 4097, "1" * 4097, "1" * 4097, "1" * 4097),
            ("1" * 5000, "1" * 5000, "1" * 5000, "1" * 5000),
        )
        for values in cases:
            with self.subTest(sample=str(values[0])[:20], length=len(str(values[0]))):
                with self.assertRaisesRegex(GateError, "SERIAL_IDENTITY_INVALID"):
                    exact_middle_split(*values)

    def test_serial_split_4096_digits_without_integer_string_conversion(self):
        prefix = "0" * 4092
        result = exact_middle_split(
            prefix + "1000", prefix + "1003", prefix + "1001", prefix + "1002"
        )
        self.assertEqual(result["left"], (prefix + "1000", prefix + "1000", 1))
        self.assertEqual(result["out"], (prefix + "1001", prefix + "1002", 2))
        self.assertEqual(result["right"], (prefix + "1003", prefix + "1003", 1))
        self.assertEqual(result["source_quantity"], 4)
        self.assertEqual(
            result,
            exact_middle_split(prefix + "1000", prefix + "1003",
                               prefix + "1001", prefix + "1002"),
        )

    def test_serial_split_edges_singleton_and_fail_closed_intervals(self):
        start = exact_middle_split("00001000", "00002999", "00001000", "00001000")
        self.assertIsNone(start["left"])
        self.assertEqual(start["out"], ("00001000", "00001000", 1))
        self.assertEqual(start["right"], ("00001001", "00002999", 1999))
        end = exact_middle_split("00001000", "00002999", "00002999", "00002999")
        self.assertEqual(end["left"], ("00001000", "00002998", 1999))
        self.assertIsNone(end["right"])
        self.assertEqual(end["source_quantity"], 2000)
        for values in (
            ("00001000", "00002999", "00000999", "00001000"),
            ("00001000", "00002999", "00002999", "00003000"),
            ("00002000", "00001000", "00001500", "00001600"),
            ("00001000", "00002999", "00001999", "00001500"),
        ):
            with self.subTest(values=values), self.assertRaisesRegex(GateError, "PHYSICAL_RANGE_OUTSIDE_SOURCE"):
                exact_middle_split(*values)
        with self.assertRaisesRegex(GateError, "SERIAL_IDENTITY_INVALID"):
            exact_middle_split("001000", "00002999", "00001500", "00001999")

    def test_serial_split_exact_conservation_and_zero_identity(self):
        result = exact_middle_split("00001000", "00002999", "00001500", "00001999")
        self.assertEqual(result, {
            "left": ("00001000", "00001499", 500),
            "out": ("00001500", "00001999", 500),
            "right": ("00002000", "00002999", 1000),
            "source_quantity": 2000,
        })
        self.assertEqual(result, exact_middle_split("00001000", "00002999",
                                                     "00001500", "00001999"))
        self.assertEqual(
            exact_middle_split("00000000", "00000000", "00000000", "00000000"),
            {"left": None, "out": ("00000000", "00000000", 1),
             "right": None, "source_quantity": 1},
        )

    def test_serial_split_small_interval_oracle(self):
        for source_start in range(8):
            for source_end in range(source_start, 9):
                for physical_start in range(source_start, source_end + 1):
                    for physical_end in range(physical_start, source_end + 1):
                        actual = exact_middle_split(
                            *(f"{n:04d}" for n in
                              (source_start, source_end, physical_start, physical_end))
                        )
                        expected_ranges = (
                            (source_start, physical_start - 1),
                            (physical_start, physical_end),
                            (physical_end + 1, source_end),
                        )
                        for label, (first, last) in zip(("left", "out", "right"), expected_ranges):
                            expected = (f"{first:04d}", f"{last:04d}", last - first + 1) if first <= last else None
                            self.assertEqual(actual[label], expected)
                        self.assertEqual(actual["source_quantity"], source_end - source_start + 1)

    def test_postfacto_no_reranking(self):
        good = dict(signed_range=("00001500", "00001999"), booked_range=("00001500", "00001999"),
                    unique_source=True, sufficient_stock=True, hold_clear=True, no_prior_out=True,
                    owner_confirmed=True)
        self.assertTrue(validate_postfacto_physical(**good))
        with self.assertRaises(GateError):
            validate_postfacto_physical(**dict(good, booked_range=("00001000", "00001499")))
        with self.assertRaises(GateError):
            validate_postfacto_physical(**dict(good, reranked=True))

    def test_session_semantics(self):
        clean = {k: True for k in SESSION_GATES}
        self.assertEqual(classify_global_session(clean), "CLEAN_PASS")
        self.assertEqual(classify_global_session(clean, repaired_historical_defects=True), "REMEDIATED_PASS")
        for key in ("no_orphan_child", "no_active_reservation", "formula_hash_ok", "no_sold_serial_eligible"):
            with self.subTest(key=key):
                self.assertEqual(classify_global_session(dict(clean, **{key: False}),
                                 repaired_historical_defects=True), "BLOCKED_SAFE")
        incomplete = clean.copy()
        incomplete.pop("evidence_ok")
        self.assertEqual(classify_global_session(incomplete), "BLOCKED_SAFE")


if __name__ == "__main__":
    unittest.main()
