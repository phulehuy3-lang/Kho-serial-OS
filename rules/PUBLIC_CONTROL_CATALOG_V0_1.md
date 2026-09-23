# PUBLIC_CONTROL_CATALOG_V0_1

Status: **PUBLIC CONSOLIDATION BASELINE**

## Purpose

Define the public control inventory, responsibility boundaries, and allowed
dependencies after Phase 2 Controls 01–09.

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

### Control 08 — DRY_RUN_MUTATION_CONTRACT_V0_1

Validates a synthetic mutation manifest architecture without any executable
write capability.

Responsibilities include:

- deterministic manifest hash;
- idempotency binding;
- reviewed dry-run mutation whitelist;
- exact rollback pairing;
- explicit approval binding;
- mandatory post-transition read-back obligations;
- invariant `production_write_authorized=False`.

Dependency policy:

- may depend on `SOURCE_POOL_AUTHORITY_V0_1` only through an explicit
  upstream resolution object;
- same-year only in v0.1;
- HOLD release excluded;
- must not import a production adapter or connected-service client;
- PASS means dry-run contract coherence only, never write authority.

### Control 09 — RANKED_PREFIX_ALLOCATION_LINEAGE_V0_1

Validates deterministic ranked-prefix allocation and lineage over an
already-authorized candidate set.

Responsibilities include:

- canonical NEAREST-PRIOR ranking;
- ranked-prefix allocation;
- independent verifier on a separate implementation path;
- deterministic candidate-set hashing;
- source-rank lineage;
- allocation-plan lineage.

Dependency policy:

- allocator path may depend on the bootstrap `allocation_nearest_prior.py`
  primitive;
- verifier must not call allocator decision/ranking helpers;
- candidate authority/completeness is explicitly upstream;
- must not import Cross-Year Authority, Source-Pool Authority, HOLD lifecycle,
  release-gate aggregation, Rule Graph, or artifact-release logic.

## Accepted local duplication

The following duplication is currently intentional:

- local `PASS` / `HOLD` labels inside domain controls;
- canonical-JSON hashing helpers inside the authority and dry-run contract
  modules.

Reason: forcing a shared common-core module now would introduce coupling before
the schemas are proven stable. Consolidation should occur only when a shared
semantic contract exists, not merely to reduce line count.

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

source-pool authority ─> explicit resolution ─> dry-run mutation contract

already-authorized candidates ─> ranked-prefix allocation + lineage
```

Domain-specific authority/HOLD decisions remain separately scoped and must not
be converted to PASS merely because another control passed.

The dry-run mutation contract is not a release or mutation executor.

## Deferred larger migrations

The original monolithic outbound decision kernel remains intentionally
unmigrated. Only its unique ranked-prefix allocation and lineage layer was
extracted as Control 09 after dependency/duplication/public-boundary audit.

Rule Graph release profiles, BBGH/DDH artifact semantics, live candidate
universe authority, and executable outbound mutation remain outside Control 09.

Executable production adapters/writers are outside the current public
capability boundary and remain prohibited.
