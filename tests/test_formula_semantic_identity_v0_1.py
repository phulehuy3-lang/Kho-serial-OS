from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.formula_semantic_identity_v0_1 import (
    EXPORTED_QUERY_WRAPPER,
    FORMULA_SEMANTIC_HASH_ALGORITHM,
    FORMULA_SEMANTIC_HASH_CONTRACT_ID,
    HOLD,
    NATIVE_QUERY,
    PASS,
    assess_formula_semantic_identity,
    compute_formula_contract_hash,
    compute_formula_semantic_hash,
    normalize_query_source,
    normalize_query_text,
    validate_formula_semantic_contract,
    with_computed_formula_contract_hash,
)


def contract():
    return with_computed_formula_contract_hash(
        contract_id="QUERY-CONTRACT-A",
        source="SOURCE_TABLE!A:Z",
        query_text="SELECT A,B,C WHERE C > 0 AND B = TRUE",
        header_rows=1,
        exported_fallback_literal="Header",
    )


def native_formula():
    return (
        '=QUERY(SOURCE_TABLE!A:Z,'
        '"select A,B,C where C > 0 and B = TRUE",1)'
    )


def exported_formula():
    return (
        'IFERROR(__xludf.DUMMYFUNCTION('
        '"QUERY(SOURCE_TABLE!A:Z,'
        '"""select A,B,C where C > 0 and B = TRUE"",1)"),'
        '"Header")'
    )


class FormulaSemanticContractTests(unittest.TestCase):
    def test_clean_contract_is_valid(self) -> None:
        self.assertEqual(validate_formula_semantic_contract(contract()), ())

    def test_contract_hash_drift_is_rejected(self) -> None:
        drifted = replace(contract(), contract_hash="0" * 64)
        self.assertIn(
            "FORMULA_SEMANTICS:CONTRACT_HASH_MISMATCH",
            validate_formula_semantic_contract(drifted),
        )

    def test_boolean_header_rows_is_rejected(self) -> None:
        item = with_computed_formula_contract_hash(
            contract_id="QUERY-CONTRACT-A",
            source="SOURCE_TABLE!A:Z",
            query_text="SELECT A",
            header_rows=True,  # type: ignore[arg-type]
            exported_fallback_literal="Header",
        )
        self.assertIn(
            "FORMULA_SEMANTICS:HEADER_ROWS_INVALID",
            validate_formula_semantic_contract(item),
        )

    def test_hash_algorithm_id_is_versioned(self) -> None:
        self.assertEqual(
            FORMULA_SEMANTIC_HASH_ALGORITHM,
            "SHA256_CANONICAL_QUERY_SEMANTICS_V1",
        )

    def test_semantic_hash_v1_golden_vector(self) -> None:
        digest = compute_formula_semantic_hash(
            source="SOURCE_TABLE!A:Z",
            query_text="SELECT A,B,C WHERE C > 0 AND B = TRUE",
            header_rows=1,
        )
        self.assertEqual(
            digest,
            "296181cfeb95670501db89abf6a97e64"
            "884a3dea82820ecfeb976b4f8d9f29ba",
        )

    def test_formula_contract_hash_v1_golden_vector(self) -> None:
        self.assertEqual(
            compute_formula_contract_hash(contract()),
            "d5941a33c41208c8a7067cdf31025440"
            "5c1cdd0bdd426844157dba7c9d0b4e64",
        )

    def test_hash_contract_id_is_versioned(self) -> None:
        self.assertEqual(
            FORMULA_SEMANTIC_HASH_CONTRACT_ID,
            "FORMULA_QUERY_SEMANTIC_HASH_V1",
        )


