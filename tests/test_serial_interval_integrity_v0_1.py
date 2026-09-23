from __future__ import annotations

import unittest

from scripts.serial_interval_integrity_v0_1 import (
    SerialInterval,
    find_overlaps,
    intervals_overlap,
    serial_range_quantity_matches,
)


class SerialIntervalConstructionTests(unittest.TestCase):
    def test_inclusive_quantity(self) -> None:
        self.assertEqual(SerialInterval(100, 199).quantity, 100)

    def test_single_value_interval_has_quantity_one(self) -> None:
        self.assertEqual(SerialInterval(7, 7).quantity, 1)

    def test_reversed_interval_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SerialInterval(200, 100)

    def test_negative_bound_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SerialInterval(-1, 10)

    def test_boolean_bound_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            SerialInterval(True, 10)  # type: ignore[arg-type]


class SerialIntervalOverlapTests(unittest.TestCase):
    def test_disjoint_intervals_do_not_overlap(self) -> None:
        self.assertFalse(
            intervals_overlap(
                SerialInterval(100, 199),
                SerialInterval(200, 299),
            )
        )

    def test_touching_same_value_overlaps(self) -> None:
        self.assertTrue(
            intervals_overlap(
                SerialInterval(100, 200),
                SerialInterval(200, 300),
            )
        )

    def test_contained_interval_overlaps(self) -> None:
        self.assertTrue(
            intervals_overlap(
                SerialInterval(100, 500),
                SerialInterval(200, 300),
            )
        )

    def test_overlap_is_symmetric(self) -> None:
        left = SerialInterval(150, 250)
        right = SerialInterval(200, 350)
        self.assertEqual(
            intervals_overlap(left, right),
            intervals_overlap(right, left),
        )

    def test_find_overlaps_returns_all_index_pairs(self) -> None:
        intervals = (
            SerialInterval(100, 199),
            SerialInterval(300, 399),
            SerialInterval(150, 250),
            SerialInterval(390, 410),
        )
        self.assertEqual(find_overlaps(intervals), ((0, 2), (1, 3)))


class SerialQuantityReconciliationTests(unittest.TestCase):
    def test_exact_declared_quantity_matches(self) -> None:
        self.assertTrue(
            serial_range_quantity_matches(
                SerialInterval(100, 199),
                100,
            )
        )

    def test_mismatched_declared_quantity_fails(self) -> None:
        self.assertFalse(
            serial_range_quantity_matches(
                SerialInterval(100, 199),
                99,
            )
        )

    def test_negative_declared_quantity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            serial_range_quantity_matches(SerialInterval(1, 1), -1)

    def test_boolean_declared_quantity_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            serial_range_quantity_matches(
                SerialInterval(1, 1),
                True,  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
