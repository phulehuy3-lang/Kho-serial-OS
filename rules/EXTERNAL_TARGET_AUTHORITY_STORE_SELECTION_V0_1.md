# EXTERNAL_TARGET_AUTHORITY_STORE_SELECTION_V0_1

Status: **STORE CLASS SELECTED — MATERIALIZATION NOT AUTHORIZED**

## Purpose

Select the external storage boundary required by PRG-01 before any target-authority
registry record or Production target locator is created.

This is a design/decision artifact only.

It does not create a registry, locator, Production identifier, credential,
permission, provider session, live read, executable acquisition path, or writer.

Locked authority state:

- `PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED`
- `LiveReadAuthorized = False`
- `ExecutableAcquisitionAuthorized = False`
- `ProductionWriteAuthorized = False`
- Production writer = `HOLD`
- MASTER LIVE unchanged

## Decision

Selected external store class:

**restricted Google Drive / Google Workspace storage**

Selected architecture:

**one external service class with deliberately separated registry and locator
containers.**

The later materialization design must use a dedicated restricted Drive boundary
for this warehouse authority function. The registry and locator must not be the
same object and must not inherit a public or link-wide permission.

No Drive folder or authority object is created by this decision.

## 1. Registry placement

The future authoritative target-authority registry must live in a dedicated
restricted Drive container outside the public repository.

Registry records must be stored as canonical, machine-readable UTF-8 JSON
objects or an equivalently deterministic raw representation whose exact bytes
can be independently retrieved and hashed.

The registry container may hold:

- canonical target-authority record versions;
- lifecycle evidence;
- registry-wide active-index or equivalent uniqueness evidence;
- independent read-back evidence;
- recovery manifests and checksum bundles.

The public repository may retain only non-reversible opaque IDs, declared
schemas, validation rules and cryptographic hashes.

## 2. Locator placement

The actual Production target locator must live in a separate restricted locator
container/object within the selected Drive service boundary.

The locator object may contain the real Production resource identity.

The public repository and public audit artifacts may contain only:

- `external_target_locator_ref`
- `external_target_locator_hash`

The locator ref must be opaque and must not itself disclose or encode the
Production resource ID or URL.

Registry-reader access does not automatically imply locator-reader access.

## 3. Ownership and administration boundary

The future materialization action must establish an explicit Drive
ownership/admin boundary before any authority record is created.

Required logical roles remain:

- `TARGET_AUTHORITY_OWNER`
- `TARGET_AUTHORITY_APPROVER`
- `TARGET_AUTHORITY_INDEPENDENT_REVIEWER`

The selected store supports account-level and object/folder-level access
control, but this decision does not assign real accounts or change permissions.

Default materialization posture:

- no public access;
- no anyone-with-link access;
- least privilege;
- owner/administrator can create and govern the dedicated containers;
- approver receives only the access needed for approval evidence;
- independent reviewer receives read access sufficient for independent
  retrieval and hash recomputation;
- locator access may be narrower than registry access.

The owner identity must not be reused as the sole independent-review identity
for one evidence event unless a later explicit governance decision justifies
that exception.

## 4. Independent read-back path

Independent read-back must retrieve the materialized record from Drive itself,
not from owner-proposed memory, copied text, screenshots, chat content, or a
public GitHub representation.

Required read-back path:

1. resolve the approved opaque external registry reference outside public
   GitHub;
2. retrieve the exact stored registry object through the selected Drive
   boundary;
3. parse native scalar types without silent coercion;
4. recompute the canonical SHA-256 record hash;
5. verify environment = `PRODUCTION_SHADOW`;
6. verify exact warehouse schema binding;
7. verify exact five-surface registry ID/hash;
8. verify locator ref/hash;
9. verify lifecycle state;
10. evaluate registry-wide ACTIVE uniqueness;
11. emit a separate read-back evidence object with evidence ID/hash;
12. return PASS or HOLD only.

