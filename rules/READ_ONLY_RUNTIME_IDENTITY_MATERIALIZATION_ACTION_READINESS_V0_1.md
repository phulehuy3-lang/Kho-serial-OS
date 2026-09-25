# READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_ACTION_READINESS_V0_1

Status: **HOLD_READONLY_IDENTITY_MATERIALIZATION_NOT_READY**

Issue: #96

## Purpose

Re-audit whether PRG-02 is ready for a separately authorized materialization
action after the canonical identity class was selected.

Canonical identity class:

`GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT / KEYLESS_ONLY`

This artifact is readiness/governance only. It does not create a service
account, credential, key, reader grant, provider session, live warehouse read,
Production writer, or MASTER LIVE mutation.

## Fresh provider and repository evidence — 2026-09-25

Fresh evidence establishes:

- the canonical target-authority registry contains exactly one current authority
  record;
- that authority record is `ACTIVE`;
- its independent read-back state is `PASS`;
- current target resolution remains unique at the authority layer;
- the canonical target remains private and provider permission read-back shows
  only the existing owner boundary;
- no target permission was changed by this audit;
- the active Main ruleset requires five checks:
  - `unit-tests`;
  - `trusted-public-boundary`;
  - `trusted-public-boundary-v2`;
  - `trusted-warehouse-serial-scope`;
  - `trusted-public-boundary-v3`.

The historical Issue #96 wording referred to four repository checks. That count
is superseded by the current provider ruleset. Readiness now requires
preservation of all five.

## 1. Target authority dependency

Verdict: **PASS**

The current target authority remains ACTIVE/PASS and unique.

This satisfies only the PRG-01 dependency for sequencing PRG-02. It does not
grant runtime access.

## 2. Identity authority store/location selection

Verdict: **PASS FOR READINESS DESIGN — NOT MATERIALIZED**

Selected private store class:

`RESTRICTED_GOOGLE_DRIVE_WORKSPACE`

Selected logical authority root:

`PRG02_READONLY_RUNTIME_IDENTITY_V1`

Placement rule:

- the future PRG-02 root must be a dedicated restricted sibling control-plane
  root under the same private authority boundary class used by the canonical
  PRG-01 store;
- it must not reuse the warehouse MASTER, operational journal, checkpoint
  workbook, public repository, or PRG-01 REGISTRY as the PRG-02 identity store.

Required logical children:

1. `REGISTRY`
2. `PRINCIPAL_LOCATOR`
3. `EVIDENCE`
4. `RECOVERY`

This audit selects the location architecture only. It does not create these
folders or any identity record.

The actual Drive IDs remain private and must not be committed to GitHub.

## 3. Governance authority binding

Verdict: **PASS FOR READINESS DESIGN**

Canonical logical authority refs:

- owner: `READONLY_RUNTIME_IDENTITY_OWNER`
- custodian: `READONLY_RUNTIME_IDENTITY_CUSTODIAN`
- rotation: `READONLY_RUNTIME_IDENTITY_ROTATION_AUTHORITY`
- revocation: `READONLY_RUNTIME_IDENTITY_REVOCATION_AUTHORITY`
- independent reviewer:
  `READONLY_RUNTIME_IDENTITY_INDEPENDENT_REVIEWER`

Governance mode:

`SOLO_OPERATOR_SELF_REVIEW_WITH_INDEPENDENT_EVIDENCE_PATH`

Locked disclosure:

`human_separation_of_duties = false`

Under the existing solo-operator governance exception, these logical roles may
resolve to the same human operator. This must never be described as independent
human review.

Materialization and provider verification must remain separate evidence events.
Verification must reacquire provider state rather than reuse the creation
payload.

Actual account identifiers remain private.

## 4. Credential boundary

Verdict: **PASS FOR STORAGE POLICY / HOLD FOR ISSUANCE PATH**

Locked credential policy:

`NO_PERSISTED_PRIVATE_CREDENTIAL`

Prohibited:

- service-account JSON/P12 private keys;
- downloaded private key material;
- credentials in GitHub;
- credentials in warehouse Drive;
- credentials in journal/checkpoints;
- embedded long-lived secrets.

Allowed in principle:

- provider-managed short-lived credentials only.

However, the exact issuance mechanism depends on the unresolved runtime
placement described in section 5.

## 5. Runtime placement and keyless authentication path

Verdict: **HOLD**

The design permits two mutually exclusive keyless paths:

1. attached service-account identity on an approved Google Cloud workload; or
2. Workload Identity Federation for an approved external workload, followed by
   short-lived service-account impersonation.

No current authority artifact selects the intended runtime placement.

Choosing either path without a runtime-placement decision would invent a
deployment assumption.

Blocker:

`HOLD_KEYLESS_AUTH_PATH_UNRESOLVED`

