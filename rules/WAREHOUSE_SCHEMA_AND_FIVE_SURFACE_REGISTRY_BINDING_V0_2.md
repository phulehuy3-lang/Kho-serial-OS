# WAREHOUSE_SCHEMA_AND_FIVE_SURFACE_REGISTRY_BINDING_V0_2

Status: **PASS_SCHEMA_V2_AND_REGISTRY_V2_MATERIALIZED**

Issue: #146

## Purpose

Version the public inbound warehouse evidence schema so serial identity matches
current Production semantics without changing Production storage.

This revision supersedes V0_1 only for the current logical evidence contract.
V1 artifacts remain immutable historical evidence.

## 1. Warehouse schema V2

Canonical value:

`warehouse_schema_version = WAREHOUSE_INBOUND_SCHEMA_V2`

Machine-readable contract:

`WAREHOUSE_INBOUND_SCHEMA_CONTRACT_V2.json`

Canonical SHA-256:

`9a7036828810234062496179c1fe652b9078b1cd7fbe7f50e77e6991b33de203`

## 2. SERIAL_TEXT semantics

Serial identity fields are strict native text:

- non-blank;
- no surrounding whitespace;
- ASCII digits only;
- lexical identity preserved exactly;
- leading zeroes preserved;
- silent TEXT-to-INTEGER or INTEGER-to-TEXT coercion prohibited.

Numeric projection is permitted only for interval ordering and inclusive
cardinality calculations.

The numeric projection is not an identity rewrite.

Declared quantity remains a native non-negative integer.

## 3. Affected surfaces

The following fields now use `SERIAL_TEXT`:

- `INBOUND_SOURCE_RECORD.serial_start`
- `INBOUND_SOURCE_RECORD.serial_end`
- `ACTIVE_SERIAL_INTERVAL_UNIVERSE.range_start`
- `ACTIVE_SERIAL_INTERVAL_UNIVERSE.range_end`
- `INBOUND_DERIVED_QUERY_PROJECTION.serial_start`
- `INBOUND_DERIVED_QUERY_PROJECTION.serial_end`
- `ACTIVE_HOLD_INTERVAL_UNIVERSE.range_start`
- `ACTIVE_HOLD_INTERVAL_UNIVERSE.range_end`

No surface is added or removed.

## 4. Control 04 compatibility

`serial_text_interval_projection_v0_1` validates lexical serial identity and
creates a numeric `SerialInterval` only for Control 04 interval math.

It never rewrites the stored/materialized serial identity.

This preserves the existing pure interval-control implementation while making
the schema compatible with Production's TEXT serial requirement.

## 5. Five-surface registry V2

Canonical registry:

`FIVE_SURFACE_REGISTRY_V2.json`

Canonical ID:

`surface_registry_id = SR1_HCM_SERIAL_INBOUND_V2`

Canonical SHA-256:

`2c45382441fb98003b7ccb7161944de938a1f91ee8199e1c26771bf6c6d9fbad`

The registry still contains exactly the same five surfaces and role ordering.
Only its schema binding is versioned to `WAREHOUSE_INBOUND_SCHEMA_V2`.

## 6. V1 preservation

The following remain unchanged as historical authority artifacts:

- `WAREHOUSE_INBOUND_SCHEMA_CONTRACT_V1.json`
- `FIVE_SURFACE_REGISTRY_V1.json`
- their V0_1 binding/review artifacts.

No old hash or ID is relabelled as V2.

## 7. Target-authority migration boundary

The currently ACTIVE private target-authority record was independently
fresh-read during this review and remains bound to the V1 schema/registry
generation.

This V0_2 public materialization does **not** mutate or silently reinterpret that
private authority record.

Therefore target-authority compatibility remains a separate lifecycle action.

Canonical next blocker after schema V2 merge:

`HOLD_TARGET_AUTHORITY_SCHEMA_REGISTRY_REBIND_REQUIRED`

## 8. Locked authority state

This schema migration does not authorize:

- live worksheet acquisition;
- executable acquisition;
- Production write;
- MASTER LIVE mutation.

Locked:

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`

## Verdict

**`WAREHOUSE_SCHEMA_AND_FIVE_SURFACE_REGISTRY_BINDING_V0_2 =
PASS_SCHEMA_V2_AND_REGISTRY_V2_MATERIALIZED`**
