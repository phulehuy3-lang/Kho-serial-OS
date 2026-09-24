# EXTERNAL_INBOUND_ACQUISITION_ADAPTER_DESIGN_V0_1

Status: **DESIGN ONLY — EXTERNAL / READ-ONLY / NON-LIVE / NON-WRITING**

## Purpose

Define the warehouse-specific architecture for a future external read-only
acquisition runtime that may collect inbound warehouse evidence and emit exactly
one validated `INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V1`.

This document is a design contract only.

It does not implement a provider client, perform a live read, create a
credential, change permissions, discover a Production target, or authorize a
writer.

Locked authority state:

- `LiveReadAuthorized = False`
- `ProductionWriteAuthorized = False`
- executable acquisition = `HOLD`
- Production writer = `HOLD`
- MASTER LIVE mutation = prohibited

## 1. Architecture boundary

The future system is split into two trust zones.

### Zone A — external acquisition runtime

Purpose:

- resolve approved authority objects outside GitHub;
- use a dedicated read-only identity;
- acquire exactly five approved warehouse evidence surfaces;
- collect provider consistency/version evidence;
- prove serial/HOLD universe completeness;
- emit zero-write runtime attestation;
- emit receipt evidence;
- transform the capture into
  `INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V1`.

Zone A may exist only after a separate promotion decision.

### Zone B — public pure-control repository

Purpose:

- validate the materialization package;
- evaluate existing pure warehouse controls;
- run Control 13 and Control 07;
- never acquire provider data directly.

No provider SDK/client, network capability, credential, Production resource ID,
or mutation path belongs in Zone B.

## 2. External runtime inputs

The external runtime may accept only approved opaque authority references.

Required inputs:

- `target_authority_id`
- `permission_proof_authority_id`
- `surface_registry_id`
- `mapping_contract_id`
- `receipt_sink_authority_id`
- inbound `task_id`
- inbound `scope_id`

The runtime must not accept:

- arbitrary workbook/resource IDs;
- arbitrary sheet/range IDs;
- caller-supplied URLs;
- wildcard discovery requests;
- caller-supplied source-role classification;
- write mode;
- permission mutation requests.

Actual Production identifiers must be resolved only by an external authority
store after the opaque authority IDs pass validation.

## 3. Target-authority lookup contract

The external authority store must return one
`ResolvedInboundTargetAuthority` bound to:

- `target_authority_id`;
- environment = `PRODUCTION_SHADOW`;
- one logical warehouse target alias;
- exact warehouse schema version;
- exact five-surface registry ID/hash;
- lifecycle state = `ACTIVE`;
- deterministic authority-record hash;
- independent read-back status.

Fail closed if:

- zero or multiple ACTIVE records resolve;
- authority hash drifts;
- environment differs;
- schema version differs;
- surface registry binding differs;
- read-back status is not PASS.

Canonical abort:

`ABORT_TARGET_AUTHORITY_INVALID`

Production resource IDs remain external and must never be serialized into the
public materialization package.

## 4. Dedicated read-only runtime identity

The adapter design requires one dedicated runtime identity.

The identity must:

- be separate from personal/operator identities;
- have only read capabilities required for the five surfaces;
- have no write/edit permission;
- have no resource-creation permission;
- have no share/permission-management permission;
- have no write-capable fallback identity;
- have credential material stored outside GitHub;
- support revocation/rotation;
- be explicitly bound to `PRODUCTION_SHADOW`.

The runtime must independently acquire one
`EffectivePermissionProof` before reading any warehouse surface.

The proof must bind:

- identity authority;
- target authority;
- exact effective permission set;
- collection method;
- provider evidence/version marker;
- independent review/read-back;
- deterministic proof hash.

A configuration flag such as `read_only=true` is not sufficient.

Canonical abort:

`ABORT_EFFECTIVE_PERMISSION_UNPROVEN`

## 5. Exact five-surface acquisition plan

The adapter is hard-bound to exactly five logical surfaces.

### S1 — INBOUND_SOURCE_RECORD

Role:

`SOURCE_OF_TRUTH`

Purpose:

- inbound source fields;
- serial start/end;
- declared quantity;
- source read-back evidence.

