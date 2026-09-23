from __future__ import annotations

from dataclasses import replace
from datetime import date
import unittest

from scripts.dry_run_mutation_contract_v0_1 import (
    MutationIntent,
    MutationWhitelistEntry,
    ReadbackContract,
    RollbackIntent,
    assess_dry_run_mutation_contract,
    with_computed_approval_hash,
    with_computed_mutation_manifest_hash,
    with_computed_mutation_whitelist_hash,
)
from scripts.ranked_prefix_allocation_lineage_v0_1 import (
    RankedCandidate,
    build_allocation_plan,
    build_source_rank_lineage,
    compute_allocation_plan_hash,
    evaluate_ranked_prefix_allocation,
)
from scripts.readonly_shadow_snapshot_integrity_v0_1 import (
    SOURCE_OF_TRUTH,
    SurfaceReadResult,
    assess_shadow_snapshot,
    with_computed_surface_contract_hash,
    with_computed_target_contract_hash,
)
from scripts.source_pool_authority_v0_1 import (
    CANONICAL_SOURCE_IDENTITY_STATUS,
    CANONICAL_SOURCE_POOL_SCHEMA_ID,
    PASS as SOURCE_POOL_PASS,
    SourcePoolAuthorityRegistrySnapshot,
    resolve_source_pool_authority,
    with_computed_source_pool_hash,
)


DOC_DATE = date(2026, 2, 15)
TASK_ID = "TASK-CHAIN-A"
AUTHORITY_ID = "AUTH-CHAIN-A"
SOURCE_IDS = ("SRC-A", "SRC-B")


def source_pool_resolution():
    record = with_computed_source_pool_hash(
        authority_id=AUTHORITY_ID,
        task_id=TASK_ID,
        line_key="LINE-A",
        document_date=DOC_DATE,
        carrier="CARRIER-A",
        denomination=100,
        permitted_source_ids=SOURCE_IDS,
        evidence_ref="EVID-A",
    )
    snapshot = SourcePoolAuthorityRegistrySnapshot(
        source_name="SYNTHETIC_SOURCE_POOL_REGISTRY",
        source_identity_status=CANONICAL_SOURCE_IDENTITY_STATUS,
        schema_id=CANONICAL_SOURCE_POOL_SCHEMA_ID,
        source_present=True,
        readback_status=SOURCE_POOL_PASS,
        records=(record,),
    )
    return resolve_source_pool_authority(
        authority_id=AUTHORITY_ID,
        task_id=TASK_ID,
        line_key="LINE-A",
        document_date=DOC_DATE,
        carrier="CARRIER-A",
        denomination=100,
        materialized_source_ids=SOURCE_IDS,
        snapshot=snapshot,
    )


def ranked_artifacts():
    candidates = (
        RankedCandidate(
            candidate_id="SRC-A",
            source_date=date(2026, 2, 14),
            source_row=1,
            serial_start="00100",
            available_qty=60,
        ),
        RankedCandidate(
            candidate_id="SRC-B",
            source_date=date(2026, 2, 13),
            source_row=2,
            serial_start="00200",
            available_qty=60,
        ),
    )
    decision = evaluate_ranked_prefix_allocation(
        task_id=TASK_ID,
        target_date=DOC_DATE,
        requested_qty=100,
        candidates=candidates,
    )
    lineage = build_source_rank_lineage(
        task_id=TASK_ID,
        decision=decision,
        source_rank_gate_id="GATE-A",
    )
    plan = build_allocation_plan(
        task_id=TASK_ID,
        decision=decision,
        source_rank_gate_id=lineage.source_rank_gate_id,
    )
    plan_hash = compute_allocation_plan_hash(
        task_id=TASK_ID,
        decision=decision,
        lineage=lineage,
        plan_rows=plan,
    )
    return decision, plan_hash


def snapshot_hash():
    surface = with_computed_surface_contract_hash(
        surface_id="SOURCE_STATE",
        logical_name="SOURCE_STATE",
        role=SOURCE_OF_TRUTH,
        fields=("ItemID", "Quantity"),
    )
    target = with_computed_target_contract_hash(
        target_id="TARGET-A",
        schema_version="SCHEMA-A",
        surfaces=(surface,),
    )
    assessment = assess_shadow_snapshot(
        snapshot_id="SNAP-A",
        target=target,
        reads={
            "SOURCE_STATE": SurfaceReadResult(
                surface_id="SOURCE_STATE",
                version_marker="V1",
                captured_at="T1",
                rows=(
                    {"ItemID": "SRC-A", "Quantity": 60},
                    {"ItemID": "SRC-B", "Quantity": 60},
                ),
            )
        },
    )
    assert assessment.snapshot is not None
    return assessment.snapshot.snapshot_hash


