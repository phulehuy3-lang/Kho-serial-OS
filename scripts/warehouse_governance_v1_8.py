"""Pure, synthetic-safe warehouse governance gates. No provider or write access."""

import hashlib
import json

from scripts.source_readback_v0_1 import SourceReadbackRequest, evaluate_source_readback


class GateError(ValueError):
    """A warehouse governance gate failed closed."""


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_inbound_touch_set(cells, *, sheet="BUSINESS") -> bool:
    """A generic inbound operation may touch only A, C, D, O on its business row."""
    if not cells or any(s != sheet or col not in {"A", "C", "D", "O"} for s, col in cells):
        raise GateError("BLOCK_SCOPE")
    if len(cells) != len(set(cells)):
        raise GateError("DUPLICATE_CELL")
    return True


PROTECTED = ("B", "G", "H", "I", "J", "K", "L", "M", "N")


def validate_formula_snapshot(before, after, expected_hash) -> bool:
    """Bind exact formula source strings, not their displayed/cached values."""
    if any(not isinstance(before.get(c), str) or not before[c].startswith("=") for c in PROTECTED):
        raise GateError("MISSING_PREWRITE_FORMULA")
    if _digest(before) != expected_hash:
        raise GateError("STALE_PREWRITE_FORMULA_HASH")
    if any(not isinstance(after.get(c), str) or not after[c].startswith("=") for c in PROTECTED):
        raise GateError("MISSING_POSTWRITE_FORMULA")
    if _digest(after) != expected_hash:
        raise GateError("FORMULA_HASH_MISMATCH")
    return True


def formula_hash(formulas) -> str:
    return _digest(formulas)


PHASES = ("PREPARED", "PREWRITE_SEALED", "WRITTEN", "READBACK_PASS", "CLOSED")


def _validate_transaction_readback(evidence, binding) -> None:
    """Validate materialized capture against the caller's sealed transaction binding."""
    if type(evidence) is not dict or type(binding) is not dict:
        raise GateError("MISSING_READBACK_EVIDENCE")
    required = ("task_id", "scope_id", "payload_hash", "readback_capture_marker", "written_capture_marker")
    if any(type(binding.get(k)) is not str or not binding[k] or binding[k] != binding[k].strip()
           for k in required):
        raise GateError("INVALID_READBACK_BINDING")
    if (type(evidence.get("evidence_id")) is not str or not evidence["evidence_id"].strip()
            or evidence.get("capture_kind") != "INDEPENDENT_READBACK"):
        raise GateError("INVALID_READBACK_PROVENANCE")
    request = evidence.get("request")
    if type(request) is not SourceReadbackRequest or evaluate_source_readback(request).status != "PASS":
        raise GateError("READBACK_EVIDENCE_NOT_PASS")
    record = request.readback_record
    fields = {field.field_id: field.value for field in record.fields}
    if (record.task_id != binding["task_id"] or record.scope_id != binding["scope_id"]
            or record.capture_marker != binding["readback_capture_marker"]
            or record.capture_marker == binding["written_capture_marker"]
            or type(fields.get("payload_hash")) is not str
            or fields["payload_hash"] != binding["payload_hash"]):
        raise GateError("READBACK_TRANSACTION_BINDING_MISMATCH")


def validate_transition(previous, following, *, manifest_readback=False, reconciliation=False, audit=False,
                        readback_evidence=None, transaction_binding=None) -> bool:
    if previous not in PHASES or following not in PHASES or PHASES.index(following) != PHASES.index(previous) + 1:
        raise GateError("INVALID_STATE_TRANSITION")
    if any(type(value) is not bool for value in (manifest_readback, reconciliation, audit)):
        raise GateError("GATE_BOOLEAN_INVALID")
    if following == "PREWRITE_SEALED" and manifest_readback is not True:
        raise GateError("MISSING_PREWRITE_MANIFEST")
    if following in {"READBACK_PASS", "CLOSED"}:
        _validate_transaction_readback(readback_evidence, transaction_binding)
    if following == "CLOSED" and not (reconciliation is True and audit is True):
        raise GateError("MISSING_CLOSE_EVIDENCE")
    return True


def validate_correction(parent_state, parent_task_id) -> bool:
    if parent_state != "CLOSED" or not parent_task_id:
        raise GateError("POST_CLOSE_REQUIRES_CHILD_PARENT_TASK_ID")
    return True


IDENTITY_FIELDS = ("direction", "partner", "document_no", "document_date", "order", "payload_hash")


