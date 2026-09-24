# INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V0_1

Status: **PUBLIC PURE MATERIALIZATION CONTROL — NO LIVE READ / NO WRITE AUTHORITY**

## Purpose

Validate the exact materialized evidence package that a future, separately
authorized read-only acquisition boundary would have to provide before existing
warehouse inbound controls consume that evidence.

This control is pure, in-memory, synthetic, non-networked and non-writing.

A PASS proves only **structural/materialized evidence coherence**. It does not
prove upstream evidence authenticity, provider authorization, target identity,
permission effectiveness, live freshness, or production mutation authority.

## Contract identities

Package contract:

`INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V1`

Locked scenario:

`INBOUND_SERIAL_QUERY_DERIVED_V1`

## Exact warehouse surface set

The package must contain exactly one hash for each of these five logical
warehouse surfaces:

1. `INBOUND_SOURCE_RECORD`
2. `ACTIVE_SERIAL_INTERVAL_UNIVERSE`
3. `INBOUND_DERIVED_QUERY_PROJECTION`
4. `INBOUND_QUERY_FORMULA_ANCHOR`
5. `ACTIVE_HOLD_INTERVAL_UNIVERSE`

No wildcard, caller-defined, additional or missing surface is accepted.

## SurfaceHashEvidence

Each surface entry contains:

- `surface_id`: one exact allowed surface ID;
- `surface_hash`: lowercase 64-character SHA-256 hex text.

The surface tuple must be native, contain exactly five entries and contain no
duplicate surface IDs.

Input order is not authoritative. The canonical package hash orders surfaces by
the locked surface order above.

## InboundEvidenceMaterializationPackage

Required fields:

### Identity/binding

- `contract_id`
- `scenario_id`
- `task_id`
- `scope_id`

### Target/security evidence

- `target_authority_id`
- `target_authority_hash`
- `permission_proof_id`
- `permission_proof_hash`
- `surface_registry_id`
- `surface_registry_hash`
- `zero_write_attestation_id`
- `zero_write_attestation_hash`

### Snapshot/version evidence

- `warehouse_schema_version`
- `provider_version_marker`
- `capture_marker`
- `control10_target_contract_hash`
- `control10_snapshot_hash`
- exact five-entry `surfaces` tuple

### Completeness evidence

- `serial_universe_complete`: native boolean and must be `True`;
- `serial_universe_evidence_id`
- `serial_universe_evidence_hash`
- `hold_universe_complete`: native boolean and must be `True`;
- `hold_universe_evidence_id`
- `hold_universe_evidence_hash`

### Deterministic mapping/evidence bindings

- `mapping_contract_id`
- `mapping_contract_hash`
- `source_evidence_binding_id`
- `source_evidence_binding_hash`
- `formula_reconciliation_binding_id`
- `formula_reconciliation_binding_hash`

### Receipt boundary

- `receipt_id`
- `receipt_hash`

### Authority invariants

- `live_read_authorized`: native boolean and must be `False`;
- `production_write_authorized`: native boolean and must be `False`.

## Exact text and hash rules

Every ID/version/marker field must be native non-blank text with no surrounding
whitespace.

Every hash field must be native lowercase SHA-256 hex text of exactly 64
characters.

No trimming, case-folding, truthiness conversion, string coercion, list-to-tuple
coercion or default filling is permitted.

The validator does not claim any supplied hash is authentic. It only validates
shape and binds the values into one deterministic package hash.

## Deterministic package hash

After all fields pass validation, the validator computes SHA-256 over canonical
JSON containing:

- contract/scenario/task/scope;
- all opaque authority/security IDs and hashes;
- schema/provider/capture bindings;
- Control 10 hashes;
- all five surface IDs/hashes in locked order;
- native completeness booleans and their evidence IDs/hashes;
- mapping/source/formula evidence IDs/hashes;
- receipt ID/hash;
- both no-authority booleans.

Canonical JSON uses sorted object keys and compact separators.