def whitelist():
    return with_computed_mutation_whitelist_hash(
        whitelist_id="WL-A",
        entries=(MutationWhitelistEntry("RESOURCE-A", "STATE"),),
    )


def readback_contract():
    return ReadbackContract(
        contract_id="RB-A",
        full_row_readback_required=True,
        source_derived_reconciliation_required=True,
        rollback_on_mismatch=True,
        readback_status="PASS",
    )


def build_manifest(*, candidate_source_ids=SOURCE_IDS):
    decision, plan_hash = ranked_artifacts()
    assert decision.candidate_set_hash is not None
    return with_computed_mutation_manifest_hash(
        manifest_id="MANIFEST-A",
        task_id=TASK_ID,
        document_date=DOC_DATE,
        line_keys=("LINE-A",),
        source_years=(2026,),
        source_pool_authority_id=AUTHORITY_ID,
        candidate_source_ids=tuple(candidate_source_ids),
        candidate_set_hash=decision.candidate_set_hash,
        allocation_plan_hash=plan_hash,
        mutation_whitelist_id="WL-A",
        explicit_approval_id="APR-A",
        pretransition_readback_hash=snapshot_hash(),
        operations=(
            MutationIntent(
                operation_id="OP-A",
                resource_name="RESOURCE-A",
                row_key="ROW-A",
                field_name="STATE",
                expected_before="PLANNED",
                intended_after="COMMITTED",
            ),
        ),
        rollback_operations=(
            RollbackIntent(
                operation_id="OP-A",
                resource_name="RESOURCE-A",
                row_key="ROW-A",
                field_name="STATE",
                restore_value="PLANNED",
            ),
        ),
        readback_contract=readback_contract(),
    )


def approval_for(manifest):
    return with_computed_approval_hash(
        approval_id=manifest.explicit_approval_id,
        task_id=manifest.task_id,
        manifest_hash=manifest.manifest_hash,
    )


class Phase2AuthorityAllocationSnapshotDryRunChainTests(unittest.TestCase):
    def test_control_02_09_10_08_chain_passes_with_real_hashes(self) -> None:
        pool = source_pool_resolution()
        manifest = build_manifest()
        result = assess_dry_run_mutation_contract(
            manifest=manifest,
            whitelist=whitelist(),
            approval=approval_for(manifest),
            source_pool_resolution=pool,
        )
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.dry_run_contract_ready)
        self.assertFalse(result.production_write_authorized)

    def test_candidate_source_set_drift_blocks_chain(self) -> None:
        pool = source_pool_resolution()
        manifest = build_manifest(
            candidate_source_ids=("SRC-A", "SRC-X")
        )
        result = assess_dry_run_mutation_contract(
            manifest=manifest,
            whitelist=whitelist(),
            approval=approval_for(manifest),
            source_pool_resolution=pool,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:SOURCE_POOL_SOURCE_SET_MISMATCH",
            result.blocking_reasons,
        )

    def test_forged_pass_resolution_with_blockers_is_rejected(self) -> None:
        pool = replace(
            source_pool_resolution(),
            blocking_reasons=("SOURCE_POOL:SYNTHETIC_BLOCKER",),
        )
        manifest = build_manifest()
        result = assess_dry_run_mutation_contract(
            manifest=manifest,
            whitelist=whitelist(),
            approval=approval_for(manifest),
            source_pool_resolution=pool,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:SOURCE_POOL_RESOLUTION_HAS_BLOCKERS",
            result.blocking_reasons,
        )

    def test_empty_permitted_source_set_is_rejected(self) -> None:
        pool = replace(
            source_pool_resolution(),
            permitted_source_ids=(),
        )
        manifest = build_manifest()
        result = assess_dry_run_mutation_contract(
            manifest=manifest,
            whitelist=whitelist(),
            approval=approval_for(manifest),
            source_pool_resolution=pool,
        )
        self.assertIn(
            "DRY_RUN_MUTATION:SOURCE_POOL_PERMITTED_SOURCE_SET_INVALID",
            result.blocking_reasons,
        )


if __name__ == "__main__":
    unittest.main()
