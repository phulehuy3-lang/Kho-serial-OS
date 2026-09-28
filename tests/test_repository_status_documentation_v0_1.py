from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryStatusDocumentationTests(unittest.TestCase):
    def test_current_status_index_exists_and_is_explicit(self):
        status = (ROOT / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        self.assertRegex(status, r"Status snapshot: \d{4}-\d{2}-\d{2}")
        self.assertIn("Verified repository state before this documentation PR", status)
        self.assertIn("Five required checks:", status)
        for check in (
            "unit-tests", "trusted-public-boundary", "trusted-public-boundary-v2",
            "trusted-public-boundary-v3", "trusted-warehouse-serial-scope",
        ):
            self.assertIn(check, status)
        self.assertIn("PR #115 exact head", status)
        self.assertIn("**CLOSED/completed**", status)
        self.assertIn("**OPEN**: partial materialization", status)
        self.assertIn("HOLD_GOOGLE_CLOUD_IAM_EXECUTION_CAPABILITY_UNAVAILABLE", status)
        self.assertIn("Full-history privacy: NOT CLEAN", status)
        self.assertIn("ProductionWriteAuthorized=False", status)
        self.assertNotIn("Issue #96 remains OPEN", status)

    def test_readme_points_to_current_status(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("CURRENT_STATUS.md", readme)

    def test_v2_migration_is_not_still_labeled_staged(self):
        migration = (
            ROOT / "rules" / "TRUSTED_PUBLIC_BOUNDARY_V2_MIGRATION.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn(
            "Status: **STAGED; ENFORCEMENT REQUIRES RULESET READ-BACK**",
            migration,
        )
        self.assertIn("ENFORCED", migration)

    def test_historical_catalog_states_are_labeled_checkpoint(self):
        catalog = (
            ROOT / "rules" / "PUBLIC_CONTROL_CATALOG_V0_1.md"
        ).read_text(encoding="utf-8")
        for stale in (
            "Current authority remains:",
            "Current state remains:",
            "Current public-safe state:",
        ):
            self.assertNotIn(stale, catalog)
        self.assertIn("State at checkpoint:", catalog)

    def test_license_decision_is_proposed_not_silently_selected(self):
        proposal = (
            ROOT / "rules" / "LICENSE_DECISION_PROPOSAL_V0_1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("OWNER DECISION REQUIRED", proposal)
        self.assertIn("MIT", proposal)
        self.assertIn("Apache-2.0", proposal)
        self.assertFalse((ROOT / "LICENSE").exists())
        self.assertFalse((ROOT / "LICENSE.md").exists())


if __name__ == "__main__":
    unittest.main()