### S2 — ACTIVE_SERIAL_INTERVAL_UNIVERSE

Purpose:

- complete active serial interval universe for the applicable warehouse scope.

Required property:

- completeness must be proven by authority/registry semantics;
- selected subsets are invalid.

### S3 — INBOUND_DERIVED_QUERY_PROJECTION

Role:

`DERIVED_READ_ONLY`

Purpose:

- source↔derived reconciliation.

### S4 — INBOUND_QUERY_FORMULA_ANCHOR

Role:

`DERIVED_READ_ONLY`

Purpose:

- formula presence/error state;
- materialized QUERY formula text.

### S5 — ACTIVE_HOLD_INTERVAL_UNIVERSE

Purpose:

- complete active HOLD/conflict interval universe for the applicable scope.

Required property:

- completeness must be proven;
- selected subsets are invalid.

No wildcard discovery, workbook crawl, nearest-name lookup, fuzzy field
matching, arbitrary caller ranges, or unrelated Drive traversal is permitted.

Canonical abort:

`ABORT_READ_SURFACE_NOT_AUTHORIZED`

## 6. Provider consistency decision table

The adapter must not invent provider consistency semantics.

| Provider evidence | Required design behavior |
| --- | --- |
| one shared immutable snapshot/version token across all five surfaces | bind token directly and continue |
| per-surface immutable versions with a documented atomic/correlation primitive | derive one provider-consistency record under explicit provider rules |
| per-surface versions without defensible cross-surface correlation | ABORT |
| only caller clock/timestamp available | ABORT |
| provider version marker missing or blank | ABORT |
| any surface version drift during capture | re-read under provider rules or ABORT |

Canonical abort:

`ABORT_PROVIDER_VERSION_SEMANTICS_UNPROVEN`

The future implementation must prove compatibility with Control 10 before any
capture may be treated as atomically consistent.

## 7. Capture sequence

The future executable design, if separately authorized, must follow this order:

1. resolve target authority;
2. validate dedicated read-only identity;
3. collect effective-permission proof;
4. validate exact five-surface registry;
5. produce zero-write runtime attestation;
6. establish provider consistency primitive;
7. acquire all five surfaces;
8. verify provider version/capture consistency;
9. verify serial-universe completeness;
10. verify HOLD-universe completeness;
11. construct Control 10 materialized surface evidence;
12. construct deterministic mapping/source/formula evidence bindings;
13. emit receipt record;
14. construct `INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V1`;
15. validate the package using the pure package validator;
16. stop.

The external runtime must not invoke warehouse mutation after step 16.

## 8. Completeness proof generation

### Serial interval universe

The adapter must produce:

- `serial_universe_complete=True` only when the authority model proves the
  capture includes the complete active interval universe for the exact inbound
  scope;
- evidence ID/hash tied to the registry, target, provider version and capture.

If completeness cannot be proven:

`ABORT_INTERVAL_UNIVERSE_COMPLETENESS_UNPROVEN`

### HOLD interval universe

The adapter must produce:

- `hold_universe_complete=True` only when the authority model proves the
  capture includes the complete active HOLD universe for the exact scope;
- evidence ID/hash tied to the same target/provider/capture context.

If completeness cannot be proven:

`ABORT_HOLD_UNIVERSE_COMPLETENESS_UNPROVEN`

A zero-result query is not itself proof of completeness.

## 9. Zero-write runtime attestation

Before provider acquisition, the future runtime must generate one
`ZeroWriteRuntimeAttestation`.

It must prove:

- deployment/package inventory;
- loaded module/capability inventory;
- exact provider operation allowlist;
- no write/edit methods available;
- no permission-management methods available;
- no resource creation;
- no mutation executor;
- no write-capable fallback identity;
- no caller-controlled write escalation;
- environment binding;
- attestation version/capture marker;
- deterministic attestation hash.

If any capability is unknown:

`ABORT_ZERO_WRITE_RUNTIME_UNPROVEN`

The adapter design must prefer structural absence of write capability over
runtime flags that merely disable a write-capable client.

## 10. Deterministic transformation contract

The external adapter may output exactly one public boundary object:

`INBOUND_EVIDENCE_MATERIALIZATION_PACKAGE_V1`

