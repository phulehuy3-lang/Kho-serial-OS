# RANKED_PREFIX_ALLOCATION_LINEAGE_V0_1

Status: **PUBLIC BASELINE — READ-ONLY / NO MUTATION AUTHORITY**

## Purpose

Define a pure, fail-closed contract for:

1. deterministic NEAREST-PRIOR ranking over an already-authorized candidate set;
2. ranked-prefix allocation;
3. independent allocation verification;
4. source-rank lineage;
5. allocation-plan lineage;
6. canonical allocation-plan hashing.

This control does not discover candidates, authorize their business scope,
resolve cross-year authority, evaluate HOLD policy, aggregate release gates, or
perform any external mutation.

## Upstream contract

The caller must supply a candidate set that has already passed all upstream
authority/scope checks applicable to the business workflow.

Control 09 validates only the mechanics and lineage of ranking/allocation.

## Canonical ranking

Ranking reuses the public `ALLOCATION_NEAREST_PRIOR_V1_0` ordering:

`SOURCE_DATE_DESC | SOURCE_ROW_ASC | SERIAL_START_ASC`

Every supplied candidate must satisfy:

- non-empty candidate ID;
- exact `date` source date;
- positive native-integer source row;
- non-empty numeric serial-start text;
- positive native-integer available quantity;
- source date not after target date.

A future-dated candidate causes HOLD instead of being silently dropped because
the supplied set is expected to be an already-scoped eligible universe.

## Ambiguous rank keys

Two distinct candidates with the same canonical rank key are rejected.

This prevents result order from depending on caller input order when serial
texts such as `"00010"` and `"10"` have the same numeric rank key.

## Ranked-prefix allocation

Allocation consumes candidates strictly from the top of the canonical ranked
set until the requested quantity is satisfied.

The final source may be partially consumed.

Insufficient total available quantity returns HOLD.

## Independent verifier

The verifier intentionally recomputes validation, ranking, and ranked-prefix
allocation through a separate implementation path.

It must not call the allocator decision function or the allocator's canonical
ranking helper. This duplication is intentional safety redundancy, not a second
business policy.

## Candidate-set hash

Hash algorithm ID:

`SHA256_CANONICAL_JSON_V1`

Hash contract ID:

`RANKED_PREFIX_CANDIDATE_SET_HASH_V1`

The algorithm ID identifies the digest/canonical-JSON mechanism. The contract
ID identifies the exact candidate-set payload schema. Historical compatibility
requires both identities, not the algorithm string alone.

The deterministic SHA-256 hash binds:

- task ID;
- target date;
- requested quantity;
- canonical ranked candidate order;
- candidate identity;
- source date;
- source row;
- serial-start text;
- available quantity.

Input ordering therefore does not change the hash.

## Lineage

Source-rank lineage binds:

- task ID;
- source-rank gate ID;
- candidate-set hash;
- ranked candidate IDs.

Allocation-plan lineage additionally binds:

- task ID;
- source-rank gate ID;
- candidate-set hash;
- allocation rank;
- candidate ID;
- planned quantity;
- plan state.

Supported plan states are `PLANNED` and `COMMITTED`.

## Allocation-plan hash

Hash algorithm ID:

`SHA256_CANONICAL_JSON_V1`

Hash contract ID:

`RANKED_PREFIX_ALLOCATION_PLAN_HASH_V1`

The candidate-set and allocation-plan hashes intentionally share the same hash
algorithm while using different contract IDs because their payload schemas are
not interchangeable.

A canonical allocation-plan SHA-256 hash may be produced only after allocation
plan lineage validation passes.

The hash binds:

- task ID;
- source-rank gate ID;
- candidate-set hash;
- ordered allocation rows;
- allocation rank;
- candidate ID;
- planned quantity;
- plan state.

Changing plan state from `PLANNED` to `COMMITTED` therefore changes the hash.
Invalid or lineage-inconsistent plans are not hashable through the public
helper.

## Scope boundary

This control does not:

- infer candidate completeness;
- perform source-pool authorization;
- resolve cross-year exceptions;
- evaluate carrier/category/business scope;
- decide HOLD release;
- decide terminal release;
- generate BBGH/DDH artifacts;
- reserve or write inventory.

## Public boundary

Tests use synthetic short identifiers and serial values only. No live warehouse
records, operational rule graph, connected-service identifiers, credentials, or
production write paths are present.
