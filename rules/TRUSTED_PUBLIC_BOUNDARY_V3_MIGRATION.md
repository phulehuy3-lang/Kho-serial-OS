# Trusted Public Boundary V3 Migration

Status: **STAGED; ENFORCEMENT REQUIRES RULESET READ-BACK**

V3 supplements the frozen V1/V2 policy. It does not replace, rename, disable,
or relax either existing required check.

## F05 static hardening

V3 adds detection for static write-capability gaps not covered by V1/V2:

- positional method mode such as `Path(...).open("w")`;
- a simple local alias bound to a write-capable method and then called.

Regression examples are parsed as inert source text. Tests do not execute the
dangerous write examples.

## F06 history hardening

V3 adds an independent changed-path/blob acquisition path:

- `git diff-tree --raw -z` for NUL-delimited path transport;
- strict UTF-8 path decoding;
- rename/copy records consume both old and new path fields and scan the new
  path/blob;
- deletion is represented explicitly from Git status/new object ID;
- non-deleted content is read by Git blob object ID via `git cat-file blob`;
- a blob-read failure is an execution failure, not an implied deletion;
- content present only in an intermediate commit is scanned before later
  deletion.

Synthetic regressions cover ASCII names, Vietnamese names, a filename
containing a newline, rename/delete behavior, intermediate-only content and a
forced blob-read failure.

## Activation order

1. Merge this additive V3 implementation only after all currently required
   checks pass on its exact PR head.
2. Read exact post-merge main and verify:
   - the four pre-existing required checks still pass;
   - `trusted-public-boundary-v3` push workflow passes;
   - V3 log contains `STATIC_QUALITY_V3_PASS` and
     `GIT_HISTORY_BOUNDARY_V3_PASS`.
3. Add `trusted-public-boundary-v3` to the active Main ruleset while retaining
   every existing required check and all other rule semantics.
4. Fresh-read the ruleset.
5. Use a disposable, never-merged canary PR containing an inertly reachable
   source pattern missed by V1/V2 but rejected by V3. Confirm the V3 check
   fails while the required-check ruleset includes V3, then close/delete the
   canary without merge.
6. Only after steps 1–5 may V3 enforcement be recorded CLOSED.

If ruleset mutation or merge-blocking evidence cannot be obtained safely, the
V3 implementation may be merged but enforcement remains
`PARTIAL/HOLD_ENFORCEMENT_NOT_PROVEN`.

## Frozen policy rule

After V3 reaches main, the V3 workflow, scanners and regression tests become
trusted-base frozen policy paths inside the V3 workflow itself. V1/V2 frozen
paths remain unchanged.

## Authority boundary

V3 is repository safety only.

It does not authorize:

- warehouse payload reads;
- executable acquisition;
- credential creation;
- Drive/Sheets permission changes;
- Production writes;
- MASTER LIVE mutation.

`ProductionWriteAuthorized=False` remains invariant.