No identity materialization action may open until exactly one path is selected
and its prerequisites are evidenced.

## 6. User-managed key prohibition

Verdict: **PASS AT DESIGN LEVEL**

`user_managed_key_state = PROHIBITED`

Any future creation or upload of a user-managed service-account key invalidates
this readiness contract and returns PRG-02 to HOLD.

## 7. Domain-wide delegation and Workspace impersonation

Design verdict:

- `domain_wide_delegation = PROHIBITED`
- `workspace_user_impersonation = PROHIBITED`

Operational verification verdict: **HOLD**

The current connected provider capability can read Google Drive metadata but
does not provide Google Cloud IAM service-account administration/read-back or
Google Workspace Admin domain-wide-delegation read-back.

Therefore this audit cannot independently prove future service-account key
state, service-account configuration, or Workspace DWD state.

Blocker is carried with the provider-readback capability blocker below.

## 8. Provider-native independent identity read-back

Verdict: **HOLD**

The provider-native read-back contract is now fixed:

1. resolve the private principal locator;
2. reacquire the service account from Google Cloud IAM;
3. verify the expected service-account identity and enabled/disabled state;
4. list service-account keys and prove no user-managed private key exists;
5. verify domain-wide delegation is absent for the relevant Workspace
   authority boundary;
6. verify no Workspace-user impersonation path is authorized;
7. recompute the private identity authority record hash from freshly retrieved
   state;
8. record a distinct verification event;
9. return PASS or HOLD only.

Google Cloud documents provider-native service-account/key read-back, and
Google Workspace documents domain-wide delegation as an Admin-console
authorization separate from direct Drive file sharing.

However, no connected Google Cloud IAM / Workspace Admin capability is
currently available in this operating path. The connected Drive capability is
not a substitute for IAM or Admin read-back.

Blocker:

`HOLD_IDENTITY_PROVIDER_READBACK_CAPABILITY_UNBOUND`

A screenshot, copied console value, declared `KEYLESS_ONLY` flag, or operator
memory is not sufficient independent evidence.

## 9. Target permission separation

Verdict: **PASS**

Identity materialization must not change target permissions.

Google Workspace service-account access to a specific Drive/Sheets resource is
a separate direct-sharing action. Creating or governing the Cloud service
account does not itself grant access to the warehouse target.

Fresh target metadata remains owner-only.

A later reader-grant action remains separate from both PRG-02 identity
materialization and PRG-03 effective-permission proof.

## 10. Repository protection

Verdict: **PASS**

The active Main ruleset requires all five current checks.

No PRG-02 action may rename, remove, bypass, or weaken any of them.

## Readiness matrix

| Requirement | Verdict |
| --- | --- |
| target authority ACTIVE/PASS and unique | PASS |
| private identity authority store/location selected | PASS FOR DESIGN |
| owner/custodian/rotation/revocation bindings | PASS FOR DESIGN |
| exactly one keyless runtime auth path selected | HOLD |
| user-managed keys prohibited | PASS |
| DWD prohibited | PASS AT DESIGN LEVEL |
| DWD/impersonation independently verifiable | HOLD |
| provider-native identity read-back operationally bound | HOLD |
| identity creation separated from target permission grant | PASS |
| all current repository checks retained | PASS |

## Readiness decision

The former identity-class, store-selection and governance-binding ambiguity is
now closed at design level.

Two material prerequisites remain unresolved:

1. `HOLD_KEYLESS_AUTH_PATH_UNRESOLVED`
2. `HOLD_IDENTITY_PROVIDER_READBACK_CAPABILITY_UNBOUND`

Therefore:

**`READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_ACTION_READINESS_V0_1 =
HOLD_READONLY_IDENTITY_MATERIALIZATION_NOT_READY`**

This HOLD is narrower than the earlier PRG-02 readiness HOLD and must not be
interpreted as a failure of the current target authority.

## Smallest next safe step

Next design/governance action:

`READ_ONLY_RUNTIME_IDENTITY_RUNTIME_PLACEMENT_AND_PROVIDER_READBACK_V0_1`

It must:

1. select exactly one intended runtime placement;
2. select exactly one keyless authentication path consistent with that
   placement;
3. identify the provider-native IAM read-back mechanism that will be available
   during identity materialization;
4. identify the Workspace DWD verification mechanism, or prove DWD is
   inapplicable to the selected account boundary;
5. require no service-account creation yet;
6. require no credential/key creation;
7. require no Drive permission change;
8. require no warehouse Production read;
9. keep PRG-03 separate.

Only after those prerequisites PASS may a separately authorized PRG-02 identity
materialization action be opened.

## Locked state

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = `HOLD`
- no service account created
- no credential/key created
- no Drive/Sheets permission change
- no provider warehouse payload read
- no target-authority lifecycle change
- MASTER LIVE unchanged
