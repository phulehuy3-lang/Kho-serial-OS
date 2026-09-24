"""Conservative Formula Semantic Identity V2.

V1 remains frozen for historical hash compatibility. V2 preserves literals and
identifiers, normalizes only explicitly supported syntax, and fails closed for
unsupported query structures. No external I/O is performed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re


PASS = "PASS"
HOLD = "HOLD"

NATIVE_QUERY = "NATIVE_QUERY"
EXPORTED_QUERY_WRAPPER = "EXPORTED_QUERY_WRAPPER"
UNRECOGNIZED = "UNRECOGNIZED"

FORMULA_SEMANTIC_HASH_ALGORITHM_V2 = "SHA256_CONSERVATIVE_QUERY_SEMANTICS_V2"
FORMULA_SEMANTIC_HASH_CONTRACT_ID_V2 = "FORMULA_QUERY_SEMANTIC_HASH_V2"

_NATIVE_QUERY_PATTERN = re.compile(
    r'^\s*=?\s*QUERY\(\s*(?P<source>[^,;]+?)\s*[,;]\s*'
    r'"(?P<query>[^"]*)"\s*[,;]\s*'
    r'(?P<header>\d+)\s*\)\s*$',
    re.IGNORECASE | re.DOTALL,
)

_EXPORTED_QUERY_PATTERN = re.compile(
    r'^\s*=?\s*IFERROR\(\s*__XLUDF\.DUMMYFUNCTION\(\s*'
    r'"QUERY\(\s*(?P<source>[^,;]+?)\s*,\s*'
    r'"""(?P<query>.*?)""\s*,\s*'
    r'(?P<header>\d+)\s*\)"\s*\)\s*,\s*'
    r'"(?P<fallback>[^"]*)"\s*\)\s*$',
    re.IGNORECASE | re.DOTALL,
)

_SIMPLE_SHEET_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_COLUMN_RANGE_PATTERN = re.compile(r"\$?[A-Za-z]+:\$?[A-Za-z]+\Z")
_CELL_RANGE_PATTERN = re.compile(
    r"\$?[A-Za-z]+\$?\d+:\$?[A-Za-z]+\$?\d+\Z"
)
_SINGLE_CELL_PATTERN = re.compile(r"\$?[A-Za-z]+\$?\d+\Z")
_QUERY_KEYWORDS = {"SELECT", "WHERE", "AND", "OR", "TRUE", "FALSE"}


@dataclass(frozen=True, slots=True)
class FormulaSemanticContractV2:
    contract_id: str
    source: str
    query_text: str
    header_rows: int
    exported_fallback_literal: str
    contract_hash: str


@dataclass(frozen=True, slots=True)
class FormulaSemanticAssessment:
    status: str
    ready: bool
    blocking_reasons: tuple[str, ...]
    representation: str
    observed_semantic_hash: str | None
    expected_semantic_hash: str | None


def _clean(value: object) -> str:
    return value.strip() if type(value) is str else ""


def _canonical_range_text(value: str) -> str | None:
    if not (
        _COLUMN_RANGE_PATTERN.fullmatch(value)
        or _CELL_RANGE_PATTERN.fullmatch(value)
        or _SINGLE_CELL_PATTERN.fullmatch(value)
    ):
        return None
    without_absolute = value.replace("$", "")
    return re.sub(
        r"[A-Za-z]+",
        lambda match: match.group(0).upper(),
        without_absolute,
    )


def normalize_query_source_v2(value: object) -> str | None:
    """Normalize only verified source-reference syntax.

    Sheet identifiers preserve case and internal whitespace. Quotes are removed
    only for a simple identifier where quoting is semantically redundant.
    """

    if type(value) is not str:
        return None
    source = value.strip()
    if not source:
        return None

    if "!" not in source:
        return _canonical_range_text(source)

    if source.count("!") != 1:
        return None
    sheet_text, range_text = source.split("!", 1)
    sheet_text = sheet_text.strip()
    range_text = range_text.strip()

    if sheet_text.startswith("'"):
        if len(sheet_text) < 2 or not sheet_text.endswith("'"):
            return None
        inner = sheet_text[1:-1]
        if not inner or "'" in inner:
            return None
        canonical_sheet = (
            inner
            if _SIMPLE_SHEET_PATTERN.fullmatch(inner)
            else "'" + inner + "'"
        )
    else:
        if not _SIMPLE_SHEET_PATTERN.fullmatch(sheet_text):
            return None
        canonical_sheet = sheet_text

    canonical_range = _canonical_range_text(range_text)
    if canonical_range is None:
        return None
    return canonical_sheet + "!" + canonical_range


