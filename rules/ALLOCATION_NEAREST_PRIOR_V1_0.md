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


## Serial text safety contract

`SERIAL_START` remains an identifier represented as text.

For ordering, an accepted serial must:

- be a non-empty native string;
- contain ASCII decimal digits `0`–`9` only;
- contain at most **4096 digits**.

The implementation must not depend on converting the full serial to a Python
integer. Numeric ordering is derived from significant-digit length plus
lexicographic digit order, while the original serial text is retained unchanged
for identity and hashing. Leading zeroes are therefore preserved.

Non-ASCII digit characters and overlong digit strings are malformed input and
must fail closed before numeric ordering.

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
