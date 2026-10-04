"""Adversarial typed capture regressions; no provider access."""
import copy
import unittest
from scripts.native_cell_capture_v0_1 import CaptureRejected, SurfaceBound, decode_native_capture

class NativeCaptureTests(unittest.TestCase):
    def payload(self):
        return {"sheets": [{"properties": {"title": "LAB"}, "data": [{"rowData": [{"values": [{"userEnteredValue": {"stringValue": "00001"}, "effectiveValue": {"stringValue": "00001"}}, {"effectiveValue": {"boolValue": False}}, {"userEnteredValue": {"formulaValue": "=QUERY(A1:A1)"}, "effectiveValue": {"errorValue": {"type": "REF"}}}]}]}]}]}

    def decode(self, payload):
        return decode_native_capture(payload, (SurfaceBound("LAB", 3, 3),))

    def test_identity_boolean_formula_error_and_no_proof(self):
        c = self.decode(self.payload())
        self.assertEqual(c.cell("LAB", 0, 0).value, "00001")
        self.assertIs(c.cell("LAB", 0, 1).value, False)
        self.assertEqual(c.cell("LAB", 0, 2).value, "#REF!")
        self.assertEqual(c.cell("LAB", 0, 2).formula, "=QUERY(A1:A1)")
        self.assertEqual(c.cell("LAB", 2, 2).kind, "missing")
        self.assertFalse(c.atomic_snapshot_proven)
        self.assertFalse(c.domain_completeness_proven)

    def test_outside_or_pseudoint_read_rejected(self):
        c = self.decode(self.payload())
        for args in [("LAB", 3, 0), ("OTHER", 0, 0), ("LAB", True, 0)]:
            with self.assertRaisesRegex(CaptureRejected, "READ_OUTSIDE_BOUND"):
                c.cell(*args)

    def test_bad_typed_values(self):
        for value in [{"boolValue": "FALSE"}, {"numberValue": True}, {"numberValue": float("nan")}, {"numberValue": 10 ** 400}, {"stringValue": "x", "boolValue": True}, {"errorValue": {"type": "UNKNOWN"}}, {"errorValue": {"type": []}}]:
            p = self.payload()
            p["sheets"][0]["data"][0]["rowData"][0]["values"][0]["effectiveValue"] = value
            with self.assertRaises(CaptureRejected):
                self.decode(p)

    def test_duplicate_position(self):
        p = self.payload()
        p["sheets"][0]["data"].append(copy.deepcopy(p["sheets"][0]["data"][0]))
        with self.assertRaisesRegex(CaptureRejected, "DUPLICATE_OR_OUTSIDE_POSITION"):
            self.decode(p)

    def test_missing_duplicate_extra_surface(self):
        for mode in ["missing", "duplicate", "extra"]:
            p = self.payload()
            if mode == "missing":
                p["sheets"] = []
            elif mode == "duplicate":
                p["sheets"].append(copy.deepcopy(p["sheets"][0]))
            else:
                p["sheets"][0]["properties"]["title"] = "OTHER"
            with self.assertRaisesRegex(CaptureRejected, "SURFACE_SET_MISMATCH"):
                self.decode(p)

    def test_invalid_response_or_grid(self):
        for p in [{}, {"sheets": [{"properties": {"title": "LAB"}}]}]:
            with self.assertRaises(CaptureRejected):
                self.decode(p)

    def test_negative_or_pseudo_offset(self):
        for offset in [-1, True, "0"]:
            p = self.payload()
            p["sheets"][0]["data"][0]["startRow"] = offset
            with self.assertRaisesRegex(CaptureRejected, "INVALID_GRID"):
                self.decode(p)

    def test_limit_invalid_duplicate_bounds(self):
        for bounds, limit in [((SurfaceBound("LAB", 3, 3),), 8), ((SurfaceBound("LAB", True, 3),), 100), ((SurfaceBound("LAB", 3, 3), SurfaceBound("LAB", 3, 3)), 100)]:
            with self.assertRaises(CaptureRejected):
                decode_native_capture(self.payload(), bounds, max_cells=limit)

    def test_outside_capture(self):
        p = self.payload()
        p["sheets"][0]["data"][0]["startColumn"] = 2
        with self.assertRaisesRegex(CaptureRejected, "DUPLICATE_OR_OUTSIDE_POSITION"):
            self.decode(p)

    def test_invalid_formula(self):
        p = self.payload()
        p["sheets"][0]["data"][0]["rowData"][0]["values"][2]["userEnteredValue"] = {"formulaValue": "QUERY(A1:A1)"}
        with self.assertRaisesRegex(CaptureRejected, "INVALID_FORMULA"):
            self.decode(p)

    def test_effective_missing_scalar_rejected_but_blank_formula_diagnostic(self):
        p = self.payload()
        del p["sheets"][0]["data"][0]["rowData"][0]["values"][0]["effectiveValue"]
        with self.assertRaisesRegex(CaptureRejected, "EFFECTIVE_VALUE_MISSING"):
            self.decode(p)
        p = self.payload()
        del p["sheets"][0]["data"][0]["rowData"][0]["values"][2]["effectiveValue"]
        c = self.decode(p)
        self.assertEqual(c.cell("LAB", 0, 2).kind, "missing")
        self.assertIsNotNone(c.cell("LAB", 0, 2).formula)
        self.assertFalse(c.atomic_snapshot_proven)

    def test_nontext_surface_and_malformed_bound_are_rejected(self):
        p = self.payload()
        p["sheets"][0]["properties"]["title"] = []
        with self.assertRaisesRegex(CaptureRejected, "SURFACE_SET_MISMATCH"):
            self.decode(p)
        with self.assertRaisesRegex(CaptureRejected, "INVALID_BOUNDS"):
            decode_native_capture(self.payload(), (SurfaceBound([], 3, 3),))
