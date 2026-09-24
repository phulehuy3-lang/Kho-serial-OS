# WAREHOUSE_SERIAL_REPOSITORY_SCOPE_V1

Status: **CANONICAL SOLE-MISSION SCOPE GATE**

## Mission

`Kho-serial-OS` has exactly one mission: engineering controls for serial-range warehouse operations.

Every rule, script, test, design document, and CI capability in this repository must directly support at least one warehouse-serial capability:

- `INBOUND`
- `OUTBOUND`
- `INVENTORY`
- `SERIAL_IDENTITY_RANGE`
- `SOURCE_ALLOCATION`
- `HOLD_QUARANTINE`
- `RECONCILIATION`
- `WAREHOUSE_DOCUMENT_INTEGRITY`
- `REPOSITORY_SAFETY`

`REPOSITORY_SAFETY` is limited to safety of this warehouse-serial repository and its public engineering boundary. It is not a license to add general-purpose governance, productivity, finance, fiction, communications, or unrelated platform capabilities.

## Exact-set enforcement

The canonical manifest is `rules/WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json`.

The checker `scripts/check_warehouse_serial_scope_v1.py` discovers every regular file under:

- `rules/`
- `scripts/`
- `tests/`
- `.github/workflows/`

The discovered set must exactly equal the manifest artifact set. For every artifact, the manifest must provide:

1. one or more allowed warehouse-serial capabilities;
2. a non-empty rationale explaining the direct warehouse-serial relationship.

Missing artifacts, extra manifest entries, unknown capabilities, blank rationales, duplicate paths, or schema/mission drift fail closed.

## Human semantic review remains mandatory

The manifest makes scope declaration mandatory and machine-checkable. It cannot prove that a rationale is truthful. Reviewers must reject an artifact whose declared capability is merely nominal or whose actual purpose is outside warehouse serial operations.

Generic infrastructure is allowed only when it is necessary to protect, test, or compose warehouse-serial controls in this repository.

## Prohibited scope

Do not add capabilities whose primary purpose is unrelated to warehouse serial operations, including:

- general PHÚ OS runtime or memory governance;
- finance or investing;
- fiction/media workflows;
- email, calendar, messaging, or generic personal automation;
- generic business administration unrelated to warehouse serials;
- production credentials, live warehouse data, or executable production writers.

Any ambiguous proposal is `HOLD_SCOPE` until a direct warehouse-serial purpose is documented and reviewed.

## Authority boundary

Passing this scope gate does not authorize production writes, MASTER LIVE mutation, connected-service access, or operational release. Existing public-boundary, HOLD, reconciliation, and production-authorization controls remain independently required.
