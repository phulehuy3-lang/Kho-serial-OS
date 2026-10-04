"""Version-bound V2 lab validation of native captures; never acquisition readiness."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from scripts.native_cell_capture_v0_1 import NativeCapture, CaptureRejected
from scripts.serial_text_interval_projection_v0_1 import SerialTextInterval, serial_text_range_quantity_matches

SCHEMA_SHA256 = "9a7036828810234062496179c1fe652b9078b1cd7fbe7f50e77e6991b33de203"
ALIASES = {
    "INBOUND_SOURCE_RECORD": "V2_SOURCE",
    "ACTIVE_SERIAL_INTERVAL_UNIVERSE": "V2_ACTIVE",
    "INBOUND_DERIVED_QUERY_PROJECTION": "V2_DERIVED",
    "INBOUND_QUERY_FORMULA_ANCHOR": "V2_ANCHOR",
    "ACTIVE_HOLD_INTERVAL_UNIVERSE": "V2_HOLD",
}

@dataclass(frozen=True, slots=True)
class NativeV2LabReport:
    errors: tuple[str, ...]
    record_counts: tuple[tuple[str, int], ...]

    @property
    def status(self) -> str:
        return "REJECT" if self.errors else "PASS_SCHEMA_ONLY"

    @property
    def ready(self) -> bool:
        return False


def validate_native_v2_lab(capture: NativeCapture, schema: dict) -> NativeV2LabReport:
    digest = hashlib.sha256(json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if digest != SCHEMA_SHA256:
        raise CaptureRejected("SCHEMA_HASH_MISMATCH")
    records = {}
    errors = []
    for surface in schema["surface_contracts"]:
        title = ALIASES[surface["surface_id"]]
        fields = surface["fields"]
        names = [field["field_id"] for field in fields]
        bound = next((b for b in capture.bounds if b.title == title), None)
        if bound is None or bound.columns < len(fields):
            raise CaptureRejected("SURFACE_BINDING_MISSING")
        if [capture.cell(title, 0, col).value for col in range(len(fields))] != names:
            errors.append(title + ":HEADER_MISMATCH")
        rows = []
        for number in range(1, bound.rows):
            values = [capture.cell(title, number, col).value for col in range(len(fields))]
            if all(v is None or v == "" for v in values):
                continue
            row = dict(zip(names, values))
            rows.append(row)
            row_valid = True
            for col, (field, value) in enumerate(zip(fields, values)):
                kind = field["type"]
                if kind in ("TEXT", "SERIAL_TEXT"):
                    valid = type(value) is str and bool(value) and value == value.strip()
                    if kind == "SERIAL_TEXT":
                        valid = valid and all("0" <= char <= "9" for char in value)
                elif kind == "TEXT_OR_NULL":
                    valid = value is None or type(value) is str
                elif kind == "BOOLEAN":
                    valid = type(value) is bool
                else:
                    valid = type(value) is int and value >= 0
                valid = valid and capture.cell(title, number, col).kind != "e"
                if not valid:
                    row_valid = False
                    errors.append(f"{title}:{number + 1}:{field['field_id']}:{kind}")
            if row_valid and ("serial_start" in row or "range_start" in row):
                low, high = (row["serial_start"], row["serial_end"]) if "serial_start" in row else (row["range_start"], row["range_end"])
                try:
                    interval = SerialTextInterval(low, high)
                    if "declared_quantity" in row and not serial_text_range_quantity_matches(interval, row["declared_quantity"]):
                        errors.append(title + ":QUANTITY_MISMATCH")
                except (TypeError, ValueError):
                    errors.append(title + ":INTERVAL_INVALID")
        records[title] = rows
        count = len(rows)
        if surface["cardinality"] == "EXACTLY_ONE_RECORD" and count != 1:
            errors.append(title + ":CARDINALITY")
        if surface["cardinality"] == "ONE_OR_MORE_RECORDS" and count < 1:
            errors.append(title + ":CARDINALITY")
        for key in ("interval_id", "anchor_id", "hold_id"):
            if key + "_unique" in surface["constraints"]:
                values = [r[key] for r in rows]
                if any(type(v) is not str for v in values) or len(values) != len(set(values)):
                    errors.append(title + ":DUPLICATE_OR_INVALID_" + key)
    if records["V2_SOURCE"] != records["V2_DERIVED"]:
        errors.append("V2_SOURCE:DERIVED_RECONCILIATION")
    return NativeV2LabReport(tuple(errors), tuple((name, len(rows)) for name, rows in records.items()))