class FormulaSemanticIdentityTests(unittest.TestCase):
    def test_native_query_passes(self) -> None:
        result = assess_formula_semantic_identity(
            formula=native_formula(),
            contract=contract(),
        )
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.ready)
        self.assertEqual(result.representation, NATIVE_QUERY)

    def test_exported_wrapper_passes_same_core_semantics(self) -> None:
        native = assess_formula_semantic_identity(
            formula=native_formula(),
            contract=contract(),
        )
        exported = assess_formula_semantic_identity(
            formula=exported_formula(),
            contract=contract(),
        )
        self.assertEqual(exported.status, PASS)
        self.assertEqual(exported.representation, EXPORTED_QUERY_WRAPPER)
        self.assertEqual(
            native.observed_semantic_hash,
            exported.observed_semantic_hash,
        )

    def test_absolute_and_quoted_source_normalizes(self) -> None:
        formula = (
            '=QUERY(\'SOURCE_TABLE\'!$A:$Z,'
            '"SELECT A, B, C WHERE C>0 AND B=TRUE",1)'
        )
        result = assess_formula_semantic_identity(
            formula=formula,
            contract=contract(),
        )
        self.assertEqual(result.status, PASS)

    def test_native_semicolon_separator_is_supported(self) -> None:
        formula = (
            '=QUERY(SOURCE_TABLE!A:Z;'
            '"SELECT A,B,C WHERE C > 0 AND B = TRUE";1)'
        )
        result = assess_formula_semantic_identity(
            formula=formula,
            contract=contract(),
        )
        self.assertEqual(result.status, PASS)

    def test_extra_predicate_fails(self) -> None:
        formula = (
            '=QUERY(SOURCE_TABLE!A:Z,'
            '"SELECT A,B,C WHERE C > 0 AND B = TRUE AND A = 7",1)'
        )
        result = assess_formula_semantic_identity(
            formula=formula,
            contract=contract(),
        )
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "FORMULA_SEMANTICS:QUERY_TEXT_MISMATCH",
            result.blocking_reasons,
        )

    def test_changed_select_order_fails(self) -> None:
        formula = (
            '=QUERY(SOURCE_TABLE!A:Z,'
            '"SELECT A,C,B WHERE C > 0 AND B = TRUE",1)'
        )
        result = assess_formula_semantic_identity(
            formula=formula,
            contract=contract(),
        )
        self.assertIn(
            "FORMULA_SEMANTICS:QUERY_TEXT_MISMATCH",
            result.blocking_reasons,
        )

    def test_wrong_source_fails(self) -> None:
        formula = (
            '=QUERY(OTHER_TABLE!A:Z,'
            '"SELECT A,B,C WHERE C > 0 AND B = TRUE",1)'
        )
        result = assess_formula_semantic_identity(
            formula=formula,
            contract=contract(),
        )
        self.assertIn(
            "FORMULA_SEMANTICS:SOURCE_MISMATCH",
            result.blocking_reasons,
        )

    def test_wrong_header_count_fails(self) -> None:
        formula = (
            '=QUERY(SOURCE_TABLE!A:Z,'
            '"SELECT A,B,C WHERE C > 0 AND B = TRUE",0)'
        )
        result = assess_formula_semantic_identity(
            formula=formula,
            contract=contract(),
        )
        self.assertIn(
            "FORMULA_SEMANTICS:HEADER_ROWS_MISMATCH",
            result.blocking_reasons,
        )

    def test_exported_fallback_drift_fails(self) -> None:
        formula = exported_formula().replace('"Header")', '"Other")')
        result = assess_formula_semantic_identity(
            formula=formula,
            contract=contract(),
        )
        self.assertIn(
            "FORMULA_SEMANTICS:FALLBACK_LITERAL_MISMATCH",
            result.blocking_reasons,
        )

    def test_outer_executable_logic_is_rejected(self) -> None:
        formula = f'=IF(TRUE,{native_formula()},"Header")'
        result = assess_formula_semantic_identity(
            formula=formula,
            contract=contract(),
        )
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "FORMULA_SEMANTICS:UNSUPPORTED_REPRESENTATION",
            result.blocking_reasons,
        )

    def test_blank_formula_fails_closed(self) -> None:
        result = assess_formula_semantic_identity(
            formula="   ",
            contract=contract(),
        )
        self.assertIn(
            "FORMULA_SEMANTICS:FORMULA_MISSING",
            result.blocking_reasons,
        )

    def test_query_normalization_is_conservative(self) -> None:
        self.assertEqual(
            normalize_query_text(
                " select A, B where C>=1 and D <> 2 "
            ),
            "SELECT A,B WHERE C >= 1 AND D <> 2",
        )

    def test_source_normalization_preserves_logical_identity(self) -> None:
        self.assertEqual(
            normalize_query_source("'source_table'!$A:$Z"),
            "SOURCE_TABLE!A:Z",
        )

    def test_semantic_hash_is_deterministic(self) -> None:
        first = compute_formula_semantic_hash(
            source="SOURCE_TABLE!A:Z",
            query_text="SELECT A,B,C WHERE C > 0 AND B = TRUE",
            header_rows=1,
        )
        second = compute_formula_semantic_hash(
            source="'source_table'!$A:$Z",
            query_text=" select A, B, C where C>0 and B=TRUE ",
            header_rows=1,
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
