from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.check_git_history_boundary import _email_is_public_safe, scan_range


class GitHistoryBoundaryTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def test_added_then_deleted_secret_is_still_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._git(root, "init")
            self._git(root, "config", "user.name", "Synthetic Test")
            safe_email = "12345+synthetic" + "@" + "users.noreply.github.com"
            self._git(root, "config", "user.email", safe_email)
            (root / "safe.txt").write_text("safe\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "base")
            base = self._git(root, "rev-parse", "HEAD")

            token = "github_" + "pat_" + "A" * 30
            (root / "leak.txt").write_text(token + "\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "introduce then remove")
            (root / "leak.txt").unlink()
            self._git(root, "add", "-A")
            self._git(root, "commit", "-m", "remove")
            head = self._git(root, "rev-parse", "HEAD")

            old = os.getcwd()
            try:
                os.chdir(root)
                issues = scan_range(base, head)
            finally:
                os.chdir(old)
            self.assertTrue(any(x.code == "GITHUB_TOKEN" for x in issues))

    def test_personal_commit_email_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._git(root, "init")
            self._git(root, "config", "user.name", "Synthetic Test")
            unsafe_email = "person" + "@" + "example.com"
            self._git(root, "config", "user.email", unsafe_email)
            (root / "safe.txt").write_text("safe\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "bad metadata")
            head = self._git(root, "rev-parse", "HEAD")

            old = os.getcwd()
            try:
                os.chdir(root)
                issues = scan_range("0" * 40, head)
            finally:
                os.chdir(old)
            self.assertTrue(any(x.code == "PUBLIC_AUTHOR_EMAIL" for x in issues))

    def test_user_noreply_commit_email_passes_metadata_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._git(root, "init")
            self._git(root, "config", "user.name", "Synthetic Test")
            safe_email = "12345+synthetic" + "@" + "users.noreply.github.com"
            self._git(root, "config", "user.email", safe_email)
            (root / "safe.txt").write_text("safe\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "safe metadata")
            head = self._git(root, "rev-parse", "HEAD")

            old = os.getcwd()
            try:
                os.chdir(root)
                issues = scan_range("0" * 40, head)
            finally:
                os.chdir(old)
            self.assertFalse(any("EMAIL" in x.code for x in issues))

    def test_github_squash_committer_email_is_safe(self) -> None:
        self.assertTrue(_email_is_public_safe("noreply" + "@" + "github.com"))


if __name__ == "__main__":
    unittest.main()
