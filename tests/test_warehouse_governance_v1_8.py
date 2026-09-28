"""Synthetic regressions for the 28 September control-plane defects."""

import unittest

from scripts.warehouse_governance_v1_8 import (
    GateError, PROTECTED, SESSION_GATES, classify_global_session,
    composite_identity, duplicate_decision, exact_middle_split, formula_hash,
    validate_correction, validate_formula_snapshot, validate_inbound_touch_set,
    validate_postfacto_physical, validate_transition,
)


class GovernanceTests(unittest.TestCase):
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
