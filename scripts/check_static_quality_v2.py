"""Additional trusted policy for aliased process and dynamic imports.

V2 supplements the frozen V1 policy; it does not relax any V1 rejection.
"""

from __future__ import annotations

import ast
from pathlib import Path
import sys

try:
    from scripts.check_static_quality import StaticIssue, scan_static_quality
except ModuleNotFoundError:
    from check_static_quality import StaticIssue, scan_static_quality


BLOCKED_ROOTS = {"os", "subprocess", "importlib", "ctypes", "multiprocessing"}
BLOCKED_BUILTINS = {"eval", "exec", "__import__", "getattr", "setattr"}
ALLOWED_SCRIPT_IMPORTS = {
    "__future__", "ast", "collections", "dataclasses", "datetime", "hashlib",
    "json", "pathlib", "re", "scripts", "sys", "types", "typing",
    "check_repo_boundary", "check_static_quality", "check_git_history_boundary",
}


def scan_static_quality_v2(root: Path) -> tuple[StaticIssue, ...]:
    """Apply V1 and reject aliasable process/dynamic facilities in code.

    Existing V1's dedicated local Git-history scanner is the sole exception
    for subprocess. No other production module needs these import roots.
    """

    issues = list(scan_static_quality(root))
    for directory in ("scripts", "tests"):
        base = root / directory
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = path.relative_to(root).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
            except (OSError, SyntaxError):
                continue  # V1 already rejects unreadable or unparsable files.
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = [alias.name.split(".", 1)[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    roots = [node.module.split(".", 1)[0]] if node.module else []
                else:
                    roots = []
                for name in roots:
                    if rel.startswith("scripts/") and name not in ALLOWED_SCRIPT_IMPORTS:
                        if name != "subprocess" or rel != "scripts/check_git_history_boundary.py":
                            issues.append(StaticIssue(rel, node.lineno, "V2_IMPORT_NOT_ALLOWED", name))
                    if name in BLOCKED_ROOTS and rel not in {
                        "scripts/check_git_history_boundary.py",
                        "tests/test_git_history_boundary.py",
                    }:
                        issues.append(StaticIssue(rel, node.lineno, "V2_BLOCKED_IMPORT", name))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if (
                        node.func.id in BLOCKED_BUILTINS
                        and rel.startswith("scripts/")
                        and not (
                            node.func.id == "getattr"
                            and rel == "scripts/check_static_quality.py"
                        )
                    ):
                        issues.append(StaticIssue(rel, node.lineno, "V2_DYNAMIC_CALL", node.func.id))
    return tuple(issues)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path.cwd()
    issues = scan_static_quality_v2(root.resolve())
    if not issues:
        print("STATIC_QUALITY_V2_PASS")
        return 0
    print("STATIC_QUALITY_V2_FAIL")
    for issue in issues:
        print(f"{issue.path}:{issue.line}: {issue.code}: {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
