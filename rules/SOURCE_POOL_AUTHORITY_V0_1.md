# SOURCE_POOL_AUTHORITY_V0_1

Status: **PUBLIC BASELINE**

## Purpose

Define a fail-closed authority contract for validating whether a materialized
candidate source set is exactly covered by one structured canonical authority
record.

This control is pure and side-effect-free. It does not discover warehouse
sources, query external systems, mutate inventory, or authorize production
writes.

## Exact-set model

The public baseline supports one scope mode:

`EXACT_SOURCE_SET`

The authorized source identifiers and the materialized candidate source
identifiers must represent the same set. Ordering is not authoritative, but
duplicates, blanks, and empty sets are invalid.

## Required authority bindings

A source-pool decision may resolve to `PASS` only when all applicable
evidence is present and consistent:

1. authority ID;
2. task ID;
3. line key;
4. document date;
5. carrier/category;
6. denomination;
7. canonical source-pool registry identity;
8. expected registry schema;
9. registry read-back status;
10. exactly one matching authority record;
11. supported scope mode;
12. active record status;
13. explicit owner approval;
14. record-level read-back;
15. non-empty evidence reference;
16. valid authorized source set;
17. hash integrity;
18. exact equality between authorized and materialized source sets.

Any missing, malformed, duplicate, drifted, mismatched, or non-canonical
evidence returns `HOLD`.

## Non-authority inputs

The resolver intentionally does not infer authority from:

- free-text notes;
- sort-policy labels;
- UI state;
- generic transaction approvals;
- comments or operator intent.

## Integrity model

The authority record hash is SHA-256 over canonical JSON containing the
immutable authority fields.

## Public boundary

Examples and tests must use synthetic identifiers, dates, categories,
denominations, and evidence references only.
