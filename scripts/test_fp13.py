#!/usr/bin/env python3

import unittest
from contextlib import redirect_stdout
from fractions import Fraction
from io import StringIO

from fp13 import (
    analyze_addition,
    decode_fields,
    decode_output,
    decode_output_command,
    encode_decimal,
    parse_output_display,
    resolution,
    result_command,
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
        self.assertEqual(encode_decimal("-32640").represented, Fraction(-32640))

    def test_zero(self):
        encoded = encode_decimal("0")
        self.assertEqual((encoded.sign, encoded.exponent, encoded.fraction), (0, 0, 0))

    def test_out_of_range_values(self):
        with self.assertRaises(ValueError):
            encode_decimal("0.25")
        with self.assertRaises(ValueError):
            encode_decimal("50000")
        with self.assertRaises(ValueError):
            encode_decimal("32641")
        with self.assertRaises(ValueError):
            encode_decimal("-32641")
        with self.assertRaises(ValueError):
            encode_decimal("32640.0001")

    def test_resolution(self):
        self.assertEqual(resolution(0), Fraction(1, 256))
        self.assertEqual(resolution(8), Fraction(1))
        self.assertEqual(resolution(13), Fraction(32))
        self.assertEqual(resolution(15), Fraction(128))

    def test_result_trace_with_encoding_and_alignment_error(self):
        trace = analyze_addition("5000", "1000")
        self.assertEqual(trace.a.bits, "0 1101 10011100")
        self.assertEqual(trace.b.bits, "0 1010 11111010")
        self.assertEqual(trace.exponent_difference, 3)
        self.assertEqual(trace.aligned_a_fraction, 156)
        self.assertEqual(trace.aligned_b_fraction, 31)
        self.assertEqual(trace.aligned_a_value, Fraction(4992))
        self.assertEqual(trace.aligned_b_value, Fraction(992))
        self.assertEqual(trace.result_bits, "0 1101 10111011")
        self.assertEqual(trace.board_display, "000DBB")
        self.assertEqual(trace.expected, Fraction(6000))
        self.assertEqual(trace.aligned_sum, Fraction(5984))
        self.assertEqual(trace.normalization_error, Fraction(0))
        self.assertEqual(trace.obtained, Fraction(5984))
        self.assertEqual(trace.total_error, Fraction(-16))
        self.assertTrue(trace.valid)

    def test_result_trace_with_carry_normalization_error(self):
        trace = analyze_addition("1.5", "3.4")
        self.assertEqual(trace.exponent_difference, 1)
        self.assertEqual(trace.fraction_sum, 313)
        self.assertEqual(trace.result_bits, "0 0011 10011100")
        self.assertEqual(trace.board_display, "00039C")
        self.assertEqual(trace.expected, Fraction(49, 10))
        self.assertEqual(trace.aligned_sum, Fraction(313, 64))
        self.assertEqual(trace.normalization_error, Fraction(-1, 64))
        self.assertEqual(trace.obtained, Fraction(39, 8))
        self.assertEqual(trace.total_error, Fraction(-1, 40))

    def test_result_trace_with_left_normalization(self):
        trace = analyze_addition("-4.5", "4")
        self.assertEqual(trace.fraction_operation, "-")
        self.assertEqual(trace.fraction_sum, 16)
        self.assertEqual(trace.normalization, "left shift 3, exponent - 3")
        self.assertEqual(trace.result_bits, "1 0000 10000000")
        self.assertEqual(trace.obtained, Fraction(-1, 2))
        self.assertEqual(trace.total_error, Fraction(0))

    def test_result_trace_range_flags(self):
        underflow = analyze_addition("-0.50390625", "0.5")
        self.assertTrue(underflow.underflow)
        self.assertFalse(underflow.valid)
        self.assertEqual(underflow.obtained, Fraction(0))

        overflow = analyze_addition("32640", "32640")
        self.assertTrue(overflow.overflow)
        self.assertFalse(overflow.valid)
        self.assertEqual(overflow.board_display, "0000FF")

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

    def test_result_command_reports_decimal_error(self):
        output = StringIO()
        with redirect_stdout(output):
            result_command("5000", "1000")
        report = output.getvalue()
        self.assertIn("exponent difference: 3", report)
        self.assertIn("aligned B fraction : 00011111 (31)", report)
        self.assertIn("expected exact sum : 6000", report)
        self.assertIn("obtained field value: 5984", report)
        self.assertIn("total error        : -16", report)


if __name__ == "__main__":
    unittest.main()
