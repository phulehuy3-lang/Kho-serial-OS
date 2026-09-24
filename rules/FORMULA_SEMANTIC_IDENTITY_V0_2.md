# FORMULA_SEMANTIC_IDENTITY_V0_2

Status: **CURRENT MAIN — CONSERVATIVE / IN-MEMORY / READ-ONLY**

## Purpose

Supersede Formula Semantic Identity V0.1 for current main-branch callers without
rewriting V0.1 history or its hash vectors.

V2 prevents semantic collisions caused by uppercasing identifiers/literals or
collapsing meaningful whitespace inside literals and quoted sheet names.

## Compatibility and migration

- V0.1 remains frozen for historical/checkpoint compatibility.
- `SHA256_CANONICAL_QUERY_SEMANTICS_V1` and
  `FORMULA_QUERY_SEMANTIC_HASH_V1` are not modified.
- Current inbound profile callers migrate to V2.
- V2 uses:
  - `SHA256_CONSERVATIVE_QUERY_SEMANTICS_V2`
  - `FORMULA_QUERY_SEMANTIC_HASH_V2`
- Existing V1 hashes must never be silently reinterpreted as V2 hashes.
- The frozen `v0.2.0` tag is not moved or rewritten.

## Source normalization

V2 accepts only verified simple source-reference forms.

It may normalize:

- surrounding whitespace;
- absolute-reference dollar signs;
- cell/column reference letter case;
- redundant quotes around a simple sheet identifier.

It must preserve sheet identifier case and meaningful internal whitespace.

Therefore:

- `'SOURCE_TABLE'!$A:$Z` may equal `SOURCE_TABLE!A:Z`;
- `'Lot A'!A1:B10` must not equal `'LotA'!A1:B10`.

Unsupported source syntax returns HOLD.

## Query normalization

V2 supports the conservative subset:

`SELECT identifier (, identifier)* [WHERE condition ((AND|OR) condition)*]`

A condition is:

`identifier comparison operand`

Operands may be:

- identifier;
- ASCII numeric literal;
- exact single-quoted literal;
- `TRUE` or `FALSE`.

V2 normalizes only recognized query keywords and insignificant whitespace around
supported syntax.

It must not uppercase or whitespace-collapse:

- identifiers;
- single-quoted literals.

Consequently:

- `'hold'` differs from `'HOLD'`;
- `'A  B'` differs from `'A B'`;
- identifier `A` differs from `a`.

Unsupported functions, clauses, expressions, parentheses or other structures
fail closed instead of being guessed equivalent.

## Semantic hash

The V2 semantic hash binds:

- V2 hash-contract ID;
- conservative normalized source;
- conservative normalized query text;
- header-row count.

The formula-contract hash additionally binds:

- formula contract ID;
- V2 hash algorithm ID;
- V2 semantic hash;
- exact exported fallback literal.

V2 hashes are a new compatibility domain and must not be compared as V1 hashes.

## Supported formula representations

V2 recognizes only the same fully matched representations required by the
current warehouse formula control:

1. native `QUERY(source, "query text", header_rows)`, comma or semicolon;
2. verified exported IFERROR/DUMMYFUNCTION wrapper.

Additional executable outer logic or unsupported query/source grammar returns
HOLD.

## Authority boundary

A V2 PASS proves only formula semantic identity with the declared V2 contract.

It does not authorize live reads, release, mutation or Production write.

`ProductionWriteAuthorized=False` remains invariant.
