# Finite native lab model interface

`assess_native_domain_lab(payload, manifest, expected_manifest_sha256)` consumes a native CellData `sheets` response and a separately sealed external synthetic model. It performs no I/O or mutation.

Manifest shape:

- `contract_id`: `NATIVE_DOMAIN_LAB_CONTRACT_V0_1`.
- `scope`: `FINITE_SYNTHETIC_LAB_ONLY`.
- `excluded_domain`: `EVERYTHING_OUTSIDE_DECLARED_BODY_AND_GUARD_IS_EXCLUDED_FROM_THIS_LAB_CLAIM`.
- `surfaces`: list of `{title, body_rows, guard_rows: 3, columns, expected_cells}`.
- `expected_cells`: complete sparse list of `[zero_based_row, zero_based_column, raw_cell]`; raw_cell has only nonempty `userEnteredValue` and/or `effectiveValue`. Formula strings and effective typed values are retained. DataValidation and formatting are intentionally excluded from this parity contract; their correctness requires separate checks. Counts are derivable from this immutable hash-bound cell map, not caller completeness flags.

Each surface has exactly one allowed populated guard cell: final guard row, column zero, literal `END_R4:<title>` in both raw entered/effective slots. Other guard population returns `HOLD_REBIND`. Missing surfaces, missing terminal sentinel, silent omitted expected nonblank cells, conflicting typed content and extra body cells return HOLD. Data outside total declared body+guard rectangle is rejected by the existing decoder. A wholly omitted unknown universe outside the finite rectangle is explicitly outside this claim.

The caller must lock `canonical_sha256(manifest)` in separate external custody before execution; do not compute the expected hash from a newly captured response under test. The model may be constructed from a separately frozen baseline and deterministic synthetic mutation plan. This is lab trust, not authenticated provider authority.

PASS_SCOPED returns `scoped_ready=True`, `capture` containing body-only NativeCapture bounds/entries, and `ready=False`. Guard sentinels never reach Phu body validation. `atomic_snapshot_proven` and `production_domain_completeness_proven` remain False even on PASS. This closes only exact finite-model parity and sentinel-bounded response tests; no deployed completeness or operational acceptance is granted.

Run unit tests after installing the script beside the existing decoder in either repository with `python -m unittest discover -s tests -p test_native_capture_domain_lab_v0_1.py`.
