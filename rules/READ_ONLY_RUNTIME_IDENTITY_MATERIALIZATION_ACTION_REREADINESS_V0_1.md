# READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_ACTION_REREADINESS_V0_1

Status: **PASS_FOR_READONLY_IDENTITY_MATERIALIZATION_ACTION_ONLY**

Issue: #107

## Purpose

Re-audit PRG-02 after the runtime placement and provider-native read-back
contract were selected.

This artifact answers only one question:

**May a separately authorized read-only runtime identity materialization action
now open?**

Answer:

**YES — for the narrowly scoped materialization action defined below.**

This PASS does not create a service account, Workload Identity Federation
resource, IAM impersonation grant, credential, token, Drive reader grant,
provider session, live warehouse read, executable acquisition path, Production
writer, or MASTER LIVE mutation.

## 1. Fresh dependency read-back

Fresh provider and repository evidence on 2026-09-25 confirms:

- the canonical target-authority record remains `ACTIVE`;
- its independent read-back state remains `PASS`;
- the target authority remains bound to the existing
  `PRODUCTION_SHADOW` warehouse target;
- the canonical target remains private and owner-only;
- the target remains outside a Shared Drive;
- the target remains under a consumer Google-account boundary;
- the active Main ruleset still requires all five repository checks.

No provider permission or target-authority lifecycle state was changed during
this re-audit.

Verdict:

**PASS**

## 2. Canonical identity design

Selected identity class remains:

`GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT`

Authentication policy remains:

`KEYLESS_ONLY`

Credential policy remains:

`NO_PERSISTED_PRIVATE_CREDENTIAL`

Prohibited:

- user-managed JSON/P12 service-account keys;
- downloaded private keys;
- embedded long-lived secrets;
- Workspace-user impersonation;
- domain-wide delegation for the canonical warehouse target;
- operator/personal Google account as runtime identity.

Verdict:

**PASS**

## 3. Identity authority store and governance

Selected private logical root remains:

`PRG02_READONLY_RUNTIME_IDENTITY_V1`

Required logical children:

1. `REGISTRY`
2. `PRINCIPAL_LOCATOR`
3. `EVIDENCE`
4. `RECOVERY`

Governance mode remains:

`SOLO_OPERATOR_SELF_REVIEW_WITH_INDEPENDENT_EVIDENCE_PATH`

Locked disclosure:

`human_separation_of_duties = false`

Canonical logical authorities remain bound for:

- owner;
- custodian;
- rotation;
- revocation;
- independent evidence-path reviewer.

Materialization and provider verification must remain separate evidence events.

Verdict:

**PASS FOR ACTION OPENING**

## 4. Runtime placement prerequisite

Issue #105 selected exactly one runtime placement:

`GITHUB_ACTIONS_EXTERNAL_WORKLOAD / DEFAULT_BRANCH_MAIN_ONLY`

The trust design binds:

- exact numeric repository ID;
- exact numeric owner ID;
- `refs/heads/main`.

No pull request, fork, tag, feature branch, arbitrary repository, wildcard
principal or name-only trust is eligible.

Verdict:

**PASS**

## 5. Keyless authentication prerequisite

Issue #105 selected exactly one keyless authentication path:

`GITHUB_ACTIONS_OIDC -> GOOGLE_CLOUD_WORKLOAD_IDENTITY_FEDERATION ->
SERVICE_ACCOUNT_IMPERSONATION`

Long-lived service-account keys remain prohibited.

The future WIF setup is **not** part of the identity materialization action
authorized by this re-readiness decision.

Verdict:

**PASS FOR SEQUENCING**

## 6. Provider-native read-back prerequisite

The provider verification contract is fixed.

A materialization action may close only after a distinct verification event
freshly reacquires the service account through Google Cloud IAM and verifies:

1. exact service-account identity;
2. provider unique ID/project binding;
3. enabled/disabled state;
4. `USER_MANAGED` key list is empty;
5. service-account IAM policy contains no unexpected principal;
6. no write/admin-style runtime binding was silently introduced;
7. the private identity-authority record recomputes to the expected hash;
8. materialization-event ID and verification-event ID differ.

The verification event may not use only the creation response, screenshots,
copied console output, operator memory or the public GitHub artifact.

Verdict:

**PASS FOR ACTION OPENING**

Operational note:

The current ChatGPT-connected operating path does not itself expose Google
Cloud IAM mutation/read-back tools. That limits who can execute the later
provider action, but it does not make this governance re-readiness design
incomplete. The materialization action must fail closed if provider-native
creation/read-back capability is unavailable at execution time.

## 7. Workspace DWD prerequisite

Fresh canonical-target metadata continues to show a consumer Google-account /
My Drive ownership boundary, not a Google Workspace domain or Shared Drive.

For this target:

`workspace_domain_wide_delegation_applicability =
NOT_APPLICABLE_TO_CANONICAL_TARGET_BOUNDARY`

No delegated Workspace user is permitted.

If the canonical target later moves to a Workspace organization or Shared
Drive, this re-readiness PASS becomes stale and must be rerun.

Verdict:

**PASS**

## 8. Exact scope of the next materialization action

A separately authorized action may now perform **only** the following
authority-bearing operations:

### A. Private PRG-02 control-plane boundary

May create the private logical PRG-02 authority-store topology:

- `PRG02_READONLY_RUNTIME_IDENTITY_V1`
- `REGISTRY`
- `PRINCIPAL_LOCATOR`
- `EVIDENCE`
- `RECOVERY`

It must remain restricted and outside the public repository.

### B. Dedicated service account

May create exactly one new
`GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT` for PRG-02.

Creation must not generate a user-managed private key.

### C. Private identity authority record

May materialize exactly one private identity authority record bound to:

- the current ACTIVE target-authority ID/hash;
- `PRODUCTION_SHADOW`;
- the selected service-account principal locator;
- `KEYLESS_ONLY`;
- `NO_PERSISTED_PRIVATE_CREDENTIAL`;
- DWD prohibited/not applicable to the canonical target;
- Workspace-user impersonation prohibited;
- governance authority refs;
- independent-readback state;
- lifecycle state;
- deterministic identity-record hash.

Actual provider principal/project locators remain private.

### D. Provider read-back

Must perform a separate provider-native verification event.

The action may reach its own CLOSED/PASS state only after that fresh read-back
passes.

## 9. Explicitly excluded from the next action

The materialization action authorized by this re-readiness must **not**:

- create a Workload Identity Pool;
- create a Workload Identity Provider;
- add the GitHub federated principal to service-account IAM;
- grant `roles/iam.workloadIdentityUser`;
- request an OIDC token;
- mint a Google access token;
- create/upload a service-account key;
- share the warehouse target with the service account;
- grant Drive/Sheets reader permission;
- call the warehouse target through the service account;
- inspect warehouse Production payload;
- activate executable acquisition;
- enable a Production writer;
- alter the target-authority lifecycle;
- mutate MASTER LIVE.

Those are later separately authorized steps.

## 10. Materialization action close criteria

The future action may close PASS only when all of the following are true:

1. exactly one dedicated service account was created;
2. no user-managed service-account key exists;
3. the private PRG-02 authority store exists at the selected boundary;
4. exactly one canonical identity authority record exists for the current
   target/environment;
5. the identity record hash recomputes exactly;
6. creation/materialization and verification evidence IDs differ;
7. fresh IAM read-back reacquires the service account;
8. fresh key read-back shows zero USER_MANAGED keys;
9. fresh IAM-policy read-back shows no unexpected principal;
10. no WIF/IAM impersonation grant was added;
11. no Drive/Sheets permission changed;
12. no warehouse payload was read;
13. all five repository checks remain required;
14. public-boundary audit finds no provider secret/private locator leakage.

Any unknown required state = HOLD.

## 11. Readiness matrix

| Requirement | Re-readiness verdict |
| --- | --- |
| target authority ACTIVE/PASS | PASS |
| target authority unique/current | PASS |
| target owner-only/private | PASS |
| identity class selected | PASS |
| private authority-store architecture selected | PASS |
| governance authority refs selected | PASS |
| solo-operator evidence model explicit | PASS |
| runtime placement selected | PASS |
| one keyless auth path selected | PASS |
| user-managed keys prohibited | PASS |
| DWD disposition resolved | PASS |
| provider-native IAM read-back contract fixed | PASS |
| target permission grant separated | PASS |
| WIF setup separated | PASS |
| PRG-03 separated | PASS |
| five repository checks retained | PASS |

## 12. Re-readiness decision

All prerequisites identified by Issue #96 have now been resolved at the
governance/design level.

Therefore:

**`READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_ACTION_REREADINESS_V0_1 =
PASS_FOR_READONLY_IDENTITY_MATERIALIZATION_ACTION_ONLY`**

This PASS means a separately authorized materialization action may open.

It does not mean the identity exists and does not authorize WIF, Drive access,
live reads or executable acquisition.

## 13. Smallest next safe action

Next action:

`READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_V0_1`

Scope:

**private PRG-02 authority-store boundary + exactly one keyless service account
+ private identity authority record + fresh provider IAM read-back only.**

If the execution environment cannot create/reacquire the service account
through Google Cloud IAM, the action must remain HOLD rather than substituting
screenshots/manual assertions.

## Locked state

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = `HOLD`
- no service account created by this re-audit
- no WIF pool/provider created
- no IAM impersonation grant created
- no credential/key/token created
- no Drive/Sheets permission change
- no provider warehouse payload read
- no target-authority lifecycle change
- MASTER LIVE unchanged
