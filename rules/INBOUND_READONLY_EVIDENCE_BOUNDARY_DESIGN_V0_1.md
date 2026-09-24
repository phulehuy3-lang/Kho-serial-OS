# INBOUND_READONLY_EVIDENCE_BOUNDARY_DESIGN_V0_1

Status: **DESIGN ONLY — NON-LIVE / NON-WRITING / IMPLEMENTATION HOLD**

## Purpose

Define the warehouse-specific boundary required to transform a future approved
read-only inbound capture into already-materialized evidence for
`INBOUND_SERIAL_QUERY_DERIVED_V1`.

This document specifies contracts only. It does not create or authorize a live
reader, target, credential, permission, connector, provider session, or writer.

Locked invariants for this design artifact:

- `LiveReadAuthorized = False`
- `ProductionWriteAuthorized = False`
- executable read-only integration = `HOLD`
- production writer = `HOLD`
- MASTER LIVE mutation = prohibited

## 1. Logical target-authority contract

Future evidence acquisition must resolve one logical warehouse target through an
authoritative runtime registry held outside this public repository.

`InboundTargetAuthority` must bind:

- `target_authority_id`;
- environment = `PRODUCTION_SHADOW`;
- logical target alias only;
- expected warehouse schema version;
- exact inbound read-surface registry ID;
- authority lifecycle state;
- independent read-back state;
- deterministic authority-record hash.

Allowed lifecycle states:

- `DRAFT`
- `APPROVED`
- `ACTIVE`
- `REVOKED`
- `SUPERSEDED`

Only one ACTIVE authority may resolve the approved logical target alias.

The public repository must never contain the production workbook/resource ID,
URL, sheet ID, range ID, credential locator, or secret.

Fail closed:

- unknown/duplicate authority;
- non-ACTIVE authority;
- schema mismatch;
- hash drift;
- failed authority read-back.

Canonical blocker:

`HOLD_TARGET_AUTHORITY_INVALID`

## 2. Dedicated read-only identity and effective-permission proof

A future live reader must use a dedicated read-only identity bound to
`PRODUCTION_SHADOW`.

The identity contract must require:

- dedicated runtime identity;
- no write/edit scope;
- no share/permission-management scope;
- no resource-creation scope;
- no fallback to a personal or write-capable identity;
- credential material outside GitHub;
- explicit environment binding;
- revocation/rotation capability.

A separate `EffectivePermissionProof` must bind:

- proof ID;
- identity authority ID;
- target authority ID;
- exact effective permission set;
- proof collection method;
- proof version/capture marker;
- explicit absence of write/edit permission;
- explicit absence of share/permission-management capability;
- explicit absence of fallback write identity;
- independent review/read-back state;
- deterministic proof hash.

A configuration flag such as `read_only=true` is not permission proof.

Canonical blocker:

`HOLD_EFFECTIVE_PERMISSION_UNPROVEN`

## 3. Exact inbound read-surface registry

Future evidence acquisition may read only surfaces declared in one exact
warehouse-specific registry.

Every `InboundReadSurface` must bind:

- surface ID;
- target authority ID;
- logical surface alias;
- exact ordered field contract;
- scalar types;
- role = `SOURCE_OF_TRUTH` or `DERIVED_READ_ONLY`;
- maximum allowed row/range scope;
- capture semantics;
- surface-contract hash;
- registry state;
- independent read-back state.

No wildcard workbook traversal, caller-supplied arbitrary range, nearest-name
sheet discovery, or unrelated Drive traversal is allowed.

### Required logical evidence surfaces

The design requires only the logical surfaces needed by the locked inbound
profile:

1. `INBOUND_SOURCE_RECORD`
   - role: `SOURCE_OF_TRUTH`
   - materializes the expected/read-back source record and serial quantity fields.

2. `ACTIVE_SERIAL_INTERVAL_UNIVERSE`
   - authoritative complete interval set for the applicable inbound overlap scope;
   - completeness must be independently bound, not inferred from a selected subset.

3. `INBOUND_DERIVED_QUERY_PROJECTION`
   - role: `DERIVED_READ_ONLY`
   - supplies normalized values for source↔derived reconciliation.

4. `INBOUND_QUERY_FORMULA_ANCHOR`
   - role: `DERIVED_READ_ONLY`
   - supplies formula presence/error state and materialized formula text.

5. `ACTIVE_HOLD_INTERVAL_UNIVERSE`
   - authoritative complete HOLD/conflict set for the applicable inbound scope;
   - used only to materialize the separate `hold_conflict` input.

A future implementation may not silently broaden or reduce this set. Any
additional or replacement surface requires a reviewed design revision.

