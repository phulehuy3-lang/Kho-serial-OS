"""Pure read-only shadow snapshot-integrity controls.

All inputs are already-materialized in memory. No external I/O is performed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, TypeAlias


PASS = "PASS"
HOLD = "HOLD"

SOURCE_OF_TRUTH = "SOURCE_OF_TRUTH"
DERIVED_READ_ONLY = "DERIVED_READ_ONLY"
_ALLOWED_ROLES = {SOURCE_OF_TRUTH, DERIVED_READ_ONLY}

Scalar: TypeAlias = str | int | bool | None
NormalizedRow: TypeAlias = tuple[tuple[str, Scalar], ...]


@dataclass(frozen=True, slots=True)
class ReadSurfaceContract:
    surface_id: str
    logical_name: str
    role: str
    fields: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True, slots=True)
class TargetSnapshotContract:
    target_id: str
    schema_version: str
    surfaces: tuple[ReadSurfaceContract, ...]
    contract_hash: str


@dataclass(frozen=True, slots=True)
class SurfaceReadResult:
    surface_id: str
    version_marker: str
    captured_at: str
    rows: tuple[Mapping[str, Scalar], ...]


@dataclass(frozen=True, slots=True)
class NormalizedSurfaceSnapshot:
    surface_id: str
    contract_hash: str
    version_marker: str
    captured_at: str
    rows: tuple[NormalizedRow, ...]
    surface_hash: str


@dataclass(frozen=True, slots=True)
class ReadOnlyShadowSnapshot:
    snapshot_id: str
    target_id: str
    schema_version: str
    surfaces: tuple[NormalizedSurfaceSnapshot, ...]
    atomic_snapshot_proven: bool
    snapshot_hash: str


@dataclass(frozen=True, slots=True)
class SnapshotAssessment:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    snapshot: ReadOnlyShadowSnapshot | None


def _clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_surface_contract_hash(
    *,
    surface_id: str,
    logical_name: str,
    role: str,
    fields: tuple[str, ...],
) -> str:
    return _canonical_sha256(
        {
            "surface_id": surface_id,
            "logical_name": logical_name,
            "role": role,
            "fields": list(fields),
        }
    )


def with_computed_surface_contract_hash(
    *,
    surface_id: str,
    logical_name: str,
    role: str,
    fields: tuple[str, ...],
) -> ReadSurfaceContract:
    return ReadSurfaceContract(
        surface_id=surface_id,
        logical_name=logical_name,
        role=role,
        fields=fields,
        contract_hash=compute_surface_contract_hash(
            surface_id=surface_id,
            logical_name=logical_name,
            role=role,
            fields=fields,
        ),
    )


def compute_target_contract_hash(
    contract: TargetSnapshotContract,
) -> str:
    return _canonical_sha256(
        {
            "target_id": contract.target_id,
            "schema_version": contract.schema_version,
            "surfaces": [
                {
                    "surface_id": surface.surface_id,
                    "contract_hash": surface.contract_hash,
                }
                for surface in contract.surfaces
            ],
        }
    )


def with_computed_target_contract_hash(
    *,
    target_id: str,
    schema_version: str,
    surfaces: tuple[ReadSurfaceContract, ...],
) -> TargetSnapshotContract:
    provisional = TargetSnapshotContract(
        target_id=target_id,
        schema_version=schema_version,
        surfaces=surfaces,
        contract_hash="",
    )
    return TargetSnapshotContract(
        target_id=provisional.target_id,
        schema_version=provisional.schema_version,
        surfaces=provisional.surfaces,
        contract_hash=compute_target_contract_hash(provisional),
    )


def validate_target_contract(
    contract: TargetSnapshotContract,
) -> tuple[str, ...]:
    blockers: list[str] = []

    if not _clean(contract.target_id):
        blockers.append("SHADOW_SNAPSHOT:TARGET_ID_MISSING")
    if not _clean(contract.schema_version):
        blockers.append("SHADOW_SNAPSHOT:SCHEMA_VERSION_MISSING")
    if not contract.surfaces:
        blockers.append("SHADOW_SNAPSHOT:SURFACES_EMPTY")

    surface_ids = tuple(surface.surface_id for surface in contract.surfaces)
    if len(set(surface_ids)) != len(surface_ids):
        blockers.append("SHADOW_SNAPSHOT:DUPLICATE_SURFACE_ID")

    for surface in contract.surfaces:
        label = surface.surface_id or "<blank>"

        if not _clean(surface.surface_id):
            blockers.append("SHADOW_SNAPSHOT:SURFACE_ID_MISSING")
        if not _clean(surface.logical_name):
            blockers.append(
                f"SHADOW_SNAPSHOT:LOGICAL_NAME_MISSING:{label}"
            )
        if surface.role not in _ALLOWED_ROLES:
            blockers.append(
                f"SHADOW_SNAPSHOT:INVALID_ROLE:{label}"
            )
        if not surface.fields:
            blockers.append(
                f"SHADOW_SNAPSHOT:FIELDS_EMPTY:{label}"
            )
        if any(not _clean(field) for field in surface.fields):
            blockers.append(
                f"SHADOW_SNAPSHOT:FIELD_NAME_INVALID:{label}"
            )
        if len(set(surface.fields)) != len(surface.fields):
            blockers.append(
                f"SHADOW_SNAPSHOT:DUPLICATE_FIELD:{label}"
            )

        expected_hash = compute_surface_contract_hash(
            surface_id=surface.surface_id,
            logical_name=surface.logical_name,
            role=surface.role,
            fields=surface.fields,
        )
        if surface.contract_hash != expected_hash:
            blockers.append(
                f"SHADOW_SNAPSHOT:SURFACE_HASH_MISMATCH:{label}"
            )

    if contract.contract_hash != compute_target_contract_hash(contract):
        blockers.append("SHADOW_SNAPSHOT:TARGET_HASH_MISMATCH")

    return tuple(sorted(set(blockers)))


def _normalize_surface_rows(
    contract: ReadSurfaceContract,
    result: SurfaceReadResult,
) -> tuple[tuple[NormalizedRow, ...], tuple[str, ...]]:
    blockers: list[str] = []
    normalized: list[NormalizedRow] = []

    if result.surface_id != contract.surface_id:
        return (), (
            f"SHADOW_SNAPSHOT:RESULT_ID_MISMATCH:{contract.surface_id}",
        )

    if not _clean(result.version_marker):
        blockers.append(
            f"SHADOW_SNAPSHOT:VERSION_MARKER_MISSING:{contract.surface_id}"
        )
    if not _clean(result.captured_at):
        blockers.append(
            f"SHADOW_SNAPSHOT:CAPTURE_MARKER_MISSING:{contract.surface_id}"
        )

    expected_fields = set(contract.fields)

    for index, row in enumerate(result.rows, start=1):
        if set(row) != expected_fields:
            blockers.append(
                "SHADOW_SNAPSHOT:FIELD_SET_MISMATCH:"
                f"{contract.surface_id}:ROW{index}"
            )
            continue

        normalized_row: list[tuple[str, Scalar]] = []
        valid = True

        for field in contract.fields:
            value = row[field]
            if value is not None and type(value) not in {str, int, bool}:
                blockers.append(
                    "SHADOW_SNAPSHOT:UNSUPPORTED_TYPE:"
                    f"{contract.surface_id}:ROW{index}:{field}"
                )
                valid = False
                continue
            normalized_row.append((field, value))

        if valid:
            normalized.append(tuple(normalized_row))

    return tuple(normalized), tuple(blockers)


def compute_surface_snapshot_hash(
    *,
    contract: ReadSurfaceContract,
    result: SurfaceReadResult,
    rows: tuple[NormalizedRow, ...],
) -> str:
    return _canonical_sha256(
        {
            "surface_id": contract.surface_id,
            "contract_hash": contract.contract_hash,
            "version_marker": result.version_marker,
            "captured_at": result.captured_at,
            "rows": [
                [[field, value] for field, value in row]
                for row in rows
            ],
        }
    )


def compute_shadow_snapshot_hash(
    *,
    snapshot_id: str,
    target: TargetSnapshotContract,
    surfaces: tuple[NormalizedSurfaceSnapshot, ...],
    atomic_snapshot_proven: bool,
) -> str:
    return _canonical_sha256(
        {
            "snapshot_id": snapshot_id,
            "target_id": target.target_id,
            "schema_version": target.schema_version,
            "surface_hashes": [
                [surface.surface_id, surface.surface_hash]
                for surface in surfaces
            ],
            "atomic_snapshot_proven": atomic_snapshot_proven,
        }
    )


def assess_shadow_snapshot(
    *,
    snapshot_id: str,
    target: TargetSnapshotContract,
    reads: Mapping[str, SurfaceReadResult],
) -> SnapshotAssessment:
    blockers = list(validate_target_contract(target))

    if not _clean(snapshot_id):
        blockers.append("SHADOW_SNAPSHOT:SNAPSHOT_ID_MISSING")

    expected_ids = tuple(surface.surface_id for surface in target.surfaces)
    actual_ids = tuple(reads.keys())

    missing_ids = sorted(set(expected_ids) - set(actual_ids))
    extra_ids = sorted(set(actual_ids) - set(expected_ids))

    for surface_id in missing_ids:
        blockers.append(
            f"SHADOW_SNAPSHOT:READ_MISSING:{surface_id}"
        )
    for surface_id in extra_ids:
        blockers.append(
            f"SHADOW_SNAPSHOT:READ_UNEXPECTED:{surface_id}"
        )

    if blockers:
        return SnapshotAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            snapshot=None,
        )

    normalized_surfaces: list[NormalizedSurfaceSnapshot] = []

    for contract in target.surfaces:
        result = reads[contract.surface_id]
        rows, row_blockers = _normalize_surface_rows(contract, result)
        blockers.extend(row_blockers)
        if row_blockers:
            continue

        normalized_surfaces.append(
            NormalizedSurfaceSnapshot(
                surface_id=contract.surface_id,
                contract_hash=contract.contract_hash,
                version_marker=result.version_marker,
                captured_at=result.captured_at,
                rows=rows,
                surface_hash=compute_surface_snapshot_hash(
                    contract=contract,
                    result=result,
                    rows=rows,
                ),
            )
        )

    if blockers:
        return SnapshotAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            snapshot=None,
        )

    surfaces = tuple(normalized_surfaces)
    version_markers = {surface.version_marker for surface in surfaces}
    atomic = len(version_markers) == 1

    snapshot = ReadOnlyShadowSnapshot(
        snapshot_id=snapshot_id,
        target_id=target.target_id,
        schema_version=target.schema_version,
        surfaces=surfaces,
        atomic_snapshot_proven=atomic,
        snapshot_hash="",
    )
    snapshot = ReadOnlyShadowSnapshot(
        snapshot_id=snapshot.snapshot_id,
        target_id=snapshot.target_id,
        schema_version=snapshot.schema_version,
        surfaces=snapshot.surfaces,
        atomic_snapshot_proven=snapshot.atomic_snapshot_proven,
        snapshot_hash=compute_shadow_snapshot_hash(
            snapshot_id=snapshot.snapshot_id,
            target=target,
            surfaces=snapshot.surfaces,
            atomic_snapshot_proven=snapshot.atomic_snapshot_proven,
        ),
    )

    if not atomic:
        return SnapshotAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=("SHADOW_SNAPSHOT:NONATOMIC_VERSION_DRIFT",),
            snapshot=snapshot,
        )

    return SnapshotAssessment(
        status=PASS,
        ready=True,
        blocking_reasons=(),
        snapshot=snapshot,
    )
