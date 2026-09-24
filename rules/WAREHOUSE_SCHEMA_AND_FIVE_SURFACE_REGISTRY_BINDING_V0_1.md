# WAREHOUSE_SCHEMA_AND_FIVE_SURFACE_REGISTRY_BINDING_V0_1

Status: **PASS_SCHEMA_AND_FIVE_SURFACE_BINDINGS_MATERIALIZED**

## Purpose

Resolve the two remaining Phase B contract blockers without reading Production
worksheet payloads and without creating a target locator or target-authority
record.

Resolved blockers:

- `HOLD_PHASE_B_WAREHOUSE_SCHEMA_VERSION_NOT_BOUND`
- `HOLD_PHASE_B_FIVE_SURFACE_REGISTRY_BINDING_NOT_BOUND`

This artifact is public-safe and non-live.

## 1. Exact warehouse schema binding

Canonical value:

`warehouse_schema_version = WAREHOUSE_INBOUND_SCHEMA_V1`

Authoritative machine-readable contract:

`WAREHOUSE_INBOUND_SCHEMA_CONTRACT_V1.json`

Canonical contract SHA-256:

`75aff780d0caa1050e81e9cc913a501ccb54767c0706622763d5f1e4d34552c1`

The schema version is not an SOP version and is not inferred from the current
Production workbook.

It is a reviewed logical evidence contract derived from already-public controls
for the locked scenario:

`INBOUND_SERIAL_QUERY_DERIVED_V1`

Any incompatible field/type/cardinality/role change requires a new
`warehouse_schema_version`.

## 2. Schema scalar rules

Text values that identify tasks, scopes, captures, fields, intervals, holds and
anchors must be native non-blank text with no surrounding whitespace.

Normalized serial/range quantities are native non-negative integers.

Native booleans are not accepted as integers.

Boolean fields require native booleans.

Nullable formula error state is represented only as native text or `null`.

No silent trimming, case-folding, string-to-integer conversion, truthiness
conversion or default filling is part of this schema.

## 3. INBOUND_SOURCE_RECORD

Role:

`SOURCE_OF_TRUTH`

Cardinality:

`EXACTLY_ONE_RECORD`

Required logical fields:

| field | type |
| --- | --- |
| `task_id` | TEXT |
| `scope_id` | TEXT |
| `capture_marker` | TEXT |
| `serial_start` | NONNEGATIVE_INTEGER |
| `serial_end` | NONNEGATIVE_INTEGER |
| `declared_quantity` | NONNEGATIVE_INTEGER |

Required invariants:

- `serial_start <= serial_end`;
- `declared_quantity = serial_end - serial_start + 1`.

This is a logical normalized evidence contract, not a declaration of physical
Production columns.

## 4. ACTIVE_SERIAL_INTERVAL_UNIVERSE

Role:

`SOURCE_OF_TRUTH`

Cardinality:

`ZERO_OR_MORE_RECORDS_COMPLETE_UNIVERSE`

Each record contains exactly the logical fields:

- `interval_id: TEXT`
- `category: TEXT`
- `range_start: NONNEGATIVE_INTEGER`
- `range_end: NONNEGATIVE_INTEGER`

Required invariants:

- `range_start <= range_end`;
- `interval_id` unique within one materialized universe;
- completeness is separately evidenced by the external acquisition boundary.

A selected subset cannot satisfy this surface.

## 5. INBOUND_DERIVED_QUERY_PROJECTION

Role:

`DERIVED_READ_ONLY`

Cardinality:

`EXACTLY_ONE_RECORD`

Logical fields and native types are exactly the same reconciliation set as
`INBOUND_SOURCE_RECORD`:

- `task_id: TEXT`
- `scope_id: TEXT`
- `capture_marker: TEXT`
- `serial_start: NONNEGATIVE_INTEGER`
- `serial_end: NONNEGATIVE_INTEGER`
- `declared_quantity: NONNEGATIVE_INTEGER`

The derived surface is never writable business authority.

## 6. INBOUND_QUERY_FORMULA_ANCHOR

Role:

`DERIVED_READ_ONLY`

Cardinality:

`ONE_OR_MORE_RECORDS`

Each anchor contains:

- `anchor_id: TEXT`
- `formula_text: TEXT`
- `formula_present: BOOLEAN`
- `error_code: TEXT_OR_NULL`

`anchor_id` must be unique inside one materialized anchor set.

Formula semantic validation remains a separate control.

