# PRG02_GITHUB_OIDC_WIF_MATERIALIZATION_V0_1

Status: **PASS_WIF_MATERIALIZED_PROVIDER_VERIFIED**

Issue: #127

## Purpose

Record public-safe evidence that the separately authorized PRG-02 GitHub
Actions OIDC Workload Identity Federation action has been materialized and
provider-native read-back has passed.

This artifact does not authorize a GitHub Actions token exchange, Drive/Sheets
target access, warehouse live read, executable acquisition, Production write or
MASTER LIVE mutation.

## Canonical runtime design

Runtime:

`GITHUB_ACTIONS_EXTERNAL_WORKLOAD / DEFAULT_BRANCH_MAIN_ONLY`

Authentication path:

`GITHUB_ACTIONS_OIDC -> GOOGLE_CLOUD_WORKLOAD_IDENTITY_FEDERATION ->
SERVICE_ACCOUNT_IMPERSONATION`

Public trust anchors:

- repository numeric ID: `1383239508`
- owner numeric ID: `300983965`
- ref: `refs/heads/main`
- issuer: `https://token.actions.githubusercontent.com`

Required mapping:

- `google.subject = assertion.sub`
- `attribute.repository_id = assertion.repository_id`
- `attribute.repository_owner_id = assertion.repository_owner_id`
- `attribute.ref = assertion.ref`

Required provider condition:

`assertion.repository_id == '1383239508' &&
 assertion.repository_owner_id == '300983965' &&
 assertion.ref == 'refs/heads/main'`

## Materialization result

Provider-native materialization and distinct verification established:

- WIF pool cardinality for this PRG-02 path = **1**
- GitHub OIDC provider cardinality in that pool = **1**
- provider state = **ACTIVE**
- issuer = **MATCH**
- attribute mapping = **MATCH**
- attribute condition = **MATCH**
- dedicated service-account federation binding count = **1**
- bound role = `roles/iam.workloadIdentityUser`
- USER_MANAGED service-account key count = **0**
- no additional WIF binding was observed

Public-safe canonical WIF configuration hash:

`397d1ad6ee08f0e7b6f7bfbc52dac647a814c82581152034fbb62020fd47b17b`

Verification evidence hash:

`d200d624dcb04f6bb1fb46e10b04a2761fdf62ec985fafed0848b28c8fa367e3`

Private provider locators, principal locators and private Drive evidence IDs are
not published.

## Explicit non-actions

This action did **not**:

- request a GitHub OIDC token;
- mint a Google access token;
- execute a GitHub Actions runtime job;
- add a Drive/Sheets reader grant;
- read warehouse Production payload;
- authorize executable acquisition;
- enable a Production writer;
- mutate MASTER LIVE.

## Final verdict

**`PRG02_GITHUB_OIDC_WIF_MATERIALIZATION_V0_1 =
PASS_WIF_MATERIALIZED_PROVIDER_VERIFIED`**

Locked:

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD

The next action, if separately authorized, is an exact GitHub Actions
OIDC-to-Google short-lived credential acceptance test. Target Drive reader
grant remains a separate later action.
