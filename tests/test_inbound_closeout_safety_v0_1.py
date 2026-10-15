"""Synthetic regressions: this test never touches MASTER LIVE."""
from copy import deepcopy
import unittest

from scripts.inbound_closeout_safety_v0_1 import validate_closeout


def fixture():
    return {
        "canonical_states": ["PREPARED", "COMMITTED", "READBACK_PASS", "CLOSED", "RECONCILE_REQUIRED"],
        "transaction": {"task_id": "TASK_SYNTHETIC", "state": "CLOSED", "readback_status": "PASS", "total_quantity": 3, "interval_count": 2},
        "approval": True,
        "source": {"task_id": "TASK_SYNTHETIC", "originals_verified": True,
                   "quantities": [1, 2], "duplicate_transaction_count": 1,
                   "hold_overlap_count": 0},
        "manifest": {"task_id": "TASK_SYNTHETIC", "sealed_before_write": True,
                     "touch_set": ["Sheet!A8", "Sheet!C8", "LEDGER!A9"]},
        "provider": {"task_id": "TASK_SYNTHETIC", "transport": "GOOGLE_SHEETS_NATIVE",
                     "request_receipt": "request-synthetic", "response_receipt": "response-synthetic",
                     "prewrite_admission_pass": True, "native_afterimage_verified": True,
                     "touch_set": ["Sheet!A8", "Sheet!C8", "LEDGER!A9"],
                     "provider_error": False, "unknown_ack": False},
        "reconciliation": {"native_recheck": True, "all_checks_pass": True,
                           "records": [{"id": "G10_SYNTHETIC", "depends_on": [], "provider_readback": True},
                                       {"id": "G18_SYNTHETIC", "depends_on": ["G10_SYNTHETIC"], "provider_readback": True}]},
    }


