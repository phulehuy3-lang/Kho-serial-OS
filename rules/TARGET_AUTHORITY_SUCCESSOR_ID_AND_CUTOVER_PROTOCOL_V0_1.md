# TARGET_AUTHORITY_SUCCESSOR_ID_AND_CUTOVER_PROTOCOL_V0_1

Status: **ACTIVE FOR SUCCESSOR MATERIALIZATION AFTER MERGE**

Scope: private target-authority lifecycle records only.

This protocol is prospective. It does not claim or reinterpret how any historical
`TA1_...` identifier was generated.

## 1. Successor authority identifier

A new successor `target_authority_id` MUST use:

`TA1_<32 lowercase hexadecimal characters>`

The 32-hex suffix MUST be generated from 16 cryptographically secure random
bytes (128 bits), e.g. a CSPRNG equivalent of Python `secrets.token_hex(16)`.

The identifier MUST NOT be derived from or encode:

- target locator IDs or hashes;
- Google Drive file/folder/provider IDs;
- account, IAM, WIF, service-account or credential identifiers;
- worksheet, serial, stock, ledger or other business payload;
- predecessor hashes or private provider revision markers.

Before materialization, the candidate ID MUST be checked against the private
authority registry for both exact filename identity and embedded
`target_authority_id`. Collision => discard and generate a new candidate.
Existing records MUST NOT be overwritten to resolve a collision.

## 2. Successor binding

The successor record MUST:

- retain the exact predecessor locator ref/hash;
- set `supersedes_authority_id` to the predecessor authority ID;
- bind the approved new warehouse schema and five-surface registry generation;
- start at `lifecycle_state=DRAFT`;
- start at `independent_readback_state=PENDING`;
- preserve the existing owner/approver/reviewer authority refs and logical target alias.

## 3. Lifecycle before cutover

The successor MUST pass:

`DRAFT -> APPROVED -> independent read-back PASS`

before any cutover mutation.

Every transition MUST recompute `authority_record_hash` from canonical compact
JSON with `authority_record_hash` omitted from the hash input.

## 4. Fail-closed cutover ordering

To maintain **at most one ACTIVE authority at every observable checkpoint**:

1. verify predecessor is the sole ACTIVE authority and successor is APPROVED + PASS;
2. transition predecessor `ACTIVE -> SUPERSEDED`;
3. set predecessor `revocation_epoch_ref` to the private supersession event;
4. recompute/read back predecessor hash;
5. verify ACTIVE count = 0;
6. transition successor `APPROVED -> ACTIVE`;
7. set successor `activation_epoch_ref` to the private activation event;
8. recompute/read back successor hash;
9. verify ACTIVE count = 1 and the ACTIVE authority is the successor.

The temporary zero-ACTIVE checkpoint is fail-closed and permitted. Two ACTIVE
records are never permitted.

If successor activation fails after predecessor supersession, do not silently
reactivate the predecessor. Remain at zero ACTIVE and HOLD until explicit
governed recovery.

## 5. Locked boundaries

This protocol does not authorize:

- Production worksheet/business-payload reads;
- MASTER LIVE business-data mutation;
- locator mutation;
- Drive permission/sharing mutation;
- IAM/WIF/service-account/credential mutation;
- executable acquisition;
- Production writer enablement.

Locked:

- `LiveReadAuthorized=False`
- `ExecutableAcquisitionAuthorized=False`
- `ProductionWriteAuthorized=False`
