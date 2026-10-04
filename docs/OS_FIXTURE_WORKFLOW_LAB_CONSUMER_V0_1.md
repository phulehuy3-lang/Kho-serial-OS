# Kho consumer of PHU finite fixture workflow v0.1

PHU's read-only lab orchestration invokes existing Kho controls in a separate isolated process: `assess_native_domain_lab`, `validate_native_v2_lab`, then `assess_fixture_allocation_lab`. No Kho control semantics or writer is changed. Keep locators, frozen model, captures, code pin, SQLite replay ledger and receipts in external custody.

Required ordering: both repos' domain gates pass first; PHU mapping and Kho schema/allocation diagnostics pass; a distinct readback acquisition has the same fingerprint; both readback domain gates pass. A PHU regular `scripts` package must not shadow Kho's namespace package. Input code byte hashes and the R4 fixed model hash are mandatory. Git base SHA remains external attestation.

`PASS_LAB`, `PASS_SCOPED`, `PASS_SCHEMA_ONLY`, and internal mapping readiness are finite synthetic diagnostics only. They grant no provider atomicity, production completeness, operational acceptance, mutation capability or production write authority. Same-payload replay refers to historical receipt and keeps Action HOLD; conflict, incomplete/failed ledger record and drift HOLD. Raw evidence does not belong in this repository.

Checkpoint 2026-10-04: unchanged Kho dependency suite 514/514 PASS; actual connected R4 read-only capture/control/readback chain PASS_LAB in both repos; 16 external transport fault-harness cases have expected results. These do not replace old NOT_RUN/PARTIAL history or prove inbound/outbound writes. Candidate publication and CI/main cutover are separate acceptance steps.
