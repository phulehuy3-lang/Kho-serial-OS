from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.cross_year_authority_v0_1 import (
    CANONICAL_AUTHORITY_SCHEMA_ID,
    CANONICAL_SOURCE_IDENTITY_STATUS,
    HOLD,
    PASS,
    CrossYearAuthorityRegistrySnapshot,
    compute_authority_record_hash,
    resolve_cross_year_authority,
    with_computed_record_hash,
)


def snapshot(
    *,
    source_identity_status: str = CANONICAL_SOURCE_IDENTITY_STATUS,
    schema_id: str = CANONICAL_AUTHORITY_SCHEMA_ID,
    source_present: bool = True,
    readback_status: str = PASS,
    records=None,
) -> CrossYearAuthorityRegistrySnapshot:
    if records is None:
        records = (
            with_computed_record_hash(
                authority_id="AUTH-SYNTH-A",
                task_id="TASK-SYNTH-A",
                decision="APPROVED",
                permitted_source_years=(2025,),
                evidence_ref="EVID-SYNTH-A",
            ),
        )
    return CrossYearAuthorityRegistrySnapshot(
        source_name="SYNTHETIC_AUTHORITY_REGISTRY",
        source_identity_status=source_identity_status,
        schema_id=schema_id,
        source_present=source_present,
        readback_status=readback_status,
        records=tuple(records),
    )


class CrossYearAuthorityTests(unittest.TestCase):
    def test_exact_canonical_record_resolves(self) -> None:
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(),
        )
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.ready)
        self.assertEqual(result.authority.permitted_source_years, (2025,))

    def test_missing_snapshot_fails_closed(self) -> None:
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=None,
        )
        self.assertEqual(result.status, HOLD)
        self.assertIn("CROSS_YEAR:SNAPSHOT_MISSING", result.blocking_reasons)

    def test_noncanonical_source_fails(self) -> None:
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(source_identity_status="UNVERIFIED"),
        )
        self.assertIn("CROSS_YEAR:SOURCE_NOT_CANONICAL", result.blocking_reasons)

    def test_schema_mismatch_fails(self) -> None:
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(schema_id="OTHER_SCHEMA"),
        )
        self.assertIn("CROSS_YEAR:SCHEMA_MISMATCH", result.blocking_reasons)

    def test_duplicate_authority_id_fails(self) -> None:
        record = snapshot().records[0]
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(records=(record, record)),
        )
        self.assertIn("CROSS_YEAR:DUPLICATE_AUTHORITY_ID", result.blocking_reasons)

    def test_task_mismatch_fails(self) -> None:
        record = with_computed_record_hash(
            authority_id="AUTH-SYNTH-A",
            task_id="OTHER-TASK",
            decision="APPROVED",
            permitted_source_years=(2025,),
            evidence_ref="EVID-SYNTH-A",
        )
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(records=(record,)),
        )
        self.assertIn("CROSS_YEAR:TASK_MISMATCH", result.blocking_reasons)

    def test_document_year_cannot_be_source_year(self) -> None:
        record = with_computed_record_hash(
            authority_id="AUTH-SYNTH-A",
            task_id="TASK-SYNTH-A",
            decision="APPROVED",
            permitted_source_years=(2026,),
            evidence_ref="EVID-SYNTH-A",
        )
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(records=(record,)),
        )
        self.assertIn("CROSS_YEAR:YEARS_INVALID", result.blocking_reasons)

    def test_duplicate_source_years_fail(self) -> None:
        record = with_computed_record_hash(
            authority_id="AUTH-SYNTH-A",
            task_id="TASK-SYNTH-A",
            decision="APPROVED",
            permitted_source_years=(2025, 2025),
            evidence_ref="EVID-SYNTH-A",
        )
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(records=(record,)),
        )
        self.assertIn("CROSS_YEAR:YEARS_INVALID", result.blocking_reasons)

    def test_hash_drift_fails(self) -> None:
        record = snapshot().records[0]
        drifted = replace(record, evidence_ref="EVID-DRIFT")
        self.assertNotEqual(
            drifted.record_hash,
            compute_authority_record_hash(drifted),
        )
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(records=(drifted,)),
        )
        self.assertIn("CROSS_YEAR:HASH_MISMATCH", result.blocking_reasons)

    def test_missing_owner_approval_fails(self) -> None:
        record = with_computed_record_hash(
            authority_id="AUTH-SYNTH-A",
            task_id="TASK-SYNTH-A",
            decision="APPROVED",
            permitted_source_years=(2025,),
            evidence_ref="EVID-SYNTH-A",
            owner_decision="PENDING",
        )
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=snapshot(records=(record,)),
        )
        self.assertIn("CROSS_YEAR:OWNER_APPROVAL_MISSING", result.blocking_reasons)

    def test_invalid_document_year_fails_closed(self) -> None:
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=True,
            snapshot=snapshot(),
        )
        self.assertIn("CROSS_YEAR:DOCUMENT_YEAR_INVALID", result.blocking_reasons)

    def test_free_text_cannot_create_authority(self) -> None:
        result = resolve_cross_year_authority(
            task_id="TASK-SYNTH-A",
            authority_id="AUTH-SYNTH-A",
            document_year=2026,
            snapshot=CrossYearAuthorityRegistrySnapshot(
                source_name="SYNTHETIC_NOTES",
                source_identity_status="UNVERIFIED",
                schema_id="NOTES_V1",
                source_present=True,
                readback_status=PASS,
                records=(),
            ),
        )
        self.assertEqual(result.status, HOLD)
        self.assertFalse(result.ready)


if __name__ == "__main__":
    unittest.main()
