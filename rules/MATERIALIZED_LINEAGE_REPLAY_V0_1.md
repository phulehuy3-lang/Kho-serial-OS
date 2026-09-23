# MATERIALIZED_LINEAGE_REPLAY_V0_1

Status: **PUBLIC BASELINE — READ-ONLY / MATERIALIZED-SCOPE ONLY**

## Purpose

Define a pure historical replay control for already-materialized same-year
candidate lineage.

The control reconstructs pre-transaction available quantity from:

`inbound_qty - prior_committed_out_qty`

and replays canonical ranked-prefix allocation through Control 09.

The pre-transaction serial start must be supplied independently from verified
serial lineage. It must never be inferred from quantity subtraction.

## Scope

This control is limited to an already-materialized candidate set.

A successful replay proves semantic parity within that supplied set only. It
does not prove that the supplied set was globally complete or independently
discovered.

## Replayability requirements

Replay evidence is NOT_REPLAYABLE unless all required historical evidence is
internally coherent, including:

- non-empty replay/task identifiers;
- exact native `date` document date;
- positive native-integer requested quantity;
- transaction closed and read-back passed;
- source-rank lineage and read-back verified;
- allocation-plan lineage verified;
- candidate scope = `MATERIALIZED_CANDIDATE_SET_ONLY`;
- candidate count matches supplied/ranked sources;
- ranked source IDs are unique and non-empty;
- selected source IDs are unique, non-empty, and inside the materialized set;
- allocation quantities are positive native integers;
- historical allocation quantities sum exactly to the transaction requested
  quantity;
- source snapshots are unique and same-year;
- source date is not after document date;
- source row is a positive native integer;
- serial start is non-empty numeric text;
- serial lineage is explicitly verified;
- inbound quantity is a positive native integer;
- prior committed outbound quantity is a non-negative native integer;
- prior committed outbound quantity does not exceed inbound quantity;
- reconstructed available quantity is positive.

## Canonical replay

After replayability passes, each source becomes a Control 09 `RankedCandidate`
with reconstructed available quantity.

Control 09 is then used to recompute:

- canonical NEAREST-PRIOR ranking;
- ranked-prefix selected sources;
- allocation quantities;
- candidate-set hash.

Historical evidence that is internally impossible before replay, including an
allocation total different from the transaction requested quantity, is
`NOT_REPLAYABLE`.

After replayability passes, any semantic mismatch between the historical
decision and the current canonical replay returns `HOLD`.

## Historical candidate-set hash

If no historical hash is present, replay may still match semantically and
reports `MISSING`.

If a hash is present under a different algorithm identifier or a different
hash contract ID, replay reports `NOT_COMPARABLE`.

Comparable candidate-set hashes require both:

- algorithm ID = `SHA256_CANONICAL_JSON_V1`;
- contract ID = `RANKED_PREFIX_CANDIDATE_SET_HASH_V1`.

The algorithm identifies the digest/canonicalization mechanism. The contract ID
identifies the exact payload schema. Matching only the algorithm is
insufficient.

When both identities match, the historical hash must be a valid lowercase
SHA-256 digest and must equal the recomputed hash. A mismatch returns `HOLD`.

The result separately exposes whether cryptographic hash equality was actually
proven. A semantic `MATCH` with a missing or non-comparable historical hash is
not represented as cryptographic equality.

## Result classes

- `MATCH`: replayable evidence and semantic parity;
- `HOLD`: replayable evidence exists but current canonical replay differs;
- `NOT_REPLAYABLE`: required historical/source evidence is insufficient or
  internally invalid.

## Dependency policy

This control may depend on Control 09
`RANKED_PREFIX_ALLOCATION_LINEAGE_V0_1` as its canonical replay kernel.

It must not depend on:

- private outbound kernels;
- production adapters;
- live candidate discovery;
- connected-service clients;
- workbook/Drive/Sheets access;
- mutation executors.

## Public boundary

Tests use synthetic short IDs, dates, quantities, and serial text only. No live
warehouse identifiers, credentials, external URLs, or production write paths
are present.
