# TARGET_AUTHORITY_DRAFT_TO_APPROVED_LIFECYCLE_READINESS_V0_1

Status: **PASS_FOR_DRAFT_TO_APPROVED_LIFECYCLE_ACTION_ONLY**

## Purpose

Audit whether the current verified DRAFT target-authority record is ready for a
separately authorized DRAFT -> APPROVED lifecycle action.

This artifact is readiness-only.

It does not modify the current DRAFT record, locator, provider permissions,
runtime identity, Production target, or MASTER LIVE.

## Verdict

**`PASS_FOR_DRAFT_TO_APPROVED_LIFECYCLE_ACTION_ONLY`**

The current DRAFT state remains intact and the transition protocol is now
specified sufficiently to open one separately authorized lifecycle action.

This verdict does not perform the transition.

## Current public-safe authority state

Target authority:

`TA1_d597fd30cfeeefc01ca9d28f71a98e0f`

Locator ref:

`LOC1_a18c6d759273701cfcf0942b505409af`

Current DRAFT authority-record hash:

`6990f08a39a2087986c8845a2549a381dbd4dba9f442d55f7caa66edc3647cc4`

Locator hash:

`91e8b5c59e6c1a9d299badc1edddc97d0c24859229a8661760504c195af9cd07`

Logical alias:

`HCM_SERIAL_MASTER_PRIMARY`

Environment:

`PRODUCTION_SHADOW`

Current lifecycle:

`DRAFT`

Current independent read-back state:

`PENDING`

Current ACTIVE count:

`0`

## 1. Fresh provider read-back

Verdict: **PASS**

Fresh provider retrieval re-acquired the current private locator and DRAFT
record from the external authority boundary.

Observed:

- REGISTRY contains exactly one current authority object;
- LOCATOR contains exactly one current locator object;
- current locator is private and owner-only;
- current record is private and owner-only;
- current Production-shadow target resolves exactly once;
- target remains private and owner-only;
- RECOVERY retains the five historical `FAILED_BOM_*` objects.

No Production worksheet payload was read.

## 2. Byte and hash integrity

Verdict: **PASS**

Fresh current bytes show:

- locator UTF-8 BOM = false;
- authority-record UTF-8 BOM = false;
- locator SHA-256 recomputes exactly to the reviewed locator hash;
- authority-record canonical hash recomputes exactly when
  `authority_record_hash` is excluded from hash input.

The earlier BOM HOLD/remediation/PASS evidence chain remains present.

## 3. Contract binding integrity

Verdict: **PASS**

Current DRAFT record still binds exactly:

- `warehouse_schema_version = WAREHOUSE_INBOUND_SCHEMA_V1`;
- schema SHA-256
  `75aff780d0caa1050e81e9cc913a501ccb54767c0706622763d5f1e4d34552c1`;
- `surface_registry_id = SR1_HCM_SERIAL_INBOUND_V1`;
- surface-registry SHA-256
  `d06d7297abcc460b3672e9ad4280f4bc5ca309e73933d5c22fae64048b30ca9a`;
- environment = `PRODUCTION_SHADOW`;
- logical alias = `HCM_SERIAL_MASTER_PRIMARY`;
- exact opaque locator ref/hash.

Current main remains protected by all four required checks.

## 4. Lifecycle versioning decision

Verdict: **PASS FOR ACTION DESIGN**

The DRAFT -> APPROVED action must use:

**one current REGISTRY object per `target_authority_id` plus a mandatory
copy-before-mutate lifecycle snapshot in private EVIDENCE.**

The transition must not create a second current REGISTRY object for the same
`target_authority_id`.

The transition must not delete or overwrite DRAFT history before a separately
stored exact snapshot is created and freshly verified.

### Required history-preservation sequence

Before updating the current REGISTRY object:

1. freshly retrieve the current DRAFT bytes from Drive;
2. verify current DRAFT canonical hash;
3. verify lifecycle is exactly DRAFT;
4. copy the exact current DRAFT bytes into private EVIDENCE as a lifecycle
   snapshot object;
5. emit a snapshot manifest containing the DRAFT authority hash, raw storage
   SHA-256 and provider revision marker when available;
