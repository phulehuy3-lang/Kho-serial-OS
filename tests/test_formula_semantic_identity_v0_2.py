from __future__ import annotations

import unittest

from scripts.formula_semantic_identity_v0_1 import compute_formula_semantic_hash
from scripts.formula_semantic_identity_v0_2 import (
    HOLD,
    PASS,
    assess_formula_semantic_identity_v2,
    compute_formula_contract_hash_v2,
    compute_formula_semantic_hash_v2,
    normalize_query_source_v2,
    normalize_query_text_v2,
    with_computed_formula_contract_hash_v2,
)


def contract(*, source="A1:B10", query_text="select A where B = 'hold'"):
    return with_computed_formula_contract_hash_v2(
        contract_id="QUERY-V2-SYNTH",
        source=source,
        query_text=query_text,
        header_rows=1,
        exported_fallback_literal="",
    )


def assess(*, expected_query="select A where B = 'hold'", actual_query=None,
           source="A1:B10", actual_source=None):
    if actual_query is None:
        actual_query = expected_query
    item = contract(source=source, query_text=expected_query)
    return assess_formula_semantic_identity_v2(
        formula=f'=QUERY({actual_source or source},"{actual_query}",1)',
        contract=item,
    )


class FormulaSemanticIdentityV2Tests(unittest.TestCase):
    def test_literal_case_drift_holds(self):
        result = assess(actual_query="select A where B = 'HOLD'")
        self.assertEqual(result.status, HOLD)

    def test_literal_internal_space_drift_holds(self):
        result = assess(
            expected_query="select A where B = 'A  B'",
            actual_query="select A where B = 'A B'",
        )
        self.assertEqual(result.status, HOLD)

    def test_quoted_sheet_space_drift_holds(self):
        result = assess(
            expected_query="select A",
            actual_query="select A",
            source="'Lot A'!A1:B10",
            actual_source="'LotA'!A1:B10",
        )
        self.assertEqual(result.status, HOLD)

    def test_identifier_case_drift_holds(self):
        result = assess(expected_query="select A", actual_query="select a")
        self.assertEqual(result.status, HOLD)

    def test_verified_keyword_case_and_external_whitespace_equivalence_passes(self):
        result = assess(
            expected_query="SELECT A, B WHERE C>=1 AND D <> 2",
            actual_query=" select A,B where C >= 1 and D<>2 ",
        )
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.ready)

    def test_absolute_and_simple_quoted_source_equivalence_passes(self):
        result = assess(
            expected_query="select A",
            actual_query="SELECT A",
            source="SOURCE_TABLE!A:Z",
            actual_source="'SOURCE_TABLE'!$A:$Z",
        )
        self.assertEqual(result.status, PASS)

    def test_unsupported_query_structure_holds(self):
        result = assess(expected_query="select A", actual_query="select upper(A)")
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "FORMULA_SEMANTICS_V2:UNSUPPORTED_QUERY_STRUCTURE",
            result.blocking_reasons,
        )

    def test_v1_collision_remains_historical_but_v2_separates_literal_case(self):
        v1_a = compute_formula_semantic_hash(
            source="A1:B10",
            query_text="select A where B = 'hold'",
            header_rows=1,
        )
        v1_b = compute_formula_semantic_hash(
            source="A1:B10",
            query_text="select A where B = 'HOLD'",
            header_rows=1,
        )
        self.assertEqual(v1_a, v1_b)

        v2_a = compute_formula_semantic_hash_v2(
            source="A1:B10",
            query_text="select A where B = 'hold'",
            header_rows=1,
        )
        v2_b = compute_formula_semantic_hash_v2(
            source="A1:B10",
            query_text="select A where B = 'HOLD'",
            header_rows=1,
        )
        self.assertNotEqual(v2_a, v2_b)

    def test_v2_semantic_hash_golden_vector(self):
        digest = compute_formula_semantic_hash_v2(
            source="SOURCE_TABLE!A:Z",
            query_text="SELECT A,B,C WHERE C > 0 AND B = TRUE",
            header_rows=1,
        )
        self.assertEqual(
            digest,
            "e1a5731ba7d0de3d8b74f2b57b5af8d4"
            "a0d3bb767da88d903d636d218f1bf07e",
        )

    def test_v2_contract_hash_golden_vector(self):
        item = with_computed_formula_contract_hash_v2(
            contract_id="QUERY-CONTRACT-A",
            source="SOURCE_TABLE!A:Z",
            query_text="SELECT A,B,C WHERE C > 0 AND B = TRUE",
            header_rows=1,
            exported_fallback_literal="Header",
        )
        self.assertEqual(
            compute_formula_contract_hash_v2(item),
            "80bdeca6ae656e0f2895c36a9c2600b3"
            "0aa54af569e627d76f001ddc232b19a0",
        )

    def test_v2_normalizers_preserve_identifier_and_literal_identity(self):
        self.assertEqual(normalize_query_source_v2("'Lot A'!$A:$Z"), "'Lot A'!A:Z")
        self.assertNotEqual(
            normalize_query_source_v2("'Lot A'!A1:B10"),
            normalize_query_source_v2("'LotA'!A1:B10"),
        )
        self.assertNotEqual(
            normalize_query_text_v2("select A where B = 'hold'"),
            normalize_query_text_v2("select a where B = 'HOLD'"),
        )


if __name__ == "__main__":
    unittest.main()
