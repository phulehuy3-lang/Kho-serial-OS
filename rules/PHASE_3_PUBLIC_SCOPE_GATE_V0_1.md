# Phase 3 Public Scope Gate v0.1

Status: **DISCOVERY ONLY — NO CONTROL 13 SELECTED**

Baseline: `v0.2.0` at
`218c8030252ea0fb23489a5631678925b2572978`.
This document does not revise that tag, the twelve-control inventory, or the
engineering-only authority boundary.

## Decision question

Is there a specific, independently testable control gap that belongs in the
public, pure, synthetic control layer and is not already covered by Controls
01–12? A proposed thirteenth control remains HOLD until the evidence and
separation tests below pass. A new number is not a reason to migrate code.

## Current candidate assessment

| Candidate surface | Existing public coverage | Decision for now |
| --- | --- | --- |
| Formula cache coherence | Control 06 already tests exact source-to-derived parity; Control 12 separately tests formula semantic identity. Neither proves external recalculation. | Do not duplicate these checks or claim recalculation. |
| Historical allocation replay | Controls 09 and 11 already establish ranked-prefix lineage and replay parity in the materialized candidate set. | Do not infer a complete global candidate universe. |
| In-memory read snapshot | Control 10 already checks supplied materialized surfaces, hashes and version-marker atomicity. | Do not add a provider, connected target or live-read authorization. |
| Dry-run mutation composition | Controls 02, 08 and 09 bind supplied authority, plan lineage and a synthetic manifest. Control 08 always denies production writing. | Do not introduce a writer or release capability. |
| Evidence provenance and completeness across control outputs | Existing composition requires explicit inputs, but a distinct, generic evidence-envelope contract has not been established by this review. | Discovery candidate only; prove a non-duplicative invariant before selecting implementation. |

## Selection gate

Before opening an implementation PR, record all of the following in a separate
public design review, using synthetic examples only:

1. One exact failure mode and a falsifiable invariant absent from Controls
   01–12; identify the existing contract that comes closest and show why it
   cannot already detect the failure.
2. The input and output schema, version identity, trust boundaries and
   fail-closed behavior. Distinguish missing evidence from contradictory
   evidence and from a valid scoped PASS.
3. Allowed dependencies and an independent verifier strategy where decisions
   could otherwise share the same faulty implementation path.
4. Adversarial examples for omission, substitution, stale evidence, mismatched
   scope/version and misleading PASS composition, with deterministic tests.
5. Proof that all inputs can be synthetic and already materialized in memory;
   no private implementation or history copied into the public repository.
6. A capability review demonstrating no filesystem/network connector,
   credential, target discovery, external read, mutation or live write.
7. A small atomic PR and exact CI log read-back for `unit-tests` and
   `trusted-public-boundary`; keep public-boundary policy intact.

If any gate lacks evidence, retain **PHASE 3 CANDIDATE HOLD**. Do not assign
the identifier Control 13, edit the public control catalog as though a control
exists, or promise a release version until selection is defensible.

## Separate operational boundary

Private operational governance, live provider/adapters, source-of-truth data,
workbook or connected-service mappings, real serials, and production write
authorization remain outside this public discovery. A public PASS cannot
authorize a live operation. No MASTER LIVE change is part of this scope gate.
