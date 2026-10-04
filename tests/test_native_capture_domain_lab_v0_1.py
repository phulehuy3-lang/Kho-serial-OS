import copy
import unittest
from scripts.native_capture_domain_lab_v0_1 import assess_native_domain_lab,canonical_sha256,CONTRACT_ID
class DomainLabTests(unittest.TestCase):
    def setUp(self):
        text=lambda v:{'userEnteredValue':{'stringValue':v},'effectiveValue':{'stringValue':v}}
        self.m={'contract_id':CONTRACT_ID,'scope':'FINITE_SYNTHETIC_LAB_ONLY','excluded_domain':'EVERYTHING_OUTSIDE_DECLARED_BODY_AND_GUARD_IS_EXCLUDED_FROM_THIS_LAB_CLAIM','surfaces':[{'title':'LAB','body_rows':3,'guard_rows':3,'columns':2,'expected_cells':[[0,0,text('header')],[1,0,text('00001')],[5,0,text('END_R4:LAB')]]}]}
        self.p={'sheets':[{'properties':{'title':'LAB'},'data':[{'rowData':[{'values':[text('header')]},{'values':[text('00001')]},{},{},{},{'values':[text('END_R4:LAB')]}]}]}]}
        self.h=canonical_sha256(self.m)
    def run_model(self,p=None,m=None,h=None):return assess_native_domain_lab(p or self.p,m or self.m,h or self.h)
    def test_finite_model_scope_only(self):
        r=self.run_model();self.assertEqual(r.status,'PASS_SCOPED');self.assertTrue(r.scoped_ready);self.assertFalse(r.ready);self.assertFalse(r.atomic_snapshot_proven);self.assertFalse(r.production_domain_completeness_proven);self.assertEqual(r.capture.bounds[0].rows,3);self.assertTrue(all(e[1]<3 for e in r.capture.entries))
    def test_silent_missing_nonblank_row_rejected_even_with_sentinel(self):
        p=copy.deepcopy(self.p);p['sheets'][0]['data'][0]['rowData'][1]={};self.assertIn('MODEL_MISMATCH',self.run_model(p).blockers[0])
    def test_missing_surface_and_guard_termination_hold(self):
        p={'sheets':[]};self.assertEqual(self.run_model(p).status,'HOLD')
        p=copy.deepcopy(self.p);p['sheets'][0]['data'][0]['rowData']=p['sheets'][0]['data'][0]['rowData'][:3];self.assertIn('SENTINEL',self.run_model(p).blockers[0])
    def test_populated_guard_requires_rebind(self):
        p=copy.deepcopy(self.p);p['sheets'][0]['data'][0]['rowData'][3]={'values':[{'effectiveValue':{'stringValue':'newrecord'}}]};self.assertEqual(self.run_model(p).status,'HOLD_REBIND')
    def test_external_hash_cannot_follow_mutated_model(self):
        m=copy.deepcopy(self.m);m['surfaces'][0]['expected_cells'].pop(1);self.assertIn('HASH_MISMATCH',self.run_model(m=m).blockers[0])
    def test_sentinel_cannot_be_formula_or_caller_boolean(self):
        m=copy.deepcopy(self.m);m['surfaces'][0]['expected_cells'][-1][-1]={'effectiveValue':{'boolValue':True}};self.assertIn('SENTINEL_MODEL',self.run_model(m=m,h=canonical_sha256(m)).blockers[0])
    def test_type_and_leading_zero_parity(self):
        p=copy.deepcopy(self.p);p['sheets'][0]['data'][0]['rowData'][1]['values'][0]={'effectiveValue':{'numberValue':1},'userEnteredValue':{'numberValue':1}};self.assertEqual(self.run_model(p).status,'HOLD')
    def test_outside_guard_response_rejected(self):
        p=copy.deepcopy(self.p);p['sheets'][0]['data'][0]['rowData'].append({'values':[{'effectiveValue':{'stringValue':'overflow'}}]});self.assertEqual(self.run_model(p).status,'HOLD')

    def test_malformed_manifest_and_payload_failclosed(self):
        for bad in (None, [], "bad", 1, True):
            with self.subTest(manifest=bad):
                r=assess_native_domain_lab(self.p,bad,canonical_sha256(bad))
                self.assertEqual(r.status,"HOLD");self.assertFalse(r.ready)
            with self.subTest(payload=bad):
                r=assess_native_domain_lab(bad,self.m,self.h)
                self.assertEqual(r.status,"HOLD");self.assertFalse(r.scoped_ready)
    def test_malformed_expected_hash_failclosed(self):
        for bad in (None, [], 123, "", "0"*63, "g"*64, "A"*64):
            with self.subTest(hash=bad):
                r=assess_native_domain_lab(self.p,self.m,bad)
                self.assertEqual(r.status,"HOLD");self.assertIn("HASH_MISMATCH",r.blockers[0])
    def test_capture_typed_values_and_coordinates_rejected(self):
        variants=[{'effectiveValue':{'numberValue':True}},{'effectiveValue':{'numberValue':float('inf')}},{'effectiveValue':{'stringValue':'a','boolValue':True}},{'userEnteredValue':{'formulaValue':7}}]
        for bad in variants:
            with self.subTest(cell=bad):
                p=copy.deepcopy(self.p);p['sheets'][0]['data'][0]['rowData'][1]['values'][0]=bad
                self.assertEqual(self.run_model(p).status,"HOLD")
        p=copy.deepcopy(self.p);p['sheets'][0]['data'][0]['startColumn']=-1
        self.assertEqual(self.run_model(p).status,"HOLD")
