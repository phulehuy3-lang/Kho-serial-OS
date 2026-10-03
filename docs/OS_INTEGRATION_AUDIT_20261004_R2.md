# Isolated integration audit — 2026-10-04

Audit: OS-INTEGRATION-20261004-01, revision R2.

## Result and scope

PASS applies only to the recorded synthetic native workflow trace, pinned pure controls and fresh final readback. Overall assurance is PARTIAL. LiveReadAuthorized=False; ExecutableAcquisitionAuthorized=False; ProductionWriteAuthorized=False. Production writer remains HOLD.

Synthetic inbound, HOLD exclusion/release, nearest-prior allocation, closed transaction readback and sold-item exclusion passed. Whole-fixture close correctly remained BLOCKED_SAFE because an unrelated ACTIVE HOLD was preserved. Eighteen negative probes blocked as expected. Targeted regressions: Phu_OS 51/51; Kho-serial-OS 66/66. Full suites were not rerun for this integration.

Tested code revisions: Phu_OS ce11307e74190645b2c3843b594d1eae23851a96 (PR #110); Kho-serial-OS d46a6a5149f543b98bb56a503ec2a4afea1040d4 (PR #155). Documentation synchronization commits are not new tested code revisions.

## Findings

- I-F01 FIXED_LAB: replace SELECT * with an explicit six-column projection in the isolated copy; conservative formula semantics remain unchanged.
- I-F02 FIXED_LAB: correct the synthetic setup date before allocation; preserve earlier captures.
- I-F03 REMEDIATED_PARTIAL: full audit contract was read late; R2 was frozen before bounded acceptance replay. Preserve this history; no retrospective CLEAN_PASS. Prelock the full contract before the next native acceptance.
- I-B01 HOLD: deployed provider verifier and integration are not proved. Require a versioned proof contract and isolated provider acceptance.
- I-B02 EXPECTED_HOLD: background ACTIVE HOLD correctly blocks global close; this is not a code defect.

## Evidence boundary

Native writes were performed by an external laboratory driver, not a deployed acquisition or production writer. Adapter conversion used laboratory OOXML; external recalculation is unproved. Source authority, approval and archive attestations were synthetic. Author self-review is not independent review.

Detailed captures and laboratory source locators remain in the private governance evidence system. No operational payload, connected source locator or raw workbook is mirrored here. Original fixture registrations and earlier scoped closures retain their historical meaning.

## Next acceptance

Prelock the contract, define provider-authenticated proof semantics, assign independent review, then run separately authorized isolated acceptance. This documentation update grants no runtime, IAM, permission or inventory-write authority.
