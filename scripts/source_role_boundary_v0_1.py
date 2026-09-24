"""Pure SOURCE_OF_TRUTH / DERIVED_READ_ONLY write-intent boundary.

No external I/O and no production mutation path.
"""

from __future__ import annotations

from dataclasses import dataclass


CONTRACT_ID = "SOURCE_ROLE_BOUNDARY_V1"
SOURCE_OF_TRUTH = "SOURCE_OF_TRUTH"
DERIVED_READ_ONLY = "DERIVED_READ_ONLY"
BUSINESS_WRITE = "BUSINESS_WRITE"
_ALLOWED_ROLES = {SOURCE_OF_TRUTH, DERIVED_READ_ONLY}


@dataclass(frozen=True, slots=True)
class SourceRoleBoundaryRequest:
    """Explicit classification evidence for one warehouse region."""

    contract_id: object
    region_roles: object
    requested_operation: object


@dataclass(frozen=True, slots=True)
class SourceRoleBoundaryResult:
    """Deterministic fail-closed boundary result."""

    status: str
    boundary_pass: bool
    blocking_reasons: tuple[str, ...]
    production_write_authorized: bool = False


def evaluate_source_role_boundary(
    request: SourceRoleBoundaryRequest,
) -> SourceRoleBoundaryResult:
    """Return PASS only for exact SOURCE_OF_TRUTH business-write intent."""

    if type(request) is not SourceRoleBoundaryRequest:
        return SourceRoleBoundaryResult(
            status="HOLD",
            boundary_pass=False,
            blocking_reasons=("REQUEST_INVALID",),
        )

    reasons: set[str] = set()

    if request.contract_id != CONTRACT_ID:
        reasons.add("CONTRACT_INVALID")

    roles = request.region_roles
    valid_container = type(roles) is tuple

    if not valid_container:
        reasons.add("CLASSIFICATION_CONTAINER_INVALID")
        normalized_roles: tuple[object, ...] = ()
    else:
        normalized_roles = roles

        if not normalized_roles:
            reasons.add("CLASSIFICATION_MISSING")
        else:
            invalid_role = any(
                type(role) is not str
                or not role
                or role != role.strip()
                or role not in _ALLOWED_ROLES
                for role in normalized_roles
            )
            if invalid_role:
                reasons.add("CLASSIFICATION_INVALID")

            valid_role_values = {
                role
                for role in normalized_roles
                if type(role) is str and role in _ALLOWED_ROLES
            }
            if valid_role_values == _ALLOWED_ROLES:
                reasons.add("CLASSIFICATION_CONTRADICTORY")
            elif len(normalized_roles) != 1:
                reasons.add("CLASSIFICATION_CARDINALITY_INVALID")

    if request.requested_operation != BUSINESS_WRITE:
        reasons.add("OPERATION_INVALID")

    if (
        valid_container
        and len(normalized_roles) == 1
        and normalized_roles[0] == DERIVED_READ_ONLY
        and request.requested_operation == BUSINESS_WRITE
    ):
        reasons.add("DERIVED_READ_ONLY_WRITE_BLOCKED")

    if not reasons:
        return SourceRoleBoundaryResult(
            status="PASS",
            boundary_pass=True,
            blocking_reasons=(),
        )

    return SourceRoleBoundaryResult(
        status="HOLD",
        boundary_pass=False,
        blocking_reasons=tuple(sorted(reasons)),
    )
