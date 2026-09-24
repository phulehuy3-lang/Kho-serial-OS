# Security Policy

## Public repository boundary

Do not commit operational warehouse data or evidence to this repository.

Prohibited content includes:

- real serial inventories or customer/account identifiers;
- invoices, delivery records, source images/PDFs, workbook exports, CSV/TSV dumps, or archives;
- credentials, tokens, private keys, passwords, or secrets;
- production Google Sheets/Drive URLs or document IDs;
- MASTER LIVE or other production snapshots;
- any code path that performs production writes.

Tests must use synthetic identifiers and synthetic dates only.

## Sole-mission scope boundary

All governed artifacts must be registered in the warehouse-serial scope
manifest and directly support the warehouse-serial mission. Unrelated generic
platform, finance, fiction, communications, PHÚ OS runtime/memory, or personal
automation capability is prohibited even when it is technically side-effect-free.

The scope manifest is machine-checkable declaration, not semantic proof.
Human review must reject nominal or misleading capability mappings.

The repository boundary and warehouse-scope checks are defense-in-depth and do
not replace human review.
