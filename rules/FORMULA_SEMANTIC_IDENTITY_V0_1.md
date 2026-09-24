# FORMULA_SEMANTIC_IDENTITY_V0_1

Status: **STATE AT V0.1 CHECKPOINT — FROZEN V1 HASH DOMAIN / IN-MEMORY / READ-ONLY**

## Purpose


> Current-main migration note (2026-09-25): V1 hash/canonicalization remains
> frozen for historical compatibility. Current callers use
> `FORMULA_SEMANTIC_IDENTITY_V0_2`. V1 hashes must not be silently
> reinterpreted as V2 hashes.

Define a pure contract for validating whether a materialized QUERY formula still
has the exact semantics approved by an explicit contract.

This control complements formula-health checks. A formula can be present and
error-free while still being wrong because its source, select list, predicates,
header count, or executable wrapper changed.

This control performs no workbook read, external I/O, recalculation, formula
repair, or mutation.

## Contract

A formula-semantic contract binds:

- non-empty contract ID;
- query source expression;
- query text;
- non-negative native-integer header-row count;
- expected fallback text for the verified exported wrapper;
- deterministic contract hash.

The contract hash binds normalized core query semantics and the exact exported
fallback literal.

## Supported representations

Version 0.1 recognizes only two fully matched shapes:

1. native spreadsheet QUERY:

   `QUERY(source, "query text", header_rows)`

   Both comma and semicolon argument separators are accepted.

2. verified OOXML-export wrapper:

   `IFERROR(__xludf.DUMMYFUNCTION("QUERY(...)"), "fallback")`

An otherwise-canonical QUERY embedded inside additional executable outer logic
is rejected.

## Normalization

Core semantic comparison normalizes:

- source case;
- source whitespace;
- absolute-reference dollar signs;
- simple quoted sheet names;
- query text case;
- repeated whitespace;
- whitespace around commas and comparison operators.

Normalization does not reorder selected fields, predicates, or expressions.

The exported fallback literal is compared exactly because it changes observable
formula behavior.

## Semantic hash

The semantic SHA-256 hash binds normalized:

- source;
- query text;
- header-row count.

The hash is independent of native-vs-exported representation.

Algorithm ID:

`SHA256_CANONICAL_QUERY_SEMANTICS_V1`

Contract ID:

`FORMULA_QUERY_SEMANTIC_HASH_V1`

The v1 semantic payload and formula-contract payload are protected by golden
vector regressions. Changing canonicalization or payload fields without a new
version identifier is therefore a compatibility failure.

## Fail-closed behavior

Assessment returns HOLD for:

- invalid contract;
- missing/blank formula text;
- unsupported formula representation;
- source drift;
- query-text drift;
- header-row drift;
- exported fallback drift;
- semantic-hash mismatch.

A PASS means only semantic identity with the declared formula contract. It does
not prove formula health, cached-value freshness, source↔derived reconciliation,
or external recalculation.

## Scope boundary

This control does not:

- read spreadsheet/workbook files;
- decide which formula anchor is authoritative;
- inspect formula error state;
- validate cached projection values;
- authorize a release or mutation.

## Public boundary

Tests use synthetic source/table names, short formulas, and in-memory strings
only. No live sheet name, workbook path, external identifier, credential, or
production write path is included.
