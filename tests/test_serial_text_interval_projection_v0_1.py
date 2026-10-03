from __future__ import annotations

import unittest

from scripts.serial_text_interval_projection_v0_1 import (
    SerialTextInterval,
    serial_text_range_quantity_matches,
)


class SerialTextIdentityTests(unittest.TestCase):
    def test_leading_zero_identity_is_preserved(self):
        interval = SerialTextInterval("000100", "000101")
        self.assertEqual(interval.identity, ("000100", "000101"))
        self.assertEqual(interval.numeric_interval.start, 100)
        self.assertEqual(interval.numeric_interval.end, 101)
        self.assertEqual(interval.quantity, 2)

    def test_numeric_projection_does_not_replace_identity(self):
        interval = SerialTextInterval("000099", "000100")
        _ = interval.numeric_interval
        self.assertEqual(interval.identity, ("000099", "000100"))

    def test_declared_quantity_uses_numeric_projection(self):
        interval = SerialTextInterval("000100", "000199")
        self.assertTrue(serial_text_range_quantity_matches(interval, 100))
        self.assertFalse(serial_text_range_quantity_matches(interval, 99))

    def test_native_integer_serial_input_is_rejected(self):
        with self.assertRaises(TypeError):
            SerialTextInterval(100, "000101")

    def test_whitespace_is_rejected_without_trimming(self):
        with self.assertRaises(TypeError):
            SerialTextInterval(" 000100", "000101")
        with self.assertRaises(TypeError):
            SerialTextInterval("000100", "000101 ")

    def test_blank_and_non_digit_text_are_rejected(self):
        for value in ("", "ABC", "001-002", "１２３"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    SerialTextInterval(value, "000200")

    def test_reversed_numeric_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            SerialTextInterval("000200", "000100")

    def test_declared_quantity_rejects_bool_and_text(self):
        interval = SerialTextInterval("000100", "000100")
        for value in (True, "1"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    serial_text_range_quantity_matches(interval, value)

    def test_negative_declared_quantity_is_rejected(self):
        interval = SerialTextInterval("000100", "000100")
        with self.assertRaises(ValueError):
            serial_text_range_quantity_matches(interval, -1)


if __name__ == "__main__":
    unittest.main()
