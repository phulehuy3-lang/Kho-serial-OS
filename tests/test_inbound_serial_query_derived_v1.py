from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.formula_semantic_identity_v0_1 import (
    assess_formula_semantic_identity,
    with_computed_formula_contract_hash,
)
from scripts.inbound_serial_query_derived_v1 import (
    HOLD,
    INBOUND_CONTROL_READY,
    PROFILE_CONTRACT_ID,
    SCENARIO_ID,
    InboundProducerOutcomes,
    InboundProfileContext,
    assess_inbound_materialized_gate_evidence,
    evaluate_inbound_profile,
    materialize_inbound_gate_evidence,
)
from scripts.reconciliation_formula_health_v0_1 import (
    FormulaAnchorSnapshot,
    exact_source_derived_reconciliation,
    formula_anchors_healthy,
)
from scripts.required_gate_set_preflight_v0_1 import MaterializedGateEvidence
from scripts.serial_interval_integrity_v0_1 import (
    SerialInterval,
    find_overlaps,
    serial_range_quantity_matches,
)
from scripts.source_readback_v0_1 import (
    CONTRACT_ID as READBACK_CONTRACT_ID,
    MaterializedSourceRecord,
    SourceFieldValue,
    SourceReadbackRequest,
    evaluate_source_readback,
)
from scripts.source_role_boundary_v0_1 import (
    BUSINESS_WRITE,
    CONTRACT_ID as ROLE_CONTRACT_ID,
    DERIVED_READ_ONLY,
    SOURCE_OF_TRUTH,
    SourceRoleBoundaryRequest,
    evaluate_source_role_boundary,
)


