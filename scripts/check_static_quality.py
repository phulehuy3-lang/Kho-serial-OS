"""Fail-closed static capability gate for the public executable baseline.

Network-capable imports and unsafe process execution are rejected across
scripts and tests. Production-facing scripts are also prohibited from local
file mutation. The Git-history scanner and its dedicated regression test may
invoke only the local `git` executable.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sys


SOURCE_DIRS = ("scripts", "tests")
GIT_SUBPROCESS_FILES = {
    "scripts/check_git_history_boundary.py",
    "tests/test_git_history_boundary.py",
}

FORBIDDEN_IMPORT_ROOTS = {
    "boto3", "ftplib", "googleapiclient", "gspread", "http", "httpx",
    "requests", "smtplib", "socket", "urllib", "urllib3",
}

FORBIDDEN_WRITE_METHODS = {
    "write_text", "write_bytes", "unlink", "touch", "mkdir", "rmdir",
    "rename", "replace",
}

FORBIDDEN_OS_WRITE_CALLS = {
    "remove", "unlink", "rename", "replace", "mkdir", "makedirs", "rmdir",
    "removedirs",
}


@dataclass(frozen=True, slots=True)
class StaticIssue:
    path: str
    line: int
    code: str
    detail: str


def _python_files(root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for directory in SOURCE_DIRS:
        base = root / directory
        if not base.exists():
            continue
        files.extend(sorted(base.rglob("*.py")))
    return tuple(files)


def _import_roots(node: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name.split(".", 1)[0] for alias in node.names)
    if node.module is None:
        return ()
    return (node.module.split(".", 1)[0],)


def _open_mode(node: ast.Call) -> tuple[str | None, bool]:
    mode_node: ast.expr | None = None
    if len(node.args) >= 2:
        mode_node = node.args[1]
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode_node = keyword.value
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return mode_node.value, False
    return None, mode_node is not None


def _call_attr_chain(node: ast.expr) -> tuple[str, ...]:
    parts: list[str] = []
    cursor = node
    while isinstance(cursor, ast.Attribute):
        parts.append(cursor.attr)
        cursor = cursor.value
    if isinstance(cursor, ast.Name):
        parts.append(cursor.id)
    return tuple(reversed(parts))


def _git_subprocess_call_is_allowed(node: ast.Call) -> bool:
    chain = _call_attr_chain(node.func)
    if chain != ("subprocess", "run"):
        return False
    if not node.args:
        return False
    cmd = node.args[0]
    if not isinstance(cmd, (ast.List, ast.Tuple)) or not cmd.elts:
        return False
    first = cmd.elts[0]
    return isinstance(first, ast.Constant) and first.value == "git"


def scan_static_quality(root: Path) -> tuple[StaticIssue, ...]:
    root = root.resolve()
    issues: list[StaticIssue] = []

    for path in _python_files(root):
        rel = path.relative_to(root).as_posix()
        is_script = rel.startswith("scripts/")

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel)
        except (OSError, SyntaxError) as exc:
            issues.append(StaticIssue(rel, getattr(exc, "lineno", 0) or 0, "PYTHON_PARSE_FAIL", str(exc)))
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for root_name in _import_roots(node):
                    if root_name in FORBIDDEN_IMPORT_ROOTS:
                        issues.append(StaticIssue(rel, node.lineno, "FORBIDDEN_NETWORK_IMPORT", root_name))
                    if root_name == "subprocess" and rel not in GIT_SUBPROCESS_FILES:
                        issues.append(StaticIssue(rel, node.lineno, "FORBIDDEN_SUBPROCESS_IMPORT", root_name))

            if not isinstance(node, ast.Call):
                continue

            chain = _call_attr_chain(node.func)
            attr = chain[-1] if chain else None

            if is_script and attr in FORBIDDEN_WRITE_METHODS:
                issues.append(StaticIssue(rel, node.lineno, "FORBIDDEN_FILE_WRITE", ".".join(chain)))

            if is_script and len(chain) >= 2 and chain[-2] == "os" and attr in FORBIDDEN_OS_WRITE_CALLS:
                issues.append(StaticIssue(rel, node.lineno, "FORBIDDEN_FILE_WRITE", ".".join(chain)))

            if is_script and (chain in {("open",), ("Path", "open")} or attr == "open"):
                mode, dynamic = _open_mode(node)
                if dynamic or (mode is not None and any(token in mode for token in ("w", "a", "x", "+"))):
                    issues.append(StaticIssue(
                        rel, node.lineno, "FORBIDDEN_FILE_WRITE",
                        "dynamic open mode" if dynamic else f"open mode {mode!r}",
                    ))

            if chain and chain[0] == "subprocess":
                if rel not in GIT_SUBPROCESS_FILES or not _git_subprocess_call_is_allowed(node):
                    issues.append(StaticIssue(rel, node.lineno, "FORBIDDEN_SUBPROCESS_CALL", ".".join(chain)))

            if chain in {("os", "system"), ("os", "popen")}:
                issues.append(StaticIssue(rel, node.lineno, "FORBIDDEN_SUBPROCESS_CALL", ".".join(chain)))

            if chain == ("__import__",) and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS:
                        issues.append(StaticIssue(rel, node.lineno, "FORBIDDEN_DYNAMIC_IMPORT", arg.value))

    return tuple(issues)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path.cwd()
    issues = scan_static_quality(root)

    if not issues:
        print("STATIC_QUALITY_PASS")
        return 0

    print("STATIC_QUALITY_FAIL")
    for issue in issues:
        print(f"{issue.path}:{issue.line}: {issue.code}: {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
