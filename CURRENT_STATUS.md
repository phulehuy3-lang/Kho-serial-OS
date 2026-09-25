# Kho-serial-OS — Current Status

Status date: 2026-09-25

This page is the repository entry point for current public engineering status.
It deliberately separates **provider state verified directly** from
**documentation state at checkpoint**. Historical lifecycle documents remain
evidence of their own checkpoints and are not silently reinterpreted as current
provider state.

## Provider state verified directly

Fresh GitHub read-back before R4 publication:

- repository: `phulehuy3-lang/Kho-serial-OS`;
- verified main SHA:
  `376b87aa5a50e5d8bacb1b935c97f47bffc115d2`;
- Main ruleset `23875625`: active;
- merge policy: pull request, squash-only, linear history, deletion and
  non-fast-forward protection;
- required checks:
  - `unit-tests`;
  - `trusted-public-boundary`;
  - `trusted-public-boundary-v2`;
  - `trusted-warehouse-serial-scope`;
- `trusted-public-boundary-v3` is now present in the active Main ruleset as the fifth required status check;
- Issue #96 remains OPEN and is a separate runtime-identity readiness issue.

Evidence links:

- [PR #97 — R1 type/producer/malformed input](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/97)
- [PR #98 — R2 Formula Semantic Identity V2](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/98)
- [PR #99 — R3 Trusted Public Boundary V3](https://github.com/phulehuy3-lang/Kho-serial-OS/pull/99)
- [Issue #96 — read-only runtime identity materialization readiness](https://github.com/phulehuy3-lang/Kho-serial-OS/issues/96)
- [R3 V3 migration status](rules/TRUSTED_PUBLIC_BOUNDARY_V3_MIGRATION.md)

## Documentation state at checkpoint

Audit-remediation state recorded on 2026-09-25:

| Package | State at checkpoint | Evidence |
|---|---|---|
| R1 — F02/F03/F04 | CLOSED | PR #97; fixed head `25cb82e72174aedca0446f033d978c12c42290b5`; squash main `4ff5060b14f68c3e647ea81aa645c1b170a2090e`; 336/336 tests; exact-head and post-merge required checks PASS |
| R2 — F01 | CLOSED | PR #98; fixed head `f5f3b3acc7b322351a9c317c3d3a96261ae5a71c`; squash main `0a4d282c779e50a074711633cf11a1face5d0423`; 347/347 tests; V2 golden vectors PASS; tag `v0.2.0` unchanged |
| R3 — F05/F06 engineering | CLOSED | PR #99; fixed head `6b434b1920fbe60f687053e16d50fb09699a20a2`; squash main `376b87aa5a50e5d8bacb1b935c97f47bffc115d2`; 353/353 tests; V3 workflow PASS |
| R3 — V3 enforcement | **CLOSED / ENFORCED** | Fresh Main ruleset read-back requires V3; synthetic PR #102 returned `mergeable_state=blocked` while V3 failed |
| R4 — F07/F08/F09 | publication in PR #100 | current-status index, checkpoint relabeling, privacy-history disclosure and owner-controlled license proposal |

The Phase 2 tag `v0.2.0` remains at
`218c8030252ea0fb23489a5631678925b2572978`. It is historical evidence and
must not be moved or rewritten to incorporate later remediations.

## History boundary: delta-history vs full-history privacy

These are intentionally separate findings.

### delta-history

The remediation PR deltas are protected by the repository history/static/scope
gates. R1/R2 exact PR heads passed the then-required four checks; R3 exact head
passed the four required checks, and the post-merge V3 workflow also passed.

**delta-history status: PASS for the remediated PR deltas verified above.**

### full-history privacy

The 2026-09-25 audit found three legacy author/committer email metadata
violations across two older commits. This page intentionally does not reproduce
the email addresses.

Those historical metadata findings were not removed by changing later commit
identity, and this remediation does **not** rewrite Git history.

**full-history privacy status: NOT CLEAN / historical exception decision still
required.**

The two audit-identified commit SHAs are retained only as technical references:

- `ca1a2afe52e61a7bc9459a36a6eb531324dd0ed0`;
- `0883e18e0447597bc80093391c6dcc24e684d491`.

## License state

No repository license has been selected in this remediation.

The concrete owner-decision proposal is:

- [LICENSE_DECISION_PROPOSAL_V0_1](rules/LICENSE_DECISION_PROPOSAL_V0_1.md)

Until the repository owner explicitly chooses and commits a license, no
`LICENSE` file should be inferred from this document.

## Locked authority boundary

Repository-control PASS is not live-system authority.

The following remain locked:

- `LiveReadAuthorized=False`;
- `ExecutableAcquisitionAuthorized=False`;
- `ProductionWriteAuthorized=False`;
- Production writer = HOLD;
- no warehouse payload read by this remediation;
- no credential/service-account creation;
- no Drive/Sheets permission change;
- no target-authority lifecycle change;
- no MASTER LIVE mutation.

## Smallest next action

The audit-remediation engineering and V3-enforcement stream is now CLOSED.

Issue #96 materialization-action readiness has been re-audited.

Current verdict:

`HOLD_READONLY_IDENTITY_MATERIALIZATION_NOT_READY`

The store/location and solo-operator governance bindings are now specified.
Two blockers remain:

- `HOLD_KEYLESS_AUTH_PATH_UNRESOLVED`;
- `HOLD_IDENTITY_PROVIDER_READBACK_CAPABILITY_UNBOUND`.

Issue #105 selected the canonical runtime/read-back design:

- runtime: `GITHUB_ACTIONS_EXTERNAL_WORKLOAD / DEFAULT_BRANCH_MAIN_ONLY`;
- authentication: `OIDC -> WORKLOAD_IDENTITY_FEDERATION -> SERVICE_ACCOUNT_IMPERSONATION`;
- target access remains a later direct Drive `reader` grant;
- provider identity read-back is Google Cloud IAM service-account get, user-managed-key list and IAM-policy read-back;
- Workspace DWD is not applicable to the current consumer-account target boundary.

The two Issue #96 design blockers are resolved at design level.

Issue #107 re-readiness verdict:

`PASS_FOR_READONLY_IDENTITY_MATERIALIZATION_ACTION_ONLY`

Issue #109 materialization has started.

Completed:

- private `PRG02_READONLY_RUNTIME_IDENTITY_V1` authority-store topology;
- owner-only/shared=false read-back for root and all four required children.

Current materialization verdict:

`PARTIAL / HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE`

The current operating path does not expose provider-native Google Cloud IAM
service-account create/read-back capability, so the dedicated service account,
private identity authority record and IAM verification have not been
materialized.

Issue #109 remains OPEN. The existing Drive topology must be reused when IAM
capability becomes available.

WIF setup, IAM impersonation binding, Drive reader grant, PRG-03, live reads and
executable acquisition remain separate later actions.
