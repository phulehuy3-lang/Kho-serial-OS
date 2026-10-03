# Kho-serial-OS — Current Status

Status snapshot: 2026-10-03 (Asia/Ho_Chi_Minh).

This page records a verified repository snapshot, not a live authority grant. A
merge of this document necessarily creates a newer main SHA; use the
[main branch](https://github.com/phulehuy3-lang/Kho-serial-OS/tree/main) and
its current checks for the latest provider state. Earlier SHAs below are
explicit historical checkpoints.

## Verified repository state before this documentation PR

- Main: `49e5f4a8adfae47e6f50cc3074ad380768525a27` (R5 squash from
  [PR #115](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/115)).
- Main ruleset `23875625`: active; pull request, squash-only, linear
  history, no deletion or non-fast-forward, strict required status checks,
  no bypass actors.
- Five required checks: `unit-tests`, `trusted-public-boundary`,
  `trusted-public-boundary-v2`, `trusted-warehouse-serial-scope`,
  `trusted-public-boundary-v3`.
- PR #115 exact head `289e63dcf4f9a64cb5d952269d8103186576c238`:
  372/372 unit tests and 5/5 required checks PASS. Post-merge exact main:
  372/372 and 5/5 PASS. Branch cleanup verified.
- At the snapshot, no PR was open before R5, and the frozen Phase 2 tag
  `v0.2.0` still pointed to `218c8030252ea0fb23489a5631678925b2572978`.

## Engineering history and current issue state

| Work | Verified checkpoint | Meaning |
| --- | --- | --- |
| R1 type/producer/malformed input | [PR #97](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/97), squash `4ff5060b14f68c3e647ea81aa645c1b170a2090e` | Closed at its checkpoint; 336 tests and the then-required four checks passed. |
| R2 formula semantic identity V2 | [PR #98](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/98), squash `0a4d282c779e50a074711633cf11a1face5d0423` | Closed at its checkpoint; 347 tests. |
| R3 trusted public boundary V3 | [PR #99](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/99), squash `376b87aa5a50e5d8bacb1b935c97f47bffc115d2` | Engineering closed at its checkpoint; subsequent ruleset read-back established V3 as the fifth required check. |
| R4 status/history/license governance | [PR #100](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/100) | Historical remediation; license decision and full-history privacy exception remain separate. |
| Warehouse governance v1.8 profile | [PR #114](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/114), squash `f6f9fd550a490305327988ccf146d69a22aa188e` | Pure synthetic profile; 367/367 and 5/5 at that main. No Production write authority. |
| R5 serial identity hardening | [PR #115](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/115), squash `49e5f4a8adfae47e6f50cc3074ad380768525a27` | Test-only head `eac66310f87675b5190fe7b8d89f5b7f0a4e1bbb` reproduced Unicode/overlong failure; final head and main passed 372/372 and 5/5. ASCII text, max 4096 digits, preserved width/leading zero and exact split conservation. |

Issue state was read directly at this snapshot:

- [#96](https://github.com/phulehuy3-lang/Kho-serial-OS/issues/96)
  **CLOSED/completed** (readiness audit); its earlier HOLD was a historical
  audit result, not an open issue now.
- [#105](https://github.com/phulehuy3-lang/Kho-serial-OS/issues/105)
  **CLOSED/completed** (runtime placement/provider read-back design).
- [#107](https://github.com/phulehuy3-lang/Kho-serial-OS/issues/107)
  **CLOSED/completed** (re-readiness; `PASS_FOR_READONLY_IDENTITY_MATERIALIZATION_ACTION_ONLY`).
- [#109](https://github.com/phulehuy3-lang/Kho-serial-OS/issues/109)
  **OPEN**: partial materialization; private
  `PRG02_READONLY_RUNTIME_IDENTITY_V1` topology already exists with
  `REGISTRY`, `PRINCIPAL_LOCATOR`, `EVIDENCE`, `RECOVERY`.
  `HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE`.
- [#111](https://github.com/phulehuy3-lang/Kho-serial-OS/issues/111)
  **OPEN**: same execution-capability blocker. No service account or
  provider-native IAM verification was established by the repository work.

The selected future design remains GitHub Actions on default-branch main,
OIDC → Workload Identity Federation → service-account impersonation. This
design decision is not a deployed federation, IAM grant, credential, or
permission proof.

## History and license

Remediation deltas passed their applicable boundary checks at their own
checkpoints. The separate full-history privacy audit found legacy
author/committer email metadata violations across two older commits
(`ca1a2afe52e61a7bc9459a36a6eb531324dd0ed0` and
`0883e18e0447597bc80093391c6dcc24e684d491`).
**Full-history privacy: NOT CLEAN; historical exception decision outstanding.**
No history rewrite is authorized here.

No license has been selected. See
[LICENSE_DECISION_PROPOSAL_V0_1](rules/LICENSE_DECISION_PROPOSAL_V0_1.md).
Do not infer a license from that proposal.

## Locked authority boundary

Repository checks and synthetic tests do not prove live inventory correctness.
`LiveReadAuthorized=False`; `ExecutableAcquisitionAuthorized=False`;
`ProductionWriteAuthorized=False`; Production writer = HOLD.
No warehouse Production payload, MASTER LIVE business data, serial stock or
ledger was read or changed by R5 or this documentation sync. No credential,
service account, Drive/Sheets grant or target-authority lifecycle change was
created by those repository actions.

## PHU-8 post-merge remediation — 2026-10-01

> Historical checkpoint. The PARTIAL/HOLD state in this section was superseded by the accepted closure checkpoint on 2026-10-03 below.


Baseline main `6a687f7123788dc00e4e6fea40242692e8072ec3` passed 372 tests and
five checks but reproduced boolean, READBACK_PASS and HOLD-release false-PASS.
[PR #117](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/117) is merged.
Regression-only commit `a619e3be670a8d15384ae689f2ed214aa682de41` ran 377 tests
with 15 expected failures. Reviewed head
`b05427b6c8e76729e34c7e05f88b7ca65d3e4400` and exact squash main
`ecbdd8d4c7403d65942471b641647a3b0b00005f` passed 382/382 tests and 5/5 checks.
These are verified checkpoints; this documentation update creates a newer SHA.

The merged controls enforce native booleans, materialized readback evidence
bound to a separately sealed transaction for READBACK_PASS/CLOSED, exact ACTIVE
HOLD identity/range/state and explicit complete peer-snapshot metadata.
Pre-merge review removed unsupported terminal interval-status mappings and
added compatibility regression; terminal isolation remains preserved.

Engineering remediation: **PASS**. Operational acceptance: **PARTIAL/HOLD**.
Canonical regression records RG-0118–RG-0121 are synthetic PASS. RG-0122 remains
NOT_RUN for operational integration acceptance. A passing repository suite does
not authenticate evidence provenance, capture freshness or peer completeness.

### RG-0122 required acceptance

| Gate | Required materialized evidence | Current limit |
| --- | --- | --- |
| Operational caller | Exact caller source/version and invocation path using the remediated API | Operational use is not proved by synthetic callers |
| Boolean validation | Positive native booleans; text, numbers, null and containers rejected through the actual caller | Pure regression PASS; operational acceptance pending |
| Readback binding | Independently accepted sealed task/scope/payload binding; independent fresh readback; exact fields/types/values and distinct captures | Labels and markers alone do not prove provenance or independence |
| HOLD readiness | Authoritative complete peer capture; identity/category/range/state parity; duplicate/conflicting IDs and overlap negatives | Completeness flag alone is insufficient; readiness is not release authorization |
| Compatibility | Terminal isolation and negative production-write guard through the actual invocation path | Synthetic compatibility evidence only |
| Applicable SOP conformance | Immutable FILE, header-bound schema, structural reconciliation, batch identity, stale-scope invalidation, complete descendants, machine classification, exact manifest/touch equality | Each applicable v1.9 requirement needs canonical acceptance; no blanket conformance claim |

Integration PASS requires exact-version controlled positive and adversarial
results, independently accepted provenance/freshness/completeness, and canonical
acceptance for every applicable control. Inapplicability requires an explicit
authority-backed rationale. Missing evidence keeps RG-0122 NOT_RUN and readiness
HOLD. Acceptance may inspect already-materialized evidence without live access;
this checklist grants no provider capability.

#109/#111 remain separate OPEN/HOLD. No credential, IAM grant, live warehouse
read, MASTER LIVE change or PRG-02 recreation is introduced. P2 serial
Unicode/overlong follow-up remains outside this P1 remediation.

## PHU-8 closure — 2026-10-03

PHU-8 is **DONE** and canonical regression `RG-0122` is **PASS** for
operational integration acceptance on an isolated synthetic provider fixture.

The accepted on-demand ChatGPT → Google Sheets path materialized the evidence
that had remained missing at the 2026-10-01 checkpoint:

- immutable ORIGINAL evidence remained byte-identical and retained the same
  provider `modified_time`; an overwrite attempt was blocked before mutation
  and verification was append-only;
- the writer was bound to a freshly read header map (`Status:D`); a drifted
  header moving `Status` to column C was blocked before the adversarial target
  could be mutated;
- descendant traversal and same-carrier peer capture were complete; the actual
  11 native session gates classified `CLEAN_PASS`, while a forced-false
  adversarial gate classified `BLOCKED_SAFE`;
- the finalized manifest targeted only `D2`, the provider mutation touched only
  `D2`, and independent full-row read-back confirmed `D2=ACCEPTED` with all
  non-target sentinels unchanged.

Canonical evidence is recorded in `NJ-0292` and `RG-0122`. The operational
read model reports `PRODUCTION_SYNCED / TESTED_PASS`, with regression
`NOT_RUN=0`, open risk `0`, and open P1 `0` at the closure checkpoint.

This PASS does **not** authorize a Production writer, does not relabel historical
source-rank evidence, and does not release PRG-02 runtime/IAM holds.
[#109](https://github.com/phulehuy3-lang/Kho-serial-OS/issues/109) and
[#111](https://github.com/phulehuy3-lang/Kho-serial-OS/issues/111) remain
separate OPEN/HOLD items. `LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`, and `ProductionWriteAuthorized=False`
remain unchanged.

## PRG-02 IAM/runtime blocker refresh — 2026-10-03

> Historical checkpoint. The OPEN/HOLD state below was superseded by the provider-native capability and identity-materialization closure later on 2026-10-03.


Issues #109 and #111 remain **OPEN/HOLD** after a fresh execution-capability
re-audit.

Current evidence:

- no connected ChatGPT tool exposes Google Cloud IAM service-account lifecycle;
- no installable Google Cloud IAM connector is available in the current plugin
  catalog; BigQuery remains unavailable and is not a lifecycle substitute;
- the execution container has no `gcloud`, ADC or
  `GOOGLE_APPLICATION_CREDENTIALS`;
- Google's current IAM remote MCP reference exposes role and deny-policy tools,
  not service-account lifecycle tools, so it is insufficient for #109 even if
  connected;
- Google Cloud CLI remote MCP still excludes
  `gcloud iam service-accounts`, so it is also insufficient for #109;
- a remote-terminal path to a user-controlled machine is discoverable and could
  satisfy the approved CLI/API capability class only after explicit connection
  and authenticated project/account read-back.

Therefore #111 is not cleared and #109 must not proceed to service-account
creation yet. The already-materialized private PRG-02 topology remains the
resume point and must not be recreated.

Locked state remains:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.


## PRG-02 IAM/runtime identity closure — 2026-10-03

Issue #111 is **CLOSED/PASS** and Issue #109 is eligible for **CLOSED/PASS**
after actual provider-native materialization and independent verification.

Verified public-safe facts:

- provider-native Google Cloud IAM create/get/key-list/getIamPolicy capability
  was bound through an explicitly authorized user-controlled execution path;
- exactly one dedicated PRG-02 service account was created;
- fresh USER_MANAGED key count = 0;
- fresh service-account IAM-policy binding count = 0;
- one private principal locator and one private identity-authority record exist;
- identity-record and locator hashes independently recomputed MATCH;
- materialization and verification event IDs differ;
- no WIF resource, impersonation grant, Drive target permission, warehouse
  Production read, executable acquisition, Production writer or MASTER LIVE
  mutation occurred.

Public-safe opaque evidence:

- principal locator `PL1_b730cce235f250ae6d1951c83bea6169`
  / `423b877409d5ff7588fbb4edea3adda7f2746d68022fb471f6f2f7eb1ca629d7`;
- identity record `RRI1_c81708f91c3167a4aebb7cef5f4f175f`
  / `62723bff3a70a10e2291dc63396a43eebfe49da8e948fc62fe3e9207051e0b33`;
- materialization evidence
  `eed2566bb581aeaca93310c1dc753a68cc906f440e85a32c5b3d3a0ccdc4bd50`;
- verification evidence
  `d2c2f24704278de0e0e0bafb56ec66da0b4a074b033885833b7c6469f669e283`.

Private provider principal/project locators and private Drive IDs are not
published here.

Locked state remains:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.

## PRG-02 GitHub OIDC WIF materialization — 2026-10-03

Issue #127 has provider-native evidence sufficient for **CLOSED/PASS** after
public-safe repository sync.

Verified public-safe state:

- exactly one PRG-02 WIF pool and one GitHub OIDC provider;
- provider ACTIVE;
- GitHub issuer MATCH;
- exact repository numeric ID `1383239508`;
- exact owner numeric ID `300983965`;
- exact ref `refs/heads/main`;
- required four-attribute mapping MATCH;
- exact three-claim provider condition MATCH;
- exactly one `roles/iam.workloadIdentityUser` federation binding;
- USER_MANAGED service-account key count = 0;
- WIF config hash =
  `397d1ad6ee08f0e7b6f7bfbc52dac647a814c82581152034fbb62020fd47b17b`;
- verification evidence hash =
  `d200d624dcb04f6bb1fb46e10b04a2761fdf62ec985fafed0848b28c8fa367e3`.

No OIDC/access token was minted, no GitHub runtime job was executed, no Drive
target permission changed, no warehouse Production payload was read and MASTER
LIVE was not mutated.

Locked:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.

## PRG-02 short-lived credential acceptance — 2026-10-03

Issue #129 has sufficient evidence for **CLOSED/PASS**.

Sanitized workflow-dispatch run `37106077065` on `main`
(`1fbce8321ec84b7f2514b68fd70daba6c3a3737b`) proved:

- GitHub OIDC issuance PASS;
- Google STS/WIF exchange PASS;
- dedicated service-account impersonation PASS;
- 300-second short-lived access token PASS;
- no credentials file was created;
- Google project environment variables were not exported;
- project locator was not exported in the sanitized run;
- target resource read = false;
- resource write = false.

A prior run had a public-log privacy defect and is tracked separately in #132.
That issue must not reproduce the private locator.

This acceptance proves authentication only.

Locked:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.

## PRG-02 historical acceptance-log containment — 2026-10-03

Issue #132 has sufficient evidence for **CLOSED/PASS** after deletion and
independent read-back.

Verified public-safe state:

- original historical run `37105787660` was preserved privately before
  deletion;
- raw historical log SHA-256 =
  `cf9a3c348ff3183bacfe6e1b6d84d13f4a36abe343663ca095895fdef7b88afe`;
- privacy logging path was remediated by PR #131;
- sanitized replacement run `37106077065` succeeded;
- one-time containment run `37106675321` returned
  `HISTORICAL_RUN_DELETE_REQUEST=PASS`,
  `HISTORICAL_RUN_GET_404=PASS`, and
  `HISTORICAL_RUN_CONTAINMENT=PASS`;
- independent direct GitHub API read also returned 404 for the deleted run;
- containment-log SHA-256 =
  `8d56ecf07a7a59cfdb161a9b3041743dd0a0a144cd8763f8e0de1d151a48afae`;
- the one-time helper workflow is removed during closure.

No private locator is reproduced in this repository.

Locked:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.

## PRG-02 target-access readiness — 2026-10-03

Issue #136 has evidence sufficient for
**PASS_FOR_DIRECT_FILE_READER_GRANT_ACTION_ONLY**.

Verified public-safe prerequisites:

- target authority is ACTIVE/PASS;
- dedicated PRG-02 runtime identity is materialized and keyless;
- WIF and sanitized short-lived credential acceptance are PASS;
- current canonical target permission state is owner-only;
- the dedicated runtime principal has no current target permission;
- exact target file can be shared by the connected owner;
- private readiness snapshot SHA-256 =
  `26ff671488e3cac37c2abdda22f61f7e6f7628849508287a33a2f3e35c32a764`.

The next separately authorized action may grant only exact file-level
`reader` permission to the exact dedicated runtime identity, followed by
fresh permission read-back.

This readiness does not grant target access.

Locked:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.

## PRG-02 direct Drive reader grant — 2026-10-03

Issue #139 has evidence sufficient for
**PASS_DIRECT_FILE_READER_GRANT_POST_READBACK**.

Fresh provider metadata confirms:

- exact canonical target permission count = 2;
- owner permission remains present;
- exactly one dedicated runtime user permission exists;
- dedicated runtime permission role = `reader`;
- no domain/group/anyone grant exists;
- no worksheet/warehouse payload was read during verification;
- public post-grant snapshot SHA-256 =
  `889c43fed1253efa21ccb4043ed8c30c24b3fd3823c67ea9b8fd058b0a5c4ad2`.

This closes the provider permission materialization step only.

PRG-03 effective-permission proof remains separate.

Locked:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.

## PRG-03 effective Drive permission proof — 2026-10-03

Issue #141 has evidence sufficient for
**PASS_EFFECTIVE_DRIVE_PERMISSION_METADATA_ONLY**.

Accepted workflow run:

- run `37108886203`, attempt `2`;
- head `43418e7304d64c02fa33684fd30d043cc6c5bfad`;
- GitHub conclusion = `success`;
- OIDC issuance PASS;
- STS/WIF exchange PASS;
- dedicated service-account impersonation PASS;
- short-lived access-token PASS;
- exact Drive `files.get(fields=kind)` PASS;
- effective direct reader permission PASS;
- target locator not exported;
- worksheet payload read = false;
- resource write = false.

Attempt #1 failed closed on `accessNotConfigured`; enabling
`drive.googleapis.com` was sufficient remediation.

Public acceptance snapshot SHA-256 =
`6954f63b8c07cc160e463a178cf29f7f44a5955c8139fe1372a63c85d40b91c7`.

This closes the effective-permission blocker only.

Remaining executable-acquisition blockers include exact Production surface
bindings, serial/HOLD universe completeness, provider version semantics,
zero-write runtime attestation, and tamper-evident receipt boundary.

Locked:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.

## Warehouse inbound schema V2 — 2026-10-03

Issue #146 / Linear PHU-18 materializes a versioned public schema compatible
with Production serial identity semantics.

New bindings:

- `WAREHOUSE_INBOUND_SCHEMA_V2`;
- schema hash =
  `9a7036828810234062496179c1fe652b9078b1cd7fbe7f50e77e6991b33de203`;
- `SR1_HCM_SERIAL_INBOUND_V2`;
- registry hash =
  `2c45382441fb98003b7ccb7161944de938a1f91ee8199e1c26771bf6c6d9fbad`.

Serial/range identity is now strict `SERIAL_TEXT`; lexical identity and leading
zeroes are preserved. Numeric projection is permitted only for pure interval
ordering/cardinality and never replaces source identity.

The private inbound source selector now passes V2 schema conformance.

Historical schema-V2 checkpoint (superseded by the accepted PHU-19 and
PHU-17 closures below): at that checkpoint, the ACTIVE target-authority
record still bound the V1 schema/registry generation and PRG-04 was HOLD on
`HOLD_TARGET_AUTHORITY_SCHEMA_REGISTRY_REBIND_REQUIRED`.

Current control-plane state as of 2026-10-03: PHU-18/#146, PHU-19/#148 and
PHU-17/#145 are Done/closed within their respective scopes. V2 authority is
ACTIVE, V1 is SUPERSEDED, and exact-five physical binding is accepted PASS.
The supporting protocol and closure documentation are merged in PR #149
and PR #150. These scoped closures do not authorize live reads, executable
acquisition or Production writes; all three authorization flags remain False
and the Production writer remains HOLD.

Locked:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.

## Smallest next action

PHU-8 requires no further action at this checkpoint. Reopen its acceptance only
if the caller/workflow, SOP v1.9.x, header/schema binding, peer/descendant logic,
manifest-touch contract, readback API, or a new false-PASS changes the accepted
assumptions.

#109/#111 require no further action at this checkpoint. Future work must start at the next separately authorized runtime/WIF/target-access gate; this closure does not authorize live reads, executable acquisition, target sharing or Production writes.


## PRG-04 exact five Production surface bindings closure — 2026-10-03

Issue #145 / Linear PHU-17 has sufficient evidence for **CLOSED/PASS**.

Fresh control-plane-only read-back after the target-authority V1→V2 migration
established exactly five deterministic physical bindings for the locked inbound
surface set. Source-vs-derived roles are preserved; the inbound source record is
bound by an exact stable selector rather than a guessed row; the derived
projection and formula anchor are bound to the exact current anchor formula;
and system-table bindings are header/schema bound.

Private canonical binding hash:
`c2a75f6cdc94ccff776b9fa5472b81fb988714ce6d311a840cb8086d036e96e1`.

Public-safe fingerprints:
- inbound source header: `db5fd124214d262695422a5f9d7e3f209b5b5547146e969a6d87a893ee3da198`;
- serial-universe header: `d1461129b036e7db9be544a4643f2139499b90a58de0f8b51b3c2642994535cf`;
- HOLD-universe header: `35b4d93ef94af27912ef7913071c45471fd0525c4e46dd322c7e884ccabce02d`;
- derived anchor formula: `4b6976ebc5ab6941ad18fee425634a7e661e17eb81f0a4aaa7b2dd38bb51e388`.

The closure evidence is bound to the ACTIVE V2 target authority and
`SR1_HCM_SERIAL_INBOUND_V2`. The private artifact was materialized in the
restricted authority evidence boundary and read back after creation.

No serial/stock/ledger business rows were read. No MASTER LIVE business-data,
locator, Drive permission, IAM/WIF/service-account or credential mutation was
performed.

Locked state remains:
`LiveReadAuthorized=False`,
`ExecutableAcquisitionAuthorized=False`,
`ProductionWriteAuthorized=False`,
Production writer = HOLD.


## 2026-10-04 isolated integration R2 checkpoint

See [isolated integration audit](docs/OS_INTEGRATION_AUDIT_20261004_R2.md).

Synthetic trace and targeted controls PASS; overall assurance PARTIAL. Provider/deployed acceptance and production writer HOLD; all three authorization flags remain False. This is a separate laboratory generation and does not upgrade the original fixture registration or earlier runtime closures.
