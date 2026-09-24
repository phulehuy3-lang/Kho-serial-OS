from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryStatusDocumentationTests(unittest.TestCase):
    def test_current_status_index_exists_and_is_explicit(self):
        status = (ROOT / "CURRENT_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("Status date: 2026-09-25", status)
        self.assertIn("Provider state verified directly", status)
        self.assertIn("Documentation state at checkpoint", status)
        self.assertIn("delta-history", status)
        self.assertIn("full-history privacy", status)
        self.assertIn("trusted-public-boundary-v3", status)
        self.assertIn("PARTIAL/HOLD_ENFORCEMENT_NOT_PROVEN", status)
        self.assertIn("Issue #96", status)
        self.assertIn("ProductionWriteAuthorized=False", status)

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
