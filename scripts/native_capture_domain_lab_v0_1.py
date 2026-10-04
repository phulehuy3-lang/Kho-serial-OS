"""Verify a prelocked finite synthetic model, never provider/Production authority."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from scripts.native_cell_capture_v0_1 import SurfaceBound, NativeCapture, decode_native_capture, CaptureRejected

CONTRACT_ID = "NATIVE_DOMAIN_LAB_CONTRACT_V0_1"

def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True, slots=True)
class LabDomainAssessment:
    status: str
    scoped_ready: bool
    blockers: tuple[str, ...]
    manifest_sha256: str | None = None
    capture: NativeCapture | None = None
    @property
    def ready(self) -> bool:
        return False
    @property
    def atomic_snapshot_proven(self) -> bool:
        return False
    @property
    def production_domain_completeness_proven(self) -> bool:
        return False

def _raw(cell: dict) -> dict:
    return {key: cell[key] for key in ("userEnteredValue", "effectiveValue") if cell.get(key)}

def assess_native_domain_lab(payload: dict, manifest: dict, expected_manifest_sha256: str) -> LabDomainAssessment:
    """Expected hash must come from separately locked external lab custody.

    Each returned surface must expose the terminal guard sentinel in column zero. Expected
    cells are a complete sparse typed map of the frozen synthetic rectangle.
    Exact parity proves this model only; captures need not be provider atomic.
    """
    try:
        if not isinstance(payload, dict):
            raise CaptureRejected("INVALID_RESPONSE")
        if not isinstance(manifest, dict):
            raise CaptureRejected("INVALID_MANIFEST")
        digest = canonical_sha256(manifest)
        if type(expected_manifest_sha256) is not str or len(expected_manifest_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_manifest_sha256) or digest != expected_manifest_sha256:
            raise CaptureRejected("EXTERNAL_MANIFEST_HASH_MISMATCH")
        if manifest.get("contract_id") != CONTRACT_ID or manifest.get("scope") != "FINITE_SYNTHETIC_LAB_ONLY" or manifest.get("excluded_domain") != "EVERYTHING_OUTSIDE_DECLARED_BODY_AND_GUARD_IS_EXCLUDED_FROM_THIS_LAB_CLAIM":
            raise CaptureRejected("INVALID_LAB_SCOPE")
        surfaces = manifest.get("surfaces")
        if not isinstance(surfaces, list) or not surfaces:
            raise CaptureRejected("INVALID_MANIFEST")
        bounds = []
        expected = {}
        body_limits = {}
        sentinel_positions = {}
        for surface in surfaces:
            if not isinstance(surface, dict):
                raise CaptureRejected("INVALID_MANIFEST")
            title, body, guard, cols = (surface.get(k) for k in ("title", "body_rows", "guard_rows", "columns"))
            if type(title) is not str or not title or title in body_limits or any(type(v) is not int or v < 1 for v in (body, guard, cols)):
                raise CaptureRejected("INVALID_MANIFEST_BOUND")
            if guard != 3:
                raise CaptureRejected("EXACT_THREE_GUARD_ROWS_REQUIRED")
            bounds.append(SurfaceBound(title, body + guard, cols));body_limits[title]=body
            cells=surface.get("expected_cells")
            if not isinstance(cells,list):
                raise CaptureRejected("INVALID_EXPECTED_CELLS")
            for cell in cells:
                if not isinstance(cell,list) or len(cell)!=3:
                    raise CaptureRejected("INVALID_EXPECTED_CELL")
                row,col,value=cell
                if type(row) is not int or type(col) is not int or not 0<=row<body+guard or not 0<=col<cols or not isinstance(value,dict) or not _raw(value):
                    raise CaptureRejected("INVALID_EXPECTED_CELL")
                pos=(title,row,col)
                if pos in expected or set(value)-{"userEnteredValue","effectiveValue"}:
                    raise CaptureRejected("INVALID_EXPECTED_CELL")
                expected[pos]=value
            terminal=(title,body+guard-1,0)
            sentinel={"userEnteredValue":{"stringValue":"END_R4:"+title},"effectiveValue":{"stringValue":"END_R4:"+title}}
            if expected.get(terminal)!=sentinel or any(pos[0]==title and pos[1]>=body and pos!=terminal for pos in expected):
                raise CaptureRejected("INVALID_GUARD_SENTINEL_MODEL")
            sentinel_positions[title]=terminal
        # Decoder checks all returned positions/types and declared-area limit.
        decoded = decode_native_capture(payload,tuple(bounds))
        actual={}
        for sheet in payload["sheets"]:
            title=sheet["properties"]["title"]
            for grid in sheet["data"]:
                row0,col0=grid.get("startRow",0),grid.get("startColumn",0)
                for i,row in enumerate(grid.get("rowData",[])):
                    for j,cell in enumerate(row.get("values",[])):
                        raw=_raw(cell)
                        if raw: actual[(title,row0+i,col0+j)]=raw
        unexpected_guard=[pos for pos in actual if pos[1]>=body_limits[pos[0]] and pos!=sentinel_positions[pos[0]]]
        if unexpected_guard:
            return LabDomainAssessment("HOLD_REBIND",False,("POPULATED_GUARD_OUTSIDE_LAB_BODY",),digest)
        if any(actual.get(pos)!=expected[pos] for pos in sentinel_positions.values()):
            raise CaptureRejected("GUARD_TERMINATION_SENTINEL_MISSING_OR_CHANGED")
        if actual!=expected:
            raise CaptureRejected("FROZEN_TYPED_MODEL_MISMATCH_OR_TRUNCATION")
        body_capture = NativeCapture(tuple(SurfaceBound(b.title, body_limits[b.title], b.columns) for b in bounds), tuple(entry for entry in decoded.entries if entry[1] < body_limits[entry[0]]))
        return LabDomainAssessment("PASS_SCOPED",True,(),digest,body_capture)
    except (CaptureRejected,TypeError,ValueError,KeyError) as error:
        return LabDomainAssessment("HOLD",False,(str(error),))
