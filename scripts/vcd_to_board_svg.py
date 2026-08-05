#!/usr/bin/env python3
"""Generate a visual DE10-Lite board-test summary from the GHDL VCD."""

from __future__ import annotations

import html
import sys
from fractions import Fraction
from pathlib import Path

from vcd_to_wave_svg import find, padded, parse_vcd, snapshot_at


# Stable sample points from top_fp_adder_testbench.vhd. Each point is taken
# after the switches settle and before the next synchronized button transition.
INPUT_STEPS = (
    {
        "state": "S1",
        "field": "sinal de A",
        "sample_ns": 700,
        "expected_display": "51   0",
        "expected_bits": "0",
        "decimal": "0",
        "switches": "SW9",
    },
    {
        "state": "F1",
        "field": "fração de A",
        "sample_ns": 860,
        "expected_display": "F1 195",
        "expected_bits": "11000011",
        "decimal": "195",
        "switches": "SW9..SW2",
    },
    {
        "state": "E1",
        "field": "expoente de A",
        "sample_ns": 1060,
        "expected_display": "E1  08",
        "expected_bits": "1000",
        "decimal": "8",
        "switches": "SW9..SW6",
    },
    {
        "state": "S2",
        "field": "sinal de B",
        "sample_ns": 1260,
        "expected_display": "52   0",
        "expected_bits": "0",
        "decimal": "0",
        "switches": "SW9",
    },
    {
        "state": "F2",
        "field": "fração de B",
        "sample_ns": 1460,
        "expected_display": "F2 195",
        "expected_bits": "11000011",
        "decimal": "195",
        "switches": "SW9..SW2",
    },
    {
        "state": "E2",
        "field": "expoente de B",
        "sample_ns": 1660,
        "expected_display": "E2  08",
        "expected_bits": "1000",
        "decimal": "8",
        "switches": "SW9..SW6",
    },
)


# The board testbench checks positive, negative, underflow, signed-zero and
# exponent-overflow results, including the physical validity LED behavior.
RESULT_CASES = (
    {
        "title": "Caso 1 — soma positiva",
        "sample_ns": 1800,
        "formula": "+195 + 195 = +390",
        "expected_a": "0100011000011",
        "expected_b": "0100011000011",
        "expected_result": "0100111000011",
        "expected_display": "0009C3",
        "expected_ledr": "0100000000",
        "decision": "carry incrementa o expoente de 8 para 9",
    },
    {
        "title": "Caso 2 — resultado negativo",
        "sample_ns": 3260,
        "formula": "−0.5 + 0 = −0.5",
        "expected_a": "1000010000000",
        "expected_b": "0000000000000",
        "expected_result": "1000010000000",
        "expected_display": "001080",
        "expected_ledr": "1100000000",
        "decision": "LEDR9 aceso representa sign_out = 1",
    },
    {
        "title": "Caso 3 — underflow",
        "sample_ns": 4660,
        "formula": "−129/256 + 128/256 = −1/256",
        "expected_a": "1000010000001",
        "expected_b": "0000010000000",
        "expected_result": "1000000000000",
        "expected_display": "001000",
        "expected_ledr": "1000000000",
        "invalid_label": "underflow",
        "decimal_override": "inválido; a soma real é −0.00390625",
        "decision": "LEDR8 apaga: um resultado não nulo foi perdido na normalização",
        "status_text": "PASS — underflow detectado e LEDR8 apagado como esperado",
    },
    {
        "title": "Caso 4 — cancelamento exato",
        "sample_ns": 6060,
        "formula": "+0.5 − 0.5 = zero",
        "expected_a": "0000010000000",
        "expected_b": "1000010000000",
        "expected_result": "1000000000000",
        "expected_display": "001000",
        "expected_ledr": "1100000000",
        "decision": "o núcleo literal preserva o sinal no zero",
    },
    {
        "title": "Caso 5 — overflow de expoente",
        "sample_ns": 7460,
        "formula": "+32640 + 32640 exige expoente 16",
        "expected_a": "0111111111111",
        "expected_b": "0111111111111",
        "expected_result": "0000011111111",
        "expected_display": "0000FF",
        "expected_ledr": "0000000000",
        "invalid_label": "overflow",
        "decimal_override": "inválido; 0000FF decodificaria 0.99609375",
        "decision": "LEDR8 apaga: a palavra com expoente retornando a zero é inválida",
        "status_text": "PASS — overflow detectado e LEDR8 apagado como esperado",
    },
)


