"""Scan every commit introduced by a PR/push for public-boundary violations.

Usage:
    python scripts/check_git_history_boundary.py BASE_SHA HEAD_SHA

BASE_SHA is exclusive. HEAD_SHA is inclusive. The scanner inspects commit
author/committer email metadata and every changed file as it existed in each
introduced commit. This catches a sensitive payload that is added in one
commit and deleted in a later commit before the PR head.

This module performs read-only local Git subprocess calls only.
"""

from __future__ import annotations

from pathlib import PurePosixPath
import subprocess
import sys

try:
    from scripts.check_repo_boundary import (
        ALLOWED_PUBLIC_EMAIL_SUFFIXES,
        FORBIDDEN_DIRS,
        FORBIDDEN_SUFFIXES,
        MAX_TEXT_BYTES,
        BoundaryIssue,
        scan_text,
    )
except ModuleNotFoundError:
    from check_repo_boundary import (
        ALLOWED_PUBLIC_EMAIL_SUFFIXES,
        FORBIDDEN_DIRS,
        FORBIDDEN_SUFFIXES,
        MAX_TEXT_BYTES,
        BoundaryIssue,
        scan_text,
    )


ZERO_SHA = "0" * 40


def _git(args: list[str], *, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    return result.stdout


def _commit_list(base_sha: str, head_sha: str) -> tuple[str, ...]:
    if base_sha == ZERO_SHA:
        output = _git(["rev-list", "--reverse", head_sha])
    else:
        output = _git(["rev-list", "--reverse", f"{base_sha}..{head_sha}"])
    assert isinstance(output, str)
    return tuple(line for line in output.splitlines() if line)


def _commit_emails(commit: str) -> tuple[str, str]:
    output = _git(["show", "-s", "--format=%ae%n%ce", commit])
    assert isinstance(output, str)
    lines = output.splitlines()
    if len(lines) != 2:
        raise RuntimeError(f"unexpected email metadata for {commit}")
    return lines[0].strip(), lines[1].strip()


def _email_is_public_safe(email: str) -> bool:
    lowered = email.lower()
    return any(lowered.endswith(suffix) for suffix in ALLOWED_PUBLIC_EMAIL_SUFFIXES)


def _changed_paths(commit: str) -> tuple[str, ...]:
    output = _git(["diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit])
    assert isinstance(output, str)
    return tuple(line for line in output.splitlines() if line)


def _blob(commit: str, path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def scan_commit(commit: str) -> tuple[BoundaryIssue, ...]:
    issues: list[BoundaryIssue] = []

    author_email, committer_email = _commit_emails(commit)
    for role, email in (("AUTHOR", author_email), ("COMMITTER", committer_email)):
        if not _email_is_public_safe(email):
            issues.append(BoundaryIssue(
                f"commit:{commit}",
                f"PUBLIC_{role}_EMAIL",
                f"{role.lower()} email must use a GitHub noreply address",
            ))

    for path_text in _changed_paths(commit):
        path = PurePosixPath(path_text)
        if any(part.lower() in FORBIDDEN_DIRS for part in path.parts[:-1]):
            issues.append(BoundaryIssue(path_text, "FORBIDDEN_DIRECTORY_HISTORY", "prohibited directory appeared in commit history"))

        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            issues.append(BoundaryIssue(path_text, "FORBIDDEN_FILE_TYPE_HISTORY", f"{path.suffix.lower()} payload appeared in commit history"))
            continue

        blob = _blob(commit, path_text)
        if blob is None:
            continue
        if len(blob) > MAX_TEXT_BYTES:
            issues.append(BoundaryIssue(path_text, "UNSCANNABLE_HISTORY_FILE", "historical file exceeds text scan limit"))
            continue
        try:
            text_content = blob.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(BoundaryIssue(path_text, "UNSCANNABLE_HISTORY_FILE", "historical file is not UTF-8 text"))
            continue
        if "\x00" in text_content:
            issues.append(BoundaryIssue(path_text, "UNSCANNABLE_HISTORY_FILE", "historical file contains binary NUL data"))
            continue
        issues.extend(scan_text(path_text, text_content))

    return tuple(issues)


def scan_range(base_sha: str, head_sha: str) -> tuple[BoundaryIssue, ...]:
    issues: list[BoundaryIssue] = []
    for commit in _commit_list(base_sha, head_sha):
        issues.extend(scan_commit(commit))
    return tuple(issues)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: check_git_history_boundary.py BASE_SHA HEAD_SHA")
        return 2

    issues = scan_range(args[0], args[1])
    if not issues:
        print("GIT_HISTORY_BOUNDARY_PASS")
        return 0

    print("GIT_HISTORY_BOUNDARY_FAIL")
    for issue in issues:
        print(f"{issue.path}: {issue.code}: {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
