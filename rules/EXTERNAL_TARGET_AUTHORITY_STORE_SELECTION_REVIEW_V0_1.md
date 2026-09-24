# EXTERNAL_TARGET_AUTHORITY_STORE_SELECTION_REVIEW_V0_1

Status: **STORE-SELECTION CONFORMANCE PASS / MATERIALIZATION STILL HOLD**

## Purpose

Independently review `EXTERNAL_TARGET_AUTHORITY_STORE_SELECTION_V0_1` against
the PRG-01 materialization plan, the external-readiness audit, the public
repository boundary and the no-live/no-write authority invariants.

This review does not create the selected Drive boundary or authorize external
materialization.

## Review matrix

### R-01 — authoritative single-source semantics

**PASS AT DESIGN LEVEL**

The selection defines one dedicated restricted Drive authority boundary for the
canonical registry and prevents journal/checkpoint copies from becoming
authority by implication.

### R-02 — ownership/admin model

**PASS AT DESIGN LEVEL**

The selected service supports explicit owner/admin and per-object access
control. Actual identities and permissions remain unassigned and require a
separate action.

### R-03 — Production identifier isolation

**PASS**

The actual locator is placed in a separate restricted object/container and
public GitHub receives only opaque refs and hashes.

### R-04 — history/tamper evidence

**PASS WITH DECLARED LIMITATION**

Drive is not represented as immutable. The design requires revision/history
metadata, deterministic canonical bytes, SHA-256 binding and independent
read-back/hash recomputation.

### R-05 — independent read-back

**PASS AT DESIGN LEVEL**

Read-back retrieves the external stored object rather than reusing
owner-proposed data.

A distinct reviewer identity still has to be assigned later.

### R-06 — deterministic hash recomputation

**PASS**

Canonical machine-readable storage plus exact-byte retrieval supports
deterministic authority and locator hashing.

### R-07 — ACTIVE uniqueness

**PASS AT DESIGN LEVEL**

The provider itself is not misrepresented as enforcing uniqueness. The design
requires fail-closed registry-wide uniqueness validation before ACTIVE
transition.

### R-08 — backup/recovery

**PASS AT DESIGN LEVEL**

Recovery is explicitly subordinate to hash and uniqueness revalidation and
cannot silently become authority.

### R-09 — auditability/evidence retention

**PASS AT DESIGN LEVEL**

Registry, locator and evidence are separated within the selected external
service class and bind through opaque refs/hashes.

### R-10 — no executable acquisition dependency

**PASS**

No warehouse/provider Production read is required to create or independently
read back the authority registry.

### R-11 — governance roles

**PASS AT DESIGN LEVEL**

Owner, approver and independent reviewer roles remain distinct logical roles,
with later external identity assignment mandatory.

### R-12 — locator separation

**PASS**

Registry-reader access does not automatically grant locator-reader access.

### R-13 — candidate comparison

**PASS**

The decision assessed:

- restricted Google Drive/Workspace;
- private Git repository;
- another private object/external store class.

The selected Drive boundary is the smallest currently evidenced option that
does not weaken public-data separation or rely on unavailable private-repo
ruleset enforcement.

### R-14 — current-evidence discipline

**PASS**

Existing Drive journals/checkpoints are not relabeled as authority.

No existing file is treated as a registry or locator merely because it is
available.

### R-15 — authority invariants

**PASS**

The decision preserves:

- `PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED`;
- `LiveReadAuthorized=False`;
- `ExecutableAcquisitionAuthorized=False`;
- `ProductionWriteAuthorized=False`;
- Production writer = HOLD;
- MASTER LIVE unchanged.

## Residual blockers

Store selection resolves only the first prerequisite identified by the
PRG-01 readiness audit.

Still missing:

- dedicated Drive authority container materialization;
- exact registry/locator/evidence permission boundaries;
- actual governance identity assignments;
- actual locator object;
- actual target-authority record;
- authoritative warehouse schema binding in that record;
- authoritative five-surface registry binding;
- lifecycle activation;
- independent read-back evidence;
- canonical hash recomputation against materialized content;
- ACTIVE uniqueness proof;
- backup/recovery read-back evidence.

## Verdict

**Store-selection conformance = PASS.**

**Selected store class =
RESTRICTED_GOOGLE_DRIVE_WORKSPACE_WITH_SEPARATED_REGISTRY_LOCATOR_EVIDENCE.**

**Materialization authorization = NOT GRANTED.**

**PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED.**

**LiveReadAuthorized = False.**

**ExecutableAcquisitionAuthorized = False.**

**ProductionWriteAuthorized = False.**

Next safe step:

**`EXTERNAL_TARGET_AUTHORITY_DRIVE_MATERIALIZATION_READINESS_V0_1`**
