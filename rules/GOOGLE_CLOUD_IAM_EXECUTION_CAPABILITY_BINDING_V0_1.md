# GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_BINDING_V0_1

Status: **PASS_PROVIDER_NATIVE_IAM_EXECUTION_CAPABILITY_BOUND**

Issue: #111
Blocked action: #109

## Purpose

Bind a provider-native Google Cloud IAM execution path that can resume
`READ_ONLY_RUNTIME_IDENTITY_MATERIALIZATION_V0_1` from the dedicated
service-account creation step.

This control does not authorize service-account creation by itself.

## 1. Current execution environment read-back

Fresh capability discovery on 2026-09-25 found:

- no ChatGPT tool exposing Google Cloud IAM service-account lifecycle
  operations;
- no installable/available Google Cloud IAM connector for this session;
- the only discovered Google Cloud-adjacent connector with IAM wording was a
  BigQuery connector that is disabled by administrator policy and is not a
  service-account lifecycle substitute;
- the current local execution environment has no `gcloud` executable;
- no Google Application Default Credentials environment binding is present;
- no Google-related credential environment is exposed to this execution path.

Therefore no provider-native IAM creation/read-back path is currently bound.

## 2. Required provider-native operations

The bound execution path must support all of the following against the selected
Google Cloud project/account boundary:

1. create exactly one user-managed service account;
2. reacquire that exact service account;
3. list its service-account keys and distinguish `USER_MANAGED` from
   `SYSTEM_MANAGED`;
4. require `USER_MANAGED = 0`;
5. retrieve the service-account IAM allow policy;
6. perform the read-back in a verification event distinct from the creation
   event.

Provider-native Google Cloud IAM methods corresponding to the required
read-back include:

- service-account get/list semantics;
- `projects.serviceAccounts.keys.list`;
- `projects.serviceAccounts.getIamPolicy`.

Google Cloud CLI/Console/Cloud Shell or a future first-party IAM connector may
be used only if they provide those provider-native semantics without exposing
long-lived credentials to the repository or warehouse control plane.

## 3. Accepted capability classes

A future execution path may satisfy this control only through one of these
classes:

### A. Connected provider-native Google Cloud IAM tool

Preferred.

Requirements:

- authenticated to the intended user/project boundary;
- supports service-account create/get;
- supports service-account key-list read-back;
- supports service-account IAM-policy read-back;
- does not expose private keys or long-lived credentials to ChatGPT/repository
  artifacts.

### B. Provider-native Google Cloud Console / Cloud Shell execution path

Acceptable only when the execution agent has direct authenticated access to the
user's Google Cloud Console/Cloud Shell session and can perform the provider
actions itself.

Manual screenshots or copied console values do not satisfy read-back.

### C. Authenticated Google Cloud CLI/API execution environment

Acceptable only when the execution environment is explicitly connected to the
user's Google Cloud project/account authority and the credential boundary is
approved.

Ambient or unknown credentials must never be used.

## 4. Rejected substitutes

The following do not bind the capability:

- Google Drive connector access;
- Gmail/Calendar/Contacts access;
- BigQuery IAM features;
- public web access to Google Cloud documentation;
- screenshots;
- copied command output supplied without provider reacquisition;
- operator memory;
- a locally installed CLI with no authenticated Google Cloud authority;
- guessed project/service-account identifiers;
- service-account JSON/P12 key files.

## 5. Current blocker proof

Current environment result:

`provider_native_iam_tool = ABSENT`

`installable_google_cloud_iam_plugin = ABSENT`

`gcloud_cli = ABSENT`

`google_application_default_credentials = ABSENT`

Therefore:

**`GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_BINDING_V0_1 =
HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE`**

## 6. Effect on Issue #109

Issue #109 remains OPEN.

Already-materialized Drive topology must be reused:

- `PRG02_READONLY_RUNTIME_IDENTITY_V1`
- `REGISTRY`
- `PRINCIPAL_LOCATOR`
- `EVIDENCE`
- `RECOVERY`

Do not recreate that topology.

Resume point after this blocker clears:

**dedicated service-account creation**

Then:

1. provider-native service-account reacquisition;
2. `USER_MANAGED` key list = zero;
3. IAM-policy read-back;
4. private identity-authority record materialization;
5. deterministic record-hash recomputation;
6. separate verification event.

## 7. Explicitly out of scope

This blocker-resolution control does not authorize:

- WIF pool/provider creation;
- `roles/iam.workloadIdentityUser`;
- GitHub OIDC setup;
- access-token minting;
- Drive/Sheets target sharing;
- warehouse Production read;
- executable acquisition;
- Production writer;
- target-authority lifecycle mutation;
- MASTER LIVE mutation.

## 8. Smallest next safe step

Expose or connect one provider-native Google Cloud IAM execution path satisfying
Section 3.

Once such a path is actually available, re-run this binding control. Only a
PASS result may resume #109.


## 9. Active execution-path probing — 2026-09-25

After the initial HOLD, the operating session attempted two provider-native
execution paths rather than stopping at catalog discovery.

### 9.1 Local Google Cloud CLI path

Attempt:

- verified Linux x86_64 / 64-bit runtime;
- verified no existing `gcloud`;
- attempted to download the official Google Cloud CLI Linux archive from
  Google's documented `dl.google.com` distribution endpoint.

Result:

**HOLD**

The execution container could not resolve `dl.google.com`, so the archive
could not be downloaded and no CLI installation occurred.

Security result:

- no OAuth flow was started;
- no Google credential was created or stored;
- no project was selected;
- no service-account action was attempted.

This failure is an execution-network limitation, not proof that Google Cloud
CLI itself is unsuitable.

### 9.2 Google Cloud CLI Remote MCP path

Google Cloud's official Cloud CLI remote MCP server was evaluated as a possible
provider-native execution path.

Google's current documentation states that the remote MCP server supports
`gcloud` execution generally but explicitly excludes the
`gcloud iam service-accounts` command group.

Because Issue #109 requires service-account create/get plus key and IAM-policy
read-back, the remote MCP server cannot satisfy this control.

Result:

**REJECTED_FOR_PRG02_SERVICE_ACCOUNT_LIFECYCLE**

This is a product-capability mismatch, not an authentication failure.

### 9.3 Updated blocker proof

Current environment result is now stronger than discovery-only evidence:

- provider-native IAM connector: ABSENT;
- installable IAM plugin: ABSENT;
- existing local gcloud: ABSENT;
- attempted official CLI download: BLOCKED_BY_RUNTIME_DNS;
- Google Cloud CLI Remote MCP: AVAILABLE IN GENERAL, but
  `gcloud iam service-accounts` explicitly UNSUPPORTED;
- ADC binding: ABSENT.

Therefore the overall verdict remains:

**`HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE`**

The blocker is now demonstrated by active execution-path probing.

## 10. Remaining viable execution classes

After active probing, the viable classes are narrowed to:

1. a future provider-native Google Cloud IAM connector that exposes
   service-account lifecycle operations; or
2. an authenticated Google Cloud Console/Cloud Shell execution path that the
   execution agent can directly control; or
3. an explicitly authorized CLI/API environment where Google Cloud CLI/API
   access is already available and provider state can be freshly reacquired.

The Google Cloud CLI Remote MCP server is explicitly not sufficient for #109
under its current command restrictions.


## Locked state

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD
- no service account created
- no user-managed service-account key created
- no WIF resource created
- no IAM impersonation grant created
- no Drive/Sheets target permission change
- no warehouse Production read
- target authority unchanged
- MASTER LIVE unchanged


## 11. Capability re-audit — 2026-10-03

Fresh capability discovery was repeated after PHU-8 closure.

Current ChatGPT/plugin/runtime evidence:

- no connected ChatGPT tool exposes Google Cloud IAM service-account lifecycle
  operations;
- plugin discovery still exposes no installable Google Cloud IAM/service-account
  lifecycle connector;
- the BigQuery connector remains disabled by administrator policy and is not a
  substitute for the required service-account create/get/key-list/IAM-policy
  sequence;
- the current execution container still has no `gcloud` executable;
- `GOOGLE_APPLICATION_CREDENTIALS` is unset and no Application Default
  Credentials file is present.

Google's current official documentation exposes an IAM remote MCP server, but
its published MCP reference currently exposes tools for IAM v1 roles and v2 deny
policies rather than service-account lifecycle operations. It therefore does
not satisfy Issue #109's required create/get/key-list/IAM-policy sequence.

Google's current Cloud CLI remote MCP documentation also lists
`gcloud iam service-accounts` among unsupported command groups, so that
remote MCP path cannot satisfy Issue #109 either.

A separate remote-terminal connector to a user-controlled machine is
discoverable in the ChatGPT plugin catalog. It can satisfy accepted class C
only after the user explicitly connects an authorized machine and the session
freshly proves an authenticated Google Cloud project/account boundary with CLI
or direct REST/API capability for the required service-account operations.
Discovery alone does not clear this control.

Verdict remains:

**`HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE`**

Updated viable next paths:

1. connect an explicitly authorized user-controlled terminal/Cloud Shell/CLI or
   direct REST/API environment and prove authenticated project/account authority
   before any IAM mutation; or
2. use a future connector only if its exact published tool list actually exposes
   service-account create/get, USER_MANAGED key-list and service-account
   IAM-policy read-back.

The current Google IAM remote MCP server is **not** such a connector.

The existing PRG-02 Drive topology must not be recreated.



## 12. Capability binding PASS — 2026-10-03

A user-controlled Windows execution path was explicitly connected and
authenticated through Google Cloud CLI.

Fresh provider-native evidence established:

- an authenticated user-controlled Google Cloud CLI session exists;
- exactly one visible ACTIVE project boundary was selected for this action;
- project metadata read-back succeeded;
- service-account get/describe succeeded;
- service-account USER_MANAGED key-list read-back succeeded;
- service-account IAM-policy read-back succeeded;
- project-level permission testing proved `iam.serviceAccounts.create` is
  granted to the authenticated operator.

The capability proof used provider-native CLI/API read-back rather than
screenshots or copied console values.

No service account, key, Workload Identity Federation resource, impersonation
grant, Drive/Sheets permission, warehouse Production payload, MASTER LIVE
business data or Production writer state was changed while proving this
capability.

Therefore:

**`GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_BINDING_V0_1 =
PASS_PROVIDER_NATIVE_IAM_EXECUTION_CAPABILITY_BOUND`**

Issue #111 may close. Issue #109 may resume only from its locked dedicated
service-account materialization step.
