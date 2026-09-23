from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.check_static_quality import scan_static_quality


class StaticQualityTests(unittest.TestCase):
    def _scan(self, relative: str, content: str):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return scan_static_quality(root)

    def test_requests_import_is_blocked(self) -> None:
        issues = self._scan("scripts/bad.py", "import requests\n")
        self.assertTrue(any(x.code == "FORBIDDEN_NETWORK_IMPORT" for x in issues))

    def test_subprocess_is_blocked_outside_history_scanner(self) -> None:
        issues = self._scan("scripts/bad.py", "import subprocess\nsubprocess.run(['git','status'])\n")
        self.assertTrue(any(x.code.startswith("FORBIDDEN_SUBPROCESS") for x in issues))

    def test_file_write_is_blocked(self) -> None:
        issues = self._scan("scripts/bad.py", "from pathlib import Path\nPath('x').write_text('x')\n")
        self.assertTrue(any(x.code == "FORBIDDEN_FILE_WRITE" for x in issues))


if __name__ == "__main__":
    unittest.main()
