"""Disposable, synthetic v1.9.2 workflow regression. No production payload."""
from dataclasses import replace
import hashlib
import unittest

from scripts.evidence_recovery_v1_9_2 import (
    STAGES, StageRecord, EvidenceIdentity, ArchiveReadback, Candidate,
    RecoveryRequest, evaluate_recovery, evaluate_prewrite, classify_outbound_history,
)


def fixture(source=b'synthetic-random-image-fixture'):
    digest = hashlib.sha256(source).hexdigest()
    identity = EvidenceIdentity('fixture-key', 'library-synthetic',
        '/synthetic/IMG_RANDOM.jpeg', 'IMG_RANDOM.jpeg', 'DOC-SYNTHETIC',
        '2026-01-01', 'SYNTHETIC_SUPPLIER', digest, len(source),
        'image/jpeg', '2026-01-01T00:00:00+00:00', 'ORIGINAL')
    archive = ArchiveReadback('fixture-key', 'canonical-synthetic',
        'folder-synthetic', 'readback-synthetic', '2026-01-01T01:00:00+00:00', source)
    candidate = Candidate(identity, source, True, archive)
    return RecoveryRequest('fixture-key', True, 0, (candidate,), digest, (), ('root-synthetic',))


def complete_records():
    return tuple(StageRecord(stage, 'fixture-key', 'NO_MATCH', 'receipt-' + stage) for stage in STAGES)


def prewrite(request, **changes):
    values = dict(task_id='task-synthetic', resolved_task_ids=('task-synthetic',),
        frozen_generation='generation-synthetic', current_generation='generation-synthetic',
        prior_gates_pass=True)
    values.update(changes)
    return evaluate_prewrite(request, **values)


