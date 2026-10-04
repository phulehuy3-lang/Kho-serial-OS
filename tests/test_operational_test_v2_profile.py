import unittest

from scripts.operational_test_v2_profile import (
    ALLOCATION_POLICY,
    BINDING_ID,
    CONTRACT_ID,
    GENERATION_ID,
    HEADER_AGGREGATE_SHA256,
    POPULATION_MANIFEST_SHA256,
    REQUIRED_HEADERS,
    WarehouseProfileRejected,
    rank_candidates,
    validate_event,
    validate_header_manifest,
    validate_hold_record,
    validate_operational_plan,
    build_warehouse_intent,
)


class WarehouseOperationalV2Tests(unittest.TestCase):
    def test_exact_headers_pass(self):
        validate_header_manifest({k: list(v) for k, v in REQUIRED_HEADERS.items()})

    def test_header_drift_holds(self):
        actual = {k: list(v) for k, v in REQUIRED_HEADERS.items()}
        actual["OP_EVENT_LEDGER"][0] = "Wrong"
        with self.assertRaisesRegex(WarehouseProfileRejected, "HEADER_MISMATCH"):
            validate_header_manifest(actual)

    def test_document_line_hold_requires_both_targets(self):
        with self.assertRaisesRegex(WarehouseProfileRejected, "HOLD_TARGET_LINE"):
            validate_hold_record({"ScopeType":"DOCUMENT_LINE","Status":"ACTIVE","TargetDocumentID":"D1"})

    def test_released_hold_requires_lineage(self):
        with self.assertRaisesRegex(WarehouseProfileRejected, "HOLD_RELEASE_LINEAGE"):
            validate_hold_record({"ScopeType":"INTERVAL","Status":"RELEASED","TargetIntervalID":"I1"})

    def test_reversal_requires_link(self):
        with self.assertRaisesRegex(WarehouseProfileRejected, "REVERSAL_LINK"):
            validate_event({"EventType":"REVERSAL","Status":"COMMITTED","TransactionKey":"T","SessionID":"S"})

    def test_long_serial_remains_text(self):
        validate_event({
            "EventType":"OUT","Status":"COMMITTED","TransactionKey":"T","SessionID":"S",
            "SerialStart":"900719925474099300","SerialEnd":"900719925474099301","SourceDate":"2026-10-01"
        })
        with self.assertRaisesRegex(WarehouseProfileRejected, "SERIAL_TEXT"):
            validate_event({
                "EventType":"OUT","Status":"COMMITTED","TransactionKey":"T","SessionID":"S",
                "SerialStart":900719925474099300,"SerialEnd":"900719925474099301"
            })

    def test_rank_is_source_date_desc_row_asc_serial_asc(self):
        base={"Status":"AVAILABLE","AvailableQty":1,"HoldFlag":False,"EvidenceStatus":"VERIFIED",
              "AvailableEnd":"0009"}
        rows=[
            {**base,"id":"old","SourceDate":"2026-09-01","SourceRow":1,"AvailableStart":"0001"},
            {**base,"id":"b","SourceDate":"2026-10-01","SourceRow":2,"AvailableStart":"0005"},
            {**base,"id":"a","SourceDate":"2026-10-01","SourceRow":1,"AvailableStart":"0006"},
            {**base,"id":"a2","SourceDate":"2026-10-01","SourceRow":1,"AvailableStart":"0004"},
            {**base,"id":"future","SourceDate":"2026-10-06","SourceRow":0,"AvailableStart":"0000"},
        ]
        ranked=rank_candidates(rows,"2026-10-05")
        self.assertEqual([x["id"] for x in ranked],["a2","a","b","old"])

    def test_active_hold_blocks_candidate(self):
        c={"SourceDate":"2026-10-01","Status":"AVAILABLE","AvailableQty":1,"HoldFlag":True,
           "EvidenceStatus":"VERIFIED","AvailableStart":"0001","AvailableEnd":"0001","SourceRow":1}
        with self.assertRaisesRegex(WarehouseProfileRejected, "ACTIVE_HOLD"):
            rank_candidates([c],"2026-10-05")

    def test_operational_plan_is_test_only(self):
        plan={
            "contract_id":CONTRACT_ID,"generation_id":GENERATION_ID,"binding_id":BINDING_ID,
            "header_aggregate_sha256":HEADER_AGGREGATE_SHA256,
            "population_manifest_sha256":POPULATION_MANIFEST_SHA256,
            "allocation_policy":ALLOCATION_POLICY,"production_write_authorized":False,
            "operation_type":"IN",
        }
        validate_operational_plan(plan)
        plan["production_write_authorized"]=True
        with self.assertRaisesRegex(WarehouseProfileRejected, "PRODUCTION_AUTHORITY"):
            validate_operational_plan(plan)

    def test_writer_intent_forbids_derived_surface(self):
        with self.assertRaisesRegex(WarehouseProfileRejected, "WRITE_SURFACE_FORBIDDEN"):
            build_warehouse_intent("IN", [{
                "sheet":"ELIGIBLE_STOCK","key":"I1","field":"Status","before":"A","after":"B"
            }])

    def test_writer_intent_is_header_bound(self):
        intent=build_warehouse_intent("IN", [{
            "sheet":"SYSTEM_INTERVAL_STATE","key":"I1","field":"Status","before":"HOLD","after":"AVAILABLE"
        }])
        self.assertEqual(intent[0]["field"],"Status")

    def test_old_generation_holds(self):
        plan={
            "contract_id":CONTRACT_ID,"generation_id":"R5","binding_id":BINDING_ID,
            "header_aggregate_sha256":HEADER_AGGREGATE_SHA256,
            "population_manifest_sha256":POPULATION_MANIFEST_SHA256,
            "allocation_policy":ALLOCATION_POLICY,"production_write_authorized":False,
            "operation_type":"IN",
        }
        with self.assertRaisesRegex(WarehouseProfileRejected, "GENERATION_ID"):
            validate_operational_plan(plan)


if __name__ == "__main__":
    unittest.main()