def _tokenize_query_v2(
    value: object,
) -> tuple[tuple[str, str], ...] | None:
    if type(value) is not str:
        return None
    query = value.strip()
    if not query:
        return None

    tokens: list[tuple[str, str]] = []
    index = 0
    while index < len(query):
        char = query[index]

        if char.isspace():
            index += 1
            continue

        if char == "'":
            end = index + 1
            while end < len(query):
                if query[end] == "'":
                    if end + 1 < len(query) and query[end + 1] == "'":
                        end += 2
                        continue
                    break
                end += 1
            if end >= len(query):
                return None
            tokens.append(("LITERAL", query[index : end + 1]))
            index = end + 1
            continue

        if char.isascii() and (char.isalpha() or char == "_"):
            end = index + 1
            while (
                end < len(query)
                and query[end].isascii()
                and (query[end].isalnum() or query[end] == "_")
            ):
                end += 1
            raw = query[index:end]
            keyword = raw.upper()
            if keyword in _QUERY_KEYWORDS:
                tokens.append(("KEYWORD", keyword))
            else:
                tokens.append(("IDENTIFIER", raw))
            index = end
            continue

        if char.isascii() and char.isdigit():
            end = index + 1
            while (
                end < len(query)
                and query[end].isascii()
                and query[end].isdigit()
            ):
                end += 1
            if end < len(query) and query[end] == ".":
                decimal_end = end + 1
                while (
                    decimal_end < len(query)
                    and query[decimal_end].isascii()
                    and query[decimal_end].isdigit()
                ):
                    decimal_end += 1
                if decimal_end == end + 1:
                    return None
                end = decimal_end
            tokens.append(("NUMBER", query[index:end]))
            index = end
            continue

        if char == ",":
            tokens.append(("COMMA", ","))
            index += 1
            continue

        if index + 1 < len(query) and query[index : index + 2] in {
            "<=",
            ">=",
            "<>",
        }:
            tokens.append(("OPERATOR", query[index : index + 2]))
            index += 2
            continue

        if char in {"=", "<", ">"}:
            tokens.append(("OPERATOR", char))
            index += 1
            continue

        return None

    return tuple(tokens)


def normalize_query_text_v2(value: object) -> str | None:
    """Canonicalize the supported conservative QUERY subset.

    Supported grammar:
      SELECT identifier (, identifier)*
      [WHERE identifier comparison operand ((AND|OR) condition)*]

    Operands may be identifiers, ASCII numeric literals, exact single-quoted
    literals, or TRUE/FALSE. Identifier and literal text are never uppercased or
    whitespace-collapsed.
    """

    tokens = _tokenize_query_v2(value)
    if not tokens:
        return None

    index = 0

    def take(kind: str, exact: str | None = None) -> str | None:
        nonlocal index
        if index >= len(tokens) or tokens[index][0] != kind:
            return None
        current = tokens[index][1]
        if exact is not None and current != exact:
            return None
        index += 1
        return current

    if take("KEYWORD", "SELECT") is None:
        return None

    selected: list[str] = []
    identifier = take("IDENTIFIER")
    if identifier is None:
        return None
    selected.append(identifier)

    while index < len(tokens) and tokens[index][0] == "COMMA":
        index += 1
        identifier = take("IDENTIFIER")
        if identifier is None:
            return None
        selected.append(identifier)

    canonical = "SELECT " + ",".join(selected)
    if index == len(tokens):
        return canonical

    if take("KEYWORD", "WHERE") is None:
        return None

    conditions: list[str] = []
    joins: list[str] = []

    while True:
        left = take("IDENTIFIER")
        operator = take("OPERATOR")
        if left is None or operator is None or index >= len(tokens):
            return None

        kind, right = tokens[index]
        if kind in {"IDENTIFIER", "NUMBER", "LITERAL"}:
            index += 1
        elif kind == "KEYWORD" and right in {"TRUE", "FALSE"}:
            index += 1
        else:
            return None

        conditions.append(f"{left} {operator} {right}")

        if index == len(tokens):
            break
        if tokens[index][0] != "KEYWORD" or tokens[index][1] not in {
            "AND",
            "OR",
        }:
            return None
        joins.append(tokens[index][1])
        index += 1

    canonical += " WHERE " + conditions[0]
    for join, condition in zip(joins, conditions[1:]):
        canonical += f" {join} {condition}"
    return canonical


