from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_V1 = ROOT / "rules" / "WAREHOUSE_INBOUND_SCHEMA_CONTRACT_V1.json"
SCHEMA_V2 = ROOT / "rules" / "WAREHOUSE_INBOUND_SCHEMA_CONTRACT_V2.json"
REGISTRY_V1 = ROOT / "rules" / "FIVE_SURFACE_REGISTRY_V1.json"
REGISTRY_V2 = ROOT / "rules" / "FIVE_SURFACE_REGISTRY_V2.json"

EXPECTED_SCHEMA_V2_HASH = "9a7036828810234062496179c1fe652b9078b1cd7fbe7f50e77e6991b33de203"
EXPECTED_REGISTRY_V2_HASH = "2c45382441fb98003b7ccb7161944de938a1f91ee8199e1c26771bf6c6d9fbad"

EXPECTED_SURFACES = (
    "INBOUND_SOURCE_RECORD",
    "ACTIVE_SERIAL_INTERVAL_UNIVERSE",
    "INBOUND_DERIVED_QUERY_PROJECTION",
    "INBOUND_QUERY_FORMULA_ANCHOR",
    "ACTIVE_HOLD_INTERVAL_UNIVERSE",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def by_surface(schema: dict) -> dict[str, dict]:
    return {
        item["surface_id"]: item
        for item in schema["surface_contracts"]
    }


def field_types(surface: dict) -> dict[str, str]:
    return {
        item["field_id"]: item["type"]
        for item in surface["fields"]
    }


class WarehouseInboundSchemaV2Tests(unittest.TestCase):
    def test_v1_is_preserved_as_historical_contract(self):
        v1 = load(SCHEMA_V1)
        self.assertEqual(v1["warehouse_schema_version"], "WAREHOUSE_INBOUND_SCHEMA_V1")
        source = by_surface(v1)["INBOUND_SOURCE_RECORD"]
        self.assertEqual(field_types(source)["serial_start"], "NONNEGATIVE_INTEGER")

    def test_v2_has_new_contract_identity_and_expected_hash(self):
        v2 = load(SCHEMA_V2)
        self.assertEqual(v2["warehouse_schema_version"], "WAREHOUSE_INBOUND_SCHEMA_V2")
        self.assertEqual(canonical_hash(v2), EXPECTED_SCHEMA_V2_HASH)

    def test_v2_serial_identity_fields_are_strict_serial_text(self):
        v2 = load(SCHEMA_V2)
        surfaces = by_surface(v2)

        expected_serial_fields = {
            "INBOUND_SOURCE_RECORD": ("serial_start", "serial_end"),
            "ACTIVE_SERIAL_INTERVAL_UNIVERSE": ("range_start", "range_end"),
            "INBOUND_DERIVED_QUERY_PROJECTION": ("serial_start", "serial_end"),
            "ACTIVE_HOLD_INTERVAL_UNIVERSE": ("range_start", "range_end"),
        }

        for surface_id, fields in expected_serial_fields.items():
            with self.subTest(surface_id=surface_id):
                types = field_types(surfaces[surface_id])
                for field_id in fields:
                    self.assertEqual(types[field_id], "SERIAL_TEXT")

    def test_quantity_remains_native_nonnegative_integer(self):
        v2 = load(SCHEMA_V2)
        source = by_surface(v2)["INBOUND_SOURCE_RECORD"]
        derived = by_surface(v2)["INBOUND_DERIVED_QUERY_PROJECTION"]
        self.assertEqual(field_types(source)["declared_quantity"], "NONNEGATIVE_INTEGER")
        self.assertEqual(field_types(derived)["declared_quantity"], "NONNEGATIVE_INTEGER")

    def test_serial_text_rules_preserve_identity_and_forbid_silent_coercion(self):
        rules = load(SCHEMA_V2)["serial_text_rules"]
        self.assertIs(rules["native_text"], True)
        self.assertIs(rules["ascii_digits_only"], True)
        self.assertIs(rules["preserve_lexical_identity"], True)
        self.assertIs(rules["numeric_projection_for_interval_math_only"], True)
        self.assertIs(rules["silent_text_integer_coercion_prohibited"], True)

    def test_registry_v2_is_exact_five_surface_binding(self):
        registry = load(REGISTRY_V2)
        self.assertEqual(registry["surface_registry_id"], "SR1_HCM_SERIAL_INBOUND_V2")
        self.assertEqual(registry["warehouse_schema_version"], "WAREHOUSE_INBOUND_SCHEMA_V2")
        self.assertEqual(
            tuple(item["surface_id"] for item in registry["surfaces"]),
            EXPECTED_SURFACES,
        )
        self.assertEqual(
            tuple(item["ordinal"] for item in registry["surfaces"]),
            (1, 2, 3, 4, 5),
        )
        self.assertEqual(canonical_hash(registry), EXPECTED_REGISTRY_V2_HASH)

    def test_registry_v1_is_preserved_and_not_relabelled(self):
        registry = load(REGISTRY_V1)
        self.assertEqual(registry["surface_registry_id"], "SR1_HCM_SERIAL_INBOUND_V1")
        self.assertEqual(registry["warehouse_schema_version"], "WAREHOUSE_INBOUND_SCHEMA_V1")

    def test_v2_public_contract_contains_no_provider_locator_keys(self):
        forbidden = {
            "drive_id",
            "spreadsheet_id",
            "sheet_id",
            "range_id",
            "resource_id",
            "production_url",
            "credential",
            "service_account",
        }

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn(key.lower(), forbidden)
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(load(SCHEMA_V2))
        walk(load(REGISTRY_V2))


if __name__ == "__main__":
    unittest.main()
