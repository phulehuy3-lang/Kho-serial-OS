from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_warehouse_serial_scope_v1 import check_scope


class WarehouseSerialScopeTests(unittest.TestCase):
    def _fixture(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for folder in ("rules", "scripts", "tests", ".github/workflows"):
            (root / folder).mkdir(parents=True, exist_ok=True)
        (root / "rules" / "WAREHOUSE_SERIAL_REPOSITORY_SCOPE_V1.md").write_text("scope", encoding="utf-8")
        (root / "scripts" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
        return temp, root

    def _write_manifest(self, root: Path, paths):
        payload = {
            "schema_id": "WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1",
            "mission": "WAREHOUSE_SERIAL_ONLY",
            "artifacts": [
                {
                    "path": path,
                    "capabilities": ["REPOSITORY_SAFETY"],
                    "rationale": "Synthetic warehouse-serial scope fixture.",
                }
                for path in paths
            ],
        }
        manifest = root / "rules" / "WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json"
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        return manifest

    def test_exact_set_passes(self):
        temp, root = self._fixture()
        try:
            paths = {
                "rules/WAREHOUSE_SERIAL_REPOSITORY_SCOPE_V1.md",
                "rules/WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json",
                "scripts/sample.py",
            }
            self._write_manifest(root, paths)
            self.assertEqual(check_scope(root), ())
        finally:
            temp.cleanup()

    def test_undeclared_artifact_fails(self):
        temp, root = self._fixture()
        try:
            paths = {
                "rules/WAREHOUSE_SERIAL_REPOSITORY_SCOPE_V1.md",
                "rules/WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json",
                "scripts/sample.py",
            }
            self._write_manifest(root, paths)
            (root / "rules" / "unrelated.md").write_text("x", encoding="utf-8")
            self.assertTrue(any(x.startswith("UNDECLARED_ARTIFACT:") for x in check_scope(root)))
        finally:
            temp.cleanup()

    def test_stale_manifest_entry_fails(self):
        temp, root = self._fixture()
        try:
            paths = {
                "rules/WAREHOUSE_SERIAL_REPOSITORY_SCOPE_V1.md",
                "rules/WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json",
                "scripts/sample.py",
                "scripts/missing.py",
            }
            self._write_manifest(root, paths)
            self.assertIn("STALE_MANIFEST_ENTRY:scripts/missing.py", check_scope(root))
        finally:
            temp.cleanup()

    def test_unknown_capability_and_blank_rationale_fail(self):
        temp, root = self._fixture()
        try:
            manifest = self._write_manifest(
                root,
                {
                    "rules/WAREHOUSE_SERIAL_REPOSITORY_SCOPE_V1.md",
                    "rules/WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json",
                    "scripts/sample.py",
                },
            )
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["artifacts"][0]["capabilities"] = ["FINANCE"]
            payload["artifacts"][0]["rationale"] = " "
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            errors = check_scope(root)
            self.assertTrue(any(x.startswith("CAPABILITY_UNKNOWN:") for x in errors))
            self.assertTrue(any(x.startswith("RATIONALE_MISSING:") for x in errors))
        finally:
            temp.cleanup()

    def test_mission_drift_fails(self):
        temp, root = self._fixture()
        try:
            manifest = self._write_manifest(
                root,
                {
                    "rules/WAREHOUSE_SERIAL_REPOSITORY_SCOPE_V1.md",
                    "rules/WAREHOUSE_SERIAL_SCOPE_MANIFEST_V1.json",
                    "scripts/sample.py",
                },
            )
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["mission"] = "GENERAL_CONTROL_FRAMEWORK"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIn("MISSION_INVALID", check_scope(root))
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
