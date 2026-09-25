# READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_V0_1

Status: **PARTIAL / HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE**

Issue: #109

## Purpose

Execute the separately authorized PRG-02 identity materialization action after
Issue #107 returned
`PASS_FOR_READONLY_IDENTITY_MATERIALIZATION_ACTION_ONLY`.

This action is fail-closed. Provider evidence must come from provider-native
Google Cloud IAM create/read-back capability. Screenshots, copied console
values, operator memory and manual assertions are not substitutes.

## 1. Pre-action state

Fresh pre-action read-back confirmed:

- target authority remained ACTIVE/PASS;
- target remained private and owner-only;
- Main ruleset remained protected by all five required checks;
- no service account, WIF resource, IAM grant, Drive reader grant or live
  runtime permission was authorized by the re-readiness step itself.

## 2. Private PRG-02 authority-store materialization

Completed:

`PRG02_READONLY_RUNTIME_IDENTITY_V1`

Required child topology was created:

1. `REGISTRY`
2. `PRINCIPAL_LOCATOR`
3. `EVIDENCE`
4. `RECOVERY`

The root is a private sibling control-plane boundary under the same private
authority-boundary class used for PRG-01.

Fresh Drive metadata read-back for the root and all four children confirmed:

- `shared = false`;
- exactly one owner permission;
- no reader/writer/group/domain grant.

Private provider folder IDs are intentionally excluded from this public
repository.

Opaque topology evidence hash:

`b18da7b917fc9c0e70123020547d67259940f39a1a2ff1725e4fd3214c92564e`

The hash binds the private root/child locators, parent relations, logical names
and owner-only/shared=false state.

Verdict:

**PASS — PRIVATE AUTHORITY-STORE BOUNDARY MATERIALIZED**

## 3. Dedicated service-account materialization

Required action:

Create exactly one
`GOOGLE_CLOUD_USER_MANAGED_SERVICE_ACCOUNT` for PRG-02 without generating or
uploading a user-managed private key.

Execution result:

**NOT EXECUTED**

Current operating capability does not expose Google Cloud IAM service-account
creation.

Plugin/tool discovery was performed before declaring this blocker. No
available Google Cloud IAM/service-account management connector was found for
this session.

A BigQuery connector was discoverable but unavailable and, in any case, is not
a substitute for Google Cloud IAM service-account lifecycle operations.

Blocker:

`HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE`

## 4. Private identity authority record

Required action:

Materialize exactly one private identity authority record after provider-native
service-account creation, binding:

- current target-authority ID/hash;
- PRODUCTION_SHADOW environment;
- service-account principal locator;
- KEYLESS_ONLY;
- NO_PERSISTED_PRIVATE_CREDENTIAL;
- governance authority refs;
- DWD not applicable/prohibited for the canonical target boundary;
- Workspace-user impersonation prohibited;
- lifecycle state;
- independent-readback state;
- deterministic identity-record hash.

Execution result:

**NOT EXECUTED**

Reason:

No valid principal locator exists until the service account is created.

No placeholder or guessed principal is permitted.

## 5. Provider-native verification

Required independent verification:

1. reacquire service account through Google Cloud IAM;
2. verify exact provider identity, unique ID/project binding and state;
3. list USER_MANAGED keys and require zero;
4. read service-account IAM policy;
5. reject unexpected principals/bindings;
6. recompute private identity-record hash;
7. use a verification event distinct from materialization.

Execution result:

**NOT EXECUTED**

Reason:

The current operating path does not expose provider-native Google Cloud IAM
read-back.

Screenshots/manual assertions were not used.

## 6. Explicit non-actions

This partial execution did **not**:

- create a service account;
- create/upload a service-account key;
- create a Workload Identity Pool or Provider;
- create an IAM impersonation grant;
- request an OIDC or Google access token;
- change Drive/Sheets target permissions;
- read warehouse Production payload;
- enable executable acquisition;
- enable a Production writer;
- alter target-authority lifecycle;
- mutate MASTER LIVE.

## 7. Materialization action result

Completed component:

- private PRG-02 authority-store topology: **PASS**

Uncompleted required components:

- dedicated service account: **HOLD**
- private identity authority record: **HOLD**
- provider-native IAM independent read-back: **HOLD**

Overall action verdict:

**`READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_V0_1 =
PARTIAL / HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE`**

Issue #109 must remain OPEN until the provider-native IAM creation/read-back
capability is available and the remaining materialization steps pass.

## 8. Smallest next safe step

Bind an execution path that supports provider-native Google Cloud IAM
service-account lifecycle operations required by this contract.

Minimum required capabilities:

- create one user-managed service account;
- get the exact service account;
- list service-account keys by key type;
- get the service-account IAM policy.

The capability must support fresh read-back after creation.

Once available, resume Issue #109 from the service-account materialization
step. Do not recreate the already-materialized PRG-02 Drive topology.

## Locked state

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD
- service account not created
- WIF not created
- IAM impersonation grant not created
- no credential/key/token created
- no Drive/Sheets target permission change
- no warehouse Production read
- target authority unchanged
- MASTER LIVE unchanged
