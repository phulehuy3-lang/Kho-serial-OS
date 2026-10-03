# PRG-05/06 completeness and PRG-07 consistency — v0.1

Status: DESIGN / PURE SYNTHETIC COHERENCE ONLY. Runtime gates remain HOLD.

## Authoritative method required
A privately approved method must bind ACTIVE V2 target and registry hashes,
physical binding hash, method hash, task/scope and logical surface. Define exact
source table domain, active-state and scope predicates, blank/tombstone semantics,
hidden/filter handling and treatment of out-of-table records. Enumerate the full
authority domain BEFORE filtering. Headers and physical bindings alone do not
prove that the domain contains every relevant serial/HOLD record.

Record bounds and complete position coverage, response shape, termination,
truncation/limit status and consistency proof. An empty selected query is not
completeness evidence. A sealed empty domain still requires accepted authority
and termination proof. Missing, duplicate, extra or malformed positions fail
closed. Bound drift requires a new capture; never silently extend the scope.

The pure helper checks supplied coverage metadata for both serial and HOLD
universes. Its acceptance flags are caller assertions, not authenticated authority.
Context strings are compared for equality, not authenticated or hash-recomputed.
A coherent result must not be mapped directly to package completeness=True.
An external independent evidence verifier must first establish method provenance,
actual capture, record identity, source classification and provider consistency.
The helper does not inspect serial payload or validate row-level semantics.

## PRG-07 provider finding
Official references reviewed on 2026-10-03:
- https://developers.google.com/workspace/drive/api/reference/rest/v3/files
- https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/batchGet

Drive documents a monotonically increasing file version and restricts
headRevisionId to binary content. Sheets values.batchGet returns requested ranges;
its response contract does not supply a shared immutable snapshot token for the
five surfaces. Inference: these references alone do not establish the required
cross-surface Control 10 consistency primitive for native Sheets.

Decision: HOLD_PROVIDER_VERSION_SEMANTICS_UNPROVEN. Equal before/after version
checks are useful drift detection, not an accepted atomicity proof. Caller time,
file modifiedTime, response order and one HTTP request must not replace provider
snapshot authority. Dynamic formula/external dependencies and formula-vs-value
capture require explicit treatment. If no defensible consistency method can be
independently accepted, abort; any alternative immutable snapshot architecture
requires a separate reviewed design and scope authorization.

## Acceptance evidence and negative matrix
Method authority approval, independent review, exact bounds/predicates and private
record hash are still missing. Demonstrate whole-domain enumeration with synthetic
fixtures first; then actual capture only after separate promotion and authorization.
Test omissions, hidden/filter subsets, duplicate/out-of-domain positions, empty
responses, wrong task/scope/surface/consistency context, pseudo-booleans, unknown
termination, cap/truncation and drift. Fixture success does not close PRG-05/06.

## Boundary
No provider SDK, network acquisition, discovery, credential, runtime workflow,
permission mutation, receipt-store materialization or warehouse writer is added.
LiveReadAuthorized=False; ExecutableAcquisitionAuthorized=False;
ProductionWriteAuthorized=False; Production writer HOLD.
PHU-20 remains In Progress/Blocked. PRG-08/09 require separate materialized proof.
