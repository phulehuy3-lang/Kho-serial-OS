# Inbound Serial Acceptance Profile — Design v0.1

Status: **DESIGN SELECTED — IMPLEMENTATION HOLD**

## Why this is the next roadmap item

After sole-mission repository enforcement closed, the next useful gap is not a
new generic framework primitive. Control 13 already checks exact gate-set
coverage, but it intentionally cannot decide which warehouse gates apply.

Inbound serial acceptance is selected because a bad inbound record contaminates
inventory, future allocation, HOLD decisions, and reconciliation downstream.
The design stays pure and synthetic. It adds no live reader, connector,
credential, production writer, or MASTER LIVE mutation.

Rejected for this step:

- executable production writer: remains HOLD;
- live adapter/provider: remains outside the public capability boundary;
- another generic evidence/composition control: duplicates Phase 3 direction;
- full outbound kernel migration: broader and higher-risk than an inbound
  scenario profile.

## Locked scenario

Candidate scenario identity:

`INBOUND_SERIAL_QUERY_DERIVED_V1`

This profile is intentionally narrow: an inbound serial-range transaction whose
authoritative source update has a QUERY-based derived/read-model surface that
must remain consistent.

A different derived mechanism requires a separate reviewed profile version; do
not silently drop `formula_semantics`.

## Exact required gate universe

A future executable profile must declare exactly these gate IDs to Control 13:

1. `source_role_boundary`
2. `source_readback`
3. `serial_range_quantity`
4. `serial_overlap_free`
5. `source_derived_reconciliation`
6. `formula_health`
7. `formula_semantics`

`hold_conflict` remains the separate native boolean/unknown input required by
Control 07 and is not hidden inside the gate map.

No gate may be inferred from another gate's PASS.

## Producer audit

| Gate | Existing public producer | Current state |
| --- | --- | --- |
| source_role_boundary | SOURCE_ROLE_BOUNDARY_V0_1 implements RULE-0099 write-intent boundary | available after this primitive merges |
| source_readback | SOURCE_READBACK_V0_1 validates expected vs already-materialized source read-back | available after this primitive merges |
| serial_range_quantity | Control 04 | available |
| serial_overlap_free | Control 04, over the caller-supplied canonical comparison set | available, scope authority remains upstream |
| source_derived_reconciliation | Control 06 | available |
| formula_health | Control 06 | available |
| formula_semantics | Control 12 | available |

After SOURCE_READBACK_V0_1 merges, all seven declared inbound gate producers
exist in the public pure-control layer. The full inbound profile may then move
from producer-blocked HOLD to a separate implementation review. This still does
not authorize live reads, production writes, or any MASTER LIVE mutation.

## Composition order

```text
upstream warehouse evidence
    -> source-role boundary evaluation
    -> source read-back evaluation
    -> Control 04 interval quantity + overlap results
    -> Control 06 reconciliation + formula-health results
    -> Control 12 formula-semantics result
    -> exact scenario/task/scope/capture-bound records
    -> Control 13 exact required-set preflight
    -> validated native boolean/unknown map
       + separate hold_conflict
    -> Control 07
```

A structurally complete profile with any False/None gate remains HOLD through
Control 07.

## Decision vocabulary

A future profile may return only:

- `INBOUND_CONTROL_READY`
- `HOLD`

`INBOUND_CONTROL_READY` means the synthetic public control chain is complete
for this locked scenario. It does **not** mean:

- inventory was written;
- source data is live or fresh;
- the caller is authorized;
- a production writer exists;
- MASTER LIVE may be changed.

Every future result must carry
`production_write_authorized=False`.

## Adversarial fixtures required before implementation

Implementation must prove at least:

1. all seven exact gates True + hold_conflict=False -> INBOUND_CONTROL_READY;
2. any required gate omitted -> Control 13 HOLD;
3. any extra/duplicate/mismatched task/scope/capture record -> Control 13 HOLD;
4. source role unknown or derived region presented as writable -> HOLD;
5. source read-back missing/mismatch -> HOLD;
6. serial quantity mismatch -> HOLD;
7. overlapping serial interval in the canonical comparison set -> HOLD;
8. source↔derived mismatch -> HOLD;
9. formula missing or REF/SPILL/error state -> HOLD;
10. formula semantic drift -> HOLD;
11. any gate False/None -> Control 07 HOLD;
12. hold_conflict=True/None -> Control 07 HOLD;
13. string/integer pseudo-booleans -> validation failure/HOLD;
14. no path ever sets production_write_authorized=True.

All fixtures use synthetic short identifiers and serial ranges only.

## Smallest next implementation step

Do **not** implement the whole profile yet.

The smallest missing prerequisite is a pure,
side-effect-free `SOURCE_ROLE_BOUNDARY_V0_1` evaluator that turns an explicit
region classification and requested operation into a native boolean/HOLD-safe
result:

- business write intent is permitted only for `SOURCE_OF_TRUTH`;
- `DERIVED_READ_ONLY` always blocks business write intent;
- unknown, blank, malformed, or unsupported classifications fail closed;
- no workbook mapping, connector, live target, or writer is allowed.

After SOURCE_READBACK_V0_1 is independently merged, re-audit all seven
producer contracts together and only then implement the pure inbound profile
composition.

## Repository scope decision

This design maps directly to warehouse-serial capabilities:
`INBOUND`, `INVENTORY`, `SERIAL_IDENTITY_RANGE`,
`RECONCILIATION`, and `HOLD_QUARANTINE`.

It is not a general-purpose workflow framework.
