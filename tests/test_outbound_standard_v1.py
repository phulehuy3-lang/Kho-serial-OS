from __future__ import annotations

from dataclasses import replace
from datetime import date
import unittest

from scripts.outbound_standard_v1 import (
    ALLOCATION_FIELDS,
    CLEAN_PASS,
    CURRENT_STATE_SAFE_EXECUTION,
    FAMILY_TEMPLATE_FALLBACK,
    GENERIC_TEMPLATE_FALLBACK,
    HISTORICAL_AS_OF_RECONSTRUCTION,
    PARTNER_SPECIFIC_CANONICAL,
    POSTFACTO_PHYSICAL_DELIVERY,
    READ_ONLY_NO_PRODUCTION_MUTATION,
    REMEDIATED_PASS,
    OutboundCloseInputs,
    OutboundControlError,
    SinglePassState,
    bind_allocation_fields,
    choose_template_authority,
    classify_outbound_close,
    classify_single_pass_close,
    resolve_effective_date_mode,
    validate_rank_plan_decision,
)


class OutboundStandardV1Tests(unittest.TestCase):
    def test_backdated_without_delivery_proof_uses_current_safe_mode(self):
        result = resolve_effective_date_mode(
            document_date=date(2026, 9, 29),
            execution_date=date(2026, 10, 2),
        )
        self.assertEqual(result.mode, CURRENT_STATE_SAFE_EXECUTION)

    def test_proven_prior_delivery_uses_postfacto_mode(self):
        result = resolve_effective_date_mode(
            document_date=date(2026, 9, 29),
            execution_date=date(2026, 10, 2),
            prior_delivery_proven=True,
        )
        self.assertEqual(result.mode, POSTFACTO_PHYSICAL_DELIVERY)

    def test_historical_reconstruction_is_explicit(self):
        result = resolve_effective_date_mode(
            document_date=date(2026, 9, 29),
            execution_date=date(2026, 10, 2),
            historical_reconstruction=True,
        )
        self.assertEqual(result.mode, HISTORICAL_AS_OF_RECONSTRUCTION)

    def test_ambiguous_date_mode_blocks(self):
        with self.assertRaises(OutboundControlError):
            resolve_effective_date_mode(
                document_date=date(2026, 9, 29),
                execution_date=date(2026, 10, 2),
                prior_delivery_proven=True,
                historical_reconstruction=True,
            )

    def test_template_priority_partner_family_generic(self):
        self.assertEqual(
            choose_template_authority(
                partner_template_id="PARTNER-A",
                family_template_id="FAMILY-A",
                generic_template_id="GENERIC-A",
            ).template_class,
            PARTNER_SPECIFIC_CANONICAL,
        )
        self.assertEqual(
            choose_template_authority(
                family_template_id="FAMILY-A",
                generic_template_id="GENERIC-A",
            ).template_class,
            FAMILY_TEMPLATE_FALLBACK,
        )
        self.assertEqual(
            choose_template_authority(
                generic_template_id="GENERIC-A",
            ).template_class,
            GENERIC_TEMPLATE_FALLBACK,
        )

    def test_missing_template_blocks(self):
        with self.assertRaises(OutboundControlError):
            choose_template_authority()

    def test_allocation_header_binding_exact_and_reordered(self):
        exact = bind_allocation_fields(ALLOCATION_FIELDS)
        self.assertEqual(exact["RankPlanDecision"], 15)
        reordered = list(ALLOCATION_FIELDS)
        reordered[0], reordered[1] = reordered[1], reordered[0]
        mapped = bind_allocation_fields(reordered)
        self.assertEqual(set(mapped), set(ALLOCATION_FIELDS))

    def test_allocation_header_missing_duplicate_or_wrong_blocks(self):
        for headers in (
            ALLOCATION_FIELDS[:-1],
            ALLOCATION_FIELDS[:-1] + (ALLOCATION_FIELDS[-2],),
            ALLOCATION_FIELDS[:-1] + ("UnexpectedField",),
        ):
            with self.subTest(headers=headers), self.assertRaises(
                OutboundControlError
            ):
                bind_allocation_fields(headers)

    def test_rank_plan_must_be_formula_owned(self):
        self.assertTrue(
            validate_rank_plan_decision(
                formula_present=True,
                evaluated_value="PASS_PLAN_RANK",
            )
        )
        with self.assertRaises(OutboundControlError):
            validate_rank_plan_decision(
                formula_present=False,
                evaluated_value="PASS_PLAN_RANK",
            )
        with self.assertRaises(OutboundControlError):
            validate_rank_plan_decision(
                formula_present=True,
                evaluated_value="BLOCK",
            )

    def test_single_pass_clean_and_remediated(self):
        base = SinglePassState(True, True, 1, True, True, False)
        self.assertEqual(classify_single_pass_close(base), CLEAN_PASS)
        self.assertEqual(
            classify_single_pass_close(
                replace(base, repaired_historical_defect=True)
            ),
            REMEDIATED_PASS,
        )

    def test_single_pass_multiple_mutations_or_missing_readback_blocks(self):
        for state in (
            SinglePassState(True, True, 2, True, True),
            SinglePassState(True, True, 1, False, True),
            SinglePassState(False, True, 1, True, True),
        ):
            with self.subTest(state=state), self.assertRaises(
                OutboundControlError
            ):
                classify_single_pass_close(state)

    def _close_inputs(self, **changes):
        values = dict(
            execution_mode=CURRENT_STATE_SAFE_EXECUTION,
            template_class=GENERIC_TEMPLATE_FALLBACK,
            allocation_plan_pass=True,
            hold_clear=True,
            duplicate_prewrite_pass=True,
            postwrite_readback_pass=True,
            final_anti_replay_lock=True,
            repaired_historical_defect=False,
        )
        values.update(changes)
        return OutboundCloseInputs(**values)

    def test_standard_outbound_closes_clean(self):
        self.assertEqual(
            classify_outbound_close(self._close_inputs()),
            CLEAN_PASS,
        )

    def test_repaired_outbound_is_never_clean(self):
        self.assertEqual(
            classify_outbound_close(
                self._close_inputs(repaired_historical_defect=True)
            ),
            REMEDIATED_PASS,
        )

    def test_historical_reconstruction_never_authorizes_mutation_close(self):
        self.assertEqual(
            classify_outbound_close(
                self._close_inputs(
                    execution_mode=HISTORICAL_AS_OF_RECONSTRUCTION,
                    allocation_plan_pass=False,
                    hold_clear=False,
                    duplicate_prewrite_pass=False,
                    postwrite_readback_pass=False,
                    final_anti_replay_lock=False,
                )
            ),
            READ_ONLY_NO_PRODUCTION_MUTATION,
        )

    def test_prewrite_or_close_gate_failure_blocks(self):
        for changes in (
            {"allocation_plan_pass": False},
            {"hold_clear": False},
            {"duplicate_prewrite_pass": False},
            {"postwrite_readback_pass": False},
            {"final_anti_replay_lock": False},
        ):
            with self.subTest(changes=changes), self.assertRaises(
                OutboundControlError
            ):
                classify_outbound_close(self._close_inputs(**changes))

    def test_strict_boolean_semantics(self):
        for bad in ("TRUE", "FALSE", 1, 0, None):
            with self.subTest(bad=bad), self.assertRaises(
                OutboundControlError
            ):
                classify_outbound_close(
                    self._close_inputs(allocation_plan_pass=bad)
                )


if __name__ == "__main__":
    unittest.main()
