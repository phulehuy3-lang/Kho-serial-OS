from __future__ import annotations

import unittest

from scripts.reconciliation_formula_health_v0_1 import (
    FormulaAnchorSnapshot,
    exact_source_derived_reconciliation,
    formula_anchor_healthy,
    formula_anchors_healthy,
)


class SourceDerivedReconciliationTests(unittest.TestCase):
    def test_exact_metrics_pass(self) -> None:
        source = {
            "item_count": 12,
            "quantity_total": 480,
            "healthy": True,
        }
        derived = {
            "item_count": 12,
            "quantity_total": 480,
            "healthy": True,
        }
        self.assertTrue(
            exact_source_derived_reconciliation(source, derived)
        )

    def test_value_mismatch_fails(self) -> None:
        self.assertFalse(
            exact_source_derived_reconciliation(
                {"quantity_total": 100},
                {"quantity_total": 99},
            )
        )

    def test_missing_key_fails(self) -> None:
        self.assertFalse(
            exact_source_derived_reconciliation(
                {"quantity_total": 100, "item_count": 2},
                {"quantity_total": 100},
            )
        )

    def test_extra_derived_key_fails(self) -> None:
        self.assertFalse(
            exact_source_derived_reconciliation(
                {"quantity_total": 100},
                {"quantity_total": 100, "extra": 0},
            )
        )

    def test_bool_and_int_do_not_reconcile(self) -> None:
        self.assertFalse(
            exact_source_derived_reconciliation(
                {"healthy": True},
                {"healthy": 1},
            )
        )

    def test_float_and_int_do_not_reconcile(self) -> None:
        self.assertFalse(
            exact_source_derived_reconciliation(
                {"quantity_total": 100},
                {"quantity_total": 100.0},
            )
        )

    def test_blank_metric_key_fails_closed(self) -> None:
        self.assertFalse(
            exact_source_derived_reconciliation(
                {"": 1},
                {"": 1},
            )
        )

    def test_non_string_metric_key_fails_closed(self) -> None:
        self.assertFalse(
            exact_source_derived_reconciliation(
                {1: "value"},
                {1: "value"},
            )
        )


class FormulaAnchorHealthTests(unittest.TestCase):
    def test_present_error_free_anchor_passes(self) -> None:
        self.assertTrue(
            formula_anchor_healthy(
                FormulaAnchorSnapshot("VIEW_A", True)
            )
        )

    def test_blank_error_text_is_healthy(self) -> None:
        self.assertTrue(
            formula_anchor_healthy(
                FormulaAnchorSnapshot("VIEW_A", True, "   ")
            )
        )

    def test_ref_error_fails(self) -> None:
        self.assertFalse(
            formula_anchor_healthy(
                FormulaAnchorSnapshot("VIEW_A", True, "#REF!")
            )
        )

    def test_spill_error_fails(self) -> None:
        self.assertFalse(
            formula_anchor_healthy(
                FormulaAnchorSnapshot("VIEW_A", True, "#SPILL!")
            )
        )

    def test_any_reported_error_fails(self) -> None:
        self.assertFalse(
            formula_anchor_healthy(
                FormulaAnchorSnapshot("VIEW_A", True, "#VALUE!")
            )
        )

    def test_missing_formula_fails(self) -> None:
        self.assertFalse(
            formula_anchor_healthy(
                FormulaAnchorSnapshot("VIEW_A", False)
            )
        )

    def test_non_boolean_formula_present_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            FormulaAnchorSnapshot(
                "VIEW_A",
                1,  # type: ignore[arg-type]
            )

    def test_blank_anchor_name_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FormulaAnchorSnapshot("   ", True)

    def test_non_text_error_code_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            FormulaAnchorSnapshot(
                "VIEW_A",
                True,
                7,  # type: ignore[arg-type]
            )

    def test_all_unique_anchors_must_be_healthy(self) -> None:
        self.assertTrue(
            formula_anchors_healthy(
                (
                    FormulaAnchorSnapshot("VIEW_A", True),
                    FormulaAnchorSnapshot("VIEW_B", True),
                )
            )
        )

    def test_one_bad_anchor_blocks_group(self) -> None:
        self.assertFalse(
            formula_anchors_healthy(
                (
                    FormulaAnchorSnapshot("VIEW_A", True),
                    FormulaAnchorSnapshot("VIEW_B", True, "#REF!"),
                )
            )
        )

    def test_duplicate_anchor_names_fail_closed(self) -> None:
        self.assertFalse(
            formula_anchors_healthy(
                (
                    FormulaAnchorSnapshot("VIEW_A", True),
                    FormulaAnchorSnapshot("VIEW_A", True),
                )
            )
        )

    def test_empty_anchor_evidence_fails_closed(self) -> None:
        self.assertFalse(formula_anchors_healthy(()))


if __name__ == "__main__":
    unittest.main()
