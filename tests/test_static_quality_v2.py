from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.check_static_quality_v2 import scan_static_quality_v2


class StaticQualityV2Tests(unittest.TestCase):
    def _scan(self, content: str):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            (root / "scripts" / "sample.py").write_text(content, encoding="utf-8")
            return scan_static_quality_v2(root)

    def test_aliased_os_process_paths_are_blocked(self) -> None:
        for content in (
            "import os as alias\nalias.system('true')\n",
            "from os import system as run\nrun('true')\n",
            "import subprocess as process\nprocess.run(['true'])\n",
            "import posix\nposix.system('true')\n",
        ):
            with self.subTest(content=content):
                self.assertTrue(any(issue.code in {"V2_BLOCKED_IMPORT", "V2_IMPORT_NOT_ALLOWED"} for issue in self._scan(content)))

    def test_dynamic_import_and_exec_are_blocked(self) -> None:
        for content in (
            "import importlib\n",
            "__import__('os')\n",
            "exec('pass')\n",
            "getattr(object(), 'danger')\n",
        ):
            with self.subTest(content=content):
                self.assertTrue(bool(self._scan(content)))

    def test_pure_module_is_allowed(self) -> None:
        self.assertEqual(self._scan("from dataclasses import dataclass\n"), ())


if __name__ == "__main__":
    unittest.main()
