#!/usr/bin/env python3

import unittest
from contextlib import redirect_stdout
from fractions import Fraction
from io import StringIO

from fp13 import (
    decode_fields,
    decode_output,
    decode_output_command,
    encode_decimal,
    parse_output_display,
)


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

    def test_decode_board_output(self):
        self.assertEqual(parse_output_display("001499"), (1, 4, 153))
        self.assertEqual(parse_output_display("0004d4"), (0, 4, 212))
        self.assertEqual(parse_output_display("001FFF"), (1, 15, 255))
        self.assertEqual(decode_output("001499"), Fraction(-153, 16))
        self.assertEqual(decode_output("0004D4"), Fraction(53, 4))
        self.assertEqual(decode_output("001FFF"), Fraction(-32640))

    def test_reject_invalid_board_display(self):
        with self.assertRaises(ValueError):
            parse_output_display("1499")
        with self.assertRaises(ValueError):
            parse_output_display("00149Z")
        with self.assertRaises(ValueError):
            decode_output("002000")

    def test_decode_output_reports_ledr8_validity(self):
        output = StringIO()
        with redirect_stdout(output):
            decode_output_command("0000FF", 0)
        self.assertIn("invalid underflow/overflow", output.getvalue())
        self.assertIn("diagnostic, not the exact sum", output.getvalue())

        output = StringIO()
        with redirect_stdout(output):
            decode_output_command("001499", 1)
        self.assertIn("valid (LEDR8 is on)", output.getvalue())


if __name__ == "__main__":
    unittest.main()
