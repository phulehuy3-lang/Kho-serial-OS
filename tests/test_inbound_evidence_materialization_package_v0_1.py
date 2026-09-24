from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.inbound_evidence_materialization_package_v0_1 import (
    CONTRACT_ID,
    HOLD,
    PASS,
    REQUIRED_SURFACES,
    SCENARIO_ID,
    InboundEvidenceMaterializationPackage,
    SurfaceHashEvidence,
    validate_inbound_evidence_materialization_package,
)


def h(character: str) -> str:
    return character * 64


class InboundEvidenceMaterializationPackageTests(unittest.TestCase):
    def package(self):
        surfaces = tuple(
            SurfaceHashEvidence(surface_id, h(str(index + 1)))
            for index, surface_id in enumerate(REQUIRED_SURFACES)
        )
        return InboundEvidenceMaterializationPackage(
            contract_id=CONTRACT_ID,
            scenario_id=SCENARIO_ID,
            task_id="TASK-1",
            scope_id="SCOPE-1",
            target_authority_id="TA-1",
            target_authority_hash=h("a"),
            permission_proof_id="PERM-1",
            permission_proof_hash=h("b"),
            surface_registry_id="REG-1",
            surface_registry_hash=h("c"),
            zero_write_attestation_id="ZW-1",
            zero_write_attestation_hash=h("d"),
            warehouse_schema_version="SCHEMA-1",
            provider_version_marker="PROVIDER-1",
            capture_marker="CAPTURE-1",
            control10_target_contract_hash=h("e"),
            control10_snapshot_hash=h("f"),
            surfaces=surfaces,
            serial_universe_complete=True,
            serial_universe_evidence_id="SERIAL-U-1",
            serial_universe_evidence_hash=h("1"),
            hold_universe_complete=True,
            hold_universe_evidence_id="HOLD-U-1",
            hold_universe_evidence_hash=h("2"),
            mapping_contract_id="MAP-1",
            mapping_contract_hash=h("3"),
            source_evidence_binding_id="SOURCE-E-1",
            source_evidence_binding_hash=h("4"),
            formula_reconciliation_binding_id="FORMULA-E-1",
            formula_reconciliation_binding_hash=h("5"),
            receipt_id="RECEIPT-1",
            receipt_hash=h("6"),
            live_read_authorized=False,
            production_write_authorized=False,
        )

    def assess(self, package=None):
        return validate_inbound_evidence_materialization_package(
            self.package() if package is None else package
        )

    def assert_hold(self, result, reason):
        self.assertEqual(result.status, HOLD)
        self.assertFalse(result.package_coherent)
        self.assertIn(reason, result.blocking_reasons)
        self.assertIsNone(result.package_hash)
        self.assertFalse(result.live_read_authorized)
        self.assertFalse(result.production_write_authorized)

    def test_exact_synthetic_package_passes_without_authority(self):
        result = self.assess()
        self.assertEqual(result.status, PASS)
        self.assertTrue(result.package_coherent)
        self.assertEqual(result.blocking_reasons, ())
        self.assertEqual(len(result.package_hash), 64)
        self.assertFalse(result.live_read_authorized)
        self.assertFalse(result.production_write_authorized)

    def test_surface_order_does_not_change_package_hash(self):
        package = self.package()
        reversed_package = replace(
            package,
            surfaces=tuple(reversed(package.surfaces)),
        )
        self.assertEqual(
            self.assess(package).package_hash,
            self.assess(reversed_package).package_hash,
        )

    def test_missing_extra_and_duplicate_surfaces_hold(self):
        package = self.package()
        missing = replace(package, surfaces=package.surfaces[:-1])
        extra = replace(
            package,
            surfaces=package.surfaces
            + (SurfaceHashEvidence("EXTRA_SURFACE", h("7")),),
        )
        duplicate = replace(
            package,
            surfaces=package.surfaces + (package.surfaces[0],),
        )
        for candidate in (missing, extra, duplicate):
            with self.subTest(candidate=candidate):
                self.assert_hold(self.assess(candidate), "SURFACE_SET_INVALID")

    def test_surface_container_must_be_native_tuple(self):
        package = self.package()
        self.assert_hold(
            self.assess(replace(package, surfaces=list(package.surfaces))),
            "SURFACE_CONTAINER_INVALID",
        )

    def test_malformed_surface_hash_holds(self):
        package = self.package()
        bad = replace(
            package,
            surfaces=(
                SurfaceHashEvidence(REQUIRED_SURFACES[0], "A" * 64),
                *package.surfaces[1:],
            ),
        )
        self.assert_hold(self.assess(bad), "SURFACE_EVIDENCE_INVALID")

    def test_blank_or_whitespace_bindings_hold(self):
        package = self.package()
        candidates = (
            replace(package, task_id=""),
            replace(package, scope_id=" SCOPE-1"),
            replace(package, warehouse_schema_version=" "),
            replace(package, provider_version_marker=" PROVIDER-1"),
            replace(package, capture_marker="CAPTURE-1 "),
        )
        reasons = (
            "BINDING_INVALID",
            "BINDING_INVALID",
            "SCHEMA_VERSION_INVALID",
            "PROVIDER_VERSION_INVALID",
            "CAPTURE_MARKER_INVALID",
        )
        for candidate, reason in zip(candidates, reasons):
            with self.subTest(reason=reason):
                self.assert_hold(self.assess(candidate), reason)

    def test_contract_and_scenario_drift_hold(self):
        package = self.package()
        self.assert_hold(
            self.assess(replace(package, contract_id="V2")),
            "CONTRACT_INVALID",
        )
        self.assert_hold(
            self.assess(replace(package, scenario_id="OTHER")),
            "SCENARIO_INVALID",
        )

    def test_serial_universe_completeness_requires_native_true(self):
        package = self.package()
        for value in (False, None, 1, "PASS"):
            with self.subTest(value=value):
                self.assert_hold(
                    self.assess(replace(package, serial_universe_complete=value)),
                    "SERIAL_UNIVERSE_COMPLETENESS_UNPROVEN",
                )

    def test_hold_universe_completeness_requires_native_true(self):
        package = self.package()
        for value in (False, None, 1, "PASS"):
            with self.subTest(value=value):
                self.assert_hold(
                    self.assess(replace(package, hold_universe_complete=value)),
                    "HOLD_UNIVERSE_COMPLETENESS_UNPROVEN",
                )

    def test_authority_permission_registry_and_zero_write_evidence_are_required(self):
        package = self.package()
        cases = (
            (
                replace(package, target_authority_hash="bad"),
                "TARGET_AUTHORITY_EVIDENCE_INVALID",
            ),
            (
                replace(package, permission_proof_id=" "),
                "PERMISSION_EVIDENCE_INVALID",
            ),
            (
                replace(package, surface_registry_hash="A" * 64),
                "SURFACE_REGISTRY_EVIDENCE_INVALID",
            ),
            (
                replace(package, zero_write_attestation_id=""),
                "ZERO_WRITE_EVIDENCE_INVALID",
            ),
        )
        for candidate, reason in cases:
            with self.subTest(reason=reason):
                self.assert_hold(self.assess(candidate), reason)

    def test_control10_hash_bindings_are_required(self):
        package = self.package()
        self.assert_hold(
            self.assess(replace(package, control10_snapshot_hash="f" * 63)),
            "CONTROL10_BINDING_INVALID",
        )

    def test_completeness_evidence_ids_and_hashes_are_required(self):
        package = self.package()
        self.assert_hold(
            self.assess(replace(package, serial_universe_evidence_id="")),
            "SERIAL_UNIVERSE_EVIDENCE_INVALID",
        )
        self.assert_hold(
            self.assess(replace(package, hold_universe_evidence_hash="Z" * 64)),
            "HOLD_UNIVERSE_EVIDENCE_INVALID",
        )

    def test_mapping_source_formula_and_receipt_evidence_are_required(self):
        package = self.package()
        cases = (
            (
                replace(package, mapping_contract_hash=""),
                "MAPPING_EVIDENCE_INVALID",
            ),
            (
                replace(package, source_evidence_binding_id=" SOURCE-E-1"),
                "SOURCE_EVIDENCE_BINDING_INVALID",
            ),
            (
                replace(package, formula_reconciliation_binding_hash="5" * 63),
                "FORMULA_RECONCILIATION_BINDING_INVALID",
            ),
            (
                replace(package, receipt_hash="G" * 64),
                "RECEIPT_EVIDENCE_INVALID",
            ),
        )
        for candidate, reason in cases:
            with self.subTest(reason=reason):
                self.assert_hold(self.assess(candidate), reason)

    def test_authority_invariants_must_be_native_false(self):
        package = self.package()
        candidates = (
            replace(package, live_read_authorized=True),
            replace(package, live_read_authorized=0),
            replace(package, production_write_authorized=True),
            replace(package, production_write_authorized="False"),
        )
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                self.assert_hold(
                    self.assess(candidate),
                    "AUTHORITY_INVARIANT_INVALID",
                )

    def test_package_type_invalid_holds(self):
        self.assert_hold(
            validate_inbound_evidence_materialization_package(object()),
            "PACKAGE_TYPE_INVALID",
        )

    def test_multiple_blockers_are_sorted(self):
        package = replace(
            self.package(),
            scenario_id="OTHER",
            task_id=" TASK-1",
            target_authority_hash="BAD",
            serial_universe_complete=False,
            live_read_authorized=True,
        )
        result = self.assess(package)
        self.assertEqual(
            result.blocking_reasons,
            tuple(sorted(result.blocking_reasons)),
        )
        self.assertFalse(result.live_read_authorized)
        self.assertFalse(result.production_write_authorized)


if __name__ == "__main__":
    unittest.main()
