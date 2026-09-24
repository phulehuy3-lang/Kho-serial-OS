"""Pure already-materialized warehouse source read-back validation.

No external I/O, no live read, and no production mutation path.
"""

from __future__ import annotations

from dataclasses import dataclass


CONTRACT_ID = "SOURCE_READBACK_V1"


@dataclass(frozen=True, slots=True)
class SourceFieldValue:
    """One exact source field/value pair."""

    field_id: object
    value: object


@dataclass(frozen=True, slots=True)
class MaterializedSourceRecord:
    """One already-materialized source record bound to task/scope/capture."""

    task_id: object
    scope_id: object
    capture_marker: object
    fields: object


@dataclass(frozen=True, slots=True)
class SourceReadbackRequest:
    """Expected source record and optional already-materialized read-back."""

    contract_id: object
    expected_record: object
    readback_record: object


@dataclass(frozen=True, slots=True)
class SourceReadbackResult:
    """Deterministic fail-closed source read-back result."""

    status: str
    readback_match: bool
    blocking_reasons: tuple[str, ...]
    production_write_authorized: bool = False


def _valid_exact_text(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
    )


def _supported_scalar(value: object) -> bool:
    return value is None or type(value) in {str, int, bool}


def _record_valid(record: object) -> bool:
    if type(record) is not MaterializedSourceRecord:
        return False

    if not all(
        _valid_exact_text(value)
        for value in (record.task_id, record.scope_id, record.capture_marker)
    ):
        return False

    if type(record.fields) is not tuple or not record.fields:
        return False

    field_ids: list[str] = []
    for field in record.fields:
        if type(field) is not SourceFieldValue:
            return False
        if not _valid_exact_text(field.field_id):
            return False
        if not _supported_scalar(field.value):
            return False
        field_ids.append(field.field_id)

    return len(set(field_ids)) == len(field_ids)


def _field_map(record: MaterializedSourceRecord) -> dict[str, object]:
    return {
        field.field_id: field.value
        for field in record.fields
    }


def evaluate_source_readback(
    request: SourceReadbackRequest,
) -> SourceReadbackResult:
    """Return PASS only for exact expected/read-back parity and binding."""

    reasons: set[str] = set()

    if type(request) is not SourceReadbackRequest:
        return SourceReadbackResult(
            status="HOLD",
            readback_match=False,
            blocking_reasons=("EXPECTED_RECORD_INVALID",),
        )

    if request.contract_id != CONTRACT_ID:
        reasons.add("CONTRACT_INVALID")

    expected_valid = _record_valid(request.expected_record)
    if not expected_valid:
        reasons.add("EXPECTED_RECORD_INVALID")

    readback_missing = request.readback_record is None
    if readback_missing:
        reasons.add("READBACK_MISSING")
        readback_valid = False
    else:
        readback_valid = _record_valid(request.readback_record)
        if not readback_valid:
            reasons.add("READBACK_RECORD_INVALID")

    if expected_valid and readback_valid:
        expected = request.expected_record
        readback = request.readback_record

        if (
            expected.task_id != readback.task_id
            or expected.scope_id != readback.scope_id
            or expected.capture_marker != readback.capture_marker
        ):
            reasons.add("BINDING_MISMATCH")

        expected_fields = _field_map(expected)
        readback_fields = _field_map(readback)

        if set(expected_fields) != set(readback_fields):
            reasons.add("FIELD_SET_MISMATCH")
        else:
            for field_id in sorted(expected_fields):
                expected_value = expected_fields[field_id]
                readback_value = readback_fields[field_id]
                if type(expected_value) is not type(readback_value):
                    reasons.add("TYPE_MISMATCH")
                elif expected_value != readback_value:
                    reasons.add("VALUE_MISMATCH")

    if not reasons:
        return SourceReadbackResult(
            status="PASS",
            readback_match=True,
            blocking_reasons=(),
        )

    return SourceReadbackResult(
        status="HOLD",
        readback_match=False,
        blocking_reasons=tuple(sorted(reasons)),
    )