class EvidenceRecoveryTests(unittest.TestCase):
    def test_disposable_workflow_orders_gates_before_mutation(self):
        request = fixture()
        ledger = []
        trace = []
        result = prewrite(request)
        trace.extend(result.trace)
        if result.status == 'PREWRITE_READY':
            ledger.append('synthetic-mutation')
            trace.append('DISPOSABLE_MUTATION')
        self.assertEqual(ledger, ['synthetic-mutation'])
        self.assertEqual(trace[:3], ['G1A_RECOVERY_PASS', 'G1B_IDENTITY_PASS', 'G1C_ARCHIVE_READBACK_PASS'])
        self.assertLess(trace.index('G1C_ARCHIVE_READBACK_PASS'), trace.index('DISPOSABLE_MUTATION'))
        self.assertFalse(result.inventory_mutation_authorized)
        self.assertFalse(result.missing_evidence_hold_allowed)

    def test_search_zero_without_records_is_not_missing(self):
        result = evaluate_recovery(replace(fixture(), candidates=()))
        self.assertEqual(result.status, 'SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED')
        self.assertFalse(result.missing_evidence_hold_allowed)

    def test_each_incomplete_stage_prefix_cannot_prove_missing(self):
        for count in range(len(STAGES)):
            with self.subTest(count=count):
                result = evaluate_recovery(replace(fixture(), candidates=(), stage_records=complete_records()[:count]))
                self.assertFalse(result.missing_evidence_hold_allowed)

    def test_all_no_match_stages_allow_absence_classification_only(self):
        result = evaluate_recovery(replace(fixture(), candidates=(), stage_records=complete_records()))
        self.assertEqual(result.status, 'SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY')
        self.assertTrue(result.missing_evidence_hold_allowed)
        self.assertFalse(result.prospective_prewrite_ready)
        self.assertFalse(result.inventory_mutation_authorized)

    def test_unavailable_stage_never_proves_absence(self):
        for i in range(len(STAGES)):
            records = list(complete_records())
            records[i] = replace(records[i], outcome='UNAVAILABLE')
            self.assertFalse(evaluate_recovery(replace(fixture(), candidates=(), stage_records=tuple(records))).missing_evidence_hold_allowed)

    def test_unbound_reordered_and_duplicate_stages_block(self):
        records = complete_records()
        for bad in ((replace(records[0], evidence_key='other'),), records[::-1],
                    (records[0], records[0]), (replace(records[0], receipt_id=''),)):
            self.assertEqual(evaluate_recovery(replace(fixture(), candidates=(), stage_records=bad)).status, 'BLOCKED_UNPROVEN')

    def test_positive_search_hits_cannot_prove_missing(self):
        result = evaluate_recovery(replace(fixture(), candidates=(), text_search_hits=1, stage_records=complete_records()))
        self.assertFalse(result.missing_evidence_hold_allowed)

    def test_bytes_unavailable_does_not_shadow_good_candidate(self):
        request = fixture()
        unavailable = replace(request.candidates[0], source_bytes=None)
        for candidates in ((unavailable, request.candidates[0]), (request.candidates[0], unavailable)):
            self.assertEqual(evaluate_recovery(replace(request, candidates=candidates)).status, 'SOURCE_ARCHIVED_VERIFIED')

    def test_known_bytes_unavailable_never_missing(self):
        request = fixture()
        result = evaluate_recovery(replace(request, candidates=(replace(request.candidates[0], source_bytes=None),), stage_records=complete_records()))
        self.assertEqual(result.status, 'SOURCE_BYTES_UNAVAILABLE')
        self.assertFalse(result.missing_evidence_hold_allowed)

    def test_ambiguous_candidates_block(self):
        request = fixture()
        self.assertEqual(evaluate_recovery(replace(request, candidates=request.candidates * 2)).status, 'BLOCKED_UNPROVEN')

    def test_source_hash_and_byte_size_are_computed(self):
        request = fixture()
        candidate = request.candidates[0]
        for bad in (replace(candidate, source_bytes=b'changed'),
                    replace(candidate, identity=replace(candidate.identity, byte_size=True)),
                    replace(candidate, identity=replace(candidate.identity, byte_size=999)),
                    replace(candidate, identity=replace(candidate.identity, sha256='f'*64))):
            self.assertFalse(prewrite(replace(request, candidates=(bad,))).prospective_prewrite_ready)

    def test_historical_hash_mismatch(self):
        self.assertEqual(evaluate_recovery(replace(fixture(), historical_sha256='f'*64)).status, 'SOURCE_HASH_MISMATCH')

    def test_found_without_archive_blocks_disposable_mutation(self):
        request = fixture()
        result = prewrite(replace(request, candidates=(replace(request.candidates[0], archive=None),)))
        self.assertEqual(result.status, 'SOURCE_FOUND_NOT_CANONICAL')
        self.assertFalse(result.prospective_prewrite_ready)
        self.assertFalse(result.missing_evidence_hold_allowed)

    def test_archive_bytes_must_match_exactly(self):
        request = fixture()
        candidate = request.candidates[0]
        bad = replace(candidate, archive=replace(candidate.archive, readback_bytes=b'other'))
        self.assertEqual(prewrite(replace(request, candidates=(bad,))).status, 'SOURCE_HASH_MISMATCH')

    def test_archive_binding_and_timestamps_block(self):
        request = fixture()
        candidate = request.candidates[0]
        for archive in (replace(candidate.archive, evidence_key='other'),
                        replace(candidate.archive, canonical_file_id=''),
                        replace(candidate.archive, receipt_id=''),
                        replace(candidate.archive, provider_readback_at='2025-01-01T00:00:00+00:00'),
                        replace(candidate.archive, provider_readback_at='2026-01-01')):
            self.assertEqual(prewrite(replace(request, candidates=(replace(candidate, archive=archive),))).status, 'BLOCKED_UNPROVEN')

    def test_identity_binding_required_fields(self):
        request = fixture()
        candidate = request.candidates[0]
        for field in ('library_file_id', 'library_path', 'original_filename',
                      'document_no', 'document_date', 'supplier_role', 'mime',
                      'provider_created_at', 'evidence_grade'):
            with self.subTest(field=field):
                bad = replace(candidate, identity=replace(candidate.identity, **{field: ''}))
                self.assertEqual(prewrite(replace(request, candidates=(bad,))).status, 'BLOCKED_UNPROVEN')

    def test_single_recovery_root(self):
        for roots in ((), ('a','b'), 'root', (True,)):
            self.assertEqual(evaluate_recovery(replace(fixture(), active_recovery_roots=roots)).status, 'BLOCKED_UNPROVEN')

    def test_strict_boolean_and_container_validation(self):
        request = fixture()
        for bad in (None, {}, replace(request, prior_chat_supplied='TRUE'),
                    replace(request, text_search_hits=True), replace(request, candidates=[]),
                    replace(request, stage_records=[]),
                    replace(request, candidates=(replace(request.candidates[0], visual_match='TRUE'),))):
            self.assertEqual(evaluate_recovery(bad).status, 'BLOCKED_UNPROVEN')

    def test_stable_id_not_row_position(self):
        for ids in ((), ('other',), ('task-synthetic', 'task-synthetic'), ['task-synthetic']):
            self.assertEqual(prewrite(fixture(), resolved_task_ids=ids).status, 'BLOCKED_UNPROVEN')

    def test_concurrent_generation_invalidates_prewrite(self):
        self.assertEqual(prewrite(fixture(), current_generation='new-generation').status, 'BLOCKED_UNPROVEN')

    def test_existing_warehouse_gates_are_required(self):
        for value in (False, 'PASS', 1, None):
            self.assertEqual(prewrite(fixture(), prior_gates_pass=value).status, 'BLOCKED_UNPROVEN')

    def test_postclose_proof_never_becomes_original_rank_pass(self):
        self.assertEqual(classify_outbound_history(historical_prewrite_snapshot_available=False,
                          postclose_fail_closed_proven=True), 'POSTCLOSE_FAIL_CLOSED_ONLY')
        self.assertEqual(classify_outbound_history(historical_prewrite_snapshot_available=True,
                          postclose_fail_closed_proven=True), 'HISTORICAL_SOURCE_RANK_REPLAYABLE')
        self.assertEqual(classify_outbound_history(historical_prewrite_snapshot_available='TRUE',
                          postclose_fail_closed_proven=True), 'BLOCKED_UNPROVEN')


