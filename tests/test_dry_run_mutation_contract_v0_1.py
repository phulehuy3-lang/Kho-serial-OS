from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
import hashlib
import unittest

from scripts.dry_run_mutation_contract_v0_1 import (
    DRY_RUN_REVIEWED_ONLY,
    HOLD,
    PASS,
    ApprovalBinding,
    MutationIntent,
    MutationWhitelistEntry,
    ReadbackContract,
    RollbackIntent,
    assess_dry_run_mutation_contract,
    compute_idempotency_key,
    with_computed_approval_hash,
    with_computed_mutation_manifest_hash,
    with_computed_mutation_whitelist_hash,
)
from scripts.source_pool_authority_v0_1 import (
    SourcePoolAuthorityResolution,
)


DOC_DATE = date(2026, 2, 15)
CANDIDATE_HASH = hashlib.sha256(b"candidate-set").hexdigest()
PLAN_HASH = hashlib.sha256(b"allocation-plan").hexdigest()
READBACK_HASH = hashlib.sha256(b"pretransition-readback").hexdigest()


def operations() -> tuple[MutationIntent, ...]:
    return (
        MutationIntent(
            operation_id="OP-A",
            resource_name="RESOURCE-A",
            row_key="ROW-A",
            field_name="STATE",
            expected_before="PLANNED",
            intended_after="COMMITTED",
        ),
        MutationIntent(
            operation_id="OP-B",
            resource_name="RESOURCE-B",
            row_key="ROW-B",
            field_name="QUANTITY",
            expected_before=0,
            intended_after=25,
        ),
    )


def rollbacks() -> tuple[RollbackIntent, ...]:
    return (
        RollbackIntent(
            operation_id="OP-A",
            resource_name="RESOURCE-A",
            row_key="ROW-A",
            field_name="STATE",
            restore_value="PLANNED",
        ),
        RollbackIntent(
            operation_id="OP-B",
            resource_name="RESOURCE-B",
            row_key="ROW-B",
            field_name="QUANTITY",
            restore_value=0,
        ),
    )


def whitelist():
    return with_computed_mutation_whitelist_hash(
        whitelist_id="WL-SYNTH-A",
        entries=(
            MutationWhitelistEntry("RESOURCE-A", "STATE"),
            MutationWhitelistEntry("RESOURCE-B", "QUANTITY"),
        ),
    )


def readback_contract() -> ReadbackContract:
    return ReadbackContract(
        contract_id="RB-SYNTH-A",
        full_row_readback_required=True,
        source_derived_reconciliation_required=True,
        rollback_on_mismatch=True,
        readback_status="PASS",
    )


def source_pool(
    *,
    status: str = "PASS",
    ready: bool = True,
    verified: bool = True,
    authority_id: str | None = "AUTH-SYNTH-POOL-A",
) -> SourcePoolAuthorityResolution:
    return SourcePoolAuthorityResolution(
        status=status,
        ready=ready,
        blocking_reasons=() if ready else ("SOURCE_POOL:BLOCKED",),
        authority_id=authority_id,
        candidate_scope_verified=verified,
        permitted_source_ids=("SOURCE-SYNTH-A",) if ready else (),
    )


def manifest(**overrides):
    values = {
        "manifest_id": "MANIFEST-SYNTH-A",
        "task_id": "TASK-SYNTH-A",
        "document_date": DOC_DATE,
        "line_keys": ("LINE-A",),
        "source_years": (2026,),
        "source_pool_authority_id": "AUTH-SYNTH-POOL-A",
        "candidate_source_ids": ("SOURCE-SYNTH-A",),
        "candidate_set_hash": CANDIDATE_HASH,
        "allocation_plan_hash": PLAN_HASH,
        "mutation_whitelist_id": "WL-SYNTH-A",
        "explicit_approval_id": "APR-SYNTH-A",
        "pretransition_readback_hash": READBACK_HASH,
        "operations": operations(),
        "rollback_operations": rollbacks(),
        "readback_contract": readback_contract(),
    }
    values.update(overrides)
    return with_computed_mutation_manifest_hash(**values)


def approval_for(item):
    return with_computed_approval_hash(
        approval_id=item.explicit_approval_id,
        task_id=item.task_id,
        manifest_hash=item.manifest_hash,
    )


def assess(item=None, *, wl=None, approval=None, pool=None):
    item = manifest() if item is None else item
    return assess_dry_run_mutation_contract(
        manifest=item,
        whitelist=whitelist() if wl is None else wl,
        approval=approval_for(item) if approval is None else approval,
        source_pool_resolution=source_pool() if pool is None else pool,
    )


