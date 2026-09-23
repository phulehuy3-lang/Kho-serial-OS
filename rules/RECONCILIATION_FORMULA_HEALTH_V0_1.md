# RECONCILIATION_FORMULA_HEALTH_V0_1

Status: **PUBLIC BASELINE**

## Purpose

Define two pure fail-closed controls for derived read models:

1. exact source-to-derived reconciliation of normalized metrics;
2. formula-anchor health validation.

These controls complement the public SOURCE_OF_TRUTH / DERIVED_READ_ONLY
boundary. They do not select production fields, read spreadsheets, repair
formulas, or mutate any source or derived region.

## Exact reconciliation

The caller supplies two normalized metric mappings:

- authoritative source metrics;
- derived/read-model metrics.

Reconciliation passes only when:

- both mappings expose exactly the same key set;
- every key is a non-empty string;
- each corresponding value has exactly the same Python type;
- each corresponding value compares equal.

This deliberately treats `True` and `1` as different values because their
types differ.

Missing keys, extra keys, blank/non-string keys, type drift, or value drift
return `False`.

## Formula-anchor health

A formula anchor is healthy only when:

- its name is non-empty;
- `formula_present` is a native boolean and is `True`;
- `error_code` is either `None` or blank text.

Any non-blank reported error blocks health, including errors such as
`#REF!`, `#SPILL!`, or `#VALUE!`.

A group of anchors is healthy only when:

- at least one anchor is supplied;
- anchor names are unique;
- every anchor is individually healthy.

## Scope boundary

This control does not decide:

- which metrics must be reconciled;
- which formula anchors are mandatory for a business workflow;
- whether a release may proceed;
- whether any formula should be repaired.

Those responsibilities remain with higher-level, explicitly scoped controls.

## Public boundary

Tests use synthetic metric names and synthetic formula-anchor names only. No
live workbook names, operational totals, external-system identifiers, or
production write paths are included.
