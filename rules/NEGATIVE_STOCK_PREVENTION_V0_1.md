# NEGATIVE_STOCK_PREVENTION_V0_1

Status: **PUBLIC BASELINE**

## Purpose

Define a minimal fail-closed stock arithmetic control for proposed issues.

This control is pure and side-effect-free. It does not allocate sources,
reserve stock, mutate inventory, select warehouse rows, or perform external I/O.

## Arithmetic rule

Given:

- `available`: current available quantity;
- `requested`: proposed issue quantity;

the remaining quantity is:

`available - requested`

A proposed issue is blocking when the remaining quantity would be negative.

Exact depletion to zero is allowed.

## Input contract

Both quantities must be native non-negative integers.

The following are invalid:

- negative values;
- booleans;
- floats;
- numeric strings;
- missing/non-integer values.

Invalid inputs fail closed by raising a validation error rather than being
silently coerced.

## Scope boundary

This primitive does not determine whether a quantity is actually available in
production. The caller must supply an already validated quantity from an
authorized source.

It also does not authorize release, allocation, or mutation.

## Public boundary

Tests use small synthetic quantities only. No live stock figures, warehouse
identifiers, serials, external-system references, or production write paths are
present.
