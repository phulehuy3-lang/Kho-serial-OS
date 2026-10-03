# PRG04_PRODUCTION_SURFACE_BINDINGS_V0_1

Status: **PARTIAL_HOLD_SOURCE_RECORD_BINDING_UNRESOLVED**

Issue: #145

## Scope

Audit and materialize exact Production bindings for the five locked inbound
logical surfaces using control-plane metadata only.

No serial, stock, ledger or worksheet business payload rows were read.

Private exact physical binding evidence is retained outside this public
repository.

Private evidence SHA-256:

`c65423e9a403800c58f0060978accea8855b6019519fc3b82119bf6695a49aeb`

## Locked logical registry

- `INBOUND_SOURCE_RECORD`
- `ACTIVE_SERIAL_INTERVAL_UNIVERSE`
- `INBOUND_DERIVED_QUERY_PROJECTION`
- `INBOUND_QUERY_FORMULA_ANCHOR`
- `ACTIVE_HOLD_INTERVAL_UNIVERSE`

Canonical public registry:

- `surface_registry_id = SR1_HCM_SERIAL_INBOUND_V1`
- registry hash =
  `d06d7297abcc460b3672e9ad4280f4bc5ca309e73933d5c22fae64048b30ca9a`

## Authority-backed binding results

### ACTIVE_SERIAL_INTERVAL_UNIVERSE

**PROVEN**

Bound to the canonical Production interval-state authority represented publicly
as `SYSTEM_INTERVAL_STATE`.

The binding is structural/header-bound and not caller-selected.

### INBOUND_DERIVED_QUERY_PROJECTION

**PROVEN**

Bound to the canonical protected derived availability projection represented
publicly as `ELIGIBLE_STOCK`.

Direct writes to this projection remain prohibited.

### INBOUND_QUERY_FORMULA_ANCHOR

**PROVEN**

Bound to the canonical QUERY anchor represented publicly as
`ELIGIBLE_STOCK!A3`.

### ACTIVE_HOLD_INTERVAL_UNIVERSE

**PROVEN**

Bound to the canonical HOLD authority represented publicly as
`SYSTEM_HOLD_REGISTRY`.

Operational HOLD projections remain non-authoritative derivatives.

### INBOUND_SOURCE_RECORD

**HOLD**

Current Production controls define:

- the locked business writer semantics;
- source-of-truth parity requirements;
- stable transaction identity;
- protected formula boundaries.

However, no approved control-plane artifact currently binds
`INBOUND_SOURCE_RECORD` to one deterministic physical selector for the
transaction-dependent item business row.

No authority-backed contract currently supplies all of:

- exact permitted item-sheet set or equivalent registry;
- deterministic sheet selection rule;
- stable row identity rule;
- exact logical-field to physical-field mapping;
- duplicate/missing-source fail-closed behavior.

Inferring a source from a form, log or nearest matching item sheet would violate
the no-inference/no-wildcard boundary.

Canonical blocker:

`HOLD_INBOUND_SOURCE_RECORD_PHYSICAL_BINDING_UNRESOLVED`

## Verdict

Four of five Production surface bindings are materially supported.

PRG-04 therefore remains:

**`PARTIAL_HOLD_SOURCE_RECORD_BINDING_UNRESOLVED`**

It is not permissible to relabel PRG-04 PASS.

## Smallest safe next action

Design and review:

`INBOUND_SOURCE_RECORD_PHYSICAL_SELECTOR_V0_1`

That selector must be control-plane governed and must:

1. enumerate the exact allowed Production item-sheet universe or bind an
   equivalent authoritative registry;
2. select one item sheet deterministically from transaction attributes;
3. resolve one source row by stable transaction/batch identity, never by row
   position alone;
4. map the logical source fields to exact physical fields;
5. fail closed on zero or multiple matches;
6. prohibit wildcard discovery, fuzzy/nearest-name matching and caller-defined
   ranges;
7. preserve the A/C/D/O writer and protected-formula boundaries;
8. be independently read back before PRG-04 can close.

Design/review may use control-plane metadata only.

## Locked

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
- Production writer = HOLD
- MASTER LIVE business data unchanged
