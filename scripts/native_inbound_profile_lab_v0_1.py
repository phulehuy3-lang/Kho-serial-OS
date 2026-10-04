"""Seven actual inbound producers on finite before/after native captures."""
from __future__ import annotations
import dataclasses
from scripts.native_cell_capture_v0_1 import NativeCapture
from scripts.inbound_serial_query_derived_v1 import InboundProfileContext,InboundProducerOutcomes,evaluate_inbound_profile,PROFILE_CONTRACT_ID
from scripts.source_role_boundary_v0_1 import SourceRoleBoundaryRequest,evaluate_source_role_boundary,SOURCE_OF_TRUTH,BUSINESS_WRITE
from scripts.source_readback_v0_1 import SourceFieldValue,MaterializedSourceRecord,SourceReadbackRequest,evaluate_source_readback
from scripts.serial_interval_integrity_v0_1 import SerialInterval,find_overlaps,serial_range_quantity_matches
from scripts.reconciliation_formula_health_v0_1 import FormulaAnchorSnapshot,exact_source_derived_reconciliation,formula_anchors_healthy
from scripts.formula_semantic_identity_v0_2 import with_computed_formula_contract_hash_v2,assess_formula_semantic_identity_v2

def assess_native_inbound_profile_lab(before: NativeCapture,after: NativeCapture) -> dict:
    result={'status':'HOLD','ready':False,'production_write_authorized':False,'operational_acceptance':False,'blockers':[]}
    try:
        if type(before)is not NativeCapture or type(after)is not NativeCapture:raise ValueError('NATIVE_CAPTURE_TYPE')
        source={str(c):after.cell('V2_SOURCE',1,c).value for c in range(6)};derived={str(c):after.cell('V2_DERIVED',1,c).value for c in range(6)}
        ctx=InboundProfileContext(PROFILE_CONTRACT_ID,'R5_INBOUND5','TEST20','R5_MATERIALIZED_NATIVE_READBACK')
        expected=MaterializedSourceRecord(ctx.task_id,ctx.scope_id,ctx.capture_marker,tuple(SourceFieldValue(str(c),before.cell('V2_SOURCE',1,c).value)for c in range(6)))
        actual=MaterializedSourceRecord(ctx.task_id,ctx.scope_id,ctx.capture_marker,tuple(SourceFieldValue(k,v)for k,v in source.items()))
        readback=evaluate_source_readback(SourceReadbackRequest('SOURCE_READBACK_V1',expected,actual))
        role=evaluate_source_role_boundary(SourceRoleBoundaryRequest('SOURCE_ROLE_BOUNDARY_V1',(SOURCE_OF_TRUTH,),BUSINESS_WRITE))
        incoming=SerialInterval(int(source['3']),int(source['4']));bnd=next(b for b in before.bounds if b.title=='V2_ACTIVE')
        active=[SerialInterval(int(before.cell('V2_ACTIVE',r,2).value),int(before.cell('V2_ACTIVE',r,3).value))for r in range(1,bnd.rows)if before.cell('V2_ACTIVE',r,0).value is not None]
        holdbound=next(b for b in before.bounds if b.title=='V2_HOLD')
        held=[SerialInterval(int(before.cell('V2_HOLD',r,2).value),int(before.cell('V2_HOLD',r,3).value))for r in range(1,holdbound.rows)if before.cell('V2_HOLD',r,4).value is True and before.cell('V2_HOLD',r,5).value=='ACTIVE']
        conflict=any(incoming.start<=h.end and h.start<=incoming.end for h in held)
        formula=after.cell('V2_DERIVED',1,0)
        contract=with_computed_formula_contract_hash_v2(contract_id='R5_FINITE_INBOUND_QUERY',source='V2_SOURCE!A2:F2',query_text='select A,B,C,D,E,F',header_rows=0,exported_fallback_literal='')
        semantics=assess_formula_semantic_identity_v2(formula=formula.formula,contract=contract)
        producers=InboundProducerOutcomes(role,readback,serial_range_quantity_matches(incoming,source['5']),not bool(find_overlaps(tuple([incoming]+active))),exact_source_derived_reconciliation(source,derived),formula_anchors_healthy((FormulaAnchorSnapshot('V2_DERIVED!A2',formula.formula is not None,formula.value if formula.kind=='e'else None),)),semantics)
        profile=evaluate_inbound_profile(ctx,producers,conflict)
        result.update(status=profile.status,profile=dataclasses.asdict(profile),producer_outcomes=dataclasses.asdict(producers),hold_conflict=conflict,lab_role_assumption='EXPLICIT_SYNTHETIC_SOURCE_ROLE_ONLY',universe='FROZEN_PREINBOUND_V2_ACTIVE_NOT_POSTINSERT_SELF')
    except (ValueError,TypeError,KeyError,AttributeError,StopIteration)as error:result['blockers'].append(str(error))
    return result
