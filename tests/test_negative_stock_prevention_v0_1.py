from __future__ import annotations

import unittest

from scripts.negative_stock_prevention_v0_1 import (
    issue_would_create_negative_stock,
    remaining_stock,
)


class NegativeStockPreventionTests(unittest.TestCase):
    def test_exact_depletion_is_allowed(self) -> None:
        self.assertEqual(remaining_stock(100, 100), 0)
        self.assertFalse(issue_would_create_negative_stock(100, 100))

    def test_issue_above_available_is_blocking(self) -> None:
        self.assertEqual(remaining_stock(100, 101), -1)
        self.assertTrue(issue_would_create_negative_stock(100, 101))

    def test_issue_below_available_remains_non_negative(self) -> None:
        self.assertEqual(remaining_stock(100, 40), 60)
        self.assertFalse(issue_would_create_negative_stock(100, 40))

    def test_zero_request_is_allowed(self) -> None:
        self.assertEqual(remaining_stock(7, 0), 7)
        self.assertFalse(issue_would_create_negative_stock(7, 0))

    def test_zero_available_with_positive_request_blocks(self) -> None:
        self.assertEqual(remaining_stock(0, 1), -1)
        self.assertTrue(issue_would_create_negative_stock(0, 1))

    def test_negative_available_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            remaining_stock(-1, 0)

    def test_negative_requested_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            remaining_stock(1, -1)

    def test_boolean_available_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            remaining_stock(True, 0)  # type: ignore[arg-type]

    def test_boolean_requested_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            remaining_stock(1, False)  # type: ignore[arg-type]

    def test_float_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            remaining_stock(10.0, 1)  # type: ignore[arg-type]

    def test_numeric_text_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            remaining_stock(10, "1")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
