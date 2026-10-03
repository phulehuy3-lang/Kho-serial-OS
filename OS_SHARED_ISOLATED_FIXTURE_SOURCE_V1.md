# Shared isolated warehouse fixture source V1

Fixture identity: `OS_SHARED_ISOLATED_FIXTURE_V1`.

This source registration binds a synthetic-only external workbook to warehouse engineering controls. It contains technical artifact identity and schema mapping. Workbook bytes and custody locators remain outside this repository.

## Validation boundary

The workbook supports schema/type checks, strict serial TEXT identity, exact QUERY semantic identity, and independent reconciliation against a synthetic serialized projection cache. The cache at `ELIGIBLE_STOCK!A3` is explicitly serialized test data with cached header `IntervalID`, using the verified export wrapper. It does not prove that Excel or Google Sheets executed the formula.

`external_recalculation_proven=False`; allocation acceptance remains `NOT_RUN`; operational acceptance remains false. Live-read, executable acquisition, and Production write authorization all remain false. A fixture PASS does not activate an authority record or change MASTER LIVE.

## Mapping

| Logical surface | Workbook alias |
| --- | --- |
| INBOUND_SOURCE_RECORD | V2_SOURCE |
| ACTIVE_SERIAL_INTERVAL_UNIVERSE | V2_ACTIVE |
| INBOUND_DERIVED_QUERY_PROJECTION | V2_DERIVED |
| INBOUND_QUERY_FORMULA_ANCHOR | V2_ANCHOR |
| ACTIVE_HOLD_INTERVAL_UNIVERSE | V2_HOLD |

Logical aliases use schema field order, header row 1 and data from row 2. Physical adapter mapping uses `SYSTEM_INTERVAL_STATE`, `ELIGIBLE_STOCK`, and `SYSTEM_HOLD_REGISTRY`. Existing canonical contracts remain unchanged.

## Reported local verification

The independently supplied workbook has 11 sheets. Saved-file validation passed the existing Phu adapter, Kho V2 schema and serial bridge, lexical identity/projection parity, and unchanged-file-hash checks. The pinned existing targeted tests passed 61/61; actual workbook mutations produced the expected fail-closed outcome in 16/16 cases (13 Phu HOLD and 3 Kho V2 REJECT).

These counts describe local execution on the synthetic fixture. CI on this metadata PR checks engineering repository safety and regressions; it does not download or execute the external workbook and does not authenticate external custody. Runtime acceptance, external spreadsheet recalculation, allocation acceptance, and live worksheet acquisition are outside this proof.

## Identity and custody

Before using a separately supplied file, independently compare its byte SHA-256 with `rules/OS_SHARED_ISOLATED_FIXTURE_SOURCE_V1.json`. A changed file is a different generation and requires a new bound registration. This record is a technical source identity, not an automated loader or an active target-authority record.

Only technical metadata and this document are stored in GitHub. No office payload, operational serial record, external document ID, credential, or write path is introduced.
