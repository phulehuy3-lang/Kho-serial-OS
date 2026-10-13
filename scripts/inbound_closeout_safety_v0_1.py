"""Fail-closed, synthetic-only verifier for existing inbound G9/G10/G15/G18.

Pure Python; never connects to Google Sheets, never authorizes Production writes.
The schema and proof data must be supplied by the caller from verified sources.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


@dataclass(frozen=True)
class Verdict:
    status: str
    reasons: tuple[str, ...]


def validate_closeout(evidence: Mapping[str, Any]) -> Verdict:
    """Require authoritative enum, independent provider receipts and truthful gate closure.

    Expected keys: canonical_states, transaction, manifest, provider, source,
    reconciliation, approval. All samples in tests are synthetic.
    """
    issues: set[str] = set()
    if not isinstance(evidence, Mapping):
        return Verdict("HOLD", ("INVALID_INPUT",))

    states = evidence.get("canonical_states")
    tx = evidence.get("transaction")
    manifest = evidence.get("manifest")
    provider = evidence.get("provider")
    source = evidence.get("source")
    recon = evidence.get("reconciliation")
    approval = evidence.get("approval")

    if not isinstance(states, (list, tuple, set)) or not states or not all(isinstance(s, str) for s in states):
        issues.add("CANONICAL_STATE_SCHEMA_MISSING")
        states = ()
    if not isinstance(tx, Mapping):
        tx = {}
        issues.add("TRANSACTION_MISSING")
    if tx.get("state") not in states:
        issues.add("STATE_NOT_IN_CANONICAL_ENUM")
    if tx.get("state") != "CLOSED" or tx.get("readback_status") != "PASS":
        issues.add("TERMINAL_CLOSURE_NOT_PROVEN")
    if not isinstance(tx.get("task_id"), str) or not tx.get("task_id"):
        issues.add("TRANSACTION_ID_INVALID")

    if approval is not True:
        issues.add("APPROVAL_MISSING")
    if not isinstance(source, Mapping):
        source = {}
        issues.add("SOURCE_EVIDENCE_MISSING")
    if not isinstance(manifest, Mapping):
        manifest = {}
        issues.add("G8_MANIFEST_MISSING")
    if not isinstance(provider, Mapping):
        provider = {}
        issues.add("PROVIDER_PROOF_MISSING")
    if not isinstance(recon, Mapping):
        recon = {}
        issues.add("RECONCILIATION_PROOF_MISSING")

    task_id = tx.get("task_id")
    if manifest.get("task_id") != task_id or source.get("task_id") != task_id or provider.get("task_id") != task_id:
        issues.add("TASK_BINDING_MISMATCH")
    if manifest.get("sealed_before_write") is not True:
        issues.add("G8_NOT_SEALED_BEFORE_WRITE")
    if source.get("originals_verified") is not True:
        issues.add("ORIGINAL_EVIDENCE_UNVERIFIED")
    if provider.get("transport") not in ("GOOGLE_SHEETS_NATIVE", "APPROVED_NATIVE_WRITER"):
        issues.add("PROVIDER_TRANSPORT_UNVERIFIED")
    if not provider.get("request_receipt") or not provider.get("response_receipt"):
        issues.add("PROVIDER_REQUEST_RESPONSE_MISSING")
    if provider.get("prewrite_admission_pass") is not True:
        issues.add("G9_ADMISSION_NOT_ATTESTED")
    planned = manifest.get("touch_set")
    touched = provider.get("touch_set")
    def canonical_touch_set(items: object, reason: str) -> frozenset[str] | None:
        if (type(items) not in (list, tuple) or not items
                or any(type(item) is not str or not item.strip() or item.strip() != item for item in items)):
            issues.add(reason)
            return None
        unique = frozenset(items)
        if len(unique) != len(items):
            issues.add(reason)
            return None
        return unique

    planned_exact = canonical_touch_set(planned, "G8_TOUCH_SET_INVALID")
    actual_exact = canonical_touch_set(touched, "ACTUAL_TOUCH_SET_MISSING_OR_DUPLICATE")
    if planned_exact is not None and actual_exact is not None and planned_exact != actual_exact:
        issues.add("ACTUAL_TOUCH_SET_MISMATCH")
    if provider.get("native_afterimage_verified") is not True:
        issues.add("NATIVE_AFTERIMAGE_MISSING")
    if provider.get("provider_error") is not False or provider.get("unknown_ack") is not False:
        issues.add("UNKNOWN_COMMIT_STATE_NO_REPLAY")

    quantities = source.get("quantities")
    if (not isinstance(quantities, (list, tuple)) or not quantities or
            any(type(n) is not int or n < 1 for n in quantities) or
            sum(quantities) != tx.get("total_quantity") or
            len(quantities) != tx.get("interval_count")):
        issues.add("SOURCE_LEDGER_STATE_QUANTITY_MISMATCH")
    if type(tx.get("total_quantity")) is not int or type(tx.get("interval_count")) is not int:
        issues.add("TRANSACTION_QUANTITY_SCHEMA_INVALID")
    if type(source.get("duplicate_transaction_count")) is not int or source.get("duplicate_transaction_count") != 1:
        issues.add("IDEMPOTENCY_NOT_UNIQUE")
    if type(source.get("hold_overlap_count")) is not int or source.get("hold_overlap_count") != 0:
        issues.add("ACTIVE_HOLD_OR_OVERLAP")

    if recon.get("native_recheck") is not True:
        issues.add("G10_G18_NATIVE_RECHECK_MISSING")
    if recon.get("all_checks_pass") is not True:
        issues.add("RECONCILIATION_HAS_HOLD")
    # The dependency graph must be complete, acyclic, and independently provider-bound.
    records = recon.get("records")
    if type(records) not in (list, tuple) or not records:
        issues.add("RECON_RECORDS_MISSING")
    else:
        edges: dict[str, tuple[str, ...]] = {}
        for record in records:
            if not isinstance(record, Mapping):
                issues.add("RECON_STRUCTURAL_INVALID")
                continue
            key = record.get("id")
            dependencies = record.get("depends_on")
            if (type(key) is not str or not key.strip() or key != key.strip()
                    or type(dependencies) not in (list, tuple)
                    or any(type(dep) is not str or not dep.strip() for dep in dependencies)
                    or len(set(dependencies)) != len(dependencies)):
                issues.add("RECON_STRUCTURAL_INVALID")
                continue
            if key in edges:
                issues.add("RECON_DUPLICATE_ID")
            edges[key] = tuple(dependencies)
            if record.get("provider_readback") is not True:
                issues.add("RECON_WITHOUT_PROVIDER_READBACK")
        for key, dependencies in edges.items():
            if any(dep not in edges for dep in dependencies):
                issues.add("RECON_DEPENDENCY_MISSING")
        colors: dict[str, int] = {}

        def visit(node: str) -> None:
            if colors.get(node) == 1:
                issues.add("CIRCULAR_RECONCILIATION")
                return
            if colors.get(node) == 2:
                return
            colors[node] = 1
            for dependency in edges[node]:
                if dependency in edges:
                    visit(dependency)
            colors[node] = 2

        for key in edges:
            visit(key)

    return Verdict("PASS" if not issues else "HOLD", tuple(sorted(issues)))