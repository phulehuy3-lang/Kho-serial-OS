# PRG03_EFFECTIVE_DRIVE_PERMISSION_PROOF_V0_1

Status: **PASS_EFFECTIVE_DRIVE_PERMISSION_METADATA_ONLY**

Issue: #141

## Purpose

Record public-safe acceptance evidence that the dedicated PRG-02 runtime
identity can exercise its exact Drive reader permission through:

`GitHub Actions OIDC -> Google WIF -> service-account impersonation ->
Drive files.get`.

This proof is intentionally limited to minimal Drive metadata access.

## Accepted runtime

Accepted workflow:

- `PRG-03 Effective Drive Permission Proof`
- run ID: `37108886203`
- accepted attempt: `2`
- head SHA: `43418e7304d64c02fa33684fd30d043cc6c5bfad`
- conclusion: `success`

The first attempt failed closed with provider reason
`accessNotConfigured`. The only remediation was enabling
`drive.googleapis.com` on the existing runtime project. No IAM/WIF/Drive
permission broadening was introduced.

## PASS markers

Attempt #2 emitted:

- `OIDC_TOKEN_ISSUANCE=PASS`
- `STS_WIF_EXCHANGE=PASS`
- `SERVICE_ACCOUNT_IMPERSONATION=PASS`
- `SHORT_LIVED_ACCESS_TOKEN=PASS`
- `DRIVE_METADATA_GET=PASS`
- `DRIVE_EFFECTIVE_PERMISSION=PASS`
- `TARGET_LOCATOR_EXPORTED=false`
- `WORKSHEET_PAYLOAD_READ=false`
- `RESOURCE_WRITE_EXECUTED=false`

Runtime constraints:

- OAuth scope = `drive.metadata.readonly`
- exact Drive API method = `files.get`
- requested field = `kind` only
- target locator supplied through repository secret
- no repository checkout
- no credentials file
- no exported Google project environment
- no response body printed
- temporary response file removed before completion

Public acceptance snapshot SHA-256:

`6954f63b8c07cc160e463a178cf29f7f44a5955c8139fe1372a63c85d40b91c7`

## What this proves

This acceptance proves that:

1. GitHub Actions can mint an OIDC assertion under the locked main-branch trust;
2. Google WIF accepts the assertion;
3. the dedicated PRG-02 service account can be impersonated;
4. a short-lived Drive metadata token can be issued;
5. that runtime identity can successfully exercise the direct reader grant on
   the exact canonical target.

## What this does not prove

This metadata-only effective-permission PASS does not prove:

- exact five Production surface bindings;
- active serial-universe completeness;
- active HOLD-universe completeness;
- provider snapshot/version semantics;
- zero-write capability for a future acquisition adapter;
- tamper-evident receipt-store materialization;
- worksheet/cell payload read safety;
- executable acquisition readiness;
- Production write authority.

Therefore historical promotion blockers outside effective permission remain
separate.

## Locked state

After PRG-03:

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD

No MASTER LIVE business data was mutated.

## Verdict

**`PRG03_EFFECTIVE_DRIVE_PERMISSION_PROOF_V0_1 =
PASS_EFFECTIVE_DRIVE_PERMISSION_METADATA_ONLY`**
