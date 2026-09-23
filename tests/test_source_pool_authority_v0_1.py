from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
import unittest

from scripts.source_pool_authority_v0_1 import (
    CANONICAL_SOURCE_IDENTITY_STATUS,
    CANONICAL_SOURCE_POOL_SCHEMA_ID,
    EXACT_SOURCE_SET,
    HOLD,
    PASS,
    SourcePoolAuthorityRegistrySnapshot,
    compute_source_pool_record_hash,
    resolve_source_pool_authority,
    with_computed_source_pool_hash,
)


DOC_DATE = date(2026, 2, 15)


def record(**overrides):
    values = {
        "authority_id": "AUTH-SYNTH-POOL-A",
        "task_id": "TASK-SYNTH-A",
        "line_key": "LINE-SYNTH-A",
        "document_date": DOC_DATE,
        "carrier": "CARRIER-SYNTH-A",
        "denomination": 100,
        "permitted_source_ids": ("SOURCE-SYNTH-A", "SOURCE-SYNTH-B"),
        "evidence_ref": "EVID-SYNTH-A",
        "scope_mode": EXACT_SOURCE_SET,
        "registry_status": "ACTIVE_CANONICAL",
        "owner_decision": "APPROVED_BY_OWNER",
        "readback_status": PASS,
    }
    values.update(overrides)
    return with_computed_source_pool_hash(**values)


def snapshot(
    *,
    records=None,
    source_identity_status=CANONICAL_SOURCE_IDENTITY_STATUS,
    schema_id=CANONICAL_SOURCE_POOL_SCHEMA_ID,
    source_present=True,
    readback_status=PASS,
):
    return SourcePoolAuthorityRegistrySnapshot(
        source_name="SYNTHETIC_SOURCE_POOL_REGISTRY",
        source_identity_status=source_identity_status,
        schema_id=schema_id,
        source_present=source_present,
        readback_status=readback_status,
        records=(record(),) if records is None else tuple(records),
    )


def resolve(*, snap=None, source_ids=("SOURCE-SYNTH-A", "SOURCE-SYNTH-B")):
    return resolve_source_pool_authority(
        authority_id="AUTH-SYNTH-POOL-A",
        task_id="TASK-SYNTH-A",
        line_key="LINE-SYNTH-A",
        document_date=DOC_DATE,
        carrier="CARRIER-SYNTH-A",
        denomination=100,
        materialized_source_ids=source_ids,
        snapshot=snapshot() if snap is None else snap,
    )


