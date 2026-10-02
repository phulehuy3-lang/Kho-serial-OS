"""SOP v1.9.2 pure evidence gates over already-acquired records.

No discovery client, archive writer, inventory writer or live authority.
Provider facts must be supplied by a trusted caller; this validates their
bindings and bytes, not the authenticity of a caller's provider attestations.
"""
from dataclasses import dataclass
from datetime import date, datetime
import hashlib

STAGES = (
    'CURRENT_ATTACHMENTS', 'PROJECT_LIBRARY_PATH', 'TIME_WINDOW_INVENTORY',
    'VISUAL_INSPECTION', 'HISTORICAL_IDENTITY', 'HASH_COMPARISON',
    'CANONICAL_LOOKUP',
)


def _text(value) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _sha(value) -> bool:
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _time(value) -> datetime | None:
    if not _text(value):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


@dataclass(frozen=True)
class StageRecord:
    stage: object
    evidence_key: object
    outcome: object  # NO_MATCH or UNAVAILABLE; unavailable never proves absence
    receipt_id: object


@dataclass(frozen=True)
class EvidenceIdentity:
    evidence_key: object
    library_file_id: object
    library_path: object
    original_filename: object
    document_no: object
    document_date: object
    supplier_role: object
    sha256: object
    byte_size: object
    mime: object
    provider_created_at: object
    evidence_grade: object


@dataclass(frozen=True)
class ArchiveReadback:
    evidence_key: object
    canonical_file_id: object
    canonical_folder_id: object
    receipt_id: object
    provider_readback_at: object
    readback_bytes: object


@dataclass(frozen=True)
class Candidate:
    identity: object
    source_bytes: object
    visual_match: object
    archive: object = None


@dataclass(frozen=True)
class RecoveryRequest:
    evidence_key: object
    prior_chat_supplied: object
    text_search_hits: object
    candidates: object
    historical_sha256: object
    stage_records: object
    active_recovery_roots: object


@dataclass(frozen=True)
class GateResult:
    status: str
    blocking_reasons: tuple[str, ...] = ()
    identity: EvidenceIdentity | None = None
    trace: tuple[str, ...] = ()
    missing_evidence_hold_allowed: bool = False
    prospective_prewrite_ready: bool = False
    inventory_mutation_authorized: bool = False


def _blocked(reason) -> GateResult:
    return GateResult('BLOCKED_UNPROVEN', (reason,))


