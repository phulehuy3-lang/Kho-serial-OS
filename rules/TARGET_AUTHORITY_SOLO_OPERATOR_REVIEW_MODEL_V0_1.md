# TARGET_AUTHORITY_SOLO_OPERATOR_REVIEW_MODEL_V0_1

Status: **PASS_SOLO_OPERATOR_REVIEW_MODEL_ADOPTED**

## Purpose

Define the explicit governance exception that permits one human operator to
perform target-authority ownership, approval and verification duties without
pretending that human segregation of duties exists.

This project is operated by one person.

Therefore this model replaces the previously unresolved requirement for a
distinct external human reviewer with a stricter **evidence-path separation**
control.

This is a governance decision only.

It does not create a Drive authority boundary, registry record, Production
locator, credential, permission, provider session, live read, executable
acquisition path, Production write, or MASTER LIVE mutation.

Locked authority state:

- `PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED`
- `LiveReadAuthorized = False`
- `ExecutableAcquisitionAuthorized = False`
- `ProductionWriteAuthorized = False`
- Production writer = `HOLD`
- MASTER LIVE unchanged

## 1. Operational reality

The warehouse project has one human operator.

Consequences:

- no second human reviewer currently exists;
- a second account controlled by the same human is not independent review;
- fake segregation of duties is prohibited;
- owner, approver and verification responsibilities may be performed by the
  same human only under this declared solo-operator model;
- the evidence bundle must explicitly state that human separation of duties is
  absent.

## 2. Relationship to the existing materialization plan

`INBOUND_TARGET_AUTHORITY_REGISTRY_MATERIALIZATION_PLAN_V0_1` states that the
same external identity may satisfy owner and independent-review responsibilities
when a later governance decision explicitly permits and justifies that
exception.

This artifact is that later governance decision.

Historical artifacts remain historical evidence.

In particular:

- `EXTERNAL_TARGET_AUTHORITY_DRIVE_MATERIALIZATION_READINESS_V0_1` correctly
  recorded the earlier blocker
  `HOLD_INDEPENDENT_REVIEWER_IDENTITY_NOT_BOUND`;
- this artifact does not rewrite that history;
- it supersedes that blocker for the current one-person operating model by
  replacing **identity independence** with **evidence-path independence**.

## 3. Canonical review mode

The only permitted review-mode label under this exception is:

`SOLO_OPERATOR_SELF_REVIEW_WITH_INDEPENDENT_EVIDENCE_PATH`

The following labels are prohibited unless a genuinely separate human reviewer
later exists and is independently evidenced:

- `INDEPENDENT_HUMAN_REVIEW`
- `INDEPENDENT_REVIEWER_PRESENT`
- `SEGREGATION_OF_DUTIES_ENFORCED`

The system must never imply those conditions are true under this model.

## 4. Role collapse

Under this solo model, the same external identity may fulfill:

- `TARGET_AUTHORITY_OWNER`
- `TARGET_AUTHORITY_APPROVER`
- the logical read-back/reviewer role used by the existing record schema.

This is permitted only because:

1. the one-person operating reality is explicit;
2. no independent-human-review claim is made;
3. materialization and verification are separated into distinct evidence
   events;
4. verification must reacquire the authoritative object from Drive;
5. verification must recompute deterministic integrity and uniqueness evidence;
6. all limitations remain visible in the final evidence bundle.

The existing
`independent_reviewer_authority_ref`
field may therefore equal the owner authority ref under this model.

When it does, every associated read-back evidence object must state:

- `review_mode = SOLO_OPERATOR_SELF_REVIEW_WITH_INDEPENDENT_EVIDENCE_PATH`
- `human_separation_of_duties = false`

The field name is retained for schema compatibility and must not be interpreted
as proof of a different human identity.

## 5. Evidence-path independence

Evidence-path independence means the verification result comes from a fresh
provider retrieval path rather than from the authoring payload.

