"""Warehouse-side Operational TEST V2 profile.

Pure business/schema validation. No provider I/O and no Production authority.
"""
from __future__ import annotations

from datetime import date

CONTRACT_ID = "OS_OPERATIONAL_TEST_CONTRACT_V2_0_R1_20261004"
GENERATION_ID = "OPTEST_SCHEMA_GEN_V2_0_R1"
BINDING_ID = "OPTEST_BINDING_V2_0_R1_M3"
HEADER_AGGREGATE_SHA256 = "762b9451a94339b8798f0bbd79d36c6792715bf66f952ef8f2839e735f24caa7"
POPULATION_MANIFEST_SHA256 = "0063246baacf8c73bdb4280968d40c0cb3830576ac991a96e55f4c9adb2126b4"
ALLOCATION_POLICY = "SOURCE_DATE_DESC|SOURCE_ROW_ASC|SERIAL_START_ASC"

HOLD_SCOPES = frozenset({"INTERVAL", "DOCUMENT", "DOCUMENT_LINE"})
HOLD_STATES = frozenset({"ACTIVE", "RELEASED"})
EVENT_TYPES = frozenset({"IN", "OUT", "HOLD_APPLY", "HOLD_RELEASE", "REVERSAL", "RESET_REGRESSION"})
TRANSACTION_STATES = frozenset({"PREPARED", "COMMITTED", "ABORTED"})

REQUIRED_HEADERS = {
    "OP_EVIDENCE_REGISTRY": ("EvidenceID","EvidenceType","ObjectID","FileSHA256","Location","CaptureTime","ReadbackStatus","Status"),
    "OP_TRANSACTION_REGISTRY": ("TransactionKey","PayloadHash","OperationType","DocumentID","DocumentLineID","DocumentDate","ReceiptDate","SourceDate","Status","SessionID","PreparedAt","CommittedAt","ParentTransactionKey","CallerRunID","GenerationID"),
    "OP_EVENT_LEDGER": ("EventID","TransactionKey","EventType","ParentEventID","ReversalOfEventID","IntervalID","Qty","SerialStart","SerialEnd","SourceDate","Status","CreatedAt","SessionID","GenerationID"),
    "OP_ALLOCATION_LEDGER": ("AllocationID","TransactionKey","Rank","IntervalID","Qty","SerialStart","SerialEnd","SourceDate","SourceRow","PolicyVersion","Status","GenerationID"),
    "OP_SESSION_REGISTRY": ("SessionID","StartedAt","ClosedAt","State","StartGeneration","EndGeneration","ReconciliationStatus","AuditStatus","WriterIdentity"),
    "OP_RECONCILIATION": ("SessionID","PopulationManifestID","SurfaceCount","IntervalQty","InboundCommittedQty","OutboundCommittedQty","ReversalQty","AllocationQty","UnresolvedBlockers","ReadbackStatus","ReconciliationStatus","GenerationID"),
}

class WarehouseProfileRejected(ValueError):
    pass


