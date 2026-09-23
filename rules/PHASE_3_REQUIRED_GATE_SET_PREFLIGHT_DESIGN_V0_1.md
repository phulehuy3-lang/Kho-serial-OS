# Phase 3 Required Gate Set Preflight — Design v0.1

Status: **DESIGN SELECTED; IMPLEMENTATION TRACKED SEPARATELY**

Inputs: `PHASE_3_PUBLIC_SCOPE_GATE_V0_1` and
`PHASE_3_EVIDENCE_COMPLETENESS_DESIGN_REVIEW_V0_1`.
The released `v0.2.0` twelve-control baseline remains unchanged.

## Decision and rejected alternative

Select a **separate, pure in-memory preflight** as the candidate Control 13.
Its sole new invariant is exact coverage and context binding of an explicitly
declared required gate set before passing a map to Control 07.

Do not extend Control 07 v0.1 in place: changing its required signature breaks
callers, while an optional parameter leaves the original omission path open.
Control 07 remains the boolean/unknown and HOLD-conflict aggregator. A caller
that opts into this new composition must feed Control 07 only the validated
output of the preflight. This public contract cannot force arbitrary external
callers to opt in.

No hash/envelope authenticity scheme is needed for this proven gap. An opaque
digest would not establish source authority or independent provenance and
would add an unverified promise. Source authenticity, gate applicability, and
live snapshot freshness remain upstream responsibilities.

## Versioned input schema

Contract identity: `REQUIRED_GATE_SET_PREFLIGHT_V1`.

`RequiredGateScenario` (immutable):
- `contract_id`: exact version identity above;
- `scenario_id`, `task_id`, `scope_id`: non-empty exact text;
- `required_gate_ids`: non-empty tuple of unique, non-blank exact text;
- `expected_capture_marker`: non-empty exact text supplied by the caller.

`MaterializedGateEvidence` (immutable record):
- `gate_id`, `scenario_id`, `task_id`, `scope_id`,
  `capture_marker`: non-empty exact text;
- `value`: native `True`, native `False`, or `None` only.

Input `evidence` is an ordered tuple of records, not a mapping, so duplicate
gate IDs remain detectable. Identifiers are compared exactly, with no case
folding or whitespace rewriting; leading/trailing whitespace or blank
identifiers are invalid. A capture marker is an equality binding only, not a
timestamp, proof of atomicity, or independent freshness evidence. The caller
must supply an authoritative required set and expected marker; this preflight
cannot discover them.

## Output and composition

`GateSetPreflightResult`:
- `status`: `PASS` or `HOLD`;
- `ready`: native boolean;
- `blocking_reasons`: deterministic sorted tuple of reason codes;
- `validated_gate_map`: complete mapping from declared gate IDs to their
  native boolean/unknown values **only when structurally PASS**; otherwise
  absent.

PASS asserts exact set equality and context/marker binding, not that every
gate passed. Therefore `False` and `None` values can be structurally valid
and must reach Control 07, which then returns HOLD. The preflight never
accepts `hold_conflict` or decides release. Composition order:

```text
caller-declared required set + materialized evidence
    -> exact-set/context preflight PASS
    -> validated native map + separate hold_conflict
    -> Control 07 READY_FOR_RELEASE or HOLD
```

If preflight HOLD, do not call Control 07 as if a partial map were complete.
No result grants production write authority.

## Deterministic validation and adversarial tests

Validation must report malformed scenario/records as HOLD, never silently drop
them. Check unique exact IDs before set comparison. Reason codes must
distinguish `SCENARIO_INVALID`, `EVIDENCE_MISSING`, `EVIDENCE_EXTRA`,
`EVIDENCE_DUPLICATE`, `BINDING_MISMATCH`, `MARKER_MISMATCH`, and
`VALUE_INVALID`. Multiple independent blockers are returned in sorted order.
Empty evidence is missing evidence. No free-form status string is a boolean.

| Synthetic fixture | Preflight | Control 07 after PASS |
| --- | --- | --- |
| Required A,B; matching A=True,B=True | PASS, exact A/B map | READY only if hold_conflict=False |
| Required A,B; only A=True | HOLD / EVIDENCE_MISSING | Must not be called |
| Required A,B; A=True,B=True,C=True | HOLD / EVIDENCE_EXTRA | Must not be called |
| Required A,B; A duplicated | HOLD / EVIDENCE_DUPLICATE | Must not be called |
| Evidence B from another task, scope or scenario | HOLD / BINDING_MISMATCH | Must not be called |
| Evidence B has another capture marker | HOLD / MARKER_MISMATCH | Must not be called |
| B="PASS" or B=1 | HOLD / VALUE_INVALID | Must not be called |
| Required A,B; A=True,B=False | PASS, exact A/B map | HOLD / B:FAIL |
| Required A,B; A=True,B=None | PASS, exact A/B map | HOLD / B:UNKNOWN |
| Matching evidence, hold_conflict=None | PASS | HOLD / hold_conflict:UNKNOWN |
| Blank/duplicate required ID or unknown contract ID | HOLD / SCENARIO_INVALID | Must not be called |
| Same records in another order | Same decision and sorted output | Same aggregation |
| Caller omits a truly required business gate from the scenario | Cannot detect | Upstream authority HOLD; no global completeness claim |

The implementation PR should include a direct regression for the exact
previously demonstrated omission: the bare Control 07 call may return READY,
but the new preflight must HOLD on the missing declared gate. Preserve
Control 07's existing tests and v0.1 behavior.

## Capability and review gates

Candidate code is one small side-effect-free module plus focused synthetic
tests and a catalog update **only after implementation is verified**. It must
not import business control implementations, copy private code/history, read
files or network, access credentials, discover targets, or write anything.
No production adapter, workbook/Drive/Sheets connector, live serial, invoice,
resource identifier, or MASTER LIVE mutation is in scope.

Before implementation merge, review exact diff, non-personal commit metadata,
adversarial results, `unit-tests` and `trusted-public-boundary` logs, and
post-merge push checks. A control number in this design alone is a selected
candidate, not evidence that implementation passed CI or a release was tagged.
