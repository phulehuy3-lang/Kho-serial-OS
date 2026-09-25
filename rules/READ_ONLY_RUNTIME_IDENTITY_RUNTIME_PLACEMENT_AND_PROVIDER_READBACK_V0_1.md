# READ_ONLY_RUNTIME_IDENTITY_RUNTIME_PLACEMENT_AND_PROVIDER_READBACK_V0_1

Status: **PASS_RUNTIME_PLACEMENT_AND_PROVIDER_READBACK_DESIGN**

Issue: #105

## Purpose

Resolve the two remaining design prerequisites from Issue #96 without creating
a service account, credential, Workload Identity Federation resource, Drive
reader grant, provider session, live warehouse read, executable acquisition
path, Production writer, or MASTER LIVE mutation.

Resolved blockers:

- `HOLD_KEYLESS_AUTH_PATH_UNRESOLVED`
- `HOLD_IDENTITY_PROVIDER_READBACK_CAPABILITY_UNBOUND`

This is design/governance only. Provider materialization remains separately
authorized.

## 1. Canonical runtime placement

Selected placement:

`GITHUB_ACTIONS_EXTERNAL_WORKLOAD / DEFAULT_BRANCH_MAIN_ONLY`

The intended workload is a dedicated GitHub Actions job in the public
`Kho-serial-OS` repository.

Binding evidence:

- repository numeric ID: `1383239508`
- owner numeric ID: `300983965`
- default branch: `main`

Numeric IDs are used as the stable trust anchor rather than repository/owner
names.

No pull-request, fork, tag, feature-branch or arbitrary workflow identity is
eligible for runtime authentication.

## 2. Canonical keyless authentication path

Selected path:

`GITHUB_ACTIONS_OIDC -> GOOGLE_CLOUD_WORKLOAD_IDENTITY_FEDERATION ->
SERVICE_ACCOUNT_IMPERSONATION`

Long-lived service-account JSON/P12 keys remain prohibited.

The future GitHub Actions job may request an OIDC token only with the minimum
GitHub job permissions needed for that exchange:

- `id-token: write`
- `contents: read`

This does not grant repository-content write permission.

The WIF provider must map and evaluate at minimum:

- `google.subject = assertion.sub`
- `attribute.repository_id = assertion.repository_id`
- `attribute.repository_owner_id = assertion.repository_owner_id`
- `attribute.ref = assertion.ref`

Required attribute condition:

`assertion.repository_id == '1383239508' &&
 assertion.repository_owner_id == '300983965' &&
 assertion.ref == 'refs/heads/main'`

A name-only trust condition is insufficient.

## 3. Service-account impersonation boundary

The selected runtime identity remains:

`GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT`

The federated GitHub identity may later receive only the minimum Google Cloud
permission required to obtain short-lived credentials for that one service
account.

The expected Google Cloud binding is the provider-defined Workload Identity
User relationship scoped to the selected external principal.

That binding is not created by this issue.

No other human, repository, branch, tag, workflow from another repository,
group identity, or wildcard principal may receive the impersonation grant.

## 4. Drive/Sheets target access remains separate

The service account is not granted warehouse access by existing in Google
Cloud.

The canonical target uses direct Google Drive/Sheets sharing to the service
account principal as a later, separately authorized action.

That later grant remains:

`Drive role = reader`

No parent-folder grant, domain grant, group grant, writer/editor grant or
wildcard discovery is permitted.

PRG-03 must independently prove effective permission after any reader grant.

## 5. Workspace domain-wide delegation applicability

Fresh private provider metadata for the canonical target shows a consumer
Google-account/My Drive ownership boundary rather than a Google Workspace
domain boundary.

Therefore, for this exact target:

`workspace_domain_wide_delegation_applicability =
NOT_APPLICABLE_TO_CANONICAL_TARGET_BOUNDARY`

This statement is narrowly scoped. It does not claim that the service account
could never be authorized by some unrelated Workspace domain.

For the warehouse runtime:

- no Workspace organization is part of the canonical target authority;
- no Workspace user impersonation is required;
- no delegated `subject` user is permitted;
- the only target access path is direct file sharing to the service account.

If the canonical target later moves into a Workspace domain or Shared Drive,
this decision becomes stale and must be re-audited.

## 6. Provider-native service-account read-back

The materialization verification event must reacquire Google Cloud IAM state
through provider-native IAM APIs rather than trusting creation output.

Required read-back sequence:

1. reacquire the exact service account with
   `projects.serviceAccounts.get`;