No provider Production data read is required for this procedure.

## 5. History and tamper-evidence model

Google Drive is not treated as an intrinsically immutable ledger.

Therefore the selected design requires layered tamper evidence:

- Drive revision/history metadata where available;
- deterministic canonical JSON;
- SHA-256 hash for every authority-bearing record;
- SHA-256 hash for every locator object;
- independent read-back hash recomputation;
- lifecycle evidence objects;
- public storage of only opaque authority/evidence IDs and non-sensitive hashes
  when later authorized by the relevant governance step.

A later public hash anchor may prove drift without exposing the Production
locator.

Hash equality does not by itself prove authority; it proves content identity
only when the independently retrieved external object is authoritative.

## 6. ACTIVE uniqueness support

The storage provider alone is not considered a database uniqueness constraint.

At-most-one ACTIVE authority for one
`(environment, logical_target_alias)` pair must therefore be enforced by the
materialization/read-back governance layer.

A later materialization procedure must fail closed when:

- zero ACTIVE records exist where one is required;
- more than one ACTIVE record exists;
- the active index and canonical record set disagree;
- the independently recomputed registry view differs from approval evidence.

No lifecycle transition to ACTIVE may occur before the independent uniqueness
check passes.

## 7. Backup and recovery

The future store must support recovery without promoting a backup copy into
authority merely because it exists.

Required recovery expectation:

- retain canonical record bytes and hashes;
- retain locator bytes and hash separately;
- retain lifecycle/read-back evidence;
- preserve provider revision/history where available;
- maintain a restricted backup copy or exported recovery bundle under a
  separately identified recovery reference;
- after recovery, recompute all hashes and ACTIVE uniqueness before authority is
  restored;
- never use a stale backup locator silently.

A backup is evidence/recovery material, not an ACTIVE authority by itself.

## 8. Evidence-retention location

Independent read-back and lifecycle evidence must remain in the same restricted
external service class but in a logically separate evidence area.

Evidence retention must be capable of storing:

- evidence ID;
- evidence hash;
- record hash observed;
- locator hash observed;
- registry uniqueness result;
- lifecycle state observed;
- reviewer authority reference;
- provider revision/version marker where available.

Raw Production warehouse payloads are not required for PRG-01 store
materialization and must not be collected merely to satisfy this gate.

## 9. Opaque public reference scheme

Future public references must be non-reversible identifiers.

Permitted public forms include:

- `target_authority_id`;
- `authority_record_hash`;
- `surface_registry_id`;
- `surface_registry_hash`;
- opaque read-back evidence ID/hash;
- opaque external locator ref/hash.

Prohibited public content includes:

- Drive file/folder IDs that directly resolve the Production locator;
- Production workbook/resource ID;
- Production URL;
- provider account identity that directly resolves the target;
- sheet/range identifiers;
- credentials or tokens;
- raw Production metadata.

## 10. Candidate assessment

### Candidate A — restricted Google Drive / Workspace store

**Selected.**

Strengths:

- already used as an external evidence/checkpoint surface for PHÚ OS operations;
- current searched operational artifacts are not publicly shared;
- supports separated objects/containers and granular sharing;
- supports independent retrieval without executable warehouse acquisition;
- supports provider revision/history metadata;
- supports deterministic raw-object retrieval suitable for hash recomputation;
- can keep Production locator identities completely outside public GitHub;
- supports a single service boundary while still separating registry, locator
  and evidence access.

Limitations:

- no Shared Drive is currently available to the connected account;
- provider storage is not inherently immutable;
- uniqueness is not provider-enforced;
- role separation is ineffective until distinct external identities are
  actually assigned;
- retention/recovery discipline must be materialized and independently tested.

These limitations are explicit blockers for later materialization evidence, not
reasons to prefer a weaker public/private Git repository boundary.

### Candidate B — private Git repository

**Not selected.**

Strengths:

