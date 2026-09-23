# Kho Serial OS

Public, sanitized engineering controls for serial-range warehouse workflows.

## Scope

This repository contains only generic control rules, side-effect-free Python
logic, synthetic tests, and CI.

It intentionally excludes operational warehouse data, real serial inventories,
invoices, delivery documents, workbook exports, connected Drive/Sheets
identifiers, credentials, secrets, and production write capability.

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

Phase 2 adds seven sanitized controls:

1. CROSS_YEAR_AUTHORITY_V0_1
2. SOURCE_POOL_AUTHORITY_V0_1
3. HOLD_LIFECYCLE_CONTROL_V0_1
4. SERIAL_INTERVAL_INTEGRITY_V0_1
5. NEGATIVE_STOCK_PREVENTION_V0_1
6. RECONCILIATION_FORMULA_HEALTH_V0_1
7. FAIL_CLOSED_RELEASE_GATES_V0_1

The authoritative public dependency/composition map is documented in
`rules/PUBLIC_CONTROL_CATALOG_V0_1.md`.

## Composition rule

A PASS from one control is not implicit authorization for another control.
Higher-level workflows must explicitly map already-scoped control outcomes into
their own inputs.

The generic release-gate aggregator accepts native booleans or unknown
(`None`) values only. It does not accept string status labels as implicit PASS.

The repository remains an engineering-control baseline, not an operational
database and not an authority for live warehouse state.
