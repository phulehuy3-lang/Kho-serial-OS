# INBOUND_TARGET_AUTHORITY_REGISTRY_MATERIALIZATION_PLAN_V0_1

Status: **NON-LIVE MATERIALIZATION PLAN — PRG-01 REMAINS HOLD**

## Purpose

Define the exact non-live plan required to materialize the external
target-authority registry used by the future inbound read-only acquisition
boundary.

This artifact is planning/governance only.

It does not create a Production registry record, resolve a Production target,
store a Production resource identifier, call a provider, create a credential,
change permission, perform a live read, or authorize executable acquisition.

Locked authority state:

- `LiveReadAuthorized = False`
- `ExecutableAcquisitionAuthorized = False`
- `ProductionWriteAuthorized = False`
- Production writer = `HOLD`
- PRG-01 = `HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED`

## 1. Dependency role

PRG-01 is the dependency root for later runtime evidence.

The following gates cannot be defensibly materialized before one canonical
target authority exists:

- PRG-02 dedicated read-only identity binding;
- PRG-03 effective-permission proof;
- PRG-04 exact five Production surface bindings.

Therefore this plan must complete before those remediation tracks are opened.

## 2. Registry location boundary

The authoritative registry must exist outside this public repository.

GitHub may contain only:

- registry schema/specification;
- opaque authority identifiers;
- lifecycle rules;
- canonical hashing rules;
- review procedure;
- evidence checklist;
- hashes/references that reveal no Production resource identity.

GitHub must not contain:

- workbook/resource ID;
- target URL;
- sheet ID;
- range ID;
- credential locator;
- secret/token;
- provider account identifier that directly resolves the Production target;
- raw Production metadata.

## 3. Canonical registry record

Logical record type:

`InboundTargetAuthorityRegistryRecordV1`

Required fields:

### Identity

- `target_authority_id`
- `environment`
- `logical_target_alias`

### Warehouse contract binding

- `warehouse_schema_version`
- `surface_registry_id`
- `surface_registry_hash`

### External target locator binding

- `external_target_locator_ref`
- `external_target_locator_hash`

These two fields are opaque references only.

The external locator object itself must remain outside GitHub and may contain
the actual Production resource identity.

### Governance roles

- `owner_authority_ref`
- `approver_authority_ref`
- `independent_reviewer_authority_ref`

These are logical authority references only. They must not contain personal
email addresses, account IDs, or credentials in this public repository.

### Lifecycle

- `lifecycle_state`
- `supersedes_authority_id` or `None`
- `activation_epoch_ref`
- `revocation_epoch_ref` or `None`

Epoch references are opaque external evidence references, not caller timestamps
used as authority.

### Read-back

- `independent_readback_state`
- `independent_readback_evidence_id`
- `independent_readback_evidence_hash`

### Integrity

- `record_schema_version`
- `authority_record_hash`

## 4. Exact field rules

Every text identifier must be:

- native text;
- non-blank;
- free of leading/trailing whitespace;
- stable after approval;
- opaque where the field is an external reference.

Every hash must be:

- lowercase SHA-256;
- exactly 64 hexadecimal characters.

No silent coercion, trimming, case-folding, fallback identifier or default
value is allowed.

## 5. Fixed environment

The only permitted environment for this registry record is:

`PRODUCTION_SHADOW`

The registry plan does not define or authorize:

- `PRODUCTION_WRITE`;
- write-capable target authority;
- caller-controlled environment switching.

Any other environment is fail-closed.

Blocker:

`HOLD_TARGET_AUTHORITY_ENVIRONMENT_INVALID`

## 6. Lifecycle model

Allowed lifecycle states:

1. `DRAFT`
2. `APPROVED`
3. `ACTIVE`
4. `REVOKED`
5. `SUPERSEDED`

### DRAFT

A proposed authority record under preparation.

It cannot be resolved by the acquisition boundary.

### APPROVED

Governance review has accepted the record content, but it is not yet the active
authority.

It cannot be used by an acquisition runtime.

### ACTIVE

The only lifecycle state eligible for future target resolution.

ACTIVE does not authorize live read by itself.

### REVOKED

The authority must never resolve again.

### SUPERSEDED

A replacement authority exists or is being activated under a controlled
transition.

The superseded record remains immutable historical evidence.

## 7. Uniqueness constraints

At any point, the external registry must enforce:

- one `target_authority_id` -> one immutable record version;
- no duplicate active record hash;
- at most one ACTIVE record for one
  `(environment, logical_target_alias)` pair;
- one ACTIVE record must bind exactly one
  `surface_registry_id/surface_registry_hash`;
- one ACTIVE record must bind exactly one
  `warehouse_schema_version`;
- an ACTIVE record cannot have
  `independent_readback_state != PASS`.

