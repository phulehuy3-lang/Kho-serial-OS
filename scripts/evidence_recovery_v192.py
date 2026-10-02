"""Offline evidence-only SOP v1.9.2 adapter. No production authority."""
from dataclasses import dataclass
import hashlib


def _valid_text(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _valid_sha256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


# SOP_INBOUND_STANDARD_V1_9_2 prospective evidence-recovery hardening.
V192_SOURCE_RECOVERY_IN_PROGRESS = "SOURCE_RECOVERY_IN_PROGRESS"
V192_SOURCE_ARCHIVED_VERIFIED = "SOURCE_ARCHIVED_VERIFIED"
V192_SOURCE_FOUND_NOT_CANONICAL = "SOURCE_FOUND_NOT_CANONICAL"
V192_SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED = (
    "SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED"
)
V192_SOURCE_BYTES_UNAVAILABLE = "SOURCE_BYTES_UNAVAILABLE"
V192_SOURCE_HASH_MISMATCH = "SOURCE_HASH_MISMATCH"
V192_SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY = (
    "SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY"
)
V192_HISTORICAL_SOURCE_RANK_REPLAYABLE = "HISTORICAL_SOURCE_RANK_REPLAYABLE"
V192_POSTCLOSE_FAIL_CLOSED_ONLY = "POSTCLOSE_FAIL_CLOSED_ONLY"
V192_BLOCKED_UNPROVEN = "BLOCKED_UNPROVEN"


@dataclass(frozen=True, slots=True)
class EvidenceRecoveryCandidateV192:
    filename: object
    library_path: object
    sha256: object
    visual_match: object
    bytes_available: object = False
    canonical_archived: object = False
    library_file_id: object = None
    source_bytes: object = None
    canonical_file_id: object = None
    provider_readback_bytes: object = None


@dataclass(frozen=True, slots=True)
class EvidenceRecoveryRequestV192:
    evidence_key: object
    prior_chat_supplied: object
    text_search_hits: object
    candidates: object
    historical_sha256: object
    all_stages_exhausted: object
    completed_stages: object = ()


@dataclass(frozen=True, slots=True)
class EvidenceRecoveryResultV192:
    status: str
    selected_path: str | None
    selected_sha256: str | None
    missing_evidence_hold_allowed: bool
    inventory_mutation_authorized: bool = False


def _validate_recovery_request_v1_9_2(
    request: EvidenceRecoveryRequestV192,
) -> None:
    if not _valid_text(request.evidence_key):
        raise ValueError("EVIDENCE_KEY_INVALID")
    if type(request.prior_chat_supplied) is not bool:
        raise ValueError("PRIOR_CHAT_FLAG_INVALID")
    if type(request.text_search_hits) is not int or request.text_search_hits < 0:
        raise ValueError("TEXT_SEARCH_HITS_INVALID")
    if type(request.candidates) is not tuple:
        raise ValueError("CANDIDATES_CONTAINER_INVALID")
    if type(request.all_stages_exhausted) is not bool:
        raise ValueError("EXHAUSTION_FLAG_INVALID")
    if request.historical_sha256 is not None and not _valid_sha256(
        request.historical_sha256
    ):
        raise ValueError("HISTORICAL_HASH_INVALID")
    for candidate in request.candidates:
        if type(candidate) is not EvidenceRecoveryCandidateV192:
            raise ValueError("CANDIDATE_TYPE_INVALID")
        if not (
            _valid_text(candidate.filename)
            and _valid_text(candidate.library_path)
            and _valid_sha256(candidate.sha256)
        ):
            raise ValueError("CANDIDATE_IDENTITY_INVALID")
        for value in (
            candidate.visual_match,
            candidate.bytes_available,
            candidate.canonical_archived,
        ):
            if type(value) is not bool:
                raise ValueError("CANDIDATE_BOOLEAN_INVALID")


def evaluate_evidence_recovery_v1_9_2(
    request: object,
) -> EvidenceRecoveryResultV192:
    """Search-zero is not missing; recovery remains inventory-read-only."""

    if type(request) is not EvidenceRecoveryRequestV192:
        raise ValueError("REQUEST_TYPE_INVALID")
    _validate_recovery_request_v1_9_2(request)

    visual_hash_mismatch = False
    bytes_unavailable = False
    for candidate in request.candidates:
        if candidate.visual_match is not True:
            continue
        if candidate.bytes_available is not True:
            bytes_unavailable = True
            continue
        if type(candidate.source_bytes) is not bytes:
            bytes_unavailable = True
            continue
        if hashlib.sha256(candidate.source_bytes).hexdigest() != candidate.sha256:
            visual_hash_mismatch = True
            continue
        if not _valid_text(candidate.library_file_id):
            continue
        if (
            request.historical_sha256 is not None
            and candidate.sha256 != request.historical_sha256
        ):
            visual_hash_mismatch = True
            continue
        return EvidenceRecoveryResultV192(
            (
                V192_SOURCE_ARCHIVED_VERIFIED
                if (candidate.canonical_archived is True
                    and _valid_text(candidate.canonical_file_id)
                    and type(candidate.provider_readback_bytes) is bytes
                    and candidate.provider_readback_bytes == candidate.source_bytes)
                else V192_SOURCE_FOUND_NOT_CANONICAL
            ),
            candidate.library_path,
            candidate.sha256,
            False,
        )

    if bytes_unavailable:
        return EvidenceRecoveryResultV192(
            V192_SOURCE_BYTES_UNAVAILABLE, None, None, False
        )
    if visual_hash_mismatch:
        return EvidenceRecoveryResultV192(
            V192_SOURCE_HASH_MISMATCH,
            None,
            None,
            False,
        )
    if (
        request.prior_chat_supplied is True
        and request.all_stages_exhausted is False
    ):
        return EvidenceRecoveryResultV192(
            V192_SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED,
            None,
            None,
            False,
        )
    if (request.all_stages_exhausted is True
        and type(request.completed_stages) is tuple
        and request.completed_stages == RECOVERY_STAGES_V192):
        return EvidenceRecoveryResultV192(
            V192_SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY,
            None,
            None,
            True,
        )
    return EvidenceRecoveryResultV192(
        V192_SOURCE_RECOVERY_IN_PROGRESS,
        None,
        None,
        False,
    )


def validate_single_active_recovery_root_v1_9_2(
    active_root_count: object,
) -> bool:
    if type(active_root_count) is not int or active_root_count != 1:
        raise ValueError("RECOVERY_ROOT_CARDINALITY_INVALID")
    return True


def classify_outbound_historical_proof_v1_9_2(
    *,
    historical_prewrite_snapshot_available: object,
    postclose_fail_closed_proven: object,
) -> str:
    """Post-close fail-closed proof never becomes retroactive rank PASS."""

    if type(historical_prewrite_snapshot_available) is not bool:
        return V192_BLOCKED_UNPROVEN
    if type(postclose_fail_closed_proven) is not bool:
        return V192_BLOCKED_UNPROVEN
    if historical_prewrite_snapshot_available is True:
        return V192_HISTORICAL_SOURCE_RANK_REPLAYABLE
    if postclose_fail_closed_proven is True:
        return V192_POSTCLOSE_FAIL_CLOSED_ONLY
    return V192_BLOCKED_UNPROVEN



RECOVERY_STAGES_V192 = (
    "CURRENT_ATTACHMENTS", "PROJECT_PATH", "TIME_WINDOW_INVENTORY",
    "VISUAL_INSPECTION", "HISTORICAL_IDENTITY", "HASH_COMPARISON",
    "CANONICAL_LOOKUP",
)


def run_disposable_evidence_workflow_v192(
    request: object, sandbox: object,
) -> tuple[EvidenceRecoveryResultV192, tuple[str, ...]]:
    """Execute G1A/B/C before a disposable marker; no production writer exists.

    The sandbox must be an exact list, not a callback or provider adapter.
    Remaining warehouse gates are outside this evidence-only regression.
    """
    if type(sandbox) is not list:
        raise ValueError("DISPOSABLE_SANDBOX_REQUIRED")
    result = evaluate_evidence_recovery_v1_9_2(request)
    trace = ["G1A_RECOVERY"]
    if result.selected_sha256 is not None:
        trace.append("G1B_IDENTITY_BYTES_BOUND")
    if result.status == V192_SOURCE_ARCHIVED_VERIFIED:
        trace.append("G1C_PROVIDER_READBACK_MATCH")
        sandbox.append("DISPOSABLE_MARKER")
        trace.append("DISPOSABLE_MUTATION")
    return result, tuple(trace)
