# RULE-0099 — SOURCE_OF_TRUTH / DERIVED_READ_ONLY

Status: **ACTIVE**

## Rule

Every writable business region must be classified before use as exactly one of:

- `SOURCE_OF_TRUTH`
- `DERIVED_READ_ONLY`

Only `SOURCE_OF_TRUTH` accepts business-data writes.

## Derived read-only patterns

Generated/read-model regions are read-only. This includes, when used as derived outputs:

- `QUERY`
- `FILTER`
- `ARRAYFORMULA`
- spill ranges
- lookup outputs
- read models
- availability projections
- derived `ELIGIBLE_STOCK`

Manual write/paste into these regions is prohibited.

## Mandatory verification

Before release/closure, verify:

- source read-back;
- source → SYS → view/read-model parity;
- formula anchors remain intact;
- no active `#REF!` / `#SPILL!`;
- source ↔ derived reconciliation passes.

## Release rule

`CLOSED` / `READY_FOR_RELEASE` is permitted only when both source and derived layers pass their applicable controls.

## Failure rule

A failing source, failing derived layer, broken formula anchor, unresolved spill/reference error, or unresolved reconciliation issue blocks release and requires `HOLD` until resolved.

## Scope rule

RULE-0099 is a control-boundary rule. It does not itself authorize changes to inventory, serials, allocation history, or production data.
