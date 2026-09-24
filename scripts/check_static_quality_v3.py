"""Additive V3 static capability checks.

V3 supplements the frozen V1/V2 gates. It detects positional Path.open write
modes and simple aliases of write-capable bound methods. It never executes the
source being scanned.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sys


SOURCE_DIRS = ("scripts", "tests")
WRITE_METHODS = {
    "write_text",
    "write_bytes",
    "unlink",
    "touch",
    "mkdir",
    "rmdir",
    "rename",
    "replace",
}
WRITE_MODE_TOKENS = ("w", "a", "x", "+")


@dataclass(frozen=True, slots=True)
class StaticIssueV3:
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


def _literal_string(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and type(node.value) is str:
        return node.value
    return None


def _positional_or_keyword_mode(node: ast.Call) -> tuple[str | None, bool]:
    mode_node: ast.expr | None = None
    if node.args:
        mode_node = node.args[0]
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode_node = keyword.value
    if mode_node is None:
        return None, False
    literal = _literal_string(mode_node)
    if literal is None:
        return None, True
    return literal, False


def _is_write_mode(mode: str) -> bool:
    return any(token in mode for token in WRITE_MODE_TOKENS)


def _simple_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        value = node.value
        if not isinstance(value, ast.Attribute):
            continue
        method = value.attr
        if method not in WRITE_METHODS and method != "open":
            continue

        if isinstance(node, ast.Assign):
            targets = node.targets
        else:
            targets = [node.target]

        for target in targets:
            if isinstance(target, ast.Name):
                aliases[target.id] = method
    return aliases


def scan_static_quality_v3(root: Path) -> tuple[StaticIssueV3, ...]:
    """Return only additive V3 issues; V1/V2 remain separate required gates."""

    root = root.resolve()
    issues: list[StaticIssueV3] = []

    for path in _python_files(root):
        rel = path.relative_to(root).as_posix()
        is_script = rel.startswith("scripts/")

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel)
        except (OSError, SyntaxError) as exc:
            issues.append(
                StaticIssueV3(
                    rel,
                    exc.lineno if isinstance(exc, SyntaxError) and exc.lineno else 0,
                    "V3_PYTHON_PARSE_FAIL",
                    str(exc),
                )
            )
            continue

        aliases = _simple_aliases(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if (
                is_script
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "open"
                and node.args
            ):
                mode, dynamic = _positional_or_keyword_mode(node)
                if dynamic or (mode is not None and _is_write_mode(mode)):
                    issues.append(
                        StaticIssueV3(
                            rel,
                            node.lineno,
                            "V3_FORBIDDEN_POSITIONAL_OPEN_WRITE",
                            "dynamic positional open mode"
                            if dynamic
                            else f"positional open mode {mode!r}",
                        )
                    )

            if is_script and isinstance(node.func, ast.Name):
                method = aliases.get(node.func.id)
                if method in WRITE_METHODS:
                    issues.append(
                        StaticIssueV3(
                            rel,
                            node.lineno,
                            "V3_FORBIDDEN_WRITE_ALIAS",
                            f"{node.func.id} aliases {method}",
                        )
                    )
                elif method == "open":
                    mode, dynamic = _positional_or_keyword_mode(node)
                    if dynamic or (mode is not None and _is_write_mode(mode)):
                        issues.append(
                            StaticIssueV3(
                                rel,
                                node.lineno,
                                "V3_FORBIDDEN_WRITE_ALIAS",
                                f"{node.func.id} aliases open",
                            )
                        )

    return tuple(issues)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path.cwd()
    issues = scan_static_quality_v3(root)

    if not issues:
        print("STATIC_QUALITY_V3_PASS")
        return 0

    print("STATIC_QUALITY_V3_FAIL")
    for issue in issues:
        print(f"{issue.path}:{issue.line}: {issue.code}: {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