It requires all of the following:

- materialization event is completed before verification begins;
- verification has a distinct evidence/event ID;
- verification re-resolves the stored object from the external Drive authority
  boundary;
- verification reads the provider-stored authoritative bytes or provider
  metadata directly;
- verification does not reuse the owner's in-memory proposal object as proof;
- verification recomputes hashes from the newly retrieved canonical bytes;
- verification re-evaluates lifecycle and registry-wide uniqueness;
- verification records provider revision/version markers where available;
- verification emits its own evidence object.

A second browser tab, second account, copied local file, screenshot, chat copy,
or manually retyped payload does not create evidence-path independence.

## 6. Materialization event boundary

A materialization event may:

- create or update the explicitly authorized authority object;
- compute the proposed canonical hash;
- store the object;
- emit materialization evidence;
- then stop.

The materialization evidence must have an opaque event ID.

After the event closes, its in-memory payload, copied text or local
representation is not sufficient read-back evidence.

## 7. Verification event boundary

The verification event must use a different opaque event/evidence ID.

It must begin from external authority references and provider retrieval, not
from the materialization payload.

Required sequence for authority records:

1. resolve the authoritative REGISTRY object from the restricted Drive
   boundary;
2. retrieve the stored canonical bytes;
3. verify exact schema and native types;
4. recompute `authority_record_hash`;
5. verify target environment;
6. verify warehouse schema binding;
7. verify five-surface registry binding;
8. verify locator ref/hash binding;
9. verify lifecycle state;
10. independently enumerate the authoritative REGISTRY object set;
11. recompute ACTIVE uniqueness;
12. capture provider revision/version markers where available;
13. emit a separate verification evidence object;
14. return only PASS or HOLD.

Required sequence for the locator when locator verification is authorized:

1. retrieve the stored LOCATOR bytes from Drive;
2. recompute locator hash;
3. compare it to the registry locator-hash binding;
4. never copy the real Production locator into public GitHub or broad journal
   text.

## 8. No authority write during verification

While an evidence-path verification event is running, no authority-bearing
write may be used to repair the object being verified.

If verification discovers a defect:

- verification returns HOLD;
- the verification event closes;
- a new remediation/materialization event is opened separately;
- a later fresh verification event must rerun from provider-stored state.

A read-back procedure that silently fixes data before returning PASS is invalid.

## 9. Event separation

The following must differ:

- `materialization_event_id`
- `verification_event_id`

The verification evidence must bind:

- materialization event ID;
- verification event ID;
- object opaque ref;
- observed provider revision/version marker where available;
- recomputed hash;
- expected hash;
- lifecycle result;
- uniqueness result;
- review mode;
- `human_separation_of_duties=false`;
- final PASS/HOLD result.

Timestamp difference alone is not evidence of independence.

## 10. Registry-wide ACTIVE uniqueness

The solo model does not weaken uniqueness.

Verification must still scan the authoritative registry set.

For one `(environment, logical_target_alias)` pair:

- zero ACTIVE when one is required = HOLD;
- exactly one ACTIVE = eligible for further checks;
- more than one ACTIVE = HOLD.

Any optional active index remains DERIVED_READ_ONLY and cannot replace the full
registry scan.

## 11. Provider revision and retrieval evidence

Drive is not treated as immutable.

Where Drive exposes revision/version metadata, verification evidence must bind
the observed marker.

Hash equality proves content identity, not human independence.

The solo model therefore combines:

- provider retrieval;
- provider revision/version marker where available;
- deterministic canonical hash;
- event separation;
- registry-wide uniqueness;
- explicit no-human-independence disclosure.

## 12. Evidence sources that are invalid

The following cannot satisfy provider read-back:

- owner-proposed in-memory object;
- copied chat content;
- screenshots;
- pasted notes;
- GitHub copies;
- journal summaries;
- manually retyped content;
- a hash copied from the materialization result without recomputation.

