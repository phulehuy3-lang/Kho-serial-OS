import unittest
from scripts.native_cell_capture_v0_1 import NativeCapture,SurfaceBound,NativeCell
from scripts.native_mutation_lifecycle_lab_v0_1 import assess_native_mutation_lifecycle_lab
class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.c=NativeCapture((SurfaceBound('SYSTEM_INTERVAL_STATE',8,31),),(('SYSTEM_INTERVAL_STATE',7,9,NativeCell(5,'n')),));self.ops=[{'sheet':'SYSTEM_INTERVAL_STATE','row':7,'column':9,'after':{'numberValue':5}}]
    def test_materialized_readback_all_lifecycle_transitions(self):
        r=assess_native_mutation_lifecycle_lab(self.c,self.ops,'TEST_LAB','a'*64);self.assertEqual(r['status'],'CLOSED_LAB');self.assertEqual(len(r['transitions']),4);self.assertFalse(r['ready']);self.assertFalse(r['production_write_authorized'])
    def test_source_value_mismatch_cannot_close(self):
        self.ops[0]['after']={'numberValue':4};self.assertEqual(assess_native_mutation_lifecycle_lab(self.c,self.ops,'TEST_LAB','a'*64)['status'],'HOLD')
    def test_duplicate_fields_cannot_close(self):
        self.assertEqual(assess_native_mutation_lifecycle_lab(self.c,self.ops*2,'TEST_LAB','a'*64)['status'],'HOLD')
    def test_missing_transaction_hash_holds(self):
        self.assertEqual(assess_native_mutation_lifecycle_lab(self.c,self.ops,'TEST_LAB','')['status'],'HOLD')
    def test_outside_capture_or_empty_manifest_holds(self):
        self.ops[0]['row']=8;self.assertEqual(assess_native_mutation_lifecycle_lab(self.c,self.ops,'TEST_LAB','a'*64)['status'],'HOLD');self.assertEqual(assess_native_mutation_lifecycle_lab(self.c,[],'TEST_LAB','a'*64)['status'],'HOLD')
