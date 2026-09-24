from __future__ import annotations

from unittest.mock import patch
import unittest

import scripts.check_git_history_boundary_v3 as v3


ZERO = "0" * 40


def raw(status: str, old_oid: str, new_oid: str, *paths: str) -> bytes:
    header = f":100644 100644 {old_oid} {new_oid} {status}".encode("ascii")
    return b"\0".join((header, *(p.encode("utf-8") for p in paths), b""))


class HistoryBoundaryV3Tests(unittest.TestCase):
    def test_nul_parser_preserves_ascii_vietnamese_newline_and_rename_delete(self):
        oid1 = "1" * 40
        oid2 = "2" * 40
        payload = b"".join((
            raw("A", ZERO, oid1, "rules/ascii.md"),
            raw("A", ZERO, oid1, "rules/kiểm_toán.md"),
            raw("A", ZERO, oid1, "rules/line\nbreak.md"),
            raw("R100", oid1, oid2, "rules/old.md", "rules/new.md"),
            raw("D", oid1, ZERO, "rules/deleted.md"),
        ))
        entries = v3.parse_raw_diff_z(payload)
        self.assertEqual(
            tuple(e.path for e in entries),
            (
                "rules/ascii.md",
                "rules/kiểm_toán.md",
                "rules/line\nbreak.md",
                "rules/new.md",
                "rules/deleted.md",
            ),
        )
        self.assertFalse(entries[3].deleted)
        self.assertTrue(entries[4].deleted)
        self.assertIsNone(entries[4].object_id)

    def test_intermediate_only_payload_is_scanned_by_object_id(self):
        oid = "a" * 40
        bad = ("synthetic" + "@" + "example.com").encode("utf-8")

        def fake_git(args, *, text=True):
            if args[0] == "rev-list":
                return "c1\nc2\n"
            if args[0] == "diff-tree" and args[-1] == "c1":
                return raw("A", ZERO, oid, "rules/kiểm_toán.md")
            if args[0] == "diff-tree" and args[-1] == "c2":
                return raw("D", oid, ZERO, "rules/kiểm_toán.md")
            if args[:2] == ["cat-file", "blob"] and args[2] == oid:
                return bad
            raise AssertionError(args)

        with patch.object(v3, "_git", side_effect=fake_git):
            issues = v3.scan_range_v3("base", "head")
        self.assertTrue(any(i.path == "rules/kiểm_toán.md" for i in issues))

    def test_blob_read_failure_is_not_treated_as_delete(self):
        oid = "b" * 40

        def fake_git(args, *, text=True):
            if args[0] == "rev-list":
                return "c1\n"
            if args[0] == "diff-tree":
                return raw("A", ZERO, oid, "rules/ascii.md")
            if args[:2] == ["cat-file", "blob"]:
                raise RuntimeError("synthetic blob read failure")
            raise AssertionError(args)

        with patch.object(v3, "_git", side_effect=fake_git):
            with self.assertRaisesRegex(RuntimeError, "blob read failure"):
                v3.scan_range_v3("base", "head")


if __name__ == "__main__":
    unittest.main()
