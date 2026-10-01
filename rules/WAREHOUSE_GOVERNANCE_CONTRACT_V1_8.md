# Warehouse governance contract v1.8 — public specification

This is a sanitized, pure engineering mirror of the inbound hardening rules. It does not carry operational authority, live adapter access or write permission. Existing public Phase 2 and Phase 3 control numbering is unchanged; these are named gate profiles composed with current controls.

| Operational contract ID | Public invariant |
| --- | --- |
| `SOP_INBOUND_STANDARD_V1_8` | Evidence and provenance, composite identity, full-history overlap/HOLD, source vs derived, exact cell allowlist, sealed prewrite, formula hash, state path, independent read-back and reconciliation precede close. Generic inbound business cells: A,C,D,O only. |
| `CTRL_CELL_LEVEL_WRITER_ENFORCEMENT_V1` | Expand proposed writes to individual cells; reject an A:O rectangle, including blank values in protected cells. This repository supplies only a pure validator. |
| `CTRL_PROTECTED_FORMULA_HASH_V1` | Compare exact formula strings for B and G:N before and after a write; missing formula or changed code fails even if a displayed value looks right. |
| `CTRL_TRANSACTION_STATE_MACHINE_V1` | PREPARED → PREWRITE_SEALED → WRITTEN → READBACK_PASS → CLOSED, with evidence at each transition; no direct close, terminal reopen or post-close parent rewrite. A correction requires a linked child. |
| `CTRL_DOCUMENT_COMPOSITE_IDENTITY_V1` | Direction, partner identity or explicit unresolved-role token, document number, date, order/batch discriminator and payload hash identify a document. The same nominal number with distinct order/payload is not by itself a duplicate. Same complete composite blocks replay. |
| `CTRL_GLOBAL_SESSION_CLOSE_V1` | Check all terminal transactions, orphan children, duplicate keys, active reservations, unresolved HOLD, recon, sold serial eligibility, formula drift, evidence, audit IDs and movement arithmetic. All clear and no defect = CLEAN_PASS; repaired immutable defect = REMEDIATED_PASS; unresolved gate = BLOCKED_SAFE. |
| `CTRL_POSTFACTO_PHYSICAL_DELIVERY_V1_1` | An already delivered signed serial range may be reconciled only to that exact range after source/stock/HOLD/overlap/owner gates. Keep a prior source-rank denial for audit and do not re-rank the historical physical delivery. Count parent and child physical quantity once. |
| `CTRL_EXACT_SERIAL_SPLIT_V2` | Four endpoints must be native non-empty strings of equal width, ASCII digits `0`–`9` only, at most 4096 digits each. Reject bool, other types, Unicode decimal, overlong, reversed or out-of-source ranges without coercion. Preserve original width and leading zeros; compare and increment/decrement as decimal text, without converting a full serial string to Python `int`. For source [S,E] and physical [P1,P2], left [S,P1−1] + out [P1,P2] + right [P2+1,E] conserves exact quantity and serial union without overlap or gap. Sold serial remaining eligible or formula drift blocks close. |

The predecessor inbound v1.7 and post-facto v1.0 are superseded prospectively in the operational authority. No historical record is erased. This public repository is a generic validation mirror; a passing unit test never proves the live inventory or evidence state.

## Synthetic tests

`scripts/warehouse_governance_v1_8.py` and `tests/test_warehouse_governance_v1_8.py` exercise the pure invariants with invented intervals and document labels. They neither connect to a provider nor mutate inventory.

## PHU-8 transition evidence caller contract

Native booleans are required for transition and postfacto inputs. Text booleans,
integers and unknown values are rejected without coercion. The repaired-history
classification flag is also a native boolean.

Both WRITTEN -> READBACK_PASS and READBACK_PASS -> CLOSED require:
- a materialized SourceReadbackRequest passing SOURCE_READBACK_V1 exact field,
  type, value and binding checks;
- a nonempty evidence ID and INDEPENDENT_READBACK capture kind;
- the caller's sealed transaction_binding containing task_id, scope_id,
  payload_hash, readback_capture_marker and written_capture_marker;
- readback task/scope/payload matching that sealed binding, and an expected
  readback capture marker distinct from the written capture marker.
CLOSED additionally requires native True reconciliation and audit inputs.

The caller must obtain the sealed binding and evidence from the canonical
accepted source, enforce capture ordering/freshness and independently acquired
provenance. These pure validators cannot authenticate caller assertions or prove
provider capture independence. No runtime integration or production readiness
is conferred by a synthetic PASS. Old callers missing evidence now fail closed.
