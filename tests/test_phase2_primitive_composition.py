from __future__ import annotations

import unittest

from scripts.fail_closed_release_gates_v0_1 import (
    HOLD,
    READY_FOR_RELEASE,
    evaluate_release_gates,
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


def composed_decision(
    *,
    source_metrics=None,
    derived_metrics=None,
    anchors=None,
    intervals=None,
    available=200,
    requested=150,
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

    gates = {
        "formula_health": formula_anchors_healthy(anchors),
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
