# CROSS_YEAR_AUTHORITY_V0_1

Status: **PUBLIC BASELINE**

## Purpose

Define a fail-closed, transaction-scoped authority contract for using source
records from years other than the document year.

This control is pure and side-effect-free. It does not discover warehouse
records, read external systems, write production data, or authorize any
production mutation.

## Canonical evidence requirements

A cross-year decision is releasable only when all of the following are true:

1. the caller supplies a structured authority-registry snapshot;
2. the snapshot identifies itself as canonical and uses the expected schema;
3. the registry and selected record both pass read-back;
4. exactly one authority record matches the requested authority ID;
5. task binding matches exactly;
6. decision state is approved and active;
7. owner approval is explicit;
8. evidence reference is present;
9. permitted source years are positive, unique, non-empty, and exclude the
   document year;
10. the authority record hash matches its canonical immutable payload.

Any missing, malformed, duplicate, drifted, or non-canonical evidence returns
`HOLD`.

## Non-authority inputs

The resolver intentionally does not infer authority from:

- free-text notes;
- generic approval flags;
- comments;
- UI labels;
- implicit business context.

## Integrity model

The authority record hash is SHA-256 over canonical JSON containing the
immutable decision fields. Hash mismatch blocks release.

## Public boundary

Examples and tests must use synthetic IDs, dates, years, and evidence
references only.
