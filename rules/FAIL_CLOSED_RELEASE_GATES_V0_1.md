# FAIL_CLOSED_RELEASE_GATES_V0_1

Status: **PUBLIC BASELINE — DECISION ONLY**

## Purpose

Define a pure fail-closed aggregator for already-scoped release gates.

This control does not evaluate business rules itself. Callers must supply the
set of gates that are applicable to the current transaction or batch.

The aggregator only answers whether the supplied evidence is sufficient for a
release-ready decision.

## Decision model

Each applicable gate has one of three states:

- `True` — PASS;
- `False` — FAIL;
- `None` — UNKNOWN / missing evidence.

The HOLD-conflict input also has the same three-state representation:

- `False` — no HOLD conflict;
- `True` — HOLD conflict present;
- `None` — HOLD state unknown.

## Fail-closed rules

The result is `HOLD` when any of the following is true:

- no gate evidence is supplied;
- any gate is `False`;
- any gate is `None`;
- HOLD conflict is `True`;
- HOLD conflict is `None`.

Only a non-empty set of all-`True` applicable gates with
`hold_conflict=False` may return `READY_FOR_RELEASE`.

## Input integrity

Gate names must be unique mapping keys and must be non-empty strings.

Gate values must be native booleans or `None`. Text such as `"PASS"`,
integers such as `1`, and other coercible values are invalid and raise a
validation error rather than being silently accepted.

The HOLD-conflict value must likewise be a native boolean or `None`.

## Determinism

Blocking reasons are returned in deterministic gate-name order, followed by
the HOLD-conflict result when applicable.

## Scope boundary

This control does not:

- decide which gates apply;
- execute any release;
- mutate inventory, HOLD state, formulas, or source data;
- infer missing evidence;
- read external systems.

It aggregates only already-scoped evidence supplied by the caller.

## Public boundary

Tests use synthetic gate names and boolean/unknown states only. No live
warehouse data, serials, external-system identifiers, or production write
paths are included.
