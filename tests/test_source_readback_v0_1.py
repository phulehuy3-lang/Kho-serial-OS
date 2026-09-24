from __future__ import annotations

import unittest

from scripts.source_readback_v0_1 import (
    CONTRACT_ID,
    MaterializedSourceRecord,
    SourceFieldValue,
    SourceReadbackRequest,
    evaluate_source_readback,
)


class SourceReadbackTests(unittest.TestCase):
    def record(
        self,
        fields,
        task_id="TASK-1",
        scope_id="SCOPE-1",
        capture_marker="CAPTURE-1",
    ):
        return MaterializedSourceRecord(
            task_id=task_id,
            scope_id=scope_id,
            capture_marker=capture_marker,
            fields=fields,
        )

    def assess(self, expected, readback, contract_id=CONTRACT_ID):
        return evaluate_source_readback(
            SourceReadbackRequest(
                contract_id=contract_id,
                expected_record=expected,
                readback_record=readback,
            )
        )

    def assert_hold(self, result, reason):
        self.assertEqual(result.status, "HOLD")
        self.assertFalse(result.readback_match)
        self.assertIn(reason, result.blocking_reasons)
        self.assertFalse(result.production_write_authorized)

    def test_exact_match_passes_without_write_authority(self):
        expected = self.record(
            (
                SourceFieldValue("serial_start", "000123"),
                SourceFieldValue("quantity", 2),
                SourceFieldValue("active", True),
                SourceFieldValue("note", None),
            )
        )
        readback = self.record(
            (
                SourceFieldValue("note", None),
                SourceFieldValue("active", True),
                SourceFieldValue("quantity", 2),
                SourceFieldValue("serial_start", "000123"),
            )
        )
        result = self.assess(expected, readback)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.readback_match)
        self.assertEqual(result.blocking_reasons, ())
        self.assertFalse(result.production_write_authorized)

    def test_missing_readback_is_distinct(self):
        expected = self.record((SourceFieldValue("quantity", 2),))
        self.assert_hold(self.assess(expected, None), "READBACK_MISSING")

    def test_wrong_contract_identity_holds(self):
        record = self.record((SourceFieldValue("quantity", 2),))
        self.assert_hold(
            self.assess(record, record, contract_id="SOURCE_READBACK_V2"),
            "CONTRACT_INVALID",
        )

    def test_malformed_expected_record_holds(self):
        invalid = self.record(
            (SourceFieldValue(" quantity", 2),)
        )
        valid = self.record((SourceFieldValue("quantity", 2),))
        self.assert_hold(
            self.assess(invalid, valid),
            "EXPECTED_RECORD_INVALID",
        )

    def test_malformed_readback_record_holds(self):
        expected = self.record((SourceFieldValue("quantity", 2),))
        invalid = self.record(
            (SourceFieldValue("quantity", 2.0),)
        )
        self.assert_hold(
            self.assess(expected, invalid),
            "READBACK_RECORD_INVALID",
        )

    def test_binding_drift_holds(self):
        expected = self.record((SourceFieldValue("quantity", 2),))
        variants = (
            self.record((SourceFieldValue("quantity", 2),), task_id="TASK-2"),
            self.record((SourceFieldValue("quantity", 2),), scope_id="SCOPE-2"),
            self.record(
                (SourceFieldValue("quantity", 2),),
                capture_marker="CAPTURE-2",
            ),
        )
        for readback in variants:
            with self.subTest(readback=readback):
                self.assert_hold(
                    self.assess(expected, readback),
                    "BINDING_MISMATCH",
                )

    def test_missing_and_extra_fields_hold(self):
        expected = self.record(
            (
                SourceFieldValue("serial_start", "000123"),
                SourceFieldValue("quantity", 2),
            )
        )
        missing = self.record((SourceFieldValue("serial_start", "000123"),))
        extra = self.record(
            (
                SourceFieldValue("serial_start", "000123"),
                SourceFieldValue("quantity", 2),
                SourceFieldValue("extra", "x"),
            )
        )
        self.assert_hold(
            self.assess(expected, missing),
            "FIELD_SET_MISMATCH",
        )
        self.assert_hold(
            self.assess(expected, extra),
            "FIELD_SET_MISMATCH",
        )

    def test_duplicate_field_ids_invalidate_record(self):
        duplicate = self.record(
            (
                SourceFieldValue("quantity", 2),
                SourceFieldValue("quantity", 2),
            )
        )
        valid = self.record((SourceFieldValue("quantity", 2),))
        self.assert_hold(
            self.assess(duplicate, valid),
            "EXPECTED_RECORD_INVALID",
        )
        self.assert_hold(
            self.assess(valid, duplicate),
            "READBACK_RECORD_INVALID",
        )

    def test_bool_and_int_are_not_same_type(self):
        expected = self.record((SourceFieldValue("flag", True),))
        readback = self.record((SourceFieldValue("flag", 1),))
        self.assert_hold(
            self.assess(expected, readback),
            "TYPE_MISMATCH",
        )

    def test_text_and_integer_are_not_same_type(self):
        expected = self.record((SourceFieldValue("serial", "123"),))
        readback = self.record((SourceFieldValue("serial", 123),))
        self.assert_hold(
            self.assess(expected, readback),
            "TYPE_MISMATCH",
        )

    def test_same_type_different_value_holds(self):
        expected = self.record((SourceFieldValue("quantity", 2),))
        readback = self.record((SourceFieldValue("quantity", 3),))
        self.assert_hold(
            self.assess(expected, readback),
            "VALUE_MISMATCH",
        )

    def test_leading_zero_text_identity_is_preserved(self):
        expected = self.record((SourceFieldValue("serial", "000123"),))
        readback = self.record((SourceFieldValue("serial", "123"),))
        self.assert_hold(
            self.assess(expected, readback),
            "VALUE_MISMATCH",
        )

    def test_field_container_must_be_native_nonempty_tuple(self):
        valid = self.record((SourceFieldValue("quantity", 2),))
        for fields in ([], (), [SourceFieldValue("quantity", 2)]):
            with self.subTest(fields=fields):
                invalid = self.record(fields)
                self.assert_hold(
                    self.assess(invalid, valid),
                    "EXPECTED_RECORD_INVALID",
                )

    def test_invalid_identifiers_fail_closed(self):
        valid = self.record((SourceFieldValue("quantity", 2),))
        invalid_records = (
            self.record((SourceFieldValue("quantity", 2),), task_id=""),
            self.record((SourceFieldValue("quantity", 2),), task_id=" TASK-1"),
            self.record((SourceFieldValue("quantity", 2),), scope_id=1),
            self.record((SourceFieldValue("quantity", 2),), capture_marker=" "),
        )
        for invalid in invalid_records:
            with self.subTest(invalid=invalid):
                self.assert_hold(
                    self.assess(invalid, valid),
                    "EXPECTED_RECORD_INVALID",
                )

    def test_unsupported_scalar_values_fail_closed(self):
        valid = self.record((SourceFieldValue("quantity", 2),))
        for value in (2.0, [], {}, ("x",)):
            with self.subTest(value=value):
                invalid = self.record((SourceFieldValue("quantity", value),))
                self.assert_hold(
                    self.assess(invalid, valid),
                    "EXPECTED_RECORD_INVALID",
                )

    def test_multiple_independent_reasons_are_sorted(self):
        expected = self.record((SourceFieldValue("quantity", 2),))
        readback = self.record(
            (SourceFieldValue("quantity", 3),),
            task_id="TASK-2",
        )
        result = self.assess(
            expected,
            readback,
            contract_id="WRONG",
        )
        self.assertEqual(
            result.blocking_reasons,
            tuple(sorted(result.blocking_reasons)),
        )
        self.assertIn("BINDING_MISMATCH", result.blocking_reasons)
        self.assertIn("CONTRACT_INVALID", result.blocking_reasons)
        self.assertIn("VALUE_MISMATCH", result.blocking_reasons)
        self.assertFalse(result.production_write_authorized)


if __name__ == "__main__":
    unittest.main()
