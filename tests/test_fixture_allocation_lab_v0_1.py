import unittest
from dataclasses import dataclass
from datetime import date
import scripts,pathlib
scripts.__path__.append(str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from scripts.native_cell_capture_v0_1 import NativeCapture,NativeCell,SurfaceBound
from scripts.fixture_allocation_lab_v0_1 import AllocationLabProfile,assess_fixture_allocation_lab
@dataclass
class Bound:
    title:str='SYSTEM_INTERVAL_STATE'
    rows:int=5
    columns:int=31
@dataclass
class Cell:
    value:object
class Capture:
    def __init__(self):
        self.bounds=(Bound(),);self.cells={}
        h={0:'IntervalID',2:'Carrier',3:'Denomination',9:'AvailableQty',10:'AvailableStart',11:'AvailableEnd',13:'HoldFlag',18:'SourceRow',19:'SourceDate',29:'YearGateEligible'}
        for c,v in h.items():self.cells[0,c]=v
        for r,(i,q,lo,hi,day,srow) in enumerate([('TEST_A',10,'000100','000109',46266,1),('TEST_B',5,'000200','000204',46267,2),('TEST_LONG',2,'900719925474099300','900719925474099301',46271,6),('LAB_IN',5,'000900','000904',46299,7)],1):
            for c,v in {0:i,2:'TEST_CARRIER',3:20000,9:q,10:lo,11:hi,13:False,18:srow,19:day,29:True}.items():self.cells[r,c]=v
    def native(self):
        entries=[('SYSTEM_INTERVAL_STATE',r,c,NativeCell(v,'b' if type(v)is bool else 'n' if type(v)in(int,float) else 'str')) for (r,c),v in self.cells.items()]
        for c,v in {0:'HoldID',1:'ScopeType',2:'TargetID',9:'Status'}.items():entries.append(('SYSTEM_HOLD_REGISTRY',0,c,NativeCell(v,'str')))
        return NativeCapture((SurfaceBound('SYSTEM_INTERVAL_STATE',5,31),SurfaceBound('SYSTEM_HOLD_REGISTRY',3,10)),tuple(entries))
class Test(unittest.TestCase):
    def profile(self,q=8):return AllocationLabProfile(('TEST_A','TEST_B','TEST_LONG','LAB_IN'),date(2026,10,4),q)
    def test_rank_and_lexical(self):
        r=assess_fixture_allocation_lab(Capture().native(),self.profile())
        self.assertEqual(r.status,'PASS_LAB');self.assertEqual([(x.source_id,x.quantity) for x in r.allocations],[('LAB_IN',5),('TEST_LONG',2),('TEST_B',1)])
        self.assertEqual(r.allocations[1].serial_end,'900719925474099301');self.assertFalse(r.production_write_authorized)
    def test_future(self):
        c=Capture();c.cells[4,19]=46300;self.assertEqual(assess_fixture_allocation_lab(c.native(),self.profile()).blocking_reasons,('FUTURE_SOURCE_DATE',))
    def test_duplicate(self):
        c=Capture();c.cells[4,0]='TEST_A';self.assertEqual(assess_fixture_allocation_lab(c.native(),self.profile()).blocking_reasons,('DUPLICATE_OR_INVALID_SOURCE',))
    def test_insufficient(self):self.assertEqual(assess_fixture_allocation_lab(Capture().native(),self.profile(23)).blocking_reasons,('INSUFFICIENT_QUANTITY',))
    def test_numeric_serial(self):
        c=Capture();c.cells[4,10]=900;self.assertEqual(assess_fixture_allocation_lab(c.native(),self.profile()).blocking_reasons,('SERIAL_TEXT_INVALID',))
    def test_frozen_set(self):
        c=Capture();c.cells[4,13]=True;self.assertEqual(assess_fixture_allocation_lab(c.native(),self.profile()).blocking_reasons,('FROZEN_SOURCE_SET_MISMATCH',))
    def holdcapture(self,scope='INTERVAL',state='ACTIVE',target='LAB_IN'):
        cap=Capture().native();entries=cap.entries+tuple(('SYSTEM_HOLD_REGISTRY',1,col,NativeCell(v,'str')) for col,v in {0:'H1',1:scope,2:target,9:state}.items())
        return NativeCapture(cap.bounds,entries)
    def test_active_hold_conflict(self):self.assertEqual(assess_fixture_allocation_lab(self.holdcapture(),self.profile()).blocking_reasons,('ACTIVE_HOLD_ELIGIBLE_CONFLICT',))
    def test_unrelated_hold(self):self.assertEqual(assess_fixture_allocation_lab(self.holdcapture(target='OTHER'),self.profile()).status,'PASS_LAB')
    def test_unknown_scope_even_released(self):self.assertEqual(assess_fixture_allocation_lab(self.holdcapture(scope='UNKNOWN',state='RELEASED'),self.profile()).blocking_reasons,('HOLD_REGISTRY_SCOPE_STATE_UNSUPPORTED',))
    def test_unknown_state(self):self.assertEqual(assess_fixture_allocation_lab(self.holdcapture(state='MAYBE'),self.profile()).blocking_reasons,('HOLD_REGISTRY_SCOPE_STATE_UNSUPPORTED',))
    def test_overlap(self):
        c=Capture();c.cells[4,10]='000100';c.cells[4,11]='000104';self.assertEqual(assess_fixture_allocation_lab(c.native(),self.profile()).blocking_reasons,('ELIGIBLE_SERIAL_OVERLAP',))
    def test_nan_date(self):
        c=Capture();c.cells[4,19]=float('nan');self.assertEqual(assess_fixture_allocation_lab(c.native(),self.profile()).blocking_reasons,('SOURCE_CELL_KIND_VALUE_MISMATCH',))
    def test_wrong_capture(self):self.assertEqual(assess_fixture_allocation_lab({},self.profile()).blocking_reasons,('CAPTURE_TYPE_INVALID',))
    def test_malformed_native(self):self.assertEqual(assess_fixture_allocation_lab(NativeCapture(None,None),self.profile()).status,'HOLD')
    def test_duplicate_cells(self):
        cap=Capture().native();self.assertEqual(assess_fixture_allocation_lab(NativeCapture(cap.bounds,cap.entries+(cap.entries[0],)),self.profile()).blocking_reasons,('CAPTURE_DUPLICATE_CELL',))
    def test_profile_float_denomination(self):
        from dataclasses import replace
        self.assertEqual(assess_fixture_allocation_lab(Capture().native(),replace(self.profile(),denomination=20000.0)).blocking_reasons,('CATEGORY_MAPPING_UNBOUND',))
    def test_source_float_denomination(self):
        c=Capture();c.cells[4,3]=20000.0;self.assertEqual(assess_fixture_allocation_lab(c.native(),self.profile()).blocking_reasons,('CATEGORY_MAPPING_MISMATCH',))
    def test_padded_source_id(self):
        c=Capture();c.cells[4,0]=' LAB_IN ';self.assertEqual(assess_fixture_allocation_lab(c.native(),self.profile()).blocking_reasons,('DUPLICATE_OR_INVALID_SOURCE',))
    def test_kind_disagreement(self):
        cap=Capture().native();entries=tuple((n,r,c,NativeCell(v.value,'b') if (r,c)==(4,3) and n=='SYSTEM_INTERVAL_STATE' else v) for n,r,c,v in cap.entries)
        self.assertEqual(assess_fixture_allocation_lab(NativeCapture(cap.bounds,entries),self.profile()).blocking_reasons,('SOURCE_CELL_KIND_VALUE_MISMATCH',))
    def test_source_literal_formula(self):
        cap=Capture().native();entries=tuple((n,r,c,NativeCell(v.value,v.kind,'=1') if (r,c)==(4,3) and n=='SYSTEM_INTERVAL_STATE' else v) for n,r,c,v in cap.entries)
        self.assertEqual(assess_fixture_allocation_lab(NativeCapture(cap.bounds,entries),self.profile()).blocking_reasons,('SOURCE_LITERAL_FORMULA_UNSUPPORTED',))
if __name__=='__main__':unittest.main()
