# Trusted Public Boundary V2 Migration

Status: **STAGED; ENFORCEMENT REQUIRES RULESET READ-BACK**

V2 supplements the frozen V1 policy. It blocks aliased process/dynamic
imports in Python and linked Git objects that appear only in intermediate
commits. Synthetic regressions reproduce both previously missed cases.

## Activation order

1. Merge the small V2 policy PR only after existing `unit-tests` and
   `trusted-public-boundary` pass on the exact head SHA. Read their logs.
2. Confirm both push workflows pass on the post-merge canonical main.
   Specifically read `STATIC_QUALITY_V2_PASS` and
   `GIT_HISTORY_BOUNDARY_V2_PASS` from the new workflow log.
3. Add `trusted-public-boundary-v2` to the active Main ruleset's required
   status checks, retaining `unit-tests` and `trusted-public-boundary`.
4. Read the ruleset and a subsequent PR check run directly from GitHub.
   Prove a failing V2 check blocks merge before declaring enforcement CLOSED.

Until step 4 is evidenced, policy code may be present while the enforcement
upgrade remains PARTIAL. Do not disable V1 or bypass the protected main branch.

V2 is a scoped static/history gate, not a proof that all future Python
capabilities or all sensitive strings are detectable. The public repository
still has no live connector, production writer or warehouse data authority.