class SourcePoolAuthorityTests(unittest.TestCase):
    def test_exact_structured_source_pool_resolves(self) -> None:
        result = resolve()
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.ready)
        self.assertTrue(result.candidate_scope_verified)

    def test_materialized_order_is_not_authoritative(self) -> None:
        result = resolve(source_ids=("SOURCE-SYNTH-B", "SOURCE-SYNTH-A"))
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.candidate_scope_verified)

    def test_missing_snapshot_fails_closed(self) -> None:
        result = resolve_source_pool_authority(
            authority_id="AUTH-SYNTH-POOL-A",
            task_id="TASK-SYNTH-A",
            line_key="LINE-SYNTH-A",
            document_date=DOC_DATE,
            carrier="CARRIER-SYNTH-A",
            denomination=100,
            materialized_source_ids=("SOURCE-SYNTH-A",),
            snapshot=None,
        )
        self.assertEqual(result.status, HOLD)
        self.assertIn("SOURCE_POOL:SNAPSHOT_MISSING", result.blocking_reasons)

    def test_noncanonical_source_fails(self) -> None:
        result = resolve(
            snap=snapshot(source_identity_status="UNVERIFIED")
        )
        self.assertIn("SOURCE_POOL:SOURCE_NOT_CANONICAL", result.blocking_reasons)

    def test_schema_mismatch_fails(self) -> None:
        result = resolve(snap=snapshot(schema_id="OTHER_SCHEMA"))
        self.assertIn("SOURCE_POOL:SCHEMA_MISMATCH", result.blocking_reasons)

    def test_duplicate_authority_id_fails(self) -> None:
        item = record()
        result = resolve(snap=snapshot(records=(item, item)))
        self.assertIn("SOURCE_POOL:DUPLICATE_AUTHORITY_ID", result.blocking_reasons)

    def test_materialized_set_must_equal_authorized_set(self) -> None:
        result = resolve(source_ids=("SOURCE-SYNTH-A",))
        self.assertIn("SOURCE_POOL:MATERIALIZED_SET_MISMATCH", result.blocking_reasons)

    def test_duplicate_materialized_source_ids_fail(self) -> None:
        result = resolve(
            source_ids=("SOURCE-SYNTH-A", "SOURCE-SYNTH-A")
        )
        self.assertIn(
            "SOURCE_POOL:MATERIALIZED_SOURCE_SET_INVALID",
            result.blocking_reasons,
        )

    def test_duplicate_permitted_source_ids_fail(self) -> None:
        item = record(
            permitted_source_ids=("SOURCE-SYNTH-A", "SOURCE-SYNTH-A")
        )
        result = resolve(snap=snapshot(records=(item,)))
        self.assertIn(
            "SOURCE_POOL:PERMITTED_SOURCE_SET_INVALID",
            result.blocking_reasons,
        )

    def test_task_line_and_business_scope_are_bound(self) -> None:
        item = record(
            task_id="OTHER-TASK",
            line_key="OTHER-LINE",
            carrier="OTHER-CARRIER",
            denomination=200,
        )
        result = resolve(snap=snapshot(records=(item,)))
        self.assertIn("SOURCE_POOL:TASK_MISMATCH", result.blocking_reasons)
        self.assertIn("SOURCE_POOL:LINE_MISMATCH", result.blocking_reasons)
        self.assertIn("SOURCE_POOL:CARRIER_MISMATCH", result.blocking_reasons)
        self.assertIn("SOURCE_POOL:DENOMINATION_MISMATCH", result.blocking_reasons)

    def test_document_date_is_bound(self) -> None:
        item = record(document_date=date(2026, 2, 14))
        result = resolve(snap=snapshot(records=(item,)))
        self.assertIn("SOURCE_POOL:DOCUMENT_DATE_MISMATCH", result.blocking_reasons)

    def test_datetime_is_not_accepted_as_document_date(self) -> None:
        result = resolve_source_pool_authority(
            authority_id="AUTH-SYNTH-POOL-A",
            task_id="TASK-SYNTH-A",
            line_key="LINE-SYNTH-A",
            document_date=datetime(2026, 2, 15, 8, 0),
            carrier="CARRIER-SYNTH-A",
            denomination=100,
            materialized_source_ids=("SOURCE-SYNTH-A",),
            snapshot=snapshot(),
        )
        self.assertIn("SOURCE_POOL:DOCUMENT_DATE_INVALID", result.blocking_reasons)

    def test_bool_denomination_is_invalid(self) -> None:
        result = resolve_source_pool_authority(
            authority_id="AUTH-SYNTH-POOL-A",
            task_id="TASK-SYNTH-A",
            line_key="LINE-SYNTH-A",
            document_date=DOC_DATE,
            carrier="CARRIER-SYNTH-A",
            denomination=True,
            materialized_source_ids=("SOURCE-SYNTH-A",),
            snapshot=snapshot(),
        )
        self.assertIn("SOURCE_POOL:DENOMINATION_INVALID", result.blocking_reasons)

    def test_unsupported_scope_mode_fails(self) -> None:
        item = record(scope_mode="SUBSET_ALLOWED")
        result = resolve(snap=snapshot(records=(item,)))
        self.assertIn("SOURCE_POOL:SCOPE_MODE_UNSUPPORTED", result.blocking_reasons)

    def test_missing_owner_approval_fails(self) -> None:
        item = record(owner_decision="PENDING")
        result = resolve(snap=snapshot(records=(item,)))
        self.assertIn("SOURCE_POOL:OWNER_APPROVAL_MISSING", result.blocking_reasons)

    def test_hash_drift_fails(self) -> None:
        item = record()
        drifted = replace(item, evidence_ref="EVID-DRIFT")
        self.assertNotEqual(
            drifted.record_hash,
            compute_source_pool_record_hash(drifted),
        )
        result = resolve(snap=snapshot(records=(drifted,)))
        self.assertIn("SOURCE_POOL:HASH_MISMATCH", result.blocking_reasons)

    def test_free_text_or_generic_state_cannot_create_authority(self) -> None:
        result = resolve(
            snap=snapshot(
                source_identity_status="NOTES_ONLY",
                schema_id="GENERIC_NOTES_V1",
            )
        )
        self.assertEqual(result.status, HOLD)
        self.assertFalse(result.candidate_scope_verified)


if __name__ == "__main__":
    unittest.main()
