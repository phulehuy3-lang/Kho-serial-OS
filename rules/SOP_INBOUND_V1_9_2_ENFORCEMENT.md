# Prospective inbound evidence enforcement — v1.9.2

Controls: `CTRL_EVIDENCE_RECOVERY_BEFORE_MISSING_V1` and
`CTRL_EVIDENCE_IDENTITY_BINDING_V1`.

Use `validate_inbound_transition_v1_9_2` for a v1.9.2 inbound caller, including
both PREPARED -> PREWRITE_SEALED and PREWRITE_SEALED -> WRITTEN. The existing
`validate_transition` API remains a legacy v1.8 interface. It does not claim
v1.9.2 compliance. No production writer or provider adapter exists here.

## G1A discovery

`SEARCH_ZERO_IS_NOT_MISSING`. A caller supplies already-acquired candidate
records. A successful unique candidate resolves G1A without exhaustively
searching every provider. For absence, require ordered, evidence-key-bound,
distinct receipts for CURRENT_ATTACHMENTS, PROJECT_LIBRARY_PATH,
TIME_WINDOW_INVENTORY, VISUAL_INSPECTION, HISTORICAL_IDENTITY, HASH_COMPARISON,
and CANONICAL_LOOKUP. Each must be NO_MATCH, with text search hits zero.
UNAVAILABLE, incomplete discovery, positive hits, or inaccessible known bytes
never prove absence. A result permits classification only; it does not create
or release a warehouse HOLD. The existing effective HOLD propagation controls
remain mandatory for an actual HOLD operation.

## G1B identity

Bind evidence key, Library ID/path, original name, document number/date,
supplier role, SHA-256, byte size, MIME, provider creation timestamp and grade.
Compute SHA-256 and size from immutable source bytes; compare any known
historical hash. Ambiguous candidates block. Every unresolved evidence key has
exactly one active RecoveryRoot; search attempts stay events under that root.

## G1C canonical archive readback

Bind canonical file/folder IDs, evidence key, distinct readback receipt and
provider timestamp. Require byte-for-byte source/readback equality. Missing
archive yields SOURCE_FOUND_NOT_CANONICAL; changed bytes yield
SOURCE_HASH_MISMATCH. A trusted external caller is responsible for obtaining
real provider records and authenticating them. This pure evaluator validates
bindings, not the authenticity of arbitrary caller attestations.

The composite prewrite gate also requires exact stable-ID resolution, current
scope generation and a strictly typed PASS result from the existing warehouse
gates. Reevaluate immediately before WRITTEN. This supplements immutable
prewrite manifests, formula protection and descendant/session controls;
it does not replace them or grant inventory-write authority.

## Historical boundary

Preserve historical false closes, manual gates and prewrite omissions as
append-only evidence. Post-close fail-closed proof is POSTCLOSE_FAIL_CLOSED_ONLY.
A historical prewrite snapshot permits replay, never automatically historical
rank PASS. Remediated execution must never become CLEAN_PASS retrospectively.

## Regression and limits

`python -m unittest discover -s tests -p 'test_evidence_recovery_v1_9_2.py' -v`
executes a disposable synthetic workflow and negative cases. The public fixture
uses random image naming and zero text hits with computed hash and matching
in-memory archive readback. No real document, serial, customer or provider IDs
are published. Tests exercise gate enforcement; they do not prove live Library
search, live canonical archiving, or a stock mutation under v1.9.2.

The earlier `evidence_recovery_v192` evidence-only API is retained for historical
compatibility, not full v1.9.2 prewrite compliance. Use the composite caller above.

## Online postcommit retry handoff (08/10/2026)

This section aligns repository roles with the canonical ONLINE warehouse
operating guidance (RULE-0032, journal NJ-0337) and does **not** create another
SOP, implement provider access, or grant Production mutation authority.

- **Authority:** MASTER LIVE Google Sheets remains the business source of truth.
  SOP_INBOUND_STANDARD_V1_9_2 (G0-G18) and its existing evidence, prewrite
  manifest, serial TEXT/overlap/HOLD, cross-layer readback, audit and closure
  gates remain mandatory for each actual inbound. RULE-0032 organizes routine
  operations into READ -> PREPARE -> COMMIT -> VERIFY without relaxing gates.
- **Ownership:** Kho-serial-OS validates warehouse/schema/evidence invariants,
  and emits bounded intents. Phu_OS owns connected-session orchestration and
  the pure postcommit retry decision (Phu_OS PR #120). Do not copy a writer or
  UI-retry loop into Kho-serial-OS: there is no warehouse provider writer here.
- **After uncertain commit:** on timeout, lost WRITE_ACK, rejected control
  write or operator UI Retry, the caller must perform a fresh provider-native
  READ by stable transaction/document/event identity **before** deciding.
  If any business/log/ledger/interval/eligible side effect is present, never
  re-issue the business mutation. COMMITTED_PENDING_READBACK is
  RECONCILE_ONLY, not a success/close verdict. CLOSED exact-once records
  forbid duplicate writes; unknown or partial commit, incomplete evidence,
  identity conflict, stale source or blocked provider read must HOLD.
- **Readback:** a sparse Google Sheets rowData for a requested blank range is
  not alone proof of control drift. Resolve requested bounds and typed CellData;
  when completeness/identity cannot be proven, HOLD. Do not reconstruct a
  prewrite manifest or evidence hash after the commit. Historical defects
  remain visible and any corrective write needs an independently authorized
  append-only remediation.
- **Separation of acceptance:** Phu_OS PR #120 merged with synthetic CI PASS,
  but its guard is **not** demonstrated as a deployed ChatGPT ONLINE runtime
  hook or Operational TEST V2 native E2E. TEST M5 T03-T36 remain NOT_RUN,
  mutation/Production gates remain false. Legitimate daily LIVE work can
  follow its own approved canonical SOP without Desktop or TEST completion;
  live write authority must never be inferred from synthetic tests.
- **Regression trigger:** for future changes to postcommit identity/parity
  contracts, test the exact lost-ACK -> two-UI-Retries -> incomplete
  audit/reconciliation chain. Record the native write-attempt count and
  provider receipts before claiming deployed anti-replay protection.

This is a **documentation/contract handoff only**, not code-level enforcement
or acceptance certification for the separate live online path.
