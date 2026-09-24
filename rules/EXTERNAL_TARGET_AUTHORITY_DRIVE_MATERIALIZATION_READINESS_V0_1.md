# EXTERNAL_TARGET_AUTHORITY_DRIVE_MATERIALIZATION_READINESS_V0_1

Status: **HOLD_DRIVE_AUTHORITY_MATERIALIZATION_NOT_READY**

## Purpose

Audit whether the selected restricted Google Drive / Google Workspace
target-authority store is sufficiently specified and externally grounded to
justify a separately authorized materialization action.

This artifact is readiness/governance only.

It does not create a Drive folder, registry record, Production target locator,
credential, permission, provider session, live read, executable acquisition
path, Production write, or MASTER LIVE mutation.

Locked authority state:

- `PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED`
- `LiveReadAuthorized = False`
- `ExecutableAcquisitionAuthorized = False`
- `ProductionWriteAuthorized = False`
- Production writer = `HOLD`
- MASTER LIVE unchanged

## Verdict

**HOLD_DRIVE_AUTHORITY_MATERIALIZATION_NOT_READY**

The selected Drive architecture can now be specified precisely enough for a
future materialization action, but one material prerequisite remains
unresolved:

**no distinct external identity has been independently evidenced for
`TARGET_AUTHORITY_INDEPENDENT_REVIEWER`.**

The target-authority owner must not self-prove the independent read-back event.

Therefore this issue closes the storage/topology/serialization/hash/uniqueness
design gap, but does not authorize Drive materialization yet.

## Evidence reviewed

Reviewed against current main:

- `INBOUND_TARGET_AUTHORITY_REGISTRY_MATERIALIZATION_PLAN_V0_1`
- `PRG01_TARGET_AUTHORITY_EXTERNAL_MATERIALIZATION_READINESS_AUDIT_V0_1`
- `EXTERNAL_TARGET_AUTHORITY_STORE_SELECTION_V0_1`
- `EXTERNAL_TARGET_AUTHORITY_STORE_SELECTION_REVIEW_V0_1`
- active repository ruleset;
- current Drive service capabilities;
- current Shared Drive availability.

Observed:

- the selected external service class remains Google Drive / Workspace;
- no Shared Drive is currently available to the connected Drive account;
- current PHÚ OS journal/checkpoint files are ordinary operational evidence and
  are not the target-authority registry;
- no dedicated target-authority container is materialized;
- no registry record or Production target locator is materialized;
- no independent reviewer external identity has been evidenced.

## 1. Exact logical Drive topology

The later materialization action must create one dedicated authority root using
a non-sensitive logical name:

`PRG01_TARGET_AUTHORITY_V1`

Required child containers:

1. `REGISTRY`
2. `LOCATOR`
3. `EVIDENCE`
4. `RECOVERY`

Logical topology:

```text
PRG01_TARGET_AUTHORITY_V1/
  REGISTRY/
  LOCATOR/
  EVIDENCE/
  RECOVERY/
```

The public repository may publish these logical aliases.

The public repository must never publish the actual Drive file/folder IDs of
the locator-bearing boundary.

A generic My Drive root or an existing PHÚ OS journal/checkpoint folder is not a
valid substitute.

## 2. Container roles

### REGISTRY

Authoritative home of canonical
`InboundTargetAuthorityRegistryRecordV1` objects and registry-level lifecycle
state.

It must not contain the actual Production resource locator.

### LOCATOR

Restricted home of canonical `ExternalTargetLocatorV1` objects.

This is the only authority-store area permitted to contain the real Production
resource identity.

### EVIDENCE

Home of:

- approval evidence;
- independent read-back evidence;
- lifecycle-transition evidence;
- uniqueness-check evidence;
- canonical hash recomputation evidence;
- no-public-ID leakage evidence;
- provider revision/version markers.

### RECOVERY

Restricted recovery-only copies and manifests.

A recovery copy is never ACTIVE authority merely because it exists.

## 3. Ownership/admin boundary

The authority root must be owned/administered by the external identity that
fulfills:

`TARGET_AUTHORITY_OWNER`

The public repository must represent this only as a logical authority ref.

Actual account identifiers, emails and Drive IDs remain external.

Because no Shared Drive is currently available, V0.1 must use a dedicated
restricted My Drive hierarchy owned by the designated owner identity.

This limitation must be re-audited if a Shared Drive later becomes available.

## 4. Governance identity model

Required logical roles:

- `TARGET_AUTHORITY_OWNER`
- `TARGET_AUTHORITY_APPROVER`
- `TARGET_AUTHORITY_INDEPENDENT_REVIEWER`

The owner and approver responsibilities may be fulfilled under the existing
governance model, but the independent-review event requires a distinct external
identity from the owner for that evidence event.

Required invariant:

`owner_external_identity != independent_reviewer_external_identity`

The public repository may contain only opaque logical refs for these roles.

### Current evidence

Owner/approver authority is defined at governance level.

However, no distinct external identity has been independently evidenced for
`TARGET_AUTHORITY_INDEPENDENT_REVIEWER`.

Therefore reviewer identity binding is the only material blocker to the
container-creation action.

