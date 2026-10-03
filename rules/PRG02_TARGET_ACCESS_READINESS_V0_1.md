# PRG02_TARGET_ACCESS_READINESS_V0_1

Status: **PASS_FOR_DIRECT_FILE_READER_GRANT_ACTION_ONLY**

Issue: #136

## Purpose

Record public-safe readiness evidence for the next PRG-02 target-access step.

This artifact authorizes no permission change by itself.

## Verified prerequisites

Current target authority:

- target authority ref: `TA1_d597fd30cfeeefc01ca9d28f71a98e0f`
- lifecycle = `ACTIVE`
- independent read-back state = `PASS`
- authority hash =
  `18d82986492840594d6e9eea82df4daeb024140d49c308b66fe22da098a17151`
- target locator ref = `LOC1_a18c6d759273701cfcf0942b505409af`
- target locator hash =
  `91e8b5c59e6c1a9d299badc1edddc97d0c24859229a8661760504c195af9cd07`

Current dedicated runtime identity:

- principal locator ref = `PL1_b730cce235f250ae6d1951c83bea6169`
- principal locator hash =
  `423b877409d5ff7588fbb4edea3adda7f2746d68022fb471f6f2f7eb1ca629d7`
- runtime identity record ref =
  `RRI1_c81708f91c3167a4aebb7cef5f4f175f`
- runtime identity hash =
  `62723bff3a70a10e2291dc63396a43eebfe49da8e948fc62fe3e9207051e0b33`
- USER_MANAGED key count = 0
- WIF materialization = PASS
- sanitized short-lived credential acceptance = PASS

Private provider metadata established that the canonical target currently has
exactly owner-only permission and the dedicated runtime principal is not yet
granted access.

The connected owner can share the exact target file.

Private readiness snapshot SHA-256:

`26ff671488e3cac37c2abdda22f61f7e6f7628849508287a33a2f3e35c32a764`

Private target/provider/principal locators remain outside this repository.

## Allowed next action

Exactly one separately authorized permission mutation may be considered:

- exact canonical target file only;
- exact dedicated runtime service account only;
- Drive role = `reader`;
- direct file-level grant only;
- no parent-folder grant;
- no domain grant;
- no group grant;
- no anyone/link-wide grant;
- no writer/editor/commenter permission;
- no target content read during the grant action.

## Required post-grant evidence

The grant action must immediately perform provider metadata read-back and prove:

1. owner permission remains present;
2. exactly one new permission exists for the dedicated runtime principal;
3. that permission role is exactly `reader`;
4. target is not public and has no domain/group/anyone grant;
5. no parent-folder grant was introduced;
6. no unexpected principal exists;
7. no worksheet/warehouse payload was read;
8. no MASTER LIVE business data was mutated.

Any ambiguity or extra permission = HOLD.

## PRG-03 separation

A successful reader grant does not prove effective runtime access.

After grant/read-back, a separate PRG-03 gate must prove the effective
permission path using the dedicated runtime identity.

Until PRG-03 passes:

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD

## Verdict

**`PRG02_TARGET_ACCESS_READINESS_V0_1 =
PASS_FOR_DIRECT_FILE_READER_GRANT_ACTION_ONLY`**

This readiness does not itself mutate Drive permissions and does not authorize
a live warehouse read.
