# Kho Serial OS

Public, sanitized engineering controls for serial-range warehouse workflows.

## Scope

This repository contains only generic control rules, side-effect-free Python logic, synthetic tests, and CI.

It intentionally excludes operational warehouse data, real serial inventories, invoices, delivery documents, workbook exports, connected Drive/Sheets identifiers, credentials, secrets, and any production write capability.

## Safety model

- fail closed when a required control input is missing or malformed;
- keep serial identities as text;
- treat derived views as read-only;
- separate engineering validation from production authorization;
- use synthetic data in tests;
- require a repository-boundary check before tests.

## Initial public baseline

The bootstrap implements the deterministic NEAREST-PRIOR source ordering rule and publishes the SOURCE_OF_TRUTH / DERIVED_READ_ONLY boundary rule. It is not an operational database and is not authoritative for live warehouse state.