6. freshly retrieve the stored snapshot from EVIDENCE;
7. verify its exact bytes/hash against the source DRAFT;
8. only after snapshot verification PASS may the current REGISTRY object be
   updated.

If the snapshot cannot be reacquired or its hashes differ:

`HOLD_DRAFT_HISTORY_SNAPSHOT_INVALID`

The lifecycle action must stop before REGISTRY mutation.

Drive revision history is supplementary evidence only.

Provider revisions are not treated as permanent retention because the current
raw objects do not expose a guaranteed keep-forever revision contract.

The private EVIDENCE snapshot is therefore mandatory.

## 5. Exact DRAFT lifecycle snapshot contract

Required private object:

`TargetAuthorityLifecycleSnapshotV1`

It must bind:

- snapshot evidence ID;
- transition event ID;
- target-authority ID;
- captured lifecycle state = DRAFT;
- current authority-record hash;
- exact raw DRAFT storage SHA-256;
- provider revision/version marker when available;
- snapshot object content hash;
- environment;
- logical alias;
- locator ref/hash;
- warehouse schema version/hash;
- five-surface registry ID/hash;
- review mode;
- `human_separation_of_duties=false`.

The exact copied DRAFT bytes remain private.

Public GitHub may expose only the opaque snapshot evidence ID/hash.

## 6. Approval decision evidence contract

Verdict: **PASS FOR ACTION DESIGN**

Before REGISTRY mutation, create one private:

`TargetAuthorityApprovalDecisionEvidenceV1`

Required fields:

- `approval_evidence_schema_version`;
- `approval_event_id`;
- `decision = APPROVE`;
- `approval_model = SOLO_OPERATOR`;
- `review_mode = SOLO_OPERATOR_SELF_REVIEW_WITH_INDEPENDENT_EVIDENCE_PATH`;
- `human_separation_of_duties = false`;
- target-authority ID;
- `from_lifecycle_state = DRAFT`;
- `to_lifecycle_state = APPROVED`;
- current DRAFT authority-record hash;
- DRAFT snapshot evidence ID/hash;
- locator ref/hash;
- warehouse schema version/hash;
- five-surface registry ID/hash;
- `live_read_authorized = false`;
- `executable_acquisition_authorized = false`;
- `production_write_authorized = false`;
- `master_live_mutated = false`;
- `approval_evidence_hash`.

`approval_evidence_hash` must be deterministic SHA-256 over canonical JSON
excluding only `approval_evidence_hash` itself.

The approval evidence must be stored and freshly reacquired before lifecycle
mutation.

## 7. Permitted REGISTRY mutation

The separately authorized lifecycle action may update the one current REGISTRY
object only after the DRAFT snapshot and approval evidence both verify PASS.

Only these lifecycle/read-back fields may change:

- `lifecycle_state: DRAFT -> APPROVED`;
- `independent_readback_evidence_id` -> a new transition-specific PENDING
  read-back evidence ID;
- `independent_readback_evidence_hash` -> the hash of that new PENDING
  read-back evidence;
- `authority_record_hash` -> recomputed canonical APPROVED record hash.

The following must remain byte-for-byte/semantically unchanged:

- target-authority ID;
- environment;
- logical target alias;
- warehouse schema version;
- surface registry ID/hash;
- external locator ref/hash;
- owner authority ref;
- approver authority ref;
- independent reviewer authority ref;
- record schema version;
- `supersedes_authority_id`;
- `revocation_epoch_ref`.

`activation_epoch_ref` must also remain unchanged during DRAFT -> APPROVED.

APPROVED is not ACTIVE; an approval action must not fabricate an activation
epoch.

Any unexpected field change = HOLD.

## 8. Independent read-back state rule

This readiness audit explicitly forbids carrying forward or manufacturing a
PASS state during the approval write.

During DRAFT -> APPROVED:

`independent_readback_state = PENDING`

must remain PENDING.

The transition must bind a **new** transition-specific pending read-back
evidence ID/hash.

The Phase B DRAFT verification PASS cannot be reused as proof that the new
APPROVED bytes have been read back.

After the transition event closes, a distinct verification event must freshly
reacquire the APPROVED record and recompute its hash.

That verification event may emit PASS/HOLD evidence but must not write the
authority object.

A later separately authorized read-back-finalization/lifecycle action is
required before any record may claim
`independent_readback_state = PASS`.

