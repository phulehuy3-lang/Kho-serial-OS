from __future__ import annotations

import unittest

from scripts.source_role_boundary_v0_1 import (
    BUSINESS_WRITE,
    CONTRACT_ID,
    DERIVED_READ_ONLY,
    SOURCE_OF_TRUTH,
    SourceRoleBoundaryRequest,
    evaluate_source_role_boundary,
)


class SourceRoleBoundaryTests(unittest.TestCase):
    def assess(self, roles, operation=BUSINESS_WRITE, contract_id=CONTRACT_ID):
        return evaluate_source_role_boundary(
            SourceRoleBoundaryRequest(
                contract_id=contract_id,
                region_roles=roles,
                requested_operation=operation,
            )
        )

    def assert_hold(self, result, reason):
        self.assertEqual(result.status, "HOLD")
        self.assertFalse(result.boundary_pass)
        self.assertIn(reason, result.blocking_reasons)
        self.assertFalse(result.production_write_authorized)

    def test_exact_source_of_truth_business_write_passes_boundary_only(self):
        result = self.assess((SOURCE_OF_TRUTH,))
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.boundary_pass)
        self.assertEqual(result.blocking_reasons, ())
        self.assertFalse(result.production_write_authorized)

    def test_derived_read_only_blocks_business_write(self):
        self.assert_hold(
            self.assess((DERIVED_READ_ONLY,)),
            "DERIVED_READ_ONLY_WRITE_BLOCKED",
        )

    def test_both_roles_are_contradictory(self):
        result = self.assess((SOURCE_OF_TRUTH, DERIVED_READ_ONLY))
        self.assert_hold(result, "CLASSIFICATION_CONTRADICTORY")

    def test_duplicate_same_role_fails_exact_one_cardinality(self):
        self.assert_hold(
            self.assess((SOURCE_OF_TRUTH, SOURCE_OF_TRUTH)),
            "CLASSIFICATION_CARDINALITY_INVALID",
        )

    def test_empty_tuple_is_missing_classification(self):
        self.assert_hold(self.assess(()), "CLASSIFICATION_MISSING")

    def test_list_is_not_coerced_to_tuple(self):
        self.assert_hold(
            self.assess([SOURCE_OF_TRUTH]),
            "CLASSIFICATION_CONTAINER_INVALID",
        )

    def test_blank_whitespace_unknown_and_lowercase_roles_are_invalid(self):
        for role in ("", " ", " SOURCE_OF_TRUTH", "SOURCE_OF_TRUTH ", "source_of_truth", "OTHER"):
            with self.subTest(role=role):
                self.assert_hold(
                    self.assess((role,)),
                    "CLASSIFICATION_INVALID",
                )

    def test_non_string_role_is_invalid(self):
        self.assert_hold(self.assess((1,)), "CLASSIFICATION_INVALID")

    def test_invalid_operations_fail_closed_without_coercion(self):
        for operation in ("", " ", "WRITE", " BUSINESS_WRITE", "BUSINESS_WRITE ", 1, True, None):
            with self.subTest(operation=operation):
                self.assert_hold(
                    self.assess((SOURCE_OF_TRUTH,), operation=operation),
                    "OPERATION_INVALID",
                )

    def test_wrong_contract_identity_holds(self):
        self.assert_hold(
            self.assess((SOURCE_OF_TRUTH,), contract_id="SOURCE_ROLE_BOUNDARY_V2"),
            "CONTRACT_INVALID",
        )

    def test_multiple_blockers_are_sorted_deterministically(self):
        result = self.assess(
            (SOURCE_OF_TRUTH, DERIVED_READ_ONLY),
            operation="WRITE",
            contract_id="WRONG",
        )
        self.assertEqual(result.status, "HOLD")
        self.assertEqual(
            result.blocking_reasons,
            tuple(sorted(result.blocking_reasons)),
        )
        self.assertIn("CLASSIFICATION_CONTRADICTORY", result.blocking_reasons)
        self.assertIn("CONTRACT_INVALID", result.blocking_reasons)
        self.assertIn("OPERATION_INVALID", result.blocking_reasons)
        self.assertFalse(result.production_write_authorized)


    def test_malformed_request_holds_without_exception(self):
        for request in (None, True, {}, "SOURCE_OF_TRUTH"):
            with self.subTest(request=request):
                result = evaluate_source_role_boundary(request)  # type: ignore[arg-type]
                self.assert_hold(result, "REQUEST_INVALID")


if __name__ == "__main__":
    unittest.main()
