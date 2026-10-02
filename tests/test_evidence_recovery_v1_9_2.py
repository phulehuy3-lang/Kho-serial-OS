from __future__ import annotations

import unittest

from scripts.evidence_recovery_v1_9_2 import (
    BLOCKED_UNPROVEN,
    HISTORICAL_SOURCE_RANK_REPLAYABLE,
    POSTCLOSE_FAIL_CLOSED_ONLY,
    SOURCE_ARCHIVED_VERIFIED,
    SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED,
    SOURCE_FOUND_NOT_CANONICAL,
    SOURCE_HASH_MISMATCH,
    SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY,
    EvidenceCandidate,
    EvidenceRecoveryError,
    EvidenceRecoveryRequest,
    classify_outbound_historical_proof,
    evaluate_evidence_recovery,
    validate_single_active_recovery_root,
)


def h(character: str) -> str:
    return character * 64


class EvidenceRecoveryV192Tests(unittest.TestCase):
    def test_px62750_public_safe_pattern_recovers_random_filename_after_zero_search(self):
        expected = h("a")
        request = EvidenceRecoveryRequest(
            evidence_key="PX62750-PUBLIC-SAFE",
            prior_chat_supplied=True,
            text_search_hits=0,
            candidates=(
                EvidenceCandidate(
                    "unrelated-image.bin.txt",
                    "/warehouse-project/unrelated-image.bin.txt",
                    h("b"),
                    False,
                ),
                EvidenceCandidate(
                    "IMG_RANDOM_EVIDENCE.bin.txt",
                    "/warehouse-project/IMG_RANDOM_EVIDENCE.bin.txt",
                    expected,
                    True,
                    True,
                    True,
                ),
            ),
            historical_sha256=expected,
            all_stages_exhausted=False,
        )

        result = evaluate_evidence_recovery(request)
        self.assertEqual(result.status, SOURCE_ARCHIVED_VERIFIED)
        self.assertEqual(result.selected_sha256, expected)
        self.assertFalse(result.missing_evidence_hold_allowed)
        self.assertFalse(result.inventory_mutation_authorized)

    def test_search_zero_alone_never_means_missing(self):
        result = evaluate_evidence_recovery(
            EvidenceRecoveryRequest(
                evidence_key="EVID-A",
                prior_chat_supplied=True,
                text_search_hits=0,
                candidates=(),
                historical_sha256=None,
                all_stages_exhausted=False,
            )
        )
        self.assertEqual(
            result.status,
            SOURCE_ATTACHMENT_PRIOR_CHAT_NOT_MATERIALIZED,
        )
        self.assertFalse(result.missing_evidence_hold_allowed)

    def test_hash_mismatch_blocks_candidate_substitution(self):
        result = evaluate_evidence_recovery(
            EvidenceRecoveryRequest(
                evidence_key="EVID-A",
                prior_chat_supplied=True,
                text_search_hits=0,
                candidates=(
                    EvidenceCandidate(
                        "candidate.bin.txt",
                        "/warehouse-project/candidate.bin.txt",
                        h("b"),
                        True,
                    ),
                ),
                historical_sha256=h("a"),
                all_stages_exhausted=True,
            )
        )
        self.assertEqual(result.status, SOURCE_HASH_MISMATCH)
        self.assertFalse(result.missing_evidence_hold_allowed)

    def test_found_not_canonical_is_distinct_from_missing(self):
        result = evaluate_evidence_recovery(
            EvidenceRecoveryRequest(
                evidence_key="EVID-A",
                prior_chat_supplied=True,
                text_search_hits=0,
                candidates=(
                    EvidenceCandidate(
                        "candidate.bin.txt",
                        "/warehouse-project/candidate.bin.txt",
                        h("a"),
                        True,
                        True,
                        False,
                    ),
                ),
                historical_sha256=h("a"),
                all_stages_exhausted=False,
            )
        )
        self.assertEqual(result.status, SOURCE_FOUND_NOT_CANONICAL)
        self.assertFalse(result.missing_evidence_hold_allowed)

    def test_exhaustive_not_found_is_only_true_missing_outcome(self):
        result = evaluate_evidence_recovery(
            EvidenceRecoveryRequest(
                evidence_key="EVID-A",
                prior_chat_supplied=False,
                text_search_hits=0,
                candidates=(),
                historical_sha256=None,
                all_stages_exhausted=True,
            )
        )
        self.assertEqual(
            result.status,
            SOURCE_NOT_FOUND_AFTER_EXHAUSTIVE_RECOVERY,
        )
        self.assertTrue(result.missing_evidence_hold_allowed)

    def test_recovery_root_cardinality_is_exactly_one(self):
        self.assertTrue(validate_single_active_recovery_root(1))
        for bad in (0, 2, True, "1", None):
            with self.subTest(bad=bad), self.assertRaises(EvidenceRecoveryError):
                validate_single_active_recovery_root(bad)

    def test_tx517_tx518_pattern_never_gets_retroactive_rank_pass(self):
        decision = classify_outbound_historical_proof(
            historical_prewrite_snapshot_available=False,
            postclose_fail_closed_proven=True,
        )
        self.assertEqual(decision, POSTCLOSE_FAIL_CLOSED_ONLY)
        self.assertNotEqual(decision, HISTORICAL_SOURCE_RANK_REPLAYABLE)

        for bad in ("FALSE", 0, None):
            with self.subTest(bad=bad):
                self.assertEqual(
                    classify_outbound_historical_proof(
                        historical_prewrite_snapshot_available=bad,
                        postclose_fail_closed_proven=True,
                    ),
                    BLOCKED_UNPROVEN,
                )


if __name__ == "__main__":
    unittest.main()
