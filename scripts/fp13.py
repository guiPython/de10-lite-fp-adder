#!/usr/bin/env python3
"""Encode and decode the simplified normalized 13-bit book format."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from decimal import Decimal, getcontext
from fractions import Fraction


getcontext().prec = 50


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


def parse_board_display(display: str) -> tuple[int, int]:
    """Parse the exact E<exponent> F<fraction> format shown by the board."""
    compact = "".join(display.upper().split())
    match = re.fullmatch(r"E([0-9A-F])F([0-9A-F]{2})", compact)
    if match is None:
        raise ValueError('board display must use the format "E4 F99"')
    return int(match.group(1), 16), int(match.group(2), 16)


def decode_board_hex(sign: int, display: str) -> Fraction:
    exponent, fraction = parse_board_display(display)
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


def decode_command(sign: int, exponent: int, fraction: int) -> None:
    value = decode_fields(sign, exponent, fraction)
    normalized = fraction == 0 or fraction >= 128
    print(f"packed 13 bits    : {sign} {exponent:04b} {fraction:08b}")
    print(f"normalized fields : {'yes' if normalized else 'no'}")
    print(f"formula           : (-1)^{sign} * ({fraction}/256) * 2^{exponent}")
    print(f"decimal value     : {decimal_text(value)}")
    if fraction == 0 and sign == 1:
        print("note              : signed zero (-0) produced by sign-and-magnitude")


def decode_hex_command(sign: int, display: str) -> None:
    exponent, fraction = parse_board_display(display)
    # Validate the LED sign together with the hexadecimal fields.
    value = decode_board_hex(sign, display)
    led_state = "on (negative)" if sign == 1 else "off (positive/zero)"
    print(f"board display     : E{exponent:X} F{fraction:02X}")
    print(f"LEDR9 / sign      : {sign} = {led_state}")
    print(f"exponent          : 0x{exponent:X} = {exponent} = {exponent:04b}_2")
    print(f"fraction          : 0x{fraction:02X} = {fraction} = {fraction:08b}_2")
    print(f"packed 13 bits    : {sign} {exponent:04b} {fraction:08b}")
    print(f"formula           : (-1)^{sign} * ({fraction}/256) * 2^{exponent}")
    print(f"decimal value     : {decimal_text(value)}")
    if fraction == 0 and sign == 1:
        print("note              : signed zero (-0) produced by sign-and-magnitude")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="convert decimal to normalized fields")
    encode_parser.add_argument("decimal")

    decode_parser = subparsers.add_parser("decode", help="convert fields back to decimal")
    decode_parser.add_argument("sign", type=int)
    decode_parser.add_argument("exponent", type=int)
    decode_parser.add_argument("fraction", type=int)

    decode_hex_parser = subparsers.add_parser(
        "decode-hex", help='convert the board display, e.g. 1 "E4 F99", to decimal'
    )
    decode_hex_parser.add_argument("sign", type=int, help="LEDR9 value: 0 or 1")
    decode_hex_parser.add_argument("display", help='display fields in the form "E4 F99"')
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "encode":
            encode_command(args.decimal)
        elif args.command == "decode":
            decode_command(args.sign, args.exponent, args.fraction)
        else:
            decode_hex_command(args.sign, args.display)
    except ValueError as error:
        print(f"error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
