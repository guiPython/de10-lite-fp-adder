#!/usr/bin/env python3
"""Encode, decode and analyze the simplified 13-bit book format."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from decimal import Decimal, getcontext
from fractions import Fraction


getcontext().prec = 50

MAX_MAGNITUDE = Fraction(255, 256) * (2**15)


@dataclass(frozen=True)
class Encoded:
    sign: int
    exponent: int
    fraction: int
    requested: Fraction
    represented: Fraction

    @property
    def error(self) -> Fraction:
        return self.represented - self.requested

    @property
    def bits(self) -> str:
        return f"{self.sign} {self.exponent:04b} {self.fraction:08b}"


@dataclass(frozen=True)
class AdditionTrace:
    """Observable steps of the simplified adder from Listing 3.19."""

    a: Encoded
    b: Encoded
    big_operand: str
    common_exponent: int
    exponent_difference: int
    aligned_a_fraction: int
    aligned_b_fraction: int
    aligned_a_value: Fraction
    aligned_b_value: Fraction
    fraction_operation: str
    fraction_sum: int
    normalization: str
    result_sign: int
    result_exponent: int
    result_fraction: int
    underflow: bool
    overflow: bool

    @property
    def expected(self) -> Fraction:
        return self.a.requested + self.b.requested

    @property
    def obtained(self) -> Fraction:
        return decode_fields(
            self.result_sign,
            self.result_exponent,
            self.result_fraction,
        )

    @property
    def aligned_sum(self) -> Fraction:
        return self.aligned_a_value + self.aligned_b_value

    @property
    def normalization_error(self) -> Fraction:
        return self.obtained - self.aligned_sum

    @property
    def total_error(self) -> Fraction:
        return self.obtained - self.expected

    @property
    def result_bits(self) -> str:
        return (
            f"{self.result_sign} {self.result_exponent:04b} "
            f"{self.result_fraction:08b}"
        )

    @property
    def board_display(self) -> str:
        return f"00{self.result_sign:X}{self.result_exponent:X}{self.result_fraction:02X}"

    @property
    def valid(self) -> bool:
        return not (self.underflow or self.overflow)


def parse_decimal(text: str) -> Fraction:
    return Fraction(Decimal(text))


def encode_decimal(text: str) -> Encoded:
    requested = parse_decimal(text)
    if requested == 0:
        return Encoded(0, 0, 0, requested, Fraction(0))

    sign = int(requested < 0)
    magnitude = abs(requested)
    if magnitude < Fraction(1, 2):
        raise ValueError("magnitude is below the smallest normalized value, 0.5")
    if magnitude > MAX_MAGNITUDE:
        raise ValueError("magnitude exceeds the largest representable value, 32640")

    exponent = 0
    normalized = magnitude
    while normalized >= 1:
        normalized /= 2
        exponent += 1

    if exponent > 15:
        raise ValueError("magnitude exceeds the largest representable value, 32640")

    # The book ignores rounding. Converting to int truncates toward zero.
    fraction = int(normalized * 256)
    if not 128 <= fraction <= 255:
        raise ValueError("value cannot be represented as a normalized nonzero word")

    represented_magnitude = Fraction(fraction, 256) * (2**exponent)
    represented = -represented_magnitude if sign else represented_magnitude
    return Encoded(sign, exponent, fraction, requested, represented)


def decode_fields(sign: int, exponent: int, fraction: int) -> Fraction:
    if sign not in (0, 1):
        raise ValueError("sign must be 0 or 1")
    if not 0 <= exponent <= 15:
        raise ValueError("exponent must be between 0 and 15")
    if not 0 <= fraction <= 255:
        raise ValueError("fraction must be between 0 and 255")

    magnitude = Fraction(fraction, 256) * (2**exponent)
    return -magnitude if sign else magnitude


def resolution(exponent: int) -> Fraction:
    """Return one fraction-field step, 2^(exponent-8)."""
    power = exponent - 8
    if power >= 0:
        return Fraction(2**power)
    return Fraction(1, 2 ** (-power))


def signed_field_value(sign: int, exponent: int, fraction: int) -> Fraction:
    return decode_fields(sign, exponent, fraction)


def leading_zero_count(fraction_sum: int) -> int:
    """Reproduce the book priority encoder, including zero -> seven."""
    low_fraction = fraction_sum & 0xFF
    for count in range(7):
        if low_fraction & (0x80 >> count):
            return count
    return 7


def analyze_addition(a_text: str, b_text: str) -> AdditionTrace:
    """Encode two decimals and reproduce the packed VHDL addition."""
    a = encode_decimal(a_text)
    b = encode_decimal(b_text)

    magnitude_a = (a.exponent << 8) | a.fraction
    magnitude_b = (b.exponent << 8) | b.fraction

    # The original sorter selects operand B when both magnitudes are equal.
    if magnitude_a > magnitude_b:
        big_name, big, small = "A", a, b
    else:
        big_name, big, small = "B", b, a

    exponent_difference = big.exponent - small.exponent
    aligned_small_fraction = small.fraction >> exponent_difference

    if big_name == "A":
        aligned_a_fraction = a.fraction
        aligned_b_fraction = aligned_small_fraction
    else:
        aligned_a_fraction = aligned_small_fraction
        aligned_b_fraction = b.fraction

    aligned_a_value = signed_field_value(
        a.sign,
        big.exponent,
        aligned_a_fraction,
    )
    aligned_b_value = signed_field_value(
        b.sign,
        big.exponent,
        aligned_b_fraction,
    )

    if big.sign == small.sign:
        fraction_sum = big.fraction + aligned_small_fraction
        fraction_operation = "+"
    else:
        fraction_sum = big.fraction - aligned_small_fraction
        fraction_operation = "-"

    underflow = False
    overflow = False
    result_sign = big.sign

    if fraction_sum & 0x100:
        result_exponent = (big.exponent + 1) & 0xF
        result_fraction = (fraction_sum >> 1) & 0xFF
        overflow = big.exponent == 15
        normalization = "carry: fraction >> 1, exponent + 1"
    else:
        leading_zeros = leading_zero_count(fraction_sum)
        if leading_zeros > big.exponent:
            result_exponent = 0
            result_fraction = 0
            underflow = fraction_sum != 0
            normalization = (
                f"underflow: {leading_zeros} leading zeros exceed exponent "
                f"{big.exponent}"
            )
        else:
            result_exponent = big.exponent - leading_zeros
            result_fraction = ((fraction_sum & 0xFF) << leading_zeros) & 0xFF
            normalization = (
                "none" if leading_zeros == 0 else
                f"left shift {leading_zeros}, exponent - {leading_zeros}"
            )

    return AdditionTrace(
        a=a,
        b=b,
        big_operand=big_name,
        common_exponent=big.exponent,
        exponent_difference=exponent_difference,
        aligned_a_fraction=aligned_a_fraction,
        aligned_b_fraction=aligned_b_fraction,
        aligned_a_value=aligned_a_value,
        aligned_b_value=aligned_b_value,
        fraction_operation=fraction_operation,
        fraction_sum=fraction_sum,
        normalization=normalization,
        result_sign=result_sign,
        result_exponent=result_exponent,
        result_fraction=result_fraction,
        underflow=underflow,
        overflow=overflow,
    )


def parse_output_display(display: str) -> tuple[int, int, int]:
    """Parse the six-digit zero-extended 00SEFF word shown by the board."""
    compact = "".join(display.upper().split())
    match = re.fullmatch(r"[0-9A-F]{6}", compact)
    if match is None:
        raise ValueError('board display must use six hexadecimal digits, e.g. "001499"')

    packed = int(compact, 16)
    if packed > 0x1FFF:
        raise ValueError("board display exceeds the 13-bit range 000000..001FFF")
    sign = (packed >> 12) & 1
    exponent = (packed >> 8) & 0xF
    fraction = packed & 0xFF
    return sign, exponent, fraction


def decode_output(display: str) -> Fraction:
    """Decode the numeric fields embedded in a six-digit 00SEFF output."""
    sign, exponent, fraction = parse_output_display(display)
    return decode_fields(sign, exponent, fraction)


def decimal_text(value: Fraction) -> str:
    decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
    text = format(decimal_value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def encode_command(decimal_value: str) -> None:
    encoded = encode_decimal(decimal_value)
    print(f"requested decimal : {decimal_text(encoded.requested)}")
    print(f"sign              : {encoded.sign}")
    print(f"exponent          : {encoded.exponent} = {encoded.exponent:04b}_2")
    print(f"fraction          : {encoded.fraction} = {encoded.fraction:08b}_2")
    print(f"normalized        : (-1)^{encoded.sign} * 0.{encoded.fraction:08b} * 2^{encoded.exponent}")
    print(f"packed 13 bits    : {encoded.bits}")
    print(f"represented value : {decimal_text(encoded.represented)}")
    print(f"representation err: {decimal_text(encoded.error)}")


def print_operand(label: str, encoded: Encoded) -> None:
    print(f"{label} requested       : {decimal_text(encoded.requested)}")
    print(f"{label} packed 13 bits  : {encoded.bits}")
    print(
        f"{label} fields          : S={encoded.sign}, E={encoded.exponent}, "
        f"F={encoded.fraction}"
    )
    print(
        f"{label} resolution      : 2^({encoded.exponent}-8) = "
        f"{decimal_text(resolution(encoded.exponent))}"
    )
    print(f"{label} represented     : {decimal_text(encoded.represented)}")
    print(f"{label} encoding error  : {decimal_text(encoded.error)}")


def result_command(a_text: str, b_text: str) -> None:
    trace = analyze_addition(a_text, b_text)

    print("INPUT ENCODING")
    print_operand("A", trace.a)
    print()
    print_operand("B", trace.b)

    print("\nALIGNMENT")
    print(f"larger magnitude   : operand {trace.big_operand}")
    print(f"A exponent         : {trace.a.exponent} ({trace.a.exponent:04b})")
    print(f"B exponent         : {trace.b.exponent} ({trace.b.exponent:04b})")
    print(f"exponent difference: {trace.exponent_difference}")
    print(f"common exponent    : {trace.common_exponent}")
    print(
        f"common resolution  : 2^({trace.common_exponent}-8) = "
        f"{decimal_text(resolution(trace.common_exponent))}"
    )
    print(
        f"aligned A fraction : {trace.aligned_a_fraction:08b} "
        f"({trace.aligned_a_fraction})"
    )
    print(
        f"aligned B fraction : {trace.aligned_b_fraction:08b} "
        f"({trace.aligned_b_fraction})"
    )
    print(f"aligned A value    : {decimal_text(trace.aligned_a_value)}")
    print(f"aligned B value    : {decimal_text(trace.aligned_b_value)}")
    print(
        "A alignment error : "
        f"{decimal_text(trace.aligned_a_value - trace.a.represented)}"
    )
    print(
        "B alignment error : "
        f"{decimal_text(trace.aligned_b_value - trace.b.represented)}"
    )

    if trace.big_operand == "A":
        big_fraction = trace.a.fraction
        small_fraction = trace.aligned_b_fraction
    else:
        big_fraction = trace.b.fraction
        small_fraction = trace.aligned_a_fraction

    print("\nADD/SUBTRACT AND NORMALIZE")
    print(
        f"fraction operation : {big_fraction} {trace.fraction_operation} "
        f"{small_fraction} = {trace.fraction_sum}"
    )
    print(f"normalization      : {trace.normalization}")
    print(f"result packed bits : {trace.result_bits}")
    print(f"board display      : {trace.board_display}")
    if trace.valid:
        print(
            f"result resolution  : 2^({trace.result_exponent}-8) = "
            f"{decimal_text(resolution(trace.result_exponent))}"
        )
    elif trace.overflow:
        print("result resolution  : unavailable; required exponent exceeds 15")
    else:
        print("result resolution  : unavailable; required exponent is below 0")
    print(
        "result validity    : "
        + (
            "invalid (overflow)" if trace.overflow else
            "invalid (underflow)" if trace.underflow else
            "valid"
        )
    )

    print("\nDECIMAL CHECK")
    print(f"expected exact sum : {decimal_text(trace.expected)}")
    print(f"sum after alignment: {decimal_text(trace.aligned_sum)}")
    if trace.valid:
        print(f"normalization error: {decimal_text(trace.normalization_error)}")
        print(f"obtained field value: {decimal_text(trace.obtained)}")
        print(f"total error        : {decimal_text(trace.total_error)}")
    else:
        print(f"diagnostic field value: {decimal_text(trace.obtained)}")
        print(f"diagnostic error   : {decimal_text(trace.total_error)}")
        print("warning            : invalid result fields are not the exact sum")


def decode_output_command(display: str, ledr8: int | None) -> None:
    sign, exponent, fraction = parse_output_display(display)
    value = decode_output(display)
    led_state = "on (negative)" if sign == 1 else "off (positive/zero)"
    print(f"board display     : 00{sign:X}{exponent:X}{fraction:02X}")
    print(f"packed hexadecimal: 0x{sign:X}{exponent:X}{fraction:02X}")
    print(f"embedded sign     : {sign}; LEDR9 should be {led_state}")
    print(f"exponent          : 0x{exponent:X} = {exponent} = {exponent:04b}_2")
    print(f"fraction          : 0x{fraction:02X} = {fraction} = {fraction:08b}_2")
    print(f"packed 13 bits    : {sign} {exponent:04b} {fraction:08b}")
    print(f"formula           : (-1)^{sign} * ({fraction}/256) * 2^{exponent}")
    print(f"decoded field value: {decimal_text(value)}")
    if ledr8 is None:
        print("result validity   : unknown; provide LEDR8=0/1 or check the board LED")
    elif ledr8 == 1:
        print("result validity   : valid (LEDR8 is on)")
    else:
        print("result validity   : invalid underflow/overflow (LEDR8 is off)")
        print("warning           : decoded fields are diagnostic, not the exact sum")
    if fraction == 0 and sign == 1:
        print("note              : signed zero (-0) produced by sign-and-magnitude")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="convert decimal to normalized fields")
    encode_parser.add_argument("decimal")

    decode_parser = subparsers.add_parser(
        "decode",
        help='decode the six-display board output in 00SEFF format, e.g. "001499"',
    )
    decode_parser.add_argument(
        "display",
        help='exactly six hexadecimal digits: 00SEFF (S=sign, E=exponent, FF=fraction)',
    )
    decode_parser.add_argument(
        "--ledr8",
        type=int,
        choices=(0, 1),
        help="optional validity LED: 1=valid, 0=underflow/overflow",
    )

    result_parser = subparsers.add_parser(
        "result",
        help="trace encoding, alignment, normalization and decimal error",
    )
    result_parser.add_argument("a", help="first decimal operand")
    result_parser.add_argument("b", help="second decimal operand")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "encode":
            encode_command(args.decimal)
        elif args.command == "decode":
            decode_output_command(args.display, args.ledr8)
        else:
            result_command(args.a, args.b)
    except ValueError as error:
        print(f"error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
