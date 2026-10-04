"""Pin the finite R4 model without promoting Production authority."""
import unittest,json,hashlib
from pathlib import Path
class R4RegistrationTests(unittest.TestCase):
 def test_contract_generation_and_flags(self):
  rules=Path(__file__).resolve().parents[1]/'rules';r=json.loads((rules/'OS_SHARED_NATIVE_FIXTURE_SOURCE_V1_2_R4.json').read_text());c=json.loads((rules/r['domain_contract_path'].split('/')[-1]).read_text());old=json.loads((rules/'OS_SHARED_ISOLATED_FIXTURE_SOURCE_V1_1.json').read_text())
  self.assertEqual(r['domain_contract_sha256'],hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest());self.assertEqual(r['predecessor_native_fixture_id'],old['native_fixture_id']);self.assertNotEqual(r['fixture_id'],old['native_fixture_id']);self.assertEqual(c['guard_rows'],3);self.assertEqual(r['model_scope'],'FINITE_SYNTHETIC_BODY_PLUS_THREE_GUARD_ROWS_ONLY')
  self.assertEqual(len(r['external_frozen_model_sha256']),64)
  for k in ['provider_atomicity_proven','production_domain_completeness_proven','operational_acceptance','live_read_authorized','executable_acquisition_authorized','production_write_authorized']:self.assertIs(r[k],False)
  self.assertIn('PRESERVE_ORIGINAL',r['historical_results']);self.assertEqual(r['native_locators'],'EXTERNAL_CONFIG_ONLY')
