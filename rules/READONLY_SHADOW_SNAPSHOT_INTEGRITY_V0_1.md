# READONLY_SHADOW_SNAPSHOT_INTEGRITY_V0_1

Status: **PUBLIC BASELINE — IN-MEMORY / READ-ONLY / NO CONNECTOR**

## Purpose

Define a pure integrity contract for building deterministic multi-surface
read-only snapshots from already-materialized data.

This control validates only snapshot structure, schema binding, row shape,
scalar types, deterministic hashing, and version-marker atomicity.

It does not connect to any external system, load credentials, discover targets,
resolve business authority, execute allocation, or mutate data.

## Surface contract

Each read surface binds:

- non-empty surface ID;
- non-empty logical name;
- role = `SOURCE_OF_TRUTH` or `DERIVED_READ_ONLY`;
- non-empty ordered field list;
- unique field names;
- deterministic SHA-256 contract hash.

Blank or duplicate field names fail closed.

## Target snapshot contract

A target snapshot contract binds:

- non-empty target ID;
- non-empty schema version;
- non-empty ordered surface list;
- unique surface IDs;
- deterministic SHA-256 target-contract hash.

The supplied read set must match the target surface set exactly. Missing or
extra surfaces fail closed.

## Row normalization

Each row must expose exactly the contract field set.

Supported scalar values are:

- text;
- native integers;
- native booleans;
- `None`.

Floats and custom values are rejected.

Normalized rows preserve contract field order before hashing.

## Surface and snapshot hashes

Each surface snapshot hash binds:

- surface ID;
- surface contract hash;
- version marker;
- capture marker;
- normalized rows.

The multi-surface snapshot hash binds:

- snapshot ID;
- target ID;
- schema version;
- ordered surface hashes;
- atomicity result.

The same normalized inputs therefore produce the same hashes.

## Atomicity

Every surface read must carry a non-empty version marker.

A multi-surface snapshot is considered atomically consistent only when all
surface version markers are identical.

Version drift returns `HOLD` while preserving the computed snapshot as
diagnostic evidence with `atomic_snapshot_proven=False`.

## Scope boundary

This control does not:

- prove that an external read was authorized;
- perform a live read;
- validate credentials or permissions;
- infer source-pool or approval authority;
- execute replay logic;
- authorize a production write.

## Public boundary

Tests use synthetic short IDs and in-memory row mappings only. No external URL,
resource ID, credential, live connector, filesystem mutation, or network
capability is present.
