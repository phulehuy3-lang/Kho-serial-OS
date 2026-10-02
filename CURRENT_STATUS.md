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

Issues #109 and #111 remain **OPEN/HOLD** after a fresh execution-capability
re-audit.

Current evidence:

- no connected ChatGPT tool exposes Google Cloud IAM service-account lifecycle;
- no installable Google Cloud IAM connector is available in the current plugin
  catalog; BigQuery remains unavailable and is not a lifecycle substitute;
- the execution container has no `gcloud`, ADC or
  `GOOGLE_APPLICATION_CREDENTIALS`;
- Google now documents a first-party IAM remote MCP server, but it is not
  connected to this session;
- Google Cloud CLI remote MCP still excludes
  `gcloud iam service-accounts`, so it remains insufficient for #109;
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


## Smallest next action

PHU-8 requires no further action at this checkpoint. Reopen its acceptance only
if the caller/workflow, SOP v1.9.x, header/schema binding, peer/descendant logic,
manifest-touch contract, readback API, or a new false-PASS changes the accepted
assumptions.

Re-evaluate #111 only when a real provider-native Google Cloud IAM execution
path exists for create/get, zero USER_MANAGED keys and IAM-policy read-back.
Then follow #109's exact action contract. Until then, keep #109/#111 OPEN/HOLD;
do not repeat capability probing or create an audit PR just to restate HOLD.

