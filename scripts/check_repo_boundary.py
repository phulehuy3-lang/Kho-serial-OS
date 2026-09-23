"""Fail-closed public repository boundary guard.

Scans the checked-out repository snapshot. This is one layer only; CI also
runs the Git history boundary gate so content cannot be hidden in an earlier
commit and removed before the PR head.

This module performs no network or production I/O.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
import re
import sys

FORBIDDEN_SUFFIXES = {
    ".xlsx", ".xlsm", ".xlsb", ".ods",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".csv", ".tsv", ".zip", ".7z", ".rar",
    ".jpg", ".jpeg", ".png", ".webp", ".heic",
    ".eml", ".msg",
}

FORBIDDEN_DIRS = {
    "data", "evidence", "exports", "master_live",
    "production_snapshots", "raw_production",
}

SKIP_DIRS = {".git"}
MAX_TEXT_BYTES = 1_000_000

SECRET_PATTERNS = (
    ("PRIVATE_KEY", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GITHUB_TOKEN", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("GOOGLE_API_KEY", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("AWS_ACCESS_KEY", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("SLACK_TOKEN", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("REFRESH_TOKEN", re.compile(r"(?i)\brefresh[_-]?token\b\s*[:=]\s*['\"][^'\"]{12,}['\"]")),
)

CONNECTED_DOC_URL_PATTERNS = (
    ("GOOGLE_SHEETS_URL", re.compile(r"https://docs\.google\.com/spreadsheets/d/[A-Za-z0-9_-]{20,}")),
    ("GOOGLE_DOCS_URL", re.compile(r"https://docs\.google\.com/document/d/[A-Za-z0-9_-]{20,}")),
    ("GOOGLE_DRIVE_URL", re.compile(r"https://drive\.google\.com/(?:file/d/|open\?id=)[A-Za-z0-9_-]{20,}")),
)

LABELED_PRODUCTION_ID_PATTERN = re.compile(
    r"(?i)\b(?:serial|seri|imei|iccid|msisdn|mst|tax\s*id|"
    r"số\s*tài\s*khoản|so\s*tai\s*khoan|account(?:\s*number)?)\b"
    r"[^\n\r\d]{0,20}(\d{10,22})\b"
)

EMAIL_PATTERN = re.compile(
    r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
)
ALLOWED_PUBLIC_EMAIL_SUFFIXES = ("@users.noreply.github.com", "@noreply.github.com")


@dataclass(frozen=True, slots=True)
class BoundaryIssue:
    path: str
    code: str
    detail: str


def _iter_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_symlink() or path.is_file():
            yield path


def scan_text(rel_text: str, content: str) -> tuple[BoundaryIssue, ...]:
    issues: list[BoundaryIssue] = []

    for code, pattern in SECRET_PATTERNS:
        if pattern.search(content):
            issues.append(BoundaryIssue(rel_text, code, "credential/token-like material"))

    for code, pattern in CONNECTED_DOC_URL_PATTERNS:
        if pattern.search(content):
            issues.append(BoundaryIssue(rel_text, code, "connected production document URL/ID is not allowed"))

    if LABELED_PRODUCTION_ID_PATTERN.search(content):
        issues.append(BoundaryIssue(
            rel_text,
            "LABELED_PRODUCTION_IDENTIFIER",
            "long numeric identifier appears next to a production label",
        ))

    # Generic personal emails are prohibited in repository file content.
    # GitHub noreply addresses are allowed for documentation/test fixtures.
    for match in EMAIL_PATTERN.finditer(content):
        value = match.group(0).lower()
        if not value.endswith(ALLOWED_PUBLIC_EMAIL_SUFFIXES):
            issues.append(BoundaryIssue(
                rel_text,
                "PUBLIC_PERSONAL_EMAIL",
                "non-noreply email address appears in public repository content",
            ))
            break

    return tuple(issues)


def scan_repository(root: Path) -> tuple[BoundaryIssue, ...]:
    root = root.resolve()
    issues: list[BoundaryIssue] = []

    for path in _iter_files(root):
        rel = path.relative_to(root)
        rel_text = rel.as_posix()

        if any(part.lower() in FORBIDDEN_DIRS for part in rel.parts[:-1]):
            issues.append(BoundaryIssue(rel_text, "FORBIDDEN_DIRECTORY", "operational/evidence directory is not allowed"))

        if path.is_symlink():
            issues.append(BoundaryIssue(rel_text, "SYMLINK", "linked paths are not allowed"))
            continue

        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES:
            issues.append(BoundaryIssue(rel_text, "FORBIDDEN_FILE_TYPE", f"{suffix} payload is not allowed"))
            continue

        try:
            if path.stat().st_size > MAX_TEXT_BYTES:
                issues.append(BoundaryIssue(rel_text, "UNSCANNABLE_FILE", "file exceeds text scan limit"))
                continue
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            issues.append(BoundaryIssue(rel_text, "UNSCANNABLE_FILE", "file is not readable UTF-8 text"))
            continue

        if "\x00" in content:
            issues.append(BoundaryIssue(rel_text, "UNSCANNABLE_FILE", "file contains binary NUL data"))
            continue

        issues.extend(scan_text(rel_text, content))

    return tuple(issues)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path.cwd()
    issues = scan_repository(root)

    if not issues:
        print("REPOSITORY_BOUNDARY_PASS")
        return 0

    print("REPOSITORY_BOUNDARY_FAIL")
    for issue in issues:
        print(f"{issue.path}: {issue.code}: {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