Blocker:

`HOLD_INDEPENDENT_REVIEWER_IDENTITY_NOT_BOUND`

## 5. Permission matrix

No public or link-wide sharing is permitted.

Target permission design:

| Area | Owner | Approver | Independent reviewer | Other principals |
| --- | --- | --- | --- | --- |
| root | owner/admin | no inherited write requirement | no inherited write requirement | none |
| REGISTRY | write/admin | read | read | none |
| LOCATOR | write/admin | no access by default | read only when needed for locator-hash verification | none |
| EVIDENCE | write/admin | write for approval evidence | write for independent read-back evidence | none |
| RECOVERY | write/admin | no access by default | read only for recovery verification when explicitly required | none |

Permission inheritance must be reviewed after creation.

Any unexpected principal, domain-wide grant, public grant, or anyone-with-link
grant is HOLD.

The later action must capture provider permission read-back before any
authority record is created.

## 6. Canonical registry serialization

Registry records must be stored as raw machine-readable UTF-8 JSON, not as
native Google Docs/Sheets.

Canonical serialization:

- UTF-8;
- no BOM;
- object keys sorted lexicographically;
- compact separators `,` and `:`;
- exact native JSON scalar types;
- explicit `null` for nullable fields;
- no extra undeclared fields;
- no whitespace normalization by the reader;
- no hidden provider metadata included in the hashed payload;
- final hash field excluded from its own hash input.

Canonical hash:

`SHA256(canonical_registry_payload_bytes)`

The stored record and independently retrieved bytes must reproduce the same
hash.

## 7. Canonical locator serialization

`ExternalTargetLocatorV1` must also be raw UTF-8 canonical JSON.

Minimum logical fields:

- `locator_schema_version`
- `locator_ref`
- `provider_class`
- `production_resource_locator`

The actual `production_resource_locator` remains external and must never be
copied into GitHub or journal artifacts.

Canonical locator hash:

`SHA256(canonical_locator_payload_bytes)`

The public boundary may expose only:

- opaque `external_target_locator_ref`;
- lowercase 64-hex `external_target_locator_hash`.

## 8. File naming

Drive object names must not encode Production resource IDs, workbook IDs,
URLs, account IDs, sheet IDs or range IDs.

Permitted logical patterns include opaque IDs such as:

- `TA_<opaque-id>.json`
- `LOC_<opaque-id>.json`
- `EVD_<opaque-id>.json`
- `RCV_<opaque-id>.json`

The filename is not authority.

Authority is determined by canonical content, lifecycle state, hashes,
permissions and independent read-back.

## 9. Lifecycle evidence procedure

Allowed lifecycle:

`DRAFT -> APPROVED -> ACTIVE`

Historical terminal states:

- `REVOKED`
- `SUPERSEDED`

Every lifecycle transition must produce a separate evidence object under
EVIDENCE containing at least:

- opaque evidence ID;
- target-authority ID;
- previous lifecycle state;
- new lifecycle state;
- pre-transition authority hash;
- post-transition authority hash;
- actor logical authority ref;
- provider revision/version marker where available;
- transition result;
- evidence hash.

No transition object may embed the Production locator.

Unknown or skipped transition = HOLD.

## 10. ACTIVE uniqueness enforcement

Drive itself is not treated as a database uniqueness engine.

Uniqueness must be independently computed over the authoritative REGISTRY
object set.

For one `(environment, logical_target_alias)` pair:

- zero ACTIVE = HOLD when an active authority is required;
- exactly one ACTIVE = eligible for further checks;
- more than one ACTIVE = HOLD.

The uniqueness evaluator must also reject:

- duplicate active hashes;
- conflicting target-authority IDs;
- registry/read-back disagreement;
- an ACTIVE record whose independent read-back state is not PASS.

An optional `active-index.json` may exist only as a derived convenience view.
It is not source-of-truth and cannot override a full registry scan.

## 11. Independent read-back

The independent reviewer must retrieve authoritative objects from Drive itself.

The reviewer must not use:

- owner-supplied in-memory payloads;
- screenshots;
- copied chat text;
- GitHub copies;
- journal copies.

Required read-back:

1. retrieve exact registry object from REGISTRY;
2. retrieve locator object from LOCATOR only if authorized for hash
   recomputation;
3. verify provider revision/version markers where available;
4. recompute locator hash;
5. recompute registry hash;
6. verify schema and exact field types;
7. verify `PRODUCTION_SHADOW`;
8. verify schema/surface binding;
9. verify lifecycle state;
10. scan REGISTRY for ACTIVE uniqueness;
11. write independent evidence to EVIDENCE;
12. return PASS or HOLD only.

Independent reviewer identity must differ from owner identity.

This requirement is not currently evidenced.

## 12. Backup and recovery design

RECOVERY must contain only restricted recovery material.

Required recovery bundle:

- canonical registry record bytes;
- canonical locator bytes;
- evidence objects;
- recovery manifest;
- hashes of every included object;
- provider revision/version markers where available.

Recovery procedure must:

1. restore into a non-authoritative staging location;
2. recompute every object hash;
3. verify registry/locator bindings;
4. scan ACTIVE uniqueness;
5. verify lifecycle evidence;
6. verify permissions;
7. perform independent reviewer read-back;
8. only then permit an explicit authority-restoration decision.

No stale backup may silently replace the current locator.

## 13. Evidence-retention model

EVIDENCE is logically separate from REGISTRY and LOCATOR.

Evidence objects must be append-oriented and hash-bound.

Required evidence categories:

- `APPROVAL`
- `READBACK`
- `UNIQUENESS`
- `LIFECYCLE`
- `PERMISSION_READBACK`
- `PUBLIC_LEAKAGE_CHECK`
- `RECOVERY_VALIDATION`

Drive revision/history strengthens auditability but is not treated as immutable
authority.

## 14. No-public-ID leakage test

Before any PRG-01 promotion review, run a public-boundary audit across:

- public GitHub repository content and history added by the materialization
  workflow;
- public issue/PR text;
- public control catalog;
- operational journal summaries intended to be broadly visible.

The audit must reject:

- Drive folder/file IDs that resolve the LOCATOR boundary;
- Production resource/workbook IDs;
- Production URLs;
- provider account identifiers that resolve the target;
- sheet/range IDs;
- raw Production metadata;
- credentials/tokens.

Only opaque refs and non-sensitive hashes may cross the public boundary.

## 15. Provider Production-data dependency

The Drive authority-store materialization sequence does not require reading
warehouse Production data.

Container creation, permission establishment, schema serialization, role
binding, hash procedures and evidence layout are control-plane operations.

The actual Production resource locator may only be introduced in a later
separately authorized locator-materialization action.

No provider warehouse payload is required for container-only materialization.

## 16. Materialization phases

A later authorized action must be split.

### Phase A — authority boundary materialization

Allowed only after reviewer identity binding closes.

May create:

- root container;
- REGISTRY;
- LOCATOR;
- EVIDENCE;
- RECOVERY;
- minimum permissions;
- permission read-back evidence.

Must not create:

- real Production locator;
- ACTIVE authority record;
- provider runtime identity;
- live read.

### Phase B — locator/record materialization

Requires a separate authorization after Phase A read-back.

May then materialize the locator and DRAFT registry record under the already
validated boundary.

This audit does not authorize either phase.

## 17. Readiness matrix

| Requirement | Design state | External evidence state | Verdict |
| --- | --- | --- | --- |
| exact topology | specified | not materialized | PASS FOR READINESS DESIGN |
| owner/admin boundary | specified | owner role exists logically | PASS FOR READINESS DESIGN |
| owner/approver model | specified | governance exists | PASS FOR READINESS DESIGN |
| independent reviewer identity | specified | distinct external identity not evidenced | HOLD |
| permission matrix | specified | not materialized | PASS FOR READINESS DESIGN |
| registry serialization | specified | not materialized | PASS FOR READINESS DESIGN |
| locator serialization | specified | not materialized | PASS FOR READINESS DESIGN |
| deterministic hashing | specified | no materialized object yet | PASS FOR READINESS DESIGN |
| ACTIVE uniqueness | specified | no registry set yet | PASS FOR READINESS DESIGN |
| lifecycle evidence | specified | no record yet | PASS FOR READINESS DESIGN |
| independent read-back path | specified | cannot execute without reviewer identity | HOLD |
| backup/recovery | specified | not materialized | PASS FOR READINESS DESIGN |
| evidence-retention model | specified | not materialized | PASS FOR READINESS DESIGN |
| public leakage control | specified | public repo checks active | PASS FOR READINESS DESIGN |
| Production-data independence | specified | no live read required | PASS |
| separate materialization authorization | required | preserved | PASS |

## 18. Smallest next safe step

Do not create Drive authority folders yet.

The smallest missing prerequisite is:

**`TARGET_AUTHORITY_INDEPENDENT_REVIEWER_IDENTITY_BINDING_V0_1`**

That step must:

1. bind one distinct external identity to
   `TARGET_AUTHORITY_INDEPENDENT_REVIEWER`;
2. prove it differs from the owner external identity;
3. define the exact minimum Drive permission set it will receive;
4. prohibit owner self-read-back;
5. retain only an opaque reviewer authority ref in public GitHub;
6. keep actual email/account identifiers external;
7. require no Production-data read;
8. change no permission yet.

Only after that binding is reviewed may a separately authorized Phase A Drive
authority-boundary creation action be considered.

## Final state

**Drive materialization readiness =
`HOLD_DRIVE_AUTHORITY_MATERIALIZATION_NOT_READY`**

**Resolved design areas = topology, container roles, permission matrix,
serialization, hashing, lifecycle evidence, uniqueness, read-back procedure,
backup/recovery, evidence retention, public leakage control.**

**Remaining blocker =
`HOLD_INDEPENDENT_REVIEWER_IDENTITY_NOT_BOUND`**

**PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED**

**LiveReadAuthorized = False**

**ExecutableAcquisitionAuthorized = False**

**ProductionWriteAuthorized = False**

**Production writer = HOLD**

**MASTER LIVE unchanged**
