"""Fail-closed exact-set scope gate for the Kho Serial OS sole mission."""

from __future__ import annotations

import json
from pathlib import Path
import sys


MANIFEST_PATH = "rules/WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json"
SCHEMA_ID = "WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1"
MISSION_ID = "WAREHOUSE_SERIAL_ONLY"
GOVERNED_ROOTS = ("rules", "scripts", "tests", ".github/workflows")
ALLOWED_CAPABILITIES = {
    "INBOUND",
    "OUTBOUND",
    "INVENTORY",
    "SERIAL_IDENTITY_RANGE",
    "SOURCE_ALLOCATION",
    "HOLD_QUARANTINE",
    "RECONCILIATION",
    "WAREHOUSE_DOCUMENT_INTEGRITY",
    "REPOSITORY_SAFETY",
}


def _discover(root: Path) -> set[str]:
    discovered: set[str] = set()
    for relative_root in GOVERNED_ROOTS:
        base = root / relative_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            discovered.add(path.relative_to(root).as_posix())
    return discovered


def check_scope(root: Path) -> tuple[str, ...]:
    root = root.resolve()
    manifest_file = root / MANIFEST_PATH
    if not manifest_file.is_file():
        return ("MANIFEST_MISSING",)

    try:
        payload = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ("MANIFEST_INVALID_JSON",)

    errors: set[str] = set()
    if not isinstance(payload, dict):
        return ("MANIFEST_INVALID_SCHEMA",)
    if payload.get("schema_id") != SCHEMA_ID:
        errors.add("SCHEMA_ID_INVALID")
    if payload.get("mission") != MISSION_ID:
        errors.add("MISSION_INVALID")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return tuple(sorted(errors | {"ARTIFACTS_INVALID"}))

    declared: set[str] = set()
    for item in artifacts:
        if not isinstance(item, dict):
            errors.add("ARTIFACT_ENTRY_INVALID")
            continue
        path = item.get("path")
        capabilities = item.get("capabilities")
        rationale = item.get("rationale")

        if not isinstance(path, str) or not path or path != path.strip():
            errors.add("ARTIFACT_PATH_INVALID")
            continue
        if path in declared:
            errors.add(f"DUPLICATE_PATH:{path}")
        declared.add(path)

        if (
            not isinstance(capabilities, list)
            or not capabilities
            or any(not isinstance(value, str) for value in capabilities)
            or len(capabilities) != len(set(capabilities))
        ):
            errors.add(f"CAPABILITIES_INVALID:{path}")
        else:
            unknown = set(capabilities) - ALLOWED_CAPABILITIES
            if unknown:
                errors.add(f"CAPABILITY_UNKNOWN:{path}")

        if not isinstance(rationale, str) or not rationale.strip():
            errors.add(f"RATIONALE_MISSING:{path}")

    discovered = _discover(root)
    for path in sorted(discovered - declared):
        errors.add(f"UNDECLARED_ARTIFACT:{path}")
    for path in sorted(declared - discovered):
        errors.add(f"STALE_MANIFEST_ENTRY:{path}")

    return tuple(sorted(errors))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path.cwd()
    errors = check_scope(root)
    if not errors:
        print("WAREHOUSE_SERIAL_SCOPE_PASS")
        return 0
    print("WAREHOUSE_SERIAL_SCOPE_FAIL")
    for error in errors:
        print(error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
