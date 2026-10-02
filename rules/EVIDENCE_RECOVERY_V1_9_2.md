# Evidence Recovery and Identity — SOP Inbound v1.9.2

Status: **public-safe enforcement contract**.

This contract is a prospective hardening layer for warehouse inbound evidence.
It contains no Production locator data, source files, serial values, credentials,
or live-read/write authority.

## G1A — recovery before missing

SEARCH_ZERO_IS_NOT_MISSING.

A zero-result text lookup does not prove that source evidence is absent. Before
a missing-source conclusion, an implementation must exhaust applicable recovery
stages: current attachment inventory, project/library inventory, time-window
listing independent of filename, visual candidate inspection, historical
evidence identity, deterministic hash comparison, and canonical-store lookup.

The only true not-found terminal status is
SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY.

Other distinct states are:

- SOURCE_RECOVERY_IN_PROGRESS
- SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED
- SOURCE_FOUND_NOT_CANONICAL
- SOURCE_BYTES_UNAVAILABLE
- SOURCE_HASH_MISMATCH
- SOURCE_ARCHIVED_VERIFIED

One unresolved evidence identity has exactly one active RecoveryRoot.

## G1B — stable identity binding

Accepted evidence is bound by the strongest available immutable tuple:
EvidenceID, provider/library identity, path, original name, document metadata,
SHA-256, byte size, MIME, canonical object identity, canonical parent and
provider read-back markers.

A working or privacy-reduced derivative has a distinct identity and cannot
replace the original source-of-truth object.

Recovery is read-only to inventory. Discovery alone never authorizes a
Production stock mutation.

## G1C — canonical archive/read-back

Once a candidate is accepted, the same immutable bytes must satisfy the
existing canonical archive and provider-read-back controls before an
evidence-dependent mutation can close, or the workflow remains fail-closed
under the narrowest accurate HOLD reason.

## Mandatory regression pattern

The public fixture mirrors the PX62750 incident pattern without Production
identifiers:

1. source is an image-like artifact with a random filename;
2. document-text search returns zero;
3. time-window project/library inventory finds the candidate;
4. visual inspection identifies it;
5. candidate SHA-256 equals the previously bound historical hash;
6. recovery returns SOURCE_ARCHIVED_VERIFIED;
7. no false missing-evidence HOLD is allowed.

## Historical outbound proof boundary

Post-close fail-closed replay is not retroactive proof that the original
pre-write source-rank gate passed. If the historical pre-write snapshot is not
available, the strongest admissible classification is
POSTCLOSE_FAIL_CLOSED_ONLY.

This rule preserves prior audit defects instead of rewriting history.
