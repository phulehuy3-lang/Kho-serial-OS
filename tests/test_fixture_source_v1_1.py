"""New synthetic registration preserves the predecessor and authority locks."""
import json
import hashlib
from pathlib import Path
import unittest

class FixtureRegistrationTests(unittest.TestCase):
    def test_predecessor_and_new_generation_are_separate(self):
        rules = Path(__file__).resolve().parents[1] / "rules"
        old = json.loads((rules / "OS_SHARED_ISOLATED_FIXTURE_SOURCE_V1.json").read_text())
        new = json.loads((rules / "OS_SHARED_ISOLATED_FIXTURE_SOURCE_V1_1.json").read_text())
        self.assertEqual(old["artifact_sha256"], "de0f5958f02c510230c8570fb203dff30948c893e9642f3a32aeb4616e20272d")
        self.assertEqual(new["predecessor_fixture_id"], old["fixture_id"])
        self.assertNotEqual(new["fixture_id"], old["fixture_id"])
        self.assertNotEqual(new["artifact_sha256"], old["artifact_sha256"])
        self.assertNotEqual(new["native_fixture_id"], new["fixture_id"])
        self.assertEqual(new["workbook_sheet_count"], 13)
        self.assertEqual(new["native_formula_contract"]["query_text"], "select A,B,C,D,E,F")
        for field in ["provider_atomicity_proven", "domain_completeness_proven", "operational_acceptance", "live_read_authorized", "executable_acquisition_authorized", "production_write_authorized"]:
            self.assertIs(new[field], False)

    def test_contract_hash_and_authority_locks(self):
        rules = Path(__file__).resolve().parents[1] / "rules"
        registry = json.loads((rules / "OS_SHARED_ISOLATED_FIXTURE_SOURCE_V1_1.json").read_text())
        contract = json.loads((rules / "NATIVE_CAPTURE_LAB_CONTRACT_V0_1.json").read_text())
        digest = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(registry["native_capture_contract_sha256"], digest)
        self.assertEqual(registry["native_capture_contract_id"], contract["contract_id"])
        self.assertEqual(contract["authority_status"], "LAB_ONLY_NOT_PRODUCTION_AUTHORITY")
        for field in ["provider_atomicity_proven", "domain_completeness_proven", "live_read_authorized", "executable_acquisition_authorized", "production_write_authorized"]:
            self.assertIs(contract[field], False)