This prevents a circular pattern where a record is marked PASS before the bytes
being certified have actually been retrieved.

## 9. Transition event boundary

The DRAFT -> APPROVED action must use one opaque transition event ID distinct
from every prior Phase B event ID.

Allowed order:

1. preflight current DRAFT/locator/target/bindings/permissions;
2. create DRAFT lifecycle snapshot;
3. close snapshot write;
4. fresh-read snapshot and verify;
5. create approval decision evidence;
6. close approval-evidence write;
7. fresh-read approval evidence and verify;
8. create new PENDING read-back evidence for the APPROVED transition;
9. update the one current REGISTRY record to APPROVED;
10. recompute/store the new authority-record hash;
11. close the transition event;
12. stop all authority writes.

No Production payload read is required.

## 10. Verification event boundary

After the transition event closes, use a distinct verification event ID.

Verification must freshly reacquire:

- current APPROVED REGISTRY bytes;
- current locator bytes;
- DRAFT lifecycle snapshot;
- approval decision evidence;
- transition-specific PENDING read-back evidence;
- full current REGISTRY object set;
- relevant permission/sharing metadata.

It must verify:

- exact target-authority ID;
- lifecycle exactly APPROVED;
- APPROVED record canonical hash;
- unchanged schema/surface/locator/governance bindings;
- `independent_readback_state=PENDING`;
- transition-specific pending evidence binding;
- DRAFT snapshot integrity;
- approval evidence integrity;
- ACTIVE count remains zero;
- private owner-only boundary;
- no public Production identifier leakage.

Verification may return only PASS or HOLD.

No authority-bearing write is allowed during verification.

## 11. APPROVED non-resolvability

Verdict: **PASS**

APPROVED remains non-resolvable by the future acquisition runtime.

Only ACTIVE is eligible for target resolution.

Therefore DRAFT -> APPROVED does not authorize:

- live provider acquisition;
- executable acquisition;
- runtime credentials;
- Production writes;
- MASTER LIVE mutation.

## 12. Fail-closed blockers

Required blockers include:

- `HOLD_DRAFT_HISTORY_SNAPSHOT_INVALID`;
- `HOLD_APPROVAL_EVIDENCE_INVALID`;
- `HOLD_DRAFT_STATE_DRIFT`;
- `HOLD_APPROVED_HASH_MISMATCH`;
- `HOLD_APPROVED_BINDING_DRIFT`;
- `HOLD_APPROVED_READBACK_PREMATURE_PASS`;
- `HOLD_APPROVED_ACTIVE_COUNT_NONZERO`;
- `HOLD_APPROVED_PERMISSION_DRIFT`;
- `HOLD_APPROVED_VERIFICATION_FAILED`.

Unknown state = HOLD.

## 13. Public leakage boundary

Public evidence may contain only:

- logical alias;
- opaque target-authority ID;
- opaque locator ref;
- authority/locator/schema/surface hashes;
- opaque transition/snapshot/approval/verification evidence refs and hashes;
- lifecycle and verdict states.

It must not publish:

- Drive authority file/folder IDs;
- provider revision IDs;
- Production resource/workbook ID or URL;
- provider account identity;
- sheet/range IDs;
- credentials/tokens;
- raw Production metadata/rows.

## 14. Allowed next action

The smallest next safe action is one separately authorized:

`TARGET_AUTHORITY_DRAFT_TO_APPROVED_LIFECYCLE_ACTION_V0_1`

It may perform only the exact sequence specified above.

It must stop after fresh APPROVED verification.

It must not set `independent_readback_state=PASS` in the same action.

It must not transition APPROVED -> ACTIVE.

## Final state

**Lifecycle readiness =
`PASS_FOR_DRAFT_TO_APPROVED_LIFECYCLE_ACTION_ONLY`**

**Current lifecycle = DRAFT**

**Current authority state =
`DRAFT_TARGET_AUTHORITY_MATERIALIZED_NOT_ACTIVE`**

**Current ACTIVE count = 0**

**LiveReadAuthorized=False**

**ExecutableAcquisitionAuthorized=False**

**ProductionWriteAuthorized=False**

**Production writer = HOLD**

**MASTER LIVE unchanged**
