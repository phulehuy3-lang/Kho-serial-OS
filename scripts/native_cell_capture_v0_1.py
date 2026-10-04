"""Bounded typed native capture decoder; no provider I/O or authority grant."""
from __future__ import annotations
from dataclasses import dataclass

class CaptureRejected(ValueError):
    """Capture is malformed or outside the declared lab bounds."""

@dataclass(frozen=True, slots=True)
class SurfaceBound:
    title: str
    rows: int
    columns: int

@dataclass(frozen=True, slots=True)
class NativeCell:
    value: object
    kind: str
    formula: str | None = None

@dataclass(frozen=True, slots=True)
class NativeCapture:
    bounds: tuple[SurfaceBound, ...]
    entries: tuple[tuple[str, int, int, NativeCell], ...]

    @property
    def atomic_snapshot_proven(self) -> bool:
        return False

    @property
    def domain_completeness_proven(self) -> bool:
        return False

    def cell(self, title: str, row: int, column: int) -> NativeCell:
        bound = next((b for b in self.bounds if b.title == title), None)
        if bound is None or type(row) is not int or type(column) is not int or not (0 <= row < bound.rows and 0 <= column < bound.columns):
            raise CaptureRejected("READ_OUTSIDE_BOUND")
        return next((v for n, r, c, v in self.entries if (n, r, c) == (title, row, column)), NativeCell(None, "missing"))

ERROR_CODES = {"REF": "#REF!", "DIVIDE_BY_ZERO": "#DIV/0!", "VALUE": "#VALUE!", "N_A": "#N/A", "NAME": "#NAME?", "NUM": "#NUM!", "ERROR": "#ERROR!", "NULL_VALUE": "#NULL!", "LOADING": "#LOADING!"}

def _value(value: object) -> tuple[object, str]:
    if not isinstance(value, dict) or len(value) > 1:
        raise CaptureRejected("AMBIGUOUS_VALUE")
    if not value:
        return None, "missing"
    key, item = next(iter(value.items()))
    if key == "stringValue" and type(item) is str:
        return item, "str"
    if key == "boolValue" and type(item) is bool:
        return item, "b"
    if key == "numberValue" and ((type(item) is int and abs(item) <= 2 ** 53 - 1) or (type(item) is float and (item == item and -float("inf") < item < float("inf")))):
        return item, "n"
    if key == "errorValue" and isinstance(item, dict) and type(item.get("type")) is str and item.get("type") in ERROR_CODES:
        return ERROR_CODES[item["type"]], "e"
    raise CaptureRejected("INVALID_TYPED_VALUE")

def decode_native_capture(payload: dict, bounds: tuple[SurfaceBound, ...], *, max_cells: int = 6000) -> NativeCapture:
    if type(max_cells) is not int or max_cells < 1 or not isinstance(bounds, tuple) or not bounds or not all(isinstance(b, SurfaceBound) and type(b.title) is str for b in bounds) or len({b.title for b in bounds}) != len(bounds):
        raise CaptureRejected("INVALID_BOUNDS")
    for b in bounds:
        if not b.title or type(b.rows) is not int or type(b.columns) is not int or b.rows < 1 or b.columns < 1:
            raise CaptureRejected("INVALID_BOUNDS")
    if sum(b.rows * b.columns for b in bounds) > max_cells:
        raise CaptureRejected("CAPTURE_LIMIT")
    if not isinstance(payload, dict) or not isinstance(payload.get("sheets"), list):
        raise CaptureRejected("INVALID_RESPONSE")
    bound_map = {b.title: b for b in bounds}
    seen_sheets = set()
    seen_cells = set()
    entries = []
    for sheet in payload["sheets"]:
        if not isinstance(sheet, dict) or not isinstance(sheet.get("properties"), dict):
            raise CaptureRejected("INVALID_SHEET")
        title = sheet["properties"].get("title")
        if type(title) is not str or title not in bound_map or title in seen_sheets:
            raise CaptureRejected("SURFACE_SET_MISMATCH")
        seen_sheets.add(title)
        data = sheet.get("data")
        if not isinstance(data, list) or not data:
            raise CaptureRejected("MISSING_GRID_DATA")
        for grid in data:
            if not isinstance(grid, dict):
                raise CaptureRejected("INVALID_GRID")
            row0, col0 = grid.get("startRow", 0), grid.get("startColumn", 0)
            rows = grid.get("rowData", [])
            if type(row0) is not int or type(col0) is not int or row0 < 0 or col0 < 0 or row0 >= bound_map[title].rows or col0 >= bound_map[title].columns or not isinstance(rows, list):
                raise CaptureRejected("INVALID_GRID")
            if row0 + len(rows) > bound_map[title].rows:
                raise CaptureRejected("DUPLICATE_OR_OUTSIDE_POSITION")
            for i, row in enumerate(rows):
                if not isinstance(row, dict) or not isinstance(row.get("values", []), list):
                    raise CaptureRejected("INVALID_ROW")
                for j, cell in enumerate(row.get("values", [])):
                    pos = (title, row0 + i, col0 + j)
                    b = bound_map[title]
                    if pos in seen_cells or pos[1] >= b.rows or pos[2] >= b.columns:
                        raise CaptureRejected("DUPLICATE_OR_OUTSIDE_POSITION")
                    seen_cells.add(pos)
                    if not isinstance(cell, dict):
                        raise CaptureRejected("INVALID_CELL")
                    value, kind = _value(cell.get("effectiveValue", {}))
                    entered = cell.get("userEnteredValue", {})
                    if not isinstance(entered, dict) or len(entered) > 1:
                        raise CaptureRejected("AMBIGUOUS_ENTERED_VALUE")
                    if entered and not cell.get("effectiveValue") and "formulaValue" not in entered and entered != {"stringValue": ""}:
                        raise CaptureRejected("EFFECTIVE_VALUE_MISSING")
                    formula = entered.get("formulaValue")
                    if formula is not None:
                        if type(formula) is not str or not formula.startswith("="):
                            raise CaptureRejected("INVALID_FORMULA")
                    else:
                        _value(entered)
                    entries.append((*pos, NativeCell(value, kind, formula)))
    if seen_sheets != set(bound_map):
        raise CaptureRejected("SURFACE_SET_MISMATCH")
    return NativeCapture(bounds, tuple(entries))
