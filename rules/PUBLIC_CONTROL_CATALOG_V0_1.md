# PUBLIC_CONTROL_CATALOG_V0_1

Status: **PUBLIC CONTROL INVENTORY — PHASE 2 BASELINE + PHASE 3 ADDITION**

## Purpose

Define the public control inventory, responsibility boundaries, and allowed
dependencies for frozen Phase 2 Controls 01–12 and the later Phase 3 addition.

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

Artifacts:

- `rules/RULE_0099_SOURCE_OF_TRUTH_DERIVED_READ_ONLY.md`
- `rules/SOURCE_ROLE_BOUNDARY_V0_1.md`
- `scripts/source_role_boundary_v0_1.py`

Responsibility:

- only authoritative source regions may pass the business-write role boundary;
- derived/read-model regions are treated as read-only and block business-write intent;
- classification must be explicit and exactly one allowed role;
- malformed, contradictory, missing, or unsupported classification fails closed;
- release still requires separate applicable source read-back and read-model integrity controls to pass;
- this pure boundary never grants production write authority.

## Inbound source verification primitives

### SOURCE_ROLE_BOUNDARY_V0_1

Implements the RULE-0099 SOURCE_OF_TRUTH / DERIVED_READ_ONLY business-write
role boundary as a pure fail-closed evaluator. It does not authorize a write.

### SOURCE_READBACK_V0_1

Validates one already-materialized expected source record against one
already-materialized read-back record with exact task/scope/capture binding,
exact field-set equality, exact scalar type equality and exact value equality.

Dependency policy:

- pure in-memory primitive;
- no live read, provider, connector, target discovery or credential;
- does not replace Control 10 snapshot integrity or Control 06 reconciliation;
- produces only source-readback evidence for an explicitly scoped workflow;
- PASS never grants production write authority.

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

## Phase 3 control

### Control 13 — REQUIRED_GATE_SET_PREFLIGHT_V0_1

Checks exact required-gate coverage, duplicate IDs, and scenario/task/scope/
capture-marker binding in already-materialized evidence. A structural PASS
returns an immutable, complete native boolean/unknown map for explicit
downstream composition with Control 07. `False` and `None` are forwarded and
remain blocking there. The caller is responsible for declaring the authoritative
required set and marker; this control proves neither global gate applicability
nor live freshness, evidence authenticity, production release, or write
authority. It imports no business controls or connected-service client.

The frozen `v0.2.0` release remains the twelve-control Phase 2 baseline;
Control 13 is a later main-branch addition.

## Warehouse scenario profiles

### INBOUND_SERIAL_QUERY_DERIVED_V1

A locked, warehouse-specific pure composition profile for inbound serial-range
acceptance when a QUERY-derived read-model surface is applicable.

Exact required gate universe:

- source_role_boundary;
- source_readback;
- serial_range_quantity;
- serial_overlap_free;
- source_derived_reconciliation;
- formula_health;
- formula_semantics.

Composition policy:

- producer outcomes are already-materialized;
- all seven records are bound to one scenario/task/scope/capture marker;
- Control 13 must PASS exact-set/binding preflight before Control 07 is called;
- `hold_conflict` remains a separate native boolean/unknown input;
- only all-seven-True plus `hold_conflict=False` maps to
  `INBOUND_CONTROL_READY`;
- every path preserves `production_write_authorized=False`.

This profile is not a live adapter, production release decision, mutation
executor, or general-purpose scenario framework.

## Post-profile boundary decision

### POST_PROFILE_BOUNDARY_AUDIT_V0_1

After closure of `INBOUND_SERIAL_QUERY_DERIVED_V1`, the remaining gap is not
another generic control. It is the warehouse-specific boundary between future
approved read-only evidence acquisition and the already-materialized producer
inputs consumed by the inbound profile.

Current decision:

- pure inbound profile: CLOSED;
- executable live read: HOLD;
- production writer: HOLD;
- next permitted artifact:
  `INBOUND_READONLY_EVIDENCE_BOUNDARY_DESIGN_V0_1`;
- next artifact is design-only, non-live and non-writing;
- no production identifiers, credentials, permissions, network client or
  MASTER LIVE mutation may be introduced.

See `rules/POST_PROFILE_BOUNDARY_AUDIT_V0_1.md` for the full boundary matrix
and promotion rule.

## Inbound read-only evidence boundary

### INBOUND_READONLY_EVIDENCE_BOUNDARY_DESIGN_V0_1

Design-only specification for the future warehouse-specific boundary between an
approved read-only Production-shadow capture and the already-materialized
inputs consumed by `INBOUND_SERIAL_QUERY_DERIVED_V1`.

The design locks:

- logical target authority without Production resource IDs in GitHub;
- dedicated read-only identity and effective-permission proof;
- five exact inbound evidence surfaces, including complete serial and HOLD
  interval universes;
- runtime zero-write attestation;
- provider version/capture/atomicity semantics compatible with Control 10;
- deterministic mapping into the seven existing inbound producers plus separate
  `hold_conflict`;
- evidence receipt/tamper boundary.

Conformance review:

`INBOUND_READONLY_EVIDENCE_BOUNDARY_DESIGN_REVIEW_V0_1`

Current authority state:

- design conformance = PASS;
- implementation = HOLD;
- `LiveReadAuthorized=False`;
- `ProductionWriteAuthorized=False`;
- no live client, credential, target ID or MASTER LIVE mutation.

## Inbound read-only implementation readiness

### INBOUND_READONLY_EVIDENCE_IMPLEMENTATION_READINESS_AUDIT_V0_1

Verdict:

`HOLD_IMPLEMENTATION_NOT_READY`

