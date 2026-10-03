# PRG02_HISTORICAL_RUN_CONTAINMENT_V0_1

Status: **PASS_HISTORICAL_LOG_CONTAINED**

Issue: #132

## Purpose

Record public-safe closure evidence for containment of one historical GitHub
Actions run whose public log exposed a project locator that project governance
treats as private.

This control does not reproduce the locator value.

## Preserved private audit evidence

Before deletion, the original historical log was preserved in the private
PRG-02 evidence store.

Public-safe evidence bindings:

- historical run ID: `37105787660`
- original raw-log SHA-256:
  `cf9a3c348ff3183bacfe6e1b6d84d13f4a36abe343663ca095895fdef7b88afe`
- sanitized replacement run ID: `37106077065`
- privacy remediation PR: #131
- containment execution PR: #134

The private evidence object remains owner-only and is not published.

## Containment execution

One-time helper workflow run `37106675321` executed on `main` with only:

- `actions: write`
- `contents: read`

The helper was hard-bound to the single historical run ID.

Observed markers:

- `HISTORICAL_RUN_DELETE_REQUEST=PASS`
- `HISTORICAL_RUN_GET_404=PASS`
- `HISTORICAL_RUN_CONTAINMENT=PASS`

An independent direct GitHub API read after deletion also returned
`404 Not Found` for the historical run.

Containment-log SHA-256:

`8d56ecf07a7a59cfdb161a9b3041743dd0a0a144cd8763f8e0de1d151a48afae`

## Privacy / operational boundary

The containment action did not:

- expose the private locator again;
- modify WIF pool/provider configuration;
- modify service-account IAM policy;
- create credentials or keys;
- change Drive/Sheets target permissions;
- read warehouse Production payload;
- mutate MASTER LIVE;
- enable a Production writer.

## Final verdict

**`PRG02_HISTORICAL_RUN_CONTAINMENT_V0_1 =
PASS_HISTORICAL_LOG_CONTAINED`**

The historical public run is no longer retrievable through the GitHub Actions
run endpoint.

The one-time helper workflow is removed as part of closure so no standing
repository action remains with this deletion purpose.

Locked state remains:

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD
