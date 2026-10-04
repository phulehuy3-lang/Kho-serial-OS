"""Pure G04-R4 fixture allocation; no I/O, write, provider or owner authority.

Reads an already decoded bounded NativeCapture. The frozen permitted set and
TEST20 category mapping are synthetic lab assumptions, not production approval.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date,timedelta
from scripts.native_cell_capture_v0_1 import NativeCapture,NativeCell,SurfaceBound,CaptureRejected

PROFILE_ID='OS_SHARED_FIXTURE_ALLOCATION_LAB_R4'
SERIAL_MAX_DIGITS=4096

@dataclass(frozen=True)
class AllocationLabProfile:
    permitted_source_ids: tuple[str,...]
    target_date: date
    requested_qty: int
    category: str='TEST20'
    carrier: str='TEST_CARRIER'
    denomination: int=20000
    profile_id: str=PROFILE_ID

@dataclass(frozen=True)
class LabAllocation:
    source_id: str
    rank: int
    quantity: int
    serial_start: str
    serial_end: str

@dataclass(frozen=True)
class AllocationLabResult:
    status: str
    allocations: tuple[LabAllocation,...]
    ranked_source_ids: tuple[str,...]
    blocking_reasons: tuple[str,...]
    profile_id: str=PROFILE_ID
    production_write_authorized: bool=False
    operational_acceptance: bool=False
    provider_proof_verified: bool=False

def _serial(value: object) -> bool:
    return type(value) is str and 0<len(value)<=SERIAL_MAX_DIGITS and all('0'<=c<='9' for c in value)

def _number_order(value: str) -> tuple[int,str]:
    significant=value.lstrip('0') or '0'
    return len(significant),significant

def _text_add(value: str,amount: int) -> str:
    # Arithmetic on a serial projection; lexical source identity stays unchanged.
    # Python int conversion limit is avoided by elementary decimal addition.
    digits=list(value);carry=amount
    for i in range(len(digits)-1,-1,-1):
        carry,n=divmod(int(digits[i])+carry,10);digits[i]=str(n)
    return (str(carry) if carry else '')+''.join(digits)

def _distance(lo: str,hi: str) -> int:
    # Bound is deliberately stricter here: fixture inputs <= 128 digits.
    if len(lo)>128 or len(hi)>128:raise ValueError('SERIAL_FIXTURE_BOUND')
    return int(hi)-int(lo)+1

def _assess_fixture_allocation_lab(capture: object,profile: AllocationLabProfile) -> AllocationLabResult:
    def hold(reason: str) -> AllocationLabResult:return AllocationLabResult('HOLD',(),(),(reason,))
    if type(profile) is not AllocationLabProfile or profile.profile_id!=PROFILE_ID:return hold('PROFILE_INVALID')
    if (type(profile.target_date) is not date or type(profile.requested_qty) is not int or profile.requested_qty<=0 or type(profile.permitted_source_ids) is not tuple or not profile.permitted_source_ids or any(type(x)is not str or not x or x!=x.strip() for x in profile.permitted_source_ids) or len(set(profile.permitted_source_ids))!=len(profile.permitted_source_ids)):return hold('PROFILE_INVALID')
    if type(profile.category)is not str or type(profile.carrier)is not str or type(profile.denomination)is not int or (profile.category,profile.carrier,profile.denomination)!=('TEST20','TEST_CARRIER',20000):return hold('CATEGORY_MAPPING_UNBOUND')
    if type(capture) is not NativeCapture:return hold('CAPTURE_TYPE_INVALID')
    if type(capture.bounds)is not tuple or type(capture.entries)is not tuple or any(type(x)is not SurfaceBound or type(x.title)is not str or type(x.rows)is not int or type(x.columns)is not int or x.rows<=0 or x.columns<=0 for x in capture.bounds):return hold('CAPTURE_SHAPE_INVALID')
    if len({x.title for x in capture.bounds})!=len(capture.bounds):return hold('CAPTURE_SHAPE_INVALID')
    positions=set()
    for entry in capture.entries:
        if type(entry)is not tuple or len(entry)!=4:return hold('CAPTURE_SHAPE_INVALID')
        title,row,col,cell=entry
        bnd=next((x for x in capture.bounds if x.title==title),None)
        if bnd is None or type(row)is not int or type(col)is not int or not(0<=row<bnd.rows and 0<=col<bnd.columns) or type(cell)is not NativeCell:return hold('CAPTURE_SHAPE_INVALID')
        if title in ('SYSTEM_INTERVAL_STATE','SYSTEM_HOLD_REGISTRY'):
            if cell.formula is not None:return hold('SOURCE_LITERAL_FORMULA_UNSUPPORTED')
            coherent=(cell.kind=='missing' and cell.value is None) or (cell.kind in ('str','s','inlineStr') and type(cell.value)is str) or (cell.kind=='b' and type(cell.value)is bool) or (cell.kind=='n' and type(cell.value)in(int,float) and (type(cell.value)is int or cell.value==cell.value and cell.value not in (float('inf'),-float('inf'))))
            if not coherent:return hold('SOURCE_CELL_KIND_VALUE_MISMATCH')
        if (title,row,col) in positions:return hold('CAPTURE_DUPLICATE_CELL')
        positions.add((title,row,col))
    bound=next((x for x in capture.bounds if x.title=='SYSTEM_INTERVAL_STATE'),None)
    if bound is None or bound.columns<31:return hold('SOURCE_BOUND_MISSING')
    headers={0:'IntervalID',2:'Carrier',3:'Denomination',9:'AvailableQty',10:'AvailableStart',11:'AvailableEnd',13:'HoldFlag',18:'SourceRow',19:'SourceDate',29:'YearGateEligible'}
    if any(capture.cell(bound.title,0,c).value!=v for c,v in headers.items()):return hold('SOURCE_HEADER_MISMATCH')
    eligible=[];seen=set()
    for r in range(1,bound.rows):
        vals={c:capture.cell(bound.title,r,c).value for c in headers}
        ident=vals[0]
        if ident is None and all(v is None for v in vals.values()):continue
        if type(ident)is not str or not ident or ident!=ident.strip() or ident in seen:return hold('DUPLICATE_OR_INVALID_SOURCE')
        seen.add(ident)
        if type(vals[9])is not int or type(vals[13])is not bool or type(vals[29])is not bool:return hold('SOURCE_TYPE_INVALID')
        if vals[9]<0:return hold('NEGATIVE_QUANTITY')
        if vals[9]==0 or vals[13] or not vals[29]:continue
        if type(vals[2])is not str or type(vals[3])is not int or (vals[2],vals[3])!=(profile.carrier,profile.denomination):return hold('CATEGORY_MAPPING_MISMATCH')
        lo,hi=vals[10],vals[11]
        if not _serial(lo) or not _serial(hi):return hold('SERIAL_TEXT_INVALID')
        try:
            if _distance(lo,hi)!=vals[9]:return hold('QUANTITY_MISMATCH')
        except ValueError:return hold('SERIAL_FIXTURE_BOUND')
        if type(vals[18])is not int or vals[18]<=0:return hold('SOURCE_ROW_INVALID')
        serialdate=vals[19]
        if type(serialdate)not in(int,float) or (type(serialdate)is float and (serialdate!=serialdate or serialdate in (float('inf'),-float('inf')))) or serialdate!=int(serialdate):return hold('SOURCE_DATE_INVALID')
        try:day=date(1899,12,30)+timedelta(days=int(serialdate))
        except (ValueError,OverflowError):return hold('SOURCE_DATE_INVALID')
        if day>profile.target_date:return hold('FUTURE_SOURCE_DATE')
        eligible.append((ident,day,vals[18],lo,hi,vals[9]))
    holdbound=next((x for x in capture.bounds if x.title=='SYSTEM_HOLD_REGISTRY'),None)
    if holdbound is None or holdbound.columns<10:return hold('HOLD_REGISTRY_BOUND_MISSING')
    if any(capture.cell(holdbound.title,0,c).value!=v for c,v in {0:'HoldID',1:'ScopeType',2:'TargetID',9:'Status'}.items()):return hold('HOLD_REGISTRY_HEADER_MISMATCH')
    active=set();hold_ids=set()
    for row in range(1,holdbound.rows):
        ident,scope,target,status=(capture.cell(holdbound.title,row,c).value for c in (0,1,2,9))
        if all(v is None for v in (ident,scope,target,status)):continue
        if any(type(v)is not str or not v or v!=v.strip() for v in (ident,scope,target,status)) or ident in hold_ids:return hold('HOLD_REGISTRY_RECORD_INVALID')
        hold_ids.add(ident)
        if scope!='INTERVAL' or status not in ('ACTIVE','RELEASED','REVERSED','CANCELLED'):return hold('HOLD_REGISTRY_SCOPE_STATE_UNSUPPORTED')
        if status=='ACTIVE':active.add(target)
    if active.intersection(x[0] for x in eligible):return hold('ACTIVE_HOLD_ELIGIBLE_CONFLICT')
    for i,left in enumerate(eligible):
        for right in eligible[i+1:]:
            if int(left[3])<=int(right[4]) and int(right[3])<=int(left[4]):return hold('ELIGIBLE_SERIAL_OVERLAP')
    if {x[0] for x in eligible}!=set(profile.permitted_source_ids):return hold('FROZEN_SOURCE_SET_MISMATCH')
    ranked=sorted(eligible,key=lambda x:(-x[1].toordinal(),x[2],_number_order(x[3])))
    # Detect rank ambiguity before allocation.
    if len({(x[1],x[2],_number_order(x[3])) for x in ranked})!=len(ranked):return hold('AMBIGUOUS_RANK')
    remaining=profile.requested_qty;alloc=[]
    for rank,x in enumerate(ranked,1):
        take=min(remaining,x[5])
        if take:alloc.append(LabAllocation(x[0],rank,take,x[3],_text_add(x[3],take-1)))
        remaining-=take
        if remaining==0:break
    if remaining:return hold('INSUFFICIENT_QUANTITY')
    # Independently validate the greedy prefix by traversing unsorted input and
    # selecting each next earliest canonical candidate, not reusing sorted order.
    pool=list(eligible);remaining=profile.requested_qty;independent=[];rank=0
    while remaining:
        next_source=min(pool,key=lambda x:(-x[1].toordinal(),x[2],_number_order(x[3])))
        pool.remove(next_source);rank+=1;take=min(remaining,next_source[5]);remaining-=take
        independent.append((next_source[0],rank,take,next_source[3],_text_add(next_source[3],take-1)))
    if independent!=[(a.source_id,a.rank,a.quantity,a.serial_start,a.serial_end) for a in alloc]:return hold('INDEPENDENT_PREFIX_MISMATCH')
    return AllocationLabResult('PASS_LAB',tuple(alloc),tuple(x[0] for x in ranked),())


def assess_fixture_allocation_lab(capture: object,profile: AllocationLabProfile) -> AllocationLabResult:
    try:
        return _assess_fixture_allocation_lab(capture,profile)
    except (CaptureRejected,AttributeError,TypeError,ValueError,OverflowError,KeyError):
        return AllocationLabResult('HOLD',(),(),('CAPTURE_OR_PROFILE_MALFORMED',))
