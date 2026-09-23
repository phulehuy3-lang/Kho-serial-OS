from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.check_repo_boundary import scan_repository


class RepositoryBoundaryTests(unittest.TestCase):
    def _scan(self, relative: str, content: str):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return scan_repository(root)

    def test_labeled_serial_in_tests_is_not_exempt(self) -> None:
        label = "ser" + "ial"
        value = "1234567" + "89012345"
        issues = self._scan("tests/test_bad.py", f'{label} = "{value}"\n')
        self.assertTrue(any(x.code == "LABELED_PRODUCTION_IDENTIFIER" for x in issues))

    def test_google_sheet_url_is_blocked(self) -> None:
        prefix = "https://docs.google.com/spread" + "sheets/d/"
        issues = self._scan("README.md", prefix + "A" * 25)
        self.assertTrue(any(x.code == "GOOGLE_SHEETS_URL" for x in issues))

    def test_personal_email_is_blocked(self) -> None:
        email = "person" + "@" + "example.com"
        issues = self._scan("docs/note.md", "contact = " + email)
        self.assertTrue(any(x.code == "PUBLIC_PERSONAL_EMAIL" for x in issues))

    def test_github_user_noreply_email_is_allowed(self) -> None:
        email = "12345+synthetic" + "@" + "users.noreply.github.com"
        issues = self._scan("docs/note.md", email)
        self.assertFalse(any(x.code == "PUBLIC_PERSONAL_EMAIL" for x in issues))

    def test_github_webflow_committer_email_is_allowed(self) -> None:
        email = "noreply" + "@" + "github.com"
        issues = self._scan("docs/note.md", email)
        self.assertFalse(any(x.code == "PUBLIC_PERSONAL_EMAIL" for x in issues))


if __name__ == "__main__":
    unittest.main()
