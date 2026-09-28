# Kho-serial-OS — Current Status

Status snapshot: 2026-09-29 (Asia/Ho_Chi_Minh).

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

## Smallest next action

Re-evaluate #111 only when a real provider-native Google Cloud IAM execution
path exists for create/get, zero USER_MANAGED keys and IAM-policy read-back.
Then follow #109's exact action contract. Until then, keep #109/#111 OPEN/HOLD;
do not repeat capability probing or create an audit PR just to restate HOLD.
