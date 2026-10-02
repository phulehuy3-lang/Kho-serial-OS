from dataclasses import replace
import hashlib
import unittest
from scripts.evidence_recovery_v192 import (
    EvidenceRecoveryCandidateV192 as Candidate,
    EvidenceRecoveryRequestV192 as Request,
    evaluate_evidence_recovery_v1_9_2 as evaluate,
    run_disposable_evidence_workflow_v192 as workflow,
    RECOVERY_STAGES_V192,
    classify_outbound_historical_proof_v1_9_2 as classify,
    validate_single_active_recovery_root_v1_9_2 as root,
)

class EvidenceRecoveryTests(unittest.TestCase):
    def request(self):
        data = b'synthetic evidence; no warehouse business data'
        digest = hashlib.sha256(data).hexdigest()
        candidate = Candidate('IMG_random.jpeg', '/synthetic/IMG_random.jpeg',
                              digest, True, True, True, 'synthetic-file', data,
                              'synthetic-canonical', data)
        return Request('synthetic-evidence', True, 0, (candidate,), digest, False)

    def test_search_zero_recovers_before_disposable_mutation(self):
        sandbox = []
        result, trace = workflow(self.request(), sandbox)
        self.assertEqual(result.status, 'SOURCE_ARCHIVED_VERIFIED')
        self.assertFalse(result.missing_evidence_hold_allowed)
        self.assertFalse(result.inventory_mutation_authorized)
        self.assertEqual(trace, ('G1A_RECOVERY', 'G1B_IDENTITY_BYTES_BOUND',
                                'G1C_PROVIDER_READBACK_MATCH', 'DISPOSABLE_MUTATION'))
        self.assertEqual(sandbox, ['DISPOSABLE_MARKER'])

    def test_unverified_archive_never_mutates(self):
        request = self.request()
        for changes in ({'canonical_archived': False}, {'provider_readback_bytes': b'wrong'},
                        {'canonical_file_id': None}, {'library_file_id': None},
                        {'source_bytes': None}, {'source_bytes': b'forged'},
                        {'bytes_available': False}):
            with self.subTest(changes=changes):
                sandbox = []
                result, _ = workflow(replace(request, candidates=(replace(request.candidates[0], **changes),)), sandbox)
                self.assertNotEqual(result.status, 'SOURCE_ARCHIVED_VERIFIED')
                self.assertEqual(sandbox, [])
                self.assertFalse(result.missing_evidence_hold_allowed)

    def test_exhaustion_requires_all_stage_receipts(self):
        request = replace(self.request(), candidates=(), all_stages_exhausted=True)
        self.assertFalse(evaluate(request).missing_evidence_hold_allowed)
        result = evaluate(replace(request, completed_stages=RECOVERY_STAGES_V192))
        self.assertEqual(result.status, 'SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY')
        self.assertTrue(result.missing_evidence_hold_allowed)

    def test_unavailable_candidate_does_not_hide_valid_one(self):
        request = self.request()
        bad = replace(request.candidates[0], bytes_available=False)
        self.assertEqual(evaluate(replace(request, candidates=(bad,) + request.candidates)).status,
                         'SOURCE_ARCHIVED_VERIFIED')

    def test_strict_boolean_and_single_root(self):
        for value in ('TRUE', 1, None):
            with self.assertRaises(ValueError):
                evaluate(replace(self.request(), prior_chat_supplied=value))
        for count in (0, 2, True, '1'):
            with self.assertRaises(ValueError):
                root(count)
        self.assertTrue(root(1))

    def test_outbound_history_cannot_be_upgraded(self):
        self.assertEqual(classify(historical_prewrite_snapshot_available=False,
                                  postclose_fail_closed_proven=True), 'POSTCLOSE_FAIL_CLOSED_ONLY')
        self.assertEqual(classify(historical_prewrite_snapshot_available='TRUE',
                                  postclose_fail_closed_proven=True), 'BLOCKED_UNPROVEN')

    def test_production_callback_rejected(self):
        with self.assertRaises(ValueError):
            workflow(self.request(), lambda: None)