Canonical blockers:

- `HOLD_READ_SURFACE_NOT_AUTHORIZED`
- `HOLD_INTERVAL_UNIVERSE_INCOMPLETE`
- `HOLD_HOLD_UNIVERSE_INCOMPLETE`

## 4. Runtime zero-write attestation

Before any future live read, the runtime must produce a zero-write attestation.

`ZeroWriteRuntimeAttestation` must bind:

- environment identity;
- deployment/package inventory hash;
- loaded-module/capability inventory hash;
- effective identity authority;
- provider capability inventory;
- no write/edit method available;
- no permission-management method available;
- no mutation executor loaded;
- no caller-controlled write-mode escalation;
- no write-capable fallback identity;
- attestation version/capture marker;
- deterministic attestation hash.

Required future verdict:

`ZERO_WRITE_RUNTIME_PROVEN`

Unknown or partial capability evidence must fail closed:

`HOLD_ZERO_WRITE_RUNTIME_UNPROVEN`

This design does not implement such an attestation and does not authorize a
runtime to connect.

## 5. Provider version / capture / atomicity contract

The future provider boundary must declare what consistency evidence it can
actually supply.

It must define:

- provider revision/version marker semantics;
- per-surface version marker semantics;
- one shared capture marker for the evidence bundle;
- whether a true atomic multi-surface read is possible;
- correlation rule across surfaces;
- maximum permitted capture window, if any;
- mandatory re-read behavior on drift;
- fail-closed state when consistency cannot be proven.

For the current public Control 10 contract, all materialized surfaces used in
one snapshot must normalize to one non-empty version marker before
`atomic_snapshot_proven=True`.

If the provider cannot supply evidence capable of satisfying that invariant,
live execution remains HOLD until a separately reviewed compatibility design is
approved. Caller timestamps must not be fabricated as provider versions.

Canonical blocker:

`HOLD_SNAPSHOT_VERSION_UNPROVEN`

## 6. Deterministic evidence-to-producer mapping

A future materializer must produce the exact existing inbound producer inputs
without adding new business semantics.

### Gate 1 — source_role_boundary

Source:

- `INBOUND_SOURCE_RECORD` registry role.

Mapping:

- exact registry role tuple -> `SOURCE_ROLE_BOUNDARY_V0_1`.

No caller text may override the canonical surface role.

### Gate 2 — source_readback

Source:

- expected source projection bound to the inbound task;
- captured `INBOUND_SOURCE_RECORD`.

Mapping:

- exact task/scope/capture binding;
- exact field set;
- exact scalar types;
- exact values -> `SOURCE_READBACK_V0_1`.

### Gate 3 — serial_range_quantity

Source:

- serial start;
- serial end;
- declared quantity from `INBOUND_SOURCE_RECORD`.

Mapping:

- exact text-preserved serial identity parsed only under the reviewed interval
  contract;
- inclusive quantity check -> Control 04.

### Gate 4 — serial_overlap_free

Source:

- proposed inbound interval;
- complete `ACTIVE_SERIAL_INTERVAL_UNIVERSE`.

Mapping:

- canonical interval construction and overlap semantics -> Control 04.

A selected or partial comparison set is insufficient.

### Gate 5 — source_derived_reconciliation

Source:

- normalized authoritative source fields;
- normalized `INBOUND_DERIVED_QUERY_PROJECTION` fields.

Mapping:

- exact field/value parity -> Control 06.

### Gate 6 — formula_health

Source:

- `INBOUND_QUERY_FORMULA_ANCHOR` materialized presence/error state.

Mapping:

- formula-anchor health -> Control 06.

### Gate 7 — formula_semantics

Source:

- materialized QUERY formula text;
- explicit reviewed QUERY semantic contract.

Mapping:

- exact semantic identity -> Control 12.

The materializer must not create a semantic contract from the observed formula
itself. That would convert observation into authority.

### Separate hold_conflict input

Source:

- proposed inbound interval;
- complete `ACTIVE_HOLD_INTERVAL_UNIVERSE`.

Mapping:

- fail-closed HOLD conflict assessment;
- native boolean/unknown only.

This input remains separate from the seven-gate Control 13 universe, matching
the locked profile.

## 7. Evidence bundle and receipt boundary

A future read-only evidence bundle must bind metadata without placing production
payloads in this public repository.

`InboundReadonlyEvidenceBundle` must bind:

- evidence bundle ID;
- environment identity;
- target authority ID;
- identity/permission proof ID;
- read-surface registry ID/hash;
- runtime zero-write attestation ID/hash;
- schema version;
- provider version marker;
- capture marker;
- Control 10 target/snapshot contract hashes;
- materialized surface hashes;
- deterministic evidence-mapping contract hash;
- resulting seven producer evidence hashes or equivalent deterministic
  references;
