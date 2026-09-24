# SOURCE_READBACK_V0_1

Status: **PUBLIC PURE WAREHOUSE CONTROL — NO LIVE READ / NO PRODUCTION AUTHORITY**

## Purpose

Validate one already-materialized warehouse source read-back against an
explicit expected source record after a proposed inbound source update.

This control is the public producer for the `source_readback` gate in
`INBOUND_SERIAL_QUERY_DERIVED_V1`.

It does not perform the read. It compares only supplied in-memory evidence.

## Non-duplication boundary

This invariant is distinct from existing controls:

- Control 10 validates snapshot structure, schema binding and version-marker
  atomicity, but does not compare a declared expected source value set against
  a read-back value set.
- Control 06 can compare two mappings exactly, but does not bind the comparison
  to one task, scope and capture marker.

SOURCE_READBACK_V0_1 adds only the narrow expected-vs-read-back value/binding
contract required by inbound source verification. It introduces no live reader,
hash authenticity claim, or new mutation authority.

## Contract identity

`SOURCE_READBACK_V1`

## Input schema

`SourceFieldValue`:

- `field_id`: exact non-blank text with no surrounding whitespace;
- `value`: one supported scalar.

Supported scalar values are exactly:

- text;
- native integer;
- native boolean;
- `None`.

Floats, containers and custom objects are invalid. Exact type equality is
required, so native boolean `True` is not equal to native integer `1`.

`MaterializedSourceRecord`:

- `task_id`: exact non-blank text;
- `scope_id`: exact non-blank text;
- `capture_marker`: exact non-blank text;
- `fields`: non-empty native tuple of `SourceFieldValue` records.

Field IDs must be unique inside each record. Field order is not semantically
significant; comparison is by exact field ID.

`SourceReadbackRequest`:

- `contract_id`: exact `SOURCE_READBACK_V1`;
- `expected_record`: required `MaterializedSourceRecord`;
- `readback_record`: either a `MaterializedSourceRecord` or `None`.

`None` is the only representation of missing read-back evidence.

No trimming, case-folding, string coercion, scalar coercion, list-to-tuple
coercion or implicit field filling is allowed.

## Binding rule

Expected and read-back records must have exact equality for:

- `task_id`;
- `scope_id`;
- `capture_marker`.

The capture marker is an equality binding supplied by the caller. It does not
prove wall-clock freshness, atomicity, source authority or live-read origin.

## Exact read-back rule

PASS requires:

1. exact contract identity;
2. valid expected record;
3. present and valid read-back record;
4. exact task/scope/capture binding;
5. exact field-ID set equality;
6. exact scalar type equality for each field;
7. exact scalar value equality for each field.

Missing or extra read-back fields block PASS. Duplicate field IDs block PASS.
No subset comparison is permitted.

## Result

`SourceReadbackResult` returns:

- `status`: `PASS` or `HOLD`;
- `readback_match`: native boolean;
- `blocking_reasons`: deterministic sorted tuple;
- `production_write_authorized`: always native `False`.

PASS means only that the supplied already-materialized source record exactly
matches the expected record under this contract.

PASS does not prove:

- that an external read actually occurred;
- that the read was authorized;
- that the capture marker is fresh or atomic;
- that the source region is SOURCE_OF_TRUTH;
- that derived formulas are healthy;
- that source↔derived reconciliation passed;
- that any inventory write is authorized.

## Reason codes

- `CONTRACT_INVALID`
- `EXPECTED_RECORD_INVALID`
- `READBACK_MISSING`
- `READBACK_RECORD_INVALID`
- `BINDING_MISMATCH`
- `FIELD_SET_MISMATCH`
- `TYPE_MISMATCH`
- `VALUE_MISMATCH`

Malformed identifiers, invalid field containers, duplicate field IDs,
unsupported scalar values, or invalid field records make the corresponding
record invalid.

When a record is invalid, the evaluator does not manufacture secondary
field-set/value mismatch claims from unusable evidence.

## Adversarial requirements

| Synthetic case | Required result |
| --- | --- |
| exact expected/read-back match | PASS |
| read-back is None | HOLD / READBACK_MISSING |
| wrong contract identity | HOLD / CONTRACT_INVALID |
| malformed expected record | HOLD / EXPECTED_RECORD_INVALID |
| malformed read-back record | HOLD / READBACK_RECORD_INVALID |
| task/scope/capture differs | HOLD / BINDING_MISMATCH |
| read-back omits one field | HOLD / FIELD_SET_MISMATCH |
| read-back adds one field | HOLD / FIELD_SET_MISMATCH |
| duplicate field ID | corresponding RECORD_INVALID |
| bool vs int | HOLD / TYPE_MISMATCH |
| text vs integer | HOLD / TYPE_MISMATCH |
| same type, different value | HOLD / VALUE_MISMATCH |
| float/container/custom scalar | corresponding RECORD_INVALID |
| leading-zero text identity changes | HOLD / VALUE_MISMATCH |
| any HOLD result | production_write_authorized=False |
| PASS result | production_write_authorized=False |

## Relationship to inbound acceptance

This control produces only the `source_readback` boolean evidence.

The inbound profile must still independently require:

- source-role boundary;
- serial range quantity;
- serial overlap freedom;
- source↔derived reconciliation;
- formula health;
- formula semantics;
- separate `hold_conflict`.

No PASS may substitute for another gate.

## Public boundary

Tests use synthetic short IDs and values only. The implementation has no
filesystem, network, workbook, provider, connector, credential, target
discovery, live-read or mutation capability.

MASTER LIVE is out of scope.