# Physical active-low patterns on HEX5..HEX0, including the decimal-point bit.
SEGMENTS_TO_CHAR = {
    "11000000": "0",
    "11111001": "1",
    "10100100": "2",
    "10110000": "3",
    "10011001": "4",
    "10010010": "5",
    "10000010": "6",
    "11111000": "7",
    "10000000": "8",
    "10010000": "9",
    "10001000": "A",
    "10000011": "b",
    "11000110": "C",
    "10100001": "d",
    "10000110": "E",
    "10001110": "F",
    "11111111": " ",
}


def require_equal(actual: str, expected: str, context: str) -> None:
    """Stop figure generation if the sampled VCD contradicts the test plan."""
    if actual != expected:
        raise RuntimeError(f"{context}: expected {expected!r}, observed {actual!r}")


def top_signal(snapshot: dict[str, str], reference: str) -> str:
    """Read one top-level testbench signal without matching the UUT duplicate."""
    return padded(find(snapshot, f"top_fp_adder_testbench/{reference}"), 1)


def display_text(snapshot: dict[str, str]) -> str:
    """Decode the six physical active-low seven-segment output vectors."""
    characters: list[str] = []
    for index in range(5, -1, -1):
        pattern = padded(top_signal(snapshot, f"hex{index}[7:0]"), 8)
        try:
            characters.append(SEGMENTS_TO_CHAR[pattern])
        except KeyError as error:
            raise RuntimeError(f"Unknown HEX{index} segment pattern {pattern}") from error
    return "".join(characters)


def field_bits(word: str, state: str) -> str:
    """Return only the switch/LED bits used by the active input state."""
    if state.startswith("S"):
        return word[0]
    if state.startswith("F"):
        return word[:8]
    return word[:4]


def packed_text(word: str) -> str:
    return f"{word[0]} | {word[1:5]} | {word[5:13]}"


def decoded_decimal(word: str) -> str:
    """Decode one sign/exponent/fraction word for the visual explanation."""
    sign = int(word[0])
    exponent = int(word[1:5], 2)
    fraction = int(word[5:13], 2)
    value = Fraction(fraction, 256) * (2**exponent)
    if sign:
        value = -value
    if value.denominator == 1:
        text = str(value.numerator)
    else:
        text = format(value.numerator / value.denominator, ".10g")
    if fraction == 0 and sign == 1:
        return "−0 (zero com sinal)"
    return text.replace("-", "−")


def collect_input_steps(snapshots):
    steps = []
    for metadata in INPUT_STEPS:
        snapshot = snapshot_at(snapshots, metadata["sample_ns"] * 1_000_000)
        raw_display = display_text(snapshot)
        switch_word = padded(top_signal(snapshot, "sw[9:0]"), 10)
        led_word = padded(top_signal(snapshot, "ledr[9:0]"), 10)
        switch_bits = field_bits(switch_word, metadata["state"])
        led_bits = field_bits(led_word, metadata["state"])

        require_equal(raw_display, metadata["expected_display"], f'{metadata["state"]} display')
        require_equal(switch_bits, metadata["expected_bits"], f'{metadata["state"]} switches')
        require_equal(led_bits, metadata["expected_bits"], f'{metadata["state"]} LEDs')

        # The digit 5 is the physical seven-segment approximation used for S.
        visual_display = raw_display
        if metadata["state"].startswith("S"):
            visual_display = "S" + raw_display[1:]
        steps.append(
            {
                **metadata,
                "display": visual_display,
                "switch_bits": switch_bits,
                "led_bits": led_bits,
            }
        )
    return steps


