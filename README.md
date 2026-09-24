# Kho Serial OS

Public, sanitized engineering controls for serial-range warehouse workflows.

## Scope

**Sole mission:** this repository exists only for serial-range warehouse controls.
It must not evolve into a general-purpose control framework.

Every rule, script, test, design document, and CI capability must directly
support inbound, outbound, inventory, serial identity/range, source allocation,
HOLD/quarantine, reconciliation, warehouse-document integrity, or repository
safety for those warehouse-serial functions.

The canonical scope rule is
`rules/WAREHOUSE_SERIAL_REPOSITORY_SCOPE_V1.md`; exact-set registration is
enforced by `rules/WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json` and
`scripts/check_warehouse_serial_scope_v1.py`.

This repository contains only sanitized, side-effect-free engineering controls,
synthetic tests, and CI serving that sole mission.

It intentionally excludes operational warehouse data, real serial inventories,
invoices, delivery documents, workbook exports, connected Drive/Sheets
identifiers, credentials, secrets, production write capability, and unrelated
PHÚ OS, finance, fiction, communications, or general personal-automation logic.

## Safety model

- fail closed when a required control input is missing, unknown, or malformed;
- preserve serial identity as text where identity fidelity matters;
- treat derived views as read-only;
- separate engineering validation from production authorization;
- keep control modules side-effect-free;
- use synthetic data in tests;
- require both repository-boundary checks before merge.

## Public control baseline

The bootstrap baseline provides:

- deterministic NEAREST-PRIOR source ordering;
- SOURCE_OF_TRUTH / DERIVED_READ_ONLY boundary enforcement;
- public-boundary and static-capability CI.

Phase 2 adds twelve sanitized controls:

1. CROSS_YEAR_AUTHORITY_V0_1
2. SOURCE_POOL_AUTHORITY_V0_1
3. HOLD_LIFECYCLE_CONTROL_V0_1
4. SERIAL_INTERVAL_INTEGRITY_V0_1
5. NEGATIVE_STOCK_PREVENTION_V0_1
6. RECONCILIATION_FORMULA_HEALTH_V0_1
7. FAIL_CLOSED_RELEASE_GATES_V0_1
8. DRY_RUN_MUTATION_CONTRACT_V0_1
9. RANKED_PREFIX_ALLOCATION_LINEAGE_V0_1
10. READONLY_SHADOW_SNAPSHOT_INTEGRITY_V0_1
11. MATERIALIZED_LINEAGE_REPLAY_V0_1
12. FORMULA_SEMANTIC_IDENTITY_V0_1

Phase 3 adds one scoped, pure composition preflight:

13. REQUIRED_GATE_SET_PREFLIGHT_V0_1

The authoritative public dependency/composition map is documented in
`rules/PUBLIC_CONTROL_CATALOG_V0_1.md`.

The Phase 2 `v0.2.0` tag remains the frozen twelve-control release. Control 13
is a later main-branch addition and does not alter that tag.

## Composition rule

A PASS from one control is not implicit authorization for another control.
Higher-level workflows must explicitly map already-scoped control outcomes into
their own inputs.

The generic release-gate aggregator accepts native booleans or unknown
(`None`) values only. It does not accept string status labels as implicit PASS.

The dry-run mutation contract may depend on an already-resolved source-pool
authority decision, but a PASS still never grants production write authority.

The ranked-prefix lineage control accepts an already-authorized candidate set,
reuses the canonical NEAREST-PRIOR ordering, and keeps its independent verifier
on a separate implementation path.

The read-only shadow snapshot control validates only already-materialized
in-memory surface data; it contains no provider, connector, credential, target
discovery, authority resolver, or replay engine.

The materialized-lineage replay control reconstructs historical same-year
availability from verified lineage evidence and replays Control 09 only within
the explicitly supplied materialized candidate set. A MATCH is not proof of
global candidate completeness.

Formula health and formula semantic identity are intentionally separate:
Control 06 checks formula presence/error health, while Control 12 checks whether
a materialized QUERY formula still matches an explicit semantic contract.

Control 13 validates exact coverage against a caller-declared required gate
set before Control 07 aggregates its complete boolean/unknown map. It does not
establish which business gates the caller should declare.

The repository remains an engineering-control baseline, not an operational
database and not an authority for live warehouse state.
