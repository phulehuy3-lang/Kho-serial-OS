# G04-R4 allocation fixture revision

The previous G04 expected NOT_RUN is retained as historical evidence. Its runner/domain contract was unbound. This new explicit R4 profile supersedes that limitation only for fresh isolated fixture execution; it does not reclassify prior runs.

New expected: PASS_LAB for requested quantity 8 on the frozen permitted source set LAB_IN, TEST_LONG, TEST_B, TEST_A at 2026-10-04. Canonical policy SOURCE_DATE_DESC | SOURCE_ROW_ASC | SERIAL_START_ASC. Expected prefix LAB_IN5 → TEST_LONG2 → TEST_B1. Category TEST20 maps to TEST_CARRIER/20000 solely in this synthetic lab profile.

The repo-owned pure runner consumes an already decoded, bounded NativeCapture. A separate source-domain assessment must first establish the supplied domain or deny it. The permitted-source set is supplied by the locked fixture profile, not inferred owner authority. Row bounds alone do not prove completeness. Numeric serials, mixed booleans, future dates, duplicates, quantity drift, altered permitted sets and insufficient quantity block. Independent prefix recomputation checks producer allocation. No network, write, provider verifier, operational authorization or production workflow exists here.

Every result keeps production_write_authorized=false, operational_acceptance=false, provider_proof_verified=false. PASS_LAB is isolated allocation acceptance only; the outer native domain/provider boundary stays HOLD where proof is unproven.

Phu_OS does not contain Kho ranked-prefix modules at the pinned baseline. This shared pure fixture runner is self-contained and public-safe; it can be installed in both repos with the same source hash. It does not copy private or business payloads.
