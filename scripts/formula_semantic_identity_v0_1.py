"""Pure formula semantic-identity validation.

Inputs are already-materialized formula strings. No external I/O is performed.
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

FORMULA_SEMANTIC_HASH_ALGORITHM = "SHA256_CANONICAL_QUERY_SEMANTICS_V1"
FORMULA_SEMANTIC_HASH_CONTRACT_ID = "FORMULA_QUERY_SEMANTIC_HASH_V1"


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


@dataclass(frozen=True, slots=True)
class FormulaSemanticContract:
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
    return value.strip() if isinstance(value, str) else ""


def normalize_query_source(value: str) -> str:
    normalized = re.sub(r"\$", "", "".join(value.upper().split()))
    if normalized.startswith("'") and "'!" in normalized:
        sheet, tail = normalized.split("'!", 1)
        normalized = sheet[1:] + "!" + tail
    return normalized


def normalize_query_text(value: str) -> str:
    normalized = " ".join(value.upper().split())
    normalized = re.sub(r"\s*,\s*", ",", normalized)
    normalized = re.sub(r"\s*(<=|>=|<>|=|<|>)\s*", r" \1 ", normalized)
    return " ".join(normalized.split())


def compute_formula_semantic_hash(
    *,
    source: str,
    query_text: str,
    header_rows: int,
) -> str:
    payload = {
        "hash_contract_id": FORMULA_SEMANTIC_HASH_CONTRACT_ID,
        "source": normalize_query_source(source),
        "query_text": normalize_query_text(query_text),
        "header_rows": header_rows,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contract_hash_payload(
    contract: FormulaSemanticContract,
) -> dict[str, object]:
    return {
        "contract_id": contract.contract_id,
        "hash_algorithm": FORMULA_SEMANTIC_HASH_ALGORITHM,
        "hash_contract_id": FORMULA_SEMANTIC_HASH_CONTRACT_ID,
        "semantic_hash": compute_formula_semantic_hash(
            source=contract.source,
            query_text=contract.query_text,
            header_rows=contract.header_rows,
        ),
        "exported_fallback_literal": contract.exported_fallback_literal,
    }


def compute_formula_contract_hash(
    contract: FormulaSemanticContract,
) -> str:
    encoded = json.dumps(
        _contract_hash_payload(contract),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def with_computed_formula_contract_hash(
    *,
    contract_id: str,
    source: str,
    query_text: str,
    header_rows: int,
    exported_fallback_literal: str,
) -> FormulaSemanticContract:
    provisional = FormulaSemanticContract(
        contract_id=contract_id,
        source=source,
        query_text=query_text,
        header_rows=header_rows,
        exported_fallback_literal=exported_fallback_literal,
        contract_hash="",
    )
    return FormulaSemanticContract(
        contract_id=provisional.contract_id,
        source=provisional.source,
        query_text=provisional.query_text,
        header_rows=provisional.header_rows,
        exported_fallback_literal=provisional.exported_fallback_literal,
        contract_hash=compute_formula_contract_hash(provisional),
    )


def validate_formula_semantic_contract(
    contract: FormulaSemanticContract,
) -> tuple[str, ...]:
    blockers: list[str] = []

    if not _clean(contract.contract_id):
        blockers.append("FORMULA_SEMANTICS:CONTRACT_ID_MISSING")
    if not _clean(contract.source):
        blockers.append("FORMULA_SEMANTICS:SOURCE_MISSING")
    if not _clean(contract.query_text):
        blockers.append("FORMULA_SEMANTICS:QUERY_TEXT_MISSING")
    if (
        not isinstance(contract.header_rows, int)
        or isinstance(contract.header_rows, bool)
        or contract.header_rows < 0
    ):
        blockers.append("FORMULA_SEMANTICS:HEADER_ROWS_INVALID")
    if not isinstance(contract.exported_fallback_literal, str):
        blockers.append("FORMULA_SEMANTICS:FALLBACK_LITERAL_INVALID")

    if not blockers:
        if contract.contract_hash != compute_formula_contract_hash(contract):
            blockers.append("FORMULA_SEMANTICS:CONTRACT_HASH_MISMATCH")

    return tuple(sorted(set(blockers)))


def _parse_formula(
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


def assess_formula_semantic_identity(
    *,
    formula: str,
    contract: FormulaSemanticContract,
) -> FormulaSemanticAssessment:
    """Compare a materialized formula with an explicit semantic contract."""

    blockers = list(validate_formula_semantic_contract(contract))

    if not isinstance(formula, str) or not formula.strip():
        blockers.append("FORMULA_SEMANTICS:FORMULA_MISSING")
        return FormulaSemanticAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=tuple(sorted(set(blockers))),
            representation=UNRECOGNIZED,
            observed_semantic_hash=None,
            expected_semantic_hash=(
                None
                if validate_formula_semantic_contract(contract)
                else compute_formula_semantic_hash(
                    source=contract.source,
                    query_text=contract.query_text,
                    header_rows=contract.header_rows,
                )
            ),
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

    expected_hash = compute_formula_semantic_hash(
        source=contract.source,
        query_text=contract.query_text,
        header_rows=contract.header_rows,
    )

    parsed = _parse_formula(formula)
    if parsed is None:
        return FormulaSemanticAssessment(
            status=HOLD,
            ready=False,
            blocking_reasons=(
                "FORMULA_SEMANTICS:UNSUPPORTED_REPRESENTATION",
            ),
            representation=UNRECOGNIZED,
            observed_semantic_hash=None,
            expected_semantic_hash=expected_hash,
        )

    representation, source, query_text, header_rows, fallback = parsed

    observed_hash = compute_formula_semantic_hash(
        source=source,
        query_text=query_text,
        header_rows=header_rows,
    )

    if normalize_query_source(source) != normalize_query_source(contract.source):
        blockers.append("FORMULA_SEMANTICS:SOURCE_MISMATCH")
    if normalize_query_text(query_text) != normalize_query_text(contract.query_text):
        blockers.append("FORMULA_SEMANTICS:QUERY_TEXT_MISMATCH")
    if header_rows != contract.header_rows:
        blockers.append("FORMULA_SEMANTICS:HEADER_ROWS_MISMATCH")
    if (
        representation == EXPORTED_QUERY_WRAPPER
        and fallback != contract.exported_fallback_literal
    ):
        blockers.append("FORMULA_SEMANTICS:FALLBACK_LITERAL_MISMATCH")
    if observed_hash != expected_hash:
        blockers.append("FORMULA_SEMANTICS:SEMANTIC_HASH_MISMATCH")

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