Equal validated package content therefore produces the same package hash,
regardless of input surface tuple order.

## Result

`MaterializationPackageResult` returns:

- `status`: `PASS` or `HOLD`;
- `package_coherent`: native boolean;
- `blocking_reasons`: deterministic sorted tuple;
- `package_hash`: deterministic SHA-256 hex on PASS, otherwise `None`;
- `live_read_authorized=False` always;
- `production_write_authorized=False` always.

## Reason codes

- `PACKAGE_TYPE_INVALID`
- `CONTRACT_INVALID`
- `SCENARIO_INVALID`
- `BINDING_INVALID`
- `TARGET_AUTHORITY_EVIDENCE_INVALID`
- `PERMISSION_EVIDENCE_INVALID`
- `SURFACE_REGISTRY_EVIDENCE_INVALID`
- `ZERO_WRITE_EVIDENCE_INVALID`
- `SCHEMA_VERSION_INVALID`
- `PROVIDER_VERSION_INVALID`
- `CAPTURE_MARKER_INVALID`
- `CONTROL10_BINDING_INVALID`
- `SURFACE_CONTAINER_INVALID`
- `SURFACE_SET_INVALID`
- `SURFACE_EVIDENCE_INVALID`
- `SERIAL_UNIVERSE_COMPLETENESS_UNPROVEN`
- `SERIAL_UNIVERSE_EVIDENCE_INVALID`
- `HOLD_UNIVERSE_COMPLETENESS_UNPROVEN`
- `HOLD_UNIVERSE_EVIDENCE_INVALID`
- `MAPPING_EVIDENCE_INVALID`
- `SOURCE_EVIDENCE_BINDING_INVALID`
- `FORMULA_RECONCILIATION_BINDING_INVALID`
- `RECEIPT_EVIDENCE_INVALID`
- `AUTHORITY_INVARIANT_INVALID`

Multiple independent blockers are returned in sorted order.

## Adversarial requirements

The test suite must prove at least:

1. one exact synthetic package -> PASS;
2. surface tuple order changes -> same package hash;
3. missing surface -> HOLD;
4. extra/unknown surface -> HOLD;
5. duplicate surface -> HOLD;
6. list instead of tuple -> HOLD;
7. malformed/non-lowercase/non-64 SHA-256 hash -> HOLD;
8. blank/whitespace ID, version or marker -> HOLD;
9. scenario drift -> HOLD;
10. task/scope binding malformed -> HOLD;
11. serial-universe completeness `False` -> HOLD;
12. serial-universe completeness `None` or pseudo-boolean -> HOLD;
13. HOLD-universe completeness `False` -> HOLD;
14. HOLD-universe completeness `None` or pseudo-boolean -> HOLD;
15. missing/malformed authority/permission/zero-write evidence -> HOLD;
16. malformed Control 10 binding -> HOLD;
17. mapping/source/formula/receipt evidence drift -> HOLD;
18. `live_read_authorized=True` or pseudo-boolean -> HOLD;
19. `production_write_authorized=True` or pseudo-boolean -> HOLD;
20. every result exposes no live or production write authority.

## Relationship to existing controls

This package does not execute Control 10 or the seven inbound producers.

It validates the **materialized package boundary** that a future external
acquisition layer would have to satisfy before those pure controls receive
already-materialized evidence.

The package PASS must never be converted directly into
`INBOUND_CONTROL_READY`. The existing producer controls, Control 13, and
Control 07 remain independently required.

## Public repository boundary

The implementation must not:

- import network/provider clients;
- access Google Sheets/Drive live;
- load credentials;
- discover production targets;
- read files as acquisition evidence;
- contain raw production rows or real serials in tests;
- grant/change permissions;
- expose a mutation method;
- create a production writer;
- mutate MASTER LIVE;
- weaken trusted public-boundary policies.

## Locked authority state

**LiveReadAuthorized = False**

**ProductionWriteAuthorized = False**

**Production writer = HOLD**

**MASTER LIVE unchanged**
