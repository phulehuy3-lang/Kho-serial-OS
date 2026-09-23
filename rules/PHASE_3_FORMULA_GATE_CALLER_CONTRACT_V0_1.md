# Phase 3 formula-gate caller contract — review candidate v0.1

Status: **SCOPED ENGINEERING PROPOSAL — NO OPERATIONAL AUTHORITY**

## Decision scope and source

This candidate covers only an already-materialized, synthetic formula-gate
preview. The public control catalog's Control 12 dependency policy requires
independent Control 06 formula presence/error health and Control 12 formula
semantic identity results when both are applicable. That published rule is the
source of this *two-gate engineering scope*. It does not select all gates
required for a warehouse transaction, artifact release, or production action.

A maintainer may review the public engineering contract through the protected
main PR and required CI. A separate, identified operational decision owner
must approve any business scenario and its complete applicable gate set before
a live caller can exist. This document records no such approval.

## Exact proposed caller contract

Contract identity: `FORMULA_GATE_PREVIEW_V1`.
Scenario: `SYNTHETIC_FORMULA_PAIR`.
Required gate IDs, exactly:
- `formula_health`: native boolean/unknown result from Control 06; detects
  presence and error health only;
- `formula_semantics`: native boolean/unknown result from Control 12; detects
  semantic identity only.

The caller receives an explicit task ID, scope ID, and expected capture marker
from its synthetic fixture. It must build a
`REQUIRED_GATE_SET_PREFLIGHT_V1` scenario with exactly these two IDs and pass
an ordered tuple of separately materialized, scenario/task/scope/marker-bound
gate records to Control 13. It must pass only the preflight's validated map
to Control 07, together with a separate native `hold_conflict` input. If the
preflight returns HOLD, the caller returns HOLD without invoking Control 07.
A structurally complete `False` or `None` gate reaches Control 07 and
returns HOLD. Unknown HOLD conflict also returns HOLD.

| Evidence case | Control 13 | Control 07 / preview |
| --- | --- | --- |
| Both matching native True, hold_conflict=False | PASS | READY within synthetic preview only |
| One gate absent, duplicated, extra or mismatched binding | HOLD | Not invoked; HOLD |
| Either gate False or None | PASS | HOLD |
| Both True, hold_conflict=None or True | PASS | HOLD |

No derived boolean may substitute for the other gate. The capture marker
proves exact equality within the supplied records, not a fresh, atomic, or
authenticated live snapshot. The preview's READY is an engineering result,
not production release readiness, source-of-truth correctness, or write
authorization.

## Evidence and authority gate before implementation

1. Verify the two-gate rule against the canonical catalog and keep Controls
   06, 12, 13 and 07 individually unchanged.
2. Obtain maintainer review of the exact preview scope and mapping through
   a protected-main PR. This review authorizes only synthetic public code.
3. Implement a small pure caller and adversarial tests for all table rows,
   with no filesystem, network, workbook, provider, target or writer capability.
4. Read both `unit-tests` and trusted-boundary V1/V2 logs at the exact PR
   head; squash merge and read back post-merge workflows and ruleset.
5. Keep operational integration HOLD until an identified business authority
   provides and independently reviews the complete scenario-specific gate
   universe, provenance, freshness requirements and separate HOLD-conflict
   source. Version that decision before attaching any operational caller.

This proposal does not touch private Phu_OS, MASTER LIVE, production adapters,
real records or the frozen Phase 2 v0.2.0 tag.