def collect_result_cases(snapshots):
    cases = []
    for metadata in RESULT_CASES:
        snapshot = snapshot_at(snapshots, metadata["sample_ns"] * 1_000_000)
        operand_a = padded(find(snapshot, "/uut/reg_a[12:0]"), 13)
        operand_b = padded(find(snapshot, "/uut/reg_b[12:0]"), 13)
        result = padded(find(snapshot, "/uut/result[12:0]"), 13)
        display = display_text(snapshot)
        ledr = padded(top_signal(snapshot, "ledr[9:0]"), 10)

        require_equal(operand_a, metadata["expected_a"], f'{metadata["title"]} operand A')
        require_equal(operand_b, metadata["expected_b"], f'{metadata["title"]} operand B')
        require_equal(result, metadata["expected_result"], f'{metadata["title"]} result')
        require_equal(display, metadata["expected_display"], f'{metadata["title"]} display')
        require_equal(ledr, metadata["expected_ledr"], f'{metadata["title"]} LEDs')

        cases.append(
            {
                **metadata,
                "a": packed_text(operand_a),
                "b": packed_text(operand_b),
                "result": packed_text(result),
                "decimal": metadata.get("decimal_override", decoded_decimal(result)),
                "display": display,
                "ledr": ledr,
            }
        )
    return cases


def render_display(parts: list[str], x: int, y: int, characters: str, digit_width: int = 48) -> None:
    """Draw six readable display cells in the same HEX5-to-HEX0 order."""
    gap = 6
    for index, character in enumerate(characters):
        cell_x = x + index * (digit_width + gap)
        parts.append(
            f'<rect class="digit" x="{cell_x}" y="{y}" width="{digit_width}" height="58" rx="6"/>'
        )
        visible = "·" if character == " " else character
        parts.append(
            f'<text class="digit-text" x="{cell_x + digit_width / 2}" y="{y + 41}" '
            f'text-anchor="middle">{html.escape(visible)}</text>'
        )


def render_leds(parts: list[str], x: int, y: int, bits: str) -> None:
    """Draw LEDR9..LEDR0; class and text both communicate the bit state."""
    for index, bit in enumerate(bits):
        led_number = 9 - index
        led_x = x + index * 36
        css_class = "led-on" if bit == "1" else "led-off"
        parts.append(f'<circle class="{css_class}" cx="{led_x + 11}" cy="{y + 11}" r="9"/>')
        parts.append(
            f'<text class="led-label" x="{led_x + 11}" y="{y + 36}" text-anchor="middle">{led_number}</text>'
        )


