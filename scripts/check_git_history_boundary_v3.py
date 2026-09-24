"""Additive V3 Git-history public-boundary scanner.

V3 preserves the frozen V1/V2 policy and strengthens changed-path/blob
acquisition: NUL-delimited path parsing, blob reads by object ID, and explicit
separation of deletion from blob-read failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import sys

try:
    from scripts.check_git_history_boundary import ZERO_SHA, _git
    from scripts.check_repo_boundary import (
        FORBIDDEN_DIRS,
        FORBIDDEN_SUFFIXES,
        MAX_TEXT_BYTES,
        BoundaryIssue,
        scan_text,
    )
except ModuleNotFoundError:
    from check_git_history_boundary import ZERO_SHA, _git
    from check_repo_boundary import (
        FORBIDDEN_DIRS,
        FORBIDDEN_SUFFIXES,
        MAX_TEXT_BYTES,
        BoundaryIssue,
        scan_text,
    )


@dataclass(frozen=True, slots=True)
class RawDiffEntry:
    path: str
    object_id: str | None
    deleted: bool


def _decode_path(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Git path is not UTF-8") from exc


def parse_raw_diff_z(data: bytes) -> tuple[RawDiffEntry, ...]:
    """Parse `git diff-tree --raw -z` without line-based path splitting."""

    if type(data) is not bytes:
        raise RuntimeError("raw diff payload must be bytes")

    fields = data.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()

    entries: list[RawDiffEntry] = []
    index = 0
    while index < len(fields):
        header_bytes = fields[index]
        index += 1
        try:
            header = header_bytes.decode("ascii")
        except UnicodeDecodeError as exc:
            raise RuntimeError("malformed non-ASCII raw diff header") from exc

        parts = header.split(" ")
        if len(parts) != 5 or not parts[0].startswith(":"):
            raise RuntimeError(f"malformed raw diff header: {header!r}")

        _old_mode, _new_mode, _old_oid, new_oid, status = (
            parts[0][1:],
            parts[1],
            parts[2],
            parts[3],
            parts[4],
        )

        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(fields):
            raise RuntimeError("raw diff path payload truncated")

        raw_paths = fields[index : index + path_count]
        index += path_count
        paths = tuple(_decode_path(value) for value in raw_paths)
        path = paths[-1]

        deleted = status.startswith("D") or not new_oid.strip("0")
        entries.append(
            RawDiffEntry(
                path=path,
                object_id=None if deleted else new_oid,
                deleted=deleted,
            )
        )

    return tuple(entries)


def _commit_list_v3(base_sha: str, head_sha: str) -> tuple[str, ...]:
    if base_sha == ZERO_SHA:
        output = _git(["rev-list", "--reverse", head_sha])
    else:
        output = _git(["rev-list", "--reverse", f"{base_sha}..{head_sha}"])
    if type(output) is not str:
        raise RuntimeError("unexpected rev-list payload type")
    return tuple(line for line in output.splitlines() if line)


def _changed_entries(commit: str) -> tuple[RawDiffEntry, ...]:
    output = _git(
        [
            "diff-tree",
            "--no-commit-id",
            "--raw",
            "-r",
            "-z",
            "-M",
            "--root",
            commit,
        ],
        text=False,
    )
    if type(output) is not bytes:
        raise RuntimeError("unexpected raw diff payload type")
    return parse_raw_diff_z(output)


def _blob_by_object_id(object_id: str) -> bytes:
    output = _git(["cat-file", "blob", object_id], text=False)
    if type(output) is not bytes:
        raise RuntimeError("unexpected blob payload type")
    return output


def _scan_blob(path_text: str, blob: bytes) -> tuple[BoundaryIssue, ...]:
    path = PurePosixPath(path_text)
    issues: list[BoundaryIssue] = []

    if any(part.lower() in FORBIDDEN_DIRS for part in path.parts[:-1]):
        issues.append(
            BoundaryIssue(
                path_text,
                "FORBIDDEN_DIRECTORY_HISTORY_V3",
                "prohibited directory appeared in commit history",
            )
        )

    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        issues.append(
            BoundaryIssue(
                path_text,
                "FORBIDDEN_FILE_TYPE_HISTORY_V3",
                f"{path.suffix.lower()} payload appeared in commit history",
            )
        )
        return tuple(issues)

    if len(blob) > MAX_TEXT_BYTES:
        issues.append(
            BoundaryIssue(
                path_text,
                "UNSCANNABLE_HISTORY_FILE_V3",
                "historical file exceeds text scan limit",
            )
        )
        return tuple(issues)

    try:
        text_content = blob.decode("utf-8")
    except UnicodeDecodeError:
        issues.append(
            BoundaryIssue(
                path_text,
                "UNSCANNABLE_HISTORY_FILE_V3",
                "historical file is not UTF-8 text",
            )
        )
        return tuple(issues)

    if "\x00" in text_content:
        issues.append(
            BoundaryIssue(
                path_text,
                "UNSCANNABLE_HISTORY_FILE_V3",
                "historical file contains binary NUL data",
            )
        )
        return tuple(issues)

    issues.extend(scan_text(path_text, text_content))
    return tuple(issues)


def scan_commit_v3(commit: str) -> tuple[BoundaryIssue, ...]:
    issues: list[BoundaryIssue] = []
    for entry in _changed_entries(commit):
        if entry.deleted:
            continue
        if entry.object_id is None:
            raise RuntimeError(
                f"non-deleted path has no blob object ID: {entry.path!r}"
            )
        blob = _blob_by_object_id(entry.object_id)
        issues.extend(_scan_blob(entry.path, blob))
    return tuple(issues)


def scan_range_v3(base_sha: str, head_sha: str) -> tuple[BoundaryIssue, ...]:
    issues: list[BoundaryIssue] = []
    for commit in _commit_list_v3(base_sha, head_sha):
        issues.extend(scan_commit_v3(commit))
    return tuple(issues)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: check_git_history_boundary_v3.py BASE_SHA HEAD_SHA")
        return 2

    issues = scan_range_v3(args[0], args[1])
    if not issues:
        print("GIT_HISTORY_BOUNDARY_V3_PASS")
        return 0

    print("GIT_HISTORY_BOUNDARY_V3_FAIL")
    for issue in issues:
        print(f"{issue.path}: {issue.code}: {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
