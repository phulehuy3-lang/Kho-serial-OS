"""Schema-bound lab regressions; no provider acquisition."""
import dataclasses
import json
from pathlib import Path
import unittest
from scripts.native_cell_capture_v0_1 import NativeCapture, NativeCell, SurfaceBound, CaptureRejected
from scripts.native_v2_lab_adapter_v0_1 import ALIASES, validate_native_v2_lab

class NativeV2LabTests(unittest.TestCase):
    def setup_capture(self):
        schema = json.loads((Path(__file__).resolve().parents[1] / "rules/WAREHOUSE_INBOUND_SCHEMA_CONTRACT_V2.json").read_text())
        values = {"serial_start": "00001", "serial_end": "00005", "range_start": "00001", "range_end": "00005", "declared_quantity": 5, "hold_flag": True, "formula_present": True, "error_code": None, "status": "ACTIVE"}
        entries = []
        bounds = []
        for s in schema["surface_contracts"]:
            n = ALIASES[s["surface_id"]]
            bounds.append(SurfaceBound(n, 4, len(s["fields"])))
            for col, f in enumerate(s["fields"]):
                entries.append((n, 0, col, NativeCell(f["field_id"], "str")))
                v = values.get(f["field_id"], f["field_id"])
                kind = "missing" if v is None else "b" if type(v) is bool else "n" if type(v) is int else "str"
                entries.append((n, 1, col, NativeCell(v, kind)))
        return NativeCapture(tuple(bounds), tuple(entries)), schema

    def changed(self, capture, title, col, value, kind):
        return dataclasses.replace(capture, entries=tuple((n, r, c, NativeCell(value, kind)) if (n, r, c) == (title, 1, col) else (n, r, c, v) for n, r, c, v in capture.entries))

    def test_positive_is_schema_only_not_ready(self):
        c, s = self.setup_capture()
        r = validate_native_v2_lab(c, s)
        self.assertEqual(r.errors, ())
        self.assertEqual(r.status, "PASS_SCHEMA_ONLY")
        self.assertFalse(r.ready)

    def test_numeric_serial_rejected_for_specific_reason(self):
        c, s = self.setup_capture()
        r = validate_native_v2_lab(self.changed(c, "V2_SOURCE", 3, 1, "n"), s)
        self.assertEqual(r.status, "REJECT")
        self.assertIn("V2_SOURCE:2:serial_start:SERIAL_TEXT", r.errors)

    def test_quantity_and_order_rejected(self):
        c, s = self.setup_capture()
        r = validate_native_v2_lab(self.changed(c, "V2_SOURCE", 5, 4, "n"), s)
        self.assertIn("V2_SOURCE:QUANTITY_MISMATCH", r.errors)
        r = validate_native_v2_lab(self.changed(c, "V2_SOURCE", 3, "00006", "str"), s)
        self.assertIn("V2_SOURCE:INTERVAL_INVALID", r.errors)

    def test_duplicate_interval_rejected(self):
        c, s = self.setup_capture()
        duplicate = tuple((n, 2, col, v) for n, row, col, v in c.entries if n == "V2_ACTIVE" and row == 1)
        r = validate_native_v2_lab(dataclasses.replace(c, entries=c.entries + duplicate), s)
        self.assertIn("V2_ACTIVE:DUPLICATE_OR_INVALID_interval_id", r.errors)

    def test_schema_drift_rejected(self):
        c, s = self.setup_capture()
        s["warehouse_schema_version"] = "OTHER"
        with self.assertRaisesRegex(CaptureRejected, "SCHEMA_HASH_MISMATCH"):
            validate_native_v2_lab(c, s)

    def test_error_cannot_pass_as_text(self):
        c, s = self.setup_capture()
        r = validate_native_v2_lab(self.changed(c, "V2_SOURCE", 0, "#REF!", "e"), s)
        self.assertIn("V2_SOURCE:2:task_id:TEXT", r.errors)

    def test_missing_bound_rejected(self):
        c, s = self.setup_capture()
        c = dataclasses.replace(c, bounds=c.bounds[:-1])
        with self.assertRaisesRegex(CaptureRejected, "SURFACE_BINDING_MISSING"):
            validate_native_v2_lab(c, s)