if __name__ == '__main__':
    unittest.main()


class GovernanceCallerTests(unittest.TestCase):
    def call(self, previous, following, request, **changes):
        from scripts.warehouse_governance_v1_8 import validate_inbound_transition_v1_9_2
        values = dict(recovery_request=request, task_id='task-synthetic',
            resolved_task_ids=('task-synthetic',), frozen_generation='g',
            current_generation='g', prior_gates_pass=True, manifest_readback=True)
        values.update(changes)
        return validate_inbound_transition_v1_9_2(previous, following, **values)

    def test_caller_seals_then_writes_disposable_state(self):
        trace = []
        sealed = self.call('PREPARED', 'PREWRITE_SEALED', fixture())
        trace.extend(sealed.trace)
        trace.append('PREWRITE_SEALED')
        self.call('PREWRITE_SEALED', 'WRITTEN', fixture())
        trace.append('DISPOSABLE_MUTATION')
        self.assertLess(trace.index('G1C_ARCHIVE_READBACK_PASS'), trace.index('PREWRITE_SEALED'))
        self.assertLess(trace.index('PREWRITE_SEALED'), trace.index('DISPOSABLE_MUTATION'))

    def test_caller_cannot_skip_manifest(self):
        with self.assertRaises(ValueError):
            self.call('PREPARED', 'PREWRITE_SEALED', fixture(), manifest_readback=False)

    def test_caller_cannot_use_unarchived_or_missing_evidence(self):
        request = fixture()
        for bad in (replace(request, candidates=()), replace(request,
                    candidates=(replace(request.candidates[0], archive=None),))):
            for previous, following in (('PREPARED','PREWRITE_SEALED'), ('PREWRITE_SEALED','WRITTEN')):
                with self.assertRaises(ValueError):
                    self.call(previous, following, bad)

    def test_caller_rechecks_concurrency_before_write(self):
        self.call('PREPARED', 'PREWRITE_SEALED', fixture())
        with self.assertRaises(ValueError):
            self.call('PREWRITE_SEALED', 'WRITTEN', fixture(), current_generation='new')


class OriginalGradeTests(unittest.TestCase):
    def test_derivative_and_invalid_document_date_block(self):
        request = fixture()
        candidate = request.candidates[0]
        for changes in ({'evidence_grade':'DERIVED'}, {'document_date':'bad'}, {'document_date':'20260101'}):
            bad = replace(candidate, identity=replace(candidate.identity, **changes))
            self.assertEqual(prewrite(replace(request, candidates=(bad,))).status, 'BLOCKED_UNPROVEN')
