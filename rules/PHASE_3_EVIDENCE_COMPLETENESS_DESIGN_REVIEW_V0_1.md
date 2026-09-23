# Phase 3 Evidence Completeness Design Review v0.1

Status: **GAP DEMONSTRATED; IMPLEMENTATION CANDIDATE HOLD**

Parent scope gate: `rules/PHASE_3_PUBLIC_SCOPE_GATE_V0_1.md`.
This is a design review, not a new public control or release. It changes no
existing control, catalog inventory, operational rule, or production authority.

## Reproducible failure mode

Control 07 intentionally aggregates only the caller's supplied applicable
gate map. Its contract does not define the required gate universe. In the
canonical public code, a non-empty map with all native `True` values and
`hold_conflict=False` returns `READY_FOR_RELEASE`.

Using the current public `evaluate_release_gates` implementation with
synthetic names:

```python
evaluate_release_gates({"formula_health": True}, False)
# ReleaseDecision(status='READY_FOR_RELEASE', ready=True, blocking_gates=())

evaluate_release_gates(
    {"formula_health": True, "formula_semantics": None}, False
)
# ReleaseDecision(status='HOLD', ready=False,
#                 blocking_gates=('formula_semantics:UNKNOWN',))
```

Assume a *caller-declared* scenario requiring both independent Control 06
health and Control 12 semantics. Omitting `formula_semantics` entirely permits
the first result, whereas including it as unknown correctly blocks. This does
not establish a production release vulnerability or a defect in Control 07:
the documented responsibility for deciding which gates apply belongs to its
caller. It demonstrates a distinct missing public invariant at the composition
boundary: **the provided evidence keys must exactly cover an independently
declared required set for the same task/scope before boolean aggregation**.

Controls 06 and 12 validate different properties; Control 07 validates each
provided value, not set completeness, task identity, provenance, or capture
coherence. Controls 02/08/09 have specific bindings within their own dry-run
chain and do not supply a generic required-gate contract to Control 07.

## Minimal proposed contract, still unselected

A pure in-memory preflight would accept:

- an explicit, versioned caller-supplied scenario contract containing non-empty
  `scenario_id`, `task_id`, `scope_id`, `contract_version`, and an ordered,
  unique set of required gate IDs;
- an already-materialized evidence record for each gate, containing exact gate
  ID, scenario/task/scope/version binding, a declared snapshot or capture
  marker, native boolean or unknown, and an opaque evidence digest with an
  explicit digest-contract identity;
- an expected snapshot/capture marker supplied by the caller.

It would reject missing or extra gates, duplicates, conflicting records,
mismatched task/scope/version/marker, malformed digest identity and non-native
boolean values. Missing evidence is UNKNOWN/HOLD; contradictory or mismatched
evidence is HOLD with distinct reasons. Only exact binding and complete
`True` evidence yields a validated boolean map for Control 07. An explicit
`hold_conflict` input remains separately required by Control 07; this preflight
does not infer or override it.

A digest is an integrity/binding token for a declared payload contract, not
proof of independent origin or authorization. A version marker binds supplied
records to an expected capture; it does not prove a live atomic read or
freshness relative to wall-clock time. Required-gate completeness is relative
only to the *caller-declared* scenario, not a global business-policy universe.
A dishonest or incomplete scenario contract cannot be repaired by this pure
control. Caller authority and applicability remain outside the public layer.

## Dependency and adversarial review

The implementation should be independent of business controls and accept
materialized plain values. It may hand a validated native boolean map to
Control 07, without importing or rewriting Control 07. The proposal requires
an independent validator path for canonical contract/evidence bindings if a
hash helper is introduced, with fixed golden vectors and mutation tests so the
same serializer mistake cannot both create and verify a record.

| Synthetic case | Required result |
| --- | --- |
| Two declared gates and two matching PASS records | Preflight PASS, followed by scoped Control 07 evaluation |
| Omit one required record | HOLD: missing evidence |
| Supply an undeclared record or duplicate gate ID | HOLD: exact set violation |
| Substitute a PASS record from another task or scope | HOLD: binding mismatch |
| Use another contract version or digest payload identity | HOLD: version/contract mismatch |
| Supply an old capture marker against a newer expected marker | HOLD: marker mismatch; no wall-clock freshness claim |
| Forge a string `"PASS"` instead of native `True` | HOLD: type mismatch |
| Change record content while retaining an old digest | HOLD: digest mismatch |
| Complete gate map with `hold_conflict=None` | Control 07 remains HOLD |
| Incomplete caller-declared scenario that omits a business-required gate | Outside pure proof; scenario authority remains HOLD upstream |

The outcome is deliberately narrower than a production release decision.
It does not establish that the caller chose every business-required gate,
that evidence came from an authorized live source, or that any operation
may mutate inventory.

## Selection decision and next gate

**Gap demonstrated in a synthetic composition, but Control 13 remains
unselected.** Before assigning a control number or writing implementation:

1. Review whether a small change to existing Control 07's explicit caller
   contract would be less complex than a new standalone preflight, while
   preserving its published v0.1 semantics and backward compatibility.
2. Fix the exact v1 schema and hash payload identity, including whether a hash
   is necessary; avoid accepting arbitrary digests as authenticity evidence.
3. Establish who supplies and independently reviews the required gate set in
   an operational integration. If that cannot be specified, leave HOLD.
4. Approve adversarial synthetic fixtures and a zero-I/O import/capability
   review before any implementation PR.

No credentials, connected resource identifiers, private code/history, live
data, external reads, writer, or MASTER LIVE change is authorized by this
review. The `v0.2.0` release tag remains immutable.