def composite_identity(document) -> str:
    if any(not isinstance(document.get(k), str) or not document[k] for k in IDENTITY_FIELDS):
        raise GateError("INCOMPLETE_DOCUMENT_IDENTITY")
    return _digest({k: document[k] for k in IDENTITY_FIELDS})


def duplicate_decision(existing, candidate) -> bool:
    key = composite_identity(candidate)
    if key in {composite_identity(item) for item in existing}:
        raise GateError("TRUE_DUPLICATE_COMPOSITE_IDENTITY")
    return True


SERIAL_MAX_DIGITS = 4096


def _serial_text(value) -> bool:
    """Match the canonical ASCII serial-text bound without coercion."""
    return (
        type(value) is str
        and 0 < len(value) <= SERIAL_MAX_DIGITS
        and all("0" <= char <= "9" for char in value)
    )


def _serial_increment(value: str) -> str:
    digits = list(value)
    for index in range(len(digits) - 1, -1, -1):
        if digits[index] != "9":
            digits[index] = chr(ord(digits[index]) + 1)
            return "".join(digits)
        digits[index] = "0"
    raise GateError("SERIAL_WIDTH_OVERFLOW")


def _serial_decrement(value: str) -> str:
    digits = list(value)
    for index in range(len(digits) - 1, -1, -1):
        if digits[index] != "0":
            digits[index] = chr(ord(digits[index]) - 1)
            return "".join(digits)
        digits[index] = "9"
    raise GateError("SERIAL_WIDTH_UNDERFLOW")


def _inclusive_quantity(start: str, end: str) -> int:
    """Subtract equal-width decimal text, converting only the difference to a count."""
    borrow = 0
    difference = []
    for left, right in zip(reversed(start), reversed(end)):
        digit = ord(right) - ord(left) - borrow
        borrow = digit < 0
        difference.append(digit + 10 if borrow else digit)
    if borrow:
        raise GateError("INVALID_INTERVAL")
    quantity = 0
    for digit in reversed(difference):
        quantity = quantity * 10 + digit
    return quantity + 1


def exact_middle_split(source_start, source_end, physical_start, physical_end) -> dict:
    vals = (source_start, source_end, physical_start, physical_end)
    if any(not _serial_text(value) for value in vals) or len({len(value) for value in vals}) != 1:
        raise GateError("SERIAL_IDENTITY_INVALID")
    # Equal-width ASCII text has the same lexical and numeric ordering.
    if not source_start <= physical_start <= physical_end <= source_end:
        raise GateError("PHYSICAL_RANGE_OUTSIDE_SOURCE")
    left_end = _serial_decrement(physical_start) if source_start < physical_start else None
    left = (source_start, left_end, _inclusive_quantity(source_start, left_end)) if left_end is not None else None
    out = (physical_start, physical_end,
           _inclusive_quantity(physical_start, physical_end))
    right_start = _serial_increment(physical_end) if physical_end < source_end else None
    right = (right_start, source_end, _inclusive_quantity(right_start, source_end)) if right_start is not None else None
    source_quantity = _inclusive_quantity(source_start, source_end)
    if sum(part[2] for part in (left, out, right) if part) != source_quantity:
        raise GateError("CONSERVATION_FAILURE")
    return {"left": left, "out": out, "right": right, "source_quantity": source_quantity}


def validate_postfacto_physical(*, signed_range, booked_range, unique_source, sufficient_stock,
                               hold_clear, no_prior_out, owner_confirmed, reranked=False) -> bool:
    if (signed_range != booked_range or reranked is not False
            or any(value is not True for value in (unique_source, sufficient_stock,
                                                  hold_clear, no_prior_out, owner_confirmed))):
        raise GateError("POSTFACTO_EXACT_PHYSICAL_GATE")
    return True


SESSION_GATES = ("terminal_coverage", "no_orphan_child", "unique_transaction_keys",
                 "no_active_reservation", "no_unresolved_hold", "reconciliation_ok",
                 "no_sold_serial_eligible", "formula_hash_ok", "evidence_ok",
                 "unique_audit_recon_ids", "movement_arithmetic_ok")


def classify_global_session(gates, *, repaired_historical_defects=False) -> str:
    if type(repaired_historical_defects) is not bool or any(gates.get(k) is not True for k in SESSION_GATES):
        return "BLOCKED_SAFE"
    return "REMEDIATED_PASS" if repaired_historical_defects else "CLEAN_PASS"
