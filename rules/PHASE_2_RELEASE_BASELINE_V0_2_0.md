# Phase 2 Release Baseline v0.2.0

Release name: **Phase 2 Public Controls Baseline**

Status: **FROZEN PHASE 2 TAG — `v0.2.0` verified at canonical commit `218c8030252ea0fb23489a5631678925b2572978`**.

## Exact commit and tag policy

The `v0.2.0` tag is the immutable Phase 2 twelve-control baseline and has
been read back at `218c8030252ea0fb23489a5631678925b2572978`.
Later Phase 3 artifacts on `main` do not alter that frozen tag.

This is an engineering-control baseline. It is not production authority,
does not authorize live writes, and does not prove MASTER LIVE correctness.

## Inventory and responsibility

| No. | Control | Primary responsibility |
| --- | --- | --- |
| 01 | CROSS_YEAR_AUTHORITY_V0_1 | Validate explicit cross-year source authority. |
| 02 | SOURCE_POOL_AUTHORITY_V0_1 | Validate the exact authorized materialized source set and scope bindings. |
| 03 | HOLD_LIFECYCLE_CONTROL_V0_1 | Validate HOLD isolation, ordered readiness, transition intent, and read-back. |
| 04 | SERIAL_INTERVAL_INTEGRITY_V0_1 | Validate inclusive intervals, overlaps, and declared quantity. |
| 05 | NEGATIVE_STOCK_PREVENTION_V0_1 | Reject proposed issues exceeding available quantity. |
| 06 | RECONCILIATION_FORMULA_HEALTH_V0_1 | Check source-to-derived parity and formula presence/error health. |
| 07 | FAIL_CLOSED_RELEASE_GATES_V0_1 | Aggregate explicitly mapped native boolean or unknown gates. |
| 08 | DRY_RUN_MUTATION_CONTRACT_V0_1 | Validate a synthetic mutation manifest without a writer. |
| 09 | RANKED_PREFIX_ALLOCATION_LINEAGE_V0_1 | Rank and allocate an authorized candidate set with independent lineage verification. |
| 10 | READONLY_SHADOW_SNAPSHOT_INTEGRITY_V0_1 | Validate already-materialized in-memory surface shape, hashes, and atomicity markers. |
| 11 | MATERIALIZED_LINEAGE_REPLAY_V0_1 | Replay historical same-year lineage within supplied materialized candidates. |
| 12 | FORMULA_SEMANTIC_IDENTITY_V0_1 | Check an already-materialized QUERY formula against a hashed semantic contract. |

The dependency details are fixed by
`rules/PUBLIC_CONTROL_CATALOG_V0_1.md`; a passing component does not
implicitly grant another component authority. Control 03 may reuse Control 04
interval semantics. Control 08 consumes explicit upstream authority and hash
evidence; its invariant remains `production_write_authorized=False`, even on
PASS. Control 09 ranks only an already-authorized candidate set, using
`SOURCE_DATE_DESC | SOURCE_ROW_ASC | SERIAL_START_ASC`; its independent
verifier does not call allocator ranking or decision helpers. Control 11 may
invoke Control 09 for replay but is limited to
`MATERIALIZED_CANDIDATE_SET_ONLY`: MATCH proves parity in the supplied set,
not global candidate completeness. Control 10 accepts already-materialized
in-memory snapshots only, with no live provider or authority resolution.

Control 06 establishes formula presence/error health and source-to-derived
parity. Control 12 establishes semantic identity; neither implies the other
or cached-value freshness. Where both apply, compose independent native
boolean outcomes through Control 07. Unknown, missing, malformed, or string
status gates do not become PASS.

## Hash and version identities

Control 09 uses `SHA256_CANONICAL_JSON_V1` with distinct payload contracts
`RANKED_PREFIX_CANDIDATE_SET_HASH_V1` and
`RANKED_PREFIX_ALLOCATION_PLAN_HASH_V1`. Historical comparison requires
matching algorithm **and** contract ID; algorithm identity alone is insufficient.
Control 12 uses `SHA256_CANONICAL_QUERY_SEMANTICS_V1` and
`FORMULA_QUERY_SEMANTIC_HASH_V1` for its versioned semantic payload.
Other deterministic hashes remain scoped to their documented control contracts;
a digest by itself does not establish payload compatibility.

## Public boundary and deferred components

The public repository contains generic, side-effect-free controls and synthetic
tests. It contains no live warehouse data, real serials or invoices, identifiers
for connected resources, secrets, credentials, production connector, executable
writer, or live workbook/Drive/Sheets write path. It imports no private Git
history. No operation in this baseline changes MASTER LIVE.

Intentionally unmigrated: the monolithic outbound decision kernel; production
mapping; production snapshot validator; synthetic writer and shadow replay
harnesses; read-only shadow live/provider adapter; Wave A response-preimage and
governance workflow; production adapters, writers and connectors; and live Rule
Graph, BBGH and DDH operational semantics. This inventory is a scope boundary,
not an implementation backlog authorized by this release.

## Release evidence and repository gates

The pre-release canonical `main` read-back was
`64298a5162cde8dfc656afb2f83860e2754ae40d`.
Its push workflow log reported `REPOSITORY_BOUNDARY_PASS`,
`GIT_HISTORY_BOUNDARY_PASS`, `STATIC_QUALITY_PASS`,
`Ran 245 tests`, and `OK`. The release regression count must be rechecked
on the post-merge canonical main and recorded in the release notes.

The Main ruleset is expected to remain active for the default branch,
require squash pull requests, linear history, and strict status checks
`unit-tests` and `trusted-public-boundary`. The branch must remain protected
with no bypass. Both checks must pass on the exact PR head before squash merge
and again on the post-merge main before the tag is created.

Consolidation Audits v1–v4 were closed before this release candidate.
Release closure requires read-back of the manifest, main SHA, tag target,
release (if published), both push workflows, test log, ruleset, branch cleanup,
and the twelve-control README/catalog inventory.