def evaluate_recovery(request) -> GateResult:
    """G1A -> G1B -> G1C; search-zero alone can never permit absence HOLD."""
    if type(request) is not RecoveryRequest:
        return _blocked('REQUEST_TYPE_INVALID')
    if not _text(request.evidence_key):
        return _blocked('EVIDENCE_KEY_INVALID')
    if type(request.prior_chat_supplied) is not bool:
        return _blocked('PRIOR_CHAT_FLAG_INVALID')
    if type(request.text_search_hits) is not int or request.text_search_hits < 0:
        return _blocked('TEXT_SEARCH_HITS_INVALID')
    if type(request.candidates) is not tuple or type(request.stage_records) is not tuple:
        return _blocked('RECOVERY_CONTAINER_INVALID')
    if request.historical_sha256 is not None and not _sha(request.historical_sha256):
        return _blocked('HISTORICAL_HASH_INVALID')
    if (type(request.active_recovery_roots) is not tuple
            or len(request.active_recovery_roots) != 1
            or not _text(request.active_recovery_roots[0])):
        return _blocked('RECOVERY_ROOT_CARDINALITY_INVALID')
    records = request.stage_records
    for record in records:
        if (type(record) is not StageRecord or record.stage not in STAGES
                or record.evidence_key != request.evidence_key
                or record.outcome not in ('NO_MATCH', 'UNAVAILABLE')
                or not _text(record.receipt_id)):
            return _blocked('STAGE_RECORD_INVALID')
    if len({r.stage for r in records}) != len(records):
        return _blocked('STAGE_DUPLICATE')
    if len({r.receipt_id for r in records}) != len(records):
        return _blocked('STAGE_RECEIPT_DUPLICATE')
    if tuple(r.stage for r in records) != STAGES[:len(records)]:
        return _blocked('STAGE_ORDER_INVALID')

    matches = []
    unavailable = False
    mismatch = False
    for candidate in request.candidates:
        if type(candidate) is not Candidate or type(candidate.visual_match) is not bool:
            return _blocked('CANDIDATE_INVALID')
        identity = candidate.identity
        if type(identity) is not EvidenceIdentity or identity.evidence_key != request.evidence_key:
            return _blocked('IDENTITY_BINDING_INVALID')
        if not candidate.visual_match:
            continue
        if candidate.source_bytes is None:
            unavailable = True
            continue
        if type(candidate.source_bytes) is not bytes or not candidate.source_bytes:
            return _blocked('SOURCE_BYTES_INVALID')
        fields = (identity.library_file_id, identity.library_path,
                  identity.original_filename, identity.document_no,
                  identity.document_date, identity.supplier_role,
                  identity.mime, identity.evidence_grade)
        if (not all(_text(v) for v in fields) or not _sha(identity.sha256)
                or type(identity.byte_size) is not int or identity.byte_size <= 0
                or _time(identity.provider_created_at) is None):
            return _blocked('IDENTITY_FIELDS_INVALID')
        if identity.evidence_grade != 'ORIGINAL':
            return _blocked('SOURCE_GRADE_NOT_ORIGINAL')
        try:
            if date.fromisoformat(identity.document_date).isoformat() != identity.document_date:
                return _blocked('DOCUMENT_DATE_INVALID')
        except ValueError:
            return _blocked('DOCUMENT_DATE_INVALID')
        actual = hashlib.sha256(candidate.source_bytes).hexdigest()
        if (actual != identity.sha256 or len(candidate.source_bytes) != identity.byte_size
                or (request.historical_sha256 is not None
                    and actual != request.historical_sha256)):
            mismatch = True
            continue
        matches.append(candidate)
    if len(matches) > 1:
        return _blocked('CANDIDATE_AMBIGUOUS')
    if matches:
        selected = matches[0]
        identity = selected.identity
        trace = ('G1A_RECOVERY_PASS', 'G1B_IDENTITY_PASS')
        archive = selected.archive
        if archive is None:
            return GateResult('SOURCE_FOUND_NOT_CANONICAL', identity=identity, trace=trace)
        if (type(archive) is not ArchiveReadback
                or archive.evidence_key != request.evidence_key
                or not all(_text(v) for v in (archive.canonical_file_id,
                    archive.canonical_folder_id, archive.receipt_id))
                or _time(archive.provider_readback_at) is None
                or _time(archive.provider_readback_at) < _time(identity.provider_created_at)
                or type(archive.readback_bytes) is not bytes):
            return _blocked('ARCHIVE_READBACK_INVALID')
        if archive.readback_bytes != selected.source_bytes:
            return GateResult('SOURCE_HASH_MISMATCH', ('ARCHIVE_BYTES_MISMATCH',), identity, trace)
        return GateResult('SOURCE_ARCHIVED_VERIFIED', identity=identity,
                          trace=trace + ('G1C_ARCHIVE_READBACK_PASS',),
                          prospective_prewrite_ready=True)
    if unavailable:
        return GateResult('SOURCE_BYTES_UNAVAILABLE')
    if mismatch:
        return GateResult('SOURCE_HASH_MISMATCH')
    if (request.text_search_hits == 0 and len(records) == len(STAGES)
            and all(r.outcome == 'NO_MATCH' for r in records)):
        return GateResult('SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY',
                          missing_evidence_hold_allowed=True)
    return GateResult('SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED'
                      if request.prior_chat_supplied else 'SOURCE_RECOVERY_IN_PROGRESS')


def evaluate_prewrite(request, *, task_id, resolved_task_ids, frozen_generation,
                      current_generation, prior_gates_pass) -> GateResult:
    """Compose evidence with stable-ID/scope checks; never grant production authority.

    prior_gates_pass is a strictly typed result from the existing warehouse gate
    caller. It is not an alternative implementation of serial/allocation gates.
    """
    recovery = evaluate_recovery(request)
    if not recovery.prospective_prewrite_ready:
        return recovery
    if (not _text(task_id) or type(resolved_task_ids) is not tuple
            or resolved_task_ids != (task_id,)):
        return _blocked('TRANSACTION_IDENTITY_NOT_UNIQUE')
    if (not _text(frozen_generation) or not _text(current_generation)
            or frozen_generation != current_generation):
        return _blocked('SESSION_SCOPE_STALE')
    if type(prior_gates_pass) is not bool or prior_gates_pass is not True:
        return _blocked('WAREHOUSE_GATES_UNPROVEN')
    return GateResult('PREWRITE_READY', identity=recovery.identity,
                      trace=recovery.trace + ('STABLE_ID_PASS', 'SCOPE_CURRENT',
                                             'WAREHOUSE_GATES_PASS', 'PREWRITE_READY'),
                      prospective_prewrite_ready=True)


def classify_outbound_history(*, historical_prewrite_snapshot_available,
                              postclose_fail_closed_proven) -> str:
    """Replayable is not historical PASS; post-close proof cannot repair history."""
    if (type(historical_prewrite_snapshot_available) is not bool
            or type(postclose_fail_closed_proven) is not bool):
        return 'BLOCKED_UNPROVEN'
    if historical_prewrite_snapshot_available:
        return 'HISTORICAL_SOURCE_RANK_REPLAYABLE'
    return 'POSTCLOSE_FAIL_CLOSED_ONLY' if postclose_fail_closed_proven else 'BLOCKED_UNPROVEN'
