# PRG02_GITHUB_OIDC_CREDENTIAL_ACCEPTANCE_V0_1

Status: **PASS_SHORT_LIVED_CREDENTIAL_ACCEPTANCE**

Issue: #129

## Purpose

Record public-safe acceptance evidence for the PRG-02 runtime authentication path:

`GitHub Actions OIDC -> Google Cloud Workload Identity Federation ->
service-account impersonation -> short-lived access token`.

This acceptance proves the authentication path only. It does not authorize
Drive/Sheets target access, warehouse Production reads, executable acquisition,
Production writes or MASTER LIVE mutation.

## Accepted runtime

The accepted run executed from:

- repository numeric ID: `1383239508`
- owner numeric ID: `300983965`
- branch: `main`
- workflow: `PRG-02 WIF Credential Acceptance`

Accepted main commit:

`1fbce8321ec84b7f2514b68fd70daba6c3a3737b`

Sanitized acceptance run:

`37106077065`

## Functional acceptance evidence

The sanitized run completed successfully and emitted:

- `OIDC_TOKEN_ISSUANCE=PASS`
- `STS_WIF_EXCHANGE=PASS`
- `SERVICE_ACCOUNT_IMPERSONATION=PASS`
- `SHORT_LIVED_ACCESS_TOKEN=PASS`
- `EXPECTED_PRINCIPAL_SECRET_PRESENT=PASS`

The access token lifetime requested by the workflow is 300 seconds and the
OAuth scope is read-only.

## Privacy / capability boundaries

The sanitized run also proved:

- `create_credentials_file=false`
- `export_environment_variables=false`
- `PROJECT_LOCATOR_EXPORTED=false`
- `TARGET_RESOURCE_READ_EXECUTED=false`
- `RESOURCE_WRITE_EXECUTED=false`

The workflow does not invoke a Drive/Sheets client and does not read warehouse
Production payload.

## Historical logging defect

An earlier functional run, `37105787660`, exposed a private project locator in
public workflow logs through exported Google project environment variables.

That logging path was remediated by PR #131 before the sanitized acceptance run.

Historical log containment/removal is tracked separately in #132 and does not
invalidate the functional authentication acceptance demonstrated by the
sanitized run.

Do not reproduce the private locator in public governance artifacts.

## Final verdict

**`PRG02_GITHUB_OIDC_CREDENTIAL_ACCEPTANCE_V0_1 =
PASS_SHORT_LIVED_CREDENTIAL_ACCEPTANCE`**

This verdict means the keyless runtime can obtain a short-lived Google
credential through the locked GitHub OIDC/WIF/service-account path.

It does **not** mean:

- Drive reader permission is granted;
- the target authority is readable by this identity;
- warehouse Production live-read is authorized;
- executable acquisition is authorized;
- Production write is authorized.

Locked:

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD

The next separately authorized step is target-access readiness / direct Drive
reader grant followed by PRG-03 effective-permission proof.