- deterministic blobs and commits;
- strong diff/history semantics;
- straightforward cryptographic content identity;
- CI could theoretically enforce ACTIVE uniqueness.

Observed limitation under the current account/repository conditions:

- the existing private-repository candidate does not have usable repository
  ruleset enforcement under the current GitHub plan;
- a ruleset read for the private candidate is rejected unless the account is
  upgraded or the repository is made public.

Additional design risk:

- Production locator identities committed to Git history are difficult to
  remove after rotation or accidental exposure;
- placing locator and registry governance in GitHub increases coupling to the
  same provider used for the public specification repository;
- public conversion is categorically unacceptable for locator-bearing content.

Therefore the private-repository candidate is weaker for the present PRG-01
boundary.

### Candidate C — private object store or another authorized external system

**Not selected for V0.1.**

No separately authorized object-store system was independently evidenced during
the readiness audit.

Introducing a new provider solely for PRG-01 would broaden operational scope,
credential management, backup design and access governance without a current
need.

A later version may supersede this decision if independently evidenced
requirements justify that change.

## 11. Why one service class with separated containers is the minimum boundary

A single mixed registry/locator object would violate least privilege and make
independent registry read-back unnecessarily reveal the Production target.

Two unrelated external providers would improve provider separation but add
credential, recovery and operational complexity before PRG-01 is materialized.

The selected compromise is therefore:

- one restricted Drive/Workspace service boundary;
- separate registry container;
- separate locator container;
- separate evidence area;
- distinct permissions where required;
- cryptographic hashes binding the objects;
- only opaque refs/hashes crossing into public GitHub.

This is the smallest architecture that satisfies the current PRG-01 design
requirements without expanding live acquisition scope.

## 12. Current external evidence

Selection evidence establishes only store-class suitability.

Observed Drive metadata shows:

- existing PHÚ OS operational journal/checkpoint artifacts are stored outside
  the public repository;
- searched relevant operational artifacts are not broadly shared;
- no current target-authority registry or target locator was found;
- no Shared Drive is presently available through the connected account.

Therefore existing journal/checkpoint files must not be relabeled as the
target-authority store.

A dedicated boundary still has to be materialized later.

## 13. Actions requiring separate authorization

This selection does not authorize:

- creation of the dedicated Drive authority folder/container;
- creation of the registry object;
- creation of the locator object;
- storage of a real Production target ID/URL;
- assignment of real owner/approver/reviewer identities;
- any permission change;
- lifecycle activation;
- creation of credentials;
- provider Production read;
- executable acquisition implementation;
- Production write;
- MASTER LIVE mutation.

Each remains a separate external action with its own evidence and review.

## 14. Materialization preconditions after this selection

Before any external creation action, a separate readiness/action artifact must
bind at least:

1. exact dedicated Drive container design;
2. registry/locator/evidence separation;
3. admin/owner identity boundary;
4. proposed approver/reviewer access model;
5. canonical record serialization;
6. canonical locator serialization;
7. hash procedure;
8. ACTIVE uniqueness procedure;
9. read-back procedure;
10. backup/recovery procedure;
11. evidence-retention procedure;
12. no-public-ID leakage test.

Only then may a separately authorized external materialization action be
considered.

## Verdict

**EXTERNAL_TARGET_AUTHORITY_STORE_SELECTION_V0_1 =
SELECTED_RESTRICTED_GOOGLE_DRIVE_WORKSPACE**

**Store-selection decision = COMPLETE**

**External registry materialization = NOT PERFORMED**

**Target locator materialization = NOT PERFORMED**

**PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED**

**LiveReadAuthorized = False**

**ExecutableAcquisitionAuthorized = False**

**ProductionWriteAuthorized = False**

**Production writer = HOLD**

**MASTER LIVE unchanged**

Next safe step:

**`EXTERNAL_TARGET_AUTHORITY_DRIVE_MATERIALIZATION_READINESS_V0_1`**