def compute_formula_semantic_hash_v2(
    *,
    source: str,
    query_text: str,
    header_rows: int,
) -> str:
    normalized_source = normalize_query_source_v2(source)
    normalized_query = normalize_query_text_v2(query_text)
    if normalized_source is None:
        raise ValueError("unsupported Formula Semantic Identity V2 source")
    if normalized_query is None:
        raise ValueError("unsupported Formula Semantic Identity V2 query")

    payload = {
        "hash_contract_id": FORMULA_SEMANTIC_HASH_CONTRACT_ID_V2,
        "source": normalized_source,
        "query_text": normalized_query,
        "header_rows": header_rows,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contract_hash_payload_v2(
    contract: FormulaSemanticContractV2,
) -> dict[str, object]:
    return {
        "contract_id": contract.contract_id,
        "hash_algorithm": FORMULA_SEMANTIC_HASH_ALGORITHM_V2,
        "hash_contract_id": FORMULA_SEMANTIC_HASH_CONTRACT_ID_V2,
        "semantic_hash": compute_formula_semantic_hash_v2(
            source=contract.source,
            query_text=contract.query_text,
            header_rows=contract.header_rows,
        ),
        "exported_fallback_literal": contract.exported_fallback_literal,
    }


def compute_formula_contract_hash_v2(
    contract: FormulaSemanticContractV2,
) -> str:
    encoded = json.dumps(
        _contract_hash_payload_v2(contract),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def with_computed_formula_contract_hash_v2(
    *,
    contract_id: str,
    source: str,
    query_text: str,
    header_rows: int,
    exported_fallback_literal: str,
) -> FormulaSemanticContractV2:
    provisional = FormulaSemanticContractV2(
        contract_id=contract_id,
        source=source,
        query_text=query_text,
        header_rows=header_rows,
        exported_fallback_literal=exported_fallback_literal,
        contract_hash="",
    )
    return FormulaSemanticContractV2(
        contract_id=provisional.contract_id,
        source=provisional.source,
        query_text=provisional.query_text,
        header_rows=provisional.header_rows,
        exported_fallback_literal=provisional.exported_fallback_literal,
        contract_hash=compute_formula_contract_hash_v2(provisional),
    )


def validate_formula_semantic_contract_v2(
    contract: object,
) -> tuple[str, ...]:
    blockers: list[str] = []

    if type(contract) is not FormulaSemanticContractV2:
        return ("FORMULA_SEMANTICS_V2:CONTRACT_SHAPE_INVALID",)

    if not _clean(contract.contract_id):
        blockers.append("FORMULA_SEMANTICS_V2:CONTRACT_ID_MISSING")
    if normalize_query_source_v2(contract.source) is None:
        blockers.append("FORMULA_SEMANTICS_V2:SOURCE_UNSUPPORTED")
    if normalize_query_text_v2(contract.query_text) is None:
        blockers.append("FORMULA_SEMANTICS_V2:QUERY_UNSUPPORTED")
    if (
        type(contract.header_rows) is not int
        or contract.header_rows < 0
    ):
        blockers.append("FORMULA_SEMANTICS_V2:HEADER_ROWS_INVALID")
    if type(contract.exported_fallback_literal) is not str:
        blockers.append("FORMULA_SEMANTICS_V2:FALLBACK_LITERAL_INVALID")

    if not blockers:
        if contract.contract_hash != compute_formula_contract_hash_v2(contract):
            blockers.append("FORMULA_SEMANTICS_V2:CONTRACT_HASH_MISMATCH")

    return tuple(sorted(set(blockers)))


def _parse_formula_v2(
    formula: str,
) -> tuple[str, str, str, int, str | None] | None:
    native = _NATIVE_QUERY_PATTERN.fullmatch(formula)
    if native is not None:
        return (
            NATIVE_QUERY,
            native.group("source"),
            native.group("query"),
            int(native.group("header")),
            None,
        )

    exported = _EXPORTED_QUERY_PATTERN.fullmatch(formula)
    if exported is not None:
        return (
            EXPORTED_QUERY_WRAPPER,
            exported.group("source"),
            exported.group("query"),
            int(exported.group("header")),
            exported.group("fallback"),
        )

    return None


def assess_formula_semantic_identity_v2(
    *,
    formula: object,
    contract: object,
) -> FormulaSemanticAssessment:
    """Compare one materialized formula against a conservative V2 contract."""

    blockers = list(validate_formula_semantic_contract_v2(contract))
    if type(contract) is not FormulaSemanticContractV2:
        return FormulaSemanticAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            representation=UNRECOGNIZED,
            observed_semantic_hash=None,
            expected_semantic_hash=None,
        )

    if type(formula) is not str or not formula.strip():
        blockers.append("FORMULA_SEMANTICS_V2:FORMULA_MISSING")
        return FormulaSemanticAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            representation=UNRECOGNIZED,
            observed_semantic_hash=None,
            expected_semantic_hash=None,
        )

    if blockers:
        return FormulaSemanticAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            representation=UNRECOGNIZED,
            observed_semantic_hash=None,
            expected_semantic_hash=None,
        )

    expected_hash = compute_formula_semantic_hash_v2(
        source=contract.source,
        query_text=contract.query_text,
        header_rows=contract.header_rows,
    )

    parsed = _parse_formula_v2(formula)
    if parsed is None:
        return FormulaSemanticAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=(
                "FORMULA_SEMANTICS_V2:UNSUPPORTED_REPRESENTATION",
            ),
            representation=UNRECOGNIZED,
            observed_semantic_hash=None,
            expected_semantic_hash=expected_hash,
        )

    representation, source, query_text, header_rows, fallback = parsed
    observed_source = normalize_query_source_v2(source)
    observed_query = normalize_query_text_v2(query_text)

    if observed_source is None:
        blockers.append("FORMULA_SEMANTICS_V2:UNSUPPORTED_SOURCE_STRUCTURE")
    if observed_query is None:
        blockers.append("FORMULA_SEMANTICS_V2:UNSUPPORTED_QUERY_STRUCTURE")

    observed_hash: str | None = None
    if observed_source is not None and observed_query is not None:
        observed_hash = compute_formula_semantic_hash_v2(
            source=source,
            query_text=query_text,
            header_rows=header_rows,
        )

    expected_source = normalize_query_source_v2(contract.source)
    expected_query = normalize_query_text_v2(contract.query_text)

    if observed_source is not None and observed_source != expected_source:
        blockers.append("FORMULA_SEMANTICS_V2:SOURCE_MISMATCH")
    if observed_query is not None and observed_query != expected_query:
        blockers.append("FORMULA_SEMANTICS_V2:QUERY_TEXT_MISMATCH")
    if header_rows != contract.header_rows:
        blockers.append("FORMULA_SEMANTICS_V2:HEADER_ROWS_MISMATCH")
    if (
        representation == EXPORTED_QUERY_WRAPPER
        and fallback != contract.exported_fallback_literal
    ):
        blockers.append("FORMULA_SEMANTICS_V2:FALLBACK_LITERAL_MISMATCH")
    if observed_hash is not None and observed_hash != expected_hash:
        blockers.append("FORMULA_SEMANTICS_V2:SEMANTIC_HASH_MISMATCH")

    if blockers:
        return FormulaSemanticAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            representation=representation,
            observed_semantic_hash=observed_hash,
            expected_semantic_hash=expected_hash,
        )

    return FormulaSemanticAssessment(
        status=PASS,
        ready=True,
        blocking_reasons=(),
        representation=representation,
        observed_semantic_hash=observed_hash,
        expected_semantic_hash=expected_hash,
    )
