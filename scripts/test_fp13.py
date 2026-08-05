#!/usr/bin/env python3

import unittest
from fractions import Fraction

from fp13 import decode_board_hex, decode_fields, encode_decimal, parse_board_display


class Fp13ConversionTest(unittest.TestCase):
    def test_exact_positive(self):
        encoded = encode_decimal("13.25")
        self.assertEqual((encoded.sign, encoded.exponent, encoded.fraction), (0, 4, 212))
        self.assertEqual(encoded.represented, Fraction(53, 4))

    def test_exact_negative(self):
        encoded = encode_decimal("-9.5625")
        self.assertEqual((encoded.sign, encoded.exponent, encoded.fraction), (1, 4, 153))
        self.assertEqual(encoded.bits, "1 0100 10011001")

    def test_truncation(self):
        encoded = encode_decimal("3.14")
        self.assertEqual((encoded.exponent, encoded.fraction), (2, 200))
        self.assertEqual(encoded.represented, Fraction(25, 8))
        self.assertEqual(encoded.error, Fraction(-3, 200))

    def test_representation_boundaries(self):
        self.assertEqual((encode_decimal("0.5").exponent, encode_decimal("0.5").fraction), (0, 128))
        self.assertEqual((encode_decimal("32640").exponent, encode_decimal("32640").fraction), (15, 255))

    def test_zero(self):
        encoded = encode_decimal("0")
        self.assertEqual((encoded.sign, encoded.exponent, encoded.fraction), (0, 0, 0))

    def test_out_of_range_values(self):
        with self.assertRaises(ValueError):
            encode_decimal("0.25")
        with self.assertRaises(ValueError):
            encode_decimal("50000")

    def test_decode(self):
        self.assertEqual(decode_fields(1, 4, 153), Fraction(-153, 16))
        self.assertEqual(decode_fields(0, 4, 212), Fraction(53, 4))

    def test_decode_hexadecimal_board_display(self):
        self.assertEqual(parse_board_display("E4 F99"), (4, 153))
        self.assertEqual(parse_board_display("e4f99"), (4, 153))
        self.assertEqual(decode_board_hex(1, "E4 F99"), Fraction(-153, 16))
        self.assertEqual(decode_board_hex(0, "E4 FD4"), Fraction(53, 4))

    def test_reject_invalid_board_display(self):
        with self.assertRaises(ValueError):
            parse_board_display("4 99")
        with self.assertRaises(ValueError):
            parse_board_display("E4 F999")
        with self.assertRaises(ValueError):
            decode_board_hex(2, "E4 F99")


if __name__ == "__main__":
    unittest.main()
