"""Pure coverage-coherence check; never proves provider provenance or live completeness."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CoverageResult:
    coverage_coherent: bool
    blocking_reasons: tuple[str, ...]
    live_read_authorized: bool = False
    executable_acquisition_authorized: bool = False
    production_write_authorized: bool = False


def assess_coverage(
    first_position: object,
    last_position: object,
    captured_positions: object,
    expected_context: object,
    captured_context: object,
    method_accepted: object,
    consistency_accepted: object,
    enumeration_terminated: object,
    truncated: object,
    limit_exceeded: object,
) -> CoverageResult:
    """Check supplied metadata only; approval booleans remain untrusted assertions.

    Context is an eight-text tuple: target hash, registry hash, binding hash,
    method hash, consistency-proof hash, task, scope and logical surface.
    Positions cover the entire authority domain BEFORE active/scope filtering.
    A sealed empty domain is represented by last_position = first_position - 1.
    """
    reasons: set[str] = set()
    valid_bounds = (
        type(first_position) is int and type(last_position) is int
        and first_position >= 0 and last_position >= first_position - 1
        and last_position - first_position < 100000
    )
    if not valid_bounds:
        reasons.add("AUTHORITY_BOUNDS_INVALID")
    contexts_valid = (
        type(expected_context) is tuple and type(captured_context) is tuple
        and len(expected_context) == 8 and len(captured_context) == 8
        and all(type(v) is str and bool(v) and v == v.strip()
                for v in expected_context + captured_context)
    )
    if not contexts_valid or expected_context != captured_context:
        reasons.add("CONTEXT_INVALID_OR_DRIFTED")
    elif expected_context[7] not in (
        "ACTIVE_SERIAL_INTERVAL_UNIVERSE", "ACTIVE_HOLD_INTERVAL_UNIVERSE"
    ):
        reasons.add("SURFACE_INVALID")
    positions_valid = (
        type(captured_positions) is tuple
        and all(type(p) is int for p in captured_positions)
    )
    if not positions_valid:
        reasons.add("POSITION_CONTAINER_INVALID")
    elif valid_bounds:
        expected = tuple(range(first_position, last_position + 1))
        if len(captured_positions) != len(set(captured_positions)):
            reasons.add("DUPLICATE_POSITION")
        if tuple(sorted(captured_positions)) != expected:
            reasons.add("DOMAIN_COVERAGE_MISMATCH")
    if method_accepted is not True:
        reasons.add("AUTHORITY_METHOD_UNACCEPTED")
    if consistency_accepted is not True:
        reasons.add("PROVIDER_CONSISTENCY_UNACCEPTED")
    if enumeration_terminated is not True:
        reasons.add("ENUMERATION_UNTERMINATED")
    if truncated is not False:
        reasons.add("TRUNCATED_OR_UNKNOWN")
    if limit_exceeded is not False:
        reasons.add("LIMIT_EXCEEDED_OR_UNKNOWN")
    return CoverageResult(not reasons, tuple(sorted(reasons)))
