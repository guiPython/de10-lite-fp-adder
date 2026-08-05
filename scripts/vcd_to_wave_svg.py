#!/usr/bin/env python3
"""Generate a compact four-case normalization figure from a GHDL VCD file."""

from __future__ import annotations

import html
import sys
from pathlib import Path


CASES = (
    {
        "title": "Caso 1 — ordenar, alinhar e subtrair",
        "formula": "+0.10001010×2³ − 0.11011110×2⁴ = −0.10011001×2⁴",
        "decision": "Já normalizado: leado = 0",
    },
    {
        "title": "Caso 2 — normalização à esquerda",
        "formula": "−0.10010000×2³ + 0.10000000×2³ = −0.10000000×2⁰",
        "decision": "Três zeros à esquerda: expoente 3 − 3 = 0",
    },
    {
        "title": "Caso 3 — underflow",
        "formula": "−0.10000001×2⁰ + 0.10000000×2⁰ → zero",
        "decision": "leado 7 > expoente 0: a magnitude é convertida para zero",
    },
    {
        "title": "Caso 4 — carry-out",
        "formula": "+0.10010000×2³ + 0.10000000×2³ = +0.10001000×2⁴",
        "decision": "sum(8) = 1: deslocar à direita e incrementar o expoente",
    },
)


def parse_vcd(path: Path):
    id_to_name: dict[str, str] = {}
    scopes: list[str] = []
    snapshots: list[tuple[int, dict[str, str]]] = []
    values: dict[str, str] = {}
    current_time = 0
    definitions_done = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not definitions_done:
            if line.startswith("$scope"):
                scopes.append(line.split()[2])
            elif line.startswith("$upscope"):
                scopes.pop()
            elif line.startswith("$var"):
                parts = line.split()
                identifier = parts[3]
                reference = parts[4]
                id_to_name[identifier] = "/".join((*scopes, reference))
            elif line.startswith("$enddefinitions"):
                definitions_done = True
            continue

        if not line:
            continue
        if line.startswith("#"):
            snapshots.append((current_time, values.copy()))
            current_time = int(line[1:])
        elif line[0] in "01xXzZ":
            values[id_to_name[line[1:]]] = line[0].lower()
        elif line[0] in "bB":
            value, identifier = line[1:].split(None, 1)
            values[id_to_name[identifier]] = value.lower()

    snapshots.append((current_time, values.copy()))
    return snapshots


def snapshot_at(snapshots, sample_time: int) -> dict[str, str]:
    result: dict[str, str] = {}
    for timestamp, values in snapshots:
        if timestamp > sample_time:
            break
        result = values
    return result


def find(values: dict[str, str], suffix: str) -> str:
    matches = [value for name, value in values.items() if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one VCD signal ending in {suffix!r}, found {len(matches)}")
    return matches[0]


def as_int(bits: str) -> str:
    if not bits or any(bit not in "01" for bit in bits):
        return "X"
    return str(int(bits, 2))


def padded(bits: str, width: int) -> str:
    return bits.zfill(width) if all(bit in "01" for bit in bits) else bits.upper()


def build_case(snapshot: dict[str, str], metadata: dict[str, str]):
    sum_bits = padded(find(snapshot, "/uut/sum[8:0]"), 9)
    leado_bits = padded(find(snapshot, "/uut/leado[2:0]"), 3)
    norm_bits = padded(find(snapshot, "/uut/sum_norm[7:0]"), 8)
    exp_bits = padded(find(snapshot, "/uut/expn[3:0]"), 4)
    frac_bits = padded(find(snapshot, "/uut/fracn[7:0]"), 8)
    sign = find(snapshot, "normalization_testbench/sign_out")
    output = f"{sign} | {exp_bits} | {frac_bits}"
    return {
        **metadata,
        "rows": (
            ("sum[8:0]", sum_bits, f"sem sinal {as_int(sum_bits)}"),
            ("leado", leado_bits, f"{as_int(leado_bits)} zeros à esquerda"),
            ("sum_norm", norm_bits, f"0x{int(norm_bits, 2):02X}"),
            ("expn", exp_bits, f"expoente {as_int(exp_bits)}"),
            ("fracn", frac_bits, f"fração 0x{int(frac_bits, 2):02X}"),
            ("output", output, "sinal | expoente | fração"),
        ),
    }


def render(cases, output: Path):
    width, height = 1480, 960
    panel_w, panel_h = 700, 420
    positions = ((30, 40), (750, 40), (30, 500), (750, 500))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Quatro casos obrigatórios de normalização em ponto flutuante</title>',
        '<desc id="desc">Valores gerados do VCD do GHDL para ordenação e subtração, normalização à esquerda, underflow e carry-out.</desc>',
        """<style>
        :root { color-scheme: light dark; }
        .bg { fill: #ffffff; }
        .panel { fill: #f8fafc; stroke: #94a3b8; stroke-width: 1.5; }
        .band { fill: #e0f2fe; stroke: #0284c7; stroke-width: 1; }
        .title { font: 700 20px system-ui, sans-serif; fill: #0f172a; }
        .formula { font: 15px ui-monospace, monospace; fill: #334155; }
        .label { font: 600 14px ui-monospace, monospace; fill: #334155; }
        .value { font: 600 14px ui-monospace, monospace; fill: #0c4a6e; }
        .meaning { font: 13px system-ui, sans-serif; fill: #475569; }
        .decision { font: 600 14px system-ui, sans-serif; fill: #075985; }
        @media (prefers-color-scheme: dark) {
          .bg { fill: #0f172a; }
          .panel { fill: #111827; stroke: #64748b; }
          .band { fill: #0c4a6e; stroke: #38bdf8; }
          .title { fill: #f8fafc; }
          .formula, .label { fill: #cbd5e1; }
          .value { fill: #e0f2fe; }
          .meaning { fill: #cbd5e1; }
          .decision { fill: #7dd3fc; }
        }
        </style>""",
        f'<rect class="bg" width="{width}" height="{height}"/>',
    ]

    for case, (x, y) in zip(cases, positions):
        parts.append(f'<rect class="panel" x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" rx="10"/>')
        parts.append(f'<text class="title" x="{x + 20}" y="{y + 34}">{html.escape(case["title"])}</text>')
        parts.append(f'<text class="formula" x="{x + 20}" y="{y + 62}">{html.escape(case["formula"])}</text>')

        row_y = y + 94
        for label, value, meaning in case["rows"]:
            parts.append(f'<text class="label" x="{x + 20}" y="{row_y + 20}">{html.escape(label)}</text>')
            parts.append(f'<rect class="band" x="{x + 125}" y="{row_y}" width="300" height="30" rx="4"/>')
            parts.append(f'<text class="value" x="{x + 275}" y="{row_y + 21}" text-anchor="middle">{html.escape(value)}</text>')
            parts.append(f'<text class="meaning" x="{x + 440}" y="{row_y + 20}">{html.escape(meaning)}</text>')
            row_y += 44

        parts.append(f'<text class="decision" x="{x + 20}" y="{y + 390}">{html.escape(case["decision"])}</text>')

    parts.append("</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {Path(sys.argv[0]).name} INPUT.vcd OUTPUT.svg", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    snapshots = parse_vcd(input_path)

    # Each case occupies 20 ns. Sample the stable midpoint of each interval.
    sample_times_fs = (10_000_000, 30_000_000, 50_000_000, 70_000_000)
    cases = [
        build_case(snapshot_at(snapshots, sample_time), metadata)
        for sample_time, metadata in zip(sample_times_fs, CASES)
    ]
    render(cases, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
