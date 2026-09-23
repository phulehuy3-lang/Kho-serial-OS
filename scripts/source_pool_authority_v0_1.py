"""Pure source-pool authority resolver.

No network I/O, no external-system reads, and no production write path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json


PASS = "PASS"
HOLD = "HOLD"

CANONICAL_SOURCE_POOL_SCHEMA_ID = "SOURCE_POOL_AUTHORITY_REGISTRY_V1"
CANONICAL_SOURCE_IDENTITY_STATUS = "CANONICAL_VERIFIED"
EXACT_SOURCE_SET = "EXACT_SOURCE_SET"


@dataclass(frozen=True, slots=True)
class SourcePoolAuthorityRecord:
    authority_id: str
    task_id: str
    line_key: str
    document_date: date
    carrier: str
    denomination: int
    scope_mode: str
    permitted_source_ids: tuple[str, ...]
    evidence_ref: str
    registry_status: str
    owner_decision: str
    readback_status: str
    record_hash: str


@dataclass(frozen=True, slots=True)
class SourcePoolAuthorityRegistrySnapshot:
    source_name: str
    source_identity_status: str
    schema_id: str
    source_present: bool
    readback_status: str
    records: tuple[SourcePoolAuthorityRecord, ...]


@dataclass(frozen=True, slots=True)
class SourcePoolAuthorityResolution:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    authority_id: str | None
    candidate_scope_verified: bool
    permitted_source_ids: tuple[str, ...]


def _clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_date(value: object) -> bool:
    return type(value) is date


def _valid_source_ids(values: object) -> bool:
    if not isinstance(values, tuple) or not values:
        return False
    if any(not _clean(value) for value in values):
        return False
    return len(set(values)) == len(values)


def source_pool_record_hash_payload(
    record: SourcePoolAuthorityRecord,
) -> dict[str, object]:
    return {
        "authority_id": record.authority_id,
        "task_id": record.task_id,
        "line_key": record.line_key,
        "document_date": record.document_date.isoformat(),
        "carrier": record.carrier,
        "denomination": record.denomination,
        "scope_mode": record.scope_mode,
        "permitted_source_ids": list(record.permitted_source_ids),
        "evidence_ref": record.evidence_ref,
        "registry_status": record.registry_status,
        "owner_decision": record.owner_decision,
        "readback_status": record.readback_status,
    }


def compute_source_pool_record_hash(
    record: SourcePoolAuthorityRecord,
) -> str:
    payload = source_pool_record_hash_payload(record)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def with_computed_source_pool_hash(
    *,
    authority_id: str,
    task_id: str,
    line_key: str,
    document_date: date,
    carrier: str,
    denomination: int,
    permitted_source_ids: tuple[str, ...],
    evidence_ref: str,
    scope_mode: str = EXACT_SOURCE_SET,
    registry_status: str = "ACTIVE_CANONICAL",
    owner_decision: str = "APPROVED_BY_OWNER",
    readback_status: str = PASS,
) -> SourcePoolAuthorityRecord:
    provisional = SourcePoolAuthorityRecord(
        authority_id=authority_id,
        task_id=task_id,
        line_key=line_key,
        document_date=document_date,
        carrier=carrier,
        denomination=denomination,
        scope_mode=scope_mode,
        permitted_source_ids=permitted_source_ids,
        evidence_ref=evidence_ref,
        registry_status=registry_status,
        owner_decision=owner_decision,
        readback_status=readback_status,
        record_hash="",
    )
    return SourcePoolAuthorityRecord(
        authority_id=provisional.authority_id,
        task_id=provisional.task_id,
        line_key=provisional.line_key,
        document_date=provisional.document_date,
        carrier=provisional.carrier,
        denomination=provisional.denomination,
        scope_mode=provisional.scope_mode,
        permitted_source_ids=provisional.permitted_source_ids,
        evidence_ref=provisional.evidence_ref,
        registry_status=provisional.registry_status,
        owner_decision=provisional.owner_decision,
        readback_status=provisional.readback_status,
        record_hash=compute_source_pool_record_hash(provisional),
    )


def resolve_source_pool_authority(
    *,
    authority_id: str,
    task_id: str,
    line_key: str,
    document_date: date,
    carrier: str,
    denomination: int,
    materialized_source_ids: tuple[str, ...],
    snapshot: SourcePoolAuthorityRegistrySnapshot | None,
) -> SourcePoolAuthorityResolution:
    """Validate exact source-pool authority from structured evidence."""

    blockers: list[str] = []

    if not _clean(authority_id):
        blockers.append("SOURCE_POOL:AUTHORITY_ID_MISSING")
    if not _clean(task_id):
        blockers.append("SOURCE_POOL:TASK_ID_MISSING")
    if not _clean(line_key):
        blockers.append("SOURCE_POOL:LINE_KEY_MISSING")
    if not _clean(carrier):
        blockers.append("SOURCE_POOL:CARRIER_MISSING")
    if not _positive_int(denomination):
        blockers.append("SOURCE_POOL:DENOMINATION_INVALID")
    if not _valid_date(document_date):
        blockers.append("SOURCE_POOL:DOCUMENT_DATE_INVALID")
    if not _valid_source_ids(materialized_source_ids):
        blockers.append("SOURCE_POOL:MATERIALIZED_SOURCE_SET_INVALID")

    if blockers:
        return SourcePoolAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            authority_id=None,
            candidate_scope_verified=False,
            permitted_source_ids=(),
        )

    if snapshot is None:
        return SourcePoolAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=("SOURCE_POOL:SNAPSHOT_MISSING",),
            authority_id=None,
            candidate_scope_verified=False,
            permitted_source_ids=(),
        )

    if not snapshot.source_present:
        blockers.append("SOURCE_POOL:REGISTRY_MISSING")
    if snapshot.source_identity_status != CANONICAL_SOURCE_IDENTITY_STATUS:
        blockers.append("SOURCE_POOL:SOURCE_NOT_CANONICAL")
    if snapshot.schema_id != CANONICAL_SOURCE_POOL_SCHEMA_ID:
        blockers.append("SOURCE_POOL:SCHEMA_MISMATCH")
    if snapshot.readback_status != PASS:
        blockers.append("SOURCE_POOL:REGISTRY_READBACK_NOT_PASS")

    if blockers:
        return SourcePoolAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            authority_id=None,
            candidate_scope_verified=False,
            permitted_source_ids=(),
        )

    matches = tuple(
        record
        for record in snapshot.records
        if record.authority_id == authority_id
    )

    if not matches:
        blockers.append("SOURCE_POOL:AUTHORITY_NOT_FOUND")
    elif len(matches) > 1:
        blockers.append("SOURCE_POOL:DUPLICATE_AUTHORITY_ID")

    if blockers:
        return SourcePoolAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            authority_id=None,
            candidate_scope_verified=False,
            permitted_source_ids=(),
        )

    record = matches[0]

    if record.task_id != task_id:
        blockers.append("SOURCE_POOL:TASK_MISMATCH")
    if record.line_key != line_key:
        blockers.append("SOURCE_POOL:LINE_MISMATCH")
    if record.document_date != document_date:
        blockers.append("SOURCE_POOL:DOCUMENT_DATE_MISMATCH")
    if record.carrier != carrier:
        blockers.append("SOURCE_POOL:CARRIER_MISMATCH")
    if record.denomination != denomination:
        blockers.append("SOURCE_POOL:DENOMINATION_MISMATCH")
    if record.scope_mode != EXACT_SOURCE_SET:
        blockers.append("SOURCE_POOL:SCOPE_MODE_UNSUPPORTED")
    if record.registry_status != "ACTIVE_CANONICAL":
        blockers.append("SOURCE_POOL:AUTHORITY_NOT_ACTIVE")
    if record.owner_decision != "APPROVED_BY_OWNER":
        blockers.append("SOURCE_POOL:OWNER_APPROVAL_MISSING")
    if record.readback_status != PASS:
        blockers.append("SOURCE_POOL:RECORD_READBACK_NOT_PASS")
    if not _clean(record.evidence_ref):
        blockers.append("SOURCE_POOL:EVIDENCE_MISSING")
    if not _valid_source_ids(record.permitted_source_ids):
        blockers.append("SOURCE_POOL:PERMITTED_SOURCE_SET_INVALID")

    if record.record_hash != compute_source_pool_record_hash(record):
        blockers.append("SOURCE_POOL:HASH_MISMATCH")

    if (
        _valid_source_ids(record.permitted_source_ids)
        and set(record.permitted_source_ids) != set(materialized_source_ids)
    ):
        blockers.append("SOURCE_POOL:MATERIALIZED_SET_MISMATCH")

    if blockers:
        return SourcePoolAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            authority_id=record.authority_id,
            candidate_scope_verified=False,
            permitted_source_ids=record.permitted_source_ids,
        )

    return SourcePoolAuthorityResolution(
        status=PASS,
        ready=True,
        blocking_reasons=(),
        authority_id=record.authority_id,
        candidate_scope_verified=True,
        permitted_source_ids=record.permitted_source_ids,
    )