The evidence-boundary design is coherent, but executable live acquisition is
not ready because target authority, effective read-only permission, exact
Production surface bindings, interval/HOLD universe completeness, provider
version semantics, runtime zero-write enforcement and tamper-evident receipt
storage are not yet materialized.

The current trusted public boundary also intentionally prohibits normal
network/provider clients in production scripts. That policy must not be
weakened merely to make a live reader fit.

Next safe step:

`INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V0_1`

This next artifact must remain pure, in-memory, synthetic and non-writing. It
will define/validate the exact materialized package a future external
read-only acquisition boundary would have to provide.

Authority remains:

- `LiveReadAuthorized=False`;
- `ProductionWriteAuthorized=False`;
- Production writer = HOLD;
- MASTER LIVE unchanged.

## Inbound evidence materialization package

### INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V0_1

Pure warehouse-specific package boundary selected after the read-only
implementation-readiness audit returned
`HOLD_IMPLEMENTATION_NOT_READY`.

The validator accepts only opaque/materialized evidence and locks:

- scenario `INBOUND_SERIAL_QUERY_DERIVED_V1`;
- exact task/scope binding;
- target-authority, permission, surface-registry and zero-write evidence
  ID/hash pairs;
- warehouse schema, provider version and capture markers;
- Control 10 target/snapshot hashes;
- exactly five locked inbound surface hashes;
- explicit native-boolean completeness proof for active serial and HOLD
  universes;
- deterministic mapping/source/formula evidence bindings;
- receipt ID/hash;
- deterministic canonical package hash;
- `LiveReadAuthorized=False`;
- `ProductionWriteAuthorized=False`.

A package PASS means structural/materialized evidence coherence only. It does
not prove upstream authenticity or authorize a live read, and it must not be
converted directly into `INBOUND_CONTROL_READY`.

The package remains pure, in-memory, synthetic, non-networked and non-writing.
Production acquisition and writer capabilities remain outside the current
public repository boundary.

## Post-materialization external acquisition readiness

### POST_MATERIALIZATION_EXTERNAL_ACQUISITION_READINESS_AUDIT_V0_1

Verdict:

`PASS_FOR_EXTERNAL_ADAPTER_DESIGN_ONLY`

The materialization package now creates a stable handoff between a future
external read-only acquisition boundary and the existing pure warehouse
controls.

This is sufficient to design, but not implement, an external adapter.

The adapter design must remain outside executable provider capability and keep
the current public boundary intact. Runtime blockers remain independently open:

- target authority not materialized;
- effective read-only permission not materialized;
- exact Production surface bindings not materialized;
- serial/HOLD universe completeness unproven;
- provider version/capture semantics unproven;
- zero-write runtime unproven;
- tamper-evident receipt store not materialized.

Next permitted artifact:

`EXTERNAL_INBOUND_ACQUISITION_ADAPTER_DESIGN_V0_1`

Authority remains:

- `LiveReadAuthorized=False`;
- `ProductionWriteAuthorized=False`;
- Production writer = HOLD;
- MASTER LIVE unchanged.

## External inbound acquisition adapter design

### EXTERNAL_INBOUND_ACQUISITION_ADAPTER_DESIGN_V0_1

Design-only warehouse-specific architecture for a future external runtime that
would acquire exactly five inbound evidence surfaces and emit one validated
`INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V1`.

The design locks:

- external runtime separation from the public pure-control code path;
- opaque target-authority lookup;
- dedicated read-only identity and independent effective-permission proof;
- exact five-surface acquisition with no wildcard discovery;
- provider consistency/version fail-closed decision table;
- explicit serial/HOLD universe completeness proof;
- zero-write runtime attestation;
- deterministic package transformation;
- append-only or independently tamper-evident receipt boundary;
- abort-on-ambiguity semantics;
- ten promotion gates before any executable adapter issue.

Conformance review:

`EXTERNAL_INBOUND_ACQUISITION_ADAPTER_DESIGN_REVIEW_V0_1`

Current authority:

- design conformance = PASS;
- executable acquisition readiness = HOLD;
- `LiveReadAuthorized=False`;
- `ExecutableAcquisitionAuthorized=False`;
- `ProductionWriteAuthorized=False`;
- Production writer = HOLD;
- MASTER LIVE unchanged.

## External inbound acquisition promotion readiness

### EXTERNAL_INBOUND_ACQUISITION_PROMOTION_READINESS_AUDIT_V0_1

Verdict:

`HOLD_EXECUTABLE_ACQUISITION_NOT_READY`

Promotion requires ten independently evidenced gates.

Current result:

- PRG-01 target-authority registry — HOLD;
- PRG-02 dedicated read-only identity — HOLD;
- PRG-03 effective permission proof — HOLD;
- PRG-04 exact five Production surface bindings — HOLD;
- PRG-05 serial-universe completeness — HOLD;
- PRG-06 HOLD-universe completeness — HOLD;
- PRG-07 provider version/capture semantics — HOLD;
- PRG-08 zero-write runtime enforcement — HOLD;
- PRG-09 tamper-evident receipt boundary — HOLD;
- PRG-10 repository placement/four required checks — PASS.

The one governance PASS cannot offset nine missing runtime evidence gates.

Next permitted artifact:

`INBOUND_TARGET_AUTHORITY_REGISTRY_MATERIALIZATION_PLAN_V0_1`

It must remain non-live and non-writing and may only define how PRG-01 would be
materialized and independently reviewed.

Authority remains:

- `LiveReadAuthorized=False`;
- `ExecutableAcquisitionAuthorized=False`;
- `ProductionWriteAuthorized=False`;
- Production writer = HOLD;
- MASTER LIVE unchanged.

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
