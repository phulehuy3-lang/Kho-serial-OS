# INBOUND_SERIAL_QUERY_DERIVED_V1

Status: **PUBLIC PURE WAREHOUSE PROFILE — NO LIVE / NO PRODUCTION AUTHORITY**

## Purpose

Compose the seven already-defined public warehouse controls required by the
locked inbound scenario:

`INBOUND_SERIAL_QUERY_DERIVED_V1`

The profile consumes already-materialized producer outcomes only. It does not
read a workbook, discover a target, call a provider, write inventory, or mutate
MASTER LIVE.

## Exact gate universe

The profile requires exactly these seven gate IDs:

1. `source_role_boundary`
2. `source_readback`
3. `serial_range_quantity`
4. `serial_overlap_free`
5. `source_derived_reconciliation`
6. `formula_health`
7. `formula_semantics`

`hold_conflict` remains a separate native boolean/unknown input to Control 07.

No producer may substitute for another gate and no gate may be omitted.

## Profile context

`InboundProfileContext` binds:

- `contract_id`: exact `INBOUND_SERIAL_QUERY_DERIVED_PROFILE_V1`;
- `task_id`: exact non-blank text;
- `scope_id`: exact non-blank text;
- `capture_marker`: exact non-blank text.

The scenario ID is fixed by code to `INBOUND_SERIAL_QUERY_DERIVED_V1`.

## Producer outcomes

`InboundProducerOutcomes` accepts already-materialized outputs from:

- SOURCE_ROLE_BOUNDARY_V0_1;
- SOURCE_READBACK_V0_1;
- Control 04 quantity result;
- Control 04 overlap-free result;
- Control 06 source↔derived reconciliation result;
- Control 06 formula-health result;
- Control 12 formula-semantic assessment.

Structured producer results are converted explicitly to native boolean/unknown
evidence. Native boolean producers are forwarded without coercion so Control 13
can reject pseudo-booleans.

A malformed or internally inconsistent structured producer result becomes
unknown (`None`) rather than PASS.

## Two-stage composition

### Stage 1 — Control 13 exact-set preflight

The profile materializes seven `MaterializedGateEvidence` records using the
same scenario/task/scope/capture binding.

Control 13 must PASS exact set equality, uniqueness, binding, capture marker,
and native boolean/unknown value validation.

If Control 13 HOLDs, Control 07 must not be called.

### Stage 2 — Control 07 fail-closed aggregation

Only Control 13's validated gate map may reach Control 07.

Control 07 then evaluates:

- any gate `False` → HOLD;
- any gate `None` → HOLD;
- `hold_conflict=True` → HOLD;
- `hold_conflict=None` → HOLD;
- all seven `True` plus `hold_conflict=False` → profile-level
  `INBOUND_CONTROL_READY`.

The Control 07 label `READY_FOR_RELEASE` is translated to
`INBOUND_CONTROL_READY` only. It is not exposed as production release
authority.

## Result

`InboundProfileResult` returns only:

- `INBOUND_CONTROL_READY`
- `HOLD`

and includes:

- `ready`: native boolean;
- deterministic `blocking_reasons`;
- `preflight_status`;
- `release_status` or `None` when Control 07 was not invoked;
- `production_write_authorized=False` always.

## Tamper-test kernel

The implementation exposes a narrow
`assess_inbound_materialized_gate_evidence` function so adversarial tests can
prove that missing, extra, duplicate, binding-mismatched, marker-mismatched, or
pseudo-boolean evidence is stopped by Control 13 before Control 07.

This function does not discover evidence or define a generic scenario. The
required gate universe and scenario ID remain hard-coded to this inbound
warehouse profile.

## Safety boundary

`INBOUND_CONTROL_READY` proves only that the supplied synthetic/public control
chain is complete for this locked scenario.

It does not prove:

- live source identity;
- live freshness or atomicity;
- external permission;
- production target authority;
- successful warehouse mutation;
- rollback capability;
- production writer readiness.

Every path preserves:

`production_write_authorized=False`

No live adapter, connector, credential, filesystem/network access, workbook
mapping, real serial, or MASTER LIVE mutation is included.
