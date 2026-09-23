# SERIAL_INTERVAL_INTEGRITY_V0_1

Status: **PUBLIC BASELINE**

## Purpose

Define pure, fail-closed integrity checks for inclusive numeric serial intervals.

This control is intentionally narrow. It does not allocate stock, discover
records, read external systems, mutate inventory, or decide warehouse business
scope.

## Interval model

A serial interval is represented by two non-negative native integers:

`start <= end`

The interval is inclusive, so its quantity is:

`end - start + 1`

Boolean values are rejected even though Python treats `bool` as a subclass of
`int`.

## Overlap semantics

Two intervals overlap when they share at least one serial value.

Examples:

- `[100, 199]` and `[200, 299]` do not overlap;
- `[100, 200]` and `[200, 300]` overlap at `200`;
- a fully contained interval overlaps its container.

The batch helper returns every overlapping pair by input index. It is
scope-agnostic: callers must supply the canonically correct comparison set.

## Quantity reconciliation

A declared quantity matches an interval only when it equals the inclusive
interval cardinality exactly.

Declared quantities must be non-negative native integers. Negative, boolean, or
non-integer values are invalid.

## Public boundary

Tests use short synthetic numeric ranges only. No live serials, warehouse
identifiers, external-system references, or production write paths are present.
