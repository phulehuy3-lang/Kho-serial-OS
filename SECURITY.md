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

The repository boundary check is defense-in-depth and does not replace human review.