class DryRunMutationContractTests(unittest.TestCase):
    def test_clean_contract_passes_but_never_authorizes_write(self) -> None:
        result = assess()
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.dry_run_contract_ready)
        self.assertFalse(result.production_write_authorized)
        self.assertEqual(result.blocking_reasons, ())

    def test_non_dry_run_and_cross_year_fail_closed(self) -> None:
        item = manifest(
            source_years=(2025,),
            execution_mode="EXECUTE",
        )
        result = assess(item)
        self.assertEqual(result.status, HOLD)
        self.assertIn(
            "DRY_RUN_MUTATION:EXECUTION_MODE_NOT_DRY_RUN",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:SOURCE_YEARS_INVALID",
            result.blocking_reasons,
        )
        self.assertFalse(result.production_write_authorized)

    def test_duplicate_source_years_fail_closed(self) -> None:
        result = assess(manifest(source_years=(2026, 2026)))
        self.assertIn(
            "DRY_RUN_MUTATION:SOURCE_YEARS_INVALID",
            result.blocking_reasons,
        )

    def test_datetime_is_not_accepted_as_document_date(self) -> None:
        item = manifest(document_date=datetime(2026, 2, 15, 8, 0))
        result = assess(item)
        self.assertIn(
            "DRY_RUN_MUTATION:DOCUMENT_DATE_INVALID",
            result.blocking_reasons,
        )

    def test_execution_enablement_flags_are_blocked(self) -> None:
        item = manifest(
            execution_path_status="ENABLED",
            production_ready_flag=True,
            hold_release_requested=True,
        )
        result = assess(item)
        self.assertIn(
            "DRY_RUN_MUTATION:EXECUTION_PATH_NOT_DISABLED",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:PRODUCTION_READY_MUST_REMAIN_FALSE",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:HOLD_RELEASE_EXCLUDED",
            result.blocking_reasons,
        )

    def test_mutation_outside_whitelist_fails(self) -> None:
        bad = with_computed_mutation_whitelist_hash(
            whitelist_id="WL-SYNTH-A",
            entries=(MutationWhitelistEntry("RESOURCE-A", "STATE"),),
        )
        result = assess(wl=bad)
        self.assertIn(
            "DRY_RUN_MUTATION:MUTATION_OUTSIDE_WHITELIST",
            result.blocking_reasons,
        )

    def test_whitelist_hash_and_status_drift_fail(self) -> None:
        wl = whitelist()
        drifted = replace(
            wl,
            status="OTHER",
            record_hash="0" * 64,
        )
        result = assess(wl=drifted)
        self.assertIn(
            "DRY_RUN_MUTATION:WHITELIST_NOT_DRY_RUN_REVIEWED",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:WHITELIST_HASH_MISMATCH",
            result.blocking_reasons,
        )
        self.assertNotEqual(drifted.status, DRY_RUN_REVIEWED_ONLY)

    def test_bool_and_int_are_not_exact_rollback_values(self) -> None:
        ops = (
            MutationIntent(
                "OP-A",
                "RESOURCE-A",
                "ROW-A",
                "FLAG",
                1,
                2,
            ),
        )
        rollback = (
            RollbackIntent(
                "OP-A",
                "RESOURCE-A",
                "ROW-A",
                "FLAG",
                True,
            ),
        )
        item = manifest(
            operations=ops,
            rollback_operations=rollback,
        )
        wl = with_computed_mutation_whitelist_hash(
            whitelist_id="WL-SYNTH-A",
            entries=(MutationWhitelistEntry("RESOURCE-A", "FLAG"),),
        )
        result = assess(item, wl=wl)
        self.assertIn(
            "DRY_RUN_MUTATION:ROLLBACK_NOT_EXACT",
            result.blocking_reasons,
        )

    def test_unsupported_scalar_value_fails(self) -> None:
        ops = (
            MutationIntent(
                "OP-A",
                "RESOURCE-A",
                "ROW-A",
                "STATE",
                "PLANNED",
                1.5,  # type: ignore[arg-type]
            ),
        )
        item = manifest(
            operations=ops,
            rollback_operations=(
                RollbackIntent(
                    "OP-A",
                    "RESOURCE-A",
                    "ROW-A",
                    "STATE",
                    "PLANNED",
                ),
            ),
        )
        result = assess(item)
        self.assertIn(
            "DRY_RUN_MUTATION:OPERATION_SHAPE_INVALID",
            result.blocking_reasons,
        )

    def test_expected_before_changes_idempotency_key(self) -> None:
        original = operations()
        changed = (
            replace(original[0], expected_before="OTHER"),
            original[1],
        )
        first = compute_idempotency_key(
            task_id="TASK-SYNTH-A",
            candidate_set_hash=CANDIDATE_HASH,
            allocation_plan_hash=PLAN_HASH,
            operations=original,
        )
        second = compute_idempotency_key(
            task_id="TASK-SYNTH-A",
            candidate_set_hash=CANDIDATE_HASH,
            allocation_plan_hash=PLAN_HASH,
            operations=changed,
        )
        self.assertNotEqual(first, second)

    def test_idempotency_and_manifest_hash_drift_fail(self) -> None:
        item = manifest()
        drifted = replace(
            item,
            idempotency_key="f" * 64,
            manifest_hash="e" * 64,
        )
        result = assess(
            drifted,
            approval=approval_for(drifted),
        )
        self.assertIn(
            "DRY_RUN_MUTATION:IDEMPOTENCY_KEY_MISMATCH",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:MANIFEST_HASH_MISMATCH",
            result.blocking_reasons,
        )

    def test_approval_must_bind_exact_task_and_manifest(self) -> None:
        item = manifest()
        bad = with_computed_approval_hash(
            approval_id="APR-SYNTH-A",
            task_id="OTHER-TASK",
            manifest_hash="1" * 64,
            approval_status="DENIED",
            readback_status="FAIL",
        )
        result = assess(item, approval=bad)
        self.assertIn(
            "DRY_RUN_MUTATION:APPROVAL_TASK_MISMATCH",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:APPROVAL_MANIFEST_MISMATCH",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:APPROVAL_NOT_APPROVED",
            result.blocking_reasons,
        )

    def test_inconsistent_source_pool_resolution_fails(self) -> None:
        result = assess(
            pool=source_pool(
                status="HOLD",
                ready=True,
                verified=True,
            )
        )
        self.assertIn(
            "DRY_RUN_MUTATION:SOURCE_POOL_AUTHORITY_NOT_VERIFIED",
            result.blocking_reasons,
        )

    def test_source_pool_authority_id_must_match(self) -> None:
        result = assess(pool=source_pool(authority_id="OTHER-AUTH"))
        self.assertIn(
            "DRY_RUN_MUTATION:SOURCE_POOL_AUTHORITY_ID_MISMATCH",
            result.blocking_reasons,
        )

    def test_posttransition_readback_contract_is_mandatory(self) -> None:
        bad = ReadbackContract(
            contract_id="",
            full_row_readback_required=False,
            source_derived_reconciliation_required=False,
            rollback_on_mismatch=False,
            readback_status="FAIL",
        )
        result = assess(manifest(readback_contract=bad))
        self.assertIn(
            "DRY_RUN_MUTATION:READBACK_CONTRACT_ID_MISSING",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:FULL_ROW_READBACK_REQUIRED",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:RECONCILIATION_REQUIRED",
            result.blocking_reasons,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:ROLLBACK_ON_MISMATCH_REQUIRED",
            result.blocking_reasons,
        )

    def test_approval_record_hash_drift_fails(self) -> None:
        item = manifest()
        valid = approval_for(item)
        drifted = ApprovalBinding(
            approval_id=valid.approval_id,
            task_id=valid.task_id,
            manifest_hash=valid.manifest_hash,
            approval_status=valid.approval_status,
            readback_status=valid.readback_status,
            record_hash="0" * 64,
        )
        result = assess(item, approval=drifted)
        self.assertIn(
            "DRY_RUN_MUTATION:APPROVAL_HASH_MISMATCH",
            result.blocking_reasons,
        )


    def test_source_pool_ready_and_verified_require_native_true(self) -> None:
        for field in ("ready", "verified"):
            with self.subTest(field=field):
                kwargs = {field: "False"}
                result = assess(pool=source_pool(**kwargs))
                self.assertEqual(result.status, HOLD)
                self.assertFalse(result.dry_run_contract_ready)
                self.assertFalse(result.production_write_authorized)

    def test_malformed_source_pool_resolution_holds_without_exception(self) -> None:
        result = assess(pool=True)  # type: ignore[arg-type]
        self.assertEqual(result.status, HOLD)
        self.assertFalse(result.dry_run_contract_ready)
        self.assertFalse(result.production_write_authorized)


if __name__ == "__main__":
    unittest.main()