Zero ACTIVE matches = HOLD.

More than one ACTIVE match = HOLD.

Blockers:

- `HOLD_TARGET_AUTHORITY_MISSING`
- `HOLD_TARGET_AUTHORITY_DUPLICATE_ACTIVE`

## 8. Opaque public reference scheme

The public repository may reference a future external record only through:

- `target_authority_id`;
- `authority_record_hash`;
- `surface_registry_id`;
- `surface_registry_hash`;
- independent read-back evidence ID/hash.

These references must not be reversible into a Production workbook/resource
identity from repository content alone.

The actual locator remains in an external authority store under separate access
control.

## 9. Governance roles

### Owner

Logical role:

`TARGET_AUTHORITY_OWNER`

Responsibilities:

- maintains proposed record content;
- confirms intended warehouse target purpose;
- initiates lifecycle transition request;
- cannot self-prove independent read-back.

### Approver

Logical role:

`TARGET_AUTHORITY_APPROVER`

Responsibilities:

- reviews schema/surface binding;
- approves or rejects the proposed authority record;
- cannot silently modify the approved content after approval.

### Independent reviewer

Logical role:

`TARGET_AUTHORITY_INDEPENDENT_REVIEWER`

Responsibilities:

- independently reads back the materialized external record;
- recomputes the canonical record hash;
- verifies lifecycle and uniqueness state;
- records PASS/HOLD evidence.

The same external identity may not satisfy owner and independent-review
responsibilities in one evidence event unless a later governance decision
explicitly permits and justifies it.

This plan does not assign actual people/accounts.

## 10. Canonical record hash

`authority_record_hash` must be deterministic SHA-256 over canonical JSON.

The canonical payload must include all authority-bearing fields except
`authority_record_hash` itself.

Required hashing properties:

- UTF-8 encoding;
- sorted object keys;
- compact separators;
- exact native scalar types;
- explicit `None` for nullable fields;
- no timestamps generated by the hashing function;
- no hidden provider metadata;
- no mutable display labels outside the declared schema.

Any content change must produce a different record hash.

The external materialization procedure must preserve both:

- the canonical payload used for hashing;
- the resulting hash.

## 11. Warehouse schema binding

Every target authority record must bind exactly one:

`warehouse_schema_version`

The value must refer to a separately reviewed warehouse schema contract.

A future acquisition runtime must HOLD when:

- observed schema differs;
- schema version is missing;
- schema compatibility is inferred rather than explicitly approved.

Blocker:

`HOLD_TARGET_SCHEMA_BINDING_INVALID`

## 12. Exact five-surface registry binding

Every target authority record must bind one exact:

- `surface_registry_id`
- `surface_registry_hash`

The referenced registry must represent exactly:

1. `INBOUND_SOURCE_RECORD`
2. `ACTIVE_SERIAL_INTERVAL_UNIVERSE`
3. `INBOUND_DERIVED_QUERY_PROJECTION`
4. `INBOUND_QUERY_FORMULA_ANCHOR`
5. `ACTIVE_HOLD_INTERVAL_UNIVERSE`

The target-authority record must not embed Production sheet/range identifiers
in GitHub.

A future external surface registry may resolve those details outside GitHub.

Blocker:

`HOLD_TARGET_SURFACE_REGISTRY_BINDING_INVALID`

## 13. External target locator

The actual Production resource identity must be stored in a separate external
locator object.

Required logical object:

`ExternalTargetLocatorV1`

The target-authority record may contain only:

- `external_target_locator_ref`
- `external_target_locator_hash`

The external locator must be governed so that:

- one locator ref resolves one exact Production target;
- locator changes create a new locator hash;
- locator replacement cannot silently preserve an old authority hash;
- a locator cannot be supplied directly by a caller at runtime;
- locator access is auditable.

This plan does not define or store the real locator.

## 14. Materialization sequence

A later separately authorized external action must follow this order:

1. create the external registry container;
2. establish access-control ownership for the registry;
3. create the external target locator object;
4. compute locator hash;
5. prepare one DRAFT target-authority record;
6. bind warehouse schema version;
7. bind exact five-surface registry ID/hash;
8. bind logical governance authority refs;
9. compute canonical authority-record hash;
10. perform owner review;
11. perform approver review;
12. transition DRAFT -> APPROVED if accepted;
13. independently read back the exact external record;
14. recompute authority-record hash from read-back content;
15. evaluate uniqueness constraints;
16. record read-back evidence ID/hash;
17. only after read-back PASS may an authorized lifecycle action move
    APPROVED -> ACTIVE;
18. independently read back ACTIVE state;
19. assemble the PRG-01 evidence bundle;
20. stop.

No provider data read is required or allowed merely to create this registry.

## 15. Independent read-back procedure

