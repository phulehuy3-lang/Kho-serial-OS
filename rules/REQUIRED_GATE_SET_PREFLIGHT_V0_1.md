# REQUIRED_GATE_SET_PREFLIGHT_V0_1

Status: **PUBLIC PURE CONTROL — NO PRODUCTION AUTHORITY**

## Purpose

Check exact coverage and binding of an explicitly declared set of required
gates before handing a complete native boolean/unknown map to Control 07.

Control 07 intentionally validates only the map supplied by its caller. This
control catches omission, addition, or substitution of a gate record against a
caller-supplied scenario contract. It cannot decide which business gates the
caller should declare.

## Input and result

Contract identity: `REQUIRED_GATE_SET_PREFLIGHT_V1`.

`RequiredGateScenario` binds contract identity, scenario ID, task ID, scope ID,
unique required gate IDs, and an expected capture marker. Each
`MaterializedGateEvidence` record binds the same scenario/task/scope and marker
to one gate ID and native `True`, `False`, or `None` value.

Identifiers must be exact non-blank text with no surrounding whitespace.
Evidence is an ordered tuple so duplicate IDs can be detected. Valid records
may arrive in any order. A malformed, missing, extra, duplicate, mismatched or
non-native record returns HOLD and no validated map. Multiple blockers are
returned in sorted order.

A structurally valid map may contain `False` or `None`; these values are handed
unchanged to Control 07, which decides the corresponding FAIL/UNKNOWN HOLD.
The returned map is immutable. `hold_conflict` is a separate required input to
Control 07 and is never inferred by this preflight.

## Limits

The capture marker is an equality binding, not proof of a fresh or atomic live
read. Exact set coverage is relative to the supplied scenario, not the global
business policy. This control does not authenticate evidence, resolve caller
authority, connect to a service, read a workbook, or authorize a release or
write. A caller must explicitly opt into the preflight; legacy direct calls to
Control 07 retain their published behavior.

Only already-materialized synthetic in-memory records are used in public
tests. No private code/history, live target, credential, inventory record, or
production write path is included.