2. verify the provider identity, project binding, unique ID and enabled state;
3. call `projects.serviceAccounts.keys.list` filtered to
   `USER_MANAGED`;
4. require zero user-managed keys;
5. read the service-account IAM policy with
   `projects.serviceAccounts.getIamPolicy`;
6. reject any unexpected principal or write/admin-style runtime binding;
7. recompute the private identity-authority record hash from freshly retrieved
   provider state;
8. emit a verification event distinct from the creation/materialization event.

Minimum verifier permission should be read-only, such as the permissions
contained by Google's Service Account Viewer role, or a stricter custom
read-only equivalent.

The verification identity must not use permissions that can create keys or
modify the service account merely to perform read-back.

## 7. Provider-native WIF read-back

After a separately authorized WIF setup action, provider verification must also
reacquire:

- workload identity pool;
- GitHub OIDC provider;
- attribute mapping;
- attribute condition;
- service-account IAM policy binding.

The verifier must prove the provider accepts only the exact repository/owner
numeric IDs and `refs/heads/main`.

Any name-only, organization-wide, wildcard-branch or all-pool impersonation
grant is HOLD.

## 8. Evidence-path independence

Review mode remains:

`SOLO_OPERATOR_SELF_REVIEW_WITH_INDEPENDENT_EVIDENCE_PATH`

`human_separation_of_duties = false`

Materialization and verification must use different event IDs.

Verification must start from provider identifiers/private locator refs and
fresh IAM retrieval, not from the proposal object, GitHub document, screenshot,
copied console text, chat transcript or creation response.

No silent repair is permitted during verification.

## 9. Public/private boundary

The public repository may retain:

- selected runtime class;
- selected keyless path;
- GitHub public numeric repository/owner IDs;
- logical authority refs;
- schema/contract IDs;
- non-sensitive evidence hashes;
- PASS/HOLD outcomes.

It must not retain:

- service-account email;
- Google Cloud project ID/number if designated private by the materialization
  action;
- workload identity pool/provider locator when designated private;
- target Drive resource ID/URL;
- access tokens;
- external-account credential files;
- service-account keys;
- warehouse Production payload.

## 10. Fail-closed conditions

Required HOLD conditions include:

- runtime ref is not `refs/heads/main`;
- repository or owner numeric ID mismatch;
- WIF attribute condition is absent or weaker than this contract;
- user-managed service-account key exists;
- runtime uses downloaded private-key authentication;
- service-account IAM policy contains an unexpected impersonation principal;
- runtime attempts Workspace-user impersonation;
- target access depends on DWD instead of direct service-account sharing;
- provider state cannot be reacquired;
- verifier can only inspect creation output or screenshots;
- any required provider identifier/hash does not reconcile.

Unknown state = HOLD.

## 11. Design decision

Runtime placement:

**`GITHUB_ACTIONS_EXTERNAL_WORKLOAD / DEFAULT_BRANCH_MAIN_ONLY`**

Authentication:

**`OIDC -> WORKLOAD_IDENTITY_FEDERATION -> SERVICE_ACCOUNT_IMPERSONATION`**

Target access model:

**direct later Drive reader grant to the dedicated service account**

Workspace DWD for canonical target:

**`NOT_APPLICABLE_TO_CANONICAL_TARGET_BOUNDARY`**

Provider identity read-back:

**Google Cloud IAM service-account get + USER_MANAGED key list + IAM policy
read-back**

## 12. Promotion effect

The two Issue #96 design blockers are resolved at design level:

- `HOLD_KEYLESS_AUTH_PATH_UNRESOLVED` -> RESOLVED
- `HOLD_IDENTITY_PROVIDER_READBACK_CAPABILITY_UNBOUND` -> RESOLVED BY
  PROVIDER-NATIVE READBACK CONTRACT

This does **not** mean provider resources exist.

No service account, WIF pool/provider, IAM binding, Drive reader grant,
credential, token or executable acquisition is created by this decision.

## 13. Smallest next safe step

Next safe action:

`READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_ACTION_REREADINESS_V0_1`

That re-audit must confirm all Issue #96 prerequisites against this selected
runtime/read-back design before any service-account creation action is
authorized.

## Locked state

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = `HOLD`
- no service account created
- no WIF pool/provider created
- no IAM impersonation grant created
- no credential/key/token created
- no Drive/Sheets permission change
- no provider warehouse payload read
- no target-authority lifecycle change
- MASTER LIVE unchanged