class CloseoutSafetyTests(unittest.TestCase):
    def assert_hold(self, change, reason):
        ev = fixture()
        change(ev)
        result = validate_closeout(ev)
        self.assertEqual(result.status, "HOLD")
        self.assertIn(reason, result.reasons)

    def test_valid_synthetic_pass(self):
        self.assertEqual(validate_closeout(fixture()).status, "PASS")

    def test_rejects_unlisted_terminal_enum(self):
        self.assert_hold(lambda e: e["transaction"].update(state="CLOSED_READBACK_PASS"), "STATE_NOT_IN_CANONICAL_ENUM")

    def test_rejects_premature_pending_state(self):
        self.assert_hold(lambda e: e["transaction"].update(state="COMMITTED_PENDING_READBACK"), "STATE_NOT_IN_CANONICAL_ENUM")

    def test_canonical_enum_missing(self):
        self.assert_hold(lambda e: e.pop("canonical_states"), "CANONICAL_STATE_SCHEMA_MISSING")

    def test_missing_prewrite_admission(self):
        self.assert_hold(lambda e: e["provider"].update(prewrite_admission_pass=False), "G9_ADMISSION_NOT_ATTESTED")

    def test_transport_receipt_absent(self):
        self.assert_hold(lambda e: e["provider"].update(response_receipt=""), "PROVIDER_REQUEST_RESPONSE_MISSING")

    def test_receipt_requires_nonempty_string_reference(self):
        for key in ("request_receipt", "response_receipt"):
            for value in (True, 1, ["placeholder"], {"unverified": True}, "   ", " receipt ", None):
                with self.subTest(key=key, value=value):
                    self.assert_hold(lambda e: e["provider"].update({key: value}),
                                     "PROVIDER_REQUEST_RESPONSE_MISSING")

    def test_unhashable_state_with_set_enum_holds_without_crashing(self):
        for value in ([], {}, ["CLOSED"]):
            with self.subTest(value=value):
                def corrupt(e):
                    e["canonical_states"] = set(e["canonical_states"])
                    e["transaction"]["state"] = value
                self.assert_hold(corrupt, "STATE_NOT_IN_CANONICAL_ENUM")

    def test_expected_equals_expected_is_not_actual_touch(self):
        self.assert_hold(lambda e: e["provider"].update(touch_set=[]), "ACTUAL_TOUCH_SET_MISSING_OR_DUPLICATE")

    def test_extra_protected_touch(self):
        self.assert_hold(lambda e: e["provider"]["touch_set"].append("Sheet!B8"), "ACTUAL_TOUCH_SET_MISMATCH")

    def test_missing_g8_seal(self):
        self.assert_hold(lambda e: e["manifest"].update(sealed_before_write=False), "G8_NOT_SEALED_BEFORE_WRITE")

    def test_unknown_ack_no_replay(self):
        self.assert_hold(lambda e: e["provider"].update(unknown_ack=True), "UNKNOWN_COMMIT_STATE_NO_REPLAY")

    def test_duplicate_tx_blocked(self):
        self.assert_hold(lambda e: e["source"].update(duplicate_transaction_count=2), "IDEMPOTENCY_NOT_UNIQUE")

    def test_quantity_parity(self):
        self.assert_hold(lambda e: e["source"].update(quantities=[1, 3]), "SOURCE_LEDGER_STATE_QUANTITY_MISMATCH")

    def test_circular_g18_reconciliation(self):
        self.assert_hold(lambda e: e["reconciliation"]["records"][1]["depends_on"].append("G18_SYNTHETIC"), "CIRCULAR_RECONCILIATION")

    def test_recon_without_independent_provider(self):
        self.assert_hold(lambda e: e["reconciliation"]["records"][0].update(provider_readback=False), "RECON_WITHOUT_PROVIDER_READBACK")

    def test_readback_not_finished(self):
        self.assert_hold(lambda e: e["transaction"].update(readback_status="PENDING"), "TERMINAL_CLOSURE_NOT_PROVEN")

    def test_no_owner_approval(self):
        self.assert_hold(lambda e: e.update(approval=False), "APPROVAL_MISSING")

    def test_hold_overlap(self):
        self.assert_hold(lambda e: e["source"].update(hold_overlap_count=1), "ACTIVE_HOLD_OR_OVERLAP")

    def test_indirect_g18_cycle(self):
        def corrupt(e):
            e["reconciliation"]["records"][0]["depends_on"] = ["G18_SYNTHETIC"]
        self.assert_hold(corrupt, "CIRCULAR_RECONCILIATION")

    def test_missing_reconciliation_dependency(self):
        def corrupt(e):
            e["reconciliation"]["records"][1]["depends_on"] = ["NONEXISTENT"]
        self.assert_hold(corrupt, "RECON_DEPENDENCY_MISSING")

    def test_duplicate_reconciliation_id(self):
        def corrupt(e):
            e["reconciliation"]["records"].append(deepcopy(e["reconciliation"]["records"][0]))
        self.assert_hold(corrupt, "RECON_DUPLICATE_ID")

    def test_unhashable_touch_set_holds_without_crashing(self):
        self.assert_hold(lambda e: e["provider"].update(touch_set=[["A1"]]),
                         "ACTUAL_TOUCH_SET_MISSING_OR_DUPLICATE")

    def test_string_touch_set_cannot_replace_array(self):
        self.assert_hold(lambda e: e["provider"].update(touch_set="Sheet!A8"),
                         "ACTUAL_TOUCH_SET_MISSING_OR_DUPLICATE")

    def test_unknown_provider_flags_fail_closed(self):
        self.assert_hold(lambda e: e["provider"].update(unknown_ack=None),
                         "UNKNOWN_COMMIT_STATE_NO_REPLAY")

    def test_boolean_count_rejected_as_type_invalid(self):
        self.assert_hold(lambda e: e["transaction"].update(total_quantity=True),
                         "TRANSACTION_QUANTITY_SCHEMA_INVALID")

    def test_no_mutation_side_effects(self):
        x = fixture()
        orig = deepcopy(x)
        validate_closeout(x)
        self.assertEqual(orig, x)


if __name__ == "__main__":
    unittest.main()
