# ALLOCATION_NEAREST_PRIOR_V1_0

Status: **CANONICAL BASELINE**

Canonical ordering:

`SOURCE_DATE_DESC | SOURCE_ROW_ASC | SERIAL_START_ASC`

Allocation mode: **NEAREST-PRIOR**

## Eligibility

A source is eligible only when:

`SOURCE_DATE <= TARGET_DATE`

A source dated after the target transaction/date must never be used for that allocation.

## Ordering

Among eligible sources:

1. sort by `SOURCE_DATE` descending — nearest prior date first;
2. for the same source date, sort by `SOURCE_ROW` ascending;
3. for the same date and row precedence, sort by `SERIAL_START` ascending.

## Interpretation

The primary rule is temporal proximity without crossing into the future.

The tie-breakers are deterministic:
- earlier source-row position first;
- then lower serial-start value first.

## Required post-allocation controls

An allocation result is not releasable merely because the ordering rule was followed. It must still pass the applicable controls for:

- serial/interval integrity;
- overlap;
- stock consistency;
- HOLD conflict;
- source ↔ derived reconciliation;
- read-back.

## Prohibited behavior

- allocating from a source after the target date;
- manually changing the ordering to obtain a desired serial;
- bypassing HOLD or reconciliation gates;
- rewriting canonical source history merely to make an allocation eligible.
