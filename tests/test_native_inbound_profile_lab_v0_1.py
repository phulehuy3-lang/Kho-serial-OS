import unittest
from scripts.native_cell_capture_v0_1 import NativeCapture,SurfaceBound,NativeCell
from scripts.native_inbound_profile_lab_v0_1 import assess_native_inbound_profile_lab
class InboundPipelineTests(unittest.TestCase):
    def capture(self,*,overlap=False,held=False,formula=None,changed=False):
        entries=[];source=['TEST_TASK','TEST_SCOPE','TEST_CAPTURE','000900','000904',5]
        if changed:source[2]='OTHER_CAPTURE'
        for sheet in('V2_SOURCE','V2_DERIVED'):
            for c,v in enumerate(source):entries.append((sheet,1,c,NativeCell(v,'n'if type(v)is int else'str', (formula or '=QUERY(V2_SOURCE!A2:F2;"select A,B,C,D,E,F";0)')if sheet=='V2_DERIVED'and c==0 else None)))
        for c,v in enumerate(['TEST_OLD','TEST20','000900'if overlap else'000100','000904'if overlap else'000109']):entries.append(('V2_ACTIVE',1,c,NativeCell(v,'str')))
        for c,v in enumerate(['TEST_HOLD','TEST20','000900'if held else'000300','000904'if held else'000302',True,'ACTIVE']):entries.append(('V2_HOLD',1,c,NativeCell(v,'b'if type(v)is bool else'str')))
        return NativeCapture(tuple(SurfaceBound(n,2,c)for n,c in [('V2_SOURCE',6),('V2_DERIVED',6),('V2_ACTIVE',4),('V2_HOLD',6)]),tuple(entries))
    def test_seven_actual_producers_ready_lab_only(self):
        r=assess_native_inbound_profile_lab(self.capture(),self.capture());self.assertEqual(r['status'],'INBOUND_CONTROL_READY');self.assertFalse(r['ready']);self.assertFalse(r['production_write_authorized']);self.assertEqual(len(r['producer_outcomes']),7)
    def test_existing_active_overlap_holds(self):self.assertEqual(assess_native_inbound_profile_lab(self.capture(overlap=True),self.capture())['status'],'HOLD')
    def test_active_hold_overlap_holds(self):self.assertEqual(assess_native_inbound_profile_lab(self.capture(held=True),self.capture())['status'],'HOLD')
    def test_query_star_semantics_remain_hold(self):self.assertEqual(assess_native_inbound_profile_lab(self.capture(),self.capture(formula='=QUERY(V2_SOURCE!A2:F2;"select *";0)'))['status'],'HOLD')
    def test_changed_source_intent_readback_holds(self):self.assertEqual(assess_native_inbound_profile_lab(self.capture(),self.capture(changed=True))['status'],'HOLD')
    def test_untyped_capture_holds(self):self.assertEqual(assess_native_inbound_profile_lab({},self.capture())['status'],'HOLD')
