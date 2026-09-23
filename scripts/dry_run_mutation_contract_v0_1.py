"""Pure dry-run mutation-contract validation.

This module performs no external I/O and exposes no executable write path.
A PASS never authorizes production mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json

from scripts.source_pool_authority_v0_1 import (
    PASS as SOURCE_POOL_PASS,
    SourcePoolAuthorityResolution,
)


PASS = "PASS"
HOLD = "HOLD"

DRY_RUN_ONLY = "DRY_RUN_ONLY"
SAME_YEAR_ONLY = "SAME_YEAR_ONLY"
EXECUTION_PATH_DISABLED = "EXECUTION_PATH_DISABLED"
DRY_RUN_REVIEWED_ONLY = "DRY_RUN_REVIEWED_ONLY"
SET_EXACT = "SET_EXACT"

APPROVED = "APPROVED"
READBACK_PASS = "PASS"

STOP_AND_ROLLBACK = "STOP_AND_ROLLBACK"
IDEMPOTENT_RETRY_ONLY = "IDEMPOTENT_RETRY_ONLY"

ScalarValue = str | int | bool | None


@dataclass(frozen=True, slots=True)
class MutationIntent:
    operation_id: str
    resource_name: str
    row_key: str
    field_name: str
    expected_before: ScalarValue
    intended_after: ScalarValue
    mutation_kind: str = SET_EXACT


@dataclass(frozen=True, slots=True)
class RollbackIntent:
    operation_id: str
    resource_name: str
    row_key: str
    field_name: str
    restore_value: ScalarValue


@dataclass(frozen=True, slots=True)
class MutationWhitelistEntry:
    resource_name: str
    field_name: str
    mutation_kind: str = SET_EXACT


@dataclass(frozen=True, slots=True)
class MutationWhitelistContract:
    whitelist_id: str
    status: str
    readback_status: str
    entries: tuple[MutationWhitelistEntry, ...]
    record_hash: str


@dataclass(frozen=True, slots=True)
class ApprovalBinding:
    approval_id: str
    task_id: str
    manifest_hash: str
    approval_status: str
    readback_status: str
    record_hash: str


@dataclass(frozen=True, slots=True)
class ReadbackContract:
    contract_id: str
    full_row_readback_required: bool
    source_derived_reconciliation_required: bool
    rollback_on_mismatch: bool
    readback_status: str


@dataclass(frozen=True, slots=True)
class DryRunMutationManifest:
    manifest_id: str
    task_id: str
    document_date: date
    line_keys: tuple[str, ...]
    execution_mode: str
    year_scope: str
    source_years: tuple[int, ...]
    source_pool_authority_id: str
    candidate_source_ids: tuple[str, ...]
    candidate_set_hash: str
    allocation_plan_hash: str
    mutation_whitelist_id: str
    explicit_approval_id: str
    idempotency_key: str
    execution_path_status: str
    production_ready_flag: bool
    hold_release_requested: bool
    failure_policy: str
    retry_policy: str
    pretransition_readback_hash: str
    operations: tuple[MutationIntent, ...]
    rollback_operations: tuple[RollbackIntent, ...]
    readback_contract: ReadbackContract
    manifest_hash: str


@dataclass(frozen=True, slots=True)
class DryRunMutationAssessment:
    status: str
    dry_run_contract_ready: bool
    production_write_authorized: bool
    blocking_reasons: tuple[str, ...]
    manifest_hash: str


def _clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _valid_source_ids(values: object) -> bool:
    if not isinstance(values, tuple) or not values:
        return False
    if any(not _clean(value) for value in values):
        return False
    return len(set(values)) == len(values)


def _valid_scalar(value: object) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    return isinstance(value, int) and not isinstance(value, bool)


def _exact_same_value(left: object, right: object) -> bool:
    return type(left) is type(right) and left == right


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(char in "0123456789abcdef" for char in value)


def _canonical_sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def mutation_whitelist_hash_payload(
    contract: MutationWhitelistContract,
) -> dict[str, object]:
    return {
        "whitelist_id": contract.whitelist_id,
        "status": contract.status,
        "readback_status": contract.readback_status,
        "entries": [
            {
                "resource_name": entry.resource_name,
                "field_name": entry.field_name,
                "mutation_kind": entry.mutation_kind,
            }
            for entry in contract.entries
        ],
    }


def compute_mutation_whitelist_hash(
    contract: MutationWhitelistContract,
) -> str:
    return _canonical_sha256(mutation_whitelist_hash_payload(contract))


def with_computed_mutation_whitelist_hash(
    *,
    whitelist_id: str,
    entries: tuple[MutationWhitelistEntry, ...],
    status: str = DRY_RUN_REVIEWED_ONLY,
    readback_status: str = READBACK_PASS,
) -> MutationWhitelistContract:
    provisional = MutationWhitelistContract(
        whitelist_id=whitelist_id,
        status=status,
        readback_status=readback_status,
        entries=entries,
        record_hash="",
    )
    return MutationWhitelistContract(
        whitelist_id=provisional.whitelist_id,
        status=provisional.status,
        readback_status=provisional.readback_status,
        entries=provisional.entries,
        record_hash=compute_mutation_whitelist_hash(provisional),
    )


def approval_hash_payload(binding: ApprovalBinding) -> dict[str, object]:
    return {
        "approval_id": binding.approval_id,
        "task_id": binding.task_id,
        "manifest_hash": binding.manifest_hash,
        "approval_status": binding.approval_status,
        "readback_status": binding.readback_status,
    }


def compute_approval_hash(binding: ApprovalBinding) -> str:
    return _canonical_sha256(approval_hash_payload(binding))


def with_computed_approval_hash(
    *,
    approval_id: str,
    task_id: str,
    manifest_hash: str,
    approval_status: str = APPROVED,
    readback_status: str = READBACK_PASS,
) -> ApprovalBinding:
    provisional = ApprovalBinding(
        approval_id=approval_id,
        task_id=task_id,
        manifest_hash=manifest_hash,
        approval_status=approval_status,
        readback_status=readback_status,
        record_hash="",
    )
    return ApprovalBinding(
        approval_id=provisional.approval_id,
        task_id=provisional.task_id,
        manifest_hash=provisional.manifest_hash,
        approval_status=provisional.approval_status,
        readback_status=provisional.readback_status,
        record_hash=compute_approval_hash(provisional),
    )


def idempotency_payload(
    *,
    task_id: str,
    candidate_set_hash: str,
    allocation_plan_hash: str,
    operations: tuple[MutationIntent, ...],
) -> dict[str, object]:
    return {
        "task_id": task_id,
        "candidate_set_hash": candidate_set_hash,
        "allocation_plan_hash": allocation_plan_hash,
        "operations": [
            {
                "operation_id": operation.operation_id,
                "resource_name": operation.resource_name,
                "row_key": operation.row_key,
                "field_name": operation.field_name,
                "expected_before": operation.expected_before,
                "intended_after": operation.intended_after,
                "mutation_kind": operation.mutation_kind,
            }
            for operation in operations
        ],
    }


def compute_idempotency_key(
    *,
    task_id: str,
    candidate_set_hash: str,
    allocation_plan_hash: str,
    operations: tuple[MutationIntent, ...],
) -> str:
    return _canonical_sha256(
        idempotency_payload(
            task_id=task_id,
            candidate_set_hash=candidate_set_hash,
            allocation_plan_hash=allocation_plan_hash,
            operations=operations,
        )
    )


def mutation_manifest_hash_payload(
    manifest: DryRunMutationManifest,
) -> dict[str, object]:
    return {
        "manifest_id": manifest.manifest_id,
        "task_id": manifest.task_id,
        "document_date": manifest.document_date.isoformat(),
        "line_keys": list(manifest.line_keys),
        "execution_mode": manifest.execution_mode,
        "year_scope": manifest.year_scope,
        "source_years": list(manifest.source_years),
        "source_pool_authority_id": manifest.source_pool_authority_id,
        "candidate_source_ids": list(manifest.candidate_source_ids),
        "candidate_set_hash": manifest.candidate_set_hash,
        "allocation_plan_hash": manifest.allocation_plan_hash,
        "mutation_whitelist_id": manifest.mutation_whitelist_id,
        "explicit_approval_id": manifest.explicit_approval_id,
        "idempotency_key": manifest.idempotency_key,
        "execution_path_status": manifest.execution_path_status,
        "production_ready_flag": manifest.production_ready_flag,
        "hold_release_requested": manifest.hold_release_requested,
        "failure_policy": manifest.failure_policy,
        "retry_policy": manifest.retry_policy,
        "pretransition_readback_hash": manifest.pretransition_readback_hash,
        "operations": [
            {
                "operation_id": operation.operation_id,
                "resource_name": operation.resource_name,
                "row_key": operation.row_key,
                "field_name": operation.field_name,
                "expected_before": operation.expected_before,
                "intended_after": operation.intended_after,
                "mutation_kind": operation.mutation_kind,
            }
            for operation in manifest.operations
        ],
        "rollback_operations": [
            {
                "operation_id": operation.operation_id,
                "resource_name": operation.resource_name,
                "row_key": operation.row_key,
                "field_name": operation.field_name,
                "restore_value": operation.restore_value,
            }
            for operation in manifest.rollback_operations
        ],
        "readback_contract": {
            "contract_id": manifest.readback_contract.contract_id,
            "full_row_readback_required": (
                manifest.readback_contract.full_row_readback_required
            ),
            "source_derived_reconciliation_required": (
                manifest.readback_contract.source_derived_reconciliation_required
            ),
            "rollback_on_mismatch": (
                manifest.readback_contract.rollback_on_mismatch
            ),
            "readback_status": manifest.readback_contract.readback_status,
        },
    }


def compute_mutation_manifest_hash(
    manifest: DryRunMutationManifest,
) -> str:
    return _canonical_sha256(mutation_manifest_hash_payload(manifest))


def with_computed_mutation_manifest_hash(
    *,
    manifest_id: str,
    task_id: str,
    document_date: date,
    line_keys: tuple[str, ...],
    source_years: tuple[int, ...],
    source_pool_authority_id: str,
    candidate_source_ids: tuple[str, ...],
    candidate_set_hash: str,
    allocation_plan_hash: str,
    mutation_whitelist_id: str,
    explicit_approval_id: str,
    pretransition_readback_hash: str,
    operations: tuple[MutationIntent, ...],
    rollback_operations: tuple[RollbackIntent, ...],
    readback_contract: ReadbackContract,
    execution_mode: str = DRY_RUN_ONLY,
    year_scope: str = SAME_YEAR_ONLY,
    execution_path_status: str = EXECUTION_PATH_DISABLED,
    production_ready_flag: bool = False,
    hold_release_requested: bool = False,
    failure_policy: str = STOP_AND_ROLLBACK,
    retry_policy: str = IDEMPOTENT_RETRY_ONLY,
) -> DryRunMutationManifest:
    idempotency_key = compute_idempotency_key(
        task_id=task_id,
        candidate_set_hash=candidate_set_hash,
        allocation_plan_hash=allocation_plan_hash,
        operations=operations,
    )
    provisional = DryRunMutationManifest(
        manifest_id=manifest_id,
        task_id=task_id,
        document_date=document_date,
        line_keys=line_keys,
        execution_mode=execution_mode,
        year_scope=year_scope,
        source_years=source_years,
        source_pool_authority_id=source_pool_authority_id,
        candidate_source_ids=candidate_source_ids,
        candidate_set_hash=candidate_set_hash,
        allocation_plan_hash=allocation_plan_hash,
        mutation_whitelist_id=mutation_whitelist_id,
        explicit_approval_id=explicit_approval_id,
        idempotency_key=idempotency_key,
        execution_path_status=execution_path_status,
        production_ready_flag=production_ready_flag,
        hold_release_requested=hold_release_requested,
        failure_policy=failure_policy,
        retry_policy=retry_policy,
        pretransition_readback_hash=pretransition_readback_hash,
        operations=operations,
        rollback_operations=rollback_operations,
        readback_contract=readback_contract,
        manifest_hash="",
    )
    return DryRunMutationManifest(
        manifest_id=provisional.manifest_id,
        task_id=provisional.task_id,
        document_date=provisional.document_date,
        line_keys=provisional.line_keys,
        execution_mode=provisional.execution_mode,
        year_scope=provisional.year_scope,
        source_years=provisional.source_years,
        source_pool_authority_id=provisional.source_pool_authority_id,
        candidate_source_ids=provisional.candidate_source_ids,
        candidate_set_hash=provisional.candidate_set_hash,
        allocation_plan_hash=provisional.allocation_plan_hash,
        mutation_whitelist_id=provisional.mutation_whitelist_id,
        explicit_approval_id=provisional.explicit_approval_id,
        idempotency_key=provisional.idempotency_key,
        execution_path_status=provisional.execution_path_status,
        production_ready_flag=provisional.production_ready_flag,
        hold_release_requested=provisional.hold_release_requested,
        failure_policy=provisional.failure_policy,
        retry_policy=provisional.retry_policy,
        pretransition_readback_hash=provisional.pretransition_readback_hash,
        operations=provisional.operations,
        rollback_operations=provisional.rollback_operations,
        readback_contract=provisional.readback_contract,
        manifest_hash=compute_mutation_manifest_hash(provisional),
    )


def _operation_target(
    operation: MutationIntent,
) -> tuple[str, str, str]:
    return (
        operation.resource_name,
        operation.row_key,
        operation.field_name,
    )


def _rollback_target(
    operation: RollbackIntent,
) -> tuple[str, str, str]:
    return (
        operation.resource_name,
        operation.row_key,
        operation.field_name,
    )


def assess_dry_run_mutation_contract(
    *,
    manifest: DryRunMutationManifest,
    whitelist: MutationWhitelistContract,
    approval: ApprovalBinding,
    source_pool_resolution: SourcePoolAuthorityResolution,
) -> DryRunMutationAssessment:
    """Validate a dry-run mutation contract without granting write authority."""

    blockers: list[str] = []

    if not _clean(manifest.manifest_id):
        blockers.append("DRY_RUN_MUTATION:MANIFEST_ID_MISSING")
    if not _clean(manifest.task_id):
        blockers.append("DRY_RUN_MUTATION:TASK_ID_MISSING")
    if type(manifest.document_date) is not date:
        blockers.append("DRY_RUN_MUTATION:DOCUMENT_DATE_INVALID")
    if (
        not manifest.line_keys
        or any(not _clean(line_key) for line_key in manifest.line_keys)
        or len(set(manifest.line_keys)) != len(manifest.line_keys)
    ):
        blockers.append("DRY_RUN_MUTATION:LINE_KEYS_INVALID")

    if manifest.execution_mode != DRY_RUN_ONLY:
        blockers.append("DRY_RUN_MUTATION:EXECUTION_MODE_NOT_DRY_RUN")
    if manifest.year_scope != SAME_YEAR_ONLY:
        blockers.append("DRY_RUN_MUTATION:YEAR_SCOPE_NOT_SAME_YEAR")
    if (
        not manifest.source_years
        or len(set(manifest.source_years)) != len(manifest.source_years)
        or any(
            not isinstance(year, int)
            or isinstance(year, bool)
            or year <= 0
            or year != manifest.document_date.year
            for year in manifest.source_years
        )
    ):
        blockers.append("DRY_RUN_MUTATION:SOURCE_YEARS_INVALID")

    if manifest.execution_path_status != EXECUTION_PATH_DISABLED:
        blockers.append("DRY_RUN_MUTATION:EXECUTION_PATH_NOT_DISABLED")
    if manifest.production_ready_flag is not False:
        blockers.append("DRY_RUN_MUTATION:PRODUCTION_READY_MUST_REMAIN_FALSE")
    if manifest.hold_release_requested is not False:
        blockers.append("DRY_RUN_MUTATION:HOLD_RELEASE_EXCLUDED")
    if manifest.failure_policy != STOP_AND_ROLLBACK:
        blockers.append("DRY_RUN_MUTATION:FAILURE_POLICY_INVALID")
    if manifest.retry_policy != IDEMPOTENT_RETRY_ONLY:
        blockers.append("DRY_RUN_MUTATION:RETRY_POLICY_INVALID")

    for code, value in (
        ("SOURCE_POOL_AUTHORITY_ID_MISSING", manifest.source_pool_authority_id),
        ("WHITELIST_ID_MISSING", manifest.mutation_whitelist_id),
        ("APPROVAL_ID_MISSING", manifest.explicit_approval_id),
    ):
        if not _clean(value):
            blockers.append(f"DRY_RUN_MUTATION:{code}")

    if not _valid_source_ids(manifest.candidate_source_ids):
        blockers.append("DRY_RUN_MUTATION:CANDIDATE_SOURCE_IDS_INVALID")

    for code, value in (
        ("CANDIDATE_SET_HASH_INVALID", manifest.candidate_set_hash),
        ("ALLOCATION_PLAN_HASH_INVALID", manifest.allocation_plan_hash),
        ("PRETRANSITION_READBACK_HASH_INVALID", manifest.pretransition_readback_hash),
    ):
        if not _is_sha256(value):
            blockers.append(f"DRY_RUN_MUTATION:{code}")

    if not manifest.operations:
        blockers.append("DRY_RUN_MUTATION:OPERATIONS_MISSING")

    operation_ids = tuple(
        operation.operation_id for operation in manifest.operations
    )
    if (
        any(not _clean(operation_id) for operation_id in operation_ids)
        or len(set(operation_ids)) != len(operation_ids)
    ):
        blockers.append("DRY_RUN_MUTATION:OPERATION_IDS_INVALID")

    targets = tuple(
        _operation_target(operation) for operation in manifest.operations
    )
    if len(set(targets)) != len(targets):
        blockers.append("DRY_RUN_MUTATION:DUPLICATE_MUTATION_TARGET")

    if any(
        not _clean(operation.resource_name)
        or not _clean(operation.row_key)
        or not _clean(operation.field_name)
        or operation.mutation_kind != SET_EXACT
        or not _valid_scalar(operation.expected_before)
        or not _valid_scalar(operation.intended_after)
        for operation in manifest.operations
    ):
        blockers.append("DRY_RUN_MUTATION:OPERATION_SHAPE_INVALID")

    whitelist_entry_keys = tuple(
        (entry.resource_name, entry.field_name, entry.mutation_kind)
        for entry in whitelist.entries
    )
    if not _clean(whitelist.whitelist_id):
        blockers.append("DRY_RUN_MUTATION:WHITELIST_ID_MISSING")
    if (
        not whitelist.entries
        or any(
            not _clean(entry.resource_name)
            or not _clean(entry.field_name)
            or entry.mutation_kind != SET_EXACT
            for entry in whitelist.entries
        )
        or len(set(whitelist_entry_keys)) != len(whitelist_entry_keys)
    ):
        blockers.append("DRY_RUN_MUTATION:WHITELIST_ENTRIES_INVALID")
    if whitelist.whitelist_id != manifest.mutation_whitelist_id:
        blockers.append("DRY_RUN_MUTATION:WHITELIST_ID_MISMATCH")
    if whitelist.status != DRY_RUN_REVIEWED_ONLY:
        blockers.append("DRY_RUN_MUTATION:WHITELIST_NOT_DRY_RUN_REVIEWED")
    if whitelist.readback_status != READBACK_PASS:
        blockers.append("DRY_RUN_MUTATION:WHITELIST_READBACK_NOT_PASS")
    if compute_mutation_whitelist_hash(whitelist) != whitelist.record_hash:
        blockers.append("DRY_RUN_MUTATION:WHITELIST_HASH_MISMATCH")

    allowed_entries = set(whitelist_entry_keys)
    if any(
        (
            operation.resource_name,
            operation.field_name,
            operation.mutation_kind,
        )
        not in allowed_entries
        for operation in manifest.operations
    ):
        blockers.append("DRY_RUN_MUTATION:MUTATION_OUTSIDE_WHITELIST")

    rollback_by_id = {
        operation.operation_id: operation
        for operation in manifest.rollback_operations
    }
    if (
        len(rollback_by_id) != len(manifest.rollback_operations)
        or set(rollback_by_id) != set(operation_ids)
    ):
        blockers.append("DRY_RUN_MUTATION:ROLLBACK_BATCH_MISMATCH")
    else:
        for operation in manifest.operations:
            rollback = rollback_by_id[operation.operation_id]
            if (
                _rollback_target(rollback) != _operation_target(operation)
                or not _valid_scalar(rollback.restore_value)
                or not _exact_same_value(
                    rollback.restore_value,
                    operation.expected_before,
                )
            ):
                blockers.append("DRY_RUN_MUTATION:ROLLBACK_NOT_EXACT")
                break

    expected_idempotency_key = compute_idempotency_key(
        task_id=manifest.task_id,
        candidate_set_hash=manifest.candidate_set_hash,
        allocation_plan_hash=manifest.allocation_plan_hash,
        operations=manifest.operations,
    )
    if manifest.idempotency_key != expected_idempotency_key:
        blockers.append("DRY_RUN_MUTATION:IDEMPOTENCY_KEY_MISMATCH")

    if manifest.manifest_hash != compute_mutation_manifest_hash(manifest):
        blockers.append("DRY_RUN_MUTATION:MANIFEST_HASH_MISMATCH")

    if approval.approval_id != manifest.explicit_approval_id:
        blockers.append("DRY_RUN_MUTATION:APPROVAL_ID_MISMATCH")
    if approval.task_id != manifest.task_id:
        blockers.append("DRY_RUN_MUTATION:APPROVAL_TASK_MISMATCH")
    if approval.manifest_hash != manifest.manifest_hash:
        blockers.append("DRY_RUN_MUTATION:APPROVAL_MANIFEST_MISMATCH")
    if approval.approval_status != APPROVED:
        blockers.append("DRY_RUN_MUTATION:APPROVAL_NOT_APPROVED")
    if approval.readback_status != READBACK_PASS:
        blockers.append("DRY_RUN_MUTATION:APPROVAL_READBACK_NOT_PASS")
    if compute_approval_hash(approval) != approval.record_hash:
        blockers.append("DRY_RUN_MUTATION:APPROVAL_HASH_MISMATCH")

    if (
        source_pool_resolution.status != SOURCE_POOL_PASS
        or not source_pool_resolution.ready
        or not source_pool_resolution.candidate_scope_verified
    ):
        blockers.append("DRY_RUN_MUTATION:SOURCE_POOL_AUTHORITY_NOT_VERIFIED")
    if source_pool_resolution.blocking_reasons:
        blockers.append("DRY_RUN_MUTATION:SOURCE_POOL_RESOLUTION_HAS_BLOCKERS")
    if (
        source_pool_resolution.authority_id
        != manifest.source_pool_authority_id
    ):
        blockers.append("DRY_RUN_MUTATION:SOURCE_POOL_AUTHORITY_ID_MISMATCH")
    if not _valid_source_ids(source_pool_resolution.permitted_source_ids):
        blockers.append(
            "DRY_RUN_MUTATION:SOURCE_POOL_PERMITTED_SOURCE_SET_INVALID"
        )
    elif (
        _valid_source_ids(manifest.candidate_source_ids)
        and set(source_pool_resolution.permitted_source_ids)
        != set(manifest.candidate_source_ids)
    ):
        blockers.append("DRY_RUN_MUTATION:SOURCE_POOL_SOURCE_SET_MISMATCH")

    readback = manifest.readback_contract
    if not _clean(readback.contract_id):
        blockers.append("DRY_RUN_MUTATION:READBACK_CONTRACT_ID_MISSING")
    if readback.full_row_readback_required is not True:
        blockers.append("DRY_RUN_MUTATION:FULL_ROW_READBACK_REQUIRED")
    if readback.source_derived_reconciliation_required is not True:
        blockers.append("DRY_RUN_MUTATION:RECONCILIATION_REQUIRED")
    if readback.rollback_on_mismatch is not True:
        blockers.append("DRY_RUN_MUTATION:ROLLBACK_ON_MISMATCH_REQUIRED")
    if readback.readback_status != READBACK_PASS:
        blockers.append("DRY_RUN_MUTATION:READBACK_CONTRACT_NOT_PASS")

    if blockers:
        return DryRunMutationAssessment(
            status=HOLD,
            dry_run_contract_ready=False,
            production_write_authorized=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            manifest_hash=manifest.manifest_hash,
        )

    return DryRunMutationAssessment(
        status=PASS,
        dry_run_contract_ready=True,
        production_write_authorized=False,
        blocking_reasons=(),
        manifest_hash=manifest.manifest_hash,
    )
