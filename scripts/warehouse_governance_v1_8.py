"""Pure, synthetic-safe warehouse governance gates. No provider or write access."""

import hashlib
import json


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


def validate_transition(previous, following, *, manifest_readback=False, reconciliation=False, audit=False) -> bool:
    if previous not in PHASES or following not in PHASES or PHASES.index(following) != PHASES.index(previous) + 1:
        raise GateError("INVALID_STATE_TRANSITION")
    if following == "PREWRITE_SEALED" and not manifest_readback:
        raise GateError("MISSING_PREWRITE_MANIFEST")
    if following == "CLOSED" and not (reconciliation and audit):
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


def exact_middle_split(source_start, source_end, physical_start, physical_end) -> dict:
    vals = (source_start, source_end, physical_start, physical_end)
    if any(not isinstance(x, str) or not x.isdecimal() for x in vals) or len({len(x) for x in vals}) != 1:
        raise GateError("SERIAL_IDENTITY_INVALID")
    s, e, p, q = map(int, vals)
    if not s <= p <= q <= e:
        raise GateError("PHYSICAL_RANGE_OUTSIDE_SOURCE")
    width = len(source_start)
    fmt = lambda a, b: (str(a).zfill(width), str(b).zfill(width), b - a + 1) if a <= b else None
    left, out, right = fmt(s, p - 1), fmt(p, q), fmt(q + 1, e)
    if sum(part[2] for part in (left, out, right) if part) != e - s + 1:
        raise GateError("CONSERVATION_FAILURE")
    return {"left": left, "out": out, "right": right, "source_quantity": e - s + 1}


def validate_postfacto_physical(*, signed_range, booked_range, unique_source, sufficient_stock,
                               hold_clear, no_prior_out, owner_confirmed, reranked=False) -> bool:
    if (signed_range != booked_range or reranked or not all((unique_source, sufficient_stock,
            hold_clear, no_prior_out, owner_confirmed))):
        raise GateError("POSTFACTO_EXACT_PHYSICAL_GATE")
    return True


SESSION_GATES = ("terminal_coverage", "no_orphan_child", "unique_transaction_keys",
                 "no_active_reservation", "no_unresolved_hold", "reconciliation_ok",
                 "no_sold_serial_eligible", "formula_hash_ok", "evidence_ok",
                 "unique_audit_recon_ids", "movement_arithmetic_ok")


def classify_global_session(gates, *, repaired_historical_defects=False) -> str:
    if any(gates.get(k) is not True for k in SESSION_GATES):
        return "BLOCKED_SAFE"
    return "REMEDIATED_PASS" if repaired_historical_defects else "CLEAN_PASS"
