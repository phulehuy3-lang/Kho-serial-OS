# LICENSE_DECISION_PROPOSAL_V0_1

Status: **OWNER DECISION REQUIRED**

## Purpose

Prepare a concrete license decision without silently choosing one for the
repository owner.

This file is a decision aid only. It is **not** a license grant and does not
replace a `LICENSE` file.

## Current state

At the 2026-09-25 remediation checkpoint:

- no `LICENSE` or `LICENSE.md` file is present;
- no license is selected by this remediation;
- the repository is public, but public visibility alone is not the same as an
  explicit reuse license.

## Option A — MIT

Typical characteristics:

- short permissive license;
- permits reuse, modification and redistribution subject to preservation of the
  copyright/license notice;
- includes warranty/liability disclaimer;
- does not contain the explicit patent-license language found in Apache-2.0.

Owner decision required:

`[ ] Select MIT`

## Option B — Apache License 2.0

Typical characteristics:

- permissive license;
- permits reuse, modification and redistribution under its notice conditions;
- contains an explicit patent license and patent-termination provisions;
- has more notice/compliance text than MIT.

Owner decision required:

`[ ] Select Apache-2.0`

## Option C — keep no explicit license for now

This keeps the current repository state unchanged while the owner decides.

Owner decision required:

`[ ] Keep license UNSET for now`

## Decision record required before activation

Before adding a real license file, record all of:

- chosen SPDX identifier;
- owner approval date;
- whether any third-party code or copied material requires separate notices;
- exact PR that adds the license;
- post-merge read-back of the selected license file.

This remediation does not copy ERP/library code into the repository and does
not infer compatibility obligations that have not been established.

## Decision

`UNSET — OWNER DECISION REQUIRED`
