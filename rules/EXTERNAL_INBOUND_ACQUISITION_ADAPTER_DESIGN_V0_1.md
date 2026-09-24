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


---

## READ_ONLY_RUNTIME_IDENTITY_SELECTION_V0_1 — 2026-09-25

Issue: #94

Status:

**`PASS_READONLY_RUNTIME_IDENTITY_SELECTION_DESIGN`**

This section selects the canonical identity class for PRG-02. It is design-only.
It does not create an identity, credential, permission, provider session, live
read, or Production write path.

### 1. Canonical provider identity class

The only permitted PRG-02 runtime principal class is:

`GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT`

The principal represents the acquisition workload, not a human operator.

Prohibited substitutes:

- operator/personal Google account;
- shared human account;
- generic Workspace user used interactively;
- group identity as runtime principal;
- service account with domain-wide delegation;
- service account impersonating a Workspace user;
- any writer-capable fallback identity.

### 2. Authentication posture

Authentication policy:

`KEYLESS_ONLY`

User-managed service-account private keys are prohibited in v0.1.

Permitted future authentication mechanisms are limited to provider-managed
short-lived credentials:

- attached service-account identity when the runtime is hosted on an approved
  Google Cloud workload; or
- Workload Identity Federation followed by service-account impersonation when
  the approved runtime is external to Google Cloud.

The selected authentication path is a deployment decision and must be recorded
before executable acquisition is authorized.

Long-lived JSON/P12 keys, downloaded private keys and embedded secrets are not
permitted.

### 3. Domain-wide delegation and user impersonation

Locked values:

- `domain_wide_delegation = PROHIBITED`
- `workspace_user_impersonation = PROHIBITED`

The runtime identity must never obtain authority by impersonating an owner,
administrator or warehouse operator.

### 4. Identity authority record

A future private external identity authority store must hold exactly one
canonical record with at least:

- `identity_authority_id`
- `provider_class = GOOGLE_CLOUD`
- `identity_class = GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT`
- `environment = PRODUCTION_SHADOW`
- `target_authority_id`
- `target_authority_hash`
- `principal_locator_ref`
- `authentication_policy = KEYLESS_ONLY`
- `domain_wide_delegation = PROHIBITED`
- `workspace_user_impersonation = PROHIBITED`
- `user_managed_key_state = PROHIBITED`
- `credential_boundary_ref`
- `owner_authority_ref`
- `custodian_authority_ref`
- `rotation_authority_ref`
- `revocation_authority_ref`
- `independent_reviewer_authority_ref`
- `effective_permission_proof_state = PENDING`
- `independent_readback_state`
- `lifecycle_state`
- `identity_record_hash`

The actual service-account email, project identifier and provider locator remain
outside GitHub.

Only opaque IDs and non-sensitive hashes may cross the public boundary.

### 5. Lifecycle

Allowed lifecycle states:

1. `DRAFT`
2. `APPROVED`
3. `MATERIALIZED`
4. `REVOKED`
5. `SUPERSEDED`

Rules:

- DRAFT and APPROVED are non-runtime states;
- MATERIALIZED proves identity existence/read-back only;
- MATERIALIZED does not prove effective target permission;
- REVOKED cannot return to MATERIALIZED;
- replacement requires a new identity authority ID;
- at most one non-revoked canonical PRG-02 identity may be designated for one
  target/environment at a time.

### 6. Governance authorities

Logical authorities:

- owner: `READONLY_RUNTIME_IDENTITY_OWNER`
- custodian: `READONLY_RUNTIME_IDENTITY_CUSTODIAN`
- rotation: `READONLY_RUNTIME_IDENTITY_ROTATION_AUTHORITY`
- revocation: `READONLY_RUNTIME_IDENTITY_REVOCATION_AUTHORITY`
- independent reviewer:
  `READONLY_RUNTIME_IDENTITY_INDEPENDENT_REVIEWER`

For the current solo-operator model:

`human_separation_of_duties = false`

No false human separation is asserted. Independent review is evidence-path
separation: fresh provider reacquisition, deterministic hashing and read-back
rather than a claim that a second human reviewed the action.

### 7. Credential issuance and storage boundary

Credential policy:

`NO_PERSISTED_PRIVATE_CREDENTIAL`

Requirements:

