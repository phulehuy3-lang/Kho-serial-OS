"""Materialized source readback and existing lifecycle gates; synthetic lab only."""
from __future__ import annotations
from scripts.source_readback_v0_1 import SourceFieldValue,MaterializedSourceRecord,SourceReadbackRequest,evaluate_source_readback
from scripts.warehouse_governance_v1_8 import validate_transition
FLAGS={'ready':False,'production_write_authorized':False,'operational_acceptance':False,'provider_atomicity_proven':False,'production_domain_completeness_proven':False}

def assess_native_mutation_lifecycle_lab(capture: object,operations: list,task_id: str,plan_hash: str) -> dict:
    """Native source fields are actual; transaction metadata is a caller lab seal.

    No provider-origin attestation is inferred from the seal or capture markers.
    """
    result={'status':'HOLD','blockers':[],**FLAGS}
    try:
        if type(operations)is not list or not operations or type(plan_hash)is not str or len(plan_hash)!=64:raise ValueError('LIFECYCLE_INPUT')
        expected=[];actual=[];keys=set()
        for op in operations:
            key=f"{op['sheet']}:{op['row']}:{op['column']}"
            if key in keys:raise ValueError('DUPLICATE_READBACK_FIELD')
            keys.add(key);v=op['after'];value=next(iter(v.values()))if v else None
            expected.append(SourceFieldValue(key,value));actual.append(SourceFieldValue(key,capture.cell(op['sheet'],op['row'],op['column']).value))
        # This field binds the externally sealed caller transaction. It is not a
        # claim that Google supplied a payload_hash field on the source sheet.
        expected.append(SourceFieldValue('payload_hash',plan_hash));actual.append(SourceFieldValue('payload_hash',plan_hash))
        scope='R5_DISPOSABLE_LAB';marker='READBACK:'+task_id+':'+plan_hash
        e=MaterializedSourceRecord(task_id,scope,marker,tuple(expected));a=MaterializedSourceRecord(task_id,scope,marker,tuple(actual))
        request=SourceReadbackRequest('SOURCE_READBACK_V1',e,a)
        if evaluate_source_readback(request).status!='PASS':raise ValueError('MATERIALIZED_SOURCE_READBACK_HOLD')
        evidence={'evidence_id':'R5:'+task_id,'capture_kind':'INDEPENDENT_READBACK','request':request}
        binding={'task_id':task_id,'scope_id':scope,'payload_hash':plan_hash,'readback_capture_marker':marker,'written_capture_marker':'WRITTEN:'+task_id+':'+plan_hash}
        transitions=[]
        for previous,following in zip(('PREPARED','PREWRITE_SEALED','WRITTEN','READBACK_PASS'),('PREWRITE_SEALED','WRITTEN','READBACK_PASS','CLOSED')):
            validate_transition(previous,following,manifest_readback=True,reconciliation=True,audit=True,readback_evidence=evidence,transaction_binding=binding);transitions.append((previous,following))
        result.update(status='CLOSED_LAB',transitions=transitions,source_fields_verified=len(operations),transaction_metadata='EXTERNAL_CALLER_LAB_SEAL_NOT_PROVIDER_ATTESTATION')
    except (ValueError,TypeError,KeyError,AttributeError)as error:result['blockers'].append(str(error))
    return result
