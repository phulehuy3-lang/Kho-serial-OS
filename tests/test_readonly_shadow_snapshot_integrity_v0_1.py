from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.readonly_shadow_snapshot_integrity_v0_1 import (
    DERIVED_READ_ONLY,
    HOLD,
    PASS,
    SOURCE_OF_TRUTH,
    ReadSurfaceContract,
    SurfaceReadResult,
    assess_shadow_snapshot,
    compute_surface_contract_hash,
    compute_target_contract_hash,
    validate_target_contract,
    with_computed_surface_contract_hash,
    with_computed_target_contract_hash,
)


def source_surface():
    return with_computed_surface_contract_hash(
        surface_id="SOURCE_STATE",
        logical_name="SOURCE_STATE",
        role=SOURCE_OF_TRUTH,
        fields=("ItemID", "Quantity"),
    )


def derived_surface():
    return with_computed_surface_contract_hash(
        surface_id="DERIVED_VIEW",
        logical_name="DERIVED_VIEW",
        role=DERIVED_READ_ONLY,
        fields=("ItemID", "Quantity"),
    )


def target():
    return with_computed_target_contract_hash(
        target_id="TARGET-A",
        schema_version="SCHEMA-A",
        surfaces=(source_surface(), derived_surface()),
    )


def clean_reads():
    return {
        "SOURCE_STATE": SurfaceReadResult(
            surface_id="SOURCE_STATE",
            version_marker="V1",
            captured_at="T1",
            rows=(
                {"ItemID": "A", "Quantity": 60},
                {"ItemID": "B", "Quantity": 40},
            ),
        ),
        "DERIVED_VIEW": SurfaceReadResult(
            surface_id="DERIVED_VIEW",
            version_marker="V1",
            captured_at="T2",
            rows=(
                {"ItemID": "A", "Quantity": 60},
                {"ItemID": "B", "Quantity": 40},
            ),
        ),
    }


class ContractValidationTests(unittest.TestCase):
    def test_clean_target_contract_passes(self) -> None:
        item = target()
        self.assertEqual(validate_target_contract(item), ())
        self.assertEqual(
            item.contract_hash,
            compute_target_contract_hash(item),
        )

    def test_surface_hash_is_exact(self) -> None:
        surface = source_surface()
        self.assertEqual(
            surface.contract_hash,
            compute_surface_contract_hash(
                surface_id=surface.surface_id,
                logical_name=surface.logical_name,
                role=surface.role,
                fields=surface.fields,
            ),
        )

    def test_duplicate_surface_id_fails(self) -> None:
        surface = source_surface()
        item = with_computed_target_contract_hash(
            target_id="TARGET-A",
            schema_version="SCHEMA-A",
            surfaces=(surface, surface),
        )
        self.assertIn(
            "SHADOW_SNAPSHOT:DUPLICATE_SURFACE_ID",
            validate_target_contract(item),
        )

    def test_invalid_role_and_duplicate_field_fail(self) -> None:
        broken = ReadSurfaceContract(
            surface_id="BROKEN",
            logical_name="BROKEN",
            role="MUTABLE",
            fields=("ItemID", "ItemID"),
            contract_hash="bad",
        )
        item = with_computed_target_contract_hash(
            target_id="TARGET-A",
            schema_version="SCHEMA-A",
            surfaces=(broken,),
        )
        blockers = validate_target_contract(item)
        self.assertIn(
            "SHADOW_SNAPSHOT:INVALID_ROLE:BROKEN",
            blockers,
        )
        self.assertIn(
            "SHADOW_SNAPSHOT:DUPLICATE_FIELD:BROKEN",
            blockers,
        )
        self.assertIn(
            "SHADOW_SNAPSHOT:SURFACE_HASH_MISMATCH:BROKEN",
            blockers,
        )

    def test_target_hash_drift_fails(self) -> None:
        item = target()
        drifted = replace(item, contract_hash="0" * 64)
        self.assertIn(
            "SHADOW_SNAPSHOT:TARGET_HASH_MISMATCH",
            validate_target_contract(drifted),
        )


