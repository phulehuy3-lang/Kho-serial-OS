# PUBLIC_CONTROL_CATALOG_V0_1

Status: **PUBLIC CONSOLIDATION BASELINE**

## Purpose

Define the public control inventory, responsibility boundaries, and allowed
dependencies after Phase 2 Controls 01–12.

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
- exact source-pool ↔ candidate-source-set binding;
- idempotency binding;
- reviewed dry-run mutation whitelist;
- exact rollback pairing;
- explicit approval binding;
- mandatory post-transition read-back obligations;
- invariant `production_write_authorized=False`.

Dependency policy:

- may depend on `SOURCE_POOL_AUTHORITY_V0_1` only through an explicit
  upstream resolution object;
- may consume validated candidate/allocation hashes produced by Control 09 and
  a pretransition snapshot hash produced by Control 10 without importing those
  modules;
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
- deterministic candidate-set hashing with a versioned hash contract ID;
- source-rank lineage;
- allocation-plan lineage;
- canonical allocation-plan hashing after lineage PASS.

Dependency policy:

- allocator path may depend on the bootstrap `allocation_nearest_prior.py`
  primitive;
- verifier must not call allocator decision/ranking helpers;
- candidate authority/completeness is explicitly upstream;
- must not import Cross-Year Authority, Source-Pool Authority, HOLD lifecycle,
  release-gate aggregation, Rule Graph, or artifact-release logic.

### Control 10 — READONLY_SHADOW_SNAPSHOT_INTEGRITY_V0_1

Validates deterministic in-memory multi-surface snapshot integrity.

Responsibilities include:

- surface-contract hashing;
- target/schema-contract hashing;
- exact expected read-surface set;
- exact row field-set and scalar-type validation;
- deterministic surface and snapshot hashing;
- version-marker atomicity detection.

Dependency policy:

- standalone pure snapshot primitive;
- consumes already-materialized in-memory reads only;
- must not import provider/connector, credential, permission, target-discovery,
  authority-resolver, replay-engine, or mutation code;
- does not prove that a live read was authorized.

### Control 11 — MATERIALIZED_LINEAGE_REPLAY_V0_1

Replays a historical same-year allocation decision from already-materialized
candidate/source lineage.

Responsibilities include:

- reconstructing pre-transaction available quantity as inbound minus prior
  committed outbound;
- requiring independently verified pre-transaction serial lineage;
- validating replayability of historical lineage evidence;
- replaying canonical ranking/allocation through Control 09;
- comparing ranked sources, selected sources, allocation quantities, and
  candidate-set hashes only when both hash algorithm and hash contract IDs are
  compatible;
- distinguishing `NOT_REPLAYABLE` evidence defects from `HOLD` semantic
  mismatches.

Dependency policy:

- may depend on Control 09 as the canonical ranked-prefix replay kernel;
- candidate scope is locked to `MATERIALIZED_CANDIDATE_SET_ONLY`;
- a MATCH proves parity only within the supplied materialized set;
- must not discover the global candidate universe;
- must not import private outbound replay kernels, production adapters, live
  readers, connected-service clients, or mutation code.

### Control 12 — FORMULA_SEMANTIC_IDENTITY_V0_1

Validates exact semantics of an already-materialized QUERY formula against an
explicit, hashed contract.

Responsibilities include:

- generic QUERY semantic contracts;
- deterministic contract hashing;
- normalized source/query semantics;
- exact header-row binding;
- verified native QUERY parsing;
- verified OOXML-export wrapper parsing;
- exact exported fallback binding;
- deterministic versioned semantic hashing;
- fail-closed detection of semantic drift.

Dependency policy:

- standalone pure in-memory primitive;
- complements Control 06 but does not import it;
- Control 06 proves presence/error health; Control 12 proves semantic identity;
- when both gates are applicable, higher-level composition must require both to
  pass independently before release aggregation can be ready;
- a public regression composes Controls 06 and 12 only through explicit native
  booleans into Control 07; the production control modules remain decoupled;
- neither control implies cached-value freshness or source↔derived parity;
- must not import workbook adapters, live mapping constants, connectors, or
  mutation code.

## Accepted local duplication

The following duplication is currently intentional:

- local `PASS` / `HOLD` labels inside domain controls;
- canonical-JSON/SHA-256 helpers inside Controls 01, 02, 08, 09, 10, and 12.

Control 09 additionally publishes distinct hash contract IDs for candidate-set
and allocation-plan payloads. Digest algorithm identity alone is not treated as
payload-schema compatibility.

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
interval integrity ──┐
negative stock ───────┤
reconciliation ───────┼─> explicit boolean gate map ─> release aggregator
formula health ───────┤
formula semantics ────┘

source-pool authority ───────────────┐
                                     ├─> dry-run mutation contract
authorized candidate IDs ─> ranked-prefix allocation + lineage ─┤
                                     │
materialized read surfaces ─> snapshot integrity + atomicity

historical materialized source lineage ─> Control 09 replay ─> parity result ────┘
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

The private synthetic shadow replay harness and read-only shadow adapter remain
intentionally unmigrated. Only their pure schema/snapshot-integrity layer was
extracted as Control 10. Live connector execution, credentials, permissions,
target discovery, authority resolution, and replay orchestration remain outside
Control 10.

The private production snapshot validator, synthetic writer replay harness, and
Wave A response-preimage/governance workflow remain intentionally unmigrated.
Only the same-year materialized-lineage replay primitive was extracted as
Control 11, and it explicitly does not prove global candidate completeness.

The private production mapping adapter remains intentionally unmigrated. Only
its generic in-memory QUERY formula-semantic identity primitive was extracted
as Control 12. Live sheet/range mappings, workbook access, cached-value
validation, and production snapshot orchestration remain outside Control 12.

Executable production adapters/writers are outside the current public
capability boundary and remain prohibited.
