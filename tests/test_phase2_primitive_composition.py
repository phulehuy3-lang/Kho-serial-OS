from __future__ import annotations

import unittest

from scripts.fail_closed_release_gates_v0_1 import (
    HOLD,
    READY_FOR_RELEASE,
    evaluate_release_gates,
)
from scripts.formula_semantic_identity_v0_1 import (
    assess_formula_semantic_identity,
    with_computed_formula_contract_hash,
)
from scripts.negative_stock_prevention_v0_1 import (
    issue_would_create_negative_stock,
)
from scripts.reconciliation_formula_health_v0_1 import (
    FormulaAnchorSnapshot,
    exact_source_derived_reconciliation,
    formula_anchors_healthy,
)
from scripts.serial_interval_integrity_v0_1 import (
    SerialInterval,
    find_overlaps,
)


def formula_contract():
    return with_computed_formula_contract_hash(
        contract_id="QUERY-CONTRACT-COMPOSED",
        source="SOURCE_VIEW!A:Z",
        query_text="SELECT A,B WHERE B > 0",
        header_rows=1,
        exported_fallback_literal="Header",
    )


def canonical_formula() -> str:
    return '=QUERY(SOURCE_VIEW!A:Z,"SELECT A,B WHERE B > 0",1)'


def composed_decision(
    *,
    source_metrics=None,
    derived_metrics=None,
    anchors=None,
    intervals=None,
    available=200,
    requested=150,
    formula=None,
):
    source_metrics = (
        {"item_count": 2, "quantity_total": 200}
        if source_metrics is None
        else source_metrics
    )
    derived_metrics = (
        {"item_count": 2, "quantity_total": 200}
        if derived_metrics is None
        else derived_metrics
    )
    anchors = (
        (
            FormulaAnchorSnapshot("VIEW_A", True),
            FormulaAnchorSnapshot("VIEW_B", True),
        )
        if anchors is None
        else anchors
    )
    intervals = (
        (SerialInterval(100, 199), SerialInterval(200, 299))
        if intervals is None
        else intervals
    )
    formula = canonical_formula() if formula is None else formula

    semantic = assess_formula_semantic_identity(
        formula=formula,
        contract=formula_contract(),
    )

    gates = {
        "formula_health": formula_anchors_healthy(anchors),
        "formula_semantic_identity": semantic.ready,
        "interval_integrity": not bool(find_overlaps(intervals)),
        "non_negative_stock": not issue_would_create_negative_stock(
            available,
            requested,
        ),
        "source_derived_reconciliation": (
            exact_source_derived_reconciliation(
                source_metrics,
                derived_metrics,
            )
        ),
    }
    return evaluate_release_gates(gates, hold_conflict=False)


class Phase2PrimitiveCompositionTests(unittest.TestCase):
    def test_all_primitive_evidence_can_compose_to_ready(self) -> None:
        decision = composed_decision()
        self.assertEqual(decision.status, READY_FOR_RELEASE)
        self.assertTrue(decision.ready)

    def test_reconciliation_drift_blocks_composed_release(self) -> None:
        decision = composed_decision(
            derived_metrics={"item_count": 2, "quantity_total": 199}
        )
        self.assertEqual(decision.status, HOLD)
        self.assertIn(
            "source_derived_reconciliation:FAIL",
            decision.blocking_gates,
        )

    def test_formula_error_blocks_composed_release(self) -> None:
        decision = composed_decision(
            anchors=(FormulaAnchorSnapshot("VIEW_A", True, "#REF!"),)
        )
        self.assertEqual(decision.status, HOLD)
        self.assertIn("formula_health:FAIL", decision.blocking_gates)

    def test_formula_semantic_drift_blocks_even_when_health_passes(
        self,
    ) -> None:
        decision = composed_decision(
            formula='=QUERY(SOURCE_VIEW!A:Z,"SELECT A,B WHERE B >= 0",1)'
        )
        self.assertEqual(decision.status, HOLD)
        self.assertIn(
            "formula_semantic_identity:FAIL",
            decision.blocking_gates,
        )
        self.assertNotIn(
            "formula_health:FAIL",
            decision.blocking_gates,
        )

    def test_formula_error_blocks_even_when_semantics_pass(self) -> None:
        decision = composed_decision(
            anchors=(
                FormulaAnchorSnapshot("VIEW_A", True, "#REF!"),
            ),
            formula=canonical_formula(),
        )
        self.assertEqual(decision.status, HOLD)
        self.assertIn("formula_health:FAIL", decision.blocking_gates)
        self.assertNotIn(
            "formula_semantic_identity:FAIL",
            decision.blocking_gates,
        )

    def test_health_and_semantic_failure_both_remain_visible(self) -> None:
        decision = composed_decision(
            anchors=(
                FormulaAnchorSnapshot("VIEW_A", True, "#SPILL!"),
            ),
            formula='=QUERY(SOURCE_VIEW!A:Z,"SELECT B,A WHERE B > 0",1)',
        )
        self.assertEqual(decision.status, HOLD)
        self.assertIn("formula_health:FAIL", decision.blocking_gates)
        self.assertIn(
            "formula_semantic_identity:FAIL",
            decision.blocking_gates,
        )

    def test_overlap_blocks_composed_release(self) -> None:
        decision = composed_decision(
            intervals=(
                SerialInterval(100, 200),
                SerialInterval(200, 300),
            )
        )
        self.assertEqual(decision.status, HOLD)
        self.assertIn("interval_integrity:FAIL", decision.blocking_gates)

    def test_negative_stock_blocks_composed_release(self) -> None:
        decision = composed_decision(available=10, requested=11)
        self.assertEqual(decision.status, HOLD)
        self.assertIn("non_negative_stock:FAIL", decision.blocking_gates)


if __name__ == "__main__":
    unittest.main()