If the provider-stored object cannot be reacquired, verification is HOLD.

## 13. Approval semantics

Under the solo-operator model, approval is not an independent human control.

It is an explicit operator decision recorded with an evidence ID and canonical
content hash.

The evidence must state:

`approval_model = SOLO_OPERATOR`

No downstream system may reinterpret it as dual-control approval.

## 14. Phase A Drive boundary verification

For Phase A authority-boundary creation, the same evidence-path principle
applies to folder and permission metadata.

After creation:

1. the creation event ends;
2. a distinct verification event re-reads root and child container metadata
   from Drive;
3. verifies REGISTRY / LOCATOR / EVIDENCE / RECOVERY topology;
4. re-reads permission/sharing state from the provider when the connector
   supports that evidence;
5. verifies no public/anyone/domain-wide unexpected access;
6. verifies no Production locator or registry record exists yet;
7. records the solo-operator limitation;
8. returns PASS or HOLD.

Phase A PASS does not materialize PRG-01.

## 15. High-risk write boundary

This solo-operator exception is scoped to target-authority governance and
read-only evidence acquisition preparation.

It does not automatically relax any later control for:

- Production mutation;
- executable Production writer authorization;
- destructive inventory correction;
- irreversible external action.

Those controls must be evaluated independently.

If a future control explicitly requires a second human for a high-risk write,
this artifact does not satisfy that requirement.

## 16. Fail-closed conditions

Required HOLD conditions include:

- verification reuses authoring/in-memory payload;
- materialization event ID equals verification event ID;
- provider object cannot be reacquired;
- recomputed hash mismatch;
- locator hash mismatch;
- lifecycle mismatch;
- ACTIVE uniqueness mismatch;
- provider revision evidence expected but unavailable without explanation;
- verification mutates the authority object;
- evidence claims independent human review when none exists;
- evidence omits `human_separation_of_duties=false`;
- public artifact leaks Production locator identity.

Unknown state = HOLD.

## 17. Current one-person authority semantics

Current truth:

- one human operates the project;
- human segregation of duties = **not available**;
- fake account separation = **prohibited**;
- evidence-path separation = **required**;
- provider reacquisition = **required**;
- deterministic hash recomputation = **required**;
- full registry uniqueness recomputation = **required**;
- solo-review limitation disclosure = **required**.

This is weaker than genuine independent human review in the human-governance
dimension.

It is stronger and more truthful than pretending a second account controlled
by the same person is independent.

## 18. Promotion effect

Adoption of this model resolves only the prior blocker:

`HOLD_INDEPENDENT_REVIEWER_IDENTITY_NOT_BOUND`

by replacing it with the explicitly governed solo-operator evidence-path model.

It does not make PRG-01 PASS.

After this model is merged and all repository checks pass, the next safe action
may be considered:

`PHASE_A_DRIVE_AUTHORITY_BOUNDARY_MATERIALIZATION_V0_1`

That action may create only the dedicated restricted control-plane boundary and
read it back.

It must not create the real Production locator or ACTIVE target-authority
record.

## Final decision

**TARGET_AUTHORITY_SOLO_OPERATOR_REVIEW_MODEL_V0_1 =
`PASS_SOLO_OPERATOR_REVIEW_MODEL_ADOPTED`**

**Human independent reviewer = NOT PRESENT**

**Human separation of duties = FALSE**

**Review mode =
`SOLO_OPERATOR_SELF_REVIEW_WITH_INDEPENDENT_EVIDENCE_PATH`**

**Prior reviewer-identity blocker = SUPERSEDED BY EXPLICIT GOVERNANCE
EXCEPTION**

**PRG-01 = HOLD_TARGET_AUTHORITY_NOT_MATERIALIZED**

**LiveReadAuthorized = False**

**ExecutableAcquisitionAuthorized = False**

**ProductionWriteAuthorized = False**

**Production writer = HOLD**

**MASTER LIVE unchanged**
