# Outbound Standard v1 — Public-safe enforcement contract

Status: **ACTIVE PROSPECTIVE CONTRACT**

This document mirrors five canonical outbound controls from the warehouse governance registry. It is partner-agnostic and grants no Production write, provider, IAM, credential, Google Sheets mutation or automatic BBGH authority.

## Canonical control set

1. **SOP_OUTBOUND_STANDARD_V1_0**
2. **CTRL_OUTBOUND_EFFECTIVE_DATE_SEMANTICS_V1**
3. **CTRL_BBGH_TEMPLATE_AUTHORITY_V1**
4. **CTRL_ALLOCATION_PLAN_FIELD_BOUND_WRITER_V1**
5. **CTRL_OUTBOUND_SINGLE_PASS_EXECUTION_BUNDLE_V1**

## Effective-date semantics

An old invoice/document date does not prove historical inventory state.

Every outbound resolves one mode before source ranking:

- `CURRENT_STATE_SAFE_EXECUTION`: allocate from current eligible stock.
- `POSTFACTO_PHYSICAL_DELIVERY`: exact prior physical serial evidence governs under the existing post-facto physical-delivery control.
- `HISTORICAL_AS_OF_RECONSTRUCTION`: read-only reconstruction unless a separately approved chronology remediation proves a safe write path.

Current-state allocation must never be represented as historical as-of-date allocation.

## BBGH template authority

Template selection is hierarchical:

1. verified partner-specific canonical template;
2. approved document-family template;
3. approved generic BBGH template.

Fallback use is explicit. A generic or family template may not be described as a partner-specific template. Generated artifacts never overwrite the canonical template and never invent representatives.

## Allocation-plan writer

`SYSTEM_ALLOCATION_PLAN` inputs are bound by live header identity. Canonical allocation fields are written only to their field-bound surface; no append-from-column-A shortcut is permitted. `RankPlanDecision` remains formula-owned. A literal or positionally misplaced `PASS_PLAN_RANK` blocks inventory mutation.

## Single-pass execution

The normal success path is bounded:

`fresh snapshot -> sealed prewrite manifest -> one mutation batch -> consolidated readback -> final anti-replay lock -> close`

Extra mutation rounds are remediation only. They are not part of the normal workflow.

## Terminal classification

- `CLEAN_PASS`: all applicable controls passed without repaired historical or control defects.
- `REMEDIATED_PASS`: effective state is correct but a control defect was repaired and remains in history.
- unresolved template/date/evidence/source/allocation/control defects remain fail-closed.

Correct stock alone is insufficient for `CLEAN_PASS`.

## Regression minimum

Tests must include:

- backdated document with no prior-delivery proof -> current-state safe mode;
- exact prior-delivery proof -> post-facto mode;
- historical reconstruction -> no Production mutation authority;
- partner/family/generic template priority and no-template block;
- live-header allocation binding and offset/missing/duplicate header block;
- formula-owned `PASS_PLAN_RANK`;
- exactly one Production mutation batch in the normal path;
- missing consolidated readback or final anti-replay lock blocks close;
- repaired defect yields `REMEDIATED_PASS`, never `CLEAN_PASS`.
