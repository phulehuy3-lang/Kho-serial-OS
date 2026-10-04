# Operational TEST V2 — M4 warehouse profile

Kho-serial-OS is the warehouse-side validator/intent producer for
`OS_OPERATIONAL_TEST_CONTRACT_V2_0_R1_20261004`. PHU OS remains the connected-session
orchestrator. This module performs no provider I/O and grants no Production authority.

`operational_test_v2_profile.py` locks:

- exact M2/M3 contract/generation/binding/manifest/header identities;
- exact operational registry/ledger header contracts;
- TEST HOLD scopes `INTERVAL`, `DOCUMENT`, `DOCUMENT_LINE`;
- `ACTIVE -> RELEASED` release lineage requirements;
- IN/OUT/HOLD_APPLY/HOLD_RELEASE/REVERSAL/RESET_REGRESSION event vocabulary;
- SERIAL_TEXT preservation;
- SourceDate/DocumentDate same-year and nearest-prior eligibility;
- `SOURCE_DATE_DESC | SOURCE_ROW_ASC | SERIAL_START_ASC`;
- header-bound warehouse write intents that forbid derived/historical surfaces.

M4 is code/profile integration only. No operational transaction is run and
`OperationalMutationAuthorized` remains false on the Sheet until M5.