The transformation must map:

- authority proof -> target-authority fields;
- effective-permission proof -> permission fields;
- five-surface registry -> surface-registry fields;
- zero-write attestation -> zero-write fields;
- provider consistency evidence -> provider/capture fields;
- Control 10 evidence -> target/snapshot hashes;
- five acquired surfaces -> exact five surface hashes;
- serial completeness proof -> serial completeness fields;
- HOLD completeness proof -> HOLD completeness fields;
- mapping contract -> mapping fields;
- source expected/read-back binding -> source evidence fields;
- formula/reconciliation binding -> formula evidence fields;
- receipt record -> receipt fields.

The transformation may not:

- invent missing values;
- coerce pseudo-booleans;
- replace unavailable hashes with placeholders;
- infer authority from observed business data;
- drop blockers;
- create a semantic formula contract from the observed formula;
- convert a partial universe into completeness=True.

If transformation cannot satisfy the package validator:

`ABORT_MATERIALIZATION_PACKAGE_INVALID`

## 11. Receipt / tamper-evident boundary

The external runtime must emit one receipt record before handing the package to
the pure-control boundary.

The receipt must bind at minimum:

- receipt ID;
- target-authority ID/hash;
- permission proof ID/hash;
- surface registry ID/hash;
- zero-write attestation ID/hash;
- provider version marker;
- capture marker;
- five surface hashes;
- serial/HOLD completeness evidence IDs/hashes;
- mapping contract ID/hash;
- package hash;
- runtime blocker list;
- acquisition outcome.

The receipt store must be:

- append-only, or
- independently tamper-evident.

It must be outside mutable warehouse transaction input.

Raw Production payloads and credentials must not be copied into GitHub.

Canonical abort:

`ABORT_RECEIPT_BOUNDARY_UNPROVEN`

## 12. Failure and abort semantics

Any unresolved authority/security/consistency state must abort before package
handoff.

Required abort states include:

- `ABORT_TARGET_AUTHORITY_INVALID`
- `ABORT_EFFECTIVE_PERMISSION_UNPROVEN`
- `ABORT_READ_SURFACE_NOT_AUTHORIZED`
- `ABORT_PROVIDER_VERSION_SEMANTICS_UNPROVEN`
- `ABORT_INTERVAL_UNIVERSE_COMPLETENESS_UNPROVEN`
- `ABORT_HOLD_UNIVERSE_COMPLETENESS_UNPROVEN`
- `ABORT_ZERO_WRITE_RUNTIME_UNPROVEN`
- `ABORT_RECEIPT_BOUNDARY_UNPROVEN`
- `ABORT_MATERIALIZATION_PACKAGE_INVALID`

Unknown states must never degrade to warning-only execution.

## 13. Repository placement rule

This design document may live in `Kho-serial-OS` because it directly governs
warehouse serial inbound evidence.

Executable provider/network code must not be added to the existing public
pure-control code path merely by:

- expanding static import allowlists;
- weakening public-boundary checks;
- adding credentials;
- embedding Production resource IDs;
- disabling the warehouse sole-mission gate.

A separate architecture/promotion decision is required before executable code
location is chosen.

## 14. Promotion gates before implementation

A future executable adapter issue may not open until an independent promotion
audit has evidence for all of:

1. target-authority registry materialized and read back;
2. dedicated read-only identity materialized;
3. effective-permission proof independently verified;
4. exact five Production surface bindings materialized;
5. serial-universe completeness proof method demonstrated;
6. HOLD-universe completeness proof method demonstrated;
7. actual provider version/capture semantics verified;
8. zero-write runtime enforcement demonstrated;
9. tamper-evident receipt boundary materialized;
10. executable placement does not weaken this repository's four required checks.

Until all ten are evidenced:

`ExecutableAcquisitionAuthorized=False`

## Final state

**EXTERNAL_INBOUND_ACQUISITION_ADAPTER_V0_1 = SPECIFIED_NOT_IMPLEMENTED**

**LiveReadAuthorized = False**

**ExecutableAcquisitionAuthorized = False**

**ProductionWriteAuthorized = False**

**Production writer = HOLD**

**MASTER LIVE unchanged**