- separate HOLD-conflict evidence hash/reference;
- blocker list;
- bundle hash.

Raw operational rows, real serials, production identifiers, credentials, and
secrets must remain outside GitHub.

A future receipt store must be append-only or independently tamper-evident and
separate from mutable warehouse transaction inputs.

Canonical blocker:

`HOLD_EVIDENCE_RECEIPT_BOUNDARY_UNPROVEN`

## 8. Evidence mapping integrity

The mapping layer must be declarative and exact.

It must bind:

- one mapping contract version;
- exact surface ID -> producer input mapping;
- exact field names and types;
- exact normalization rules;
- exact scenario/task/scope/capture binding;
- mapping-contract hash.

Prohibited:

- implicit fallback fields;
- nearest-header matching;
- case-insensitive guessing;
- silent type conversion;
- dynamic range broadening;
- missing-field defaulting;
- deriving authority from observed values;
- mapping one producer PASS to another producer's gate.

Any ambiguity returns:

`HOLD_EVIDENCE_MAPPING_INVALID`

## 9. Fail-closed decision matrix

| Condition | Required state |
| --- | --- |
| target authority unavailable/ambiguous | HOLD_TARGET_AUTHORITY_INVALID |
| effective read-only permission unproven | HOLD_EFFECTIVE_PERMISSION_UNPROVEN |
| surface outside exact registry | HOLD_READ_SURFACE_NOT_AUTHORIZED |
| serial interval universe incomplete | HOLD_INTERVAL_UNIVERSE_INCOMPLETE |
| HOLD universe incomplete | HOLD_HOLD_UNIVERSE_INCOMPLETE |
| runtime zero-write unproven | HOLD_ZERO_WRITE_RUNTIME_UNPROVEN |
| provider version/capture semantics unproven | HOLD_SNAPSHOT_VERSION_UNPROVEN |
| evidence mapping ambiguous/drifted | HOLD_EVIDENCE_MAPPING_INVALID |
| receipt/tamper boundary unproven | HOLD_EVIDENCE_RECEIPT_BOUNDARY_UNPROVEN |
| any required state unknown | HOLD |

Unknown security/authority states must never degrade to warnings.

## 10. Relationship to existing public controls

### Control 10

Control 10 remains the pure in-memory snapshot integrity primitive.

This boundary design supplies the future authority/security contract that would
have to exist *before* already-materialized surfaces may be trusted as inputs to
Control 10. It does not duplicate snapshot hashing or atomicity logic.

### SOURCE_ROLE_BOUNDARY_V0_1

The canonical role comes from the exact read-surface registry. The materializer
must not infer or override it.

### SOURCE_READBACK_V0_1

The future materializer supplies the expected and captured records with exact
task/scope/capture binding. SOURCE_READBACK remains the parity evaluator.

### INBOUND_SERIAL_QUERY_DERIVED_V1

This design may only produce already-materialized inputs for the locked seven
gates plus separate `hold_conflict`.

It must not change the scenario ID, gate universe, Control 13 ordering, or
Control 07 semantics.

## 11. Public-repository boundary

This design intentionally contains no:

- production resource ID or URL;
- real sheet/range identity;
- credential or secret;
- permission grant/change;
- network/client library;
- provider implementation;
- live read;
- target discovery implementation;
- filesystem evidence payload;
- write/mutation method;
- production writer;
- MASTER LIVE mutation;
- HOLD release;
- cross-year mutation.

## 12. Promotion rule

This design being merged does not authorize implementation.

Before any executable read-only integration is considered, a separate review
must prove at minimum:

1. warehouse-only scope remains intact;
2. exact target-authority materialization approach is credible;
3. effective read-only permission can be independently proven;
4. exact surface registry can be materialized without production identifiers in
   GitHub;
5. zero-write runtime can be structurally enforced;
6. provider version semantics can satisfy or defensibly adapt to Control 10;
7. interval/HOLD universe completeness can be proven;
8. evidence mapping is deterministic and non-coercive;
9. audit receipt boundary is independently tamper-evident;
10. no write-capable dependency or production credential is introduced into the
    public repository.

A separate implementation issue is mandatory.

## Final state

**INBOUND_READONLY_EVIDENCE_BOUNDARY_V0_1 = SPECIFIED_NOT_IMPLEMENTED**

**LiveReadAuthorized = False**

**Executable live read = HOLD**

**ProductionWriteAuthorized = False**

**Production writer = HOLD**

**MASTER LIVE unchanged**