class SnapshotAssessmentTests(unittest.TestCase):
    def test_clean_snapshot_passes_and_is_deterministic(self) -> None:
        first = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=clean_reads(),
        )
        second = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=clean_reads(),
        )
        self.assertEqual(first.status, PASS)
        self.assertTrue(first.ready)
        self.assertIsNotNone(first.snapshot)
        self.assertEqual(
            first.snapshot.snapshot_hash,
            second.snapshot.snapshot_hash,
        )
        self.assertTrue(first.snapshot.atomic_snapshot_proven)

    def test_row_mapping_order_does_not_change_hash(self) -> None:
        reads = clean_reads()
        reads["SOURCE_STATE"] = SurfaceReadResult(
            surface_id="SOURCE_STATE",
            version_marker="V1",
            captured_at="T1",
            rows=(
                {"Quantity": 60, "ItemID": "A"},
                {"Quantity": 40, "ItemID": "B"},
            ),
        )
        left = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=clean_reads(),
        )
        right = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=reads,
        )
        self.assertEqual(
            left.snapshot.snapshot_hash,
            right.snapshot.snapshot_hash,
        )

    def test_exact_surface_set_is_required(self) -> None:
        reads = clean_reads()
        del reads["DERIVED_VIEW"]
        result = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=reads,
        )
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "SHADOW_SNAPSHOT:READ_MISSING:DERIVED_VIEW",
            result.blocking_reasons,
        )

    def test_extra_surface_fails_closed(self) -> None:
        reads = clean_reads()
        reads["EXTRA"] = SurfaceReadResult(
            surface_id="EXTRA",
            version_marker="V1",
            captured_at="T3",
            rows=(),
        )
        result = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=reads,
        )
        self.assertIn(
            "SHADOW_SNAPSHOT:READ_UNEXPECTED:EXTRA",
            result.blocking_reasons,
        )

    def test_result_identity_mismatch_fails(self) -> None:
        reads = clean_reads()
        current = reads["SOURCE_STATE"]
        reads["SOURCE_STATE"] = replace(
            current,
            surface_id="OTHER",
        )
        result = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=reads,
        )
        self.assertIn(
            "SHADOW_SNAPSHOT:RESULT_ID_MISMATCH:SOURCE_STATE",
            result.blocking_reasons,
        )

    def test_field_set_drift_fails(self) -> None:
        reads = clean_reads()
        reads["SOURCE_STATE"] = SurfaceReadResult(
            surface_id="SOURCE_STATE",
            version_marker="V1",
            captured_at="T1",
            rows=({"ItemID": "A"},),
        )
        result = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=reads,
        )
        self.assertTrue(
            any(
                blocker.startswith("SHADOW_SNAPSHOT:FIELD_SET_MISMATCH")
                for blocker in result.blocking_reasons
            )
        )

    def test_float_value_is_rejected(self) -> None:
        reads = clean_reads()
        reads["SOURCE_STATE"] = SurfaceReadResult(
            surface_id="SOURCE_STATE",
            version_marker="V1",
            captured_at="T1",
            rows=({"ItemID": "A", "Quantity": 1.5},),  # type: ignore[dict-item]
        )
        result = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=reads,
        )
        self.assertTrue(
            any(
                blocker.startswith("SHADOW_SNAPSHOT:UNSUPPORTED_TYPE")
                for blocker in result.blocking_reasons
            )
        )

    def test_missing_version_marker_fails(self) -> None:
        reads = clean_reads()
        reads["SOURCE_STATE"] = replace(
            reads["SOURCE_STATE"],
            version_marker="",
        )
        result = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=reads,
        )
        self.assertIn(
            "SHADOW_SNAPSHOT:VERSION_MARKER_MISSING:SOURCE_STATE",
            result.blocking_reasons,
        )

    def test_version_drift_returns_hold_with_snapshot_evidence(self) -> None:
        reads = clean_reads()
        reads["DERIVED_VIEW"] = replace(
            reads["DERIVED_VIEW"],
            version_marker="V2",
        )
        result = assess_shadow_snapshot(
            snapshot_id="SNAP-A",
            target=target(),
            reads=reads,
        )
        self.assertEqual(result.status, HOLD)
        self.assertFalse(result.ready)
        self.assertIsNotNone(result.snapshot)
        self.assertFalse(result.snapshot.atomic_snapshot_proven)
        self.assertIn(
            "SHADOW_SNAPSHOT:NONATOMIC_VERSION_DRIFT",
            result.blocking_reasons,
        )

    def test_snapshot_id_is_required(self) -> None:
        result = assess_shadow_snapshot(
            snapshot_id="",
            target=target(),
            reads=clean_reads(),
        )
        self.assertIn(
            "SHADOW_SNAPSHOT:SNAPSHOT_ID_MISSING",
            result.blocking_reasons,
        )


if __name__ == "__main__":
    unittest.main()
