# Native capture lab v0.1

The adapter consumes supplied native CellData in memory; it performs no network
request, local write, authentication or provider acquisition. Source registration
v1.1 is a new external synthetic generation; v1.0 remains historical and unchanged.
Native source identity differs from the XLSX byte SHA. Connected locators and
capture payloads remain outside GitHub.

Use decode_native_capture with an explicit tuple of zero-based, origin-anchored
SurfaceBound objects. Bounds are lab declarations, not authenticated authority.
The decoder checks surface set, typed values, grid positions, duplicates and a
6000-cell default declared-area cap. Trailing absent cells mean missing within the
declared rectangle, not confirmed domain enumeration. Omitted formula effective
values remain missing; no cached value or external recalculation proof is invented.

NativeCaptureLabAdapter exposes the same selected-cell/row/anchor read methods as
the OOXML adapter. It can feed validate_production_snapshot for the versioned
INTERVAL-only mapping. Native error enums map to spreadsheet error literals.
Numeric serials are never converted to text; pseudo-booleans are rejected.

atomic_snapshot_proven=False and domain_completeness_proven=False always.
The legacy validator's READY_FOR_RELEASE is diagnostic and cannot grant runtime
or operational authority. external_recalculation_proven remains False.

Promotion requires separately reviewed domain/exclusion and response-limit
contracts, actual enumeration and provider-consistency verification, zero-write
runtime attestation and tamper-evident receipts. Equal markers/timestamps and
caller booleans are not provider proofs. No live-read/acquisition/write authority
is changed by this module or registry.

Kho additionally exposes validate_native_v2_lab, bound to the canonical V2 schema
hash. It checks exact headers/types, declared record cardinality, ID uniqueness,
interval order/quantity and source-derived equality. PASS_SCHEMA_ONLY never means
ready. Category/domain semantics, active-HOLD authority and complete-universe
claims remain unproved; this is not a Production acquisition adapter.

The Phu assess_native_capture_lab wrapper always returns operational HOLD/ready=False,
while retaining its mapping_report diagnostics. Callers must not promote the
inner mapping report as authorization.