## 7. ACTIVE_HOLD_INTERVAL_UNIVERSE

Role:

`SOURCE_OF_TRUTH`

Cardinality:

`ZERO_OR_MORE_RECORDS_COMPLETE_UNIVERSE`

Each record contains:

- `hold_id: TEXT`
- `category: TEXT`
- `range_start: NONNEGATIVE_INTEGER`
- `range_end: NONNEGATIVE_INTEGER`
- `hold_flag: BOOLEAN`
- `status: TEXT`

Required invariants:

- `range_start <= range_end`;
- `hold_id` unique inside the materialized universe;
- only active or otherwise blocking HOLD records for the exact inbound scope
  belong in this universe;
- completeness remains separately evidenced.

## 8. Physical Production mapping boundary

This schema binds normalized logical evidence only.

It intentionally does **not** contain:

- workbook/resource ID;
- Drive ID;
- sheet ID;
- range ID;
- Production URL;
- provider account identifier;
- physical column name;
- current workbook title.

Exact Production surface-to-sheet/range bindings remain a later PRG-04
responsibility.

Therefore this schema can be reviewed and versioned without reading Production
worksheet payload.

## 9. Five-surface registry binding

Canonical ID:

`surface_registry_id = SR1_HCM_SERIAL_INBOUND_V1`

Authoritative canonical payload:

`FIVE_SURFACE_REGISTRY_V1.json`

Canonical SHA-256:

`surface_registry_hash = d06d7297abcc460b3672e9ad4280f4bc5ca309e73933d5c22fae64048b30ca9a`

The registry binds:

`warehouse_schema_version = WAREHOUSE_INBOUND_SCHEMA_V1`

and exactly these five unique logical surfaces in ordinal order:

1. `INBOUND_SOURCE_RECORD` — `SOURCE_OF_TRUTH`
2. `ACTIVE_SERIAL_INTERVAL_UNIVERSE` — `SOURCE_OF_TRUTH`
3. `INBOUND_DERIVED_QUERY_PROJECTION` — `DERIVED_READ_ONLY`
4. `INBOUND_QUERY_FORMULA_ANCHOR` — `DERIVED_READ_ONLY`
5. `ACTIVE_HOLD_INTERVAL_UNIVERSE` — `SOURCE_OF_TRUTH`

No wildcard, optional sixth surface or caller-defined surface is permitted.

## 10. Canonical hashing

Both JSON authority payloads use:

- UTF-8;
- no BOM;
- lexicographically sorted object keys;
- compact separators `,` and `:`;
- exact JSON native scalar types;
- array order preserved;
- no provider metadata;
- no generated timestamp in hash input.

The SHA-256 digest is computed over the canonical JSON bytes excluding only the
trailing file newline used by repository text storage.

Schema canonical hash:

`75aff780d0caa1050e81e9cc913a501ccb54767c0706622763d5f1e4d34552c1`

Registry canonical hash:

`d06d7297abcc460b3672e9ad4280f4bc5ca309e73933d5c22fae64048b30ca9a`

## 11. Phase B effect

After this artifact is merged through all required checks, the two contract
binding blockers from Issue #72 are cleared.

This does not itself authorize Phase B materialization.

The prior Phase B readiness decision must be rerun against these new bindings.

Still prohibited here:

- `ExternalTargetLocatorV1` creation;
- `InboundTargetAuthorityRegistryRecordV1` creation;
- Drive permission changes;
- Production payload read;
- executable acquisition;
- Production write;
- MASTER LIVE mutation.

## Final state

**WAREHOUSE_SCHEMA_AND_FIVE_SURFACE_REGISTRY_BINDING_V0_1 =
`PASS_SCHEMA_AND_FIVE_SURFACE_BINDINGS_MATERIALIZED`**

**warehouse_schema_version =
`WAREHOUSE_INBOUND_SCHEMA_V1`**

**warehouse schema hash =
`75aff780d0caa1050e81e9cc913a501ccb54767c0706622763d5f1e4d34552c1`**

**surface_registry_id =
`SR1_HCM_SERIAL_INBOUND_V1`**

**surface_registry_hash =
`d06d7297abcc460b3672e9ad4280f4bc5ca309e73933d5c22fae64048b30ca9a`**

**Production locator = NOT CREATED**

**Target-authority record = NOT CREATED**

**PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED**

**LiveReadAuthorized=False**

**ExecutableAcquisitionAuthorized=False**

**ProductionWriteAuthorized=False**

**MASTER LIVE unchanged**
