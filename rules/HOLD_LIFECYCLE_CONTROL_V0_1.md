# HOLD_LIFECYCLE_CONTROL_V0_1

Status: **PUBLIC BASELINE — READ-ONLY / NO MUTATION AUTHORITY**

## Purpose

Define a fail-closed, side-effect-free HOLD lifecycle for interval-scoped
records:

```text
VALIDATE / ISOLATE
      ↓
RELEASE READINESS
      ↓
TRANSITION-INTENT GUARD
      ↓
[external controlled transition, outside this repository]
      ↓
POST-TRANSITION READ-BACK
```

This control validates state only. It does not create, release, delete, reorder,
reserve, or mutate inventory/HOLD records.

## 1. Record and isolation validation

A valid HOLD record requires:

- non-empty HOLD, scope, target, type, evidence, reason, and creation fields;
- native boolean HOLD flags;
- a known lifecycle status;
- `ACTIVE => hold_flag=True`;
- `RELEASED => hold_flag=False`;
- for interval scope, numeric ordered range bounds;
- target/category parity between registry-style record and interval state;
- interval HOLD flag parity with the lifecycle state.

Unknown or contradictory state returns `HOLD`.

## 2. Release-readiness gates

For interval scope, business gates are evaluated in mandatory order:

```text
EVIDENCE
  ↓
EXACT_SOURCE_DATE
  ↓
ACTIVE_OVERLAP
  ↓
STOCK_YEAR
```

The first failed gate determines the canonical release-readiness decision.

Required PASS conditions:

- evidence status is `VERIFIED_INDEPENDENT`;
- source date is exactly `DD/MM/YYYY`;
- parsed source year equals the supplied source year;
- no blocking same-category overlapping interval HOLD exists;
- available quantity is a positive non-boolean integer;
- source-year status is `YEAR_VERIFIED`;
- target remains `ACTIVE` with native `True` HOLD state.

A PASS result is readiness only. It is not mutation authority.

## 3. Fail-closed overlap semantics

For a same-category interval peer:

- a proven non-overlap is ignored;
- an overlapping `ACTIVE` peer blocks;
- an overlapping peer with unknown status blocks;
- an overlapping peer with malformed HOLD flag blocks;
- an overlapping non-active peer with `hold_flag=True` blocks;
- invalid range identity blocks because non-overlap cannot be proven;
- only a known non-active peer with native `False` HOLD state can be ignored.

## 4. Transition-intent guard

A transition intent may return `PASS_TRANSITION_INTENT` only when:

- target release decision is `PASS_RELEASE_READY`;
- transaction gate independently says `PASS_RELEASE_READY`;
- approval status is `APPROVED`;
- expected/actual payload hashes are non-empty and equal;
- external execution readiness is explicitly `True`;
- last safe state is `GATE_EVALUATED`.

The evaluator does not execute a transition.

## 5. Post-transition read-back

A released interval is considered read-back complete only when all required
state/view checks are known and consistent, including:

- registry HOLD flag is `False`;
- registry status is `RELEASED`;
- interval HOLD flag is `False`;
- target is absent from quarantine;
- target is present in eligible view;
- lookup no longer reports HOLD;
- ranking can see the target when otherwise eligible;
- inventory total is unchanged;
- rollback proof passes.

Missing or contradictory read-back evidence returns `HOLD`.

## 6. Public boundary

All examples and tests use synthetic short identifiers and ranges. This
baseline contains no live HOLD snapshot, external-system identifier, private
registry name, operational count, credential, production adapter, or write
path.
