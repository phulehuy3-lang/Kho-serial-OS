"""Pure inbound evidence materialization-package validation.

No live read, provider client, filesystem acquisition, credential, or writer.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


CONTRACT_ID = "INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V1"
SCENARIO_ID = "INBOUND_SERIAL_QUERY_DERIVED_V1"
PASS = "PASS"
HOLD = "HOLD"

REQUIRED_SURFACES = (
    "INBOUND_SOURCE_RECORD",
    "ACTIVE_SERIAL_INTERVAL_UNIVERSE",
    "INBOUND_DERIVED_QUERY_PROJECTION",
    "INBOUND_QUERY_FORMULA_ANCHOR",
    "ACTIVE_HOLD_INTERVAL_UNIVERSE",
)

_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True, slots=True)
class SurfaceHashEvidence:
    """Opaque deterministic hash for one locked warehouse evidence surface."""

    surface_id: object
    surface_hash: object


@dataclass(frozen=True, slots=True)
class InboundEvidenceMaterializationPackage:
    """Already-materialized opaque evidence bindings for the locked inbound scenario."""

    contract_id: object
    scenario_id: object
    task_id: object
    scope_id: object

    target_authority_id: object
    target_authority_hash: object
    permission_proof_id: object
    permission_proof_hash: object
    surface_registry_id: object
    surface_registry_hash: object
    zero_write_attestation_id: object
    zero_write_attestation_hash: object

    warehouse_schema_version: object
    provider_version_marker: object
    capture_marker: object
    control10_target_contract_hash: object
    control10_snapshot_hash: object
    surfaces: object

    serial_universe_complete: object
    serial_universe_evidence_id: object
    serial_universe_evidence_hash: object
    hold_universe_complete: object
    hold_universe_evidence_id: object
    hold_universe_evidence_hash: object

    mapping_contract_id: object
    mapping_contract_hash: object
    source_evidence_binding_id: object
    source_evidence_binding_hash: object
    formula_reconciliation_binding_id: object
    formula_reconciliation_binding_hash: object

    receipt_id: object
    receipt_hash: object

    live_read_authorized: object
    production_write_authorized: object


@dataclass(frozen=True, slots=True)
class MaterializationPackageResult:
    """Deterministic fail-closed result for the materialized package boundary."""

    status: str
    package_coherent: bool
    blocking_reasons: tuple[str, ...]
    package_hash: str | None
    live_read_authorized: bool = False
    production_write_authorized: bool = False


def _valid_text(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
    )


def _valid_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in _HEX for character in value)
    )


def _valid_id_hash_pair(identifier: object, digest: object) -> bool:
    return _valid_text(identifier) and _valid_sha256(digest)


def _validate_surfaces(
    surfaces: object,
) -> tuple[tuple[SurfaceHashEvidence, ...] | None, set[str]]:
    reasons: set[str] = set()

    if type(surfaces) is not tuple:
        reasons.add("SURFACE_CONTAINER_INVALID")
        return None, reasons

    valid_entries = all(
        type(item) is SurfaceHashEvidence
        and _valid_text(item.surface_id)
        and _valid_sha256(item.surface_hash)
        for item in surfaces
    )
    if not valid_entries:
        reasons.add("SURFACE_EVIDENCE_INVALID")
        return None, reasons

    ids = tuple(item.surface_id for item in surfaces)
    if len(ids) != len(set(ids)) or set(ids) != set(REQUIRED_SURFACES):
        reasons.add("SURFACE_SET_INVALID")
        return None, reasons

    by_id = {item.surface_id: item for item in surfaces}
    ordered = tuple(by_id[surface_id] for surface_id in REQUIRED_SURFACES)
    return ordered, reasons


def _canonical_payload(
    package: InboundEvidenceMaterializationPackage,
    ordered_surfaces: tuple[SurfaceHashEvidence, ...],
) -> dict[str, object]:
    return {
        "contract_id": package.contract_id,
        "scenario_id": package.scenario_id,
        "task_id": package.task_id,
        "scope_id": package.scope_id,
        "target_authority_id": package.target_authority_id,
        "target_authority_hash": package.target_authority_hash,
        "permission_proof_id": package.permission_proof_id,
        "permission_proof_hash": package.permission_proof_hash,
        "surface_registry_id": package.surface_registry_id,
        "surface_registry_hash": package.surface_registry_hash,
        "zero_write_attestation_id": package.zero_write_attestation_id,
        "zero_write_attestation_hash": package.zero_write_attestation_hash,
        "warehouse_schema_version": package.warehouse_schema_version,
        "provider_version_marker": package.provider_version_marker,
        "capture_marker": package.capture_marker,
        "control10_target_contract_hash": package.control10_target_contract_hash,
        "control10_snapshot_hash": package.control10_snapshot_hash,
        "surfaces": [
            {
                "surface_id": item.surface_id,
                "surface_hash": item.surface_hash,
            }
            for item in ordered_surfaces
        ],
        "serial_universe_complete": package.serial_universe_complete,
        "serial_universe_evidence_id": package.serial_universe_evidence_id,
        "serial_universe_evidence_hash": package.serial_universe_evidence_hash,
        "hold_universe_complete": package.hold_universe_complete,
        "hold_universe_evidence_id": package.hold_universe_evidence_id,
        "hold_universe_evidence_hash": package.hold_universe_evidence_hash,
        "mapping_contract_id": package.mapping_contract_id,
        "mapping_contract_hash": package.mapping_contract_hash,
        "source_evidence_binding_id": package.source_evidence_binding_id,
        "source_evidence_binding_hash": package.source_evidence_binding_hash,
        "formula_reconciliation_binding_id": package.formula_reconciliation_binding_id,
        "formula_reconciliation_binding_hash": package.formula_reconciliation_binding_hash,
        "receipt_id": package.receipt_id,
        "receipt_hash": package.receipt_hash,
        "live_read_authorized": package.live_read_authorized,
        "production_write_authorized": package.production_write_authorized,
    }


def _package_hash(
    package: InboundEvidenceMaterializationPackage,
    ordered_surfaces: tuple[SurfaceHashEvidence, ...],
) -> str:
    payload = _canonical_payload(package, ordered_surfaces)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_inbound_evidence_materialization_package(
    package: object,
) -> MaterializationPackageResult:
    """Validate structural/materialized coherence only; never grant live authority."""

    if type(package) is not InboundEvidenceMaterializationPackage:
        return MaterializationPackageResult(
            status=HOLD,
            package_coherent=False,
            blocking_reasons=("PACKAGE_TYPE_INVALID",),
            package_hash=None,
        )

    reasons: set[str] = set()

    if package.contract_id != CONTRACT_ID:
        reasons.add("CONTRACT_INVALID")
    if package.scenario_id != SCENARIO_ID:
        reasons.add("SCENARIO_INVALID")
    if not (_valid_text(package.task_id) and _valid_text(package.scope_id)):
        reasons.add("BINDING_INVALID")

    if not _valid_id_hash_pair(
        package.target_authority_id,
        package.target_authority_hash,
    ):
        reasons.add("TARGET_AUTHORITY_EVIDENCE_INVALID")

    if not _valid_id_hash_pair(
        package.permission_proof_id,
        package.permission_proof_hash,
    ):
        reasons.add("PERMISSION_EVIDENCE_INVALID")

    if not _valid_id_hash_pair(
        package.surface_registry_id,
        package.surface_registry_hash,
    ):
        reasons.add("SURFACE_REGISTRY_EVIDENCE_INVALID")

    if not _valid_id_hash_pair(
        package.zero_write_attestation_id,
        package.zero_write_attestation_hash,
    ):
        reasons.add("ZERO_WRITE_EVIDENCE_INVALID")

    if not _valid_text(package.warehouse_schema_version):
        reasons.add("SCHEMA_VERSION_INVALID")
    if not _valid_text(package.provider_version_marker):
        reasons.add("PROVIDER_VERSION_INVALID")
    if not _valid_text(package.capture_marker):
        reasons.add("CAPTURE_MARKER_INVALID")

    if not (
        _valid_sha256(package.control10_target_contract_hash)
        and _valid_sha256(package.control10_snapshot_hash)
    ):
        reasons.add("CONTROL10_BINDING_INVALID")

    ordered_surfaces, surface_reasons = _validate_surfaces(package.surfaces)
    reasons.update(surface_reasons)

    if type(package.serial_universe_complete) is not bool:
        reasons.add("SERIAL_UNIVERSE_COMPLETENESS_UNPROVEN")
    elif package.serial_universe_complete is not True:
        reasons.add("SERIAL_UNIVERSE_COMPLETENESS_UNPROVEN")

    if not _valid_id_hash_pair(
        package.serial_universe_evidence_id,
        package.serial_universe_evidence_hash,
    ):
        reasons.add("SERIAL_UNIVERSE_EVIDENCE_INVALID")

    if type(package.hold_universe_complete) is not bool:
        reasons.add("HOLD_UNIVERSE_COMPLETENESS_UNPROVEN")
    elif package.hold_universe_complete is not True:
        reasons.add("HOLD_UNIVERSE_COMPLETENESS_UNPROVEN")

    if not _valid_id_hash_pair(
        package.hold_universe_evidence_id,
        package.hold_universe_evidence_hash,
    ):
        reasons.add("HOLD_UNIVERSE_EVIDENCE_INVALID")

    if not _valid_id_hash_pair(
        package.mapping_contract_id,
        package.mapping_contract_hash,
    ):
        reasons.add("MAPPING_EVIDENCE_INVALID")

    if not _valid_id_hash_pair(
        package.source_evidence_binding_id,
        package.source_evidence_binding_hash,
    ):
        reasons.add("SOURCE_EVIDENCE_BINDING_INVALID")

    if not _valid_id_hash_pair(
        package.formula_reconciliation_binding_id,
        package.formula_reconciliation_binding_hash,
    ):
        reasons.add("FORMULA_RECONCILIATION_BINDING_INVALID")

    if not _valid_id_hash_pair(package.receipt_id, package.receipt_hash):
        reasons.add("RECEIPT_EVIDENCE_INVALID")

    if (
        type(package.live_read_authorized) is not bool
        or package.live_read_authorized is not False
        or type(package.production_write_authorized) is not bool
        or package.production_write_authorized is not False
    ):
        reasons.add("AUTHORITY_INVARIANT_INVALID")

    if reasons:
        return MaterializationPackageResult(
            status=HOLD,
            package_coherent=False,
            blocking_reasons=tuple(sorted(reasons)),
            package_hash=None,
        )

    assert ordered_surfaces is not None
    return MaterializationPackageResult(
        status=PASS,
        package_coherent=True,
        blocking_reasons=(),
        package_hash=_package_hash(package, ordered_surfaces),
    )
