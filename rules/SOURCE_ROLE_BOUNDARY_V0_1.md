# SOURCE_ROLE_BOUNDARY_V0_1

Status: **PUBLIC PURE WAREHOUSE CONTROL — NO PRODUCTION AUTHORITY**

## Purpose

Implement the executable, side-effect-free boundary implied by RULE-0099 for
warehouse-serial business-write intent.

The control answers one narrow question:

> Is an explicitly classified warehouse region eligible to pass the
> SOURCE_OF_TRUTH / DERIVED_READ_ONLY write-intent boundary?

It does not write anything.

## Contract identity

`SOURCE_ROLE_BOUNDARY_V1`

## Input

`SourceRoleBoundaryRequest` contains:

- `contract_id`: exact `SOURCE_ROLE_BOUNDARY_V1`;
- `region_roles`: a native tuple containing the explicit region
  classification evidence;
- `requested_operation`: exact `BUSINESS_WRITE`.

Allowed role values are exactly:

- `SOURCE_OF_TRUTH`
- `DERIVED_READ_ONLY`

The region must be classified as **exactly one** allowed role.

No trimming, case-folding, truthiness coercion, list-to-tuple coercion, or
free-text approval is permitted.

## Decision

`SourceRoleBoundaryResult` returns:

- `status`: `PASS` or `HOLD`;
- `boundary_pass`: native boolean;
- `blocking_reasons`: deterministic sorted tuple;
- `production_write_authorized`: always native `False`.

PASS requires all of:

1. exact contract identity;
2. `region_roles` is a native tuple;
3. exactly one role is supplied;
4. the role is exactly `SOURCE_OF_TRUTH`;
5. `requested_operation` is exactly `BUSINESS_WRITE`.

`DERIVED_READ_ONLY` always blocks business-write intent.

PASS means only that this one public boundary invariant is satisfied. It never
authorizes a production mutation.

## Reason codes

- `CONTRACT_INVALID`
- `CLASSIFICATION_CONTAINER_INVALID`
- `CLASSIFICATION_MISSING`
- `CLASSIFICATION_CONTRADICTORY`
- `CLASSIFICATION_CARDINALITY_INVALID`
- `CLASSIFICATION_INVALID`
- `OPERATION_INVALID`
- `DERIVED_READ_ONLY_WRITE_BLOCKED`

Multiple independent blockers are returned in sorted order.

If both allowed roles are supplied, the result must include
`CLASSIFICATION_CONTRADICTORY`. Duplicate same-role declarations are not
treated as agreement; they fail exact-one cardinality.

## Adversarial requirements

| Synthetic case | Required result |
| --- | --- |
| exact SOURCE_OF_TRUTH + BUSINESS_WRITE | PASS |
| exact DERIVED_READ_ONLY + BUSINESS_WRITE | HOLD / DERIVED_READ_ONLY_WRITE_BLOCKED |
| both allowed roles | HOLD / CLASSIFICATION_CONTRADICTORY |
| duplicate SOURCE_OF_TRUTH roles | HOLD / CLASSIFICATION_CARDINALITY_INVALID |
| empty tuple | HOLD / CLASSIFICATION_MISSING |
| list instead of tuple | HOLD / CLASSIFICATION_CONTAINER_INVALID |
| blank/whitespace/unknown role | HOLD / CLASSIFICATION_INVALID |
| role with surrounding whitespace | HOLD / CLASSIFICATION_INVALID |
| lower-case role | HOLD / CLASSIFICATION_INVALID |
| blank/unknown/non-string operation | HOLD / OPERATION_INVALID |
| wrong contract identity | HOLD / CONTRACT_INVALID |
| any HOLD case | production_write_authorized=False |
| PASS case | production_write_authorized=False |

## Relationship to RULE-0099

RULE-0099 remains the canonical business rule:

- only SOURCE_OF_TRUTH accepts business-data writes;
- DERIVED_READ_ONLY is not writable;
- source read-back, formula health, and source↔derived reconciliation remain
  separate release obligations.

This control implements only the **role/write-intent boundary**. It does not
implement source read-back, formula validation, reconciliation, serial
integrity, HOLD release, or business authorization.

## Public boundary

The module is pure in-memory code using synthetic tests only. It has no
filesystem, network, workbook, provider, connector, credential, target
discovery, mutation executor, or live warehouse identity.

MASTER LIVE is out of scope.
