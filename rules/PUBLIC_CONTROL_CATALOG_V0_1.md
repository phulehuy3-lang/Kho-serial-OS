# PUBLIC_CONTROL_CATALOG_V0_1

Status: **PUBLIC CONSOLIDATION BASELINE**

## Purpose

Define the public control inventory, responsibility boundaries, and allowed
dependencies after Phase 2 Controls 01–07.

This catalog is descriptive governance for the public repository. It does not
create production authority or a write path.

## Bootstrap controls

### NEAREST-PRIOR allocation ordering

Artifacts:

- `rules/ALLOCATION_NEAREST_PRIOR_V1_0.md`
- `scripts/allocation_nearest_prior.py`

Responsibility:

- eligible source date must not be after target date;
- deterministic ordering:
  `SOURCE_DATE_DESC | SOURCE_ROW_ASC | SERIAL_START_ASC`.

### SOURCE_OF_TRUTH / DERIVED_READ_ONLY boundary

Artifact:

- `rules/RULE_0099_SOURCE_OF_TRUTH_DERIVED_READ_ONLY.md`

Responsibility:

- only authoritative source regions are writable in an external implementation;
- derived/read-model regions are treated as read-only;
- release requires applicable source/read-model integrity controls to pass.

## Phase 2 controls

### Control 01 — CROSS_YEAR_AUTHORITY_V0_1

Validates structured authority for source years outside the document year.

Dependency policy: standalone.

### Control 02 — SOURCE_POOL_AUTHORITY_V0_1

Validates an exact authorized materialized source set and its task/business
bindings.

Dependency policy: standalone.

### Control 03 — HOLD_LIFECYCLE_CONTROL_V0_1

Validates HOLD isolation, ordered release-readiness gates, transition intent,
and post-transition read-back without mutation.

Dependency policy:

- may depend on `SERIAL_INTERVAL_INTEGRITY_V0_1` for canonical inclusive
  interval-overlap semantics;
- must not depend on a production adapter.

### Control 04 — SERIAL_INTERVAL_INTEGRITY_V0_1

Owns canonical inclusive interval construction, overlap semantics, and declared
quantity reconciliation.

Dependency policy: standalone primitive.

### Control 05 — NEGATIVE_STOCK_PREVENTION_V0_1

Owns strict non-negative quantity arithmetic for proposed issues.

Dependency policy: standalone primitive.

### Control 06 — RECONCILIATION_FORMULA_HEALTH_V0_1

Owns exact normalized source↔derived parity and formula-anchor health.

Dependency policy: standalone read-model integrity primitive.

### Control 07 — FAIL_CLOSED_RELEASE_GATES_V0_1

Aggregates already-scoped boolean/unknown gate evidence.

Dependency policy:

- does not import business controls;
- callers explicitly convert scoped control outcomes to native booleans;
- no string status such as `PASS` or `READY_FOR_RELEASE` is implicitly
  accepted as a passing gate.

## Accepted local duplication

The following duplication is currently intentional:

- local `PASS` / `HOLD` labels inside domain controls;
- canonical-JSON hashing helpers inside the two authority controls.

Reason: forcing a shared common-core module now would introduce coupling before
the authority schemas are proven stable. Consolidation should occur only when a
shared semantic contract exists, not merely to reduce line count.

## Prohibited coupling

Public controls must not import:

- production adapters;
- connected-service clients;
- live snapshots;
- workbook/Drive/Sheets access layers;
- mutation executors.

A pure control must not acquire write authority through composition.

## Composition contract

Higher-level workflows may compose controls only by explicit inputs.

Example:

```text
interval integrity ─┐
negative stock ─────┤
reconciliation ─────┼─> explicit boolean gate map ─> release aggregator
formula health ─────┘
```

Domain-specific authority/HOLD decisions remain separately scoped and must not
be converted to PASS merely because another control passed.

## Deferred larger migrations

Large orchestration modules such as writer dry-run contracts or outbound
decision kernels require a separate dependency and public-boundary audit before
migration. They are not implicitly approved by the completion of Controls
01–07.