class InboundSerialProfileTests(unittest.TestCase):
    def context(self):
        return InboundProfileContext(
            contract_id=PROFILE_CONTRACT_ID,
            task_id="TASK-1",
            scope_id="SCOPE-1",
            capture_marker="CAPTURE-1",
        )

    def source_record(self, quantity=2):
        return MaterializedSourceRecord(
            task_id="TASK-1",
            scope_id="SCOPE-1",
            capture_marker="CAPTURE-1",
            fields=(
                SourceFieldValue("serial_start", "000100"),
                SourceFieldValue("serial_end", "000101"),
                SourceFieldValue("quantity", quantity),
            ),
        )

    def formula_assessment(self, query_text="select A"):
        contract = with_computed_formula_contract_hash(
            contract_id="QUERY-INBOUND-1",
            source="A1:B10",
            query_text="select A",
            header_rows=1,
            exported_fallback_literal="",
        )
        formula = f'=QUERY(A1:B10,"{query_text}",1)'
        return assess_formula_semantic_identity(
            formula=formula,
            contract=contract,
        )

    def valid_outcomes(self):
        role = evaluate_source_role_boundary(
            SourceRoleBoundaryRequest(
                contract_id=ROLE_CONTRACT_ID,
                region_roles=(SOURCE_OF_TRUTH,),
                requested_operation=BUSINESS_WRITE,
            )
        )
        expected = self.source_record()
        readback = self.source_record()
        source_readback = evaluate_source_readback(
            SourceReadbackRequest(
                contract_id=READBACK_CONTRACT_ID,
                expected_record=expected,
                readback_record=readback,
            )
        )
        interval = SerialInterval(100, 101)
        serial_quantity = serial_range_quantity_matches(interval, 2)
        overlap_free = not bool(
            find_overlaps(
                (
                    interval,
                    SerialInterval(200, 201),
                )
            )
        )
        reconciliation = exact_source_derived_reconciliation(
            {"quantity": 2},
            {"quantity": 2},
        )
        formula_health = formula_anchors_healthy(
            (FormulaAnchorSnapshot("query_anchor", True, None),)
        )
        formula_semantics = self.formula_assessment()
        return InboundProducerOutcomes(
            source_role_boundary=role,
            source_readback=source_readback,
            serial_range_quantity=serial_quantity,
            serial_overlap_free=overlap_free,
            source_derived_reconciliation=reconciliation,
            formula_health=formula_health,
            formula_semantics=formula_semantics,
        )

    def assert_hold(self, result):
        self.assertEqual(result.status, HOLD)
        self.assertFalse(result.ready)
        self.assertFalse(result.production_write_authorized)

    def test_all_seven_producers_ready_returns_inbound_control_ready_only(self):
        result = evaluate_inbound_profile(
            self.context(),
            self.valid_outcomes(),
            hold_conflict=False,
        )
        self.assertEqual(result.status, INBOUND_CONTROL_READY)
        self.assertTrue(result.ready)
        self.assertEqual(result.blocking_reasons, ())
        self.assertEqual(result.preflight_status, "PASS")
        self.assertEqual(result.release_status, "READY_FOR_RELEASE")
        self.assertFalse(result.production_write_authorized)

    def test_missing_extra_duplicate_and_binding_tamper_hold_before_release(self):
        context = self.context()
        evidence = materialize_inbound_gate_evidence(
            context,
            self.valid_outcomes(),
        )
        cases = []

        cases.append(evidence[:-1])
        cases.append(
            evidence
            + (
                MaterializedGateEvidence(
                    gate_id="extra_gate",
                    scenario_id=SCENARIO_ID,
                    task_id=context.task_id,
                    scope_id=context.scope_id,
                    capture_marker=context.capture_marker,
                    value=True,
                ),
            )
        )
        cases.append(evidence + (evidence[0],))
        cases.append(
            (
                replace(evidence[0], task_id="TASK-2"),
                *evidence[1:],
            )
        )
        cases.append(
            (
                replace(evidence[0], capture_marker="CAPTURE-2"),
                *evidence[1:],
            )
        )

        for tampered in cases:
            with self.subTest(tampered=tampered):
                result = assess_inbound_materialized_gate_evidence(
                    context,
                    tuple(tampered),
                    hold_conflict=False,
                )
                self.assert_hold(result)
                self.assertEqual(result.release_status, None)
                self.assertTrue(
                    all(reason.startswith("preflight:") for reason in result.blocking_reasons)
                )

    def test_source_role_failure_holds(self):
        derived = evaluate_source_role_boundary(
            SourceRoleBoundaryRequest(
                contract_id=ROLE_CONTRACT_ID,
                region_roles=(DERIVED_READ_ONLY,),
                requested_operation=BUSINESS_WRITE,
            )
        )
        result = evaluate_inbound_profile(
            self.context(),
            replace(self.valid_outcomes(), source_role_boundary=derived),
            hold_conflict=False,
        )
        self.assert_hold(result)
        self.assertIn(
            "release:source_role_boundary:FAIL",
            result.blocking_reasons,
        )

    def test_source_readback_failure_holds(self):
        expected = self.source_record()
        mismatch = self.source_record(quantity=3)
        failed = evaluate_source_readback(
            SourceReadbackRequest(
                contract_id=READBACK_CONTRACT_ID,
                expected_record=expected,
                readback_record=mismatch,
            )
        )
        result = evaluate_inbound_profile(
            self.context(),
            replace(self.valid_outcomes(), source_readback=failed),
            hold_conflict=False,
        )
        self.assert_hold(result)
        self.assertIn(
            "release:source_readback:FAIL",
            result.blocking_reasons,
        )

    def test_each_native_boolean_gate_failure_holds_independently(self):
        names = (
            "serial_range_quantity",
            "serial_overlap_free",
            "source_derived_reconciliation",
            "formula_health",
        )
        for name in names:
            with self.subTest(name=name):
                result = evaluate_inbound_profile(
                    self.context(),
                    replace(self.valid_outcomes(), **{name: False}),
                    hold_conflict=False,
                )
                self.assert_hold(result)
                self.assertIn(f"release:{name}:FAIL", result.blocking_reasons)

    def test_formula_semantic_drift_holds(self):
        drifted = self.formula_assessment(query_text="select B")
        result = evaluate_inbound_profile(
            self.context(),
            replace(self.valid_outcomes(), formula_semantics=drifted),
            hold_conflict=False,
        )
        self.assert_hold(result)
        self.assertIn(
            "release:formula_semantics:FAIL",
            result.blocking_reasons,
        )

    def test_none_gate_is_structurally_valid_but_release_holds(self):
        result = evaluate_inbound_profile(
            self.context(),
            replace(self.valid_outcomes(), formula_health=None),
            hold_conflict=False,
        )
        self.assert_hold(result)
        self.assertEqual(result.preflight_status, "PASS")
        self.assertIn(
            "release:formula_health:UNKNOWN",
            result.blocking_reasons,
        )

    def test_hold_conflict_present_or_unknown_holds(self):
        for hold_conflict in (True, None):
            with self.subTest(hold_conflict=hold_conflict):
                result = evaluate_inbound_profile(
                    self.context(),
                    self.valid_outcomes(),
                    hold_conflict=hold_conflict,
                )
                self.assert_hold(result)
                self.assertEqual(result.preflight_status, "PASS")

    def test_pseudo_boolean_is_stopped_by_preflight(self):
        result = evaluate_inbound_profile(
            self.context(),
            replace(self.valid_outcomes(), serial_range_quantity="PASS"),
            hold_conflict=False,
        )
        self.assert_hold(result)
        self.assertEqual(result.release_status, None)
        self.assertIn("preflight:VALUE_INVALID", result.blocking_reasons)

    def test_invalid_hold_conflict_is_holding_result_not_exception(self):
        result = evaluate_inbound_profile(
            self.context(),
            self.valid_outcomes(),
            hold_conflict="NO_HOLD",
        )
        self.assert_hold(result)
        self.assertEqual(result.preflight_status, "PASS")
        self.assertIn("release:INPUT_INVALID", result.blocking_reasons)

    def test_inconsistent_structured_result_becomes_unknown_not_pass(self):
        good = self.valid_outcomes()
        inconsistent = replace(
            good.source_role_boundary,
            status="PASS",
            boundary_pass=False,
            blocking_reasons=(),
        )
        result = evaluate_inbound_profile(
            self.context(),
            replace(good, source_role_boundary=inconsistent),
            hold_conflict=False,
        )
        self.assert_hold(result)
        self.assertIn(
            "release:source_role_boundary:UNKNOWN",
            result.blocking_reasons,
        )

    def test_invalid_profile_context_holds_before_preflight(self):
        bad_context = InboundProfileContext(
            contract_id="WRONG",
            task_id=" TASK-1",
            scope_id="SCOPE-1",
            capture_marker="CAPTURE-1",
        )
        result = evaluate_inbound_profile(
            bad_context,
            self.valid_outcomes(),
            hold_conflict=False,
        )
        self.assert_hold(result)
        self.assertEqual(result.release_status, None)
        self.assertIn("PROFILE_CONTRACT_INVALID", result.blocking_reasons)
        self.assertIn("PROFILE_CONTEXT_INVALID", result.blocking_reasons)


if __name__ == "__main__":
    unittest.main()