def _text(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _serial(value: object) -> bool:
    return _text(value) and all("0" <= c <= "9" for c in value)


def _date(value: object) -> date:
    if type(value) is not str:
        raise WarehouseProfileRejected("DATE_TYPE")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise WarehouseProfileRejected("DATE_VALUE") from exc


def validate_header_manifest(actual: object) -> None:
    if type(actual) is not dict:
        raise WarehouseProfileRejected("HEADER_MANIFEST_TYPE")
    for surface, expected in REQUIRED_HEADERS.items():
        if tuple(actual.get(surface, ())) != expected:
            raise WarehouseProfileRejected("HEADER_MISMATCH:" + surface)


def validate_hold_record(record: object) -> None:
    if type(record) is not dict:
        raise WarehouseProfileRejected("HOLD_RECORD_TYPE")
    if record.get("ScopeType") not in HOLD_SCOPES:
        raise WarehouseProfileRejected("HOLD_UNSUPPORTED_SCOPE")
    if record.get("Status") not in HOLD_STATES:
        raise WarehouseProfileRejected("HOLD_STATUS")
    scope = record["ScopeType"]
    if scope == "INTERVAL" and not _text(record.get("TargetIntervalID")):
        raise WarehouseProfileRejected("HOLD_TARGET_INTERVAL")
    if scope == "DOCUMENT" and not _text(record.get("TargetDocumentID")):
        raise WarehouseProfileRejected("HOLD_TARGET_DOCUMENT")
    if scope == "DOCUMENT_LINE" and not (
        _text(record.get("TargetDocumentID")) and _text(record.get("TargetLineID"))
    ):
        raise WarehouseProfileRejected("HOLD_TARGET_LINE")
    if record["Status"] == "RELEASED":
        if not _text(record.get("ReleaseEvidence")) or not _text(record.get("ReleaseEventID")):
            raise WarehouseProfileRejected("HOLD_RELEASE_LINEAGE")


def validate_event(record: object) -> None:
    if type(record) is not dict:
        raise WarehouseProfileRejected("EVENT_RECORD_TYPE")
    if record.get("EventType") not in EVENT_TYPES:
        raise WarehouseProfileRejected("EVENT_TYPE")
    if record.get("Status") not in TRANSACTION_STATES:
        raise WarehouseProfileRejected("EVENT_STATUS")
    if not _text(record.get("TransactionKey")) or not _text(record.get("SessionID")):
        raise WarehouseProfileRejected("EVENT_IDENTITY")
    if record["EventType"] == "REVERSAL" and not _text(record.get("ReversalOfEventID")):
        raise WarehouseProfileRejected("REVERSAL_LINK")
    for key in ("SerialStart", "SerialEnd"):
        value = record.get(key)
        if value is not None and not _serial(value):
            raise WarehouseProfileRejected("SERIAL_TEXT")
    if record.get("SourceDate") is not None:
        _date(record["SourceDate"])


def validate_outbound_candidate(candidate: object, document_date: object) -> tuple:
    if type(candidate) is not dict:
        raise WarehouseProfileRejected("CANDIDATE_TYPE")
    source_date = _date(candidate.get("SourceDate"))
    doc = _date(document_date)
    if source_date.year != doc.year or source_date > doc:
        raise WarehouseProfileRejected("DATE_GATE")
    if candidate.get("Status") != "AVAILABLE":
        raise WarehouseProfileRejected("INTERVAL_STATUS")
    if type(candidate.get("AvailableQty")) is not int or candidate["AvailableQty"] <= 0:
        raise WarehouseProfileRejected("AVAILABLE_QTY")
    if candidate.get("HoldFlag") is not False:
        raise WarehouseProfileRejected("ACTIVE_HOLD")
    if candidate.get("EvidenceStatus") != "VERIFIED":
        raise WarehouseProfileRejected("EVIDENCE_STATUS")
    if not _serial(candidate.get("AvailableStart")) or not _serial(candidate.get("AvailableEnd")):
        raise WarehouseProfileRejected("SERIAL_TEXT")
    source_row = candidate.get("SourceRow")
    if type(source_row) is not int or source_row < 0:
        raise WarehouseProfileRejected("SOURCE_ROW")
    return (-source_date.toordinal(), source_row, candidate["AvailableStart"])


def rank_candidates(candidates: object, document_date: object) -> tuple:
    if type(candidates) is not list:
        raise WarehouseProfileRejected("CANDIDATES_TYPE")
    eligible = []
    for candidate in candidates:
        try:
            key = validate_outbound_candidate(candidate, document_date)
        except WarehouseProfileRejected as exc:
            if str(exc) == "DATE_GATE":
                continue
            raise
        eligible.append((key, candidate))
    eligible.sort(key=lambda item: item[0])
    return tuple(candidate for _, candidate in eligible)


def _valid_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


def validate_inbound_evidence_intent(transaction_key: object, touches: object) -> None:
    if not _text(transaction_key):
        raise WarehouseProfileRejected("TRANSACTION_KEY")
    if type(touches) is not list:
        raise WarehouseProfileRejected("TOUCHES")
    evidence_rows: dict[str, dict[str, object]] = {}
    for touch in touches:
        if type(touch) is not dict or touch.get("sheet") != "OP_EVIDENCE_REGISTRY":
            continue
        key = touch.get("key")
        field = touch.get("field")
        if _text(key) and _text(field):
            evidence_rows.setdefault(key, {})[field] = touch.get("after")
    linked = [
        (key, fields)
        for key, fields in evidence_rows.items()
        if fields.get("ObjectID") == transaction_key
    ]
    if not linked:
        raise WarehouseProfileRejected("HOLD_EVIDENCE_MISSING")
    if len(linked) != 1:
        raise WarehouseProfileRejected("HOLD_EVIDENCE_MISMATCH")
    key, fields = linked[0]
    if (
        fields.get("EvidenceID") != key
        or not _valid_sha256(fields.get("FileSHA256"))
        or fields.get("ReadbackStatus") != "PASS"
        or fields.get("Status") != "VERIFIED"
    ):
        raise WarehouseProfileRejected("HOLD_EVIDENCE_MISMATCH")


def validate_operational_plan(plan: object) -> None:
    if type(plan) is not dict:
        raise WarehouseProfileRejected("PLAN_TYPE")
    if plan.get("contract_id") != CONTRACT_ID:
        raise WarehouseProfileRejected("CONTRACT_ID")
    if plan.get("generation_id") != GENERATION_ID:
        raise WarehouseProfileRejected("GENERATION_ID")
    if plan.get("binding_id") != BINDING_ID:
        raise WarehouseProfileRejected("BINDING_ID")
    if plan.get("header_aggregate_sha256") != HEADER_AGGREGATE_SHA256:
        raise WarehouseProfileRejected("HEADER_HASH")
    if plan.get("population_manifest_sha256") != POPULATION_MANIFEST_SHA256:
        raise WarehouseProfileRejected("MANIFEST_HASH")
    if plan.get("allocation_policy") != ALLOCATION_POLICY:
        raise WarehouseProfileRejected("ALLOCATION_POLICY")
    if plan.get("production_write_authorized") is not False:
        raise WarehouseProfileRejected("PRODUCTION_AUTHORITY")
    if plan.get("operation_type") not in EVENT_TYPES:
        raise WarehouseProfileRejected("OPERATION_TYPE")


WAREHOUSE_WRITE_SURFACES = frozenset({
    "OP_EVIDENCE_REGISTRY",
    "OP_TRANSACTION_REGISTRY",
    "OP_EVENT_LEDGER",
    "SYSTEM_INTERVAL_STATE",
    "SYSTEM_HOLD_REGISTRY",
    "OP_ALLOCATION_LEDGER",
    "OP_SESSION_REGISTRY",
})
WAREHOUSE_FORBIDDEN_SURFACES = frozenset({
    "OP_CONTROL", "ELIGIBLE_STOCK", "HOLD_QUARANTINE", "OP_RECONCILIATION",
    "V2_SOURCE", "V2_ACTIVE", "V2_DERIVED", "V2_ANCHOR", "V2_HOLD",
    "R4_RESULTS", "R4_SOURCE_CONTRACT", "R5_RESULTS", "R5_SOURCE_CONTRACT",
})


def build_warehouse_intent(operation_type: object, touches: object) -> tuple[dict, ...]:
    """Normalize header-bound TEST write intents; performs no I/O."""
    if operation_type not in EVENT_TYPES:
        raise WarehouseProfileRejected("OPERATION_TYPE")
    if type(touches) is not list or not touches:
        raise WarehouseProfileRejected("TOUCHES")
    out = []
    seen = set()
    for touch in touches:
        if type(touch) is not dict or set(touch) != {"sheet", "key", "field", "before", "after"}:
            raise WarehouseProfileRejected("TOUCH_SCHEMA")
        sheet = touch["sheet"]
        if sheet in WAREHOUSE_FORBIDDEN_SURFACES or sheet not in WAREHOUSE_WRITE_SURFACES:
            raise WarehouseProfileRejected("WRITE_SURFACE_FORBIDDEN")
        if not _text(touch["key"]) or not _text(touch["field"]):
            raise WarehouseProfileRejected("TOUCH_IDENTITY")
        identity = (sheet, touch["key"], touch["field"])
        if identity in seen:
            raise WarehouseProfileRejected("DUPLICATE_TOUCH")
        seen.add(identity)
        if touch["before"] == touch["after"]:
            raise WarehouseProfileRejected("NOOP_TOUCH")
        out.append(dict(touch))
    if operation_type == "IN":
        transaction_keys = {
            touch["key"]
            for touch in touches
            if touch.get("sheet") == "OP_TRANSACTION_REGISTRY"
            and touch.get("field") == "TransactionKey"
        }
        if len(transaction_keys) != 1:
            raise WarehouseProfileRejected("TRANSACTION_KEY")
        validate_inbound_evidence_intent(next(iter(transaction_keys)), touches)
    return tuple(out)
