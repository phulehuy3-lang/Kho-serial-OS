# DRY_RUN_MUTATION_CONTRACT_V0_1

Status: **PUBLIC BASELINE — DRY-RUN ONLY / NO WRITE AUTHORITY**

## Purpose

Define a pure, side-effect-free contract for validating a synthetic mutation
manifest before any executable writer is considered.

A PASS from this control means only that the dry-run contract is internally
coherent. It never authorizes a production mutation.

## Locked scope

Version 0.1 requires:

- execution mode = `DRY_RUN_ONLY`;
- year scope = `SAME_YEAR_ONLY`;
- execution path = `EXECUTION_PATH_DISABLED`;
- production-ready flag = native `False`;
- HOLD release request = native `False`;
- source-pool authority already verified upstream;
- exact candidate source IDs bound into the manifest;
- explicit approval bound to the exact task and manifest hash;
- reviewed dry-run mutation whitelist;
- exact rollback intent for every operation;
- deterministic idempotency key;
- deterministic manifest hash;
- explicit post-transition read-back obligations.

Cross-year mutation and executable write enablement are out of scope.

## Mutation intent

Each proposed operation binds:

- operation ID;
- resource name;
- row/business key;
- field name;
- expected-before scalar;
- intended-after scalar;
- mutation kind.

Only `SET_EXACT` is supported.

Supported scalar values are:

- text;
- native integers;
- native booleans;
- `None`.

Floats and custom objects are rejected to avoid coercion ambiguity.

## Mutation whitelist

The whitelist is an independently hashed dry-run contract.

Each allowed entry binds:

- resource name;
- field name;
- mutation kind.

Every proposed operation must be covered by the whitelist.

## Idempotency

The idempotency key binds:

- task ID;
- candidate source IDs;
- candidate-set hash;
- canonical allocation-plan hash;
- ordered operations;
- expected-before values;
- intended-after values.

Changing a compare-before precondition therefore changes the idempotency key.

## Rollback exactness

Every operation must have exactly one rollback record with:

- same operation ID;
- same target;
- restore value exactly equal to expected-before;
- exact type equality.

For example, `True` is not an exact rollback for integer `1`.

## Approval binding

Approval must bind:

- approval ID;
- task ID;
- manifest hash;
- explicit `APPROVED` decision;
- read-back status = `PASS`;
- deterministic approval hash.

## Source-pool dependency

This control depends only on `SOURCE_POOL_AUTHORITY_V0_1`.

The supplied source-pool resolution must be internally PASS/ready, candidate
scope verified, contain no blockers, expose a valid non-empty permitted source
set, and bind the exact authority ID carried by the manifest.

The manifest also binds the exact candidate source IDs used by downstream
ranking/allocation. Their set must equal the source-pool resolution's
`permitted_source_ids`. Ordering may differ for the authority comparison, but
the manifest preserves the supplied candidate order in its own hash.

When composed with Control 09, candidate IDs must use the same source-ID
namespace as Control 02.

## Read-back obligations

The manifest must explicitly require:

- full-row read-back;
- source↔derived reconciliation;
- rollback on mismatch;
- read-back contract status = `PASS`.

This control validates only that these obligations are bound. It performs no
external read or write.

## Safety invariant

Every assessment returns:

`production_write_authorized = False`

even when the dry-run contract passes.

## Public boundary

All tests use synthetic resource names, IDs, hashes, dates, and values. This
control contains no live target identity, credential, connected-service client,
production adapter, or write-capable path.
