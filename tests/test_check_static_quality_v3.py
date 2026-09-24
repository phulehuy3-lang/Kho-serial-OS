from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.check_static_quality_v3 import scan_static_quality_v3


class StaticQualityV3Tests(unittest.TestCase):
    def scan(self, source: str):
        with tempfile.TemporaryDirectory(prefix="kso-v3-static-") as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "synthetic_probe.py").write_text(
                source, encoding="utf-8"
            )
            return scan_static_quality_v3(root)

    def test_path_open_positional_write_mode_is_rejected_as_inert_text(self):
        source = 'from pathlib import Path\nPath("synthetic.txt").open("w")\n'
        issues = self.scan(source)
        self.assertTrue(any(i.code == "V3_FORBIDDEN_POSITIONAL_OPEN_WRITE" for i in issues))

    def test_simple_write_method_alias_is_rejected_as_inert_text(self):
        source = (
            'from pathlib import Path\n'
            'writer = Path("synthetic.txt").write_text\n'
            'writer("synthetic")\n'
        )
        issues = self.scan(source)
        self.assertTrue(any(i.code == "V3_FORBIDDEN_WRITE_ALIAS" for i in issues))

    def test_read_method_alias_is_not_a_write_alias(self):
        source = (
            'from pathlib import Path\n'
            'reader = Path("synthetic.txt").read_text\n'
            'reader()\n'
        )
        self.assertEqual(scan_static_quality_v3_from_source(source), ())


def scan_static_quality_v3_from_source(source: str):
    with tempfile.TemporaryDirectory(prefix="kso-v3-static-safe-") as tmp:
        root = Path(tmp)
        (root / "scripts").mkdir()
        (root / "scripts" / "synthetic_probe.py").write_text(source, encoding="utf-8")
        return scan_static_quality_v3(root)


if __name__ == "__main__":
    unittest.main()
