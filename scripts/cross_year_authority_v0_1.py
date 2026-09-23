"""Pure cross-year authority resolver.

No network I/O, no external-system reads, and no production write path.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


PASS = "PASS"
HOLD = "HOLD"

CANONICAL_AUTHORITY_SCHEMA_ID = "CROSS_YEAR_AUTHORITY_REGISTRY_V1"
CANONICAL_SOURCE_IDENTITY_STATUS = "CANONICAL_VERIFIED"


@dataclass(frozen=True, slots=True)
class CrossYearAuthorityRecord:
    authority_id: str
    task_id: str
    decision: str
    permitted_source_years: tuple[int, ...]
    evidence_ref: str
    registry_status: str
    owner_decision: str
    readback_status: str
    record_hash: str


@dataclass(frozen=True, slots=True)
class CrossYearAuthorityRegistrySnapshot:
    source_name: str
    source_identity_status: str
    schema_id: str
    source_present: bool
    readback_status: str
    records: tuple[CrossYearAuthorityRecord, ...]


@dataclass(frozen=True, slots=True)
class CrossYearAuthority:
    authority_id: str
    task_id: str
    decision: str
    permitted_source_years: tuple[int, ...]
    evidence_ref: str
    source_name: str
    schema_id: str
    record_hash: str


@dataclass(frozen=True, slots=True)
class CrossYearAuthorityResolution:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    authority: CrossYearAuthority | None


def _clean_token(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _valid_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def authority_record_hash_payload(
    record: CrossYearAuthorityRecord,
) -> dict[str, object]:
    return {
        "authority_id": record.authority_id,
        "task_id": record.task_id,
        "decision": record.decision,
        "permitted_source_years": list(record.permitted_source_years),
        "evidence_ref": record.evidence_ref,
        "registry_status": record.registry_status,
        "owner_decision": record.owner_decision,
        "readback_status": record.readback_status,
    }


def compute_authority_record_hash(record: CrossYearAuthorityRecord) -> str:
    payload = authority_record_hash_payload(record)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def with_computed_record_hash(
    *,
    authority_id: str,
    task_id: str,
    decision: str,
    permitted_source_years: tuple[int, ...],
    evidence_ref: str,
    registry_status: str = "ACTIVE_CANONICAL",
    owner_decision: str = "APPROVED_BY_OWNER",
    readback_status: str = "PASS",
) -> CrossYearAuthorityRecord:
    provisional = CrossYearAuthorityRecord(
        authority_id=authority_id,
        task_id=task_id,
        decision=decision,
        permitted_source_years=permitted_source_years,
        evidence_ref=evidence_ref,
        registry_status=registry_status,
        owner_decision=owner_decision,
        readback_status=readback_status,
        record_hash="",
    )
    return CrossYearAuthorityRecord(
        authority_id=provisional.authority_id,
        task_id=provisional.task_id,
        decision=provisional.decision,
        permitted_source_years=provisional.permitted_source_years,
        evidence_ref=provisional.evidence_ref,
        registry_status=provisional.registry_status,
        owner_decision=provisional.owner_decision,
        readback_status=provisional.readback_status,
        record_hash=compute_authority_record_hash(provisional),
    )


def resolve_cross_year_authority(
    *,
    task_id: str,
    authority_id: str,
    document_year: int,
    snapshot: CrossYearAuthorityRegistrySnapshot | None,
) -> CrossYearAuthorityResolution:
    """Resolve one authority from structured canonical evidence."""

    blockers: list[str] = []

    if not _clean_token(authority_id):
        blockers.append("CROSS_YEAR:AUTHORITY_ID_MISSING")
    if not _clean_token(task_id):
        blockers.append("CROSS_YEAR:TASK_ID_MISSING")
    if not _valid_positive_int(document_year):
        blockers.append("CROSS_YEAR:DOCUMENT_YEAR_INVALID")

    if blockers:
        return CrossYearAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            authority=None,
        )

    if snapshot is None:
        return CrossYearAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=("CROSS_YEAR:SNAPSHOT_MISSING",),
            authority=None,
        )

    if not snapshot.source_present:
        blockers.append("CROSS_YEAR:REGISTRY_MISSING")
    if snapshot.source_identity_status != CANONICAL_SOURCE_IDENTITY_STATUS:
        blockers.append("CROSS_YEAR:SOURCE_NOT_CANONICAL")
    if snapshot.schema_id != CANONICAL_AUTHORITY_SCHEMA_ID:
        blockers.append("CROSS_YEAR:SCHEMA_MISMATCH")
    if snapshot.readback_status != PASS:
        blockers.append("CROSS_YEAR:REGISTRY_READBACK_NOT_PASS")

    if blockers:
        return CrossYearAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            authority=None,
        )

    matches = tuple(
        record for record in snapshot.records
        if record.authority_id == authority_id
    )

    if not matches:
        blockers.append("CROSS_YEAR:AUTHORITY_NOT_FOUND")
    elif len(matches) > 1:
        blockers.append("CROSS_YEAR:DUPLICATE_AUTHORITY_ID")

    if blockers:
        return CrossYearAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            authority=None,
        )

    record = matches[0]

    if record.task_id != task_id:
        blockers.append("CROSS_YEAR:TASK_MISMATCH")
    if record.decision != "APPROVED":
        blockers.append("CROSS_YEAR:NOT_APPROVED")
    if record.registry_status != "ACTIVE_CANONICAL":
        blockers.append("CROSS_YEAR:NOT_ACTIVE")
    if record.owner_decision != "APPROVED_BY_OWNER":
        blockers.append("CROSS_YEAR:OWNER_APPROVAL_MISSING")
    if record.readback_status != PASS:
        blockers.append("CROSS_YEAR:RECORD_READBACK_NOT_PASS")
    if not _clean_token(record.evidence_ref):
        blockers.append("CROSS_YEAR:EVIDENCE_MISSING")

    years = record.permitted_source_years
    if (
        not years
        or any(not _valid_positive_int(year) for year in years)
        or len(set(years)) != len(years)
        or document_year in years
    ):
        blockers.append("CROSS_YEAR:YEARS_INVALID")

    if record.record_hash != compute_authority_record_hash(record):
        blockers.append("CROSS_YEAR:HASH_MISMATCH")

    if blockers:
        return CrossYearAuthorityResolution(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            authority=None,
        )

    return CrossYearAuthorityResolution(
        status=PASS,
        ready=True,
        blocking_reasons=(),
        authority=CrossYearAuthority(
            authority_id=record.authority_id,
            task_id=record.task_id,
            decision=record.decision,
            permitted_source_years=record.permitted_source_years,
            evidence_ref=record.evidence_ref,
            source_name=snapshot.source_name,
            schema_id=snapshot.schema_id,
            record_hash=record.record_hash,
        ),
    )