def render(input_steps, result_cases, input_output: Path, result_output: Path) -> None:
    width, height = 1600, 780
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Sequência de configuração da interface DE10-Lite</title>',
        '<desc id="desc">Estados S1 F1 E1 S2 F2 E2, displays, switches e LEDs extraídos diretamente do VCD do GHDL.</desc>',
        """<style>
        .bg { fill: #ffffff; }
        .panel { fill: #f8fafc; stroke: #94a3b8; stroke-width: 1.5; }
        .step { fill: #f0f9ff; stroke: #7dd3fc; stroke-width: 1.5; }
        .title { font: 700 32px system-ui, sans-serif; fill: #0f172a; }
        .subtitle { font: 16px system-ui, sans-serif; fill: #475569; }
        .section { font: 700 22px system-ui, sans-serif; fill: #0f172a; }
        .card-title { font: 700 17px system-ui, sans-serif; fill: #0f172a; }
        .field { font: 14px system-ui, sans-serif; fill: #475569; }
        .mono { font: 600 14px ui-monospace, monospace; fill: #0f172a; }
        .small { font: 13px system-ui, sans-serif; fill: #475569; }
        .value-band { fill: #e0f2fe; stroke: #38bdf8; stroke-width: 1; }
        .digit { fill: #111827; stroke: #475569; stroke-width: 1; }
        .digit-text { font: 700 29px ui-monospace, monospace; fill: #fbbf24; }
        .led-on { fill: #ef4444; stroke: #991b1b; stroke-width: 2; }
        .led-off { fill: #334155; stroke: #64748b; stroke-width: 2; }
        .led-label { font: 11px ui-monospace, monospace; fill: #64748b; }
        .pass-band { fill: #dcfce7; stroke: #16a34a; stroke-width: 1.5; }
        .pass { font: 700 13px system-ui, sans-serif; fill: #166534; }
        @media (prefers-color-scheme: dark) {
          .bg { fill: #0f172a; }
          .panel { fill: #111827; stroke: #64748b; }
          .step { fill: #0c4a6e; stroke: #38bdf8; }
          .title, .section, .card-title, .mono { fill: #f8fafc; }
          .subtitle, .field, .small { fill: #cbd5e1; }
          .value-band { fill: #0c4a6e; stroke: #38bdf8; }
          .led-label { fill: #cbd5e1; }
          .pass-band { fill: #14532d; stroke: #4ade80; }
          .pass { fill: #dcfce7; }
        }
        </style>""",
        f'<rect class="bg" width="{width}" height="{height}"/>',
        '<text class="title" x="30" y="48">Testbench da DE10-Lite — sequência de configuração</text>',
        '<text class="subtitle" x="30" y="76">Valores extraídos de build/waves/top_fp_adder.vcd; a figura falha se algum display, switch ou LED divergir do esperado.</text>',
        '<text class="section" x="30" y="118">Estados de entrada validados</text>',
    ]

    # Keep both the configuration sequence and result cases in two-column
    # groups. This preserves readable text when the SVG is embedded in GitHub.
    step_width = 760
    for index, step in enumerate(input_steps):
        x = 30 + (index % 2) * 780
        y = 140 + (index // 2) * 210
        parts.append(f'<rect class="step" x="{x}" y="{y}" width="{step_width}" height="190" rx="10"/>')
        parts.append(f'<text class="card-title" x="{x + 15}" y="{y + 27}">{step["state"]}</text>')
        parts.append(
            f'<text class="field" x="{x + 52}" y="{y + 27}">{html.escape(step["field"])}</text>'
        )
        render_display(parts, x + 15, y + 43, step["display"], digit_width=30)
        parts.append(f'<text class="small" x="{x + 270}" y="{y + 62}">Valor decimal mostrado: {step["decimal"]}</text>')
        parts.append(f'<rect class="value-band" x="{x + 270}" y="{y + 76}" width="220" height="34" rx="5"/>')
        parts.append(
            f'<text class="mono" x="{x + 380}" y="{y + 99}" text-anchor="middle">SW: {step["switch_bits"]}</text>'
        )
        parts.append(f'<rect class="value-band" x="{x + 510}" y="{y + 76}" width="220" height="34" rx="5"/>')
        parts.append(
            f'<text class="mono" x="{x + 620}" y="{y + 99}" text-anchor="middle">LED: {step["led_bits"]}</text>'
        )
        parts.append(
            f'<text class="small" x="{x + 270}" y="{y + 139}">Faixa ativa: {step["switches"]}</text>'
        )

    style_block = parts[3]
    parts.append('</svg>')
    input_output.parent.mkdir(parents=True, exist_ok=True)
    input_output.write_text("\n".join(parts) + "\n", encoding="utf-8")

    width, height = 1600, 2070
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Resultados do testbench da interface DE10-Lite</title>',
        '<desc id="desc">Cinco resultados extraídos diretamente do VCD do GHDL, incluindo validade, underflow, cancelamento exato e overflow.</desc>',
        style_block,
        f'<rect class="bg" width="{width}" height="{height}"/>',
        '<text class="title" x="30" y="48">Testbench da DE10-Lite — resultados observados</text>',
        '<text class="subtitle" x="30" y="76">Displays, LEDs, operandos e resultado de 13 bits extraídos de build/waves/top_fp_adder.vcd.</text>',
        '<text class="section" x="30" y="118">Resultados conferidos no estado SHOW_RESULT</text>',
    ]

    panel_width = 760
    panel_positions = []
    for index in range(len(result_cases)):
        row = index // 2
        column = index % 2
        x = 30 + column * 780
        if index == len(result_cases) - 1 and len(result_cases) % 2 == 1:
            x = 420
        panel_positions.append((x, 140 + row * 640))
    for case, (x, y) in zip(result_cases, panel_positions):
        parts.append(f'<rect class="panel" x="{x}" y="{y}" width="{panel_width}" height="620" rx="12"/>')
        parts.append(f'<text class="card-title" x="{x + 20}" y="{y + 34}">{html.escape(case["title"])}</text>')
        parts.append(f'<text class="field" x="{x + 20}" y="{y + 61}">{html.escape(case["formula"])}</text>')

        parts.append(f'<text class="small" x="{x + 20}" y="{y + 94}">A — sinal | expoente | fração</text>')
        parts.append(f'<rect class="value-band" x="{x + 20}" y="{y + 104}" width="720" height="34" rx="5"/>')
        parts.append(f'<text class="mono" x="{x + 380}" y="{y + 127}" text-anchor="middle">{case["a"]}</text>')
        parts.append(f'<text class="small" x="{x + 20}" y="{y + 160}">B — sinal | expoente | fração</text>')
        parts.append(f'<rect class="value-band" x="{x + 20}" y="{y + 170}" width="720" height="34" rx="5"/>')
        parts.append(f'<text class="mono" x="{x + 380}" y="{y + 193}" text-anchor="middle">{case["b"]}</text>')

        parts.append(f'<text class="small" x="{x + 20}" y="{y + 230}">HEX5 … HEX0 · palavra 00SEFF</text>')
        render_display(parts, x + 215, y + 242, case["display"], digit_width=50)

        parts.append(f'<text class="small" x="{x + 20}" y="{y + 331}">LEDR9 … LEDR0</text>')
        render_leds(parts, x + 200, y + 344, case["ledr"])
        sign_state = "aceso (negativo)" if case["ledr"][0] == "1" else "apagado (positivo/zero)"
        valid_state = (
            "aceso (válido)"
            if case["ledr"][1] == "1"
            else f'apagado ({case["invalid_label"]})'
        )
        parts.append(f'<text class="small" x="{x + 20}" y="{y + 402}">LEDR9: {sign_state} · LEDR8: {valid_state}</text>')

        parts.append(f'<text class="small" x="{x + 20}" y="{y + 438}">Resultado de 13 bits</text>')
        parts.append(f'<rect class="value-band" x="{x + 20}" y="{y + 448}" width="720" height="38" rx="5"/>')
        parts.append(f'<text class="mono" x="{x + 380}" y="{y + 473}" text-anchor="middle">{case["result"]}</text>')
        parts.append(f'<text class="field" x="{x + 20}" y="{y + 515}">Decimal: {html.escape(case["decimal"])}</text>')
        parts.append(f'<text class="field" x="{x + 20}" y="{y + 542}">{html.escape(case["decision"])}</text>')
        status_text = case.get(
            "status_text", "PASS — displays, LEDs e resultado coincidem com o VCD"
        )
        parts.append(f'<rect class="pass-band" x="{x + 20}" y="{y + 563}" width="720" height="38" rx="6"/>')
        parts.append(f'<text class="pass" x="{x + 380}" y="{y + 588}" text-anchor="middle">{status_text}</text>')

    parts.append('</svg>')
    result_output.parent.mkdir(parents=True, exist_ok=True)
    result_output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 4:
        print(
            f"Usage: {Path(sys.argv[0]).name} INPUT.vcd INPUTS.svg RESULTS.svg",
            file=sys.stderr,
        )
        return 2

    input_path = Path(sys.argv[1])
    input_output_path = Path(sys.argv[2])
    result_output_path = Path(sys.argv[3])
    snapshots = parse_vcd(input_path)
    input_steps = collect_input_steps(snapshots)
    result_cases = collect_result_cases(snapshots)
    render(input_steps, result_cases, input_output_path, result_output_path)
    print(f"Board input validation generated at: {input_output_path}")
    print(f"Board result validation generated at: {result_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