- no service-account key creation;
- no credential file in GitHub;
- no credential file in warehouse Drive;
- no token in logs, evidence packages or operational journal;
- short-lived access tokens are runtime-memory-only;
- federation/attached-identity configuration is held outside warehouse business
  data and outside this public repository;
- secret-bearing fallback authentication is prohibited.

Any future requirement for a user-managed key invalidates this v0.1 selection
and requires a new design review.

### 8. Target binding

The identity authority record binds to the existing ACTIVE target authority by
opaque target authority ID/hash.

Identity materialization must not itself grant target access.

A later separately authorized reader-grant action may grant only the exact
canonical target resource:

`Drive ACL role = reader`

No parent-folder grant, domain grant, group grant, wildcard discovery or
domain-wide delegation is permitted.

The reader grant is not PRG-03 proof. PRG-03 must independently verify the
effective permission state after the grant.

### 9. Effective permission proof remains separate

PRG-03 remains mandatory and separate from PRG-02.

Future PRG-03 evidence must independently prove, against the exact canonical
target:

- reader access exists for the dedicated service account;
- no writer/editor role;
- no resource-creation capability through the target boundary;
- no share/permission-management capability;
- no inherited or alternative write-capable path;
- no write-capable fallback identity;
- approved read-only API scope/capability set only.

A configuration flag, screenshot or declared `read_only=true` is insufficient.

### 10. Independent identity read-back

A PRG-02 materialization action may close only after a distinct read-back event
reacquires provider state and verifies:

- exactly one selected service-account principal exists;
- principal identity matches the private authority locator;
- principal is not disabled;
- no user-managed service-account key exists;
- domain-wide delegation is absent;
- no Workspace user impersonation is configured;
- identity authority target binding matches the current target authority
  ID/hash;
- lifecycle and independent-readback state are coherent;
- deterministic identity-record hash recomputes exactly.

This event must not read warehouse Production payload.

### 11. Deterministic record hash

`identity_record_hash` is SHA-256 over canonical UTF-8 JSON of the complete
identity authority record excluding only the hash field itself.

Rules:

- keys sorted lexicographically;
- exact native booleans;
- no default insertion;
- no pseudo-booleans;
- no provider secret or credential material;
- any unknown required field -> HOLD.

### 12. Evidence required before materialization action

A later materialization action is not authorized by this design.

A separate readiness audit must confirm at minimum:

1. current target authority remains ACTIVE/PASS and unique;
2. canonical identity class remains
   `GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT`;
3. a private identity authority store/location is selected;
4. owner/custodian/rotation/revocation authorities are bound;
5. keyless authentication path is selected for the intended runtime placement;
6. key creation remains prohibited;
7. domain-wide delegation remains prohibited;
8. exact provider read-back method is available;
9. no target permission change occurs during identity creation;
10. four repository checks remain required.

Allowed future readiness verdicts:

- `PASS_FOR_READONLY_IDENTITY_MATERIALIZATION_ACTION_ONLY`
- `HOLD_READONLY_IDENTITY_MATERIALIZATION_NOT_READY`

Neither verdict authorizes live access.

### 13. Fail-closed states

Canonical blockers include:

- `HOLD_IDENTITY_CLASS_DRIFT`
- `HOLD_IDENTITY_AUTHORITY_UNBOUND`
- `HOLD_KEYLESS_AUTH_PATH_UNRESOLVED`
- `HOLD_USER_MANAGED_KEY_PRESENT`
- `HOLD_DOMAIN_WIDE_DELEGATION_PRESENT`
- `HOLD_USER_IMPERSONATION_PRESENT`
- `HOLD_IDENTITY_READBACK_FAILED`
- `HOLD_TARGET_AUTHORITY_DRIFT`
- `HOLD_EFFECTIVE_PERMISSION_NOT_MATERIALIZED`

Unknown identity/security state is HOLD, never warning-only.

### 14. Design decision

Selected identity:

**`GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT / KEYLESS_ONLY`**

PRG-02 state after this design:

**`DESIGN_SELECTED_NOT_MATERIALIZED`**

Next safe step:

**`READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_ACTION_READINESS_V0_1`**

Locked invariants remain:

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD
- no credential creation
- no permission change
- no live provider call
- MASTER LIVE unchanged