Independent read-back must not reuse the owner's proposed in-memory object as
evidence.

It must:

1. retrieve the materialized external registry record from its authoritative
   store;
2. verify exact `target_authority_id`;
3. verify environment = `PRODUCTION_SHADOW`;
4. verify logical target alias;
5. verify warehouse schema binding;
6. verify five-surface registry ID/hash;
7. verify external locator ref/hash;
8. verify lifecycle state;
9. verify governance role refs;
10. recompute canonical record hash;
11. compare recomputed hash with stored hash;
12. verify uniqueness constraints against the authoritative registry;
13. emit independent evidence ID/hash;
14. return only PASS or HOLD.

A screenshot, copied note, or owner assertion alone is insufficient.

## 16. PRG-01 evidence bundle

PRG-01 may move from:

`HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED`

to:

`READY_FOR_REVIEW`

only when all of the following evidence exists:

- authoritative registry container evidence;
- access-control ownership evidence;
- external locator object evidence ID/hash;
- one target-authority record ID/hash;
- lifecycle = ACTIVE;
- environment = PRODUCTION_SHADOW;
- warehouse schema version binding;
- exact five-surface registry ID/hash binding;
- owner authority reference;
- approver authority reference;
- independent reviewer authority reference;
- independent read-back state = PASS;
- independent read-back evidence ID/hash;
- uniqueness check PASS;
- canonical hash recomputation PASS;
- evidence that public GitHub content contains no Production resource ID/URL.

READY_FOR_REVIEW is not PRG-01 PASS.

A separate independent review must consume the evidence bundle.

## 17. Fail-closed states

Required blockers:

- `HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED`
- `HOLD_TARGET_AUTHORITY_ENVIRONMENT_INVALID`
- `HOLD_TARGET_AUTHORITY_MISSING`
- `HOLD_TARGET_AUTHORITY_DUPLICATE_ACTIVE`
- `HOLD_TARGET_AUTHORITY_NONACTIVE`
- `HOLD_TARGET_AUTHORITY_HASH_MISMATCH`
- `HOLD_TARGET_AUTHORITY_READBACK_FAILED`
- `HOLD_TARGET_SCHEMA_BINDING_INVALID`
- `HOLD_TARGET_SURFACE_REGISTRY_BINDING_INVALID`
- `HOLD_TARGET_LOCATOR_BINDING_INVALID`
- `HOLD_TARGET_AUTHORITY_GOVERNANCE_INVALID`
- `HOLD_TARGET_AUTHORITY_EVIDENCE_INCOMPLETE`

Unknown state is HOLD.

No blocker may degrade to warning-only promotion.

## 18. External actions requiring separate human authorization

This plan does not authorize these actions:

- creating the external authority registry;
- creating the external target locator;
- recording a real Production resource ID;
- assigning external owner/approver/reviewer accounts;
- activating a registry record;
- revoking/superseding a registry record;
- granting any system access;
- creating any read-only runtime identity;
- creating/changing provider permissions.

Each such action must occur outside this planning issue under explicit separate
authorization and evidence capture.

## 19. Promotion review checklist

Before PRG-01 can be reviewed again:

- [ ] external registry exists;
- [ ] registry access-control ownership is evidenced;
- [ ] locator object exists outside GitHub;
- [ ] locator hash independently reproducible;
- [ ] one authority record exists;
- [ ] environment is exactly PRODUCTION_SHADOW;
- [ ] schema version binding is exact;
- [ ] five-surface registry binding is exact;
- [ ] lifecycle is ACTIVE;
- [ ] uniqueness check passes;
- [ ] canonical authority hash independently recomputes;
- [ ] independent read-back passes;
- [ ] read-back evidence ID/hash exists;
- [ ] public GitHub boundary re-audit finds no Production locator;
- [ ] four required repository checks remain enforced;
- [ ] LiveReadAuthorized remains False;
- [ ] ExecutableAcquisitionAuthorized remains False;
- [ ] ProductionWriteAuthorized remains False.

## 20. Relationship to later gates

This plan does not close PRG-02, PRG-03 or PRG-04.

If PRG-01 later reaches independently reviewed PASS:

1. plan/materialize a dedicated read-only runtime identity bound to the
   canonical target authority;
2. independently prove effective permissions against the target;
3. materialize exact five Production surface bindings under the target
   authority.

No downstream gate should bypass PRG-01.

## Final state

**INBOUND_TARGET_AUTHORITY_REGISTRY_MATERIALIZATION_PLAN_V0_1 =
PLAN_COMPLETE_NOT_MATERIALIZED**

**PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED**

**LiveReadAuthorized = False**

**ExecutableAcquisitionAuthorized = False**

**ProductionWriteAuthorized = False**

**Production writer = HOLD**

**MASTER LIVE unchanged**
