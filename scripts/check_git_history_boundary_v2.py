"""V2 history policy: preserve V1 and reject transient linked Git objects."""

from __future__ import annotations

import sys

try:
    from scripts.check_git_history_boundary import _commit_list, _git, scan_range
    from scripts.check_repo_boundary import BoundaryIssue
except ModuleNotFoundError:
    from check_git_history_boundary import _commit_list, _git, scan_range
    from check_repo_boundary import BoundaryIssue


def scan_range_v2(base_sha: str, head_sha: str) -> tuple[BoundaryIssue, ...]:
    issues = list(scan_range(base_sha, head_sha))
    for commit in _commit_list(base_sha, head_sha):
        output = _git(["ls-tree", "-rz", "--full-tree", commit])
        assert isinstance(output, str)
        for entry in output.split("\0"):
            if not entry:
                continue
            header, separator, path = entry.partition("\t")
            fields = header.split(" ")
            if not separator or len(fields) != 3:
                issues.append(BoundaryIssue(f"commit:{commit}", "GIT_TREE_UNSCANNABLE", "malformed tree entry"))
                continue
            mode, kind, _object_id = fields
            if mode == "120000" or kind == "commit":
                issues.append(BoundaryIssue(path, "LINKED_OBJECT_HISTORY", f"linked object in commit {commit}"))
    return tuple(issues)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: check_git_history_boundary_v2.py BASE_SHA HEAD_SHA")
        return 2
    issues = scan_range_v2(args[0], args[1])
    if not issues:
        print("GIT_HISTORY_BOUNDARY_V2_PASS")
        return 0
    print("GIT_HISTORY_BOUNDARY_V2_FAIL")
    for issue in issues:
        print(f"{issue.path}: {issue.code}: {issue.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
