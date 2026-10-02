"""Pure SOP v1.9.2 evidence-recovery and historical-proof controls.

Public-safe, deterministic and side-effect free. No provider client, live read,
filesystem mutation, credential, or Production write authority.
"""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_RECOVERY_IN_PROGRESS = "SOURCE_RECOVERY_IN_PROGRESS"
SOURCE_ARCHIVED_VERIFIED = "SOURCE_ARCHIVED_VERIFIED"
SOURCE_FOUND_NOT_CANONICAL = "SOURCE_FOUND_NOT_CANONICAL"
SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED = (
    "SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED"
)
SOURCE_BYTES_UNAVAILABLE = "SOURCE_BYTES_UNAVAILABLE"
SOURCE_HASH_MISMATCH = "SOURCE_HASH_MISMATCH"
SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY = (
    "SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY"
)

HISTORICAL_SOURCE_RANK_REPLAYABLE = "HISTORICAL_SOURCE_RANK_REPLAYABLE"
POSTCLOSE_FAIL_CLOSED_ONLY = "POSTCLOSE_FAIL_CLOSED_ONLY"
BLOCKED_UNPROVEN = "BLOCKED_UNPROVEN"

_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    filename: object
    library_path: object
    sha256: object
    visual_match: object
    bytes_available: object = True
    canonical_archived: object = True


@dataclass(frozen=True, slots=True)
class EvidenceRecoveryRequest:
    evidence_key: object
    prior_chat_supplied: object
    text_search_hits: object
    candidates: object
    historical_sha256: object
    all_stages_exhausted: object


@dataclass(frozen=True, slots=True)
class EvidenceRecoveryResult:
    status: str
    selected_path: str | None
    selected_sha256: str | None
    missing_evidence_hold_allowed: bool
    inventory_mutation_authorized: bool = False


class EvidenceRecoveryError(ValueError):
    """Fail-closed structural error for malformed recovery evidence."""


def _valid_text(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _valid_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in _HEX for character in value)
    )


def _validate_request(request: EvidenceRecoveryRequest) -> None:
    if not _valid_text(request.evidence_key):
        raise EvidenceRecoveryError("EVIDENCE_KEY_INVALID")
    if type(request.prior_chat_supplied) is not bool:
        raise EvidenceRecoveryError("PRIOR_CHAT_FLAG_INVALID")
    if type(request.text_search_hits) is not int or request.text_search_hits < 0:
        raise EvidenceRecoveryError("TEXT_SEARCH_HITS_INVALID")
    if type(request.candidates) is not tuple:
        raise EvidenceRecoveryError("CANDIDATES_CONTAINER_INVALID")
    if type(request.all_stages_exhausted) is not bool:
        raise EvidenceRecoveryError("EXHAUSTION_FLAG_INVALID")
    if request.historical_sha256 is not None and not _valid_sha256(
        request.historical_sha256
    ):
        raise EvidenceRecoveryError("HISTORICAL_HASH_INVALID")

    for candidate in request.candidates:
        if type(candidate) is not EvidenceCandidate:
            raise EvidenceRecoveryError("CANDIDATE_TYPE_INVALID")
        if not (
            _valid_text(candidate.filename)
            and _valid_text(candidate.library_path)
            and _valid_sha256(candidate.sha256)
        ):
            raise EvidenceRecoveryError("CANDIDATE_IDENTITY_INVALID")
        for value in (
            candidate.visual_match,
            candidate.bytes_available,
            candidate.canonical_archived,
        ):
            if type(value) is not bool:
                raise EvidenceRecoveryError("CANDIDATE_BOOLEAN_INVALID")


def evaluate_evidence_recovery(
    request: object,
) -> EvidenceRecoveryResult:
    """Apply G1A/G1B semantics; search-zero alone never means missing."""

    if type(request) is not EvidenceRecoveryRequest:
        raise EvidenceRecoveryError("REQUEST_TYPE_INVALID")

    _validate_request(request)

    visual_hash_mismatch = False

    for candidate in request.candidates:
        if candidate.visual_match is not True:
            continue

        if candidate.bytes_available is not True:
            return EvidenceRecoveryResult(
                status=SOURCE_BYTES_UNAVAILABLE,
                selected_path=candidate.library_path,
                selected_sha256=None,
                missing_evidence_hold_allowed=False,
            )

        if (
            request.historical_sha256 is not None
            and candidate.sha256 != request.historical_sha256
        ):
            visual_hash_mismatch = True
            continue

        return EvidenceRecoveryResult(
            status=(
                SOURCE_ARCHIVED_VERIFIED
                if candidate.canonical_archived is True
                else SOURCE_FOUND_NOT_CANONICAL
            ),
            selected_path=candidate.library_path,
            selected_sha256=candidate.sha256,
            missing_evidence_hold_allowed=False,
        )

    if visual_hash_mismatch:
        return EvidenceRecoveryResult(
            status=SOURCE_HASH_MISMATCH,
            selected_path=None,
            selected_sha256=None,
            missing_evidence_hold_allowed=False,
        )

    if request.prior_chat_supplied is True and request.all_stages_exhausted is False:
        return EvidenceRecoveryResult(
            status=SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED,
            selected_path=None,
            selected_sha256=None,
            missing_evidence_hold_allowed=False,
        )

    if request.all_stages_exhausted is True:
        return EvidenceRecoveryResult(
            status=SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY,
            selected_path=None,
            selected_sha256=None,
            missing_evidence_hold_allowed=True,
        )

    return EvidenceRecoveryResult(
        status=SOURCE_RECOVERY_IN_PROGRESS,
        selected_path=None,
        selected_sha256=None,
        missing_evidence_hold_allowed=False,
    )


def validate_single_active_recovery_root(active_root_count: object) -> bool:
    """Enforce one unresolved evidence identity -> one active RecoveryRoot."""

    if type(active_root_count) is not int or active_root_count != 1:
        raise EvidenceRecoveryError("RECOVERY_ROOT_CARDINALITY_INVALID")
    return True


def classify_outbound_historical_proof(
    *,
    historical_prewrite_snapshot_available: object,
    postclose_fail_closed_proven: object,
) -> str:
    """Never convert post-close fail-closed proof into retroactive rank PASS."""

    if type(historical_prewrite_snapshot_available) is not bool:
        return BLOCKED_UNPROVEN
    if type(postclose_fail_closed_proven) is not bool:
        return BLOCKED_UNPROVEN

    if historical_prewrite_snapshot_available is True:
        return HISTORICAL_SOURCE_RANK_REPLAYABLE

    if postclose_fail_closed_proven is True:
        return POSTCLOSE_FAIL_CLOSED_ONLY

    return BLOCKED_UNPROVEN
