from __future__ import annotations

from datetime import date
import unittest

from scripts.allocation_nearest_prior import SourceLot, eligible_sources_nearest_prior


def lot(source_id: str, yyyy: int, mm: int, dd: int, row: int, serial: str) -> SourceLot:
    return SourceLot(source_id, date(yyyy, mm, dd), row, serial)


class NearestPriorTests(unittest.TestCase):
    def test_future_source_is_excluded(self) -> None:
        result = eligible_sources_nearest_prior(
            (
                lot("SYNTH-A", 2026, 1, 10, 1, "000000000010"),
                lot("SYNTH-B", 2026, 1, 11, 1, "000000000020"),
            ),
            date(2026, 1, 10),
        )
        self.assertEqual(tuple(x.source_id for x in result), ("SYNTH-A",))

    def test_nearest_prior_date_first(self) -> None:
        result = eligible_sources_nearest_prior(
            (
                lot("OLDER", 2026, 1, 8, 1, "000000000010"),
                lot("NEARER", 2026, 1, 9, 99, "000000000999"),
            ),
            date(2026, 1, 10),
        )
        self.assertEqual(tuple(x.source_id for x in result), ("NEARER", "OLDER"))

    def test_same_date_uses_source_row_ascending(self) -> None:
        result = eligible_sources_nearest_prior(
            (
                lot("ROW-2", 2026, 1, 9, 2, "000000000001"),
                lot("ROW-1", 2026, 1, 9, 1, "000000000999"),
            ),
            date(2026, 1, 10),
        )
        self.assertEqual(tuple(x.source_id for x in result), ("ROW-1", "ROW-2"))

    def test_same_date_and_row_uses_serial_numeric_ascending(self) -> None:
        result = eligible_sources_nearest_prior(
            (
                lot("HIGH", 2026, 1, 9, 1, "000000000020"),
                lot("LOW", 2026, 1, 9, 1, "000000000003"),
            ),
            date(2026, 1, 10),
        )
        self.assertEqual(tuple(x.source_id for x in result), ("LOW", "HIGH"))

    def test_leading_zero_identity_is_preserved(self) -> None:
        source = lot("ZERO", 2026, 1, 9, 1, "000000000003")
        result = eligible_sources_nearest_prior((source,), date(2026, 1, 10))
        self.assertEqual(result[0].serial_start, "000000000003")

    def test_invalid_serial_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            eligible_sources_nearest_prior(
                (lot("BAD", 2026, 1, 9, 1, "ABC"),),
                date(2026, 1, 10),
            )

    def test_blank_source_id_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            eligible_sources_nearest_prior(
                (lot("   ", 2026, 1, 9, 1, "000000000001"),),
                date(2026, 1, 10),
            )

    def test_zero_row_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            eligible_sources_nearest_prior(
                (lot("BAD-ROW", 2026, 1, 9, 0, "000000000001"),),
                date(2026, 1, 10),
            )

    def test_bool_row_fails_closed(self) -> None:
        source = SourceLot("BAD-BOOL", date(2026, 1, 9), True, "000000000001")
        with self.assertRaises(ValueError):
            eligible_sources_nearest_prior((source,), date(2026, 1, 10))

    def test_empty_input_is_valid(self) -> None:
        self.assertEqual(eligible_sources_nearest_prior((), date(2026, 1, 10)), ())


if __name__ == "__main__":
    unittest.main()
